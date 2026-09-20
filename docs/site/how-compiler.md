---
type: index
title: "How It Works: The Compiler (capture → ingest → claims)"
description: "The narrative path from a raw file on disk to governance-grade claims"
created: 2026-09-20
updated: 2026-09-20
---

# How It Works: The Compiler

This is the story of one file — say `docs/deployment.md` from a project you
just connected — becoming trustworthy, citable knowledge. Everything else in
wiki-fabric exists to serve this pipeline.

## Before the LLM sees anything

Capture copies the file into `evidence/raw/<project>/` and computes its
**sha256** — a cryptographic fingerprint of the exact bytes. That hash is the
anchor for everything that follows: when the file changes later, the fabric
can tell *exactly* which claims are affected, because every claim will point
back at this specific version of this specific file.

## One prompt, one contract

The extraction prompt is the compiler's most important artifact. It does three
things that make small models viable:

1. **Numbers every line** — `L1:`, `L2:`, … so the model can cite ranges
   instead of inventing locations
2. **Specifies granularity** — "exactly ONE distinct verifiable fact per
   claim, expressed in one sentence, target 5–12 claims." Without this,
   models split one fact into fragments or merge unrelated ones — and
   *different models disagree wildly* (fuzzy 0.28 before the spec; 0.75–0.85
   after)
3. **Demands a verbatim quote** — each claim must return the exact source text

## The repair pass: why models get credit for honesty

Models are good readers and sloppy typists. They strip markdown artifacts and
join lines — so the quote they return is often a *paraphrase* of the source,
not the source. The compiler treats that as **repairable**, not fatal:

```text
model says:  "The payment service retries failed webhook deliveries up to 5 times"
source says: "The payment service **retries failed webhook deliveries** up to 5 times."
             → fuzzy-match normalizes both, finds the true span,
               rewrites the quote to the verbatim text
```

This one deterministic fix moved gemma-4 E4B's quote rate from 0.65 to 0.96 —
and it applies to every model, cloud included. Models aren't wrong so much as
*lossy in predictable ways*; the compiler compensates deterministically rather
than paying for a bigger model.

## Verification, not trust

After extraction, every claim's locator is verified against the source: does
the quoted text actually appear on those lines? If not, the claim's locator is
rewritten to where the text actually lives. This runs as a `process:` actor —
deterministic, model-independent — so the audit trail distinguishes *what the
model asserted* from *what was verified*.

## The human gate

The result is a change-set: a manifest of new claims + a diff, sitting in
`evidence/traces/change-sets/`. Lint runs (0 errors gate). A human reviews.
Only then does it merge into the corpus, append to `registry/log.md`, and
commit. The LLM never writes canonical knowledge by itself — it proposes, you
decide.

## Why the anti-loop matters

Re-running ingest on an unchanged file would re-spend tokens for identical
output. So the sha256 is checked first: matching hash = skip. Files recorded
but never extracted (`status: pending`) resume cleanly. One capture, one
compile, one review — then it's free forever.

Next: [How It Works: Retrieval & Delivery](./how-retrieval)
