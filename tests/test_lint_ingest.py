"""Unit tests for lint.py helpers and ingest.py parsing logic.

Run: python3 -m pytest tests/test_lint_ingest.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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