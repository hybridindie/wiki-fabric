"""One statement parser + one frontmatter writer (#154).

12 regex copies of `statement: "?([^\n]+)` drifted into two incompatible
variants (some tolerated unquoted, eval-stability required quotes); a
legitimate frontmatter format change (statement: | block scalars) would
have silently broken ~11 consumers. All now route through
wf_common.claim_statement / wf_common.dump_frontmatter + write_frontmatter,
and a source-level guard keeps the copies from returning."""

import sys
import tempfile
import unittest
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

from wf_common import claim_statement, dump_frontmatter, write_frontmatter, parse_frontmatter


def _page(statement_block):
    return ("---\ntype: claim\nid: claim-x\n" + statement_block +
            "status: supported\n---\n\nBody.")


class TestClaimStatement(unittest.TestCase):
    def test_quoted_inline(self):
        s = claim_statement(_page('statement: "A quoted statement."\n'))
        self.assertEqual(s, "A quoted statement.")

    def test_bare_inline(self):
        s = claim_statement(_page("statement: A bare, unquoted statement.\n"))
        self.assertEqual(s, "A bare, unquoted statement.")

    def test_block_literal(self):
        s = claim_statement(_page("statement: |\n  Line one.\n  Line two.\n"))
        self.assertEqual(s, "Line one.\nLine two.")

    def test_block_folded(self):
        s = claim_statement(_page("statement: >\n  Folded line one\n  folded line two.\n"))
        self.assertEqual(s, "Folded line one folded line two.")

    def test_absent_is_empty(self):
        self.assertEqual(claim_statement("---\ntype: claim\n---\n\nBody."), "")

    def test_body_statement_not_grabbed(self):
        # only the frontmatter key line counts, not prose in the body
        self.assertEqual(claim_statement("---\ntype: claim\n---\n\nstatement: in body"), "")

    def test_path_input(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write(_page('statement: "Path-read statement."\n'))
            p = Path(f.name)
        self.assertEqual(claim_statement(p), "Path-read statement.")


class TestDumpFrontmatterRoundTrip(unittest.TestCase):
    def test_round_trip_preserves_scalars(self):
        import yaml
        fm = {
            "type": "pattern", "id": "pattern-x",
            "title": 'A "quoted" title',
            "applicability": ["long scalar " * 30],
            "statement": "line one\nline two",
            "counterexamples": [{"why": "b", "what": "a"}],
        }
        page = Path(tempfile.mkdtemp()) / "p.md"
        write_frontmatter(page, fm, "# body\n")
        back_fm, body = parse_frontmatter(page)
        self.assertEqual(back_fm, fm)
        self.assertEqual(body, "# body\n")
        # one dump convention: long scalars NEVER wrap (width=10**6)
        text = page.read_text()
        for line in text.splitlines():
            if line.startswith("  - long scalar"):
                self.assertGreater(len(line), 100)

    def test_dump_preserves_key_order(self):
        out = dump_frontmatter({"zeta": 1, "alpha": 2})
        self.assertLess(out.index("zeta"), out.index("alpha"))


class TestNoDuplicateStatementParsers(unittest.TestCase):
    """Drift guard: the 12 inline regex copies must stay replaced."""

    def test_no_inline_statement_regexes(self):
        offenders = []
        for s in _SCRIPTS.rglob("*.py"):
            if s.name == "wf_common.py" or "__pycache__" in s.parts:
                continue
            text = s.read_text()
            if "wf_common" not in text and 'statement: "?([^\\n]+)' in text:
                offenders.append(s.name)
        self.assertEqual(offenders, [])

    def test_all_consumers_route_through_shared_parser(self):
        expected = (
            "generators.py", "embed_index.py", "deepdives.py",
            "verify-effects.py", "eval-stability.py",
        )
        missing = []
        for name in expected:
            found = False
            for s in _SCRIPTS.rglob(name):
                if "__pycache__" in s.parts or "_harness" in s.parts:
                    continue
                if "claim_statement" in s.read_text():
                    found = True
                    break
            if not found:
                missing.append(name)
        self.assertEqual(missing, [])

    def test_frontmatter_writers_route_through_shared_dump(self):
        """One dump convention (#154): no script re-implements yaml.dump for
        frontmatter with its own option set."""
        offenders = []
        for s in _SCRIPTS.rglob("*.py"):
            if s.name == "wf_common.py" or "__pycache__" in s.parts:
                continue
            text = s.read_text()
            if "yaml.dump(" in text or "yaml.safe_dump(" in text:
                offenders.append(s.name)
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()