---
type: skill
name: run-judgment-eval
description: "Run the judge-calibration eval and emit a machine-checkable receipt (G-J)."
tags: [eval, executor, judgment]
---

# Run: judge calibration eval

1. `set -a; source .env.wiki-fabric 2>/dev/null; set +a`
   (cloud route needs the key; local route needs the ollama server up)
2. `python3 scripts/eval/eval-judgment.py --record`
3. Receipt = the `## [date] / **judgment-eval | ...**` registry/log.md block
   + stdout: `{judge, route, separation, mining_spread, verdict: PASS|FAIL}`

The receipt is a runtime artifact — never stored in the bundle (OKF §10).

## What it proves

- Separation: criteria-phrased positives/negatives split by ≥ 0.3 with
  positives ≥ 0.7 / negatives ≤ 0.4
- Mining spread: paraphrase ≥ 0.9 / unrelated ≤ 0.7 (the 0.8 mining
  threshold sits between them — threshold ownership lives in this eval)

A judge swap is a judgment change: re-run and PASS before judgment call
sites accept the new judge (the G-J gate; the compiler's G4 analog).