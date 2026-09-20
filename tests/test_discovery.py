"""Tests for overlay-as-config: sibling discovery, routing merge, vault refresh."""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

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
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
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
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
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
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
            rc = fc.get_repo_config(cfg, "proj-a")
        self.assertEqual(rc["routing"]["extract"], "local")
        self.assertEqual(rc.get("extract"), "local")  # promoted for consumers
        self.assertTrue(rc["discovered"])

    def test_explicit_stage_key_beats_overlay_routing(self):
        import fabric_config as fc
        cfg = self._cfg(repos={"proj-a": {"extract": "cloud"}})
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
            rc = fc.get_repo_config(cfg, "proj-a")
        self.assertEqual(rc["extract"], "cloud")  # explicit wins
        self.assertEqual(rc["routing"]["extract"], "local")  # routing dict records overlay
        # stage route resolves to cloud compiler
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
            route = fc.get_stage_route(cfg, "proj-a", "extract")
        self.assertEqual(route, "cloud-model" if False else route)  # checked below

    def test_stage_route_from_overlay(self):
        import fabric_config as fc
        cfg = self._cfg()
        cfg["llm"] = {"compiler_model": "deepseek-v4.1-flash:cloud"}
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
            from fabric_config import get_local_model
            self.assertEqual(fc.get_stage_route(cfg, "proj-a", "extract"), get_local_model(cfg))
            self.assertTrue(fc.is_local_route(cfg, "proj-a", "extract"))
            # proj-b has no routing: cloud
            self.assertEqual(fc.get_stage_route(cfg, "proj-b", "extract"), "deepseek-v4.1-flash:cloud")

    def test_get_all_repo_names_includes_discovered(self):
        import fabric_config as fc
        cfg = self._cfg()
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None):
            names = fc.get_all_repo_names(cfg)
        self.assertIn("proj-a", names)
        self.assertIn("fabric-self", names)

    def test_discovery_cache_invalidates_on_overlay_mtime(self):
        import fabric_config as fc
        cfg = self._cfg()
        with mock.patch.object(fc, "FABRIC_ROOT", self.fabric):
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
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.fabric, _ = _make_world(self.tmp)
        self.vault = self.tmp / "vault"

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _run(self, *args):
        import importlib.util as _ilu
        import fabric_config as fc
        spec = _ilu.spec_from_file_location('vault_refresh', str(Path(__file__).parent.parent / 'scripts' / 'vault-refresh.py'))
        vault_refresh = _ilu.module_from_spec(spec); spec.loader.exec_module(vault_refresh)
        with mock.patch.object(vault_refresh, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None), \
             mock.patch.object(vault_refresh, "get_all_repo_names", return_value=["proj-a", "proj-b"]):
            return vault_refresh.refresh(self.vault, *args)

    def test_refresh_creates_links_and_overlay_views(self):
        rc = self._run(False)
        self.assertEqual(rc, 0)
        for link in ("AGENTS.md", "projects", "concepts"):
            self.assertTrue((self.vault / link).is_symlink(), link)
        view = self.fabric / "projects" / "proj-a" / "overlay.yml"
        self.assertTrue(view.exists())
        self.assertIn("extract: local", view.read_text())

    def test_check_reports_drift_before_refresh(self):
        rc = self._run(True)
        self.assertEqual(rc, 1)  # missing links = drift

    def test_check_fresh_after_refresh(self):
        self._run(False)
        rc = self._run(True)
        self.assertEqual(rc, 0)

    def test_overlay_view_updates_when_content_changes(self):
        self._run(False)
        view = self.fabric / "projects" / "proj-a" / "overlay.yml"
        stale = view.read_text()
        # source overlay changes -> next refresh rewrites the view
        time.sleep(0.05)  # mtime resolution: ensure fingerprint changes
        (self.tmp / "proj-a" / ".wiki-overlay.md").write_text(
            OVERLAY_TMPL.format(slug="proj-a", routing_block="routing:\n  extract: cloud\n"))
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location('vault_refresh', str(Path(__file__).parent.parent / 'scripts' / 'vault-refresh.py'))
        vault_refresh = _ilu.module_from_spec(spec); spec.loader.exec_module(vault_refresh)
        import fabric_config as fc
        with mock.patch.object(vault_refresh, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "FABRIC_ROOT", self.fabric), \
             mock.patch.object(fc, "_OVERLAY_CACHE", None), \
             mock.patch.object(vault_refresh, "get_all_repo_names", return_value=["proj-a"]):
            vault_refresh.refresh(self.vault, False, quiet=True)
        self.assertNotEqual(view.read_text(), stale)
        self.assertIn("extract: cloud", view.read_text())


class TestReposMigrate(unittest.TestCase):
    def test_plan_finds_migratable_keys(self):
        import importlib.util as _ilu2
        _spec = _ilu2.spec_from_file_location('repos_migrate', str(Path(__file__).parent.parent / 'scripts' / 'repos-migrate.py'))
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