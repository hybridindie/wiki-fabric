---
type: wiki-article
title: "JSON Envelope Protocol"
domain: [godot-systems]
review_after: 2027-01-19
---

# JSON Envelope Protocol

8 current claim(s) support this topic.

- JSON envelopes are versioned from day one: commands are { id, command, params }, responses are { id, ok, result, error }, and requests corre [1]
- The command envelope is {id, command, params} to {id, ok, result, error, hint}, correlated by id with many requests in flight." [2]
- Many requests may be in flight concurrently, with each response matched to its request by id and no shared mutable per-request state." [3]
- In the response envelope, ok: true implies result is present and ok: false implies error and hint are present." [4]

---

[1] claim-godot-mcp-godot-mcp-agents-md-008 — JSON envelopes are versioned from day one: commands are { id, command, params },
[2] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-007 — The command envelope is {id, command, params} to {id, ok, result, error, hint},
[3] claim-godot-mcp-godot-mcp-docs-architecture-md-005 — Many requests may be in flight concurrently, with each response matched to its r
[4] claim-godot-mcp-godot-mcp-docs-architecture-md-006 — In the response envelope, ok: true implies result is present and ok: false impli

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
