#!/usr/bin/env python3
"""Deterministic attester: verify the last judgment-eval (G-J) receipt passes
the calibration gates for the CURRENT judge identity.

Usage: python3 references/attesters/check-judgment-eval.py [--judge kind[:model]]
Exit 0 = ATTESTED. Exit 1 = REFUSED (stale/failed/missing/model mismatch).
"""
import sys
import os
import re
import json
from pathlib import Path


def _log_path():
    """The receipt: $WIKI_FABRIC_DIR wins; else this file's repo tree.
    registry/ may be nested (corpus/registry — the #152 layout) or at the
    root. Deliberately dependency-free — an attester does not import the
    code it attests."""
    env = os.environ.get("WIKI_FABRIC_DIR")
    roots = ([Path(env)] if env else []) + [Path(__file__).resolve().parent.parent.parent]
    fallback = None
    for c in roots:
        for lp in (c / "registry" / "log.md", c / "corpus" / "registry" / "log.md"):
            fallback = fallback or lp
            if lp.exists():
                return lp
    return fallback


LOG = _log_path()

# mirrors eval-judgment.py / ac-judgment-eval.md (pinned values, not imports —
# an attester must not depend on the thing it attests)
POS_FLOOR, NEG_CEIL, MIN_SPREAD = 0.7, 0.4, 0.3
MINING_SAME_FLOOR, MINING_DIFF_CEIL, THRESHOLD = 0.9, 0.7, 0.8


def main():
    args = sys.argv[1:]
    judge = args[args.index("--judge") + 1] if "--judge" in args else None
    if not LOG.exists():
        print(json.dumps({"verdict": "REFUSED", "reason": "no registry/log.md"}))
        return 1
    text = LOG.read_text(errors="replace")
    blocks = re.findall(
        r"## (\d{4}-\d{2}-\d{2})[^\n]*\n\* \*\*judgment-eval \| (\w+)\*\*(.*?)(?=\n## |\Z)",
        text, re.DOTALL)
    for date, verdict, body in reversed(blocks):
        jm = re.search(r"judge: (\S+)(?: (\S+))?", body)
        if not jm:
            continue
        kind = jm.group(1)
        model = (jm.group(2) or "").split()[0] if jm.group(2) else ""
        # model token is "<model> route: <route>" in the receipt line — take
        # the first token; slash-form receipts also parse (kind model/xxx)
        if "/" in model:
            model = model.split("/")[0]
        if judge and judge not in (kind, f"{kind}/{model}", model):
            continue
        if verdict != "PASS":
            print(json.dumps({"verdict": "REFUSED",
                              "reason": f"latest judgment-eval for {kind} is {verdict} ({date})"}))
            return 1
        sep = re.search(r"spread ([\d.]+) \(pos ([\d.]+) / neg ([\d.]+)\)", body)
        mine = re.search(r"same ([\d.]+) / diff ([\d.]+)", body)
        if not (sep and mine):
            print(json.dumps({"verdict": "REFUSED",
                              "reason": "receipt missing metric lines (pre-G-J format)"}))
            return 1
        spread, pos, neg = float(sep.group(1)), float(sep.group(2)), float(sep.group(3))
        same, diff = float(mine.group(1)), float(mine.group(2))
        checks = {
            "pos_floor": pos >= POS_FLOOR,
            "neg_ceil": neg <= NEG_CEIL,
            "separation": spread >= MIN_SPREAD,
            "mining_same": same >= MINING_SAME_FLOOR,
            "mining_diff": diff <= MINING_DIFF_CEIL,
            "threshold_inside": diff < THRESHOLD < same,
        }
        if not all(checks.values()):
            failed = [k for k, ok in checks.items() if not ok]
            print(json.dumps({"verdict": "REFUSED", "date": date, "judge": kind,
                              "model": model, "failed": failed}))
            return 1
        print(json.dumps({"verdict": "ATTESTED", "date": date, "judge": kind,
                          "model": model, "separation_spread": spread,
                          "mining": {"same": same, "diff": diff}}))
        return 0
    print(json.dumps({"verdict": "REFUSED",
                      "reason": f"no judgment-eval receipt for {judge or 'current judge'} — run: python3 scripts/eval/eval-judgment.py --record"}))
    return 1


if __name__ == "__main__":
    sys.exit(main())