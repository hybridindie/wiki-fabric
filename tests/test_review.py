"""Tests for review.py — staleness scan, verify, auto-reverify."""

import sys
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent.parent

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestScan(unittest.TestCase):
    def test_scan_finds_stamps(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "cmd/review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        report = rv.scan()
        assert "due" in report and "overdue" in report and "stale" in report
        # CI has no claims (evidence/ gitignored); skip if empty
        claim_dir = REPO / "evidence" / "claims"
        if not claim_dir.exists() or not list(claim_dir.glob("claim-*.md")):
            raise unittest.SkipTest("no claims in fabric (CI)")
        assert report["current"] + len(report["due"]) + len(report["overdue"]) + len(report["stale"]) > 0

    def test_parse_date(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "cmd/review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        import datetime
        d = rv._parse_date("2026-09-21")
        assert d == datetime.date(2026, 9, 21)
        assert rv._parse_date("garbage") is None


class TestAutoReverify(unittest.TestCase):
    def test_auto_reverify_mechanism(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "cmd/review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        # the function exists and is callable
        assert callable(rv.auto_reverify)
        # dry-run doesn't write
        # (real test needs fabric content — skip if no claims)
        claim_dir = Path(__file__).parent.parent / "evidence" / "claims"
        if not claim_dir.exists() or not list(claim_dir.glob("*.md")):
            raise unittest.SkipTest("no claims in fabric")


class TestVerifyLocators(unittest.TestCase):
    """#109: locator re-verification — stamp integrity pass."""

    @staticmethod
    def _load():
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "cmd/review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        return rv

    @staticmethod
    def _fabric(tmp, locator="L2-L3", quote_line="the quote is here"):
        (tmp / "evidence" / "claims").mkdir(parents=True)
        (tmp / "evidence" / "sources").mkdir(parents=True)
        rawdir = tmp / "evidence" / "raw" / "proj"
        rawdir.mkdir(parents=True)
        (rawdir / "doc.md").write_text(
            "intro line\nthe quote is here\nthird line\nlater content\n")
        (tmp / "evidence" / "sources" / "src-proj-doc-md.md").write_text(
            "---\ntype: source\nsource_path: evidence/raw/proj/doc.md\nsha256: x\n---\n\n# s\n")
        (tmp / "evidence" / "claims" / "claim-proj-doc-md-000.md").write_text(
            "---\ntype: claim\nid: claim-proj-doc-md-000\nstatus: supported\n"
            "source_refs:\n  - source: \"[[src-proj-doc-md]]\"\n"
            f"    locator: \"{locator}\"\n    quote: \"the quote is here\"\n"
            "verified:\n  - by: \"process:locator-verification\"\n"
            "    at: \"2026-09-26\"\n---\n\n# c\n")

    def test_exact_locator_kept(self):
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as td:
            self._fabric(Path(td))
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(td)
            try:
                r = rv.verify_locators(dry_run=True)
            finally:
                rv.CORPUS_ROOT = old
            assert r["kept"] == 1 and r["fixed"] == 0 and r["contested"] == 0

    def test_drifted_locator_fixed(self):
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self._fabric(Path(tmp), locator="L99")
            cp = Path(tmp) / "evidence/claims/claim-proj-doc-md-000.md"
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(tmp)
            try:
                r = rv.verify_locators(dry_run=False)
                text = cp.read_text()
            finally:
                rv.CORPUS_ROOT = old
            assert r["fixed"] == 1
            assert 'locator: "L2"' in text or 'locator: "L2-L3"' in text
            assert "status: supported" in text  # not contested

    def test_vanished_quote_contested(self):
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self._fabric(Path(tmp))
            cp = Path(tmp) / "evidence/claims/claim-proj-doc-md-000.md"
            # quote the source does not contain
            t = cp.read_text().replace("the quote is here", "a fabricated quote entirely")
            cp.write_text(t)
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(tmp)
            try:
                r = rv.verify_locators(dry_run=False)
                text = cp.read_text()
            finally:
                rv.CORPUS_ROOT = old
            assert r["contested"] == 1
            assert "status: contested" in text
            assert "process:locator-verification" not in text

    def test_contest_edits_status_field_only(self):
        """The contest edit must touch the status FIELD, never quote content
        that happens to contain 'status: supported' (sim false-positive)."""
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self._fabric(Path(tmp))
            cp = Path(tmp) / "evidence/claims/claim-proj-doc-md-000.md"
            t = cp.read_text().replace("the quote is here", "a quote saying status: supported inside")
            cp.write_text(t)
            # fabricate the same phrase in the source so the quote exists → kept;
            # then make a second claim whose quote vanished — its edit must not
            # touch quoted content. Simplest direct check: run contest on the
            # vanished-quote claim and confirm the quote string survives.
            (Path(tmp) / "evidence/raw/proj/doc.md").write_text("intro\nother content\n")
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(tmp)
            try:
                r = rv.verify_locators(dry_run=False)
                text = cp.read_text()
            finally:
                rv.CORPUS_ROOT = old
            assert "a quote saying status: supported inside" in text, \
                "contest edit must not rewrite quote content"
            assert "status: contested" in text

    def test_dry_run_writes_nothing(self):
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as tmp:
            self._fabric(Path(tmp), locator="L99")
            cp = Path(tmp) / "evidence/claims/claim-proj-doc-md-000.md"
            before = cp.read_text()
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(tmp)
            try:
                r = rv.verify_locators(dry_run=True)
            finally:
                rv.CORPUS_ROOT = old
            assert r["fixed"] == 1
            assert cp.read_text() == before


if __name__ == "__main__":
    unittest.main()


class TestBacktickElisionRepair(unittest.TestCase):
    """#109: the extraction model empties inline-code spans — repairable."""

    @staticmethod
    def _load():
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "cmd/review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        return rv

    def test_repair_fills_empty_spans(self):
        rv = self._load()
        quote = "Numbers every line** — ``, ``, … so the model can cite ranges"
        seg = "1. **Numbers every line** — `L1:`, `L2:`, … so the model can cite ranges"
        new, did = rv.repair_backtick_elision(quote, seg)
        assert did and "`L1:`" in new and "`L2:`" in new

    def test_no_repair_when_quote_has_content(self):
        rv = self._load()
        new, did = rv.repair_backtick_elision("text `real content` end", "src `L1:` here")
        assert not did and new == "text `real content` end"

    def test_no_repair_without_source_spans(self):
        rv = self._load()
        new, did = rv.repair_backtick_elision("text ``, `` end", "no backticks here")
        assert not did

    def test_contested_quote_survives_contest_edit(self):
        """The contest edit touches the status FIELD only — quoted phrases
        containing 'status: supported' are never rewritten (sim lesson)."""
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "evidence/claims").mkdir(parents=True)
            (Path(td) / "evidence/sources").mkdir(parents=True)
            rawdir = Path(td) / "evidence/raw/proj"
            rawdir.mkdir(parents=True)
            (rawdir / "doc.md").write_text("plain source text\n")
            (Path(td) / "evidence/sources/src-proj-doc-md.md").write_text(
                "---\ntype: source\nsource_path: evidence/raw/proj/doc.md\n---\n\n# s\n")
            cp = Path(td) / "evidence/claims/claim-proj-doc-md-000.md"
            cp.write_text(
                "---\ntype: claim\nstatus: supported\n"
                "source_refs:\n  - source: \"[[src-proj-doc-md]]\"\n"
                "    locator: \"L1\"\n"
                "    quote: \"a quote with status: supported inside\"\n"
                "verified:\n  - by: \"process:locator-verification\"\n"
                "    at: \"2026-09-26\"\n---\n\n# c\n")
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(td)
            try:
                r = rv.verify_locators(dry_run=False)
                text = cp.read_text()
            finally:
                rv.CORPUS_ROOT = old
            assert r["contested"] == 1
            assert "a quote with status: supported inside" in text


class TestContestRestore(unittest.TestCase):
    """Session audit: a repaired quote left status contested forever — the kept
    path must restore status + stamp when a previously-contested quote verifies."""

    @staticmethod
    def _load():
        import importlib.util as ilu
        spec = ilu.spec_from_file_location("rv", REPO / "scripts" / "cmd/review.py")
        rv = ilu.module_from_spec(spec); spec.loader.exec_module(rv)
        return rv

    def test_contested_restored_when_quote_verifies(self, tmp_path=None):
        import tempfile
        rv = self._load()
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "evidence" / "claims").mkdir(parents=True)
            (Path(td) / "evidence" / "sources").mkdir(parents=True)
            rawdir = Path(td) / "evidence" / "raw" / "proj"
            rawdir.mkdir(parents=True)
            (rawdir / "doc.md").write_text("intro line\nthe quote is here\n")
            (Path(td) / "evidence" / "sources" / "src-proj-doc-md.md").write_text(
                "---\ntype: source\nsource_path: evidence/raw/proj/doc.md\n---\n\n# s\n")
            cp = Path(td) / "evidence" / "claims" / "claim-proj-doc-md-000.md"
            # the repaired quote (backtick-elision repaired earlier) with status
            # still contested — the exact post-repair state the audit found
            cp.write_text(
                "---\ntype: claim\nstatus: contested\n"
                "source_refs:\n  - source: \"[[src-proj-doc-md]]\"\n"
                "    locator: \"L2\"\n"
                "    quote: \"the quote is here\"\n"
                "    supports: true\n---\n\n# c\n")
            old = rv.CORPUS_ROOT
            rv.CORPUS_ROOT = Path(td)
            try:
                r = rv.verify_locators(dry_run=False)
                text = cp.read_text()
            finally:
                rv.CORPUS_ROOT = old
            assert r["kept"] == 1
            assert "status: supported" in text
            assert "process:locator-verification" in text
