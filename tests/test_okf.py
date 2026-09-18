"""Tests for lint.py --okf (OKF v0.2 §11 conformance floor).

Run: python3 -m pytest tests/test_okf.py -v
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

FIXTURES = Path(__file__).parent / "fixtures" / "okf"
import lint


def _run_okf(path):
    return lint.okf_conformance(Path(path))


class TestConformantBundle:
    def test_conformant_fixture_passes(self):
        v, meta = _run_okf(FIXTURES / "conformant")
        assert v == [], f"expected conformant, got: {v}"
        assert meta["okf_version"] == "0.2"

    def test_main_okf_flag(self, tmp_path, capsys):
        import subprocess
        r = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "lint.py"),
             "--okf", str(FIXTURES / "conformant")],
            capture_output=True, text=True)
        assert r.returncode == 0, r.stdout + r.stderr
        assert "conformant" in r.stdout


class TestViolations:
    def test_missing_frontmatter(self):
        v, _ = _run_okf(FIXTURES / "violations" / "no-frontmatter")
        codes = {c for c, _, _ in v}
        assert "OKF-FRONTMATTER" in codes

    def test_missing_type(self):
        v, _ = _run_okf(FIXTURES / "violations" / "no-type")
        codes = {c for c, _, _ in v}
        assert "OKF-TYPE" in codes

    def test_bad_log_heading(self):
        v, _ = _run_okf(FIXTURES / "violations" / "bad-log-heading")
        codes = {c for c, _, _ in v}
        assert "OKF-LOG" in codes

    def test_index_frontmatter_restriction(self):
        v, _ = _run_okf(FIXTURES / "violations" / "index-frontmatter")
        codes = {c for c, _, _ in v}
        assert "OKF-INDEX" in codes

    def test_json_output_has_okf_block(self):
        import subprocess, json
        r = subprocess.run(
            [sys.executable, str(Path(__file__).parent.parent / "scripts" / "lint.py"),
             "--okf", "--format", "json", str(FIXTURES / "violations" / "no-type")],
            capture_output=True, text=True)
        d = json.loads(r.stdout)
        assert d["mode"] == "okf"
        assert d["conformant"] is False
        assert d["violations"]


class TestMainBundle:
    def test_harness_is_conformant(self):
        v, _ = _run_okf(Path(__file__).parent.parent)
        assert v == [], f"harness must be OKF-conformant: {v}"


class TestStaleAfter:
    """OKF §5.5 stale_after lint checks."""

    def _check(self, fm, today=None):
        import datetime as dt
        from lint import check_stale_after
        return check_stale_after(fm, "test-page", today or dt.date(2026, 9, 17))

    def test_future_date_passes(self):
        e, w = self._check({"stale_after": "2027-01-01"})
        assert e is None and w is None

    def test_overdue_warns(self):
        e, w = self._check({"stale_after": "2026-09-01"})
        assert e is None and w is not None
        assert "overdue" in w

    def test_far_overdue_errors(self):
        e, w = self._check({"stale_after": "2026-01-01"})
        assert e is not None

    def test_invalid_instant_errors(self):
        e, w = self._check({"stale_after": "next-tuesday"})
        assert e is not None and "invalid" in e

    def test_iso_instant_accepted(self):
        e, w = self._check({"stale_after": "2027-06-01T00:00:00Z"})
        assert e is None and w is None

    def test_absent_ok(self):
        e, w = self._check({})
        assert e is None and w is None


class TestActors:
    """OKF §7 actor convention + §5.2 trust fields."""

    def test_actor_forms(self):
        from fabric_config import actor, get_config
        c = {"owner": "test-owner", "llm": {"model": "m1", "compiler_model": "m2"}}
        assert actor(c, "human") == "human:test-owner"
        assert actor(c, "agent", model="m2") == "agent/test-owner/m2"
        assert actor(c, "process", model="hook") == "process:hook"

    def test_lint_actor_re(self):
        import datetime as dt
        from lint import check_actors
        today = dt.date(2026, 9, 17)
        # valid
        assert check_actors({"generated": {"by": "agent/me/model-x"}}, "p") == []
        assert check_actors({"generated": {"by": "human:jane"}}, "p") == []
        assert check_actors({"generated": {"by": "process:ci"}}, "p") == []
        # invalid
        probs = check_actors({"generated": {"by": "jane"}}, "p")
        assert probs and "GENERATED" in probs[0]
        # verified invalid
        probs = check_actors({"verified": [{"by": "robot"}]}, "p")
        assert probs and "VERIFIED" in probs[0]

    def test_maturity2_needs_human_verification(self):
        import datetime as dt
        from lint import check_actors
        fm = {"type": "pattern", "status": "recommended", "maturity": 2,
              "verified": [{"by": "process:ci"}]}
        probs = check_actors(fm, "pattern-x")
        assert any("TRUST-TIER" in p for p in probs)
        fm["verified"].append({"by": "human:jane"})
        assert check_actors(fm, "pattern-x") == []


class TestTrustTier:
    def test_unverified(self):
        from context import trust_tier
        assert trust_tier({}) == "unverified"

    def test_machine_confirmed(self):
        from context import trust_tier
        assert trust_tier({"verified": [{"by": "process:ci"}]}) == "machine-confirmed"

    def test_human_reviewed(self):
        from context import trust_tier
        assert trust_tier({"verified": [{"by": "process:ci"}, {"by": "human:j"}]}) == "human-reviewed"

    def test_bare_mapping(self):
        from context import trust_tier
        assert trust_tier({"verified": {"by": "human:j"}}) == "human-reviewed"


class TestAttestedComputation:
    def test_ac_pages_conform(self):
        from lint import okf_conformance
        v, _ = okf_conformance(Path(__file__).parent.parent)
        assert v == [], f"AC pages must conform: {v}"

    def test_golden_eval_attester(self, tmp_path, monkeypatch):
        """Attester reads registry/log.md from the fabric root; seed a receipt
        in a temp fabric and run the attester from there."""
        import subprocess
        import json
        import datetime as dt
        repo = Path(__file__).parent.parent
        (tmp_path / "registry").mkdir()
        (tmp_path / "registry" / "log.md").write_text(
            f"""---
