---
type: index
title: "Behavior Evals"
description: "Golden corpus, behavior fixtures, stability, PR replay, real-repo evals"
created: 2026-09-19
updated: 2026-09-19
---

# Behavior Evals: Does the Fabric Change Agent Behavior?

The compiler evals (`eval.py`, golden corpus) measure extraction quality.
**Behavior evals** measure the thing that actually matters: when an agent
receives the context manifest, does it make a better decision?

```bash
python3 scripts/eval-behavior.py          # zero-LLM: manifest-level compliance (CI)
python3 scripts/eval-behavior.py --llm    # probe a real model + score its answer
python3 scripts/eval-behavior.py --record # append metrics to registry/log.md
```

Fixtures in `evaluations/behavior/` encode scenarios with two layers:

1. **Zero-LLM layer (deterministic):** does the compiled manifest deliver the
   required knowledge? — banned anti-pattern present in the prompt, binding
   decision present, stale pattern excluded with a reason, gap acknowledged
   (nothing selected where no knowledge exists).
2. **LLM layer (`--llm`):** the same fixture's probe question is sent to a real
   model *with* the manifest; the answer must contain the compliant behavior
   (`must_contain`) and must not contain the banned approach
   (`must_not_contain`).

Current fixtures:

| Fixture | Behavior tested |
|---------|-----------------|
| `be1-avoid-anti-pattern` | agent is told NOT to build the banned shared token cache; implements rotation + per-session |
| `be2-project-over-global` | project constraint (rotating tokens) beats the general preference (session store) |
| `be3-stale-demoted` | stale pattern excluded from the manifest, fresh pattern delivered |
| `be4-escalate-gap` | no billing knowledge exists → agent escalates rather than inventing policy |

```text
Knowledge Utility: 100% (4/4)
```

**Knowledge Utility** = fixtures whose required knowledge was delivered ÷ total.
Regression guard: CI fails if any fixture stops passing — the same discipline
as the compiler evals, applied to behavior. This is the differentiator: repos
that only promise "compounding memory" can't measure whether the memory
changed anything.

### Real-repo evaluation

For a heavyweight end-to-end check, run the whole pipeline against a real,
popular repo (default: FastAPI — large, active, well-documented Python):

```bash
python3 scripts/eval-real-repo.py                      # clone + full pipeline + LLM ingest
python3 scripts/eval-real-repo.py --skip-llm           # corpus + context metrics, no LLM
python3 scripts/eval-real-repo.py --repo /path/to/clone
python3 scripts/eval-real-repo.py --json
```

It seeds a throwaway fabric with both integrations enabled, captures a scoped
slice of the repo's docs, ingests with LLM claim extraction (or seeds
doc-backed patterns in `--skip-llm` mode), compiles probe-task manifests, and
measures each tier:

| Tier | Metric |
|------|--------|
| Corpus | sources captured, claims extracted, locator rate, lint errors |
| Context | manifest hit-rate per probe task (selected > 0 with reasons) |
| Graphify | AST symbols indexed from the real repo (e.g. 4,992 for FastAPI), entity pages written |
| Embeddings | re-rank delta when `sentence-transformers` is installed; reported as config-only when absent |

The graphify/embeddings tiers are measured *as integrations*: their
contribution is reported separately, so you can see exactly what enabling them
buys.

### PR replay evaluation

Replay **real PRs** from an active repo and measure whether the fabric would
have helped when the PR was written — a knowledge-recall eval on real-world
vocabulary:

```bash
python3 scripts/eval-pr-replay.py --repo tiangolo/fastapi --prs 16192 --llm
python3 scripts/eval-pr-replay.py --repo tiangolo/fastapi --auto 3            # pick recent merged PRs (deps-bumps skipped)
python3 scripts/eval-pr-replay.py ... --json
```

Per replayed PR (fetched live via `gh` — title, body, review comments, touched files):

- **Graphify tier:** the repo's code is AST-indexed; the report shows entity
  pages written and how many of the PR's touched files have code-symbol
  coverage (e.g. 4,992 symbols / 913 pages from FastAPI; 1/2 touched files covered).
- **Zero-LLM tier:** manifest hit-rate over docs-only corpus (honest baseline).
- **`--llm` tier:** the PR's own discussion is ingested with LLM claim
  extraction; the manifest re-compiles and the report shows
  `after LLM ingest (12 claims): coverage 0.414 (Δ +0.414)` — how much the
  PR's own knowledge improves later recall of its task.

