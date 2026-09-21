---
type: wiki-article
title: "Node Persistence in Godot"
domain: [godot-systems]
review_after: 2027-01-19
---

# Node Persistence in Godot

46 current claim(s) support this topic.

- Creating a node under a non-editable instanced child loses the new node on save, verified live as the T1 case." [1]
- `delete_node`, `move_node`, and `duplicate_node` under instance subtrees are extrapolated rather than probed, and each needs a live probe be [2]
- Verified rules, the 13-case save table, and line refs are recorded in the untracked file `458-persistence-truth-handoff.md`." [3]
- For cmd_create_tile the preview says \"This TileSet is embedded\" while the real run says \"This TileSetAtlasSource is embedded\", because t [4]
- For cmd_create_animation {'name': 'walk'} the preview says persisted: True while the real run reports persisted: false, reason: embedded_in_ [5]
- The AnimationLibrary the animation lands in is embedded in tmp_e2e_persist2_inner.tscn, but animation_probe(node_path, name) only names the  [6]
- The probe runs before the mutation while the handler's _with_persistence runs after it." [7]
- It is proposed that cmd_create_animation should probe like the resource-slot probes (a library-aware probe, as #476 did for tile_set/tree_ro [8]
- It is proposed that the real run should stamp the verdict from the same target path the probe used (pre-rename), or the probe should pass th [9]
- It is proposed that the embedded-resource reason's class word should be derived from the same object on both paths." [10]
- The reporter concludes the test is doing its job by catching real drift and that the fix is to align probe and handler on the same target te [11]
- The addon reports persisted: false with reason instanced_child_not_editable and a hint." [12]
- Moving a project file breaks every scene or script that references the old path." [13]
- Godot 4.4+ exposes the editor's rename machinery via EditorInterface/EditorFileSystem and ResourceUID." [14]
- All 13 create-family handlers now probe the parent before the mutation and stamp persisted/reason/hint." [15]
- batch_set_property and apply_node_edits now carry a persistence[] array with one {node_path, persisted, reason?, hint?} per applied/edited t [16]
- Live e2e test shows saved file agrees with every verdict, with test_persistence_e2e green on Godot 4.7.2." [17]
- The set_editable_children tool refuses local nodes, which would otherwise be a silent no-op." [18]
- PR #505 was merged on 2026-09-18." [19]
- `cmd_get_recording` maps to `recording_pending`." [20]
- `cmd_get_property_samples` maps to `capture_pending`." [21]
- `cmd_get_performance_monitors` maps to `probe_pending`." [22]
- The live e2e test `tests/integration/test_game_output_e2e.py` launches a real headless editor and plays a scratch scene whose script prints  [23]

---

[1] claim-godot-mcp-git-issue-477-md-001 — Creating a node under a non-editable instanced child loses the new node on save,
[2] claim-godot-mcp-git-issue-477-md-004 — `delete_node`, `move_node`, and `duplicate_node` under instance subtrees are ext
[3] claim-godot-mcp-git-issue-477-md-010 — Verified rules, the 13-case save table, and line refs are recorded in the untrac
[4] claim-godot-mcp-git-issue-481-md-002 — For cmd_create_tile the preview says \"This TileSet is embedded\" while the real
[5] claim-godot-mcp-git-issue-481-md-003 — For cmd_create_animation {'name': 'walk'} the preview says persisted: True while
[6] claim-godot-mcp-git-issue-481-md-004 — The AnimationLibrary the animation lands in is embedded in tmp_e2e_persist2_inne
[7] claim-godot-mcp-git-issue-481-md-006 — The probe runs before the mutation while the handler's _with_persistence runs af
[8] claim-godot-mcp-git-issue-481-md-007 — It is proposed that cmd_create_animation should probe like the resource-slot pro
[9] claim-godot-mcp-git-issue-481-md-008 — It is proposed that the real run should stamp the verdict from the same target p
[10] claim-godot-mcp-git-issue-481-md-009 — It is proposed that the embedded-resource reason's class word should be derived
[11] claim-godot-mcp-git-issue-481-md-010 — The reporter concludes the test is doing its job by catching real drift and that
[12] claim-godot-mcp-git-issue-487-md-002 — The addon reports persisted: false with reason instanced_child_not_editable and
[13] claim-godot-mcp-git-issue-532-md-001 — Moving a project file breaks every scene or script that references the old path.
[14] claim-godot-mcp-git-issue-532-md-004 — Godot 4.4+ exposes the editor's rename machinery via EditorInterface/EditorFileS
[15] claim-godot-mcp-git-pr-503-md-003 — All 13 create-family handlers now probe the parent before the mutation and stamp
[16] claim-godot-mcp-git-pr-503-md-006 — batch_set_property and apply_node_edits now carry a persistence[] array with one
[17] claim-godot-mcp-git-pr-503-md-009 — Live e2e test shows saved file agrees with every verdict, with test_persistence_
[18] claim-godot-mcp-git-pr-504-md-003 — The set_editable_children tool refuses local nodes, which would otherwise be a s
[19] claim-godot-mcp-git-pr-505-md-000 — PR #505 was merged on 2026-09-18."
[20] claim-godot-mcp-git-pr-505-md-003 — `cmd_get_recording` maps to `recording_pending`."
[21] claim-godot-mcp-git-pr-505-md-004 — `cmd_get_property_samples` maps to `capture_pending`."
[22] claim-godot-mcp-git-pr-505-md-006 — `cmd_get_performance_monitors` maps to `probe_pending`."
[23] claim-godot-mcp-git-pr-547-md-006 — The live e2e test `tests/integration/test_game_output_e2e.py` launches a real he

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
