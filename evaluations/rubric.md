---
type: registry
title: Evaluation Rubric
updated: 2026-09-11
---

# Evaluation Rubric

The golden corpus in `fixtures/`/`expected/` lets us measure how faithfully the
wiki-maintainer agent compiles source into wiki — not how fluent its prose is.

## Metrics (from the source document)

| Metric | What it measures | How |
|---|---|---|
| **Claim extraction precision/recall** | Did we extract the right claims, no more no less? | Diff `expected/claims.yaml` vs ingested `claims/`. Precision = correct/extracted; recall = correct/expected. |
| **Citation / locator correctness** | Does every claim trace to a real source location? | `lint.py` — `source_ref without locator` warnings + manual spot-check of quotes against `raw/`. |
| **Entity / concept dedup** | Are the same entities kept under one name? | `lint.py` DUP-ID + manual: no two `concept-*` with the same `statement`. |
| **Contradiction detection & classification** | Did we surface conflicts and not merge them? | `expected/contradictions.yaml` vs ingested claims' `relations`. A merged contradiction = fail. |
| **Change isolation** | Did the ingest touch only relevant canonical pages? | Diff the change-set's `diff.md` vs pages actually edited. |
| **Query answer support rate** | Fraction of answer sentences backed by a cited claim? | `questions.yaml` — count supported sentences / total. |
| **Stability across reruns** | Same source → same claims, run twice? | Re-run ingest; compare claim `id` + `statement` sets. |
| **Stability across models** | Same claims on sonnet vs opus? | Compare two runs; flag model-dependent claims. |
| **Cost / latency / tokens per ingest** | Operational cost | Record from the runner's transcript; append to `registry/log.md`. |

## Run protocol

1. In a sandbox copy of the vault, run `ingest evaluations/fixtures/source-N.md`.
2. Apply `scripts/lint.py` — must be ERRORS=0.
3. For `source-c`, confirm exactly one `contested` claim with a `contradicts` relation.
4. For `questions.yaml`, run each question; check `must_cite` + `format` + that
   the conflict surfaces (q2) instead of collapsing.
5. Score precision/recall against `expected/claims.yaml`. Record in `registry/log.md`.
6. **Gate:** a wiki-maintainer model change must not drop below the
   prior run on any metric (regression guard).

## Pass thresholds (initial)

- Claim extraction recall ≥ 0.8, precision ≥ 0.9.
- Citation locator presence = 1.0.
- Contradiction merge rate = 0 (any merged contradiction = fail).
- Query answer support rate ≥ 0.9.

## What this is for

A deterministic linter (`scripts/lint.py`) is layer 1. **This** is layer 2 —
measuring the *compiler*, not just the artifacts. When the linter reports clean
but an expected claim is missing, the agent's extraction is wrong even though the
output is structurally valid.
