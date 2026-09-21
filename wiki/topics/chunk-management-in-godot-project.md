---
type: wiki-article
title: "Chunk Management in Godot Project"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Chunk Management in Godot Project

18 current claim(s) support this topic.

- The chunk size constant CHUNK_SIZE is 16 blocks." [1]
- ChunkManager.spawn_budget_per_frame is 2, so with view_radius_chunks=8 the ~632-chunk wanted set takes ~316 frames (~5 s) to fill, nearest-f [2]
- ChunkData.blocks is a PackedInt32Array always resized to 4096 and filled with AIR, indexed as x + y*16 + z*256, with no sparse storage or pa [3]
- Dirty rebuilds always rebuild the containing chunk plus neighbors when the edit is within 1 block of a border, are budgeted at maxi(1, round [4]
- WorldForgeWorld3D._process only refreshes the HUD label; only headless tests call update_around." [5]
- Collision reads the pure world function (WorldState.get_block → edit overlay → generator baseline), so solidity exists even where chunks are [6]
- A live walk probe at demo config (vs=3, radius 8) showed residency growing from 36 to 459 chunks while walking, with zero stall frames." [7]
- #62 (move mesh builds to workers) is the keystone because #61's tier-2 dispatches through it and #64 depends on the worker-build issue." [8]
- The engine currently spends 20-33 ms/frame on streaming frames on an M4 Max against a 60+ fps (16.6 ms) target, with remaining costs being p [9]

---

[1] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-000 — The chunk size constant CHUNK_SIZE is 16 blocks."
[2] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-009 — ChunkManager.spawn_budget_per_frame is 2, so with view_radius_chunks=8 the ~632-
[3] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--002 — ChunkData.blocks is a PackedInt32Array always resized to 4096 and filled with AI
[4] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--007 — Dirty rebuilds always rebuild the containing chunk plus neighbors when the edit
[5] claim-aperiodic-chats-2026-09-07-chat-the-chuncks-are-rendering-seperated-from-one-ano-008 — WorldForgeWorld3D._process only refreshes the HUD label; only headless tests cal
[6] claim-aperiodic-chats-2026-09-11-chat-when-previewing-the-game-no-additional-chunks-ar-002 — Collision reads the pure world function (WorldState.get_block → edit overlay → g
[7] claim-aperiodic-chats-2026-09-11-chat-when-previewing-the-game-no-additional-chunks-ar-009 — A live walk probe at demo config (vs=3, radius 8) showed residency growing from
[8] claim-aperiodic-chats-2026-09-12-chat-let-s-look-at-the-open-issues-and-prioritize-the-003 — #62 (move mesh builds to workers) is the keystone because #61's tier-2 dispatche
[9] claim-aperiodic-chats-2026-09-12-chat-research-only-task-no-code-writing-no-file-chang-001 — The engine currently spends 20-33 ms/frame on streaming frames on an M4 Max agai

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
