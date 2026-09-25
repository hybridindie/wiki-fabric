---
type: attested-computation
id: ac-golden-corpus-eval
title: "Attested Computation: golden corpus claim-recall eval"
description: "Sanctioned computation for compiler-model claim extraction recall — the promote/mine gate receipt source."
generated: { by: "process:story-okf-04", at: "2026-09-18T00:00:00Z" }
runtime: python
parameters:
  - { name: model, type: string, required: true }
  - { name: record, type: boolean, required: false }
executor:
  resource: "references/skills/run-golden-eval.md"
  receipt: [model, recall, locator_rate, quote_rate, verdict]
attester:
  resource: "references/attesters/check-golden-eval.py"
verified:
  - by: "human:owner"
    at: "2026-09-18T00:00:00Z"
    reason: "compiler-eval policy definition review"
stale_after: 2027-01-01T00:00:00Z
tags: [eval, compiler, gate]
created: 2026-09-18
updated: 2026-09-18
---

# Computation

    python3 scripts/eval/eval.py   # uses WIKI_LLM_MODEL=<compiler model>

Recall threshold 0.8, locator rate 1.0, quote rate 1.0 (evaluations/rubric.md).
A model swap is a compiler change: this computation must re-run and PASS before
promote/mine accept the new model (compiler-eval gate).
