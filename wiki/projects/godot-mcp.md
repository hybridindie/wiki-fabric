---
type: index
title: "godot-mcp: What We Learned"
review_after: 2027-03-20
---

# godot-mcp: Project Retrospective

godot-mcp is an MCP bridge into the Godot editor. Its role is to let an agent drive the editor directly — for visual verification and live scene manipulation — instead of reasoning about scenes from source files alone. That matters because the editor is the only authority on what a scene actually contains and renders; a bridge that can inspect and mutate live state closes the gap between "the code looks right" and "the scene is right." The project also carries the graphify guard plugin for opencode, which keeps agent tool use honest about the knowledge graph.

## What was built

The Godot side is an addon with a command router at `res://godot/addons/godot_mcp/command_router.gd`, dispatching named commands including `Inspect` and `Coerce`. Object property coercion and null-write handling were hardened as part of this work.

The opencode side is `.opencode/plugins/graphify.js`, rewritten to port graphify's full Claude Code `PreToolUse` guard pair from `graphify/cli.py:_run_hook_guard`, replacing the previous once-per-session echo. Three mechanisms came out of that port:

- **Search guard** — fires on executed tokens with heredoc bodies and quoted spans stripped and wrappers skipped, so a command like `git commit -m "add flag support"` never triggers it (#3121 port).
- **Read/glob guard** — applies only to in-project source files, exempts `graphify-out/` reads, and softens to the STALE nudge rather than blocking when a file is newer than `graph.json` or a `.needs_update` marker exists (#1840 port).
- **Strict mode** — enabled by `GRAPHIFY_HOOK_STRICT=1` with TTL via `GRAPHIFY_HOOK_STRICT_TTL`; the first read per session of an indexed file gets a forceful once-only reminder, suppressed while `graphify-out/cache/last_query_stamp` is fresh.

Nudge transport prepends a shell-safe `echo '<text>' ;` to bash commands and appends the nudge to the tool result via `tool.execute.after` for read/grep/glob. A new `.opencode/rules/godot-mcp.md` documents what the bridge is for.

## Constraints discovered

The Godot 4.7 `EditorInterface` documentation page is 619 lines and exposes exactly 17 methods whose names contain "scene", spanning `close_scene()` through `stop_playing_scene()`. The only scene-closing method is `Error close_scene()`, which takes zero parameters, closes the currently active scene discarding pending changes, and returns `ERR_DOES_NOT_EXIST` if there is no scene to close. There is no close-by-path, close-by-index, or close-all variant. There is no method to make a different open scene tab active — no `set_current_scene`, no `activate_scene_tab`. `open_scene_from_path` opens a path and creates a new inherited scene when `set_inherited` is true, but documents no focus-existing-tab behavior. `reload_scene_from_path` fails if the scene is not open. `get_open_scenes()` and `get_open_scene_roots()` list open scenes, but the active-tab cursor can only be moved implicitly. The page has no Signals section at all — only Description, Properties, Methods, Property Descriptions, Method Descriptions, and user-contributed notes — and a case-insensitive search for `signal`, `scene_closed`, `scene_tab*`, `tab_closed`, and `tab_changed` returns zero matches. `EditorInterface` inherits plain `Object` and declares no signals. The consequence is structural: a `cmd_close_scene` handler must activate the target tab first or be limited to closing the currently active scene.

The opencode platform imposes its own limit. Because opencode cannot deny from `tool.execute.before`, Claude's `permissionDecision: deny` degrades to a strong once-per-session nudge, and session markers reuse the same `graphify-out/cache/hook_sessions/<sid>.denied` files the Claude hook writes. There is no `PreToolUse` `additionalContext` channel, which is why nudges ride on shell prefixes and `tool.execute.after` instead.

## Patterns that emerged

Several durable rules came out of the work. **Never create a new preview, always update** — `_add_preview_at` creates numbered nodes while `_move_preview_to` updates, so both paths must be checked. **Per-tick budget** (4096 cells, sorted round-robin) keeps floods from hitching the frame while preserving determinism. **Progressive rebuild** meshes a few chunks per editor frame instead of freezing. Wrong invariants hide in comments: the note on lines 147–148 that

---

_Generated from the evidence fabric on 2026-09-21. 845 current claim(s) from 845 analyzed sources._
