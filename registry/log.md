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

## [2026-09-14] eval-stability | FAIL

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.29 | fuzzy word-coverage 0.75 across 2 runs (7/11 claims)
- G6 locator presence: PASS — 11/11 claims carry L-locators
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs kimi-k2.7-code:cloud: exact 0.06 / fuzzy 0.43 (7/11 claims)
- manifest_compile_ms: 39.4
- rebuild_index_ms: 35.4
- ingest_s_per_run: 10.0
- ingest_s_second_model: 36.3

## [2026-09-14] eval-stability | PASS

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.57 | fuzzy word-coverage 0.74 across 2 runs (21/15 claims)
- G6 locator presence: PASS — 15/15 claims carry L-locators
- manifest_compile_ms: 39.4
- rebuild_index_ms: 35.4
- ingest_s_per_run: 18.3
- ingest_s_second_model: 40.5

## [2026-09-14] eval-stability | PASS

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.73 | fuzzy word-coverage 0.85 across 2 runs (21/17 claims)
- G6 locator presence: PASS — 17/17 claims carry L-locators
- manifest_compile_ms: 39.8
- rebuild_index_ms: 35.6
- ingest_s_per_run: 17.7
- ingest_s_qwen2.5-coder:7b: 17.7
- ingest_s_qwen3.8:27b-mlx: 45.9
- ingest_s_deepseek-v4.1-flash:cloud: 16.3
- ingest_s_kimi-k2.7-code:cloud: 44.5

