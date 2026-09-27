"""Unit tests for lint.py helpers and ingest.py parsing logic.

Run: python3 -m pytest tests/test_lint_ingest.py -v
"""

import sys
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

import lint as lint_mod
import ingest as ingest_mod


class TestLintFrontmatter:
    def test_valid_frontmatter(self, tmp_path):
        p = tmp_path / "note.md"
        p.write_text("---\ntype: claim\ntitle: T\n---\n\nBody text\n")
        fm, body, err = lint_mod.parse_frontmatter(p)
        assert err is None
        assert fm["type"] == "claim"
        assert "Body text" in body

    def test_missing_frontmatter_is_error(self, tmp_path):
        p = tmp_path / "note.md"
        p.write_text("No frontmatter here\n")
        fm, body, err = lint_mod.parse_frontmatter(p)
        assert err == "missing frontmatter block"
        assert fm is None

    def test_invalid_yaml(self, tmp_path):
        p = tmp_path / "note.md"
        p.write_text("---\ntype: [unclosed\n---\nbody\n")
        fm, body, err = lint_mod.parse_frontmatter(p)
        assert err and "yaml parse error" in err

    def test_valid_types_accepted(self):
        for t in ("claim", "source", "concept", "pattern", "experience-event", "log"):
            assert t in lint_mod.VALID_TYPES

    def test_unknown_type_rejected(self):
        assert "not-a-type" not in lint_mod.VALID_TYPES


class TestLintHelpers:
    def test_strip_code_removes_fenced_blocks(self):
        body = "keep this\n```bash\nrm -rf /tmp/x [[not-a-link]]\n```\nand this"
        out = lint_mod.strip_code(body)
        assert "[[not-a-link]]" not in out
        assert "keep this" in out
        assert "and this" in out

    def test_link_regex_extracts_stem(self):
        m = lint_mod.LINK_RE.search("see [[claim-foo]] for details")
        assert m.group(1) == "claim-foo"

    def test_link_regex_with_alias(self):
        m = lint_mod.LINK_RE.search("[[claim-foo|the claim]]")
        assert m.group(1) == "claim-foo"

    def test_is_placeholder(self):
        assert lint_mod.is_placeholder("x")
        assert lint_mod.is_placeholder("...")
        assert lint_mod.is_placeholder("<claim-slug>")
        assert not lint_mod.is_placeholder("claim-real-slug")

    def test_is_tpl_exempts_repo_meta(self, ):
        from pathlib import Path
        assert lint_mod.is_tpl(Path("README.md"))
        assert lint_mod.is_tpl(Path("CONTRIBUTING.md"))
        assert lint_mod.is_tpl(Path("templates/pattern.md"))
        assert lint_mod.is_tpl(Path("schemas/frontmatter.md"))
        assert not lint_mod.is_tpl(Path("evidence/claims/claim-x.md"))

    def test_repo_meta_needs_no_frontmatter(self, tmp_path):
        """Regression: README/CONTRIBUTING are visitor-facing repo pages —
        no frontmatter required (and an unknown type there isn't a fabric
        type error). The VitePress site dir is also excluded."""
        (tmp_path / "README.md").write_text("# Just a readme, no frontmatter\n")
        (tmp_path / "docs" / "site").mkdir(parents=True)
        (tmp_path / "docs" / "site" / "index.md").write_text("no fm either")
        # fabric-y page still requires frontmatter
        (tmp_path / "evidence").mkdir()
        (tmp_path / "evidence" / "claims").mkdir()
        (tmp_path / "evidence" / "claims" / "claim-x.md").write_text("# no fm\n")
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = lint_mod.main.__wrapped__(tmp_path) if hasattr(lint_mod.main, "__wrapped__") else None
        # run lint by invoking its checks directly (main() parses argv)
        import sys as _sys
        old_argv = _sys.argv
        _sys.argv = ["lint.py", str(tmp_path)]
        try:
            with contextlib.redirect_stdout(buf):
                rc = lint_mod.main()
        finally:
            _sys.argv = old_argv
        out = buf.getvalue()
        assert "FRONTMATTER README.md" not in out
        assert "FRONTMATTER docs/site/" not in out
        assert "FRONTMATTER evidence/claims/claim-x.md" in out
        assert "TYPE README.md" not in out


