---
title: "Judgment — the decision-model tier"
description: "Typed, calibrated judging: Jev cloud vs Laya on-device vs Tev1/Nimble via ollama vs generic — pros, cons, measured numbers, and setup"
type: index
---

# The Judgment Tier

Between the fabric's deterministic string ops (0 tokens, always) and its
generative LLM calls sits a third option: a **decision model** that answers
typed questions — yes/no probability (`noul`), rubric score, choice with
probabilities — against assembled state. No prose generation, ever.

> **The rule that never changes:** a decision model is a *judge, never a
> writer*. It supports checks; provenance, scope, and human gates still
> decide. A low-confidence verdict escalates (`NEAR-THRESHOLD`), it doesn't
> auto-approve. And the 0-token core (`wf context`, `wf query`, `wf lint`)
> never calls it — a test enforces that gate.

LangChain's benchmark of Jev as a judge found **100% binary accuracy vs a
human oracle, 92–913× lower variance than GPT-5.6/Claude LLM-judges, at
~1/80th Claude's cost** — that variance reduction is the whole point: a
calibrated judge lets CI gate *judgment*, not just determinism.

## Where it runs (all live)

| Surface | What the judge does | Route |
|---|---|---|
| `wf mine promotions` | near-miss cluster pairs judged "same pattern?" (merge / keep-split); an incoherence sweep demotes cluster members judged DIFFERENT from their representative (split) — an incoherent cluster can't reach a dossier intact | automatic when enabled |
| `wf verify-effects <claim>` | independent second opinion on effect classification (kills extractor-grades-own-homework); each pair gets a System One relation head too | per-claim, on demand |
| `wf eval behavior --judge` | the `--llm` probe becomes a `noul` judgment ("does the prompt deliver the binding decision?") | CI-gated |
| `wf eval stability --judge` | G4-J: fuzzy-gate-failed model pairs re-asked "same factual content?" | CI-gated |
| `wf context --judge-borderline` | opt-in: borderline beyond-`--max` candidates get one relevance judgment each (max +2 promotions, receipted) | explicit flag |
| retrieval fusion (`wf query`) | batch relevance rerank of top candidates + graph-hop gating | see [Retrieval](../how-retrieval) |
| review triage | stale-artifact reliability + claim-pair relations proposed to review queues | humans decide |

## The four backends — pick per machine

Everything speaks the same System One wire (`POST /v1/systemone`, identical
answer shapes) — `local_backend` picks *where* the weights live. Nothing
downstream changes when you switch.

### 1. Ollama decision models — `local_backend: ollama` (local-first default)

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
    local_model: tev1:latest
```

| | |
|---|---|
| **Pros** | no key; no pip dependency; server does the compute on GPU; batched rerank is fast (~70ms/page); sharp separation on *diverse* candidates — **0.970** direct answer vs **0.026** word-collision in one 4-page batch; `choice` heads return full probability maps |
| **Cons** | needs `ollama serve` up (the tier dies → degrade to lexical); 4.5–9.5 GB resident in the model slot; ~120ms/call un-batched; tev1 is a reasoner — needs `think:false` (handled) |

Measured on diverse candidates and near-misses both — this is the tier for
**retrieval fusion** and anything ranking candidates against a query.

### 2. Laya — `local_backend: laya` (auto: MLX on Apple Silicon, torch elsewhere)

| | |
|---|---|
| **Pros** | **7–14 ms** verdicts (in-process MLX — 10–20× faster than ollama); **no server dependency** (a pip package inside your process — works offline, in CI containers, on a plane); purpose-built judge with calibrated heads (related pairs ~0.93–0.96, unrelated ~0.75); tiny checkpoint (~3.4 MB); cross-platform via torch/ONNX CPU |
| **Cons** | Apple-Silicon-fastest path needs `laya-as-judge[mlx]` installed *separately from the fabric venv* (numpy conflicts); weaker on diverse-candidate ranking than the Ollama decision models; one checkpoint emits an "uncalibrated temperatures" warning (sub-band confidences are advisory — NEAR-THRESHOLD already encodes that) |

Laya wins the **hot loops**: mining's pairwise refinement (50 near-miss pairs
≈ 0.5s total), `--judge-borderline`, `eval` gates — anywhere many small calls
compound.

```bash
git clone https://github.com/rbrus/laya-as-judge.git
cd laya-as-judge && uv venv --python 3.12 && uv pip install -e '.[mlx]' --python .venv/bin/python
```

```bash
# isolation note: run eval through the LAYA venv (numpy version conflicts)
WIKI_FABRIC_DIR=~/path/to/vault /path/to/laya-as-judge/.venv/bin/python scripts/eval/eval-behavior.py --judge
```

Laya's EmulatorBackend (a keyword heuristic) is **rejected** by the `laya`
backend — real inference or nothing; a "judge" that returns identical
probabilities for related and unrelated content is worse than no judge.

### 3. Jev cloud — `route: cloud` (TypeSafe hosted)

```yaml
integrations:
  judgment:
    enabled: true
    route: cloud
    cloud_model: jev-latest        # or jev-preview
    api_key: <key>                 # or TYPESAFE_API_KEY env / secrets.env
