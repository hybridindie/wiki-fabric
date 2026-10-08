---
type: source-summary
title: Docs Site Machine Contract — Summary
description: "Faithful summary of docs-site-machine-contract.md with line locators"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T08:25:42Z" }
tags: []
source: "[[src-wiki-fabric-docs-site-machine-contract-md]]"
status: pending
created: 2026-10-08
---

# Summary

Faithful summary of docs-site-machine-contract.md.

## Key claims

- The contract surface is consumed by CI, agent harnesses, and dashboards. (locator: L9-L11)
- Lint codes are available in JSON format. (locator: L11-L14)
- Lint report codes are stable. (locator: L19-L42)
- Checks the contract enforces. (locator: L45-L47)
- The `SCOPE` check enforces that frontmatter `scope:` must match the path-implied (locator: L51-L52)
- The `REVIEW-AFTER` check flags pages with a past `review_after` date as stale. (locator: L50-L52)
- The `SYNC-CONFLICT` check blocks commit/push for unresolved team-sync conflicts. (locator: L51-L53)
- The `SOURCE-DRIFT` check detects a captured source's sha256 changed without re-i (locator: L52-L54)
- The `registry/catalog.json` file contains information about what knowledge exist (locator: L111-L115)
- The `registry/catalog.json` file is rebuilt by `wf rebuild-index` from actual fi (locator: L113-L115)
- The `registry/catalog.json` file is never hand-edited. (locator: L113-L115)
