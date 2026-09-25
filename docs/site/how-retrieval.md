---
type: index
title: "How It Works: Retrieval & Delivery (query + context)"
description: "How the fabric answers questions and compiles task context — without spending tokens"
created: 2026-09-20
updated: 2026-09-20
---

# How It Works: Retrieval & Delivery

Once knowledge is in the fabric, two commands make it useful — and both are
**deterministic**: no LLM, no API bill, no hallucinated summaries. This page
tells the story of a question and a task moving through them.

## Query: the question with a citation

An agent (or you) asks: *"Why does the write path batch?"* Four layers run:

**1. Type detection.** The question is routed by intent — `verify` questions
boost claims and locators, `decision` questions boost decisions and experience
events, `gap` questions surface open questions and contradictions. Type is
auto-detected or forced with `--type`.

**2. Lexical scoring.** Every page scores by concept overlap — words are
normalized and stemmed (`rotation` matches `rotating`), so morphological
variants still match. Pure string operations.

**3. Graph expansion.** Pages aren't scored in isolation: a claim that
`supports` or `contradicts` another claim pulls its neighbor in; with the
graphify integration, call/import edges also surface code-reachable claims.

**4. Structured answer.** The result isn't prose soup — it's
`bottom line / evidence / caveats / confidence / next action`, and every
evidence item links to the locator you can open and verify yourself.

When an answer is worth keeping, `--save` files it as a **synthesis page** —
the query result promoted to a citable page.

## Context compilation: precedence at work

`wf context` is the delivery end of the same machinery. Given a task, it:

1. Scores every page against the task's concepts (same deterministic scoring)
2. Applies **scope precedence**: project decisions > domain patterns > global
   policies — when artifacts conflict, the higher-precedence one wins
3. Filters by **status and freshness**: superseded pages are dropped, pages
   with an overdue `review_after` are dropped
4. Emits every inclusion *and* exclusion with its reason

The output is what the LLM receives — not a filesystem dump, not a RAG
pipeline's best guess, but a bounded manifest where the agent can cite the
artifact it followed.

## Why deterministic matters

Retrieval that costs tokens gets rationed; agents stop asking questions when
questions cost money. Deterministic retrieval inverts that: asking is free, so
agents ask constantly, and every answer is auditable after the fact — the same
input always produces the same manifest, which is exactly what a regression
gate needs.

## The human layer stays out of the machine context

`wf query` and `wf context` retrieve only **atoms** — claims, patterns,
decisions, concepts, experience events — never the generated human layer.
`wiki/` topics and `syntheses/` are OpenWiki-style paraphrases of claims: their
prose is for humans to read, not for a model to re-ingest (which would be
context bloat plus drift risk). Both retrieval surfaces skip `wiki/` and
`syntheses/`.

The wiki still gives the machine real value, but through its **derived edges**,
not its prose: `wf export wiki` writes `registry/wiki-graph.json` — the
topic/project → claim citation edges with staleness tiers and claim provenance,
as deterministic JSON alongside `catalog.json`. A model or agent that wants the
wiki's aggregation reads the graph for edges and cites the claim for the
content. Prose is read by people; edges are read by machines.

## The human exploration surface

For people, `wf export wiki` enriches every generated page with consistent,
OpenWiki-style anatomy — a `SUMMARY:` lead, a deterministic `## Key Takeaways` (from the page's own top-tier claims, never hallucinated), a `## Sources` backtrace to the cited claims, a `generated: {by, at}` provenance stamp, and validated/auto-repaired Mermaid diagrams. Explore the resulting `[[wikilinks]]` in Obsidian's native Graph view — it renders the topic↔topic↔project network. No separate HTML viewer is shipped; Obsidian is the human graph surface.

Next: [How It Works: The Compounding Loop](./how-compounding)
