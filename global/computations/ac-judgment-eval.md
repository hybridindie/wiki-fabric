---
type: attested-computation
id: ac-judgment-eval
title: "Attested Computation: judge calibration eval"
description: "Sanctioned computation for decision-model calibration — the judgment-gate receipt source. Only a calibrated judge may sit in the proposing seat."
generated: { by: "agent/johnd/glm-5.3-flash:cloud", at: "2026-10-03T00:00:00Z" }
runtime: python
parameters:
  - { name: judge, type: string, required: true }
  - { name: route, type: string, required: true }
  - { name: record, type: boolean, required: false }
executor:
  resource: "references/skills/run-judgment-eval.md"
  receipt: [judge, route, separation, mining_spread, verdict]
attester:
  resource: "references/attesters/check-judgment-eval.py"
verified:
  - by: "human:owner"
    at: "2026-10-03T00:00:00Z"
    reason: "judgment-gate policy definition review (G-J)"
stale_after: 2027-01-01T00:00:00Z
tags: [eval, judgment, gate, calibration]
created: 2026-10-03
updated: 2026-10-03
---

# Computation

    python3 scripts/eval/eval-judgment.py --record

Calibrates the CURRENT judge (route + model identity from
`integrations.judgment`) against the separation fixtures:

- **Separation**, the core property: known-positive and known-negative
  fixtures (criteria-phrased) must separate by a margin — positives ≥ pos
  floor (0.7), negatives ≤ neg ceiling (0.4), spread ≥ 0.3. A judge that
  cannot separate truth from noise may not propose anything.
- **Mining spread**: paraphrase pairs ≥ 0.9, unrelated pairs ≤ 0.7 — the
  0.8 mining threshold sits BETWEEN them (the threshold is owned by this
  eval, not by tuning prefs).

A judge swap (route, backend, or model id — including the ollama tag via
`systemone.judge_tag()`) is a judgment change: this computation must re-run
and PASS before any judgment call site accepts the new judge. That is the G-J
gate — the judgment analog of the G4 compiler-eval gate.