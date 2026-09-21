---
type: wiki-article
title: "Bounded Buffer with Honest Truncation"
domain: [godot-systems]
review_after: 2027-01-19
---

# Bounded Buffer with Honest Truncation

6 current claim(s) support this topic.

- Truncation must be honest: a bounded buffer with explicit truncated/dropped counts and never silently dropping entries." [1]
- mcp_debugger.gd keeps a bounded ring with a cap and honest dropped counts, one per peer." [2]
- The probe uses a bounded 500-entry ring buffer guarded by a Mutex, with eviction counted in dropped." [3]

---

[1] claim-godot-mcp-git-issue-534-md-004 — Truncation must be honest: a bounded buffer with explicit truncated/dropped coun
[2] claim-godot-mcp-git-issue-534-md-009 — mcp_debugger.gd keeps a bounded ring with a cap and honest dropped counts, one p
[3] claim-godot-mcp-git-pr-547-md-003 — The probe uses a bounded 500-entry ring buffer guarded by a Mutex, with eviction

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
