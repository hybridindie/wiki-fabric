---
type: index
title: "Why not just a wiki, notes app, or RAG?"
description: "Failure modes of alternatives and the core bet"
created: 2026-09-19
updated: 2026-09-25
---

# Why Not Just a Wiki, Notes App, or RAG (Retrieval-Augmented Generation)?

Most knowledge systems fail agents (and humans) in the same ways. Wiki Fabric is designed against those failure modes — and, critically, the governance claims are **executable**: a deterministic linter enforces them (it flags out-of-scope pages, overdue reviews, unresolved sync conflicts, and sources that changed under their claims), CI proves them, and behavior evals measure delivery.

| Common system | Failure mode | Wiki Fabric's answer |
|---|---|---|
| **Wiki / notes app** (Obsidian, Notion, Confluence) | Pages drift from reality; nothing enforces freshness or provenance; orphaned pages rot silently | Every claim carries a `last_verified` date, a source locator, and a verbatim quote. A deterministic linter (14 checks) fails loudly on broken links, orphans, hash drift, and unsupported claims |
| **RAG / vector DB** | Retrieval is opaque; answers cite nothing auditable; stale chunks silently poison results; every question costs tokens | Retrieval is deterministic (lexical + graph expansion, 0 tokens). Answers are structured (`bottom line / evidence / caveats / confidence`) and every evidence item links to a line-level locator you can open and verify |
| **Memory tools** (session memory, auto-summaries) | Unstructured prose; contradicts itself over time; no way to tell "measured" from "guessed" | Claims are atomic and typed: `supported`, `contested`, `superseded`. Contradictions are represented, not collapsed. Confidence and evidence strength are explicit fields, not vibes |
| **ADR collections** (Architecture Decision Records — written records of why a technical choice was made) | Decisions recorded but never revisited; no feedback loop from outcomes | Decisions connect to experience events (what actually happened), which cluster into patterns with measured maturity. A pattern read but never applied gets flagged |
| **Prompt/skill libraries** | Copied between projects by hand; drift apart; no evidence of what works | Skills and patterns live in one global fabric. Promotion requires replication in ≥2 independent projects. Projects inherit them automatically at session start |
| **Second-brain tools** | Capture is cheap, retrieval and trust are expensive; nothing compounds | Structure from day one: capture → claim → concept → pattern. Each layer is machine-checkable, so the fabric stays queryable as it grows to thousands of pages |

The core bet: **an LLM is a good compiler but an unreliable memory.** So the fabric stores structured, source-anchored claims (not prose summaries), does all retrieval deterministically, and spends LLM tokens only where judgment is needed — extraction and synthesis. You review at defined gates; the machine handles the bookkeeping.

---

## What Is This?

Wiki Fabric is a governance layer and reference implementation for coding-agent memory. Four properties, each machine-enforced:

