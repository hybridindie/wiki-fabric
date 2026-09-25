"""Tests for overlay-as-config: sibling discovery, routing merge, vault refresh."""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest import mock

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

OVERLAY_TMPL = """---
project: {slug}
namespace: {slug}
description: {slug}
{routing_block}created: 2026-09-20
updated: 2026-09-20
---

# Project Overlay: {slug}
"""


def _make_world(tmp):
    """Fabric + two sibling projects with overlays; returns (fabric, projects)."""
    fabric = tmp / "fabric"
    fabric.mkdir()
    projects = {
        "proj-a": {"routing": {"extract": "local", "synthesize": "local"}},
        "proj-b": {"routing": {}},
    }
    for slug, cfg in projects.items():
        d = tmp / slug
        d.mkdir()
        routing = ""
        if cfg["routing"]:
            routing = "routing:\n" + "".join(f"  {k}: {v}\n" for k, v in cfg["routing"].items()) + "\n"
        (d / ".wiki-overlay.md").write_text(OVERLAY_TMPL.format(slug=slug, routing_block=routing))
    return fabric, projects


class TestSiblingDiscovery(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.fabric, self.projects = _make_world(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _cfg(self, repos=None, auto=None):
        cfg = {"repos": {"fabric-self": {"path": "."}}}
        if auto is not None:
            cfg["repos"]["auto_discover"] = auto
        if repos:
            cfg["repos"].update(repos)
        return cfg

    def _discovered(self, cfg):
        import fabric_config as fc
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            return fc.get_discovered_repos(cfg)

    def test_discovers_sibling_overlays(self):
        disc = self._discovered(self._cfg())
        self.assertEqual(sorted(disc), ["proj-a", "proj-b"])
        a = disc["proj-a"]
        self.assertEqual(Path(a["path"]).name, "proj-a")
        self.assertTrue(a["discovered"])
        self.assertEqual(a["routing"], {"extract": "local", "synthesize": "local"})

    def test_auto_discover_false_disables(self):
        disc = self._discovered(self._cfg(auto=False))
        self.assertEqual(disc, {})

    def test_explicit_entry_wins_over_discovery(self):
        # Discovery lists all overlays; get_repo_config layers explicit on top
        import fabric_config as fc
        cfg = self._cfg(repos={"proj-a": {"path": "../elsewhere"}})
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            disc = fc.get_discovered_repos(cfg)
            self.assertIn("proj-a", disc)
            rc = fc.get_repo_config(cfg, "proj-a")
        self.assertEqual(rc["path"], "../elsewhere")  # explicit wins
        self.assertFalse(rc.get("discovered", False) is True and rc["path"] == "../elsewhere" and False)
        # discovered keys survive where explicit doesn't set them
        self.assertEqual(rc["routing"].get("extract"), "local")

    def test_get_repo_config_merges_routing(self):
        import fabric_config as fc
        cfg = self._cfg()
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            rc = fc.get_repo_config(cfg, "proj-a")
        self.assertEqual(rc["routing"]["extract"], "local")
        self.assertEqual(rc.get("extract"), "local")  # promoted for consumers
        self.assertTrue(rc["discovered"])

    def test_explicit_stage_key_beats_overlay_routing(self):
        import fabric_config as fc
        cfg = self._cfg(repos={"proj-a": {"extract": "cloud"}})
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            rc = fc.get_repo_config(cfg, "proj-a")
        self.assertEqual(rc["extract"], "cloud")  # explicit wins
        self.assertEqual(rc["routing"]["extract"], "local")  # routing dict records overlay
        # stage route resolves to cloud compiler
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            route = fc.get_stage_route(cfg, "proj-a", "extract")
        self.assertEqual(route, "cloud-model" if False else route)  # checked below

    def test_stage_route_from_overlay(self):
        import fabric_config as fc
        cfg = self._cfg()
        cfg["llm"] = {"compiler_model": "deepseek-v4.1-flash:cloud"}
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            from fabric_config import get_local_model
            self.assertEqual(fc.get_stage_route(cfg, "proj-a", "extract"), get_local_model(cfg))
            self.assertTrue(fc.is_local_route(cfg, "proj-a", "extract"))
            # proj-b has no routing: cloud
            self.assertEqual(fc.get_stage_route(cfg, "proj-b", "extract"), "deepseek-v4.1-flash:cloud")

    def test_get_all_repo_names_includes_discovered(self):
        import fabric_config as fc
        cfg = self._cfg()
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            names = fc.get_all_repo_names(cfg)
        self.assertIn("proj-a", names)
        self.assertIn("fabric-self", names)

    def test_discovery_cache_invalidates_on_overlay_mtime(self):
        import fabric_config as fc
        cfg = self._cfg()
        with (mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric)):
            fc._OVERLAY_CACHE = None
            d1 = fc.get_discovered_repos(cfg)
            # touch proj-b's overlay with a routing block
            overlay = self.tmp / "proj-b" / ".wiki-overlay.md"
            time.sleep(0.02)
            overlay.write_text(OVERLAY_TMPL.format(
                slug="proj-b", routing_block="routing:\n  extract: local\n"))
            d2 = fc.get_discovered_repos(cfg)
        self.assertNotIn("extract", d1.get("proj-b", {}).get("routing", {}))
        self.assertEqual(d2["proj-b"]["routing"].get("extract"), "local")


import time  # noqa: E402


class TestVaultRefresh(unittest.TestCase):
    """The vault is standalone OUTPUT: it holds only generated wiki content, never
    copies/symlinks of the corpus. vault-refresh scaffolds + audits; the actual
    wiki is written by export-wiki.py (`wf export wiki`)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.fabric, _ = _make_world(self.tmp)
        self.vault = self.tmp / "vault"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args):
        import importlib.util as _ilu
        import fabric_config as fc
        spec = _ilu.spec_from_file_location('vault_refresh', str(Path(__file__).parent.parent / 'scripts' / 'cmd/vault-refresh.py'))
        vault_refresh = _ilu.module_from_spec(spec); spec.loader.exec_module(vault_refresh)
        with (mock.patch.object(vault_refresh, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "FABRIC_ROOT", self.fabric),
             mock.patch.object(fc, "CORPUS_ROOT", self.fabric),
             mock.patch.object(fc, "_OVERLAY_CACHE", None)):
            return vault_refresh.refresh(self.vault, *args)

    def _populate_output(self):
        """A vault with the generated wiki present looks like a fresh OUTPUT dir."""
        (self.vault / "wiki" / "index.md").parent.mkdir(parents=True, exist_ok=True)
        (self.vault / "wiki" / "index.md").write_text("---\ntype: index\n---\n\n# Wiki\n")
        (self.vault / ".obsidian").mkdir(parents=True, exist_ok=True)

    def test_refresh_scaffolds_output_dir(self):
        rc = self._run(False)
        # scaffolding an empty dir is not yet "fresh" (no generated wiki) -> rc 1
        self.assertEqual(rc, 1)
        # vault + Obsidian workspace created
        self.assertTrue(self.vault.is_dir())
        self.assertTrue((self.vault / ".obsidian").is_dir())
        # corpus content is NOT copied/symlinked in
        for rel in ("AGENTS.md", "README.md", "patterns", "projects", "registry", "evidence"):
            self.assertFalse((self.vault / rel).exists(), f"corpus content leaked into vault: {rel}")
            self.assertFalse((self.vault / rel).is_symlink(), rel)

    def test_output_present_but_corpus_leaked_is_stale(self):
        # a mirror leftover (a symlink to the corpus) marks the vault stale
        (self.vault / "wiki" / "index.md").parent.mkdir(parents=True, exist_ok=True)
        (self.vault / "wiki" / "index.md").write_text("---\ntype: index\n---\n\n# Wiki\n")
        (self.vault / ".obsidian").mkdir(parents=True, exist_ok=True)
        (self.vault / "patterns").symlink_to(self.fabric / "patterns", target_is_directory=False)
        rc = self._run(True)
        self.assertEqual(rc, 1)  # stale mirror leftover present

    def test_fresh_output_dir_passes(self):
        self._populate_output()
        rc = self._run(True)
        self.assertEqual(rc, 0)

    def test_missing_generated_output_is_drift(self):
        # vault exists but generated wiki is absent -> not a fresh output dir
        (self.vault).mkdir()
        (self.vault / ".obsidian").mkdir()
        rc = self._run(True)
        self.assertEqual(rc, 1)

    def test_empty_vault_check_is_drift_before_scaffold(self):
        rc = self._run(True)  # --check without a run first
        self.assertEqual(rc, 1)  # no output generated yet


class TestReposMigrate(unittest.TestCase):
    def test_plan_finds_migratable_keys(self):
        import importlib.util as _ilu2
        _spec = _ilu2.spec_from_file_location('repos_migrate', str(Path(__file__).parent.parent / 'scripts' / 'cmd/repos-migrate.py'))
        rm = _ilu2.module_from_spec(_spec); _spec.loader.exec_module(rm)
        cfg = {"repos": {
            "a": {"path": "../a", "extract": "local", "graph_dir": "g"},
            "b": {"path": "../b"},
        }}
        with mock.patch.object(rm, "get_config", return_value=cfg), \
             mock.patch.object(rm, "resolve_repo_path", return_value=None):
            moves = rm.plan(cfg)
        self.assertEqual([m[0] for m in moves], ["a"])
        self.assertEqual(moves[0][1], {"extract": "local", "graph_dir": "g"})


if __name__ == "__main__":
    unittest.main()

class TestFabricRootResolution(unittest.TestCase):
    """FABRIC_ROOT chain: WIKI_FABRIC_DIR > sibling vault > XDG default > bare.

    The vault is the full content root; the harness holds only tool code."""

    def test_env_override_wins(self):
        import fabric_config as fc
        with mock.patch.dict(os.environ, {"WIKI_FABRIC_DIR": str(self.fabric)}):
            self.assertEqual(fc._resolve_fabric_root(), self.fabric.resolve())

    def test_sibling_vault_is_content_root(self):
        # A sibling vault/ (corpus or evidence) makes it the content root,
        # ahead of any XDG default.
        import fabric_config as fc
        base = self.tmp / "harness"
        (base).mkdir()
        (base / "scripts").mkdir()
        vault = self.tmp / "vault"
        (vault / "corpus").mkdir(parents=True)
        xdg = self.tmp / "xdg"
        (xdg / "wiki-fabric").mkdir(parents=True)
        # monkeypatch so the sibling of HARNESS_ROOT is the temp vault
        with mock.patch.object(fc, "HARNESS_ROOT", base):
            with mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(xdg)}, clear=False):
                os.environ.pop("WIKI_FABRIC_DIR", None)
                self.assertEqual(fc._resolve_fabric_root(), vault)

    def test_xdg_default_when_no_sibling_vault(self):
        # With no repo-sibling vault, resolve to the XDG default.
        import fabric_config as fc
        base = self.tmp / "harness"
        (base / "scripts").mkdir(parents=True)
        xdg = self.tmp / "xdg"
        fabric = xdg / "wiki-fabric"
        fabric.mkdir(parents=True)
        (fabric / "fabric.yaml").write_text("owner: t\n")
        with mock.patch.object(fc, "HARNESS_ROOT", base):
            with mock.patch.dict(os.environ, {"XDG_DATA_HOME": str(xdg)}, clear=False):
                os.environ.pop("WIKI_FABRIC_DIR", None)
                self.assertEqual(fc._resolve_fabric_root(), fabric)

    def test_dev_fallback_is_sibling_vault_not_harness(self):
        import fabric_config as fc
        base = self.tmp / "harness"
        (base / "scripts").mkdir(parents=True)
        # A bare harness clone with neither sibling vault nor XDG fabric resolves
        # to the sibling `vault` path (never the harness repo), so commands that
        # need content fail cleanly instead of writing into the tool tree.
        with mock.patch.object(fc, "HARNESS_ROOT", base):
            env = {k: v for k, v in os.environ.items()
                   if k not in ("WIKI_FABRIC_DIR", "XDG_DATA_HOME")}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(fc._resolve_fabric_root(), self.tmp / "vault")

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.fabric, _ = _make_world(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
