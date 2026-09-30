"""#155 wave-3 consolidation guards: one corpus walk, one owner chain,
one relation vocabulary, and dispatch's integration check.

These pin the consumers to the shared implementations — the source-level
guards mirror test_wf_common's no-duplicate pattern."""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))
sys.path.insert(0, str(REPO / "src"))

import wf_common


class TestCorpusWalk(unittest.TestCase):
    """155-C: context/query/rebuild-index share the walk."""

    def test_walk_excludes_generated_and_runtime_dirs(self):
        with __import__("tempfile").TemporaryDirectory() as td:
            root = Path(td)
            keep = root / "evidence" / "claims" / "claim-x.md"
            keep.parent.mkdir(parents=True)
            keep.write_text("---\ntype: claim\n---\n\nx\n")
            (root / "wiki" / "w.md").parent.mkdir(parents=True)
            (root / "wiki" / "w.md").write_text("x")
            (root / ".venv" / "v.md").parent.mkdir(parents=True)
            (root / ".venv" / "v.md").write_text("x")
            got = [p.name for p, _, _ in wf_common.corpus_walk(root)]
            self.assertEqual(got, ["claim-x.md"])

    def test_walk_yields_triple(self):
        with __import__("tempfile").TemporaryDirectory() as td:
            root = Path(td)
            p = root / "patterns" / "pattern-a.md"
            p.parent.mkdir(parents=True)
            p.write_text("x")
            items = list(wf_common.corpus_walk(root))
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0][2].as_posix(), "patterns/pattern-a.md")

    def test_no_private_skip_sets_remain(self):
        offenders = []
        for s in _SCRIPTS.rglob("*.py"):
            if s.name in ("wf_common.py",) or "__pycache__" in s.parts:
                continue
            text = s.read_text()
            if "SKIP_PARTS = {" in text:
                offenders.append(s.name)
        self.assertEqual(offenders, [])

    def test_consumers_reference_shared_walk(self):
        for name in ("context.py", "query.py"):
            found = False
            for s in _SCRIPTS.rglob(name):
                if "__pycache__" in s.parts or "_harness" in s.parts:
                    continue
                if "corpus_walk" in s.read_text():
                    found = True
                    break
            self.assertTrue(found, f"{name} must use wf_common.corpus_walk")


class TestOwnerChain(unittest.TestCase):
    """155-B: one chain, one sentinel."""

    def test_get_owner_sentinel(self):
        import unittest.mock as um
        import fabric_config as fc
        self.assertEqual(fc.OWNER_SENTINEL, "you")
        # no config, no git: sentinel
        with unittest.mock.patch.object(fc, "detect_owner_fallback", lambda: None):
            self.assertEqual(fc.get_owner({}), "you")

    def test_get_owner_git_fallback(self):
        import unittest.mock as um
        import fabric_config as fc
        with unittest.mock.patch.object(fc, "detect_owner_fallback", lambda: "gituser"):
            self.assertEqual(fc.get_owner({}), "gituser")
            self.assertEqual(fc.get_owner({"owner": "cfguser"}), "cfguser")


class TestRelVocabulary(unittest.TestCase):
    """155-E: judgment effects ⊆ lint REL_TYPES."""

    def test_effects_subset_of_lint(self):
        import judgment as j
        try:
            from lint import REL_TYPES
        except Exception:
            self.skipTest("lint not importable here")
        # no-action is the tier's abstention verdict, not a corpus relation
        effects = set(j.EFFECT_OPTIONS) - j._REL_EXEMPT
        unknown = effects - set(REL_TYPES)
        self.assertEqual(unknown, set(),
                         f"judgment effects outside the relation vocabulary: {unknown}")

    def test_contract_function(self):
        import judgment as j
        ok, detail = j.effect_options_subset_of_lint()
        self.assertTrue(ok, detail)


class TestDispatchIntegrations(unittest.TestCase):
    """155-A: the report answers from the config layer, and no dead
    regex-grep copy remains."""

    def test_no_regex_grep_enabled(self):
        text = (REPO / "src" / "wiki_fabric" / "dispatch.py").read_text()
        self.assertNotIn("def _enabled(name: str, yaml_text", text)
        self.assertIn("is_integration_active", text)


if __name__ == "__main__":
    unittest.main()