1. **Compiles raw sources into verified claims** — LLM extracts atomic assertions with line-level locators and verbatim quotes. Provenance is mandatory (lint: claims without sources can't become canonical).
2. **Promotes cross-project patterns with measured maturity** — experience events are deterministically clustered into promotion dossiers; promotion requires ≥2 independent projects and human review.
3. **Enforces scope precedence at task time** — `wf context` compiles project decisions > domain patterns > global policies into a manifest where every inclusion/exclusion carries a reason, and stale/superseded knowledge is filtered before it can mislead.
4. **Measures behavior, not vibes** — behavior evals verify the knowledge actually changes agent decisions (avoids banned approaches, honors constraints, escalates gaps); the compiler has its own golden-corpus eval; CI fails on regression.
Everything else — the `wf` CLI, uv installer, Obsidian vault, git-history capture, corpus sync — is reference implementation and integrations around that core.

---

## What is what: memory, context, and the fabric

It's tempting to call the fabric "the agent's memory" in the singular. That
conflates three different things:

- **Memory** is the capability: what the agent can retain and recall over
  time. Wiki Fabric is one *substrate* for it — a Git-governed external
  knowledge store — not the whole capability.
- **Context** is the runtime projection: the finite, model-visible payload for
  one inference step. `wf context` compiles it deterministically from
  project > domain > global knowledge; the harness adds live evidence (code,
  diffs, test output) at its own layer.
- **Working state** (plan, hypotheses, current step) belongs to the harness
  and the run, not the fabric. The fabric holds durable, attributable
  knowledge only.

Mapping the fabric's asset types to the standard agent-memory taxonomy
(working / episodic / semantic / procedural):

| Fabric asset | Memory type |
|---|---|
| Claims, concepts, decisions | semantic |
| Patterns, skills, policies | procedural |
| Experience events | episodic |
| Commitments (deferred obligations, `status: open`) | prospective |

A wiki page, a claim, a skill are storage formats — not memory types. What
matters is that each asset carries its own retrieval and trust policy, which
is why provenance, scope, and maturity are first-class fields.

---

Next: [See the architecture that implements this bet](./architecture)

---

---

## Local-first, cloud-optional

The governance spine is deliberately cloud-independent. The fabric's
deterministic core — capture, lint, context compilation, receipts, query,
mining's clustering, staleness detection — runs entirely on-device with zero
tokens. When the LLM is needed (claim extraction, synthesis, dossier
generation), each stage routes independently:

```yaml
repos:
  my-project:
    extract: local      # raw docs never leave the machine
    synthesize: local   # claims stay local too
    dossier: cloud      # experience events are less sensitive
```

The design bet: **an LLM is a good compiler but an unreliable memory** — so
the only stages that touch a model are compilation stages, and each one is
individually routable. Mixed clusters follow the least-private input (a
dossier over any cloud-routed project's events stays cloud; fully-local
clusters can go fully local). On-device runs via MLX (Apple Silicon) or
llama.cpp (GGUF, any OS), human-gated download, no always-on service.

What that means in practice:

- **Fully offline**: capture → claims (local extraction) → context → query →
  receipts → navigation → staleness → mining decisions — the whole daily loop
- **Cloud optional**: the compiler model is a quality tier for extraction and
  synthesis, validated by the same golden-corpus eval regardless of route
- **Private by configuration, not by policy**: per-repo, per-stage routing is
  the mechanism — sensitive repos pin all stages local, shared repos choose
  per stage

## Inspirations, and what this design adds

Wiki Fabric didn't invent its parts — it composes ideas from several lines of
work and adds the governance layer none of them ship. Crediting the sources
makes the additions legible.

| Inspiration | What it contributes | What Wiki Fabric adds beyond it |
|---|---|---|
| **Karpathy's LLM Wiki** | The core posture: an agent-maintained, interlinked Markdown wiki *between* raw sources and the agent — synthesized once, incrementally updated, not re-derived per query. | The wiki is **governed, not just maintained**: every claim carries provenance (source + locator + verbatim quote), a staleness gate, and a lint-enforced contract. A wiki page here is navigational memory, never ground truth — live code and tests outrank it. |
| **LangChain OpenWiki** | Wiki-as-agent-context: curated pages the agent reads before raw source, and wiki-memory as a durable substrate. | **Deterministic compilation instead of generation-time retrieval**: task context is compiled by pure string ops (0 tokens, byte-identical re-runs) with per-item reasons — and *persisted receipts* (`receipt-v1`) make "what the agent was told" an auditable artifact, not a transient prompt. |
| **CoALA's memory taxonomy** (working/episodic/semantic/procedural) | The vocabulary for typed memory stores with different update and retrieval rules. | Prospective memory is a first-class *asset kind* (`commitments/`) with trigger conditions that resurface obligations at task time — the forward-looking quarter CoALA names but most implementations omit. Scope precedence (project > domain > global) is enforced at compile time, not by prompt convention. |
| **Graphify** | Incremental AST knowledge graphs of code repos: call/import edges, communities, symbol neighborhoods. | The fabric **consumes the graph at task time**: a `Code navigation` block in every manifest (task → symbols → ranked files, 0 tokens), plus claim enrichment (`graph_edges`) and hash-based staleness detection that catches upstream graph changes between imports. |
| **System One decision models** (TypeSafe Jev; Laya-MLX open equivalent) | Low-variance, typed judgment: calibrated probabilities instead of autoregressive "LLM-as-judge" generation. | Judgment is a **tier with a contract**, never a core dependency: gated behind an integration flag, probability-recorded, never authoritative (near-threshold values escalate to the human gate), and test-isolated from the deterministic core. |

The through-line: each inspiration contributes a capability, and Wiki Fabric
wraps it in the same governance spine — provenance, scope, staleness, and
human gates are enforced by deterministic tooling (lint, CI, behavior evals)
rather than promised by convention. The unique flows are the seams between
inspired parts: the context manifest is where Graphify's structure, the
wiki's claims, and the memory taxonomy meet an agent's finite window.

## Design differences from each, in one line each

- **vs a plain LLM wiki**: knowledge is *governed* (lint, provenance, staleness), not just written.
- **vs RAG**: retrieval is deterministic and explainable; answers cite line-level locators you can open.
- **vs memory tools**: contradictions are represented (`contested`), not collapsed; confidence is a field, not a vibe.
- **vs ADR collections**: decisions connect to experience events; a pattern read but never applied gets flagged.
- **vs prompt/skill libraries**: promotion requires replication in ≥2 independent projects with measured maturity.
