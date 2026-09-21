---
type: wiki-article
title: "MkDocs Material Installation Issue"
domain: [godot-systems]
review_after: 2027-01-19
---

# MkDocs Material Installation Issue

6 current claim(s) support this topic.

- The docs workflow failed at the 'Install docs toolchain' step because `uv tool install \"mkdocs-material>=9.5,<9.8\"` errors with 'No execut [1]
- The fix was verified locally with the exact workflow command `uv tool install --with mkdocs-material --with mkdocs-exclude mkdocs` followed  [2]
- The change altered `uv tool install` to use `mkdocs` as the primary tool instead of `mkdocs-material`." [3]

---

[1] claim-godot-mcp-git-pr-512-md-001 — The docs workflow failed at the 'Install docs toolchain' step because `uv tool i
[2] claim-godot-mcp-git-pr-512-md-003 — The fix was verified locally with the exact workflow command `uv tool install --
[3] claim-godot-mcp-git-pr-512-md-006 — The change altered `uv tool install` to use `mkdocs` as the primary tool instead

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
