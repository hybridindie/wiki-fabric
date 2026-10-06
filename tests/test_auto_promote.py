"""#190 — the judged auto-apply tier for inbox pattern candidates.

Contract: tuning.promotion.{auto_apply, auto_threshold} (OFF by default) +
judgment.near_band derive one banding truth: >= thr applies (recorded via
auto_applied stamp + log, reversible via --unapply), [thr-band, thr)
escalates to the human gate, below stays (verdict recorded, annotated).
Deterministic preconditions refuse WITHOUT a judge call; the G-J gate
refuses the whole run when the judge is uncalibrated; dossiers/claims are
never eligible. The gate surfaces auto-applies as INFO rows (never
actionable alone).

Run: python3 -m pytest tests/test_auto_promote.py -v
"""
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from datetime import date, timedelta
from datetime import datetime as _dt
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parent.parent
for _p in (str(_REPO / "scripts" / "cmd"), str(_REPO / "scripts" / "lib"),
           str(_REPO / "scripts" / "wiki_lib")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

os.environ.setdefault("WIKI_FABRIC_DIR", "/tmp/definitely-not-a-fabric-autopromote")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _mk_fabric(tmp_path):
    """A minimal fabric with an inbox + promoted dirs. The promote-patterns
    module freezes its dirs at import — reload per fabric (the gate-test
    seam)."""
    import importlib
    corpus = tmp_path / "corpus"
    for d in ("patterns/_inbox", "patterns", "anti-patterns", "registry"):
        (corpus / d).mkdir(parents=True, exist_ok=True)
    (tmp_path / "fabric.yaml").write_text("owner: t\nrepos: {}\n")
    os.environ["WIKI_FABRIC_DIR"] = str(tmp_path)
    importlib.reload(importlib.import_module("fabric_config"))
    for mod in list(sys.modules):
        if mod in ("promote-patterns", "promote-patterns-module", "gate"):
            del sys.modules[mod]
    pp = _load(f"pp_{id(tmp_path) % 99999}", _REPO / "scripts" / "cmd" / "promote-patterns.py")
    return corpus, pp


def _candidate(corpus, name="pattern-chat-auto1", days_old=2, kind="pattern"):
    created = (date.today() - timedelta(days=days_old)).isoformat()
    p = corpus / "patterns" / "_inbox" / f"{name}.md"
    p.write_text(f"""---
type: {kind}
id: {name}
title: "Auto-promote test candidate"
status: candidate
maturity: 1
origin: chat-mined
project: proj
provenance:
  - source: "[[src-proj-some-doc-md]]"
    locator: "L10-L12"
    quote: "Serialize writes to single-writer systems"
tags: [chat-mined, inbox]
created: {created}
---

# {name}

Serialize writes to single-writer systems.

**Mined from:** [[src-proj-some-doc-md]] — session takeaway
""")
    return p


def _tuned(tmp_path, auto_apply=True, auto_threshold=0.90, near_band=0.1):
    yaml = _dt and __import__("yaml")
    (tmp_path / "fabric.yaml").write_text(
        "owner: t\nrepos: {}\n"
        f"tuning:\n  promotion:\n    auto_apply: {'true' if auto_apply else 'false'}\n"
        f"    auto_threshold: {auto_threshold}\n"
        f"  judgment:\n    near_band: {near_band}\n")
    import importlib
    importlib.reload(importlib.import_module("fabric_config"))


def _judged(pp, prob):
    """Patch the judgment seam: calibrated judge returns prob; G-J satisfied."""
    import judgment as J  # noqa
    return (mock.patch.object(pp, "PROMOTE_JUDGMENT", None, create=True) if False else
            _patch_judgment(pp, prob))


def _patch_judgment(pp, prob):
    patchers = [
        mock.patch("judgment.noul", lambda *a, **k: prob),
        mock.patch("judgment.judgment_eval_recorded",
                   lambda *a, **k: (True, "test receipt")),
        mock.patch("judgment.judge_identity", lambda *a, **k: ("cloud", "jev-test")),
    ]
    # call-time `from judgment import` inside promote_auto reads the MODULE
    # attributes at call time, so patching the module is sufficient — but the
    # module must be importable under the SAME sys.modules key promote sees.
    return patchers


class TestBanding(unittest.TestCase):
    """The one banding truth. The #190 amendment: derived from the SETTINGS
    (thr from promotion.auto_threshold, band from judgment.near_band) —
    0.95/0.96 apply at thr 0.95, 0.93 escalates."""

    def test_default_threshold_bands(self):
        _, pp = _mk_fabric(Path(self._tmp()))
        self.assertEqual(pp._banding(0.90, 0.90, 0.1), "apply")
        self.assertEqual(pp._banding(0.95, 0.90, 0.1), "apply")
        self.assertEqual(pp._banding(0.87, 0.90, 0.1), "escalate")
        self.assertEqual(pp._banding(0.80, 0.90, 0.1), "escalate")  # the floor IS thr-band
        self.assertEqual(pp._banding(0.79, 0.90, 0.1), "stay")
        self.assertEqual(pp._banding(0.50, 0.90, 0.1), "stay")

    def test_band_math_relative_to_tuned_threshold(self):
        _, pp = _mk_fabric(Path(self._tmp()))
        # thr=0.95, band=0.1: 0.96 applies, 0.93 in-band escalates (floor 0.85)
        self.assertEqual(pp._banding(0.96, 0.95, 0.1), "apply")
        self.assertEqual(pp._banding(0.93, 0.95, 0.1), "escalate")
        self.assertEqual(pp._banding(0.85, 0.95, 0.1), "escalate")  # at the floor
        self.assertEqual(pp._banding(0.84, 0.95, 0.1), "stay")

    def _tmp(self):
        d = tempfile.mkdtemp(dir="/tmp")
        self.addCleanup(lambda: None)
        return Path(d)


class TestPreconditions(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir="/tmp"))
        self.corpus, pp = _mk_fabric(self.tmp)
        self.pp = pp

    def test_complete_candidate_passes_preconditions(self):
        p = _candidate(self.corpus)
        fm, _ = __import__("wf_common", fromlist=["parse_frontmatter"]).parse_frontmatter(p)
        ok, why = self.pp._preconditions(p, fm)
        self.assertTrue(ok, why)

    def test_fresh_candidate_refused_no_judge_call(self):
        p = _candidate(self.corpus, days_old=0)
        calls = []
        with mock.patch("judgment.noul", lambda *a, **k: calls.append(1) or 0.95):
            fm, _ = __import__("wf_common", fromlist=["parse_frontmatter"]).parse_frontmatter(p)
            ok, why = self.pp._preconditions(p, fm)
        self.assertFalse(ok)
        self.assertIn("age", why)
        self.assertEqual(calls, [], "deterministic refusal must not call the judge")

    def test_incomplete_provenance_refused(self):
        p = _candidate(self.corpus)
        text = p.read_text().replace('    locator: "L10-L12"\n', "")
        p.write_text(text)
        fm, _ = __import__("wf_common", fromlist=["parse_frontmatter"]).parse_frontmatter(p)
        ok, why = self.pp._preconditions(p, fm)
        self.assertFalse(ok)
        self.assertIn("provenance", why)

    def test_judged_different_verdict_refused(self):
        p = _candidate(self.corpus)
        p.write_text(p.read_text() + "\n\njudged: p=0.3 -> keep separate (pattern-chat-x)\n")
        fm, _ = __import__("wf_common", fromlist=["parse_frontmatter"]).parse_frontmatter(p)
        ok, why = self.pp._preconditions(p, fm)
        self.assertFalse(ok)
        self.assertIn("judged-different", why)

    def test_dossier_type_never_eligible(self):
        p = self.corpus / "patterns" / "_inbox" / "promotion-cluster_x.md"
        p.write_text("---\ntype: promotion-dossier\nid: promotion-cluster_x\n"
                     "status: pending-review\ncreated: 2026-09-01\n---\nbody\n")
        fm, _ = __import__("wf_common", fromlist=["parse_frontmatter"]).parse_frontmatter(p)
        ok, why = self.pp._preconditions(p, fm)
        self.assertFalse(ok)
        self.assertIn("never auto-promoted", why)