```

| | |
|---|---|
| **Pros** | the calibrated hosted decision model the LangChain benchmark measured; zero local footprint; works on machines with no GPU and nothing installed; ~$0.0004/call |
| **Cons** | egress (per-call network); needs a key; the only tier with a per-call cost |

Pick this when local compute is unavailable or the calibrated hosted model
matters more than egress. The wire is identical to `route: local` — same
normalizer, so behavior parity is structural, not aspirational.

### 4. Generic — `local_backend: generic` (explicit only)

Any local text model (`llm.local_model`) emitting JSON verdicts via
`local_llm` (GGUF/llama.cpp, MLX). Lowest fidelity: no typed heads, no
calibration — for machines with *only* a GGUF file and no server. Never
auto-selected: it's the documented floor, not a default.

## Egress is a hard contract on the local tier

Ollama also hosts models remotely — tags like `:cloud`
(`glm-5.3-flash:cloud`) run on ollama's hosted farm. The local tier
**refuses** them loudly (a config error, not a silent swap):

```
LLM-CONFIG llm.local_model: 'glm-5.3-flash:cloud' routes over the network
(hosted farm) — not usable as a LOCAL judge; use a Tev/Nimble tag
```

Likewise ollama tags that aren't System One-supported (`gemma4:e4b-fixed` —
a valid ollama *model*, not a decision model) fall back to `tev1:latest`
with a notice. `wf models ensure --check` tells you which kind a tag is.

## Calibration findings (live, this fabric)

- **Criteria phrasing is the lever**: `true_desc`/`false_desc` worded
  concretely separates 0.97 vs 0.19; abstract phrasing only 0.3–0.6 vs 0.19.
  Write criteria like a spec, not a theme.
- **Mining threshold 0.8**: unrelated pairs score ~0.75 — a 0.6 threshold
  wrongly merges them. (Set once, live-calibrated; change only with a
  recorded eval.)
- **NEAR_BAND (0.1)**: values within the band escalate to the human gate —
  never auto-merge/auto-decide.
- **Deterministic repeats**: tev1 keep-warm returns identical probabilities
  across repeats (measured 3×) — CI-safe.

## The loudness contract

Pending human *decisions* (which judgment feeds) announce themselves:
terminal banner + bell at creation time (a fresh dossier is never silent),
a persistent `Gate:` line in `wf status`, optional macOS/webhook adapters.
See [Notifications](/integrations#the-loudness-contract).

## Hard contract summary

- **Never the 0-token core** — `wf context`/`query`/`lint` stay pure string
  ops (test-enforced); retrieval gains judgment only via the fusion tier.
- **Low-variance judgment, not determinism** — every judgment records
  backend + model + probability in the artifact.
- **Never authority** — a judge score supports a check; provenance, scope,
  and human gates decide.
- **Degrade everywhere** — server down, route off, timeout ⇒ the caller's
  deterministic behavior stands, byte-identical.