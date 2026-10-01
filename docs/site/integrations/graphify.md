---
title: "Graphify — the code call-graph integration"
description: "AST-extracted code intelligence: doc→code provenance, stale-claim detection, code navigation"
type: index
---

# Graphify (code call-graph)

**Graphify** is a companion tool that parses a repo's code into a call-graph
(function → function → import edges) using AST parsing — **no LLM, 0 tokens**.
Wiki-fabric consults that graph for three things: detecting stale claims after
refactors, enriching claims with code provenance, and code navigation at task
time.

Enable:

```bash
wf install --with-graphify        # at install time
wf update --with-graphify         # on an existing fabric
# or fabric.yaml:
integrations:
  graphify:
    enabled: true
    graph_dir: graphify-out       # per-repo graph dir
```

## What each verb does

```bash
wf graphify status    # per-repo dashboard: nodes/links/communities/fresh
wf graphify all       # the full cycle: update → import → enrich → diff
wf graphify enrich    # attach code_symbols + graph_edges to existing claims
wf graphify diff      # which claims reference symbols that moved
```

Measured on this repo's own graphs (real `wf graphify status` output):

```
alpaca-agents   nodes=29153 links=56030 communities=1123 fresh=✓
aperiodic       nodes= 1705 links= 1564 communities= 167 fresh=✓
godot-agents    nodes= 5792 links=12607 communities= 285 fresh=✓
```

## The four capabilities

**1. Doc→code provenance.** After ingest, `enrich` attaches the code symbols
each claim's source references, so a claim is *code-reachable* — and an
agent can open the implementing file, not just the doc.

**2. Stale-claim detection (the AST diff).** You refactor `gather_reads`
into `collect_reads`; the claim "gather_reads makes O(N) reads ~O(1)" now
points at a symbol that no longer exists. `diff` detects the rename, names
the affected claims, and ranks them for re-ingest priority — what sha256
(unchanged file) alone can never see.

**3. Code navigation at task time.** `wf context` gains a **Code navigation**
block: task tokens → graph symbols → files ranked by matching-symbol count
("open these first"). 0 tokens, deterministic, absent entirely when graphify
is off — never load-bearing.

**4. Query ranking boost.** Claims whose `graph_edges` name a symbol the
query mentions get a capped ranking boost (`graphboost`), and
code-reachable claims that lexically miss surface as a dedicated
`symbol-discovered` tier — never ranked above lexical evidence.

## Skill deltas when graphify is active

| Skill | Inactive (default) | Active (`graphify.enabled: true`) |
|-------|--------------------|-----------------------------------|
| `refresh` | sha256 drift is the only staleness signal | `wf graphify diff` runs first; graph hash diff prioritizes which claims to re-ingest |
| `ingest` | claims carry `source_refs` only | `wf graphify enrich` attaches `code_symbols` + `graph_edges` (doc→code provenance) |
| `query` | expansion via claim `relations` (frontmatter) | expansion also follows call/import edges; code-reachable claims surface |
| `lint` | contract checks only | run `wf graphify diff` after lint for code-staleness signal |
| `promote` | dossiers rest on experience outcomes | code-adjacent dossiers cite graph evidence |

## The fabric's self-graph

The fabric carries its own graph: `graphify-out/` is a code+docs graph of
`scripts/`, `README.md`, and `schemas/`. It maps the real module structure —
god nodes (`get_config()`), communities, cross-module coupling — and is what
the bridge diff/expand steps consult for claims about wiki-fabric itself.
Refresh after refactors with `graphify --update` (or a commit — the graphify
hook plugin rebuilds on branch switches).

Optional tree-sitter language packs extend extraction beyond Python (e.g.
GDScript for game-repo fabrics).

## Language packs

Language packs extend graphify's parsing to other languages. When a pack is
installed, `enrich` and `diff` apply to that language too; otherwise those
repos are silently skipped by the cycle (never hard-fail).

## When it earns its keep

- The repo's docs reference code symbols; you navigate a codebase you
  didn't write; refactors rename code (AST staleness catches what sha256
  can't).
- **Skip it** for pure-ops repos with no code claims, or docs-only fabrics.

Design rule unchanged: **integrations add capabilities; they are never
load-bearing.** Graphify off ⇒ every script behaves exactly as the core
docs describe.