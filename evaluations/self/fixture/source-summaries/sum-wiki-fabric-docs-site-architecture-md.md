---
type: source-summary
title: Docs Site Architecture — Summary
description: "Faithful summary of docs-site-architecture.md with line locators"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:41:27Z" }
tags: []
source: "[[src-wiki-fabric-docs-site-architecture-md]]"
status: pending
created: 2026-10-08
---

# Summary

Faithful summary of docs-site-architecture.md.

## Key claims

- Wiki Fabric is a fabric (one knowledge corpus per machine or team) plus a harnes (locator: L9-L12)
- Source repos connect as namespaces; knowledge flows through a one-way pipeline. (locator: L13)
- The wiki-fabric pipeline consists of source repos, fabric, and connected code re (locator: L27-L30)
- The pipeline includes stages for capturing, ingesting, synthesizing, and exporti (locator: L35-L68)
- The design rule is that every script runs standalone, but the wf CLI is the only (locator: L68-L70)
- Shared logic lives in the scripts/lib/ modules. (locator: L69-L75)
- The core format includes knowledge format, wf context, contract enforcement, beh (locator: L81-L85)
- The optional integrations include graphify, judgment tier, embeddings, git histo (locator: L86-L91)
