"""Unit tests for optional-integration gating (graphify, embeddings)."""

import sys
import json as _json
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
    def test_bridge_gate_respects_fabric_yaml(self):
        """graphify-bridge gate: runs when fabric.yaml enables graphify (this
        repo's fabric.yaml has it enabled); the gate itself is unit-tested via
        is_integration_active in TestIntegrationConfig."""
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "graphify-bridge.py"), "--status"],
            capture_output=True, text=True,
            env={"PATH": "/usr/bin:/bin"},
        )
        assert out.returncode == 0
        assert "Graphify Integration Status" in out.stdout

    def test_manifest_reports_integration_state(self, tmp_path):
        src = (REPO / "scripts" / "context.py").read_text()
        (tmp_path / "context.py").write_text(src)
        # context.py imports fabric_config + wf_common from its own directory
        for dep in ("fabric_config.py", "wf_common.py"):
            (tmp_path / dep).write_text((REPO / "scripts" / dep).read_text())
        out = subprocess.run(
            [sys.executable, str(tmp_path / "context.py"), "--task", "t", "--format", "json"],
            capture_output=True, text=True,
        )
        data = _json.loads(out.stdout)
        assert "integrations" in data
        assert data["integrations"]["graphify"] is False  # default off


class TestGraphifyBridgeCommands:
    """Happy-path coverage for the bridge commands (the REPO_CONFIG regression
    shipped because only --status was exercised). Each test runs against an
    isolated fake fabric via WIKI_FABRIC-style env isolation: the bridge reads
    fabric.yaml through fabric_config._find_config_file (repo root first), so
    we build a temp repo tree and point the bridge at it by copying scripts."""

    def _make_fabric(self, tmp_path):
        import json as _json
        scripts = tmp_path / "scripts"
        scripts.mkdir(exist_ok=True)
        # copy the real modules so behavior is identical
        for mod in ("graphify-bridge.py", "fabric_config.py", "wf_common.py"):
            (scripts / mod).write_text((REPO / "scripts" / mod).read_text())
        # fabric.yaml with graphify enabled + one repo
        (tmp_path / "fabric.yaml").write_text(
            "owner: t\n"
            "integrations:\n  graphify:\n    enabled: true\n"
            "repos:\n  fake-repo:\n    path: repos/fake-repo\n")
        # the "connected repo" with a graphify-out/graph.json
        repo = tmp_path / "repos" / "fake-repo"
        (repo / "graphify-out").mkdir(parents=True)
        graph = {
            "nodes": [{"id": "a", "label": "alpha"}, {"id": "b", "label": "beta"}],
            "links": [{"source": "a", "target": "b", "relation": "calls"}],
        }
        (repo / "graphify-out" / "graph.json").write_text(_json.dumps(graph))
        return tmp_path

    def test_import_writes_graph_and_hash(self, tmp_path, monkeypatch):
        import subprocess
        fab = self._make_fabric(tmp_path)
        # resolve_repo_path resolves relative paths against FABRIC_ROOT — which is
        # derived from __file__ (the copied script), so paths line up.
        out = subprocess.run(
            [sys.executable, str(fab / "scripts" / "graphify-bridge.py"), "--import"],
            capture_output=True, text=True, cwd=str(fab),
        )
        assert out.returncode == 0, out.stderr
        graphs = fab / "global" / "graphs"
        assert (graphs / "fake-repo-graph.json").exists()
        assert (graphs / "fake-repo-graph.hash").exists()

    def test_diff_fresh_then_stale(self, tmp_path):
        import subprocess
        fab = self._make_fabric(tmp_path)
        run = lambda *a: subprocess.run(
            [sys.executable, str(fab / "scripts" / "graphify-bridge.py"), *a],
            capture_output=True, text=True, cwd=str(fab))
        # no import yet -> no stored hash
        out = run("--diff")
        assert "no stored hash" in out.stdout
        # import -> fresh
        run("--import")
        out = run("--diff")
        assert "fresh" in out.stdout
        # mutate the graph -> stale
        gp = fab / "repos" / "fake-repo" / "graphify-out" / "graph.json"
        g = _json.loads(gp.read_text())
        g["nodes"].append({"id": "c", "label": "gamma"})
        gp.write_text(_json.dumps(g))
        out = run("--diff")
        assert "STALE" in out.stdout

    def test_enrich_is_safe_with_no_claims(self, tmp_path):
        import subprocess
        fab = self._make_fabric(tmp_path)
        run = lambda *a: subprocess.run(
            [sys.executable, str(fab / "scripts" / "graphify-bridge.py"), *a],
            capture_output=True, text=True, cwd=str(fab))
        run("--import")
        out = run("--enrich")
        assert out.returncode == 0, out.stderr
        assert "enriched 0 claims" in out.stdout

    def test_status_lists_graph(self, tmp_path):
        import subprocess
        fab = self._make_fabric(tmp_path)
        out = subprocess.run(
            [sys.executable, str(fab / "scripts" / "graphify-bridge.py"), "--status"],
            capture_output=True, text=True, cwd=str(fab),
        )
        assert "fake-repo" in out.stdout
