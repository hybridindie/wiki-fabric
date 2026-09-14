"""Unit tests for eval-stability.py — reproducibility and sensitivity gates."""

import sys
import importlib.util
from pathlib import Path

REPO = Path(__file__).parent.parent


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


es = _load_module("eval_stability", REPO / "scripts" / "eval-stability.py")


class TestMetrics:
    def test_jaccard_basics(self):
        assert es.jaccard(set(), set()) == 1.0
        assert es.jaccard({"a"}, {"a"}) == 1.0
        assert es.jaccard({"a"}, {"b"}) == 0.0
        assert abs(es.jaccard({"a", "b"}, {"b", "c"}) - 1 / 3) < 1e-9

    def test_claim_normalization_handles_tilde_and_ticks(self, tmp_path):
        f = tmp_path / "claim-x.md"
        f.write_text('---\ntype: claim\nid: claim-x\nstatus: supported\n'
                     'statement: "Latency is ~100 ms for `cmd`"\n---\n')
        got = es.claim_statements(tmp_path)
        assert got == {"latency is approximately 100 ms for cmd"}

    def test_fuzzy_coverage_detects_paraphrase_as_close(self):
        a = {"writes serialize on the main thread"}
        b = {"writes are serialized on the main thread"}
        v = es.fuzzy_coverage(a, b)
        assert 0.4 < v < 0.9  # paraphrase scores high, not perfect

    def test_fuzzy_coverage_detects_missing_content(self):
        a = {"writes serialize on the main thread"}
        b = {"oauth tokens rotate on refresh"}
        assert es.fuzzy_coverage(a, b) < 0.2


class TestCIGate:
    def test_skip_llm_mode_passes(self):
        import subprocess
        out = subprocess.run(
            [sys.executable, str(REPO / "scripts" / "eval-stability.py"), "--skip-llm"],
            capture_output=True, text=True, timeout=300,
        )
        assert out.returncode == 0, out.stdout + out.stderr
        assert "G1" in out.stdout and "G2" in out.stdout
        assert "PASS" in out.stdout
