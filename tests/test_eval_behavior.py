"""Unit tests for eval-behavior.py — the P4 behavior evaluation runner.

Run: python3 -m pytest tests/test_eval_behavior.py -v
"""

import sys
import importlib.util
import json
import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


eb = _load_module("eval_behavior", REPO / "scripts" / "eval/eval-behavior.py")


class TestRunner:
    def test_all_fixtures_pass_zero_llm(self):
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "eval/eval-behavior.py")],
            capture_output=True, text=True, timeout=180,
        )
        assert out.returncode == 0, f"eval failed:\n{out.stdout}\n{out.stderr}"
        assert "Knowledge Utility: 100%" in out.stdout

    def test_json_report_metrics(self):
        import json
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "eval/eval-behavior.py"), "--json"],
            capture_output=True, text=True, timeout=180,
        )
        data = json.loads(out.stdout)
        assert data["metrics"]["knowledge_utility"] == 1.0
        assert data["metrics"]["total"] >= 4
        for r in data["results"]:
            assert r["ok"] is True
            assert all(c["passed"] for c in r["checks"])

    def test_be1_delivers_banned_knowledge(self):
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "eval/eval-behavior.py"), "--json"],
            capture_output=True, text=True, timeout=180,
        )
        data = json.loads(out.stdout)
        be1 = next(r for r in data["results"] if r["id"].startswith("be1"))
        assert "anti-pattern-shared-token-cache" in be1["selected"]
        kinds = {c["kind"] for c in be1["checks"]}
        assert "in_prompt" in kinds

    def test_be3_stale_pattern_excluded(self):
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "eval/eval-behavior.py"), "--json"],
            capture_output=True, text=True, timeout=180,
        )
        data = json.loads(out.stdout)
        be3 = next(r for r in data["results"] if r["id"].startswith("be3"))
        excl = be3["excluded"]
        assert any("stale" in e for e in excl)


class TestSeedIsolation:
    def test_seeded_fabric_compiles_without_repo_content(self, tmp_path):
        """Seeds alone (no repo content dirs) must produce a working manifest."""
        seeds = [
            {"path": "patterns/pattern-rotate.md", "type": "pattern",
             "status": "recommended", "maturity": 2,
             "body": "Rotate tokens on refresh for oauth."},
        ]
        eb.seed_fabric(tmp_path, seeds)
        manifest = eb.compile_manifest(tmp_path, "token rotation")
        assert any(s["stem"] == "pattern-rotate" for s in manifest["selected"])