---
type: wiki-article
title: "Multi-Target Handling in Godot"
domain: [godot-systems]
review_after: 2027-01-19
---

# Multi-Target Handling in Godot

4 current claim(s) support this topic.

- Multi-target handlers report one aggregate `ok` even when individual targets do not persist." [1]
- `_batch_targets` descends into instanced children, so one aggregate `ok` never hides a lost target." [2]

## ⚠️ Due for review (2)
- `_batch_targets` uses `root.find_children(\"*\", type, true, false)`, which descends into instanced children, so every match needs its own v ⚠️⚠️[3]
- `_batch_targets` uses `root.find_children(\"*\", type, true, false)`, which descends into instanced children, so every match needs its own v ⚠️⚠️[4]

---

[1] claim-godot-mcp-git-issue-477-md-003 — Multi-target handlers report one aggregate `ok` even when individual targets do
[2] claim-godot-mcp-git-pr-503-md-008 — `_batch_targets` descends into instanced children, so one aggregate `ok` never h
[3] godot mcp git issue 477 md 006 — `_batch_targets` uses `root.find_children(\"*\", type, true, false)`, which desc ⚠️ review overdue 11d
[4] godot mcp git issue 477 md 006 — `_batch_targets` uses `root.find_children(\"*\", type, true, false)`, which desc ⚠️ review overdue 11d

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
