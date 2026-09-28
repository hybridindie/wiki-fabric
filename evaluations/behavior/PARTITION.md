---
type: eval-fixture
id: behavior-gate-partition
title: "Behavior fixture partition (living-wiki S2 / SkillOpt S2)"
description: "Seed-fixed split of behavior fixtures into a working set (development) and a held-out gate set (promote-only) — candidates cannot fit the gate they are gated on."
created: 2026-09-28
---

# Behavior fixture partition

The gate contract (#139 / SkillOpt-epic S2): `promote.py` runs the **held-out
gate set** against the candidate's merge; the candidate must not lower
Knowledge Utility on that set. Fixtures below are partitioned with a fixed
seed (`partition_seed: 42`); the gate set is touched ONLY by promote — new
fixture development happens in the working set, so a candidate (and the
author writing it) cannot fit the gate it is gated on.

| Set | Fixtures | Use |
|---|---|---|
| **held-out gate** | `be2`, `be4`, `be5` | promote.py pre-merge gate only |
| **working set** | `be1`, `be3`, `be6` | fixture development, CI (eval-behavior default run) |

Rules:
- Moving a fixture between sets is a contract change: edit this file + justify
  in the change-set (the seed makes it auditable, not casual).
- `eval-behavior.py --gate` runs ONLY the held-out set (used by promote.py).
- Utility baseline: the gate compares the merge-candidate corpus against the
  pre-merge corpus on the held-out set; **strictly-positive** for `standard`
  promotion, ties accepted-but-flagged for `recommended`, per the gate matrix
  (skills: strictly-better, ties rejected; anti-patterns: no utility gate —
  counterexamples + human review only; concepts/domains: lint + human only).