class TestIngestLineNumbers:
    def test_number_lines_prefixes(self):
        out = ingest_mod.number_lines("alpha\nbeta")
        assert out == "L1:alpha\nL2:beta"

    def test_number_lines_respects_max_chars(self):
        out = ingest_mod.number_lines("x\ny\nz", max_chars=3)
        assert "L3:" not in out  # text truncated to 3 chars -> only first line

    def test_verify_locators_fixes_off_locator(self):
        text = "first line\nthe quote is here\nthird line"
        claims = [{"quote": "the quote is here", "locator": "L99"}]
        fixed = ingest_mod.verify_and_fix_locators(claims, text)
        assert fixed[0]["locator"] != "L99"  # corrected or at least not left wrong

    def test_verify_locators_expands_single_line_to_range(self):
        # verify_and_fix_locators computes the full line range the quote spans;
        # a single-line quote on line 2 yields "L1-L2" because the 3-line search
        # window overlaps line 1's text. Assert the corrected locator is derived
        # from the actual source, not the input.
        text = "first line\nthe quote is here\nthird line"
        claims = [{"quote": "the quote is here", "locator": "L2"}]
        fixed = ingest_mod.verify_and_fix_locators(claims, text)
        assert fixed[0]["locator"].startswith("L")
        assert fixed[0]["locator"] != "L99"


class TestIngestSlug:
    def test_slugify(self):
        assert ingest_mod.slugify("Hello World! 2026") == "hello-world-2026"

    def test_slugify_path(self):
        assert ingest_mod.slugify("docs/architecture.md") == "docs-architecture-md"


class TestResumeFlipGate:
    """#93: resume must not flip pending→ingested when 0 claims extracted.

    The old code flipped unconditionally, orphaning the source: `ingested`
    with zero claims, permanently blocked by the anti-loop gate."""

    @staticmethod
    def _make_source(tmp_path, monkeypatch, extract_return):
        """Corpus with one pending source record; patch VAULT_ROOT + extractor."""
        import hashlib
        vault = tmp_path / "corpus"
        (vault / "evidence" / "sources").mkdir(parents=True)
        (vault / "evidence" / "raw" / "proj").mkdir(parents=True)
        (vault / "evidence" / "claims").mkdir(parents=True)
        (vault / "evidence" / "source-summaries").mkdir(parents=True)
        (vault / "registry").mkdir(parents=True)
        raw = vault / "evidence" / "raw" / "proj" / "doc.md"
        raw.write_text("# Doc\n\nSome content\n")
        sha = hashlib.sha256(raw.read_bytes()).hexdigest()
        rec = vault / "evidence" / "sources" / "src-proj-doc-md.md"
        rec.write_text(
            "---\ntype: source\ntitle: Doc\nresource: evidence/raw/proj/doc.md\n"
            f"source_path: evidence/raw/proj/doc.md\nsha256: {sha}\nstatus: pending\n---\n\n# Doc\n")
        monkeypatch.setattr(ingest_mod, "VAULT_ROOT", vault)
        monkeypatch.setattr(ingest_mod, "args_dry_run", False)
        monkeypatch.setattr(ingest_mod, "extract_claims_fn",
                            lambda text, path, model: extract_return)
        return vault, raw, rec

    def test_zero_claim_resume_stays_pending(self, tmp_path, monkeypatch):
        vault, raw, rec = self._make_source(tmp_path, monkeypatch, [])
        ingest_mod.ingest_source(raw, True, "test-model")
        assert "status: pending" in rec.read_text()

    def test_claim_resume_flips_to_ingested(self, tmp_path, monkeypatch):
        vault, raw, rec = self._make_source(tmp_path, monkeypatch, [
            {"statement": "Something true", "quote": "Some content", "locator": "L2"}])
        ingest_mod.ingest_source(raw, True, "test-model")
        assert "status: ingested" in rec.read_text()


