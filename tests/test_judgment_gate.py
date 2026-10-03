"""G-J gate tests (#the-judgment-boundary): judge calibration eval, the
judgment_eval_recorded gate, the deterministic attester, and the gate wiring
at every call site (mining cluster/sweep/preflight, context borderline,
verify-effects).
"""

import json
import os
import re
import subprocess
import sys
import datetime as dt
from pathlib import Path
from unittest import mock

import pytest

_REPO = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO / "scripts"
for _rel in ("cmd", "lib", "eval"):
    if str(_SCRIPTS / _rel) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS / _rel))

import importlib.util as _ilu


def _load(name, path):
    spec = _ilu.spec_from_file_location(name, path)
    mod = _ilu.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _receipt_log(tmp_path, kind="cloud", model="jev-latest", verdict="PASS",
                 date=None, spread=(0.91, 0.25, 0.66), mining=(0.93, 0.61)):
    """A well-formed judgment-eval receipt in a seeded registry/log.md.
    spread=(pos, neg, spread) — pos 0.91 / neg 0.25 / spread 0.66 (the
    calibrated happy path: separation comfortably past every gate)."""
    date = date or dt.date.today().isoformat()
    pos, neg, spr = spread
    same, diff = mining
    log = tmp_path / "registry" / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"""## {date}
* **judgment-eval | {verdict}**
- judge: {kind} {model} route: cloud
- separation: spread {spr} (pos {pos} / neg {neg})
- mining_spread: same {same} / diff {diff}
- recorded: {date}
""")
    return log


class TestGateFn:
    def test_pass_receipt_for_current_identity(self, tmp_path):
        import judgment as J
        with mock.patch.object(J, "judge_identity", return_value=("cloud", "jev-latest")), \
             mock.patch.object(J, "CORPUS_LOG", return_value=tmp_path / "registry"):
            ok, why = J.judgment_eval_recorded(log_path=_receipt_log(tmp_path))
        assert ok, why
        assert "PASS" in why

    def test_fail_when_no_receipt(self, tmp_path):
        import judgment as J
        (tmp_path / "registry").mkdir()
        with mock.patch.object(J, "judge_identity", return_value=("cloud", "jev-latest")), \
             mock.patch.object(J, "CORPUS_LOG", return_value=tmp_path / "registry"):
            ok, why = J.judgment_eval_recorded(
                log_path=tmp_path / "registry" / "empty.md")
        assert not ok and "--record" in why

    def test_fail_on_JUDGE_SWAP(self, tmp_path):
        """The core case: a receipt for jev-latest does NOT satisfy a tev1 judge."""
        import judgment as J
        _receipt_log(tmp_path, kind="cloud", model="jev-latest")
        with mock.patch.object(J, "judge_identity", return_value=("cloud", "tev3")), \
             mock.patch.object(J, "CORPUS_LOG", return_value=tmp_path / "registry"):
            ok, why = J.judgment_eval_recorded(
                log_path=tmp_path / "registry" / "log.md")
        assert not ok and "tev3" in why

    def test_fail_on_FAILED_receipt(self, tmp_path):
        import judgment as J
        _receipt_log(tmp_path, verdict="FAIL")
        with mock.patch.object(J, "judge_identity", return_value=("cloud", "jev-latest")), \
             mock.patch.object(J, "CORPUS_LOG", return_value=tmp_path / "registry"):
            ok, why = J.judgment_eval_recorded(
                log_path=tmp_path / "registry" / "log.md")
        assert not ok

    def test_env_override_is_loud(self, tmp_path, monkeypatch):
        import judgment as J
        monkeypatch.setenv("WIKI_JUDGE_GATE", "0")
        ok, why = J.judgment_eval_recorded(log_path=tmp_path / "nope" / "log.md")
        assert ok and "SKIPPED" in why  # named, never silent

    def test_kind_mismatch_refuses(self, tmp_path):
        """A cloud receipt doesn't calibrate a systemone judge."""
        import judgment as J
        _receipt_log(tmp_path, kind="cloud", model="jev-latest")
        with mock.patch.object(J, "judge_identity", return_value=("systemone", "tev1:latest")), \
             mock.patch.object(J, "CORPUS_LOG", return_value=tmp_path / "registry"):
            ok, _ = J.judgment_eval_recorded(log_path=tmp_path / "registry" / "log.md")
        assert not ok


