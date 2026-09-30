---
type: claim
id: claim-example-systemone-fusion
statement: "The retrieval fusion tier reranks top-k lexical candidates with a System One decision model and silently falls back to lexical order."
description: "Example claim page with a measured statement + the full provenance shape: source locator, verbatim quote, verification trail, and relations."
generated: { by: "agent/example/tev1-note", at: "2026-09-30T00:00:00Z" }
status: supported
confidence: high
evidence_strength: primary
source_refs:
  - source: "[[src-example-benchmark-notes]]"
    locator: "L120-L124"
    quote: "Retrieval is deterministic (lexical + graph expansion, 0 tokens). The System One fusion rerank is the one ranking signal on top of lexical order — a local decision model, egress-free, latency-budgeted, silent fall-back to lexical when disabled."
    supports: true
verified:
  - by: "process:locator-verification"
    at: "2026-09-30T00:00:00Z"
last_verified: 2026-09-30
relations:
  - target: "[[claim-example-cache-invalidation]]"
    type: "supports"
---

# Claim: System One fusion rerank

The fabric's retrieval contract is "lexical is the base, always free" — this
claim records the ONE sanctioned ranking signal above it: a local decision
model (ollama `/v1/systemone`, Tev/Nimble family) judging which top-k
candidates actually answer the query.

Measured (live, localhost, keep-warm):

| candidate | P(answers) |
|-----------|-----------:|
| direct answer | 0.970 |
| word-collision false positive | 0.026 |

The word-collision candidate scored **identically** to the direct answer
under set-overlap — the fusion tier is what kills it. Degrade contract:
judgment disabled / ollama down / >2s ⇒ `None` ⇒ lexical order stands.

**When to cite:** retrieval-rank questions, "which candidate answered?"
**When NOT to generalize:** this tier judges relevance only — it never
writes content, and every canonical merge stays human-gated (the
decision model is a judge, never a writer).