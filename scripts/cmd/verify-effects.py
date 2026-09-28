#!/usr/bin/env python3
# verify-effects.py — judged effect verification at ingest (#29 wiring A).
#
# The ingest agent drafts each claim's effect classification (step 4 of the
# ingest skill). This command runs the JUDGMENT TIER as the independent
# second opinion: for each new claim, judge it against its related existing
# claims (same-source first, then same-project) via the decision model's
# `choice` head. Verdicts are written to <claim>.effects.json next to the
# claim for the agent to reconcile — the tier verifies, the agent owns the
# final relations edit (human gate via the change-set flow still applies).
#
# Kills the self-preference conflict: the model that extracted the claim no
# longer grades its own homework unaided.
#
# Usage:
#   python3 scripts/cmd/verify-effects.py <claim.md> [claim2.md ...] [--json]
#   python3 scripts/cmd/verify-effects.py --source <project-slug>   # newest claims
#
# Requires the judgment tier (integrations.judgment); degrades with a clear
# message otherwise (keyword-classification remains the agent's judgment).

import sys
import sys as _s, pathlib as _p
_HERE = _p.Path(__file__).resolve().parent
for _dir in (_HERE, _HERE.parent / "lib", _HERE.parent):
    if str(_dir) not in _s.path:
        _s.path.insert(0, str(_dir))

import argparse
import json
import re
from pathlib import Path

from fabric_config import CORPUS_ROOT


def _statement(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r'statement: "?([^\n]+)', text)
    return (m.group(1).strip().strip('"') if m else ""), text


def verify_claim(claim_path, max_pairs=12, min_confidence=0.6):
    """Judge one new claim against its related pool. Returns a report dict."""
    from judgment import (effect_verdict, related_claim_pool,
                          judgment_route, JudgmentUnavailable)
    route = judgment_route()
    statement, _ = _statement(claim_path)
    pool = related_claim_pool(claim_path, max_n=max_pairs)
    pairs = []
    for existing in pool:
        est, _ = _statement(existing)
        if not est:
            continue
        try:
            v = effect_verdict(statement, est)
        except Exception as e:
            pairs.append({"against": existing.stem, "error": str(e)[:120],
                          "verdict": None})
            continue
        pairs.append({
            "against": existing.stem,
            "effect": v.get("effect"),
            "confidence": v.get("confidence"),
        })
    report = {
        "claim": claim_path.stem,
        "route": route,
        "pairs": pairs,
        "judged_effects": {
            p["against"]: p["effect"] for p in pairs if p.get("verdict") or p.get("effect")
        },
    }
    return report


def write_report(claim_path, report):
    """Verdicts live beside the claim (audit artifact, consumed by the agent
    during effect classification)."""
    out = claim_path.with_suffix(".effects.json")
    out.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n",
                   encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Judged effect verification for ingested claims (independent second opinion)")
    parser.add_argument("claims", nargs="*", help="New claim .md files")
    parser.add_argument("--source", help="Verify the newest N claims of a project slug")
    parser.add_argument("--newest", type=int, default=12, help="With --source: how many")
    parser.add_argument("--max-pairs", type=int, default=12,
                        help="Max existing claims to judge per new claim")
    parser.add_argument("--json", dest="report_json", action="store_true")
    args = parser.parse_args()

    from judgment import is_judgment_active
    if not is_judgment_active():
        print("Judgment tier disabled (integrations.judgment.enabled) — nothing to verify.",
              file=sys.stderr)
        return 2

    paths = [Path(c) for c in args.claims]
    if args.source:
        claims_dir = CORPUS_ROOT / "evidence" / "claims"
        paths = sorted(claims_dir.glob(f"claim-{args.source}-*.md"),
                       key=lambda p: p.stat().st_mtime, reverse=True)[:args.newest]

    if not paths:
        print("No claims to verify.", file=sys.stderr)
        return 1

    reports = []
    for p in paths:
        if not p.exists():
            print(f"missing: {p}", file=sys.stderr)
            continue
        rep = verify_claim(p, max_pairs=args.max_pairs)
        out = write_report(p, rep)
        verdicts = {}
        for pr in rep["pairs"]:
            eff = pr.get("effect")
            if eff and eff != "no-action":
                verdicts.setdefault(eff, []).append(pr["against"].replace("claim-", "")[:40])
        reports.append(rep)
        errs = [p for p in rep["pairs"] if p.get("error")]
        line = f"{p.stem}: {len(rep['pairs'])} pair(s) judged"
        if verdicts:
            parts = [f"{k}: {', '.join(v)}" for k, v in verdicts.items()]
            line += " → " + "; ".join(parts)
        else:
            line += " → no non-trivial effects"
        if errs:
            line += f" ({len(errs)} pair(s) errored — check .effects.json)"
        print(line)

    if args.report_json:
        print(json.dumps(reports, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())