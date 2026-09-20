---
type: index
title: "Why not just a wiki, notes app, or RAG?"
description: "Failure modes of alternatives and the core bet"
created: 2026-09-19
updated: 2026-09-19
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
 — LLM extracts atomic assertions with line-level locators and verbatim quotes. Provenance is mandatory (lint: claims without sources can't become canonical).
2. **Promotes cross-project patterns with measured maturity** — experience events are deterministically clustered into promotion dossiers; promotion requires ≥2 independent projects and human review.
3. **Enforces scope precedence at task time** — `wf context` compiles project decisions > domain patterns > global policies into a manifest where every inclusion/exclusion carries a reason, and stale/superseded knowledge is filtered before it can mislead.
4. **Measures behavior, not vibes** — behavior evals verify the knowledge actually changes agent decisions (avoids banned approaches, honors constraints, escalates gaps); the compiler has its own golden-corpus eval; CI fails on regression.


---

---

Next: [See the architecture that implements this bet](./architecture)
