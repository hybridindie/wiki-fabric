---
type: index
title: "godot-mcp: What We Learned"
review_after: 2027-03-20
---

# godot-mcp: What We Learned

## Current state

838 verified claim(s) from 839 analyzed sources.
⚠️ 1 claim(s) due for review.

## Key findings

- PR #442 (Enforce local ollama-only graphify backend) failed CI on ruff." [1]
- PR #441 (Fix debugger silent no-op (break state)) failed CI on live editor e2e." [2]
- PR #440 (Close editor tabs for deleted open scenes) failed CI on live editor e2e." [3]
- PR #442's real lint error is E501 line too long at scripts/graphify_gdscript_support.py:158." [4]
- PRs #441, #440, and #438 all failed e2e with the same test test_import_asset_e2e.py reporting \"addon never connected to the bridge\"." [5]
- PR #438's mypy failure is 'fetch failed' (transient network)." [6]
- main's latest CI run timed out in pytest (infra), while the previous run was green." [7]
- Qodo reviews have landed on all 5 PRs." [8]
- Qodo found a real guard bypass in #442: any arg == 'ollama' triggers it, and the --backend=ollama form is unrecognized." [9]
- Qodo found a missing regression test in #441 for the force_break poll-timeout path." [10]
- Qodo found a real bug in #440: EditorInterface.close_scene() closes the active tab, not the one for the deleted path, so multi-tab deletes c [11]
- The EditorInterface Methods table in the file spans lines 43–110." [12]
- The complete set of EditorInterface methods whose names contain \"scene\" is 17 methods, with no others present in the Methods table." [13]
- `Error close_scene()` is the only close method, takes zero parameters, closes the currently active scene discarding pending changes, and ret [14]
- EditorInterface provides no close-by-path, close-by-index, or close-all variant." [15]

