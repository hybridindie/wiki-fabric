"""Per-repo integration scoping: get_integration_cfg (repo override over
global, mirrors get_repo_graph_dir) + judgment routing through it + the
claim-project stamp at ingest (the honest per-repo cut).

Run: python3 -m pytest tests/test_integration_scoping.py -v
"""
import sys
import importlib.util
from pathlib import Path

import pytest

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import fabric_config as fc


class TestIntegrationResolver:
    CFG = {
        "integrations": {
            "judgment": {"enabled": True, "route": "cloud",
                         "cloud_model": "jev-latest", "local_backend": "laya"},
            "embeddings": {"enabled": False},
        },
        "repos": {
            "sensitive": {"integrations": {"judgment": {"enabled": True, "route": "local"}}},
            "judgment-off": {"integrations": {"judgment": {"enabled": False}}},
            "plain": {"path": "/x"},
        },
    }

    def test_global_when_no_repo(self):
        c = fc.get_integration_cfg(self.CFG, "judgment")
        assert c["enabled"] is True and c["route"] == "cloud"

    def test_repo_overrides_route_keeps_globals(self):
        # deep merge: route overridden, cloud_model + local_backend survive
        c = fc.get_integration_cfg(self.CFG, "judgment", "sensitive")
        assert c["route"] == "local"
        assert c["cloud_model"] == "jev-latest"
        assert c["local_backend"] == "laya"

    def test_repo_can_disable_a_global_on(self):
        assert fc.is_integration_active(self.CFG, "judgment", "judgment-off") is False

    def test_repo_can_enable_a_global_off(self):
        c = dict(self.CFG, integrations={"embeddings": {"enabled": False}},
                 repos={"s": {"integrations": {"embeddings": {"enabled": True}}}})
        assert fc.is_integration_active(c, "embeddings", "s") is True
        assert fc.is_integration_active(c, "embeddings") is False

    def test_repo_without_block_inherits_global(self):
        c = fc.get_integration_cfg(self.CFG, "judgment", "plain")
        assert c == fc.get_integration_cfg(self.CFG, "judgment")

    def test_unknown_repo_inherits_global(self):
        assert fc.get_integration_cfg(self.CFG, "judgment", "ghost") == \
            fc.get_integration_cfg(self.CFG, "judgment")

    def test_overlay_repos_entry_reaches(self, tmp_path, monkeypatch):
        # the overlay IS the project's config — its integrations block must
        # reach get_integration_cfg (route: local in the overlay folds over
        # the global block)
        monkeypatch.setattr(fc, "FABRIC_ROOT", tmp_path / "fabric", raising=False)
        (tmp_path / "repo").mkdir(parents=True)
        (tmp_path / "repo" / ".wiki-overlay.md").write_text(
            "---\nnamespace: myrepo\nintegrations:\n  judgment:\n    enabled: true\n    route: local\n---\n\n# o\n")
        fc._OVERLAY_CACHE = None
        cfg = {"repos": {"integrations": {"judgment": {"enabled": True, "route": "cloud"}}}}
        c = fc.get_integration_cfg(cfg, "judgment", "myrepo")
        assert c["route"] == "local" and c["enabled"] is True


class TestJudgmentRepoRouting:
    def test_route_per_repo(self):
        from judgment import judgment_config, judgment_route, JudgmentUnavailable
        cfg = {"integrations": {"judgment": {"enabled": True, "route": "cloud"}},
               "repos": {"s": {"integrations": {"judgment": {"route": "local"}}}},
               "off": {"integrations": {"judgment": {"enabled": False}}},
               "on": {"integrations": {"judgment": {"enabled": True}}}}
        assert judgment_route(cfg) == "cloud"
        assert judgment_route(cfg, repo="s") == "local"
        # global-off + repo-on: repo wins (privacy tiering can be finer-grained both ways)
        assert judgment_route(cfg, repo="on") == "cloud"

    def test_config_defaults_survive_override(self):
        from judgment import judgment_config
        cfg = {"integrations": {"judgment": {"enabled": True, "route": "cloud"}},
               "repos": {"s": {"integrations": {"judgment": {"route": "local"}}}}}
        c = judgment_config(cfg, repo="s")
        assert c["local_backend"] == "laya"
        assert "cloud_model" in c  # the global cloud_model survived the route override


class TestClaimProjectStamp:
    def test_ingest_stamps_project(self):
        from ingest import claim_frontmatter  # module loaded via cmd path
        fm = claim_frontmatter({"statement": "s", "quote": "q"},
                               "p-git-pr-1-md", 3, project="comfyui-mcp")
        assert 'project: "comfyui-mcp"' in fm

    def test_omit_leaves_no_empty_field(self):
        from ingest import claim_frontmatter
        fm = claim_frontmatter({"statement": "s", "quote": "q"}, "p-git-pr-1-md", 3)
        assert "project:" not in fm

    def test_verify_effects_derives_repo_via_frontmatter(self, tmp_path):
        import sys as _s
        import importlib.util as _ilu
        spec = _ilu.spec_from_file_location("ve_sc", _SCRIPTS / "cmd/verify-effects.py")
        ve = _ilu.module_from_spec(spec); sys.modules["ve_sc"] = ve; spec.loader.exec_module(ve)
        c = tmp_path / "claim-x-000.md"
        c.write_text("---\ntype: claim\nproject: comfyui_mcp\n---\n")
        assert ve.claim_repo(c) == "comfyui-mcp"  # canonical fold, frontmatter cut
        legacy = tmp_path / "claim-old.md"
        legacy.write_text("---\ntype: claim\n---\n")
        assert ve.claim_repo(legacy) is None     # no guess from lossy stems
