---
type: wiki-article
title: "Node Persistence in Godot"
domain: [godot-systems]
review_after: 2027-01-19
---

# Node Persistence in Godot

48 current claim(s) support this topic.

- Creating a node under a non-editable instanced child loses the new node on save, verified live as the T1 case." [1]
- The verified rule `_persistent_target(parent)` holds because the engine visits children of a skipped node's subtree, so a create where the p [2]
- The reason tokens are `instanced_child_not_editable` and `node_not_owned`." [3]
- For cmd_create_tile, the preview says \"This TileSet is embedded\" while the real run says \"This TileSetAtlasSource is embedded\"." [4]
- The probe predicts the node's resource class while the handler reports the created resource's class." [5]
- For cmd_create_animation {'name': 'walk'}, the preview says persisted: True while the real run reports persisted: false, reason: embedded_in [6]
- animation_probe(node_path, name) only names the node, so the probe predicts the node's verdict instead of the library's." [7]
- For cmd_rename_node, the preview's hint echoes the node's pre-rename path (Relic/Cold/Extra) while the real verdict is stamped after the ren [8]
- The probe runs before the mutation while the handler's _with_persistence runs after." [9]
- cmd_create_animation should probe like the resource-slot probes (a library-aware probe, as #476 did for tile_set/tree_root slots), or the pr [10]
- The real run should stamp the verdict from the same target path the probe used (pre-rename), or the probe should pass the new name." [11]
- The embedded-resource reason's class word should be derived from the same object on both paths." [12]
- The addon reports persisted: false with reason instanced_child_not_editable and a hint." [13]
- Any move breaks every scene/script referencing the old path." [14]
- The editor's own move dialog remaps scene-embedded and script class_name references." [15]
- Parent rule for creates: a create/instance/duplicate/compose under a parent inside a non-editable instanced child applies live but is lost o [16]
- Destination rule for moves: a node moved into a non-editable instance is lost, and the verdict keys on `new_parent`." [17]
- Previews agree: `cmd_node_persistence` gains `probe_parent` (create/instance/move — parent rule) and `probe_parent_of` (duplicate — resolves [18]
- The persisted verdict for editable children keys on the parent node because the flag is packed with the parent's entry." [19]
- PR #505 is titled Readiness/reason envelope sweep across poll-based handlers." [20]
- Every poll-based handler now self-reports why it is pending with a stable `reason` token." [21]
- `poll_ready` relays the `reason` in the `TIMEOUT` expiry error." [22]
- `poll_ready` relays the last `reason` in its expiry `ToolError`, producing a structured `TIMEOUT` naming the cause rather than a bare `{read [23]
- An unanswered pull reports ready: false with reason 'output_pending'." [24]

---

[1] claim-godot-mcp-git-issue-477-md-001 — Creating a node under a non-editable instanced child loses the new node on save,
[2] claim-godot-mcp-git-issue-477-md-004 — The verified rule `_persistent_target(parent)` holds because the engine visits c
[3] claim-godot-mcp-git-issue-477-md-010 — The reason tokens are `instanced_child_not_editable` and `node_not_owned`."
[4] claim-godot-mcp-git-issue-481-md-002 — For cmd_create_tile, the preview says \"This TileSet is embedded\" while the rea
[5] claim-godot-mcp-git-issue-481-md-003 — The probe predicts the node's resource class while the handler reports the creat
[6] claim-godot-mcp-git-issue-481-md-004 — For cmd_create_animation {'name': 'walk'}, the preview says persisted: True whil
[7] claim-godot-mcp-git-issue-481-md-006 — animation_probe(node_path, name) only names the node, so the probe predicts the
[8] claim-godot-mcp-git-issue-481-md-007 — For cmd_rename_node, the preview's hint echoes the node's pre-rename path (Relic
[9] claim-godot-mcp-git-issue-481-md-008 — The probe runs before the mutation while the handler's _with_persistence runs af
[10] claim-godot-mcp-git-issue-481-md-009 — cmd_create_animation should probe like the resource-slot probes (a library-aware
[11] claim-godot-mcp-git-issue-481-md-010 — The real run should stamp the verdict from the same target path the probe used (
[12] claim-godot-mcp-git-issue-481-md-011 — The embedded-resource reason's class word should be derived from the same object
[13] claim-godot-mcp-git-issue-487-md-002 — The addon reports persisted: false with reason instanced_child_not_editable and
[14] claim-godot-mcp-git-issue-532-md-001 — Any move breaks every scene/script referencing the old path."
[15] claim-godot-mcp-git-issue-532-md-004 — The editor's own move dialog remaps scene-embedded and script class_name referen
[16] claim-godot-mcp-git-pr-503-md-003 — Parent rule for creates: a create/instance/duplicate/compose under a parent insi
[17] claim-godot-mcp-git-pr-503-md-006 — Destination rule for moves: a node moved into a non-editable instance is lost, a
[18] claim-godot-mcp-git-pr-503-md-009 — Previews agree: `cmd_node_persistence` gains `probe_parent` (create/instance/mov
[19] claim-godot-mcp-git-pr-504-md-003 — The persisted verdict for editable children keys on the parent node because the
[20] claim-godot-mcp-git-pr-505-md-000 — PR #505 is titled Readiness/reason envelope sweep across poll-based handlers."
[21] claim-godot-mcp-git-pr-505-md-003 — Every poll-based handler now self-reports why it is pending with a stable `reaso
[22] claim-godot-mcp-git-pr-505-md-004 — `poll_ready` relays the `reason` in the `TIMEOUT` expiry error."
[23] claim-godot-mcp-git-pr-505-md-006 — `poll_ready` relays the last `reason` in its expiry `ToolError`, producing a str
[24] claim-godot-mcp-git-pr-547-md-006 — An unanswered pull reports ready: false with reason 'output_pending'."

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
