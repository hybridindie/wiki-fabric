---
type: wiki-article
title: "Bounded Buffer with Honest Truncation"
domain: [godot-systems]
review_after: 2027-01-19
---

# Bounded Buffer with Honest Truncation

6 current claim(s) support this topic.

- Truncation must be honest: a bounded buffer with explicit truncated/dropped counts and no silent drops, per the error-handling honesty rules [1]
- mcp_debugger.gd keeps a bounded ring with cap and honest dropped counts, one per peer, and godot_runtime_get_output is a thin pass-through w [2]
- The editor pulls game output on demand via `godot_mcp:get_output` → `godot_mcp:game_output` using a poll-and-cache pattern with no unsolicit [3]

---

[1] claim-godot-mcp-git-issue-534-md-004 — Truncation must be honest: a bounded buffer with explicit truncated/dropped coun
[2] claim-godot-mcp-git-issue-534-md-009 — mcp_debugger.gd keeps a bounded ring with cap and honest dropped counts, one per
[3] claim-godot-mcp-git-pr-547-md-003 — The editor pulls game output on demand via `godot_mcp:get_output` → `godot_mcp:g

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
