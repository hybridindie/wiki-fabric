---
type: claim
id: claim-wiki-fabric-docs-site-architecture-md-007
statement: "The optional integrations include graphify, judgment tier, embeddings, git history capture, corpus team sync, MCP server, and multi-harness skill packs."
description: "The optional integrations include graphify, judgment tier, embeddings, git history capture, corpus team sync, MCP server, and multi-harness "
resource: "[[src-wiki-fabric-docs-site-architecture-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:41:27Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T07:41:27Z"
status: supported
confidence: high
project: "wiki-fabric"
evidence_strength: primary
source_refs:
  - source: "[[src-wiki-fabric-docs-site-architecture-md]]"
    locator: "L86-L91"
    quote: "| Layer | Status |\n|-------|--------|\n| `wf` CLI, uv install | reference implementation |\n| Graphify (call-graph staleness, enrichment, code navigation) | optional integration — off by default |\n| Judgment tier (mining refinement, eval gates, ingest effect verification, opt-in context re-rank — Jev cloud / Laya local) | optional integration — off by default |\n| Embeddings (semantic re-rank boost, `wf query`) | optional integration — off by default |\n| Git history capture, corpus team sync | integrations |\n| MCP server (`wf-mcp`, incl. wiki-generation tools), multi-harness skill packs | reference implementation |"
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-architecture-md-007

The optional integrations include graphify, judgment tier, embeddings, git history capture, corpus team sync, MCP server, and multi-harness skill packs.