class TestCallSiteWiring:
    def _event(self, i, problem, intervention="did the fix"):
        return {"id": f"ee-{i}", "observed_problem": problem,
                "intervention": intervention, "outcomes": "fixed=ok",
                "project": "p1"}

    def test_mine_clusters_refused_when_uncalibrated(self, capsys, monkeypatch):
        """mine-promotions' judged clustering must fall back to keyword (and
        SAY so) when the G-J gate refuses — never a silent keyword downgrade."""
        monkeypatch.delenv("WIKI_JUDGE_GATE", raising=False)
        # two lineages (independent_projects counts DISTINCT LINEAGES) + a
        # text-near pair so the keyword pass merges them on its own
        events = [self._event(1, "alpha problem with the graph import"),
                  self._event(2, "alpha problem with the graph import again"),
                  self._event(3, "unrelated beta matter entirely different")]
        events[0]["lineage"] = "p1"
        events[1]["lineage"] = "p2"
        MP = _load(f"mine_promotions_gj_{abs(hash(str(events))) % 10000}",
                   _SCRIPTS / "cmd" / "mine-promotions.py")
        with mock.patch("judgment.judgment_eval_recorded",
                        return_value=(False, "no judgment-eval PASS receipt for judge cloud:jev-latest")), \
             mock.patch("judgment.judgment_route", return_value="cloud"):
            clusters = MP.cluster_events_judged(events, min_projects=1)
        cap = capsys.readouterr()
        everything = (cap.out + cap.err)
        assert "G-J" in everything and "keyword" in everything
        # the deterministic result stands: the keyword pass merged its own
        # set (loose Jaccard, recall-biased by design) — the judged refinement
        # (merges/splits) is what got gated off
        members = sorted(e["id"] for e in next(iter(clusters.values())))
        assert {"ee-1", "ee-2"} <= set(members)

    def test_mine_preflight_message(self, capsys, monkeypatch):
        """main()'s preflight surfaces the G-J refusal with the override hint."""
        import importlib
        mp_src = (_SCRIPTS / "cmd" / "mine-promotions.py").read_text()
        assert "WIKI_JUDGE_GATE=0" in mp_src  # the loud-off hint is present
        assert "G-J pre-flight" in mp_src

    def test_judgment_module_exports_gate(self):
        import judgment as J
        assert callable(J.judgment_eval_recorded)
        assert callable(J.judge_identity)

    def test_context_and_verify_effects_reference_gate(self):
        # the wiring exists at the call sites (source-level contract — the
        # behavior itself is exercised above through the gate fn)
        ctx = (_SCRIPTS / "cmd" / "context.py").read_text()
        ve = (_SCRIPTS / "cmd" / "verify-effects.py").read_text()
        mp = (_SCRIPTS / "cmd" / "mine-promotions.py").read_text()
        assert "judgment_eval_recorded" in ctx
        assert "judgment_eval_recorded" in ve
        assert mp.count("judgment_eval_recorded") >= 2  # preflight + sweeps


class TestAttester:
    def _attester_copy(self, tmp_path):
        (tmp_path / "registry").mkdir(parents=True, exist_ok=True)
        return (_REPO / "references" / "attesters" /
                "check-judgment-eval.py").read_text()

    def _run_attester(self, tmp_path, extra=None):
        p = tmp_path / "check-judgment-eval.py"
        p.write_text(self._attester_copy(tmp_path))
        env = {**os.environ, "WIKI_FABRIC_DIR": str(tmp_path)}  # the receipt lives HERE
        env.pop("WIKI_JUDGE_GATE", None)
        return subprocess.run([sys.executable, str(p)] + (extra or []),
                              capture_output=True, text=True, env=env)

    def test_attests_good_receipt(self, tmp_path):
        _receipt_log(tmp_path)
        r = self._run_attester(tmp_path, extra=["--judge", "jev-latest"])
        d = json.loads(r.stdout)
        assert d["verdict"] == "ATTESTED"
        assert r.returncode == 0

    def test_refuses_missing_receipt(self, tmp_path):
        r = self._run_attester(tmp_path)
        assert json.loads(r.stdout)["verdict"] == "REFUSED"
        assert r.returncode == 1

    def test_refuses_out_of_gates(self, tmp_path):
        # spread below floor: pos 0.55 / neg 0.3 → separation 0.25 < 0.3
        _receipt_log(tmp_path, spread=(0.55, 0.3, 0.25), mining=(0.93, 0.4))
        r = self._run_attester(tmp_path, extra=["--judge", "jev-latest"])
        d = json.loads(r.stdout)
        assert d["verdict"] == "REFUSED" and "separation" in d["failed"]
        assert r.returncode == 1

    def test_threshold_inside_mining_spread(self, tmp_path):
        # mining window [0.5, 0.75] doesn't contain 0.8 → REFUSED
        _receipt_log(tmp_path, mining=(0.75, 0.5))
        r = self._run_attester(tmp_path, extra=["--judge", "jev-latest"])
        d = json.loads(r.stdout)
        assert d["verdict"] == "REFUSED" and "threshold_inside" in d["failed"]

    def test_fail_receipt_refused(self, tmp_path):
        _receipt_log(tmp_path, verdict="FAIL")
        r = self._run_attester(tmp_path, extra=["--judge", "jev-latest"])
        d = json.loads(r.stdout)
        assert d["verdict"] == "REFUSED" and "FAIL" in d["reason"]


class TestEvalScript:
    def test_threshold_constant_consistency(self):
        """The eval's pinned MINING_THRESHOLD == judgment's constant — the
        eval script itself asserts this too; keep the two honest."""
        import judgment as J
        src = (_REPO / "scripts" / "eval" / "eval-judgment.py").read_text()
        m = re.search(r"MINING_THRESHOLD = ([\d.]+)", src)
        assert m and float(m.group(1)) == J.MINING_THRESHOLD_DEFAULT

    def test_ac_page_conforms(self):
        from lint import okf_conformance
        v, _ = okf_conformance(_REPO)
        acj = [x for x in v if "ac-judgment-eval" in x]
        assert acj == [], f"ac-judgment-eval must conform: {acj}"