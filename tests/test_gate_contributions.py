"""Gate contribution-freshness signal (#159-adjacent, #160 S5): connected
projects whose knowledge channels (experience-events, chats, git captures)
have gone dark surface in wf gate as INFO — never actionable by themselves.

Run: python3 -m pytest tests/test_gate_contributions.py -v
"""

import sys
import pytest
import importlib.util
from datetime import date, timedelta
from pathlib import Path

_SCRIPTS = (Path(__file__).resolve().parent.parent / "scripts").resolve()
for _rel in ("cmd", "lib", ""):
    _d = _SCRIPTS / _rel if _rel else _SCRIPTS
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))


def _load_gate():
    spec = importlib.util.spec_from_file_location("gate_contribs", _SCRIPTS / "cmd/gate.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["gate_contribs"] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture()
def fabric(tmp_path, monkeypatch):
    import layout
    import fabric_config
    monkeypatch.setattr(fabric_config, "CORPUS_ROOT", tmp_path, raising=False)
    import gate as g
    # _gate_contributions imports CORPUS_ROOT inside the function from fabric_config ✓
    projects = tmp_path / "projects"
    raw = tmp_path / "evidence" / "raw"
    for d in ("projects", "evidence/raw", "domains", "registry"):
        (tmp_path / d).mkdir(parents=True, exist_ok=True)
    return g, tmp_path


def _ev(project, created, tmp_path):
    d = tmp_path / "projects" / project / "experience-events"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"ee-{created}-{project}.md").write_text(
        f"---\ntype: experience-event\nproject: {project}\ncreated: {created}\n---\n\nbody\n")


def _chat(project, day, tmp_path):
    d = tmp_path / "evidence" / "raw" / project / "chats"
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{day}-chat-x.md").write_text("---\ntype: source\n---\n")


def _gitmark(project, day, tmp_path):
    d = tmp_path / "evidence" / "raw" / project / "git"
    d.mkdir(parents=True, exist_ok=True)
    (d / ".last-capture").write_text(day)


class TestContributionsSignal:
    def test_all_channels_fresh_no_report(self, fabric):
        g, tmp = fabric
        recent = (date.today() - timedelta(days=2)).isoformat()
        _ev("alpha", recent, tmp)
        rows, _ = g._gate_contributions(stale_days=30)
        assert rows == []

    def test_dark_project_reported(self, fabric):
        g, tmp = fabric
        old = (date.today() - timedelta(days=45)).isoformat()
        _ev("alpha", old, tmp)
        _gitmark("alpha", old, tmp)
        rows, _ = g._gate_contributions(stale_days=30)
        assert len(rows) == 1
        assert rows[0]["project"] == "alpha"
        assert rows[0]["stale_days"] >= 45

    def test_never_contributed_reported(self, fabric):
        g, tmp = fabric
        (tmp / "projects" / "ghost").mkdir(parents=True)
        rows, _ = g._gate_contributions(stale_days=30)
        assert rows == [{"project": "ghost", "last": "never", "stale_days": None}]

    def test_channels_feed_one_recency(self, fabric):
        g, tmp = fabric
        _ev("alpha", "2026-01-01", tmp)           # events ancient
        _chat("alpha", (date.today() - timedelta(days=3)).isoformat(), tmp)
        rows, _ = g._gate_contributions(stale_days=30)
        assert rows == []  # the chat capture keeps the loop alive

    def test_git_capture_keeps_loop_alive(self, fabric):
        g, tmp = fabric
        _ev("alpha", "2026-01-01", tmp)
        _gitmark("alpha", (date.today() - timedelta(days=1)).isoformat(), tmp)
        rows, _ = g._gate_contributions(stale_days=30)
        assert rows == []


class TestGateSurfaces:
    def test_contributions_never_actionable(self, fabric, monkeypatch):
        g, tmp = fabric
        (tmp / "projects" / "ghost").mkdir(parents=True)
        (tmp / "evidence" / "raw" / "ghost" / "git").mkdir(parents=True)
        monkeypatch.setattr(g, "_gate_review", lambda: (1, [{"file": "x", "overdue_days": 1}], None))
        monkeypatch.setattr(g, "_gate_promotions", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_domains", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_pattern_candidates", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_questions", lambda: ([], [], None))
        sections, actionable = g.gate()
        # review pending makes it actionable; contributions alone must not
        monkeypatch.setattr(g, "_gate_review", lambda: ([], [], None))
        sections, actionable = g.gate()
        assert actionable is False
        assert sections["contributions"][1]  # but the report is there

    def test_manifest_lists_dark_sources(self, fabric, monkeypatch, tmp_path):
        g, tmp = fabric
        (tmp / "projects" / "ghost").mkdir(parents=True)
        (tmp / "evidence" / "raw" / "ghost").mkdir(parents=True)
        monkeypatch.setattr(g, "_gate_review", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_promotions", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_domains", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_pattern_candidates", lambda: ([], [], None))
        monkeypatch.setattr(g, "_gate_questions", lambda: ([], [], None))
        sections, actionable = g.gate()
        manifest = tmp_path / "pending-gate.md"
        g._write_manifest(manifest, sections, actionable)
        text = manifest.read_text()
        assert "ghost" in text
        assert "no captured history" in text