**Term coverage** = share of the PR's own vocabulary (title + body + comments,
stemmed) present in the selected artifacts — a recall proxy on real work. The
coverage delta isolates the value of the ingest step itself.

### Stability & sensitivity evaluation

Closes the rubric's reproducibility rows with hard gates:

```bash
python3 scripts/eval-stability.py --skip-llm          # deterministic gates (CI)
python3 scripts/eval-stability.py --models qwen2.5-coder:7b,qwen3.8:27b-mlx
python3 scripts/eval-stability.py --record            # append metrics to registry/log.md
```

| Gate | What it proves | Threshold |
|------|----------------|-----------|
| G1 context determinism | 20 manifest runs byte-identical | exact (0-token code must not vary) |
| G2 rebuild determinism | `rebuild-index` output identical across runs | exact |
| G3 ingest stability | same model, same source, 2 runs | fuzzy word-coverage ≥ 0.7 (exact Jaccard reported; paraphrase ≠ instability) |
| G6 locator presence | every claim carries an L-locator | 1.0 |
| G4 model sensitivity | two models on the same source | fuzzy ≥ 0.5 (target 0.8); a fail means model swap requires re-running compiler evals |

**Live findings** (recorded in `registry/log.md`): context/rebuild are exactly
deterministic (~40ms); same-model extraction is semantically stable (fuzzy 0.76–0.86)
but drifts in wording (exact 0.31–0.73). A **5-model matrix** — local
(qwen2.5-coder:7b, qwen3.8:27b-mlx) vs Ollama cloud (deepseek-v4.1-flash:cloud,
kimi-k2.7-code:cloud, glm-5.3-flash:cloud) — first showed capability-correlated
disagreement (fuzzy 0.28–0.59). Fixing it took a contract change, not a model change:
the CLAIM_PROMPT now carries an explicit **granularity spec** (exactly one verifiable
fact per claim, target 5–12). After that: **all 10 pairwise G4 checks PASS
(fuzzy 0.75–0.85)** and claim counts converge to 11–12 across every model. The
compiler change was re-baselined against the golden corpus first (recall 0.89, locator
1.00 — PASS). Infra note: cloud reasoning models can silently return 0 claims when
reasoning consumes the token budget — the extractor now budgets 16K tokens and retries
on `finish_reason=length`.

### Model policy: ops vs compiler models

Claim extraction is *compiler work* — it compiles sources into the fabric's
canonical evidence — so it runs on a policy-designated **compiler model**, not
whatever model is configured for cheap queries:

| Setting | Default | Used for |
|---------|---------|----------|
| `llm.model` | `qwen2.5-coder:7b` | ops: capture, status, cheap query synthesis |
| `llm.compiler_model` | `deepseek-v4.1-flash:cloud` | claim extraction (`ingest --extract-claims`), synthesis, promotion mining |
| `llm.local_model` | platform-split: `mlx-community/gemma-4-e4b-it-4bit` (Apple Silicon) / `unsloth/gemma-4-e4b-it-GGUF` (other) | resolves `repos.<slug>.<stage>: local` routes — extraction, synthesis, dossier generation on-device |

```bash
# Override per-run (e.g. test a different compiler model):
WIKI_LLM_COMPILER_MODEL=kimi-k2.7-code:cloud wf ingest evidence/raw/<doc>.md --extract-claims
# Check the local model is cached; offers a human-gated download when missing:
wf models ensure [--yes]      # --check exits 0/1 without prompting (for scripts)
```

**Local routes:** `repos.<slug>.extract/synthesize/dossier: "local"` runs that
stage on-device (privacy tiering). The backend is picked from the model id —
GGUF (llama-cpp-python, universal — works on macOS/Linux/Windows) or MLX
(mlx-lm, Apple Silicon only). Chat-tuned GGUF models (gemma etc.) run through
their chat template automatically. Missing models are offered for download at
first use (only the preferred quantization split is fetched, ~4 GB), or
pre-fetch with `wf models ensure`. Install the backends with
`pip install -e ".[local]"`. GGUF is the recommended testing default: one
model format runs identically on every platform.

**The gate:** `promote.py` and `mine-promotions.py` **refuse to run** unless
`registry/log.md` contains a recorded compiler eval for the current compiler
model. This enforces the G4 lesson — model swaps are compiler changes, and
compiler changes require re-evaluation — as a hard gate instead of a docs
sentence. `wf status` shows all three models (ops, compiler, local).

---