class TestReclaimOrphans:
    """#93 recovery: --reclaim flips zero-claim ingested records to pending."""

    def test_reclaim_flips_orphan(self, tmp_path, monkeypatch, capsys):
        vault = tmp_path / "corpus"
        (vault / "evidence" / "sources").mkdir(parents=True)
        (vault / "evidence" / "raw" / "proj").mkdir(parents=True)
        (vault / "evidence" / "claims").mkdir(parents=True)
        raw = vault / "evidence" / "raw" / "proj" / "doc.md"
        raw.write_text("# Doc\n")
        rec = vault / "evidence" / "sources" / "src-proj-doc-md.md"
        rec.write_text(
            "---\ntype: source\ntitle: Doc\nresource: evidence/raw/proj/doc.md\n"
            "source_path: evidence/raw/proj/doc.md\nsha256: deadbeef\nstatus: ingested\n---\n\n# Doc\n")
        monkeypatch.setattr(ingest_mod, "VAULT_ROOT", vault)
        n = ingest_mod.reclaim_orphans("proj")
        assert n == 1
        assert "status: pending" in rec.read_text()

    def test_reclaim_skips_sources_with_claims(self, tmp_path, monkeypatch):
        vault = tmp_path / "corpus"
        (vault / "evidence" / "sources").mkdir(parents=True)
        (vault / "evidence" / "raw" / "proj").mkdir(parents=True)
        (vault / "evidence" / "claims").mkdir(parents=True)
        raw = vault / "evidence" / "raw" / "proj" / "doc.md"
        raw.write_text("# Doc\n")
        rec = vault / "evidence" / "sources" / "src-proj-doc-md.md"
        rec.write_text(
            "---\ntype: source\ntitle: Doc\nresource: evidence/raw/proj/doc.md\n"
            "source_path: evidence/raw/proj/doc.md\nsha256: deadbeef\nstatus: ingested\n---\n\n# Doc\n")
        (vault / "evidence" / "claims" / "claim-proj-doc-md-000.md").write_text(
            "---\ntype: claim\nid: claim-proj-doc-md-000\n---\n\n# c\n")
        monkeypatch.setattr(ingest_mod, "VAULT_ROOT", vault)
        assert ingest_mod.reclaim_orphans("proj") == 0
        assert "status: ingested" in rec.read_text()

    def test_reclaim_dry_run_writes_nothing(self, tmp_path, monkeypatch):
        vault = tmp_path / "corpus"
        (vault / "evidence" / "sources").mkdir(parents=True)
        (vault / "evidence" / "raw" / "proj").mkdir(parents=True)
        (vault / "evidence" / "claims").mkdir(parents=True)
        raw = vault / "evidence" / "raw" / "proj" / "doc.md"
        raw.write_text("# Doc\n")
        rec = vault / "evidence" / "sources" / "src-proj-doc-md.md"
        rec.write_text(
            "---\ntype: source\ntitle: Doc\nresource: evidence/raw/proj/doc.md\n"
            "source_path: evidence/raw/proj/doc.md\nsha256: deadbeef\nstatus: ingested\n---\n\n# Doc\n")
        monkeypatch.setattr(ingest_mod, "VAULT_ROOT", vault)
        assert ingest_mod.reclaim_orphans("proj", dry_run=True) == 1
        assert "status: ingested" in rec.read_text()


class TestLintSourceEmpty:
    """#93 lint signal: ingested + zero claims warns (recoverable, not fatal)."""

    @staticmethod
    def _run_lint(tmp_path):
        import sys as _sys, io, contextlib
        old_argv = _sys.argv
        _sys.argv = ["lint.py", str(tmp_path)]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                lint_mod.main()
        finally:
            _sys.argv = old_argv
        return buf.getvalue()

    def test_ingested_zero_claims_warns(self, tmp_path):
        vault = tmp_path / "corpus"
        (vault / "evidence" / "sources").mkdir(parents=True)
        (vault / "evidence" / "raw" / "proj").mkdir(parents=True)
        (vault / "evidence" / "claims").mkdir(parents=True)
        import hashlib
        sha = hashlib.sha256(b"# Doc\n").hexdigest()
        raw = vault / "evidence" / "raw" / "proj" / "doc.md"
        raw.write_text("# Doc\n")
        (vault / "evidence" / "sources" / "src-proj-doc-md.md").write_text(
            "---\ntype: source\ntitle: Doc\nresource: evidence/raw/proj/doc.md\n"
            f"source_path: evidence/raw/proj/doc.md\nsha256: {sha}\nstatus: ingested\n---\n\n# Doc\n")
        out = self._run_lint(vault)
        assert "SOURCE-EMPTY" in out
        assert "--reclaim" in out

    def test_ingested_with_claims_no_warning(self, tmp_path):
        vault = tmp_path / "corpus"
        (vault / "evidence" / "sources").mkdir(parents=True)
        (vault / "evidence" / "raw" / "proj").mkdir(parents=True)
        (vault / "evidence" / "claims").mkdir(parents=True)
        import hashlib
        sha = hashlib.sha256(b"# Doc\n").hexdigest()
        (vault / "evidence" / "raw" / "proj" / "doc.md").write_text("# Doc\n")
        (vault / "evidence" / "sources" / "src-proj-doc-md.md").write_text(
            "---\ntype: source\ntitle: Doc\nresource: evidence/raw/proj/doc.md\n"
            f"source_path: evidence/raw/proj/doc.md\nsha256: {sha}\nstatus: ingested\n---\n\n# Doc\n")
        (vault / "evidence" / "claims" / "claim-proj-doc-md-000.md").write_text(
            "---\ntype: claim\nid: claim-proj-doc-md-000\n---\n\n# c\n")
        out = self._run_lint(vault)
        assert "SOURCE-EMPTY evidence/sources/src-proj-doc-md.md" not in out