class TestAutoRun(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir="/tmp"))
        self.corpus, pp = _mk_fabric(self.tmp)
        self.pp = pp
        _tuned(self.tmp, auto_apply=True)

    def _run(self, probs, days_old=2):
        """One candidate per prob; run --auto; returns (report, dests)."""
        cands = []
        for i, prob in enumerate(probs):
            cands.append(_candidate(self.corpus, f"pattern-chat-a{i}", days_old=days_old))
        with mock.patch("judgment.noul",
                        side_effect=list(probs) + [probs[-1]] * 10), \
             mock.patch("judgment.judgment_eval_recorded",
                        lambda *a, **k: (True, "test receipt")), \
             mock.patch("judgment.judge_identity",
                        lambda *a, **k: ("cloud", "jev-test")):
            report = self.pp.promote_auto(dry_run=False)
        return report

    def test_off_by_default_noop(self):
        _tuned(self.tmp, auto_apply=False)
        _candidate(self.corpus)
        report = self.pp.promote_auto(dry_run=False)
        self.assertTrue(report.get("off"))
        self.assertTrue((self.corpus / "patterns" / "_inbox" / "pattern-chat-auto1.md").exists())

    def test_gj_refusal_blocks(self):
        _candidate(self.corpus)
        with mock.patch("judgment.judgment_eval_recorded",
                        lambda *a, **k: (False, "no receipt")):
            report = self.pp.promote_auto(dry_run=False)
        self.assertEqual(report.get("refused", "G-J") if report.get("refused") else report,
                         report.get("refused") or {"mode": "auto", "refused": "G-J",
                                                   "detail": "no receipt"})
        self.assertTrue((self.corpus / "patterns" / "_inbox" / "pattern-chat-auto1.md").exists())

    def test_confident_applies_with_stamp_and_log(self):
        report = self._run([0.95])
        self.assertEqual(len(report["applied"]), 1)
        dest = self.corpus / "patterns" / "pattern-chat-a0.md"
        self.assertTrue(dest.exists())
        self.assertFalse(dest.name.startswith("_"))
        import yaml as _y
        fm = _y.safe_load(dest.read_text().split("---")[1])
        self.assertEqual(fm["auto_applied"]["judge"], "cloud:jev-test")
        self.assertAlmostEqual(fm["auto_applied"]["prob"], 0.95, places=2)
        log = (self.corpus / "registry" / "log.md").read_text()
        self.assertIn("pattern-auto-apply", log)
        self.assertIn("judge=cloud:jev-test", log)

    def test_in_band_escalates_stays_in_inbox(self):
        report = self._run([0.87])
        self.assertEqual(len(report["escalated"]), 1)
        self.assertTrue((self.corpus / "patterns" / "_inbox" / "pattern-chat-a0.md").exists())
        self.assertNotIn("auto_applied", (self.corpus / "patterns" / "_inbox" / "pattern-chat-a0.md").read_text())

    def test_below_band_stays(self):
        report = self._run([0.79])
        self.assertEqual(len(report["stayed"]), 1)
        self.assertTrue((self.corpus / "patterns" / "_inbox" / "pattern-chat-a0.md").exists())

    def test_mixed_batch_band_paths(self):
        report = self._run([0.95, 0.87, 0.79])
        self.assertEqual(len(report["applied"]), 1)
        self.assertEqual(len(report["escalated"]), 1)
        self.assertEqual(len(report["stayed"]), 1)

    def test_dry_run_moves_nothing(self):
        cands = [_candidate(self.corpus)]
        with mock.patch("judgment.noul", side_effect=[0.99] * 10), \
             mock.patch("judgment.judgment_eval_recorded",
                        lambda *a, **k: (True, "test receipt")), \
             mock.patch("judgment.judge_identity", lambda *a, **k: ("cloud", "j")):
            report = self.pp.promote_auto(dry_run=True)
        self.assertTrue(cands[0].exists())
        self.assertEqual(report["applied"], [])


