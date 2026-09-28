"""Unit tests for chat-mined pattern candidates (#89).

Run: python3 -m pytest tests/test_mine_inbox.py -v
"""

import sys
import importlib.util
from pathlib import Path
from unittest import mock

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


mc = _load("mine_chats_i", Path(__file__).parent.parent / "scripts/cmd/mine-chats.py")
pp = _load("promote_patterns", Path(__file__).parent.parent / "scripts/cmd/promote-patterns.py")


TAKEAWAYS = [
    {"kind": "pattern", "statement": "Serialize writes to single-writer systems", "rationale": "two sessions"},
    {"kind": "anti-pattern", "statement": "Parallel writes to one queue corrupt ordering"},
    {"kind": "transient", "statement": "CI green at 3pm"},
    {"kind": "workflow", "statement": "Run lint before commit"},
]


class TestProposeCandidates:
    def _run(self, tmp_path, dry_run=False):
        raw = tmp_path / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        (tmp_path / "evidence" / "insights").mkdir(parents=True, exist_ok=True)
        tp = tmp_path / "transcript.md"
        tp.write_text("# Chat session ses-demo\n")
        with mock.patch.object(mc, "CORPUS_ROOT", tmp_path):
            return mc.propose_candidates(tp, TAKEAWAYS, dry_run=dry_run, project="proj"), tp

    def test_pattern_and_antipattern_staged(self, tmp_path):
        n, _ = self._run(tmp_path)
        assert n == 2  # pattern + anti-pattern; transient/workflow not staged as pattern candidates
        inbox = tmp_path / "patterns" / "_inbox"
        pages = list(inbox.glob("*.md"))
        assert len(pages) == 2
        text = pages[0].read_text()
        assert "status: candidate" in text
        assert "maturity: 1" in text
        assert "origin: chat-mined" in text
        assert "source_chat:" in text  # provenance in frontmatter
        assert "provenance:" in text

    def test_idempotent(self, tmp_path):
        n1, _ = self._run(tmp_path)
        n2, _ = self._run(tmp_path)
        assert n1 == 2 and n2 == 0
        assert len(list((tmp_path / "patterns" / "_inbox").glob("*.md"))) == 2

    def test_dry_run_writes_nothing(self, tmp_path):
        n, _ = self._run(tmp_path, dry_run=True)
        assert n == 2
        assert not (tmp_path / "patterns" / "_inbox").exists() or \
            not list((tmp_path / "patterns" / "_inbox").glob("*.md"))


class TestPromotePatterns:
    def _staged(self, tmp_path):
        raw = tmp_path / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        with mock.patch.object(mc, "CORPUS_ROOT", tmp_path):
            mc.propose_candidates(tmp_path / "transcript.md", TAKEAWAYS, project="proj")
        pages = sorted((tmp_path / "patterns" / "_inbox").glob("*.md"))
        return pages

    def test_list_pending(self, tmp_path):
        pages = self._staged(tmp_path)
        with mock.patch.object(pp, "INBOX_DIR", tmp_path / "patterns" / "_inbox"):
            pending = pp.list_pending()
        assert len(pending) == 2
        assert pending[0][1]["status"] == "candidate"

    def test_apply_moves_to_patterns(self, tmp_path):
        pages = self._staged(tmp_path)
        with mock.patch.object(pp, "INBOX_DIR", tmp_path / "patterns" / "_inbox"), \
                mock.patch.object(pp, "PATTERNS_DIR", tmp_path / "patterns"):
            assert pp.apply_candidate(pages[0])
            assert not pages[0].exists()
            dest = tmp_path / "patterns" / pages[0].name
            assert dest.exists()
            assert "chat-mined" in dest.read_text()
            assert "inbox]" not in dest.read_text()

    def test_reject_requires_reason(self, tmp_path):
        pages = self._staged(tmp_path)
        with mock.patch.object(pp, "INBOX_DIR", tmp_path / "patterns" / "_inbox"), \
                mock.patch.object(pp, "CORPUS_ROOT", tmp_path):  # tombstone must not hit the real fabric (#140)
            assert not pp.reject_candidate(pages[0].stem, "")
            assert pages[0].exists()
            assert pp.reject_candidate(pages[0].stem, "out of scope")
            assert not pages[0].exists()

    def test_apply_dry_run_writes_nothing(self, tmp_path):
        pages = self._staged(tmp_path)
        with mock.patch.object(pp, "INBOX_DIR", tmp_path / "patterns" / "_inbox"), \
                mock.patch.object(pp, "PATTERNS_DIR", tmp_path / "patterns"):
            assert pp.apply_candidate(pages[0], dry_run=True)
            assert pages[0].exists()
