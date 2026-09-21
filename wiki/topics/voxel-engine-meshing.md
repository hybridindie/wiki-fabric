---
type: wiki-article
title: "Voxel Engine Meshing"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Voxel Engine Meshing

10 current claim(s) support this topic.

- Mesher has no greedy meshing; at voxel_size > 1 each exposed face becomes s×s planar sub-quads, with chunk rebuild ~35–37 ms at vs=3." [1]
- #28 mesher perf landed S1–S3 + S5 in #30, achieving 22–25 ms/chunk from ~147 and startup fill 1.3 s vs the ≤6 s target." [2]
- The user's Godot 4 GDScript voxel engine uses 1 block = 1 m, where voxel_size (1-4) subdivides each block face into voxel_size^2 sub-quads,  [3]
- Meshing cost is dominated by scanning voxels, so RLE/bitmask structures that let the mesher skip runs make interval-tree/RLE iteration ~30-5 [4]
- The aperiodic engine is a Godot 4 GDScript voxel engine at \"Lay of the Land\" resolution (1 gameplay block = 1 m, voxel_size subdividing bl [5]

---

[1] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--011 — Mesher has no greedy meshing; at voxel_size > 1 each exposed face becomes s×s pl
[2] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-001 — #28 mesher perf landed S1–S3 + S5 in #30, achieving 22–25 ms/chunk from ~147 and
[3] claim-aperiodic-chats-2026-09-11-chat-research-only-task-no-code-writing-i-need-a-surv-000 — The user's Godot 4 GDScript voxel engine uses 1 block = 1 m, where voxel_size (1
[4] claim-aperiodic-chats-2026-09-11-chat-research-only-task-no-code-writing-i-need-a-surv-005 — Meshing cost is dominated by scanning voxels, so RLE/bitmask structures that let
[5] claim-aperiodic-chats-2026-09-12-chat-research-only-task-no-code-writing-no-file-chang-000 — The aperiodic engine is a Godot 4 GDScript voxel engine at \"Lay of the Land\" r

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