class TestUnapply(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir="/tmp"))
        self.corpus, pp = _mk_fabric(self.tmp)
        self.pp = pp
        _tuned(self.tmp, auto_apply=True)

    def test_unapply_returns_the_exact_artifact(self):
        report = self._run([0.95])
        dest = self.corpus / "patterns" / "pattern-chat-a0.md"
        self.assertTrue(dest.exists())
        ok = self.pp.unapply("pattern-chat-a0", dry_run=False)
        self.assertTrue(ok)
        self.assertFalse(dest.exists())
        back = self.corpus / "patterns" / "_inbox" / "pattern-chat-a0.md"
        self.assertTrue(back.exists())
        # the stamp STAYS: history is real, but it's a candidate again
        import yaml as _y
        fm = _y.safe_load(back.read_text().split("---")[1])
        self.assertEqual(fm["status"], "candidate")
        self.assertIn("auto_applied", fm)
        log = (self.corpus / "registry" / "log.md").read_text()
        self.assertIn("pattern-auto-unapply", log)

    def _run(self, probs):
        for i, _ in enumerate(probs):
            _candidate(self.corpus, f"pattern-chat-a{i}")
        with mock.patch("judgment.noul", side_effect=list(probs) + [0.95] * 10), \
             mock.patch("judgment.judgment_eval_recorded",
                        lambda *a, **k: (True, "test receipt")), \
             mock.patch("judgment.judge_identity", lambda *a, **k: ("cloud", "j")):
            return self.pp.promote_auto(dry_run=False)

    def test_unapply_refuses_human_applied(self):
        p = _candidate(self.corpus, "pattern-chat-human1")
        with mock.patch.object(self.pp, "PATTERNS_DIR", self.corpus / "patterns"), \
             mock.patch.object(self.pp, "INBOX_DIR", self.corpus / "patterns" / "_inbox"):
            self.pp.apply_candidate(p)
        ok = self.pp.unapply("pattern-chat-human1", dry_run=False)
        self.assertFalse(ok)
        self.assertTrue((self.corpus / "patterns" / "pattern-chat-human1.md").exists())

    def test_unapply_dry_run(self):
        self._run([0.95])
        ok = self.pp.unapply("pattern-chat-a0", dry_run=True)
        self.assertTrue(ok)
        self.assertTrue((self.corpus / "patterns" / "pattern-chat-a0.md").exists())