## [2026-09-14] eval-stability | FAIL

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.50 | fuzzy word-coverage 0.86 across 2 runs (15/18 claims)
- G6 locator presence: PASS — 18/18 claims carry L-locators
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs qwen3.8:27b-mlx: exact 0.00 / fuzzy 0.30 (15/11 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs deepseek-v4.1-flash:cloud: exact 0.00 / fuzzy 0.00 (15/0 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs kimi-k2.7-code:cloud: exact 0.04 / fuzzy 0.37 (15/13 claims)
- G4 model sensitivity: FAIL — qwen3.8:27b-mlx vs deepseek-v4.1-flash:cloud: exact 0.00 / fuzzy 0.00 (11/0 claims)
- G4 model sensitivity: PASS — qwen3.8:27b-mlx vs kimi-k2.7-code:cloud: exact 0.00 / fuzzy 0.52 (11/13 claims)
- G4 model sensitivity: PASS — deepseek-v4.1-flash:cloud vs kimi-k2.7-code:cloud: exact 0.00 / fuzzy 1.00 (0/13 claims)
- manifest_compile_ms: 40.7
- rebuild_index_ms: 38.2
- ingest_s_per_run: 16.8
- ingest_s_qwen2.5-coder:7b: 16.8
- ingest_s_qwen3.8:27b-mlx: 64.0
- ingest_s_deepseek-v4.1-flash:cloud: 15.4
- ingest_s_kimi-k2.7-code:cloud: 30.6

## [2026-09-14] eval-stability | FAIL

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.31 | fuzzy word-coverage 0.76 across 2 runs (7/10 claims)
- G6 locator presence: PASS — 10/10 claims carry L-locators
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs qwen3.8:27b-mlx: exact 0.00 / fuzzy 0.28 (7/11 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs deepseek-v4.1-flash:cloud: EMPTY claim set (7/0) — extraction failed for one model
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs kimi-k2.7-code:cloud: EMPTY claim set (7/0) — extraction failed for one model
- G4 model sensitivity: FAIL — qwen3.8:27b-mlx vs deepseek-v4.1-flash:cloud: EMPTY claim set (11/0) — extraction failed for one model
- G4 model sensitivity: FAIL — qwen3.8:27b-mlx vs kimi-k2.7-code:cloud: EMPTY claim set (11/0) — extraction failed for one model
- G4 model sensitivity: FAIL — deepseek-v4.1-flash:cloud vs kimi-k2.7-code:cloud: EMPTY claim set (0/0) — extraction failed for one model
- manifest_compile_ms: 39.9
- rebuild_index_ms: 35.7
- ingest_s_per_run: 10.8
- ingest_s_qwen2.5-coder:7b: 10.8
- ingest_s_qwen3.8:27b-mlx: 43.9
- ingest_s_deepseek-v4.1-flash:cloud: 23.3
- ingest_s_kimi-k2.7-code:cloud: 26.9

## [2026-09-14] eval-stability | FAIL

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.73 | fuzzy word-coverage 0.99 across 2 runs (17/21 claims)
- G6 locator presence: PASS — 21/21 claims carry L-locators
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs qwen3.8:27b-mlx: exact 0.04 / fuzzy 0.37 (17/12 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs deepseek-v4.1-flash:cloud: exact 0.07 / fuzzy 0.39 (17/12 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs kimi-k2.7-code:cloud: exact 0.00 / fuzzy 0.23 (17/8 claims)
- G4 model sensitivity: PASS — qwen3.8:27b-mlx vs deepseek-v4.1-flash:cloud: exact 0.09 / fuzzy 0.65 (12/12 claims)
- G4 model sensitivity: FAIL — qwen3.8:27b-mlx vs kimi-k2.7-code:cloud: exact 0.05 / fuzzy 0.46 (12/8 claims)
- G4 model sensitivity: FAIL — deepseek-v4.1-flash:cloud vs kimi-k2.7-code:cloud: exact 0.05 / fuzzy 0.49 (12/8 claims)
- manifest_compile_ms: 39.1
- rebuild_index_ms: 35.4
- ingest_s_per_run: 19.7
- ingest_s_qwen2.5-coder:7b: 19.7
- ingest_s_qwen3.8:27b-mlx: 45.9
- ingest_s_deepseek-v4.1-flash:cloud: 50.3
- ingest_s_kimi-k2.7-code:cloud: 25.7

## [2026-09-14] eval-stability | FAIL

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.56 | fuzzy word-coverage 0.86 across 2 runs (12/13 claims)
- G6 locator presence: PASS — 13/13 claims carry L-locators
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs qwen3.8:27b-mlx: exact 0.00 / fuzzy 0.28 (12/11 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs deepseek-v4.1-flash:cloud: exact 0.05 / fuzzy 0.36 (12/11 claims)
- G4 model sensitivity: FAIL — qwen2.5-coder:7b vs kimi-k2.7-code:cloud: exact 0.00 / fuzzy 0.29 (12/11 claims)
- G4 model sensitivity: PASS — qwen3.8:27b-mlx vs deepseek-v4.1-flash:cloud: exact 0.00 / fuzzy 0.57 (11/11 claims)
- G4 model sensitivity: FAIL — qwen3.8:27b-mlx vs kimi-k2.7-code:cloud: exact 0.00 / fuzzy 0.48 (11/11 claims)
- G4 model sensitivity: PASS — deepseek-v4.1-flash:cloud vs kimi-k2.7-code:cloud: exact 0.10 / fuzzy 0.59 (11/11 claims)
- manifest_compile_ms: 42.6
- rebuild_index_ms: 38.0
- ingest_s_per_run: 12.1
- ingest_s_qwen2.5-coder:7b: 12.1
- ingest_s_qwen3.8:27b-mlx: 35.4
- ingest_s_deepseek-v4.1-flash:cloud: 17.6
- ingest_s_kimi-k2.7-code:cloud: 35.9

## [2026-09-14] eval-stability | 4-model matrix (local + Ollama cloud)

- G3 same-model stability: PASS — fuzzy 0.86 (best yet, after CLAIM_PROMPT granularity spec)
- G4 pairwise (exact/fuzzy):
  - qwen2.5(12) vs qwen3.8-27b(11): 0.00/0.28
  - qwen2.5(12) vs deepseek-v4.1-flash:cloud(11): 0.05/0.36
  - qwen2.5(12) vs kimi-k2.7-code:cloud(12→8): 0.00/0.29
  - qwen3.8-27b(11) vs deepseek(11): 0.00/0.57 PASS
  - qwen3.8-27b(11) vs kimi(8): 0.00/0.48
  - deepseek(11) vs kimi(8): 0.10/0.59 PASS
- Latency: qwen2.5 12s | qwen3.8 35s | deepseek-flash 18s | kimi-k2.7 36s
- Analysis: cross-model disagreement is CAPABILITY-CORRELATED, not pure contract ambiguity:
  the two largest models agree most (0.57-0.59); qwen2.5 (small) over-splits vs everyone.
  Prompt granularity spec improved agreement (fuzzy +0.1-0.2 per pair) but cannot close
  the small-model gap. Operational guidance: use big models for compiler/promotion runs;
  qwen2.5 acceptable for cheap ops with G4 re-run on any model change.
- Infra fix: deepseek:cloud reasoning consumed the 4096-token budget → no JSON. Added
  16384-token default + finish-reason=length retry. Without it cloud reasoning models
  silently extract 0 claims.

## [2026-09-14] eval | formal golden corpus

- Total extracted: 29, golden: 9, covered: 8
- Recall: 0.89, Locator rate: 1.00, Quote rate: 1.00
- Overall: PASS

## [2026-09-14] eval | compiler re-baseline after CLAIM_PROMPT granularity spec

- Claim recall: 0.89 (threshold 0.8) — PASS
- Locator rate: 1.00 — PASS
- Quote rate: 1.00 — PASS
- 29 claims extracted across 3 fixtures, 8/9 golden keys covered
- Model: compiler_model (deepseek-v4.1-flash:cloud) — first verified run since the
  granularity spec landed; the compiler change is now regression-baselined.

## [2026-09-14] eval-stability | PASS

- G1 context determinism: PASS — 1 unique output(s) in 20 runs
- G2 rebuild determinism: PASS — index.md + index.json identical across rebuilds
- G3 ingest claim stability: PASS — exact Jaccard 0.33 | fuzzy word-coverage 0.78 across 2 runs (12/12 claims)
- G6 locator presence: PASS — 12/12 claims carry L-locators
- G4 model sensitivity: PASS — qwen2.5-coder:7b vs qwen3.8:27b-mlx: exact 0.41 / fuzzy 0.78 (12/12 claims)
- G4 model sensitivity: PASS — qwen2.5-coder:7b vs deepseek-v4.1-flash:cloud: exact 0.35 / fuzzy 0.77 (12/11 claims)
- G4 model sensitivity: PASS — qwen2.5-coder:7b vs kimi-k2.7-code:cloud: exact 0.20 / fuzzy 0.78 (12/12 claims)
- G4 model sensitivity: PASS — qwen2.5-coder:7b vs glm-5.3-flash:cloud: exact 0.14 / fuzzy 0.75 (12/12 claims)
- G4 model sensitivity: PASS — qwen3.8:27b-mlx vs deepseek-v4.1-flash:cloud: exact 0.28 / fuzzy 0.75 (12/11 claims)
- G4 model sensitivity: PASS — qwen3.8:27b-mlx vs kimi-k2.7-code:cloud: exact 0.26 / fuzzy 0.78 (12/12 claims)
- G4 model sensitivity: PASS — qwen3.8:27b-mlx vs glm-5.3-flash:cloud: exact 0.20 / fuzzy 0.76 (12/12 claims)
- G4 model sensitivity: PASS — deepseek-v4.1-flash:cloud vs kimi-k2.7-code:cloud: exact 0.21 / fuzzy 0.85 (11/12 claims)
- G4 model sensitivity: PASS — deepseek-v4.1-flash:cloud vs glm-5.3-flash:cloud: exact 0.28 / fuzzy 0.84 (11/12 claims)
- G4 model sensitivity: PASS — kimi-k2.7-code:cloud vs glm-5.3-flash:cloud: exact 0.14 / fuzzy 0.82 (12/12 claims)
- manifest_compile_ms: 39.4
- rebuild_index_ms: 36.0
- ingest_s_per_run: 35.2
- ingest_s_qwen2.5-coder:7b: 35.2
- ingest_s_qwen3.8:27b-mlx: 19.4
- ingest_s_deepseek-v4.1-flash:cloud: 18.7
- ingest_s_kimi-k2.7-code:cloud: 27.5
- ingest_s_glm-5.3-flash:cloud: 17.9

## [2026-09-14] eval-stability | 5-model matrix — G4 full PASS

- Models: qwen2.5-coder:7b, qwen3.8:27b-mlx, deepseek-v4.1-flash:cloud, kimi-k2.7-code:cloud, glm-5.3-flash:cloud
- All 10 pairwise G4 checks PASS: fuzzy 0.75-0.85, exact 0.14-0.41
- G3 same-model: fuzzy 0.78; G6 locator 1.0 (12/12 claims per run)
- Interpretation: with the granularity spec, claim extraction is now model-stable
  across 5 heterogeneous models (local + cloud, reasoning + non-reasoning). The
  earlier capability-correlated gap was a contract-precision problem, closed by the
  granularity spec.
- Latency: glm-5.3-flash 18s, deepseek 19s, qwen3.8 19s, kimi 28s, qwen2.5 35s
- Compiler model policy unchanged (deepseek-v4.1-flash:cloud); glm-5.3-flash verified
  as a peer alternative.
