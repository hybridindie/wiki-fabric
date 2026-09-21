---
type: wiki-article
title: "Chunk Management in Godot Project"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Chunk Management in Godot Project

18 current claim(s) support this topic.

- The chunk size constant CHUNK_SIZE is 16." [1]
- The chunk manager's spawn budget per frame is 2." [2]
- ChunkKey defines fixed 16-cubed chunks with CHUNK_SIZE=16, CHUNK_SIZE_2=256, and CHUNK_SIZE_3=4096." [3]
- Chunk streaming uses a spawn budget of 2 chunks per frame, scaled down by maxi(1, roundi(2/vs²)) at higher resolution." [4]
- spawn_budget_per_frame = 2 with view_radius_chunks = 8 ≈ 632 chunks ≈ 316 frames of visible fill-in." [5]
- The demo runs at voxel_size = 3 with view_radius_chunks = 8." [6]
- Live walk probe at demo config (vs=3, radius 8): residency 36 → 459 chunks while walking, zero stall frames." [7]
- Streaming frames are still 20–33 ms at demo config vs=3, and the 60 fps goal is the active front." [8]
- The engine currently runs streaming frames at 20-33 ms/frame on an M4 Max and needs 60+ fps (16.6 ms)." [9]

---

[1] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-000 — The chunk size constant CHUNK_SIZE is 16."
[2] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-009 — The chunk manager's spawn budget per frame is 2."
[3] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--002 — ChunkKey defines fixed 16-cubed chunks with CHUNK_SIZE=16, CHUNK_SIZE_2=256, and
[4] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--007 — Chunk streaming uses a spawn budget of 2 chunks per frame, scaled down by maxi(1
[5] claim-aperiodic-chats-2026-09-07-chat-the-chuncks-are-rendering-seperated-from-one-ano-008 — spawn_budget_per_frame = 2 with view_radius_chunks = 8 ≈ 632 chunks ≈ 316 frames
[6] claim-aperiodic-chats-2026-09-11-chat-when-previewing-the-game-no-additional-chunks-ar-002 — The demo runs at voxel_size = 3 with view_radius_chunks = 8."
[7] claim-aperiodic-chats-2026-09-11-chat-when-previewing-the-game-no-additional-chunks-ar-009 — Live walk probe at demo config (vs=3, radius 8): residency 36 → 459 chunks while
[8] claim-aperiodic-chats-2026-09-12-chat-let-s-look-at-the-open-issues-and-prioritize-the-003 — Streaming frames are still 20–33 ms at demo config vs=3, and the 60 fps goal is
[9] claim-aperiodic-chats-2026-09-12-chat-research-only-task-no-code-writing-no-file-chang-001 — The engine currently runs streaming frames at 20-33 ms/frame on an M4 Max and ne

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
