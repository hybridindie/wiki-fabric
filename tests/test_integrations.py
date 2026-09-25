"""Unit tests for optional-integration gating (graphify, embeddings)."""

import sys
import os
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


fc = _load_module("fabric_config", REPO / "scripts" / "lib/fabric_config.py")


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
    def _run(self, fab, *args):
        import subprocess as _sp
        return _sp.run(
            [sys.executable, str(fab / "scripts" / "harness/graphify-bridge.py"), *args],
            capture_output=True, text=True, cwd=str(fab),
            env={**os.environ, "WIKI_FABRIC_DIR": str(fab)},
        )

    def test_bridge_gate_respects_fabric_yaml(self):
        """graphify-bridge gate: runs against a temp fabric whose fabric.yaml
        enables graphify (independent of this repo's gitignored config, so it
        holds in CI)."""
        fab = self._make_fabric()
        out = self._run(fab, "--status")
        assert out.returncode == 0
        assert "Graphify Integration Status" in out.stdout

    def test_bridge_gate_refuses_when_disabled(self):
        """The gate: a fabric with graphify disabled gets the enable message,
        not a crash."""
        fab = self._make_fabric(enabled=False)
        out = self._run(fab, "--status")
        assert out.returncode == 0
        assert "Graphify integration is not enabled" in out.stdout

    def _make_fabric(self, enabled=True):
        import shutil
        import tempfile
        fab = Path(tempfile.mkdtemp()) / "_bridge_fixture_fabric"
        fab.mkdir(parents=True)
        # Mirror the real scripts/ subdir layout so the bridge bootstrap resolves
        # its lib/cmd deps (prepends scripts/, cmd/, lib/, eval/, harness/).
        shutil.copytree(REPO / "scripts", fab / "scripts", dirs_exist_ok=True)
        (fab / "corpus").mkdir(exist_ok=True)
        (fab / "fabric.yaml").write_text(
            f"owner: t\n"
            f"integrations:\n  graphify:\n    enabled: {str(enabled).lower()}\n"
            "repos:\n  fake-repo:\n    path: repos/fake-repo\n")
        return fab

    def test_manifest_reports_integration_state(self, tmp_path):
        # Mirror the real scripts/ subdir layout so context.py's bootstrap
        # (prepends scripts/, cmd/, lib/, ... to sys.path) resolves deps.
        import shutil as _sh
        _sh.copytree(REPO / "scripts", tmp_path / "scripts", dirs_exist_ok=True)
        out = subprocess.run(
            [sys.executable, str(tmp_path / "scripts" / "cmd/context.py"), "--task", "t", "--format", "json"],
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
        import shutil as _sh
        # Mirror the real scripts/ subdir layout so the bridge bootstrap resolves
        # its lib/cmd deps (prepends scripts/, cmd/, lib/, eval/, harness/).
        _sh.copytree(REPO / "scripts", tmp_path / "scripts", dirs_exist_ok=True)
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

    def _run(self, fab, *args):
        """Run graphify-bridge against the sandbox, pinning it as the fabric
        root (the harness is tool-only now; root comes from WIKI_FABRIC_DIR)."""
        import subprocess
        return subprocess.run(
            [sys.executable, str(fab / "scripts" / "harness/graphify-bridge.py"), *args],
            capture_output=True, text=True, cwd=str(fab),
            env={**os.environ, "WIKI_FABRIC_DIR": str(fab)},
        )

    def test_import_writes_graph_and_hash(self, tmp_path, monkeypatch):
        import subprocess
        fab = self._make_fabric(tmp_path)
        # resolve_repo_path resolves relative paths against FABRIC_ROOT — which is
        # derived from __file__ (the copied script), so paths line up.
        out = self._run(fab, "--import")
        assert out.returncode == 0, out.stderr
        graphs = fab / "corpus" / "global" / "graphs"
        assert (graphs / "fake-repo-graph.json").exists()
        assert (graphs / "fake-repo-graph.hash").exists()

    def test_diff_fresh_then_stale(self, tmp_path):
        import subprocess
        fab = self._make_fabric(tmp_path)
        run = lambda *a: self._run(fab, *a)
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
        run = lambda *a: self._run(fab, *a)
        run("--import")
        out = run("--enrich")
        assert out.returncode == 0, out.stderr
        assert "enriched 0 claims" in out.stdout

    def test_status_lists_graph(self, tmp_path):
        import subprocess
        fab = self._make_fabric(tmp_path)
        out = self._run(fab, "--status")
        assert "fake-repo" in out.stdout
