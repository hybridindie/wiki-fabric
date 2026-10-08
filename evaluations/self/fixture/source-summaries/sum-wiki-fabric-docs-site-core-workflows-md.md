---
type: source-summary
title: Docs Site Core Workflows — Summary
description: "Faithful summary of docs-site-core-workflows.md with line locators"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:45:28Z" }
tags: []
source: "[[src-wiki-fabric-docs-site-core-workflows-md]]"
status: pending
created: 2026-10-08
---

# Summary

Faithful summary of docs-site-core-workflows.md.

## Key claims

- Ingesting a document is not fire-and-forget: everything the LLM extracts is stag (locator: L11-L14)
- A change-set is the proposed edit (a manifest of what changed plus a diff) that  (locator: L15-L16)
- A locator is the exact file-and-line pointer every claim carries, so each statem (locator: L16-L17)
- LLM configuration: any OpenAI-compatible endpoint works — full provider table, m (locator: L44-L47)
- The ingest agent classifies each claim's effect (add | support | weaken | contra (locator: L49)
- The activity-bounded window (default 6m, budget 30): on an extremely active repo (locator: L96)
- The key discipline: LLM extraction is the most expensive operation in the fabric (locator: L121-L125)
- wf query routes the question by type, scores pages deterministically, and return (locator: L167)
- wf log captures an experience event with details like problem, intervention, and (locator: L265-L267)
- wf mine promotions clusters experience events by concept overlap to create promo (locator: L281-L282)
