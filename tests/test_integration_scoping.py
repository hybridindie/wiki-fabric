"""Integration scoping: integrations are a fabric-GLOBAL setting — the
per-repo override seam (repos.<slug>.integrations.<name>, built for the
judgment tier, #156) is removed; get_integration_cfg resolves global only.
Also: the claim-project stamp at ingest (provenance, no longer judgment
routing) and its frontmatter cut.

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
            # stale per-repo integrations blocks are INERT: the seam is gone
            "sensitive": {"integrations": {"judgment": {"enabled": True, "route": "local"}}},
            "judgment-off": {"integrations": {"judgment": {"enabled": False}}},
            "plain": {"path": "/x"},
        },
    }

    def test_global_when_no_repo(self):
        c = fc.get_integration_cfg(self.CFG, "judgment")
        assert c["enabled"] is True and c["route"] == "cloud"

    def test_repo_integration_block_is_inert(self):
        # a stale repos.<slug>.integrations block does NOT override global
        assert fc.is_integration_active(self.CFG, "judgment", "sensitive") is True
        assert fc.get_integration_cfg(self.CFG, "judgment", "sensitive") == \
            fc.get_integration_cfg(self.CFG, "judgment")

    def test_repo_cannot_disable_a_global_on(self):
        assert fc.is_integration_active(self.CFG, "judgment", "judgment-off") is True

    def test_global_off_stays_off_for_any_repo(self):
        c = dict(self.CFG, integrations={"embeddings": {"enabled": False}},
                 repos={"s": {"integrations": {"embeddings": {"enabled": True}}}})
        assert fc.is_integration_active(c, "embeddings", "s") is False

    def test_repo_without_block_inherits_global(self):
        c = fc.get_integration_cfg(self.CFG, "judgment", "plain")
        assert c == fc.get_integration_cfg(self.CFG, "judgment")

    def test_unknown_repo_inherits_global(self):
        assert fc.get_integration_cfg(self.CFG, "judgment", "ghost") == \
            fc.get_integration_cfg(self.CFG, "judgment")


class TestJudgmentGlobalOnly:
    def test_route_is_global(self):
        from judgment import judgment_route, JudgmentUnavailable
        cfg = {"integrations": {"judgment": {"enabled": True, "route": "cloud"}}}
        assert judgment_route(cfg) == "cloud"
        with pytest.raises(JudgmentUnavailable):
            judgment_route({"integrations": {"judgment": {"enabled": False}}})

    def test_config_defaults_survive(self):
        from judgment import judgment_config
        c = judgment_config({"integrations": {"judgment": {"enabled": True}}})
        assert c["local_backend"] == "laya"
        assert c["cloud_model"] == "jev-latest"

    def test_repo_arg_ignored(self):
        from judgment import judgment_route
        cfg = {"integrations": {"judgment": {"enabled": True, "route": "cloud"}}}
        assert judgment_route(cfg, repo="s") == "cloud"


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