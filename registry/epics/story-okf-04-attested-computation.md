---
type: registry
title: Story — Attested Computation type (evals + promotion as sanctioned computations)
id: story-okf-04-attested-computation
status: proposed
epic: "[[epic-okf-alignment]]"
priority: medium
estimate: L
depends_on: "[[story-okf-03-trust-provenance]]"
github_issue: https://github.com/hybridindie/wiki-fabric/issues/5
created: 2026-09-16
updated: 2026-09-16
---

# Story: Attested Computation — formalize eval/promotion as attestable runs

## As a
consumer deciding whether to trust a claim, promotion, or eval result

## I want
deterministic fabric computations (lint, eval, promote gates, entity index)
declared as `type: Attested Computation` concepts with `runtime`, `parameters`,
`executor`, `attester`

## So that
a consumer can re-run the sanctioned computation and verify the verdict
(e.g. "recall 0.89 PASS") was produced the declared way — not taken on faith
from the agent's text. OKF v0.2 §10 makes this a prescribed type; it maps
directly onto what our eval-stability gates already enforce.

## Acceptance criteria

- [ ] `Attested Computation` added to VALID_TYPES; schemas/frontmatter.md documents the contract fields (`runtime`, `parameters`, `computation`, `executor.receipt`, `attester`)
- [ ] Existing deterministic scripts get AC pages under `global/computations/` (or `computations/`): `eval.py` (golden corpus recall), `lint.py` (profile conformance), `promote.py` maturity gate, `ingest.py` locator-verification pass. Each declares:
  - `runtime: python` (or `bash` for smoke-test)
  - `parameters` (e.g. eval: model, corpus; promote: pattern_ref, maturity)
  - `executor` → run instructions under `references/skills/`
  - `attester` → deterministic check code under `references/attesters/`
- [ ] `references/` directory convention adopted for executor/attester code (OKF §6.3)
- [ ] Compiler-eval gate (model swaps require recorded compiler eval) expressed as an AC check: `promote.py` refuses without a fresh receipt from the eval computation — the refusal is the attestation gate, formalized
- [ ] Hook capture/ingest runs produce receipts (capture: `{files_copied, drift_count}`, ingest: `{claims_extracted, locators_verified}`) logged to `registry/log.md` — runtime artifacts, not in the bundle, per §10
- [ ] `wf okf` (story 5) exports AC pages verbatim — they are already portable
- [ ] At least one end-to-end attestation demonstrated: run `eval.py`, check receipt, run attester, record verdict in the story page

## Notes

- §10.6 distinction maps cleanly onto our existing split: `verified` = definition
  review (slow, in-bundle, human) vs attestation = per-run receipt check (runtime,
  deterministic). Our compiler-model policy already requires exactly this shape.
- Receipt/verdict wire formats are explicitly deferred by the spec (§12); we pick
  a minimal JSON receipt shape and note it as a fabric profile choice.

## Log

- 2026-09-16 — **Creation**: story opened.