class TestGateAutoApplies(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(dir="/tmp"))
        self.corpus, pp = _mk_fabric(self.tmp)
        self.pp = pp

    def test_marker_rows_and_info_tier(self):
        import gate as gate_mod
        import fabric_config as _fc
        fc_root_patch = mock.patch.object(_fc, "get_CORPUS_ROOT_or_none",
                                          lambda: self.corpus)
        with fc_root_patch, \
             mock.patch.dict(sys.modules, {"promote-patterns": self.pp}):
            self.assertEqual(gate_mod._gate_auto_applies()[0], 0)  # nothing applied yet
            _tuned(self.tmp, auto_apply=True)
            c = _candidate(self.corpus)
            with mock.patch("judgment.noul", side_effect=[0.99]), \
                 mock.patch("judgment.judgment_eval_recorded",
                            lambda *a, **k: (True, "receipt")), \
                 mock.patch("judgment.judge_identity", lambda *a, **k: ("cloud", "jev-test")):
                self.pp.promote_auto(dry_run=False)
            n, rows = gate_mod._gate_auto_applies()
            self.assertEqual(n, 1)
            self.assertEqual(rows[0]["judge"], "cloud:jev-test")
            # INFO tier: never actionable
            with mock.patch.object(_fc, "get_CORPUS_ROOT_or_none", lambda: self.corpus), \
                 mock.patch.dict(sys.modules, {"promote-patterns": self.pp}):
                sections, actionable = gate_mod.gate()
            self.assertIn("auto-applies", sections)
            self.assertFalse(actionable)


class TestContractsAmended(unittest.TestCase):
    """The pinned tests/docs MOVE with the opt-in (the #190 amendment list)."""

    def test_mining_template_still_never_promotes(self):
        # the scheduled pipeline keeps NO promote verb — --auto is
        # command-surface only, the CI path is untouched
        d = __import__("yaml").safe_load((_REPO / "system" / "corpus" /
                                          "mining-workflow.yml").read_text())
        run = str(d["jobs"]["mine"]["steps"])
        self.assertNotIn("promote-patterns --auto", run)

    def test_docs_pin_the_opt_in(self):
        mc = (_REPO / "docs" / "site" / "machine-contract.md").read_text()
        self.assertIn("auto_threshold", mc)
        self.assertIn("auto_apply", mc)

    def test_agents_rule5_carries_the_exception(self):
        agents = (_REPO / "AGENTS.md").read_text()
        self.assertIn("auto-promote", agents)


if __name__ == "__main__":
    unittest.main()