---
type: index
title: "aperiodic: What We Learned"
review_after: 2027-03-20
---

# aperiodic — Project Retrospective

**aperiodic** is a Godot voxel-world project whose generation layer is built around aperiodic tiling. Its role in the fabric is twofold: it is the working implementation that turns the 2023 Hat and Spectre monotile results into a terrain grammar, and it is the source of the chunk-boundary and meshing rules now promoted as load-bearing patterns. It matters because the einstein problem — a single shape that tiles the plane only non-periodically — was long-standing, and was resolved in 2023 by the Hat and then the Spectre. This project is where that result meets an actual engine.

## What was built

The engine generates worlds in integer block coordinates and scales blocks into world units only at the render and physics layer [21]. Chunks are 16 blocks on a side (`CHUNK_SIZE`) [24]. `ChunkKey.from_world()` derives chunk coordinates with `floori(float(w)/CHUNK_SIZE)`, which handles negative coordinates correctly [25], and `ChunkKey.origin()` returns the chunk's minimum corner as `Vector3i(cx*16, cy*16, cz*16)` [26].

The mesher iterates `range(ChunkKey.CHUNK_SIZE)` — 16 iterations, not 15 [27]. A block at local x=15 emits its +X face at local x=16, which is exactly the next chunk's local x=0, so the mesh is watertight and there is no 16-vs-15 bug [28]. Boundary faces are culled only when the neighbor block is both solid and opaque [29], and for neighbors outside the chunk `_neighbor` queries the authoritative `world.get_block` rather than returning air [30].

On the tiling side, the project carries a hat tiling subsystem with a metatile hierarchy (H/T/P/F) and a grammar suite. The underlying mathematics: the Hat (2023) is a single connected polygonal shape that can force an aperiodic plane tiling, though its tilings may use reflected copies of the shape [5]; the Spectre (2023) is a single chiral shape that can force aperiodicity even when reflections are allowed, using rotations and translations of one handedness with no mirrored tile required [6]. David Smith found the Hat, then worked with Joseph Samuel Myers, Craig Kaplan, and Chaim Goodman-Strauss to prove the result [7], resolving the long-standing einstein problem [8].

## Constraints discovered

The hard limits are mathematical and platform-level.

Mathematically: an aperiodic tiling covers space but has no nonzero translation that leaves the whole tiling unchanged [2]; local configurations recur, but the entire infinite arrangement cannot be translated by some fixed vector and line up with itself [9]. Penrose tiles require multiple tile types to force non-periodicity [4]; an aperiodic monotile forces non-repetition by its geometry alone [3]. Hat/Spectre tilings have recursive large-scale organization — recognizable assemblies occur as larger-scale structures, which in turn assemble into still larger ones [10] — and Spectre tilings are uniquely hierarchical, with the mathematical construction closely connected to substitution/de-substitution systems [12]. Critically, the Hat and Spectre are 2D Euclidean-plane monotiles and do not directly give a single 3D voxel that aperiodically fills all of R³ [11]. That is the boundary the engine has to respect: the tiling grammar is a 2D generator, not a 3D one.

Platform-level: a missing member in `core/world_seed.gd` cascaded into parse failures through WorldSeed, WorldState, WorldForgeWorld3D, `world_preview_3d.gd`, and the inspector plugin's `new_inspector_preview()` call [15]. Godot reported the failure at the call sites — `world_preview_3d.gd:102` could not resolve the external class member `world_seed` [13], and `inspector_plugin.gd:14` made an invalid call to a nonexistent function [14] — not at the definition.

## Patterns that emerged

The promoted patterns are [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]]. The meshing rules above are the concrete instance of the general rule documented in [[voxel-engine-meshing]].

The debugging pattern that worked: trace the cascade to the definition, not the call site. Restoring `DEFAULT_SEED: int = 12345` in `core/world_seed.gd` [16] and `rand01(salt, octave) -> float` — the deterministic [0,1) hash used by tree and ruin placement in both generators, seed-derived for reproducibility [17] — cleared every downstream error at once.

## Decisions made

Voxel size is designed as a world-space scale, not a generation parameter: generation stays in integer block coordinates, and the render/physics layer scales blocks into world units [21]. It belongs on `WorldProfile` so it is inspector-editable, preset-saveable, and drives preview rebuilds via `params_key()` [22]. It should be exposed from `WorldState` as a single authoritative accessor, with world↔block coordinate helpers added for the render layer [23].

## Current state

All headless tests pass: world_forge 13, vertical rules 11, terrain tools 6, mesher 7, presets 13, preview 9, grammar 11, hat tiling 16 [18]. All three previously-broken scripts now instantiate [19], and an editor launch produces zero parse errors [20].

Still open, from the session takeaways: mining is instantaneous (a single `set_block(AIR)` on keypress); the H/T/P/F metatile hierarchy is never drawn, so the levels that are supposed to be visible are not; the preview does not honor the profile — it has its own `tile_scale` (default 20 vs profile 14) and re-centers; the comment "Node space is block units" is the wrong invariant because children are scaled meshes; there is no undo/edit history and no regression tests for the two bugs above; and the rule "never create previews — always update" is not yet enforced across `_add_preview_at` and `_move_preview_to`. Progressive rebuild (mesh a few chunks per editor frame instead of freezing) and a per

---

_Generated from the evidence fabric on 2026-09-21. 251 current claim(s) from 251 analyzed sources._
