---
type: wiki-article
title: "Multi-Target Handling in Godot"
domain: [godot-systems]
review_after: 2027-01-19
---

# Multi-Target Handling in Godot

6 current claim(s) support this topic.

- The engine visits children of a skipped node's subtree, so a create whose parent is inside a non-editable instance is never saved, while an  [1]
- `_persistent_target` walks parents to the edited scene root, mutations apply live with a warning-with-effect and `ok: true`, and carry `pers [2]
- cmd_node_persistence gains probe_parent (create/instance/move — parent rule) and probe_parent_of (duplicate — resolves the parent of the nam [3]

---

[1] claim-godot-mcp-git-issue-477-md-003 — The engine visits children of a skipped node's subtree, so a create whose parent
[2] claim-godot-mcp-git-issue-477-md-006 — `_persistent_target` walks parents to the edited scene root, mutations apply liv
[3] claim-godot-mcp-git-pr-503-md-008 — cmd_node_persistence gains probe_parent (create/instance/move — parent rule) and

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
