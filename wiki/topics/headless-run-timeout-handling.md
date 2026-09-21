---
type: wiki-article
title: "Headless Run Timeout Handling"
domain: [godot-systems]
review_after: 2027-01-19
---

# Headless Run Timeout Handling

12 current claim(s) support this topic.

- Issue #489 is a bug report titled \"[Bug] AnimationPlayer path resolution fails for instanced scenes\"." [1]
- Issue #490 is a bug report titled \"[Bug] Headless run timeout produces false NON-ZERO EXIT finding\" and is in CLOSED state." [2]
- On timeout the tool outputs \"RUN TIMED OUT: The game did not exit within the timeout.\" and \"NON-ZERO EXIT: headless run exited with code  [3]
- In mcp_server/debug_workflow.py:140-143, on timeout exit_code is None, and None != 0 is True, so every timeout unconditionally emits a NON-Z [4]
- The proposed fix guards the exit code check with `if run_result.exit_code is not None and run_result.exit_code != 0`." [5]
- The proposed fix includes freeing the textures in _exit_tree." [6]

---

[1] claim-godot-mcp-git-issue-489-md-000 — Issue #489 is a bug report titled \"[Bug] AnimationPlayer path resolution fails
[2] claim-godot-mcp-git-issue-490-md-000 — Issue #490 is a bug report titled \"[Bug] Headless run timeout produces false NO
[3] claim-godot-mcp-git-issue-490-md-003 — On timeout the tool outputs \"RUN TIMED OUT: The game did not exit within the ti
[4] claim-godot-mcp-git-issue-490-md-005 — In mcp_server/debug_workflow.py:140-143, on timeout exit_code is None, and None
[5] claim-godot-mcp-git-issue-490-md-007 — The proposed fix guards the exit code check with `if run_result.exit_code is not
[6] claim-godot-mcp-git-issue-539-md-008 — The proposed fix includes freeing the textures in _exit_tree."

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
