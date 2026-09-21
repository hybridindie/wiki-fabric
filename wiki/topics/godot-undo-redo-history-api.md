---
type: wiki-article
title: "Godot Undo/Redo History API"
domain: [godot-systems]
review_after: 2027-01-19
---

# Godot Undo/Redo History API

8 current claim(s) support this topic.

- The proposed `cmd_redo` mirrors `cmd_undo` with `count`, `dry_run` (has_redo + next action name), and `redone`/`requested`/`last_action` res [1]
- The proposed `cmd_list_history` is read-only core returning `{ depth, has_undo, has_redo, can_redo, current_action, recent: [...] }` capped  [2]
- Godot's `UndoRedo` exposes `has_undo()`, `has_redo()`, and `get_current_action_name()` but no public stack-depth/entries API in 4.7." [3]
- If depth is not queryable, the proposed implementation should return the honest subset (`has_undo`, `has_redo`, `current_action`) and docume [4]

---

[1] claim-godot-mcp-git-issue-529-md-003 — The proposed `cmd_redo` mirrors `cmd_undo` with `count`, `dry_run` (has_redo + n
[2] claim-godot-mcp-git-issue-529-md-004 — The proposed `cmd_list_history` is read-only core returning `{ depth, has_undo,
[3] claim-godot-mcp-git-issue-529-md-005 — Godot's `UndoRedo` exposes `has_undo()`, `has_redo()`, and `get_current_action_n
[4] claim-godot-mcp-git-issue-529-md-006 — If depth is not queryable, the proposed implementation should return the honest

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
