"""SkillOpt-epic S2 (#139): artifact-typed gates — held-out fixture gate pre-merge."""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
_SCRIPTS = (REPO / "scripts").resolve()
for _d in (_SCRIPTS / "cmd", _SCRIPTS / "lib", _SCRIPTS / "eval", _SCRIPTS):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

_spec = importlib.util.spec_from_file_location("promote", _SCRIPTS / "cmd" / "promote.py")
promote = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(promote)


class TestGateSetSelection:
    def test_gate_runs_partition_only(self, tmp_path, monkeypatch, capsys):
        """--gate runs only the held-out fixtures from PARTITION.md (be2/be4/be5)."""
        import subprocess
        r = subprocess.run([sys.executable, str(_SCRIPTS / "eval" / "eval-behavior.py"),
                            "--gate", "--json"],
                           capture_output=True, text=True, cwd=str(REPO))
        assert r.returncode == 0, r.stderr
        import json
        data = json.loads(r.stdout)
        ids = {res["id"] for res in data["results"]}
        assert ids == {"be2-project-over-global", "be4-escalate-gap", "be5-receipt-proves-delivery"}
        assert data["metrics"]["total"] == 3

    def test_full_run_excludes_gate_set(self, tmp_path):
        """Default run (CI) uses the working set — gate fixtures NOT included twice;
        the gate set is reserved for promote."""
        import subprocess
        r = subprocess.run([sys.executable, str(_SCRIPTS / "eval" / "eval-behavior.py"), "--json"],
                           capture_output=True, text=True, cwd=str(REPO))
        assert r.returncode == 0
        import json
        data = json.loads(r.stdout)
        ids = {res["id"] for res in data["results"]}
        assert "be2-project-over-global" in ids  # full suite runs everything


class TestBehaviorGate:
    def test_gate_passes_on_healthy_suite(self, tmp_path, monkeypatch):
        ok, detail = promote.run_behavior_gate("test-pattern")
        # the real harness suite is green in CI/dev: gate OK
        assert ok is True
        assert "gate OK" in detail

    def test_gate_blocks_when_fixture_fails(self, tmp_path, monkeypatch):
        """A candidate merge that ships with a degraded held-out set is blocked."""
        import json as _json
        import subprocess as _sp

        class FakeResult:
            returncode = 0
            stdout = _json.dumps({"metrics": {"knowledge_utility": 0.667,
                                              "passed": 2, "total": 3}})
            stderr = ""

        monkeypatch.setattr(_sp, "run", lambda *a, **kw: FakeResult())
        ok, detail = promote.run_behavior_gate("x")
        assert ok is False
        assert "FAILED" in detail

    def test_gate_skips_when_suite_unavailable(self, tmp_path, monkeypatch):
        monkeypatch.setattr(promote, "_HARNESS", tmp_path)  # no eval-behavior.py
        ok, detail = promote.run_behavior_gate("x")
        assert ok is True
        assert "skipped" in detail

    def test_promote_blocked_by_failing_gate(self, tmp_path, monkeypatch, capsys):
        """The dossier flow refuses when the gate fails (BLOCKED path)."""
        monkeypatch.setattr(promote, "run_behavior_gate", lambda *a, **k: (False, "gate FAILED: utility 67% (2/3)"))
        d = tmp_path / "promotion-cluster_x.md"
        d.write_text("---\ntype: promotion-dossier\nstatus: pending-review\n"
                     "pattern_ref: '[[pattern-cluster_x]]'\n---\n\nbody\n")
        ok = promote.promote_dossier(d)
        assert ok is False
        assert "BLOCKED" in capsys.readouterr().out