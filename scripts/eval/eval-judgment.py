#!/usr/bin/env python3
"""eval-judgment.py — judge calibration eval (the G-J gate).

The judgment analog of the G4 compiler-eval gate (eval-stability G4):
a decision-model swap is a JUDGMENT change — the new judge must re-run this
calibration and PASS before judgment call sites accept it.

What it measures (fixtures are the eval's own — criteria-phrased per the
live-calibration finding: abstract phrasing collapses separation):

1. SEPARATION — positives (verifiably true for their state) vs negatives
   (verifiably absent) must split: pos >= 0.7, neg <= 0.4, spread >= 0.3.
2. MINING SPREAD — paraphrase pairs >= 0.9, unrelated pairs <= 0.7; the 0.8
   MINING_THRESHOLD sits strictly between. Thresholds are owned by this eval,
   not by tuning prefs (tuning may only override WITH a re-calibration).

Exit 0 = PASS (receipt recorded with --record). Exit 1 = FAIL or unavailable.
"""
import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
for _d in (_HERE.parent / "cmd", _HERE.parent / "lib"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

# GATES — pos floor / neg ceiling / min spread / mining pair bounds
POS_FLOOR = 0.7
NEG_CEIL = 0.4
MIN_SPREAD = 0.3
MINING_SAME_FLOOR = 0.9
MINING_DIFF_CEIL = 0.7
MINING_THRESHOLD = 0.8  # judgment.MINING_THRESHOLD_DEFAULT must sit inside

WIRE_TIMEOUT = int(os.environ.get("WIKI_JUDGE_EVAL_TIMEOUT", "120"))


def _fixtures():
    """Calibration fixtures — (kind, state, expected). KEPT SHALLOW + fast:
    4 noul probes + 4 mining pairs ~= 8 judge calls (~10s cloud; ~1min local).
    """
    return [
        # --- separation: noul ---
        {"kind": "noul",
         "question": "Does the state contain a binding decision about token rotation?",
         "state": "TASK: rotate the OAuth signing keys\n\nDECISION: tokens rotate at 30 days (decision-token-rotation)",
         "true_desc": "a binding decision or required pattern constraining the task is present",
         "false_desc": "no binding decision, ban, or required pattern is present",
         "expect": 1},
        {"kind": "noul",
         "question": "Does the state contain a binding decision about token rotation?",
         "state": "TASK: add a login form\n\nNOTE: the login page lists three third-party providers",
         "true_desc": "a binding decision, anti-pattern ban, or required pattern the agent must follow is present",
         "false_desc": "no binding decision, ban, or required pattern is present",
         "expect": 0},
        {"kind": "noul",
         "question": "Does this error report describe a missing-file failure?",
         "state": "ERROR: FileNotFoundError: no such file or directory: 'config.yaml'",
         "true_desc": "the state clearly exhibits the described failure",
         "false_desc": "the state does not exhibit the described failure",
         "expect": 1},
        {"kind": "noul",
         "question": "Does this error report describe a missing-file failure?",
         "state": "ERROR: connection refused by peer at 127.0.0.1:8080",
         "true_desc": "the state clearly exhibits the described failure",
         "false_desc": "the state does not exhibit the described failure",
         "expect": 0},
        # --- mining spread: same_recurrence pairs ---
        {"kind": "same", "expect": 1,
         "a": "Workflow JSON fixtures drifted from the sanitizer's expectations; templates shipped but failed validation on import.",
         "b": "The shipped workflow templates fail the sanitizer: fixture JSON diverged from what validation expects on import."},
        {"kind": "same", "expect": 1,
         "a": "Graph enrichment hit zero claims for docs-only repos because the docs never reference code files.",
         "b": "Docs-only captures get no graph-enrichment claims: the upstream docs contain no code-file references."},
        {"kind": "same", "expect": 0,
         "a": "Graph enrichment hit zero claims for docs-only repos because the docs never reference code files.",
         "b": "Model extraction runs must stay on-device for the privacy-sensitive repo."},
        {"kind": "same", "expect": 0,
         "a": "Corpus CI freshness drift was found on the dormant machine's sources after the scheduled re-verify.",
         "b": "The wiki export reconciler removed stale generated pages before regenerating topics."},
    ]


def _run():
    from judgment import noul, same_recurrence, judgment_route, JudgmentUnavailable
    import judgment as _J

    route = judgment_route()
    fx = _fixtures()

    pos, neg = [], []
    for f in [f for f in fx if f["kind"] == "noul"]:
        p = noul(f["question"], f["state"], false_desc=f["false_desc"],
                 true_desc=f["true_desc"])
        (pos if f["expect"] else neg).append(p)
        print(f"  noul expect={f['expect']} -> {p:.3f}")

    same, diff = [], []
    for f in [f for f in fx if f["kind"] == "same"]:
        s, p = same_recurrence(f["a"], f["b"],
                               threshold=_J.MINING_THRESHOLD_DEFAULT)
        (same if f["expect"] else diff).append(p)
        print(f"  pair expect={'same' if f['expect'] else 'diff'} -> {s} (p={p:.3f})")

    sep_pos = min(pos)
    sep_neg = max(neg)
    spread = sep_pos - sep_neg
    mine_hi = min(same)
    mine_lo = max(diff)

    checks = [
        ("positives >= floor", sep_pos >= POS_FLOOR, f"{sep_pos:.3f} >= {POS_FLOOR}"),
        ("negatives <= ceiling", sep_neg <= NEG_CEIL, f"{sep_neg:.3f} <= {NEG_CEIL}"),
        ("separation spread", spread >= MIN_SPREAD, f"{spread:.3f} >= {MIN_SPREAD}"),
        ("paraphrase pairs >= floor", mine_hi >= MINING_SAME_FLOOR,
         f"{mine_hi:.3f} >= {MINING_SAME_FLOOR}"),
        ("unrelated pairs <= ceiling", mine_lo <= MINING_DIFF_CEIL,
         f"{mine_lo:.3f} <= {MINING_DIFF_CEIL}"),
        ("threshold sits inside spread",
         mine_lo < MINING_THRESHOLD < mine_hi,
         f"{mine_lo:.3f} < 0.8 < {mine_hi:.3f}"),
    ]
    # the shipped threshold constant must agree with the eval's
    checks.append(("MINING_THRESHOLD_DEFAULT consistent",
                   _J.MINING_THRESHOLD_DEFAULT == MINING_THRESHOLD,
                   f"{_J.MINING_THRESHOLD_DEFAULT} == {MINING_THRESHOLD}"))

    passed = all(ok for _, ok, _ in checks)
    judge, model = _judge_identity()
    out = {
        "judge": judge, "model": model, "route": route,
        "separation": {"pos": round(sep_pos, 3), "neg": round(sep_neg, 3),
                       "spread": round(spread, 3)},
        "mining_spread": {"same": round(mine_hi, 3), "diff": round(mine_lo, 3)},
        "checks": [{"check": n, "ok": ok, "detail": d} for n, ok, d in checks],
        "verdict": "PASS" if passed else "FAIL",
    }
    print(json.dumps(out, indent=2))
    return passed, out


def _judge_identity():
    """(judge, model) for the receipt — route-specific model identity.
    Single truth: judgment.judge_identity()."""
    from judgment import judge_identity, judgment_route
    route = judgment_route()
    kind, model = judge_identity()
    return kind, model


def _record(out):
    """Append the §9 receipt to registry/log.md (runtime artifact; the gate
    + attester read it back)."""
    import layout
    from wf_common import now_iso_utc
    from datetime import date
    log = layout.registry() / "log.md"
    log.parent.mkdir(parents=True, exist_ok=True)
    if not log.exists():
        log.write_text("---\ntype: log\ntitle: Log\ncreated: "
                       f"{date.today().isoformat()}\n---\n\n# Log\n\nAppend-only timeline.\n")
    with open(log, "a") as f:
        f.write(f"\n## {date.today().isoformat()}\n")
        f.write(f"* **judgment-eval | {out['verdict']}**\n")
        f.write(f"- judge: {out['judge']} {out.get('model', '')} "
                f"route: {out['route']}\n")
        f.write(f"- separation: spread {out['separation']['spread']} "
                f"(pos {out['separation']['pos']} / neg {out['separation']['neg']})\n")
        f.write(f"- mining_spread: same {out['mining_spread']['same']} / "
                f"diff {out['mining_spread']['diff']}\n")
        f.write(f"- recorded: {now_iso_utc()}\n")


def main():
    parser = argparse.ArgumentParser(description="Judge calibration eval (G-J gate)")
    parser.add_argument("--record", action="store_true", help="Append the receipt to registry/log.md")
    parser.add_argument("--timeout", type=int, default=WIRE_TIMEOUT)
    args = parser.parse_args()
    os.environ.setdefault("WIKI_JUDGE_EVAL_TIMEOUT", str(args.timeout))
    os.environ["WIKI_JUDGE_GATE"] = "0"  # the calibration run IS the gate's input — no recursion
    try:
        passed, out = _run()
    except Exception as e:
        from judgment import JudgmentUnavailable
        print(json.dumps({"verdict": "UNAVAILABLE", "reason": str(e)}, indent=2))
        return 1
    if args.record and passed:
        _record(out)
        print(f"receipt: registry/log.md (judgment-eval | {out['verdict']})")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())