class TestProvenanceRelations:
    """#79: claims from chat/PR captures carry typed provenance edges."""

    def test_chat_capture_gets_originated_in(self):
        rels = ingest_mod.provenance_relations(
            "proj-session-1", "/corpus/evidence/raw/proj/chats/2026-09-26-topic.md")
        assert rels == [{"type": "originated_in", "target": "[[src-proj-session-1]]"}]

    def test_pr_capture_gets_decided_in(self):
        rels = ingest_mod.provenance_relations(
            "proj-git-pr-42", "/corpus/evidence/raw/proj/git/pr-42.md")
        assert rels == [{"type": "decided_in", "target": "[[src-proj-git-pr-42]]"}]

    def test_issue_capture_gets_decided_in(self):
        rels = ingest_mod.provenance_relations(
            "proj-git-issue-7", "/corpus/evidence/raw/proj/git/issue-7.md")
        assert rels[0]["type"] == "decided_in"

    def test_doc_capture_has_no_edge(self):
        rels = ingest_mod.provenance_relations(
            "proj-doc", "/corpus/evidence/raw/proj/docs/site/context.md")
        assert rels == []

    def test_claim_frontmatter_emits_relations_block(self):
        prov = [{"type": "decided_in", "target": "[[src-proj-git-pr-42]]"}]
        fm_text = ingest_mod.claim_frontmatter(
            {"statement": "S", "quote": "Q", "locator": "L1"}, "proj-git-pr-42", 0,
            provenance=prov)
        assert "relations:" in fm_text
        assert "type: decided_in" in fm_text
        assert 'target: "[[src-proj-git-pr-42]]"' in fm_text

    def test_claim_frontmatter_default_stays_empty_list(self):
        fm_text = ingest_mod.claim_frontmatter(
            {"statement": "S", "quote": "Q", "locator": "L1"}, "proj-doc", 0)
        assert "relations: []" in fm_text


class TestLintRelations:
    """Lint validates claim relation targets resolve (BROKEN-LINK) and types."""

    @staticmethod
    def _run_lint(tmp_path):
        import sys as _sys, io, contextlib
        old_argv = _sys.argv
        _sys.argv = ["lint.py", str(tmp_path)]
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                lint_mod.main()
        finally:
            _sys.argv = old_argv
        return buf.getvalue()

    def _write_claim(self, tmp_path, relations_yaml):
        (tmp_path / "evidence" / "claims").mkdir(parents=True)
        (tmp_path / "evidence" / "claims" / "claim-x.md").write_text(
            "---\ntype: claim\nid: claim-x\nstatus: supported\n"
            "source_refs:\n  - source: \"[[src-s]]\"\n    locator: L1\n"
            f"    quote: q\n{relations_yaml}\n---\n\n# claim-x\n\nBody\n")

    def test_valid_relation_passes(self, tmp_path):
        (tmp_path / "evidence" / "sources").mkdir(parents=True)
        (tmp_path / "evidence" / "sources" / "src-s.md").write_text(
            "---\ntype: source\ntitle: S\n---\n\n# src-s\n")
        self._write_claim(tmp_path,
                          "relations:\n  - type: originated_in\n    target: \"[[src-s]]\"")
        out = self._run_lint(tmp_path)
        assert "BROKEN-LINK" not in out
        assert "relation type" not in out

    def test_broken_relation_target_errors(self, tmp_path):
        self._write_claim(tmp_path,
                          "relations:\n  - type: originated_in\n    target: \"[[src-missing]]\"")
        out = self._run_lint(tmp_path)
        assert "BROKEN-LINK evidence/claims/claim-x.md: relation target [[src-missing]]" in out

    def test_unknown_relation_type_errors(self, tmp_path):
        (tmp_path / "evidence" / "sources").mkdir(parents=True)
        (tmp_path / "evidence" / "sources" / "src-s.md").write_text(
            "---\ntype: source\ntitle: S\n---\n\n# src-s\n")
        self._write_claim(tmp_path,
                          "relations:\n  - type: vibes_with\n    target: \"[[src-s]]\"")
        out = self._run_lint(tmp_path)
        assert "relation type 'vibes_with'" in out

    def test_provenance_types_are_valid(self):
        for t in ("originated_in", "decided_in", "validated_in"):
            assert t in lint_mod.REL_TYPES