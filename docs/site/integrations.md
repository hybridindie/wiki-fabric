---
type: index
title: "Optional Integrations"
description: "Graphify call-graph intelligence and embeddings (off by default)"
created: 2026-09-19
updated: 2026-09-19
---

# Optional Integrations

Integrations add capabilities on top of the core loop. They are declared in `fabric.yaml` (see [Configuration](./configuration)) and are **never load-bearing** — with the integration off, every script behaves exactly as the core docs describe.

Integrations are **off by default** and declared in `fabric.yaml`:

```yaml
integrations:
  graphify:
    enabled: true          # call-graph intelligence
    graph_dir: graphify-out
  embeddings:
    enabled: false         # semantic re-ranking (planned)
```

```bash
wf integrations                    # show what's active and what it changes
wf install --with-graphify         # enable at install time
wf update --with-graphify          # enable on an existing fabric
```

**When graphify is active**, skills change behavior — each affected skill documents the delta:

| Skill | Inactive (default) | Active (`graphify.enabled: true`) |
|-------|--------------------|-----------------------------------|
| `refresh` | sha256 drift is the only staleness signal | `graphify-bridge --diff` runs first; graph hash diff prioritizes which claims to re-ingest |
| `ingest` | claims carry `source_refs` only | `graphify-bridge --enrich` attaches `code_symbols` + `graph_edges` (doc→code provenance) |
| `query` | expansion via claim `relations` (frontmatter) | expansion also follows call/import edges; code-reachable claims surface |
| `lint` | contract checks only | run `graphify-bridge --diff` after lint for code-staleness signal |
| `promote` | dossiers rest on experience outcomes | code-adjacent dossiers cite graph evidence |

When graphify is inactive, every script runs exactly as before — the flag gates *additional* steps, never core ones. The design rule: **integrations add capabilities; they are never load-bearing.**

The fabric carries its own self-graph: `graphify-out/` is a code+docs graph of
`scripts/`, `README.md`, and `schemas/` (AST-extracted, 0 tokens). It maps the
real module structure — god nodes (`get_config()`), communities, cross-module
coupling — and is what the bridge diff/expand steps consult for claims about
wiki-fabric itself. Refresh after refactors with `graphify --update`.

---
