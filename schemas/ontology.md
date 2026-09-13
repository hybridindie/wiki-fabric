---
type: ontology
title: Domain Ontology
updated: 2026-09-11
---

# Domain Ontology

## Domains

- **agent-systems** — agent harnesses, MCP tool surfaces, retrieval/evaluation, prompt/skill design.
   - Examples of evidence here: godot-mcp tool-surface, batch/pipeline performance, sessionless migration.
- **godot-systems** — Godot editor/runtime, procedural world generation, threading, chunk streaming.
   - Examples: aperiodic monotile terrain, godot-mcp four-layer bridge, debugging protocol.

- **web-systems** — web systems (auto-proposed 2026-09-13, signal score: 79).
   - Status: proposed — review and add examples before confirming.
- **mcp-systems** — mcp systems (auto-proposed 2026-09-13, signal score: 19).
   - Status: proposed — review and add examples before confirming.
- **devops** — devops (auto-proposed 2026-09-13, signal score: 9).
   - Status: proposed — review and add examples before confirming.

## Shared tag set (lowercase)

- Cross-cutting: `agent`, `mcp`, `threading`, `safety`, `benchmark`, `procedural-generation`, `git`, `evaluation`, `retrieval`
- Tooling: `godot`, `godot-mcp`, `fastmcp`, `opencode`
- Math/domain: `tiling`, `aperiodic`, `spectre`, `hat`, `voxel`, `terrain`
- Knowledge-model: `provenance`, `pattern`, `experience-event`, `promotion`

## Scope → home mapping

- `global` → `global/*` (patterns, anti-patterns, skills, playbooks, decision-rules, entities, principles)
- `domain` → `domains/<domain>/{concepts,questions,syntheses}`
- `project` → `projects/<repo>/{experience-events,decisions}`

## Independence rule

Two evidence items sharing one lineage (same source captured into two repos, or two
claims citing the same `source` with no independent corroboration) count as **one**
evidence lineage. State lineage explicitly when clustering.

## Retrieval signal types

- `lexical` — index / grep / code-aware
- `graph` — `relations` expansion through claims/entities
- `recency` — last-verified / captured date weighting
- `uncertainty` — open `questions/` + unresolved `contradicts` relations
