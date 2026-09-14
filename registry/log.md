---
type: log
title: Log
created: 2026-09-13
updated: 2026-09-13
---

# Log

Append-only timeline. One `## [YYYY-MM-DD] <op> | <subject>` entry per operation
(`ingest`, `refresh`, `promote`, `schema-change`).
## [2026-09-13] ingest | test-g-sample-md

- Ingested sample.md (sha256 9e389fa6f9c1...)
- Extracted 0 claims
- Change-set: evidence/traces/change-sets/2026-09-13-test-g-sample-md

## [2026-09-13] eval-behavior | utility 100% (4/4)

- be1-avoid-anti-pattern: PASS
- be2-project-over-global: PASS
- be3-stale-demoted: PASS
- be4-escalate-gap: PASS

## [2026-09-14] eval-stability | PASS

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- manifest_compile_ms: 41.7
- rebuild_index_ms: 40.9

## [2026-09-14] eval-stability | full run — G4 model-sensitivity finding

- G1 context determinism: PASS — 1 unique output in 20 runs (~40ms)
- G2 rebuild determinism: PASS — index.md + index.json identical
- G3 ingest claim stability (qwen2.5-coder:7b, 2 runs): PASS on fuzzy 0.76 (exact 0.56) — wording drifts, semantics stable
- G6 locator presence: PASS — 100% (13/13)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs qwen3.8:27b-mlx exact 0.00 / fuzzy 0.28
- Finding: the two models extract genuinely different claim sets from the same fixture
  (count 15 vs 12, different facts chosen). Per rubric, compiler changes must not drop
  below prior metrics: model swaps require re-running compiler evals before adopting.
- Timings: manifest ~40ms, rebuild ~40ms, ingest qwen2.5 ~18s, qwen3.8-27b ~60-90s (cold)

## [2026-09-14] eval-stability | PASS

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- manifest_compile_ms: 84.9
- rebuild_index_ms: 84.3
