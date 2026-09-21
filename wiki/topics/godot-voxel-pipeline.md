---
type: wiki-article
title: "Godot Voxel Pipeline"
domain: [agent-systems]
review_after: 2027-01-19
---

# Godot Voxel Pipeline

6 current claim(s) support this topic.

- godot_voxel uses two separate pipelines (blocky vs Transvoxel smooth) over one VoxelBuffer, and supports non-cubic shapes via VoxelBlockyMod [1]
- Zylann's godot_voxel runs two parallel pipelines over the same VoxelBuffer storage: blocky (VoxelTerrain + VoxelMesherBlocky + VoxelBlockyLi [2]
- godot_voxel's VoxelBlockyModel carries a collision_aabbs: AABB[] list of bounding boxes relative to the model used for box-based collision v [3]

---

[1] claim-aperiodic-chats-2026-09-12-chat-let-s-start-looking-at-other-voxel-shapes-to-sup-007 — godot_voxel uses two separate pipelines (blocky vs Transvoxel smooth) over one V
[2] claim-aperiodic-chats-2026-09-12-chat-research-task-web-research-no-code-changes-topic-005 — Zylann's godot_voxel runs two parallel pipelines over the same VoxelBuffer stora
[3] claim-aperiodic-chats-2026-09-12-chat-research-task-web-research-no-code-changes-topic-006 — godot_voxel's VoxelBlockyModel carries a collision_aabbs: AABB[] list of boundin

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
