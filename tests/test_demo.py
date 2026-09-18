"""Unit tests for demo.sh — the P0 one-session value proof.

The demo must fail loudly if the context compiler stops delivering
behavior-changing knowledge. These tests run the demo and assert
the proof structure holds.
"""

import subprocess
from pathlib import Path

REPO = Path(__file__).parent.parent


def _run_demo(*extra):
    return subprocess.run(
        ["bash", str(REPO / "scripts" / "demo.sh"), *extra],
        capture_output=True, text=True, timeout=120,
    )


class TestDemo:
    def test_demo_passes_all_assertions(self):
        out = _run_demo()
        assert out.returncode == 0, f"demo failed:\n{out.stdout}\n{out.stderr}"
        # 4 proof assertions + fabric + seed = 6 checkmarks
        assert out.stdout.count("✓") >= 5

    def test_proof_lines_present(self):
        out = _run_demo()
        assert "anti-pattern warning delivered" in out.stdout
        assert "domain pattern delivered" in out.stdout
        assert "project decision delivered" in out.stdout
        assert "correct alternative delivered" in out.stdout
        assert "PROOF:" in out.stdout

    def test_prompt_contains_banned_approach(self):
        out = _run_demo()
        assert "Shared token cache across service instances" in out.stdout
        assert "DO NOT" in out.stdout
        assert "per-session" in out.stdout

    def test_prompt_labels_precedence(self):
        out = _run_demo()
        assert "BINDING DECISION" in out.stdout
        assert "Reason:" in out.stdout

    def test_json_output_is_valid_manifest(self):
        import json
        out = _run_demo("--json")
        data = json.loads(out.stdout)
        assert set(data) >= {"task", "selected", "excluded", "precedence"}
        stems = {s["stem"] for s in data["selected"]}
        assert "decision-rotation-over-sessions" in stems
        assert "anti-pattern-shared-token-cache" in stems
        # every selected item carries a reason
        assert all(s.get("reason") for s in data["selected"])