---
title: "Embeddings — the semantic re-rank"
description: "Offline semantic fusion for query ranking; ships off by default with measured value conditions"
type: index
---

# Embeddings (semantic re-rank)

A local semantic signal layered into `wf query`'s ranking: cosine(query,
claim) fused with the lexical score on the top-40 candidates. **Ships off by
default** — the measured value is conditional, see [when it earns its
keep](#when-it-earns-its-keep).

## Setup

```bash
uv tool install wiki-fabric --with fastembed    # ONNX runtime + model (once)
```

```yaml
integrations:
  embeddings:
    enabled: true
    model: all-MiniLM-L6-v2    # default; ~30 MB, cached offline
```

## What changes when it's on

- `wf query` builds (or loads) a local vector index over claim/pattern
  statements, scores every top-40 lexical candidate semantically, and fuses
  into the ordering — `RETRIEVAL["fuse_lex"]/["fuse_sem"]` (0.5/0.5).
  ~5 ms/query once vectors are cached; **no network** (fastembed ONNX,
  fully offline).
- `wf status` shows `Embeddings: enabled (vectors N)`.
- The System One fusion rerank (when the judgment tier is on) applies on
  top — embeddings widen the candidate pool semantically; the decision
  model judges which candidates *answer*.

## Determinism note

The lexical base and the graph expansion remain byte-identical and
re-runnable; embeddings add one more numeric signal to the fusion — same
corpus + same query ⇒ same fused order (model is pinned, vectors cached).
For determinism audits that can't accept an ML component at all: leave it
off (the default).

## When it earns its keep

- Corpus > ~2k claims: lexical collisions multiply and embedding space
  still separates topics.
- Cross-project word divergence is common (same concept, different
  vocabulary per repo).

**Skip it when:** small corpus; strictly within-topic queries. Measured in
the `exp-embeddings-spike-2026-09-28` experiment: at ~500 claims the gain
was thin (+3 rel@10, none at @5) — the value conditions above are the
result of that spike, not vibes. Re-benchmark when the corpus shape
changes materially.