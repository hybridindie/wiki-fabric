---
type: wiki-article
title: "Godot Undo/Redo History API"
domain: [godot-systems]
review_after: 2027-01-19
---

# Godot Undo/Redo History API

8 current claim(s) support this topic.

- There is no history introspection, so an agent cannot see stack depth, current action name, or undo/redo availability; `cmd_undo`'s `dry_run [1]
- The proposed `cmd_redo` mirrors `cmd_undo` with `count`, `dry_run` (has_redo + next action name), `redone`/`requested`/`last_action` result, [2]
- The proposed read-only core `cmd_list_history` returns `{ depth, has_undo, has_redo, can_redo, current_action, recent: [...] }` capped at ab [3]
- Godot's `UndoRedo` exposes `has_undo()`/`has_redo()`/`get_current_action_name()` but no public stack-depth or entries API in 4.7, a caveat t [4]

---

[1] claim-godot-mcp-git-issue-529-md-003 — There is no history introspection, so an agent cannot see stack depth, current a
[2] claim-godot-mcp-git-issue-529-md-004 — The proposed `cmd_redo` mirrors `cmd_undo` with `count`, `dry_run` (has_redo + n
[3] claim-godot-mcp-git-issue-529-md-005 — The proposed read-only core `cmd_list_history` returns `{ depth, has_undo, has_r
[4] claim-godot-mcp-git-issue-529-md-006 — Godot's `UndoRedo` exposes `has_undo()`/`has_redo()`/`get_current_action_name()`

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
