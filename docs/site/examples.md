---
title: "Examples"
description: "Worked examples from real sessions — the System One fusion rerank, the freshness cycle, local-model routing, and end-to-end fabric loops"
---

# Examples

Every example here is traceable to a real run on the repo that ships it —
commands you can copy, outputs with real numbers. When the tooling changed,
the example gets re-run (a stale example is worse than none: agents copy them
verbatim).

| Example | What it shows |
|---------|---------------|
| [systemone-rerank](#system-one-fusion-rerank) | the local decision-model tier reordering retrieval |
| [freshness-cycle](#the-freshness-cycle) | scheduled upstream drift → evidence → team corpus |
| [local-model-routing](#local-model-routing) | privacy tiers: ollama tags vs on-device HF vs cloud |
| [context-receipt-loop](#context-receipts-the-auditable-loop) | receipts ↔ outcomes: delivery you can audit |

## System One fusion rerank

The problem: lexical scoring gives two candidates the **same** overlap score
when they collide on words; only one actually answers the question. The
System One tier (a local decision model — ollama serves the same wire
protocol the Jev cloud uses, no auth, no egress) judges which top-k
candidates genuinely answer.

Measured live on this repo's fabric (10,419 pages, tev1:latest keep-warm on
localhost):

```
$ wf query "why do concurrent readers see torn state" --verbose
Query type: concept
Pages loaded: 10419
Scored pages: 618
  0.576 [claim   ] claim-alpaca-agents-...-workflow-analysis-md-003
  ...
  systemone rerank: {...}          # ← P(page answers) per top-10 candidate
  hop-gate reranked 3 edges        # ← graph hits ordered by P(edge serves query)
After graph expansion: 621
```

The separations are multi-order on diverse candidates (same batch,
one state, one call):

| candidate | P(answers) |
|-----------|-----------:|
| direct answer (single-writer, non-atomic rewrites) | **0.970** |
| vocabulary page mentioning "torn write" | 0.665 |
| scoped-adjacent (ontology: atomicity is global) | 0.329 |
| word-collision page (Ollama endpoints) | **0.026** |

The set-overlap scorer gives the two word-collision pages *identical* scores;
the rerank tier is what kills the false positive. Contracts:

- **silent fall-back** — judgment disabled, ollama down, or >2s ⇒ `None`
  ⇒ lexical order stands (test: `tests/test_systemone.py::TestDegradeContracts`)
- **never above lexical evidence** — the fusion weight is bounded
  (`RETRIEVAL["fuse_lex"]/["fuse_sem"]`), and graph hits (hop-gated) can
  never exceed `graph_seed_score` (0.1)
- **explicit opt-out** — `wf query ... --no-rerank`

Also on the same tier: `wf verify-effects` gains a pairwise
relation head (`supports / contradicts / supersedes` + probabilities +
confidence) — proposed contradictions flow to the review queue; **humans
decide**, contested states are the representation.

## The freshness cycle

Hooks capture *local* commit drift on *active* machines — but a team whose
every machine is dormant for a week can carry silently stale claims. The
freshness cycle makes upstream freshness independent of anyone's habits.

```bash
$ wf freshness --dry-run                    # all connected projects
=== alpaca-agents ===
  git-history: clean                        # sha256-gated: nothing new upstream
=== aperiodic ===
  git-history: captured                     # 60 new PR/issue records detected
  reverify:    clean (0 overdue+stale)
```

For real (writes evidence + the `.last-capture` state marker):

```bash
$ wf freshness                              # per connected repo
$ wf gate                                   # what needs a human
```

Scheduled on the corpus CI (scaffolded automatically by `wf sync init` /
`wf sync setup` — daily, opt-in via repo variable `WIKI_FABRIC_FRESHNESS=1`):

```
freshness.yml (corpus CI)
  → capture-git --since-state per repos: entry   (0 tokens, sha256-gated)
  → review --auto-reverify                        (mechanical, 0 tokens)
  → commit + push refreshed evidence
  → teammates: wf sync pull
```

Evidence-plane only: the cycle never rewrites claims; stale/contested states
are the representation; re-extraction stays opt-in per routing tier.

## Local-model routing

Privacy tiering is per-stage, per-repo — the fabric carries the decision,
each machine may override. Three local tiers + one cloud tier:

```yaml
# fabric.yaml — the decided defaults
llm:
  base_url: http://localhost:11434/v1
  local_model: gemma4:e4b-fixed            # ollama-served (tier 1: server-local)
  compiler_model: deepseek-v4.1-flash:cloud  # tier 4: cloud (compiler policy)

repos:
  auth-service:        # sensitive repo → everything on-device
    extract: local
    synthesize: local
  docs-repo:           # public docs → cloud is fine
    extract: cloud
```

| Tier | Model shape | Runs where | Egress |
|------|-------------|-----------|--------|
| 1. ollama-served | bare tags (`gemma4:e4b-fixed`, `tev1:latest`) | the local ollama server | **none** |
| 2. on-device HF | `mlx-community/*` (Apple), `*GGUF` | in-process (mlx-lm / llama-cpp) | **none** (model download once, human-gated) |
| 3. decision models | `tev1/nimble` tags | local ollama — **judging only** (rerank, review triage, mining gates) | **none** |
| 4. cloud | ids (deepseek, jev-latest) | hosted APIs | yes — never on the local tier |

Two traps the tooling now catches for you:

- **`:cloud` tags are NOT local** — ollama's hosted farm egresses.
  `looks_like_local_model` refuses them as `local_model`, and lint flags a
  fabric.yaml that sets one: `LLM-CONFIG llm.local_model: ... routes over
  the network (hosted farm)`.
- **Gemma4 tags can't be judges** — ollama's System One endpoint serves only
  the Tev/Nimble family; `wf models ensure --check` reports
  `OK: gemma4:e4b-fixed (ollama-served)` for extraction, and the judge falls
  back to `tev1:latest` with a notice.

Verification loop (0 LLM tokens until extraction):

```bash
wf models ensure --check          # presence probe (ollama list / HF cache)
wf ingest docs/auth.md --extract-claims   # routes via repos tier (local ⇒ gemma4)
```

## Context receipts: the auditable loop

Delivery must be reviewable against what was known — receipts make the
manifest a durable record:

```bash
$ wf context --task "Fix the torn-read window in catalog rebuild" --write-receipt
receipt: <fabric>/corpus/registry/receipts/receipt-6b965337825f.json (receipt-6b965337825f)
## Context Manifest
... (selected/excluded, every item with a reason) ...

$ # ... solve the problem, then log the outcome against that receipt:
$ wf log --project catalog --receipt receipt-6b965337825f \
    --problem "concurrent readers see torn state" \
    --intervention "single-writer mutex + atomic rewrite" \
    --outcomes "torn reads gone; rebuild latency unchanged"
```

Receipt ↔ outcome linkage is the evidence plane mining consumes: patterns
promote only with ≥2 independent projects, dossiers need human review, and
`wf utility` shows which patterns actual sessions used. The full
contract lives in [schemas/frontmatter.md](https://github.com/hybridindie/wiki-fabric/blob/main/schemas/frontmatter.md).