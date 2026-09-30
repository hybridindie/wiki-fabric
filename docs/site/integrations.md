---
type: index
title: "Optional Integrations"
description: "Graphify call-graph intelligence, embeddings, and the judgment tier (off by default)"
created: 2026-09-19
updated: 2026-09-27
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
| **graphify** | claims carry `code_symbols` + `graph_edges` (doc→code provenance); `graphify-bridge --diff` adds AST staleness detection after refactors; **`wf context` gains a `Code navigation` block** — task tokens → graph symbols → ranked file shortlist (0 tokens, deterministic); code-reachable claims surface first (query ranking boost + symbol-discovery tier); optional tree-sitter language packs extend extraction to additional languages | 0 tokens (AST + community detection) |
| **obsidian** | the vault becomes **two-way**: `wf export wiki` harvests human edits to wiki notes as evidence *before* regenerating (an export manifest records path→hash at export time; human-changed notes land in `evidence/raw/<project>/obsidian/` with capture provenance); `--push` mirrors generated notes through the [Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api). Requires the Obsidian Local REST API plugin; key from the env var (or the plugin's data.json — gitignored) | 0 tokens |
| **embeddings** | `wf query` gains a semantic re-rank boost (fusion with lexical+graph, top-40 candidates, ~5 ms/query offline). **Ships off by default** — see "when each integration earns its keep" below | local inference (fastembed ONNX, ~30 MB, no network) |
| **judgment** | low-variance decision-model judging: promotion-mining near-miss refinement (automatic when enabled), `python3 scripts/eval/eval-behavior.py --judge` fixture scoring, and `wf verify-effects` — the independent second opinion on ingest effect classification (no more extractor-grades-own-homework) | ~$0.0004/call (cloud Jev) or on-device (local Laya) |

## When each integration earns its keep

All integrations are **off by default** — each ships value only under specific
conditions, measured where the claim is quantitative:

| Integration | Ship it when… | Skip it when… |
|---|---|---|
| **graphify** | the repo's docs reference code symbols; you navigate a codebase you didn't write; refactors rename code (AST staleness catches what sha256 can't) | pure-ops repo with no code claims; docs-only fabric |
| **obsidian** | you read/curate the wiki by hand in Obsidian (two-way harvest protects human edits) | the wiki is generated-read-only for you (agent-only consumption) |
| **embeddings** | corpus > ~2k claims (lexical collisions multiply; embedding space still separates topics) or cross-project word divergence is common; re-benchmark (`exp-embeddings-spike-2026-09-28`) at scale — at ~500 claims the measured gain was thin (+3 rel@10, none @5) | small corpus; strictly within-topic queries; determinism audits that can't tolerate an ML component |
| **judgment** | promotion mining gets real traffic (near-miss pairs decide dossiers); ingest volume is high enough that self-preference risk matters (verify-effects second opinion); retrieval fusion (rerank + hop gating) wanted. The ollama decision-model tier (tev1/nimble, localhost, no key) removes the "no key and no Mac" limitation — laya remains the on-device zero-server option | tiny fabric where keyword clustering suffices |

The deterministic core never depends on any of these — every gate, lint, and
manifest works with all integrations off.

## The judgment tier

Between the fabric's deterministic string ops (0 tokens, always) and its
generative LLM calls, the judgment tier is a third option: a decision model
that evaluates typed questions (yes/no probability, rubric score, choice)
against the assembled state and returns **typed answers with calibrated
probabilities** — no text generation. LangChain's benchmark of Jev as a judge
found 100% binary accuracy vs a human oracle with 92–913× lower variance than
GPT-5.6/Claude LLM judges, at ~1/80th Claude's cost.

**Where it may run (all live):**
- `python3 scripts/eval/eval-behavior.py --judge` — the `--llm` probe of behavior evals becomes a
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
- `wf verify-effects <claim.md>...` — the **independent second opinion on
  ingest effect classification**: each new claim is judged against its
  related pool (same-source, then same-project). Verdicts land in
  `<claim>.effects.json`; your draft classification stays yours — the tier
  kills the extractor-grades-its-own-homework self-preference risk.
- `wf context --judge-borderline` — **opt-in judged re-rank**: candidates in
  the same priority tier just past `--max` get one `noul` relevance judgment
  each (max +2 promotions). Promoted items carry
  `judged-relevant (judged p=0.66)` in the manifest and the receipt; the
  default path without the flag is byte-identical (0-token core preserved).

**Wire protocol (Jev cloud route):** `POST {base}/v1/systemone` with
`{model, state, questions}` and Bearer auth — one question per request; the
answer comes back schema-identical to the local laya shape
(`answers.<name>.<type>` with calibrated values) plus a usage block.
`base` defaults to `https://api.typesafe.ai`; override with
`TYPESAFE_BASE_URL` (env) or `integrations.judgment.base_url` (config) for
self-hosted judges. Model discovery: `GET /v1/models` (ships `jev-latest`,
`jev-preview`; served model reported in the response, e.g. `jev-1.13.0`).
Model ids: `cloud_model: jev-latest`. Live-measured: ~0.4 s/call.

Worked example (cloud route, from a live run):

```
$ wf verify-effects corpus/evidence/claims/claim-godot-mcp-...-003.md
claim-godot-mcp-godot-mcp-agents-md-003: 12 pair(s) judged → no non-trivial effects
```

`<claim>.effects.json` beside the claim:

```json
{"claim": "claim-godot-mcp-godot-mcp-agents-md-003", "route": "cloud",
 "pairs": [{"against": "claim-...-007", "effect": "contradicts", "confidence": 0.35},
           {"against": "claim-...-006", "effect": "no-action", "confidence": 0.91}]}
```

A low-confidence verdict (0.35, in the near-band) is the escalation case —
the agent re-reads both claims before finalizing relations.

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
    route: local           # cloud (TypeSafe Jev) | local
    local_backend: ollama  # local-first: tev1/nimble via ollama's /v1/systemone
    local_model: tev1:latest
    # alternatives: laya | laya-mlx | laya-torch | generic
```


Cloud route key resolution: `TYPESAFE_API_KEY` env var first, then
`integrations.judgment.api_key` in fabric.yaml (gitignored — same trust model
as `llm.api_key`). The miner pre-flights before running: `route: cloud` with
no key falls back to keyword clusters for that run, with a one-line message —
never a mid-run crash.
Local route dispatches through the on-device judgment stack (see below).


## Setting up the local backends

Four local judge options now exist; pick per machine:

### 1. Ollama decision models (default suggestion — no key, no weights download)

Ollama serves the **full System One wire protocol locally** — the same
`POST /v1/systemone` the Jev cloud route uses, minus auth. The decision
family (Tev/Nimble-class reasoner-classifiers) is what the server-side gate
accepts:

```bash
ollama pull tev1:latest     # 4B decision model (Together AI) — default judge
ollama pull nimble:latest   # 9B typed classifier (Bespoke Labs)
```

```yaml
integrations:
  judgment:
    enabled: true
    route: local
    local_backend: ollama
    local_model: tev1:latest   # default; nimble:latest for sharper typed heads
```

Live-calibrated (tev1 keep-warm, localhost): ~70ms/page batched rerank,
deterministic repeated verdicts, sharp separation on diverse candidates
(0.97 direct answer / 0.03 unrelated in one 4-page batch). `:cloud` tags
(`glm-5.3-flash:cloud`) are **refused on this tier** — they route over
ollama's hosted farm (egress), which would silently break the local tier's
privacy contract. Gemma/gemma4-class tags are valid ollama models but not
System One-supported (`"...use a local Nimble or Tev model"`) — the judge
falls back to `tev1:latest` with a notice.

The same endpoint powers **retrieval fusion** (see
[the retrieval tier](./how-retrieval)): top-candidate relevance rerank,
graph-hop gating, and claim-pair relation triage
(`scripts/lib/systemone.py`).

### 2. Laya (on-device typed heads, Apple Silicon fastest)

```bash
git clone https://github.com/rbrus/laya-as-judge.git
# or, for the packaged tool: uv tool install wiki-fabric --from dist/*.whl --force --with "~/path/to/laya-as-judge[mlx]"
# Platform: the local route auto-picks by platform —
#   Apple Silicon: laya-as-judge[mlx] (7-14ms typed heads, calibrated)
#   Windows/Linux/Intel: upstream laya (pip install laya; torch or ONNX INT8
#   CPU) — the same typed heads, ~1-3s/question CPU, cross-platform, no key.
#   Both stay on-device; Jev (cloud) is the third option, works everywhere.
#   Explicit pin: local_backend: laya-mlx | laya-torch | generic.
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

**Session capture** (`wf capture chat <slug>`) covers four harnesses:
Claude Code, opencode, OpenAI Codex CLI, and Gemini CLI. Formats were built
from the harnesses' own storage schemas (verified against
`google-gemini/gemini-cli`'s `chatRecordingTypes.ts` and claude-mem's
transcript schema). Design note vs claude-mem's approach: they capture via
*hooks* (SessionStart/UserPromptSubmit/PreToolUse events) — real-time but
plugin-dependent; wiki-fabric reads the *session stores* the harnesses write
anyway — zero install requirements, sha256 anti-loop, and thread-index
frontmatter on every capture. claude-mem's hook lifecycle mapped to our
file-based capture: SessionStart/Stop ≈ session boundaries (our capture is
whole-session), PreToolUse file extraction ≈ our tool-args files_touched
(bash commands excluded by rule).

## Enabling

```bash
wf integrations                    # show what's active and what it changes
wf install --with-graphify         # enable at install time
wf update --with-graphify          # enable on an existing fabric
```

### Obsidian two-way vault

```yaml
integrations:
  obsidian:
    enabled: true
    api_url: https://127.0.0.1:27124
    api_key_env: OBSIDIAN_REST_KEY
```

Requires the [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api) plugin (community plugin; install once into the vault). Then:

- `wf export wiki` — harvests human edits as evidence before regenerating (0 tokens; the manifest baseline is established on first run)
- `wf export wiki --push` — also mirrors the generated wiki through the REST API (Obsidian must be running)
- `wf integrations` — shows server reachability, key source, manifest state, pending harvest

Off by default; off = file-copy export exactly as the core docs describe.

### MCP server

```bash
uv tool install wiki-fabric --with mcp
wf-mcp    # stdio MCP server — any MCP client
```

Exposes `fabric_query` / `fabric_context` / `fabric_gate` / `fabric_thread` / `fabric_log` — the core surface as native tools, 0 tokens, subprocess-wrapped (never a reimplementation). Mutations beyond `log` stay CLI-gated.

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
