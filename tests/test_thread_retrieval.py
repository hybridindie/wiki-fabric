"""Unit tests for thread retrieval consumers (#104).

Run: python3 -m pytest tests/test_thread_retrieval.py -v
"""

import json
import sys
import importlib.util
from pathlib import Path

import sys, pathlib as _p
_SCRIPTS = (_p.Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", "eval", "harness"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


thread = _load("thread_mod", Path(__file__).parent.parent / "scripts/cmd/thread.py")
query = _load("query_t", Path(__file__).parent.parent / "scripts/cmd/query.py")

INDEX = {
    "$schema": "wiki-fabric/threads-v1",
    "nodes": [
        {"file": "evidence/raw/proj/chats/2026-09-27-chat-s1.md", "kind": "chat-session",
         "project": "proj", "session": "ses-A", "harness": "opencode",
         "files_touched": ["scripts/a.py", "tests/b.py"]},
        {"file": "evidence/raw/proj2/git/pr-42.md", "kind": "pr-record",
         "project": "proj2", "pr": 42, "pr_state": "closed", "source_repo": "o/r",
         "merged_at": "2026-09-27"},
    ],
    "edges": [
        {"claim": "claim-proj-chats-2026-09-27-chat-s1-md-000", "type": "originated_in",
         "target": "src-proj-chats-2026-09-27-chat-s1-md"},
        {"claim": "claim-x", "type": "decided_in", "target": "src-proj2-git-pr-42-md"},
        {"claim": None, "type": "continues", "source_session": "ses-B", "target": "ses-A"},
    ],
}


class TestThreadCommand:
    def test_resolve_by_session_id(self):
        node = thread.resolve_node(INDEX, "ses-A")
        assert node and node["kind"] == "chat-session"

    def test_resolve_by_pr_number(self):
        node = thread.resolve_node(INDEX, "42")
        assert node and node["kind"] == "pr-record"

    def test_resolve_by_file_stem(self):
        node = thread.resolve_node(INDEX, "pr-42")
        assert node and node["pr"] == 42

    def test_resolve_miss_none(self):
        assert thread.resolve_node(INDEX, "nope") is None

    def test_claim_edges_matched_by_slug(self):
        node = thread.resolve_node(INDEX, "ses-A")
        edges = thread.claim_edges_for(INDEX, node)
        assert any(e["claim"].startswith("claim-proj-chats") for e in edges)

    def test_continuation_edges(self):
        node = thread.resolve_node(INDEX, "ses-A")
        rels = thread.related_sessions_for(INDEX, node)
        assert any(e["target"] == "ses-A" for e in rels)

    def test_neighborhood_and_render(self, capsys):
        nb = thread.neighborhood(INDEX, "ses-A")
        assert nb["node"]["session"] == "ses-A"
        assert nb["claim_edges"] and nb["related"]
        out = thread.render(nb)
        assert "Thread: ses-A" in out
        assert "files touched (2):" in out
        assert "originated_in" in out

    def test_json_shape(self, tmp_path, monkeypatch):
        monkeypatch.setattr(thread, "THREADS_PATH", tmp_path / "threads.json")
        (tmp_path / "threads.json").write_text(json.dumps(INDEX))
        import io, contextlib
        buf = __import__("io").StringIO()
        old_argv = sys.argv
        sys.argv = ["thread.py", "ses-A", "--json"]
        try:
            with contextlib_redirect_stdout(buf):
                rc = thread.main()
        finally:
            sys.argv = old_argv
        assert rc == 0
        data = json.loads(buf.getvalue())
        assert data["node"]["session"] == "ses-A"


def contextlib_redirect_stdout(buf):
    import contextlib, io
    return contextlib.redirect_stdout(buf)


class TestGateOnAbsentIndex:
    def test_load_index_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(thread, "THREADS_PATH", tmp_path / "missing.json")
        assert thread.load_index() is None

    def test_neighborhood_none_on_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(thread, "THREADS_PATH", tmp_path / "missing.json")
        assert thread.neighborhood(thread.load_index(), "ses-A") is None

    def test_main_reports_missing_index(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setattr(thread, "THREADS_PATH", tmp_path / "missing.json")
        old_argv = sys.argv
        sys.argv = ["thread.py", "ses-A"]
        try:
            rc = thread.main()
        finally:
            sys.argv = old_argv
        assert rc == 2


class TestQueryLineage:
    def test_lineage_shaped_query_matches(self):
        hits = query.thread_lineage(
            "where did this come from", [(0.9, _claim())], "concept", index=INDEX)
        assert len(hits) == 1
        claim_pg, node, edge_type = hits[0]
        assert node["session"] == "ses-A"
        assert edge_type == "originated_in"

    def test_non_lineage_query_noop(self):
        hits = query.thread_lineage("fix the parser", [(0.9, _claim())], "concept", index=INDEX)
        assert hits == []

    def test_gate_off_noop(self, monkeypatch):
        import unittest.mock as mock
        with mock.patch.object(query, "load_thread_index", lambda: None):
            assert query.thread_lineage("where did this come from",
                                        [(0.9, _claim())], "concept") == []  # gate mocked off

    def test_pr_node_resolved(self):
        claim = _claim(relations=[{"type": "decided_in", "target": "[[src-proj2-git-pr-42-md]]"}])
        hits = query.thread_lineage("where was this decided", [(0.9, claim)], "decision", index=INDEX)
        assert hits and hits[0][1]["kind"] == "pr-record"

    def test_answer_renders_lineage_section(self):
        hits = query.thread_lineage("where did this come from", [(0.9, _claim())], "concept", index=INDEX)
        answer = query.generate_answer("where did this come from", [(0.9, _claim())],
                                       [_claim()], "concept", thread_hits=hits)
        assert "## Lineage (evidence graph)" in answer
        assert "originated_in" in answer
        assert "2026-09-27-chat-s1.md" in answer

    def test_answer_without_hits_no_section(self):
        answer = query.generate_answer("where", [], [], "concept", thread_hits=[])
        assert "Lineage" not in answer


def _claim(relations=None):
    return {"fm": {"type": "claim", "statement": "A claim from a session.",
                   "relations": relations or [{"type": "originated_in",
                                               "target": "[[src-proj-chats-2026-09-27-chat-s1-md]]"}]},
            "type": "claim", "stem": "claim-x", "body": "",
            "rel": Path("evidence/claims/claim-x.md")}
