---
type: ontology
title: Domain Ontology
updated: 2026-09-13
---

# Domain Ontology

The ontology is living — `python3 scripts/propose-domains.py` discovers new domains
from evidence signals. Domains below are a starting point; add yours as you
connect projects.

## Domains

- **agent-systems** — agent harnesses, MCP tool surfaces, retrieval/evaluation, prompt/skill design.
- **godot-systems** — Godot editor/runtime systems, game engine tooling, concurrency.

- **web-systems** — web backends, RLS, dashboards (nomokailist evidence).
- **trading-systems** — trading backends, backtests, portfolio tooling (alpaca-agents evidence).
- **mcp-systems** — MCP server protocol, tool-schema design, stdio transports (godot-mcp, comfyui-mcp evidence).
- **devops** — CI, runners, publishing pipelines (auto-proposed 2026-09-21, signal score: 9).

- **devops** — devops (auto-proposed 2026-09-21, signal score: 9).
   - Status: proposed — review and add examples before confirming.
- **mcp-systems** — mcp systems (auto-proposed 2026-09-21, signal score: 4).
   - Status: proposed — review and add examples before confirming.

## Shared tag set (lowercase)

- Cross-cutting: `agent`, `mcp`, `threading`, `safety`, `benchmark`, `git`, `evaluation`, `retrieval`
- Tooling: `godot`, `fastmcp`, `opencode`
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