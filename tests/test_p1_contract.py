"""Unit tests for P1 lint additions: --format json, staleness, scope validation,
and registry JSON generation.

Run: python3 -m pytest tests/test_p1_contract.py -v
"""

import sys
import importlib.util
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "scripts"))


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


lint = _load_module("lint", REPO / "scripts" / "lint.py")


class TestScopeValidation:
    def test_global_scope_matches_global_path(self):
        rel = Path("patterns/pattern-x.md")
        fm = {"type": "pattern", "scope": "global"}
        assert lint.validate_scope(fm, rel) is None

    def test_project_scope_matches_projects_path(self):
        rel = Path("projects/my-project/decisions/d.md")
        fm = {"type": "decision", "scope": "project"}
        assert lint.validate_scope(fm, rel) is None

    def test_domain_scope_matches_domains_path(self):
        rel = Path("domains/agent-systems/concepts/c.md")
        fm = {"type": "concept", "scope": "domain"}
        assert lint.validate_scope(fm, rel) is None

    def test_mismatch_is_error_string(self):
        rel = Path("patterns/pattern-x.md")
        fm = {"type": "pattern", "scope": "project"}
        err = lint.validate_scope(fm, rel)
        assert err and "SCOPE" in err and "project" in err and "global" in err

    def test_no_scope_declared_is_ok(self):
        rel = Path("patterns/pattern-x.md")
        assert lint.validate_scope({"type": "pattern"}, rel) is None

    def test_scope_for_registry_is_global(self):
        assert lint.scope_for(Path("registry/catalog.md")) == "global"
        assert lint.scope_for(Path("projects/p/decisions/d.md")) == "project"


class TestStaleness:
    def _today(self):
        import datetime
        return datetime.date.today()

    def test_future_review_after_passes(self):
        import datetime
        future = (self._today() + datetime.timedelta(days=30)).isoformat()
        e, w = lint.check_staleness({"review_after": future}, Path("patterns/x.md"), self._today())
        assert e is None and w is None

    def test_recently_overdue_warns(self):
        import datetime
        past = (self._today() - datetime.timedelta(days=10)).isoformat()
        e, w = lint.check_staleness({"review_after": past}, Path("patterns/x.md"), self._today())
        assert e is None and w and "overdue 10 day(s)" in w and "REVIEW-AFTER" in w

    def test_long_overdue_flagged_in_message(self):
        import datetime
        past = (self._today() - datetime.timedelta(days=100)).isoformat()
        e, w = lint.check_staleness({"review_after": past}, Path("patterns/x.md"), self._today())
        assert e is None and w and "overdue 100 days" in w and "re-verify" in w

    def test_invalid_date_is_error(self):
        e, _w = lint.check_staleness({"review_after": "soon"}, Path("patterns/x.md"), self._today())
        assert e and "invalid date" in e

    def test_missing_review_after_is_noop(self):
        e, w = lint.check_staleness({}, Path("patterns/x.md"), self._today())
        assert e is None and w is None


class TestJsonOutput:
    def test_json_report_shape(self, tmp_path):
        (tmp_path / "note.md").write_text("no frontmatter\n")
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "lint.py"), str(tmp_path), "--format", "json"],
            capture_output=True, text=True,
        )
        report = json.loads(out.stdout)
        assert set(report) >= {"vault", "pages", "errors", "warnings", "counts", "ok", "today"}
        assert report["ok"] is False
        assert report["counts"]["errors"] >= 1
        assert any(e["code"] == "FRONTMATTER" for e in report["errors"])

    def test_json_clean_report(self, tmp_path):
        (tmp_path / "ok.md").write_text("---\ntype: registry\n---\n\n# Hub\n")
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "lint.py"), str(tmp_path), "--format", "json"],
            capture_output=True, text=True,
        )
        report = json.loads(out.stdout)
        assert report["ok"] is True
        assert report["counts"]["errors"] == 0

    def test_json_exit_code_reflects_errors(self, tmp_path):
        (tmp_path / "bad.md").write_text("no frontmatter\n")
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "lint.py"), str(tmp_path), "--format", "json"],
            capture_output=True, text=True,
        )
        assert out.returncode == 1


class TestRegistryJson:
    def test_registry_json_generated_and_valid(self, tmp_path):
        evidence = tmp_path / "evidence" / "claims"
        evidence.mkdir(parents=True)
        (evidence / "claim-demo.md").write_text(
            "---\ntype: claim\nid: claim-demo\nstatus: supported\n"
            "statement: \"Demo\"\nlast_verified: 2026-01-01\n---\n\n# claim-demo\nDemo body\n"
        )
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "rebuild-index.py"), "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        reg = tmp_path / "registry" / "index.json"
        assert reg.exists(), f"index.json not generated: {out.stdout} {out.stderr}"
        data = json.loads(reg.read_text())
        assert set(data) >= {"generated", "counts", "total", "pages"}
        stems = {p["stem"] for p in data["pages"]}
        assert "claim-demo" in stems
        page = next(p for p in data["pages"] if p["stem"] == "claim-demo")
        assert page["type"] == "claim"
        assert page["status"] == "supported"
        assert page["scope"] == "global"
        assert page["category"] in ("claims", "other")

    def test_scope_fallback_in_json(self, tmp_path):
        (tmp_path / "projects" / "proj-a" / "experience-events").mkdir(parents=True)
        f = tmp_path / "projects" / "proj-a" / "experience-events" / "ee-demo.md"
        f.write_text("---\ntype: experience-event\nproject: proj-a\ntitle: T\n---\n\n# x\n")
        subprocess.run(
            [sys.executable, str(REPO / "scripts" / "rebuild-index.py"), "--root", str(tmp_path)],
            capture_output=True, text=True,
        )
        reg = tmp_path / "registry" / "index.json"
        assert reg.exists()
        data = json.loads(reg.read_text())
        page = next((p for p in data["pages"] if p["stem"] == "ee-demo"), None)
        assert page and page["scope"] == "project"
        assert page["category"] == "experience_events"