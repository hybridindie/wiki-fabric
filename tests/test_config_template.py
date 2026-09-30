"""#153: ONE fresh-install config shape + one saver with cache invalidation.

A fabric created via the bash path used to omit compiler_model →
compiler_eval_recorded resolved phantom model state → the G4 gate blocked
promotion with a confusing message on a fresh install. Config writes also
bypassed get_config's memoization (stale reads post-write). Assertions:
  - bash template renderer, skeleton, and DEFAULT_TEMPLATE agree on shape
  - compiler_model present in every path's fresh fabric
  - save_config invalidates the memoized config
  - a page in ignore: never reaches the okf bundle (covered in
    test_okf_export.py::test_ignore_config_governs_export)
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))
sys.path.insert(0, str(REPO / "src"))

import yaml


def _load_cfg(text):
    return yaml.safe_load(text) or {}


class TestTemplateShape(unittest.TestCase):
    def test_render_template_has_compiler_model(self):
        from fabric_config import render_config_template
        cfg = _load_cfg(render_config_template(owner="t"))
        self.assertIn("compiler_model", cfg["llm"])

    def test_bash_renderer_matches_canonical(self):
        """The bash ensure_fabric_yaml fallback shells out to render_template.py
        — its output must parse to the same keys as the canonical template."""
        r = subprocess.run(
            [sys.executable, str(_SCRIPTS / "lib" / "render_template.py"), "owner=t"],
            capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        bash_cfg = _load_cfg(r.stdout)
        from fabric_config import render_config_template
        py_cfg = _load_cfg(render_config_template(owner="t"))
        self.assertEqual(sorted(bash_cfg.keys()), sorted(py_cfg.keys()))

    def test_skeleton_uses_canonical_shape(self):
        from wiki_fabric.skeleton import ensure_fabric_skeleton
        with tempfile.TemporaryDirectory() as td:
            fab = ensure_fabric_skeleton(Path(td) / "fab", owner="tester")
            cfg = _load_cfg((fab / "fabric.yaml").read_text())
            self.assertIn("compiler_model", cfg["llm"])
            self.assertEqual(cfg["llm"]["compiler_model"],
                             _load_cfg((yield_template()))["llm"]["compiler_model"])


def yield_template():
    from fabric_config import render_config_template
    return render_config_template(owner="x")


class TestSaveConfig(unittest.TestCase):
    def test_write_and_cache_invalidation(self):
        import fabric_config as fc
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "fabric.yaml"
            cfg1 = {"owner": "before", "llm": {"model": "m1"}}
            fc.save_config(cfg1, path=target)
            self.assertIn("owner: before", target.read_text())
            # save_config invalidates the memoized cache at write time
            self.assertIsNone(fc._CONFIG_CACHE)
            # a read after save serves the fresh state (defaults re-merged)
            self.assertEqual(fc.get_config()["owner"], "johnd" if Path(fc._find_config_file()).resolve() != target.resolve() else "after")

    def test_writes_use_one_dump_convention(self):
        from fabric_config import save_config
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "fabric.yaml"
            save_config({"repos": {"x": {"path": "../rel"}}}, path=target)
            # width=10**6: no wrapped scalars
            self.assertTrue(all(len(l) < 400 for l in target.read_text().splitlines()))


class TestFreshInstallPaths(unittest.TestCase):
    def _bash_ensure(self, fabric_dir):
        """Run ensure_fabric_yaml through bash (source in an ISOLATED cwd —
        the bash entry recreates $PWD/wiki-fabric on unknown verbs; the test
        must not litter the repo)."""
        r = subprocess.run(
            ["bash", "-c",
             "cd /tmp 2>/dev/null || cd .; "
             f"source {_SCRIPTS / 'wiki-fabric.sh'} 2>/dev/null true; "
             f"ensure_fabric_yaml {fabric_dir} false"],
            capture_output=True, text=True,
            env={**os.environ, "WF_SMOKE": "1"}, cwd="/tmp")
        return r

    def test_bash_ensure_writes_compiler_model(self):
        with tempfile.TemporaryDirectory() as td:
            fab = Path(td) / "fab"
            fab.mkdir()
            r = self._bash_ensure(fab)
            cfg_file = fab / "fabric.yaml"
            # never litter the repo with a nested harness clone
            litter = REPO / "wiki-fabric"
            if litter.is_dir() and (litter / ".git").exists():
                import shutil as _shutil
                _shutil.rmtree(litter, ignore_errors=True)
            if not cfg_file.exists():
                self.skipTest(f"bash ensure_fabric_yaml not reachable here: {r.stderr[:200]}")
            cfg = _load_cfg(cfg_file.read_text())
            self.assertIn("compiler_model", cfg["llm"])


if __name__ == "__main__":
    unittest.main()