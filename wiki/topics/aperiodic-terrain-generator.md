---
type: wiki-article
title: "Aperiodic Terrain Generator"
domain: [agent-systems]
review_after: 2027-01-19
---

The aperiodic terrain generator is the subsystem that translates the output of an aperiodic tiling grammar into terrain: elevation, cliffs, and vegetation. It matters because the coupling between the grammar and the terrain is narrow. Only a small fraction of the signals the grammar produces actually reach the terrain, and at least one of those signals is collapsed before use. The result is a world whose large-scale structure is driven by the tiling, but whose fine-grained aperiodic detail is largely invisible — both to the terrain and to anyone trying to debug it.

## Grammar signals consumed

The terrain generator consumes exactly 3.5 of the grammar signals [1][5]. The mapping is:

- `boundary_dist` drives ridge lift and stone cliffs.
- `region_id` applies a uniform elevation bias.
- `label == "H1"` controls tree density.

The fractional count comes from the label channel: it is consumed only through a single equality predicate rather than as a full value, while `boundary_dist` and `region_id` are used as complete signals [1][5]. Everything else the grammar emits — `tile_id`, `path`, `junction_dist`, `orientation` — has no terrain-side consumer.

## The Hat provider collapses boundary_dist

In the Hat provider, `boundary_dist` is literally assigned `edist` [2][6]. This collapses the leaf-vs-metatile distinction: whatever distance the provider computes is passed through unchanged, so downstream terrain code cannot tell whether the nearest boundary belongs to a leaf tile or a metatile. Since `boundary_dist` is the input to both ridge lift and stone cliffs [1][5], that lost distinction propagates directly into the terrain geometry.

## Observability gap in the debug overlay

The runtime debug overlay shows fps, chunks, mem, and pos — and nothing about the grammar [3][7]. Specifically, it exposes no `tile_id`, `label`, `path`, `region_id`, `boundary_dist`, `junction_dist`, or `orientation` [3][7]. Combined with the narrow signal consumption described above, this means there is no runtime view of which grammar values are reaching the terrain generator or how they are being interpreted. Verifying the grammar-to-terrain mapping requires reading code rather than inspecting a running world.

## Undifferentiated edge minimum in the Hat outline

The Hat outline has 13 edges belonging to different legal classes, but the code takes an undifferentiated minimum over all of them [4][8]. Edge class is therefore discarded at the point where the minimum is computed. Any terrain or geometry logic that depends on which class of edge is nearest cannot recover that information afterward.

## Flow

```mermaid
flowchart LR
    G[Aperiodic grammar] -->|boundary_dist| T[Terrain generator]
    G -->|region_id| T
    G -->|label == "H1"| T
    G -.->|tile_id, path, junction_dist, orientation| N[No consumer]
    T --> R[Ridge lift + stone cliffs]
    T --> E[Uniform elevation bias]
    T --> V[Tree density]
    H[Hat provider: boundary_dist = edist] --> T
    O[Debug overlay: fps / chunks / mem / pos] -.->|no grammar state| G
```

The diagram shows the three consumed signals entering the generator, the unconsumed signals dropping out, and the overlay's lack of visibility into any of it. The Hat provider feeds `boundary_dist` in already collapsed [2][6], and the edge minimum is taken without regard to class [4][8].

## Summary of constraints

Three constraints define the current design: a 3.5-signal consumption budget [1][5], a collapsed `boundary_dist` in the Hat provider [2][6], and an undifferentiated edge minimum over 13 legal edge classes [4][8]. The debug overlay provides no counterweight to any of these, since it reports only runtime performance and position [3][7].

## See also

- Aperiodic Tiling Grammar
- Hat Monotile
- Boundary Distance Field
- Region ID and Elevation Bias
- Edge Classification
- Runtime Debug Overlay

---

_Citations link to claims in evidence/claims/. Generated on 2026-09-21._
