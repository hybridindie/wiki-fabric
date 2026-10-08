---
type: claim
id: claim-wiki-fabric-docs-site-machine-contract-md-007
statement: "The `SOURCE-DRIFT` check detects a captured source's sha256 changed without re-ingest."
description: "The `SOURCE-DRIFT` check detects a captured source's sha256 changed without re-ingest."
resource: "[[src-wiki-fabric-docs-site-machine-contract-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T08:25:42Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T08:25:42Z"
status: supported
confidence: high
project: "wiki-fabric"
evidence_strength: primary
source_refs:
  - source: "[[src-wiki-fabric-docs-site-machine-contract-md]]"
    locator: "L52-L54"
    quote: "| `SOURCE-DRIFT` | a captured source's sha256 changed without re-ingest (ingest's drift trigger already stamped the old-revision claims contested+stale_after before this reports) |"
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-machine-contract-md-007

The `SOURCE-DRIFT` check detects a captured source's sha256 changed without re-ingest.
