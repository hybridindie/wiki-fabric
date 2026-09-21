---
type: index
title: "godot-mcp: What We Learned"
review_after: 2027-03-20
---

# godot-mcp — Project Retrospective

godot-mcp is an MCP server that puts the Godot editor behind an agent-facing tool surface: scene operations, asset import, script support, and the bridge that carries commands between the editor addon and the calling agent. Alongside the server it carries the opencode-side graphify plugin, which guards agent tool use against stale or unindexed knowledge. The two halves share a theme — both are about making an external system's real constraints legible to an agent instead of papering over them.

## Constraints discovered

The Godot 4.7 `EditorInterface` documentation page is 619 lines and is the complete surface. Seventeen methods contain "scene" in their names, but only one closes a scene: `Error close_scene()`, zero parameters, which closes the *currently active* scene, discards pending changes, and returns `ERR_DOES_NOT_EXIST` when nothing is open. There is no close-by-path, close-by-index, or close-all variant. There is no `set_current_scene` or `activate_scene_tab` — nothing that makes a different open tab active. `open_scene_from_path` does not document focus-existing-tab behavior, and `reload_scene_from_path` fails if the scene is not already open. `get_open_scenes()` and `get_open_scene_roots()` list what is open, but the active-tab cursor can only move implicitly.

The page also has no Signals section at all — only Description, Properties, Methods, and their descriptions. A case-insensitive search for `signal`, `scene_closed`, `scene_tab*`, `tab_closed`, and `tab_changed` returns zero matches, and `EditorInterface` inherits plain `Object`. The practical consequence: a `cmd_close_scene` handler must activate the target tab first or be limited to closing the active scene. This is the constraint that makes the multi-tab delete bug possible, and it belongs in [[godot-editor-interface]] rather than being rediscovered per handler.

## Patterns that emerged

Bridge lifecycle failures converge rather than scatter. Import-asset end-to-end failures all surface as "addon never connected to the bridge," which points at one handshake path rather than per-test flakiness — a single place to fix, and a single place to instrument.

Guard porting followed a fidelity-over-reimplementation pattern. The `.opencode/plugins/graphify.js` plugin was rewritten to port graphify's full Claude Code `PreToolUse` guard pair from `graphify/cli.py:_run_hook_guard`, replacing a once-per-session echo. The search guard fires on executed tokens with heredoc bodies and quoted spans stripped and wrappers skipped, so `git commit -m "add flag support"` never triggers it. The read/glob guard applies only to in-project source files, exempts `graphify-out/` reads, and softens to the STALE nudge when a file is newer than `graph.json` or a `.needs_update` marker exists. Strict mode, enabled by `GRAPHIFY_HOOK_STRICT=1` with a TTL, gives the first read per session of an indexed file a forceful once-only reminder. See [[graphify-hook-guards]].

Transport is where the two frontends diverge. Because opencode cannot deny from `tool.execute.before`, Claude's `permissionDecision: deny` degrades to a strong once-per-session nudge, and session markers reuse the same `graphify-out/cache/hook_sessions/<sid>.denied` files the Claude hook writes. Nudges reach the model by prepending a shell-safe `echo '<text>' ;` to bash commands and by appending to the tool result via `tool.execute.after` for read/grep/glob, since opencode has no `PreToolUse` `additionalContext` channel. See [[opencode-plugin-transport]].

## Decisions made

Treat the editor API surface as fixed and design around it rather than patching Godot. Port guards faithfully instead of reimplementing their semantics. Degrade a deny to a nudge rather than fake a block the host cannot enforce. Keep session markers byte-compatible with the Claude hook so both frontends share state.

Two review findings hardened the argument-matching code: a guard bypass where any argument equal to `ollama` triggers it while the `--backend=ollama` form goes unrecognized, and a scene-close path that closes the active tab rather than the tab for the deleted path. Both are the same lesson — equality and substring matching on CLI arguments and on editor state is fragile, and the API constraint above is what forces the second one into existence.

## Current state

The project graph holds 30 claims, all sourced to the repository or upstream documentation, with no open contradictions. The Godot API constraints and the guard-port semantics are the load-bearing entries; the rest are implementation detail hanging off them.

---

_Generated from the evidence fabric on 2026-09-21. 845 current claim(s) from 845 analyzed sources._
