---
type: index
title: "godot-mcp: What We Learned"
review_after: 2027-03-20
---

# godot-mcp: Retrospective

godot-mcp is the bridge between an agent and a running Godot editor. Its core is an editor addon — `res://godot/addons/godot_mcp/command_router.gd` — that exposes live scene manipulation and visual verification as MCP commands, backed by a rules file (`.opencode/rules/godot-mcp.md`) that states what the bridge is for. Alongside it, the project maintains `.opencode/plugins/graphify.js`, the opencode-side port of graphify's Claude Code `PreToolUse` guard pair. The two halves share a theme: both are seams where an agent's intent has to be translated into a host environment that was not designed for it, and both are constrained by what that host will actually let you do.

## What was built

The command router defines commands including `Inspect` and `Coerce`, and the addon is loaded as a Godot editor plugin. The graphify plugin was rewritten to port graphify's full Claude Code `PreToolUse` guard pair from `graphify/cli.py:_run_hook_guard`, replacing a previous once-per-session echo. That port includes a search guard that fires on executed tokens with heredoc bodies and quoted spans stripped and wrappers skipped, so a command like `git commit -m "add flag support"` never triggers it. A read/glob guard applies only to in-project source files, exempts `graphify-out/` reads, and softens to the STALE nudge rather than blocking when a file is newer than `graph.json` or a `.needs_update` marker exists. Strict mode, enabled by `GRAPHIFY_HOOK_STRICT=1` with a TTL via `GRAPHIFY_HOOK_STRICT_TTL`, gives the first read per session of an indexed file a forceful once-only reminder, suppressed while `graphify-out/cache/last_query_stamp` is fresh.

## Constraints discovered

The Godot 4.7 `EditorInterface` documentation page is 619 lines and complete. It exposes exactly 17 methods whose names contain "scene", and the only scene-closing method is `Error close_scene()`, which takes zero parameters, closes the currently active scene while discarding pending changes, and returns `ERR_DOES_NOT_EXIST` if there is no scene to close. There is no close-by-path, close-by-index, or close-all variant, and no method to make a different open scene tab active — no `set_current_scene`, no `activate_scene_tab`. `open_scene_from_path` does not document a focus-existing-tab behavior, and `reload_scene_from_path` fails if the scene is not open. `get_open_scenes()` and `get_open_scene_roots()` list open scenes, but the active-tab cursor can only be moved implicitly. The page has no Signals section at all — only Description, Properties, Methods, Property Descriptions, Method Descriptions, and user-contributed notes — and a case-insensitive search for `signal`, `scene_closed`, `scene_tab*`, `tab_closed`, and `tab_changed` returns zero matches. `EditorInterface` inherits plain `Object` and declares no signals.

opencode imposes its own limits: it cannot deny from `tool.execute.before`, and it has no `PreToolUse` `additionalContext` channel.

## Patterns that emerged

Guard logic works at the token level, not the string level: strip heredoc bodies and quoted spans, skip wrappers, then match. Guards are scoped to in-project source and exempt generated output. When state is merely stale, the guard softens to a nudge instead of blocking. On the Godot side, the durable rules are "never create previews — always update" (checking both `_move_preview_to` and `_add_preview_at`), a per-tick budget of 4096 cells sorted round-robin so floods cannot hitch the frame and determinism holds, and progressive rebuild that meshes a few chunks per editor frame instead of freezing. These are load-bearing enough to have been promoted: [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], [[pattern-cluster_cf12208f]].

## Decisions made

Port the full guard pair rather than the once-per-session echo. Because opencode cannot deny from `tool.execute.before`, Claude's `permissionDecision: deny` degrades to a strong once-per-session nudge, and session markers reuse the same `graphify-out/cache/hook_sessions/<sid>.denied` files the Claude hook writes. Nudge transport prepends a shell-safe `echo '<text>' ;` to bash commands and appends the nudge to the tool result via `tool.execute.after` for read/grep/glob. On the Godot side, previews are updated in place rather than created as numbered nodes, and mesh work is budgeted per tick.

## Current state

Several items remain open. A `cmd_close_scene` handler would need to activate the target tab first or be limited to closing the currently active scene, because scene-tab closing can only target the active tab and `EditorInterface` offers no tab-activation API. The graphify backend guard has a real bypass: any argument equal to `ollama` triggers it, and the `--backend=ollama` form is unrecognized. `EditorInterface.close_scene()` closes the active tab rather than the one for the deleted path, so multi-tab deletes close the wrong scene. Regression tests are missing — two bugs shipped because an edit changes the mesh — and a comment on lines 147–148 claiming "Node space is block units" states the wrong invariant, since children are scaled meshes.

---

_Generated from the evidence fabric on 2026-09-21. 845 current claim(s) from 845 analyzed sources._
