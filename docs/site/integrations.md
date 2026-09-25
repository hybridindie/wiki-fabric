---
type: index
title: "Optional Integrations"
description: "Graphify call-graph intelligence, embeddings, and the judgment tier (off by default)"
created: 2026-09-19
updated: 2026-09-25
---

# Optional Integrations

**Graphify** is a companion tool that parses a repo's code into a call-graph
(function → function → import edges) using AST parsing — no LLM. Wiki-fabric
consults that graph to detect stale claims after refactors and to enrich
claims with code provenance.

Integrations add capabilities on top of the core loop. They are declared in `fabric.yaml` (see [Configuration](./configuration)) and are **never load-bearing** — with the integration off, every script behaves exactly as the core docs describe. The design rule: *integrations add capabilities; they are never load-bearing.*

## What each integration does

| Integration | When active | Cost |
|-------------|-------------|------|
| **graphify** | claims carry `code_symbols` + `graph_edges` (doc→code provenance); `graphify-bridge --diff` adds AST staleness detection after refactors; **`wf context` gains a `Code navigation` block** — task tokens → graph symbols → ranked file shortlist (0 tokens, deterministic); code-reachable claims surface first | 0 tokens (AST + community detection) |
| **embeddings** | semantic re-ranking of retrieval results (planned — off by default) | local inference |
| **judgment** | low-variance decision-model judging (System One models: [TypeSafe Jev](https://docs.typesafe.ai/introduction) cloud, [Laya-MLX](https://github.com/rbrus/laya-as-judge) local) for eval gates: `wf eval-behavior --judge` scores fixtures with calibrated probabilities instead of a generative LLM judge | ~$0.0004/call (cloud) or on-device (local) |

## The judgment tier

Between the fabric's deterministic string ops (0 tokens, always) and its
generative LLM calls, the judgment tier is a third option: a decision model
that evaluates typed questions (yes/no probability, rubric score, choice)
against the assembled state and returns **typed answers with calibrated
probabilities** — no text generation. LangChain's benchmark of Jev as a judge
found 100% binary accuracy vs a human oracle with 92–913× lower variance than
GPT-5.6/Claude LLM judges, at ~1/80th Claude's cost.

**Where it may run (today):**
- `wf eval-behavior --judge` — the `--llm` probe of behavior evals becomes a
  `noul` judgment ("does the prompt deliver the binding decision?"), stable
  enough to gate CI.
- `eval-stability.py --judge` — **G4-J**: model pairs the fuzzy gate failed
  (near-miss, not empty) are re-asked "same factual content?"; judged-SAME
  downgrades wording drift to a warning, with the probability recorded.
- `mine-promotions.py --judge` — judged refinement is now **symmetrical**:
  near-miss keyword pairs get a pairwise "same recurring pattern?" verdict
  (merge), **and** an incoherence sweep demotes members judged DIFFERENT from
  their cluster's representative (split) — a keyword cluster that judgment
  says is incoherent can no longer reach a dossier intact.
- Planned: borderline-context re-ranking (each judgment recorded).

**Hard contract:**
- **Never the 0-token core.** `wf context`, `wf query`, `lint` stay pure
  string ops — guarded by a test that fails if they import the judgment module.
- **Low-variance judgment, not determinism.** Every judgment records
  backend + model + probability; near-threshold values surface as
  `NEAR-THRESHOLD` and should escalate to the human gate, not auto-decide.
- **Never authority.** A judge score supports a check; provenance, scope,
  and human gates still decide.

Config (see [Configuration](./configuration#judgment-tier)):

```yaml
integrations:
  judgment:
    enabled: true
    route: local          # cloud (TypeSafe Jev) | local (Laya-MLX on-device)
    local_backend: laya   # laya-as-judge[mlx] (typed heads, real inference)
```


Cloud route reads `TYPESAFE_API_KEY` from the environment (never committed).
Local route dispatches through the on-device judgment stack (see below).


## Setting up the local (Laya) backend

```bash
git clone https://github.com/rbrus/laya-as-judge.git
cd laya-as-judge && uv venv --python 3.12 && uv pip install -e '.[mlx]' --python .venv/bin/python
```

Model weights auto-download on first call (~3.4 MB). Live-calibrated on an
M4 Max: true-paraphrase pairs score p≈0.93–0.96, unrelated pairs p≈0.75,
steady-state latency ~11–19 ms, 0 output tokens. The `judgment.local_backend:
laya` backend **rejects laya's EmulatorBackend** (a keyword heuristic with no
discriminative power — it returns identical probabilities for related and
unrelated content); real inference requires the MLX runtime (Apple Silicon,
Python 3.11+). Keep the install separate from the fabric venv (numpy version
conflicts) and run eval commands with the laya venv's interpreter:

```bash
WIKI_FABRIC_DIR=~/path/to/vault /path/to/laya-as-judge/.venv/bin/python   scripts/eval/eval-behavior.py --judge
```

**Calibration findings (Laya, live):** criteria-phrased questions
(`true_desc`/`false_desc`) are essential — abstract phrasing scores 0.3–0.6
even when the knowledge is present; criteria wording separates 0.97 vs 0.19.
Mining threshold defaults to 0.8 (unrelated pairs score ~0.75; 0.6 would
wrongly merge them). One laya-mlx checkpoint emits an "uncalibrated
temperatures" warning — treat sub-band confidences as advisory, which the
NEAR-THRESHOLD escalation already encodes.


## Agent harnesses

Wiki Fabric installs into any agent harness — see the matrix in
[Getting Started](./getting-started#agent-harness-support). `wf harness
install` detects what you use and writes the always-on block + skills in each
tool's native format; `wf harness status` shows the current state.

## Enabling

```bash
wf integrations                    # show what's active and what it changes
wf install --with-graphify         # enable at install time
wf update --with-graphify          # enable on an existing fabric
```

## Skill deltas when graphify is active

Each affected skill documents its delta:

| Skill | Inactive (default) | Active (`graphify.enabled: true`) |
|-------|--------------------|-----------------------------------|
| `refresh` | sha256 drift is the only staleness signal | `graphify-bridge --diff` runs first; graph hash diff prioritizes which claims to re-ingest |
| `ingest` | claims carry `source_refs` only | `graphify-bridge --enrich` attaches `code_symbols` + `graph_edges` (doc→code provenance) |
| `query` | expansion via claim `relations` (frontmatter) | expansion also follows call/import edges; code-reachable claims surface |
| `lint` | contract checks only | run `graphify-bridge --diff` after lint for code-staleness signal |
| `promote` | dossiers rest on experience outcomes | code-adjacent dossiers cite graph evidence |

When graphify is inactive, every script runs exactly as before — the flag gates *additional* steps, never core ones. The design rule: **integrations add capabilities; they are never load-bearing.**

## The fabric's self-graph

The fabric carries its own graph: `graphify-out/` is a code+docs graph of
`scripts/`, `README.md`, and `schemas/` (AST-extracted, 0 tokens). It maps the
real module structure — god nodes (`get_config()`), communities, cross-module
coupling — and is what the bridge diff/expand steps consult for claims about
wiki-fabric itself. Refresh after refactors with `graphify --update`.

---

---

Next: [Integration issues? Troubleshooting](./troubleshooting)