type: log
title: Log
---

## {dt.date.today().isoformat()}
* **eval | formal golden corpus**

- Claim recall: 0.91 (threshold 0.8) — PASS
- Model: deepseek-v4.1-flash:cloud
""")
        att = repo / "references" / "attesters" / "check-golden-eval.py"
        # attester resolves FABRIC from __file__; monkeypatch by copying it into tmp
        (tmp_path / "attesters").mkdir()
        src = att.read_text().replace(
            'Path(__file__).resolve().parent.parent.parent',
            f'Path("{tmp_path}")')
        att2 = tmp_path / "check-golden-eval.py"
        att2.write_text(src)
        r = subprocess.run([sys.executable, str(att2), "--model", "deepseek-v4.1-flash:cloud"],
                           capture_output=True, text=True)
        d = json.loads(r.stdout)
        assert d["verdict"] == "ATTESTED"
        assert d["recall"] >= 0.8

    def test_lint_attester(self, tmp_path, monkeypatch):
        """Self-contained: copy the repo harness into tmp (no evidence content),
        seed a claim, then run the attester against it."""
        import subprocess
        import json
        import shutil
        repo = Path(__file__).parent.parent
        # copy harness, strip evidence + registry runtime state
        shutil.copytree(repo, tmp_path, dirs_exist_ok=True, ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", ".okflint", ".pytest_cache",
            ".obsidian", ".opencode", "node_modules", "evidence",
            "registry/catalog.json"))
        (tmp_path / "registry").mkdir(exist_ok=True)
        (tmp_path / "registry" / "log.md").write_text(
            "---\ntype: log\ntitle: Log\n---\n\n# Log\n")
        (tmp_path / "evidence" / "claims").mkdir(parents=True)
        (tmp_path / "evidence" / "claims" / "claim-x.md").write_text(
            "---\ntype: claim\nid: claim-x\nstatus: supported\n"
            'statement: "Test."\nsource_refs:\n'
            '  - source: "[[src-x]]"\n    locator: "L1"\n    quote: "Test."\n'
            "resource: \"[[src-x]]\"\n---\n\n# x\n")
        att = repo / "references" / "attesters" / "check-zero-errors.py"
        src = att.read_text().replace(
            'FABRIC = Path(__file__).resolve().parent.parent.parent',
            f'FABRIC = Path("{tmp_path}")')
        att2 = tmp_path / "check-zero-errors.py"
        att2.write_text(src)
        r = subprocess.run([sys.executable, str(att2)], capture_output=True, text=True)
        d = json.loads(r.stdout)
        assert d["verdict"] == "ATTESTED" and d["errors"] == 0


class TestIgnores:
    """fabric.yaml ignore section (globs + regexes + per-repo merge)."""

    def _cfg(self):
        return {
            "ignore": {
                "globs": ["vendor/**", "*.log"],
                "regexes": ["_archive\\d+/"],
                "projects": {"my-project": {"globs": ["addons/generated/**"]}},
            }
        }

    def test_glob_starstar(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores(self._cfg())
        assert is_ignored("vendor/x.md", ig)
        assert is_ignored("vendor/a/b/x.md", ig)
        assert not is_ignored("src/x.md", ig)

    def test_single_glob_basename(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores(self._cfg())
        assert is_ignored("deep/nested/x.log", ig)
        assert not is_ignored("deep/nested/x.md", ig)

    def test_regex(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores(self._cfg())
        assert is_ignored("a/_archive2/old.md", ig)
        assert not is_ignored("a/archives/x.md", ig)

    def test_per_repo_merge(self):
        from fabric_config import get_ignores, is_ignored
        ig_g = get_ignores(self._cfg(), "my-project")
        assert is_ignored("addons/generated/x.md", ig_g)
        assert is_ignored("vendor/x.md", ig_g)  # global still applies
        ig_other = get_ignores(self._cfg(), "other")
        assert not is_ignored("addons/generated/x.md", ig_g if False else get_ignores(self._cfg(), "other"))

    def test_no_section_noop(self):
        from fabric_config import get_ignores, is_ignored
        ig = get_ignores({})
        assert not is_ignored("anything.md", ig)
