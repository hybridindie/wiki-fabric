---
type: attested-computation
id: ac-locator-verification
title: "Attested Computation: claim locator verification"
description: "Deterministic post-extraction pass verifying every claim quote exists at its cited lines — the trust tier source for claims."
runtime: python
parameters:
  - { name: source_text, type: string, required: true }
executor:
  resource: "references/skills/run-ingest.md"
  receipt: [claims_extracted, locators_verified, fixed_locators]
attester:
  resource: "references/attesters/check-claims-verified.py"
generated: { by: "process:story-okf-04", at: "2026-09-18T00:00:00Z" }
verified:
  - by: "human:owner"
    at: "2026-09-18T00:00:00Z"
    reason: "claims trust-tier definition review"
tags: [ingest, trust]
created: 2026-09-18
updated: 2026-09-18
---

# Computation

`verify_and_fix_locators()` inside `scripts/cmd/ingest.py` — re-finds each quote in
the source text and rewrites the locator when the model drifted. Claims carrying
a verified block with `process:locator-verification` are machine-confirmed
trusting this computation.
