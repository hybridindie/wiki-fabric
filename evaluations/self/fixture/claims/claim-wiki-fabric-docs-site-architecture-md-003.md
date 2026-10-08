---
type: claim
id: claim-wiki-fabric-docs-site-architecture-md-003
statement: "The pipeline includes stages for capturing, ingesting, synthesizing, and exporting knowledge."
description: "The pipeline includes stages for capturing, ingesting, synthesizing, and exporting knowledge."
resource: "[[src-wiki-fabric-docs-site-architecture-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:41:27Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T07:41:27Z"
status: supported
confidence: medium
project: "wiki-fabric"
evidence_strength: secondary
source_refs:
  - source: "[[src-wiki-fabric-docs-site-architecture-md]]"
    locator: "L35-L68"
    quote: "```mermaid\ngraph TB subgraph \"Source Repos\" R1[\"project-a\"] R2[\"project-b\"] R3[\"project-c\"] end subgraph \"Fabric\" RAW[\"evidence/raw/<br/>(immutable captures)\"] CLAIMS[\"evidence/claims/<br/>(verified claims)\"] CONCEPTS[\"concepts/<br/>(synthesized concepts)\"] PATTERNS[\"patterns/<br/>(cross-project patterns)\"] SKILLS[\"skills/<br/>(promoted skills)\"] EVENTS[\"projects/*/experience-events/\"] ENTITIES[\"global/entities/<br/>(AST-indexed symbols)\"] GRAPHS[\"global/graphs/<br/>(graphify call graph)\"] REGISTRY[\"registry/<br/>(catalog.json, promotion queue, log)\"] end R1 & R2 & R3 -->|capture| RAW RAW -->|\"ingest.py → extract_backends (LLM)\"| CLAIMS CLAIMS -->|\"synthesize.py (LLM; contradiction-aware, #186)\"| CONCEPTS CLAIMS -->|\"mine-promotions.py\"| PATTERNS PATTERNS -->|\"promote.py\"| SKILLS INBOX[\"patterns/_inbox/<br/>(gated candidates)\"] -->|\"promote-patterns (--apply / --auto judged tier, #190)\"| PATTERNS R1 & R2 & R3 -->|\"build-entity-index.py (AST)\"| ENTITIES R1 -->|\"graphify-bridge.py (AST, 0 tokens)\"| GRAPHS EVENTS -->|\"mine-promotions.py\"| PATTERNS CLAIMS -->|\"wiki_generate.py (writer/bookkeeper, 0 tokens)\"| WIKI[\"wiki/<br/>(staged pages → change-set flow)\"], CLAIMS -->|\"export-wiki.py (signature-gated: delta refresh, #187)\"| VAULTW[\"vault wiki/<br/>(the human layer)\"], WIKI -->|\"publish-wiki.py\"| SITE[\"static site<br/>(Quartz, graph view)\"]\n```"
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-architecture-md-003

The pipeline includes stages for capturing, ingesting, synthesizing, and exporting knowledge.
