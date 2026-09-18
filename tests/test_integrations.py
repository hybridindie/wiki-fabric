"""Unit tests for optional-integration gating (graphify, embeddings)."""

import sys
import importlib.util
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


fc = _load_module("fabric_config", REPO / "scripts" / "fabric_config.py")


class TestIntegrationConfig:
    def test_default_is_inactive(self):
        assert fc.is_integration_active({}, "graphify") is False
        assert fc.is_integration_active({}, "embeddings") is False

    def test_explicit_enable(self):
        assert fc.is_integration_active({"integrations": {"graphify": {"enabled": True}}}, "graphify") is True

    def test_disabled_explicitly(self):
        assert fc.is_integration_active({"integrations": {"graphify": {"enabled": False}}}, "graphify") is False

    def test_unknown_integration_from_user_config(self):
        cfg = {"integrations": {"mything": {"enabled": True}}}
        assert fc.is_integration_active(cfg, "mything") is True

    def test_get_integrations_merges_user_over_defaults(self):
        cfg = {"integrations": {"graphify": {"enabled": True, "graph_dir": "my-graphs"}}}
        integ = fc.get_integrations(cfg)
        assert integ["graphify"] == {"enabled": True, "graph_dir": "my-graphs"}
        # embeddings default preserved
        assert integ["embeddings"]["enabled"] is False


class TestGraphifyGate:
    def test_bridge_refuses_when_inactive(self):
        """graphify-bridge must refuse (exit, helpful message) when disabled."""
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "graphify-bridge.py"), "--status"],
            capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin"},  # fabric.yaml absent in env-less run? uses repo config
        )
        # With repo fabric.yaml lacking integrations, it must NOT crash and must mention enablement
        assert "not enabled" in out.stdout or "not enabled" in out.stderr

    def test_manifest_reports_integration_state(self, tmp_path):
        import json
        src = (REPO / "scripts" / "context.py").read_text()
        (tmp_path / "context.py").write_text(src)
        # context.py imports fabric_config from its own directory
        (tmp_path / "fabric_config.py").write_text(
            (REPO / "scripts" / "fabric_config.py").read_text())
        out = subprocess.run(
            [sys.executable, str(tmp_path / "context.py"), "--task", "t", "--format", "json"],
            capture_output=True, text=True,
        )
        data = json.loads(out.stdout)
        assert "integrations" in data
        assert data["integrations"]["graphify"] is False  # default off
