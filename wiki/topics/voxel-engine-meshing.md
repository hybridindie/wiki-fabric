---
type: wiki-article
title: "Voxel Engine Meshing"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Voxel Engine Meshing

10 current claim(s) support this topic.

- The mesher has no greedy meshing; at voxel_size > 1 each exposed face becomes s×s planar sub-quads, with chunk rebuilds reported at ~35–37 m [1]
- #28 mesher perf: S1–S3 + S5 landed in #30, achieving 22–25 ms/chunk from ~147 ms and startup fill 1.3 s against a ≤6 s target." [2]
- The user's Godot 4 GDScript voxel engine uses 1 block = 1 m, with voxel_size (1-4) subdividing each block face into voxel_size^2 sub-quads,  [3]
- Greedy meshing over the sub-voxel grid uses a merge constraint of same texture plus same 4 corner AO values, collapsing flat faces from vs^2 [4]
- The engine is a Godot 4 GDScript voxel engine at \"Lay of the Land\" resolution (1 gameplay block = 1 m, voxel_size subdivides block faces 1 [5]

---

[1] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--011 — The mesher has no greedy meshing; at voxel_size > 1 each exposed face becomes s×
[2] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-001 — #28 mesher perf: S1–S3 + S5 landed in #30, achieving 22–25 ms/chunk from ~147 ms
[3] claim-aperiodic-chats-2026-09-11-chat-research-only-task-no-code-writing-i-need-a-surv-000 — The user's Godot 4 GDScript voxel engine uses 1 block = 1 m, with voxel_size (1-
[4] claim-aperiodic-chats-2026-09-11-chat-research-only-task-no-code-writing-i-need-a-surv-005 — Greedy meshing over the sub-voxel grid uses a merge constraint of same texture p
[5] claim-aperiodic-chats-2026-09-12-chat-research-only-task-no-code-writing-no-file-chang-000 — The engine is a Godot 4 GDScript voxel engine at \"Lay of the Land\" resolution

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
