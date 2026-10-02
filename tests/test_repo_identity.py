"""#158 S1+S2: canonical repo identity at the config layer.

Run: python3 -m pytest tests/test_repo_identity.py -v
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


class TestCanonicalRepoKeys:
    def test_discovered_keys_canonical(self, tmp_path, monkeypatch):
        monkeypatch.setattr(fc, "FABRIC_ROOT", tmp_path / "fabric", raising=False)
        (tmp_path / "comfyui_mcp").mkdir(parents=True)
        (tmp_path / "comfyui_mcp" / ".wiki-overlay.md").write_text(
            "---\nnamespace: comfyui_mcp\n---\n\n# overlay\n")
        fc._OVERLAY_CACHE = None
        found = fc.get_discovered_repos({"repos": {}})
        assert "comfyui-mcp" in found
        assert "comfyui_mcp" not in found
        assert found["comfyui-mcp"]["_orig_ns"] == "comfyui_mcp"

    def test_lookup_folds_both_spellings(self, tmp_path, monkeypatch):
        config = {"repos": {"comfyui-mcp": {"path": "/repos/comfyui_mcp", "routing": {"extract": "cloud"}}}}
        a = fc.get_repo_config(config, "comfyui_mcp")
        b = fc.get_repo_config(config, "comfyui-mcp")
        assert a.get("path") == b.get("path") == "/repos/comfyui_mcp"
        assert a.get("routing") == b.get("routing")

    def test_all_repo_names_dedup_canonical(self):
        config = {"repos": {"comfyui-mcp": {"path": "/x"}, "comfyui_mcp": {"path": "/y"}}}
        names = fc.get_all_repo_names(config)
        assert names.count("comfyui-mcp") == 1
        assert "comfyui_mcp" not in names

    def test_auto_discover_never_lists(self):
        assert "auto_discover" not in fc.get_all_repo_names({"repos": {"auto_discover": True}})


class TestIdentityLint:
    def test_canonical_collision_errors(self):
        config = {"repos": {"comfyui-mcp": {"path": "/a"}, "comfyui_mcp": {"path": "/b"}}}
        from lint import check_repo_identity
        probs = check_repo_identity(config)
        assert any("collides" in p for p in probs)

    def test_resolved_path_divergence_flags(self, tmp_path, monkeypatch):
        import lint
        import fabric_config as fc
        (tmp_path / "r1").mkdir(); (tmp_path / "r2").mkdir()
        config = {"repos": {"godot": {"path": str(tmp_path / "r1")}}}
        discovered = {"godot": {"path": str(tmp_path / "r2"), "_orig_ns": "godot"}}
        import contextlib, io
        monkeypatch.setattr(fc, "get_discovered_repos", lambda c: discovered)
        monkeypatch.setattr(lint, "get_config", lambda: config)
        probs = lint.check_repo_identity(config)
        assert any("different repos" in p for p in probs)

    def test_same_resolved_path_clean(self, tmp_path, monkeypatch):
        import lint
        (tmp_path / "r1").mkdir()
        config = {"repos": {"godot": {"path": str(tmp_path / "r1")}}}
        discovered = {"godot": {"path": str(tmp_path / "r1"), "_orig_ns": "godot"}}
        monkeypatch.setattr(lint, "get_config", lambda: config, raising=False)
        import fabric_config as fc
        monkeypatch.setattr(fc, "get_discovered_repos", lambda c: discovered)
        probs = lint.check_repo_identity(config)
        assert not any("different repos" in p for p in probs)

    def test_advisory_on_noncanonical_namespace(self, tmp_path, monkeypatch):
        import lint
        config = {"repos": {}}
        discovered = {"comfyui-mcp": {"path": "/x", "_orig_ns": "comfyui_mcp"}}
        monkeypatch.setattr(lint, "get_config", lambda: config, raising=False)
        import fabric_config as fc
        monkeypatch.setattr(fc, "get_discovered_repos", lambda c: discovered)
        probs = lint.check_repo_identity(config)
        assert any("non-canonical" in p for p in probs)
