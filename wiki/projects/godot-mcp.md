---
type: index
title: "godot-mcp: What We Learned"
review_after: 2027-03-20
---

# godot-mcp: What We Learned

## Current state

845 verified claim(s) from 845 analyzed sources.

## Key findings

- There are 5 open PRs in the repository." [1]
- PR #439 (Refuse zero-polygon navigation bakes) has all green CI and no review yet." [2]
- PR #442 (Enforce local ollama-only graphify backend) has a CI failure in ruff." [3]
- PR #438 (Fix Object property coercion + null-write) has CI failures in e2e and mypy." [4]
- No Qodo reviews had landed on any PR at the time of the initial triage." [5]
- The e2e failures on PRs #441, #440, and #438 all involve test_import_asset_e2e.py with the error 'addon never connected to the bridge'." [6]
- Main's latest CI run is also failing." [7]
- PR #438's mypy failure is a transient 'fetch failed' infrastructure issue, not a real type error." [8]
- PR #442 has a real lint error: E501 line too long at scripts/graphify_gdscript_support.py:158." [9]
- Qodo reviews have landed on all 5 PRs." [10]
- Qodo found a real guard bypass in PR #442 where any argument equal to 'ollama' triggers it and the --backend=ollama form is unrecognized." [11]
- Qodo found a real bug in PR #440 where EditorInterface.close_scene() closes the active tab, not the one for the deleted path, so multi-tab d [12]
- The source file is 619 lines long and constitutes the complete Godot 4.7 EditorInterface documentation page." [13]
- EditorInterface in Godot 4.7 exposes exactly 17 methods whose names contain \"scene\", spanning close_scene() through stop_playing_scene()." [14]
- The only scene-closing method is Error close_scene(), which takes zero parameters, closes the currently active scene discarding pending chan [15]

