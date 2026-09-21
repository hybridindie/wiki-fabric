---
type: wiki-article
title: "JSON Envelope Protocol"
domain: [godot-systems]
review_after: 2027-01-19
---

# JSON Envelope Protocol

8 current claim(s) support this topic.

- Every tool is tagged with a safety class (read_only | mutating | destructive | runtime), where mutating/destructive tools take dry_run and d [1]
- The command envelope is {id, command, params} → {id, ok, result, error, hint}, correlated by id with many in flight." [2]
- A cmd_ping to {pong: true} exchange is the liveness health check." [3]
- Many requests may be in flight and each response is matched to its request by id, with correlation being concurrency-safe and no shared muta [4]

---

[1] claim-godot-mcp-godot-mcp-agents-md-008 — Every tool is tagged with a safety class (read_only | mutating | destructive | r
[2] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-007 — The command envelope is {id, command, params} → {id, ok, result, error, hint}, c
[3] claim-godot-mcp-godot-mcp-docs-architecture-md-005 — A cmd_ping to {pong: true} exchange is the liveness health check."
[4] claim-godot-mcp-godot-mcp-docs-architecture-md-006 — Many requests may be in flight and each response is matched to its request by id

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
