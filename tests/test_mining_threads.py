"""Unit tests for mining with thread signals (#103).

Run: python3 -m pytest tests/test_mining_threads.py -v
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


ts = _load("thread_signals", Path(__file__).parent.parent / "scripts/lib/thread_signals.py")
mp = _load("mine_promotions_t", Path(__file__).parent.parent / "scripts/cmd/mine-promotions.py")

GRAPH = ts.build_graph({
    "nodes": [
        {"session": "ses-A", "kind": "chat-session", "project": "p1",
         "files_touched": ["a.py", "b.py"]},
        {"session": "ses-B", "kind": "chat-session", "project": "p2",
         "files_touched": ["a.py", "c.py"]},
        {"session": "ses-C", "kind": "chat-session", "project": "p3",
         "files_touched": ["z.py"]},
    ],
    "edges": [
        {"type": "continues", "source_session": "ses-B", "target": "ses-A"},
    ],
})


def _ev(project, session=None, problem="bug", intervention="fix"):
    return {"project": project, "session": session,
            "observed_problem": problem, "intervention": intervention,
            "outcomes": {"happy_path": "yes"}}


class TestThreadBoost:
    def test_same_session(self):
        boost, reasons = ts.thread_boost(_ev("p1", "ses-A"), _ev("p1", "ses-A"), GRAPH)
        assert boost == 0.4 and "same_session" in reasons

    def test_files_overlap(self):
        boost, reasons = ts.thread_boost(_ev("p1", "ses-A"), _ev("p2", "ses-B"), GRAPH)
        assert boost == 0.5  # files_overlap 0.2 + continuation 0.3
        assert any(r.startswith("files_overlap") for r in reasons)
        assert "continuation" in reasons

    def test_unconnected_zero(self):
        boost, reasons = ts.thread_boost(_ev("p1", "ses-A"), _ev("p2", "ses-C"), GRAPH)
        assert boost == 0.0 and reasons == []

    def test_no_session_zero(self):
        boost, reasons = ts.thread_boost(_ev("p1"), _ev("p2"), GRAPH)
        assert boost == 0.0 and reasons == []

    def test_capped(self):
        # same-session + continuation + overlap cannot co-occur, but cap guards stacking
        g = ts.build_graph({"nodes": [{"session": "s", "files_touched": ["a.py", "b.py", "c.py"]}],
                            "edges": [{"type": "continues", "source_session": "s", "target": "s"}]})
        boost, _ = ts.thread_boost(_ev("p", "s"), _ev("p", "s"), g)
        assert boost <= 0.9


class TestClassifyPair:
    def test_text_decides_normally(self):
        merge, why = ts.classify_pair(_ev("p", "s1"), _ev("p", "s2"), GRAPH, 0.9, 0.5)
        assert merge and why == "text"

    def test_thread_rescue_near_miss(self):
        # ses-A + ses-B: overlap 0.2 + continuation 0.3 = 0.5 boost
        merge, why = ts.classify_pair(_ev("p1", "ses-A"), _ev("p2", "ses-B"), GRAPH, 0.0, 0.5)
        assert merge and why.startswith("thread:") and "continuation" in why

    def test_below_threshold_not_merged(self):
        merge, why = ts.classify_pair(_ev("p1", "ses-A"), _ev("p2", "ses-C"), GRAPH, 0.0, 0.5)
        assert not merge and why == ""

    def test_no_graph_falls_back_to_text(self):
        merge, why = ts.classify_pair(_ev("p1"), _ev("p2", "s"), ({}, {}, set()), 0.6, 0.5)
        assert merge and why == "text"


class TestThreadContext:
    def test_context_rendered(self):
        ctx = ts.thread_context(_ev("p1", "ses-A"), _ev("p2", "ses-B"), GRAPH)
        assert "[thread context:" in ctx
        assert "touched shared files" in ctx
        assert "continues the other" in ctx

    def test_unconnected_empty(self):
        assert ts.thread_context(_ev("p1", "ses-A"), _ev("p2", "ses-C"), GRAPH) == ""


class TestFailOpen:
    def test_missing_index_loads_none(self, tmp_path, monkeypatch):
        monkeypatch.setattr(ts, "THREADS_PATH", tmp_path / "none.json")
        assert ts.load_index() is None
        g = ts.build_graph(ts.load_index())
        assert g == ({}, {}, set())

    def test_boost_zero_without_graph(self):
        boost, _ = ts.thread_boost(_ev("p", "ses-A"), _ev("q", "ses-A"), ({}, {}, set()))
        assert boost == 0.4  # same_session needs no index data beyond the events


class TestDossierCitations:
    def test_session_citations(self):
        events = [_ev("p1", "ses-A")]
        index = {"nodes": [{"session": "ses-A", "kind": "chat-session",
                            "harness": "opencode", "project": "p1",
                            "file": "evidence/raw/p1/chats/s1.md",
                            "files_touched": ["a.py"]}]}
        import unittest.mock as mock
        with mock.patch.object(ts, "load_index", lambda: index):
            out = mp._dossier_thread_citations(events)
        assert "ses-A" in out and "wf thread ses-A" in out

    def test_pr_citations(self):
        events = [_ev("p2", "ses-PR")]
        index = {"nodes": [{"session": "ses-PR", "kind": "pr-record", "pr": 42,
                            "pr_state": "closed", "file": "evidence/raw/p2/git/pr-42.md"}]}
        import unittest.mock as mock
        with mock.patch.object(ts, "load_index", lambda: index):
            out = mp._dossier_thread_citations(events)
        assert "PR #42" in out

    def test_no_index_empty(self, monkeypatch):
        monkeypatch.setattr(ts, "load_index", lambda: None)
        assert mp._dossier_thread_citations([_ev("p", "s")]) is None

    def test_events_without_sessions_none(self, monkeypatch):
        monkeypatch.setattr(ts, "load_index", lambda: {"nodes": [], "edges": []})
        assert mp._dossier_thread_citations([_ev("p")]) is None


class TestSameRecurrenceContext:
    def test_context_flows_into_state(self, monkeypatch):
        import judgment
        captured = {}
        def fake_noul(question, state, **kw):
            captured["state"] = state
            return 0.9
        monkeypatch.setattr(judgment, "noul", fake_noul)
        judgment.same_recurrence("A text", "B text", threshold=0.8,
                                 context="[thread context: shared files]")
        assert "[thread context: shared files]" in captured["state"]

    def test_no_context_unchanged(self, monkeypatch):
        import judgment
        captured = {}
        def fake_noul(question, state, **kw):
            captured["state"] = state
            return 0.9
        monkeypatch.setattr(judgment, "noul", fake_noul)
        judgment.same_recurrence("A", "B", threshold=0.8)
        assert captured["state"] == "Item A: A\n\nItem B: B"