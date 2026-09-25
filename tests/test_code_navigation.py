"""Unit tests for context.py code_navigation — graphify-gated navigation (#48).

Run: python3 -m pytest tests/test_code_navigation.py -v
"""
import contextlib
import importlib.util
import json
import sys
from pathlib import Path
from unittest import mock

REPO = Path(__file__).parent.parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ctx = _load("context", REPO / "scripts" / "cmd" / "context.py")


def _make_fabric(tmp, with_graph=True):
    repo = tmp / "repos" / "godot-mcp"
    (repo / "graphify-out").mkdir(parents=True)
    if with_graph:
        (repo / "graphify-out" / "graph.json").write_text(json.dumps({
            "nodes": [
                {"id": "mcp_server_tools_debugger_register_debugger", "label": "Debugger",
                 "_callable": True, "source_file": "mcp_server/tools/debugger.py",
                 "source_location": "L10"},
                {"id": "mcp_server_models_debugger_session", "label": "Session",
                 "_callable": True, "source_file": "mcp_server/models/debugger.py"},
                {"id": "mcp_server_tools_scene_session_open", "label": "Open",
                 "_callable": True, "source_file": "mcp_server/tools/scene_session.py",
                 "source_location": "L5"},
                {"id": "unrelated_widget", "label": "W",
                 "_callable": True, "source_file": "other/widget.py"},
            ], "links": []}))
    repo_path = repo
    cfg = {"integrations": {"graphify": {"enabled": True, "graph_dir": "graphify-out"}},
           "repos": {"godot-mcp": {"path": str(repo), "graph_dir": "graphify-out"}}}
    import fabric_config as fc
    cm = contextlib.ExitStack()
    cm.enter_context(mock.patch.object(fc, "get_config", return_value=cfg))
    cm.enter_context(mock.patch.object(fc, "is_integration_active", lambda c, n: True))
    cm.enter_context(mock.patch.object(fc, "get_all_repo_names", return_value=["godot-mcp"]))
    cm.enter_context(mock.patch.object(fc, "get_repo_config",
                                       return_value={"path": str(repo), "graph_dir": "graphify-out"}))
    cm.enter_context(mock.patch.object(fc, "resolve_repo_path", return_value=repo))
    return cm


class TestCodeNavigation:
    def test_task_to_ranked_files(self, tmp_path):
        with _make_fabric(tmp_path):
            nav = ctx.code_navigation("fix debugger session", "godot-mcp")
        assert nav, "graphify on + graph present must produce navigation"
        r = nav[0]
        assert r["repo"] == "godot-mcp"
        files = [f["path"] for f in r["files"]]
        assert files[0] == "mcp_server/tools/debugger.py", files
        assert "other/widget.py" not in files

    def test_disabled_returns_none(self, tmp_path):
        cm = _make_fabric(tmp_path)
        import fabric_config as fc
        cm.enter_context(mock.patch.object(fc, "is_integration_active", lambda c, n: False))
        with cm:
            assert ctx.code_navigation("fix debugger leak", "godot-mcp") is None

    def test_no_graph_returns_none(self, tmp_path):
        cm = _make_fabric(tmp_path, with_graph=False)
        with cm:
            assert ctx.code_navigation("fix debugger leak", "godot-mcp") is None

    def test_no_token_overlap_returns_none(self, tmp_path):
        cm = _make_fabric(tmp_path)
        with cm:
            assert ctx.code_navigation("payroll reimbursement task", "godot-mcp") is None
