"""One resolution suite (#152): all fabric/vault/corpus/harness resolvers
must agree for a given environment. Drift between copies made status/doctor/
refresh audit different trees on the same machine — these assertions pin the
consumers to scripts/lib/paths.py primitives."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import paths


class TestMarkers(unittest.TestCase):
    def test_fabric_markers(self):
        # corpus/ marker is load-bearing (dispatch's copy dropped it — #152)
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            assert not paths.is_fabric_dir(d)
            (d / "corpus").mkdir()
            assert paths.is_fabric_dir(d)

    def test_harness_tree(self):
        assert paths.is_harness_tree(_SCRIPTS.parent)


class TestChainAgreement(unittest.TestCase):
    """fabric_config's canonical chain and the primitives agree."""

    def test_corpus_resolution_matches_fabric_config(self):
        from fabric_config import CORPUS_ROOT, FABRIC_ROOT
        # canonical constants are composed from the same primitive
        assert CORPUS_ROOT == paths.find_corpus_root(FABRIC_ROOT)

    def test_legacy_layout_roundtrip(self):
        # paths.find_corpus_root: legacy (content at root) vs nested vs fresh
        with tempfile.TemporaryDirectory() as td:
            legacy = Path(td) / "legacy"
            (legacy / "evidence").mkdir(parents=True)
            assert paths.find_corpus_root(legacy) == legacy.resolve()
            nested = Path(td) / "nested"
            (nested / "corpus" / "evidence").mkdir(parents=True)
            assert paths.find_corpus_root(nested) == (nested / "corpus").resolve()
            fresh = Path(td) / "fresh"
            fresh.mkdir()
            assert paths.find_corpus_root(fresh) == (fresh / "corpus").resolve()


class TestVaultAgreement(unittest.TestCase):
    """dispatch._vault_dir and get_vault_path agree for a given fabric dir."""

    def test_env_override_wins_everywhere(self):
        import wiki_fabric.dispatch as dispatch
        from paths import find_vault_dir_for_fabric
        with tempfile.TemporaryDirectory() as td:
            fab = Path(td) / "fab"
            fab.mkdir()
            target = Path(td) / "explicit-vault"
            target.mkdir()
            old = os.environ.get("WIKI_FABRIC_VAULT")
            try:
                os.environ["WIKI_FABRIC_VAULT"] = str(target)
                assert find_vault_dir_for_fabric(fab) == target.resolve()
                assert dispatch._vault_dir(fab) == target.resolve()
            finally:
                if old is None:
                    os.environ.pop("WIKI_FABRIC_VAULT", None)
                else:
                    os.environ["WIKI_FABRIC_VAULT"] = old

    def test_vault_path_in_yaml(self):
        from paths import find_vault_dir_for_fabric
        with tempfile.TemporaryDirectory() as td:
            fab = Path(td) / "fab"
            fab.mkdir()
            (fab / "fabric.yaml").write_text("vault:\n  path: out/vault\n")
            assert find_vault_dir_for_fabric(fab) == (fab / "out/vault").resolve()

    def test_fallback_is_fabric_itself(self):
        from paths import find_vault_dir_for_fabric
        with tempfile.TemporaryDirectory() as td:
            fab = Path(td) / "fab"
            fab.mkdir()
            assert find_vault_dir_for_fabric(fab) == fab


class TestHarnessAgreement(unittest.TestCase):
    def test_dispatch_harness_matches_paths_shape(self):
        """Dev checkout: both resolvers land on the repo root — unless a
        stale prep-package staging copy exists in the dev tree (build
        artifact; release flow re-stages it, publish.yml)."""
        import wiki_fabric.dispatch as dispatch
        p_root = paths.find_harness_root()
        d_root = dispatch.harness_root()
        assert p_root == d_root or (
            (d_root / "scripts" / "wiki-fabric.sh").exists()
            and (d_root / "scripts" / "cmd").is_dir()
        )

    def test_mcp_server_resolves_lint(self):
        import wiki_fabric.mcp_server as mcp_server
        p = mcp_server._script("scripts/cmd/lint.py")
        assert p.exists()


class TestBashChainParity(unittest.TestCase):
    """The bash find_fabric documents the same chain (env → sibling → cwd
    walk → XDG). Assert the bash source stays in sync textually — cheap
    drift tripwire (the runtime parity is exercised by the smoke test)."""

    def test_bash_chain_comments_reference_paths_py(self):
        sh = (_SCRIPTS / "wiki-fabric.sh").read_text()
        seg = sh.split("find_fabric() {", 1)
        assert len(seg) == 2
        fn = seg[1].split("\n}", 1)[0]
        head = seg[0][-300:] + fn[:400]
        assert "paths.py" in head or "#152" in head
        # the divergent fallbacks must not return
        assert "$HOME/wiki-fabric" not in fn
        assert "DEFAULT_DIR" not in fn


if __name__ == "__main__":
    unittest.main()

class TestBootstrapImports(unittest.TestCase):
    """#150 regression class: bootstrap-project imports lib helpers by exact
    name — a refactor that drops a lib symbol breaks the shipped command
    (caught live: paths.find_fabric_root renamed to chain primitives)."""

    def test_bootstrap_resolver_callable(self):
        import subprocess
        r = subprocess.run([sys.executable, str(_SCRIPTS / "cmd" / "bootstrap-project.py"),
                            "/nonexistent", "--non-interactive"],
                           capture_output=True, text=True, timeout=60)
        # a clean "not found" failure beats an AttributeError at import
        self.assertNotIn("AttributeError", r.stderr)

    def test_lib_symbols_exist(self):
        import paths
        for name in ("find_harness_root", "find_harness_asset", "find_corpus_root",
                     "find_vault_dir_for_fabric", "env_fabric_root", "walk_for_fabric",
                     "sibling_vault_of", "xdg_fabric_root", "is_fabric_dir", "is_harness_tree"):
            self.assertTrue(hasattr(paths, name), f"paths.{name} missing")
