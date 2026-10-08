---
type: claim
id: claim-wiki-fabric-docs-site-machine-contract-md-004
statement: "The `SCOPE` check enforces that frontmatter `scope:` must match the path-implied scope."
description: "The `SCOPE` check enforces that frontmatter `scope:` must match the path-implied scope."
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
    locator: "L51-L52"
    quote: "| Check | Meaning |\n|-------|---------|\n| `SCOPE` | frontmatter `scope:` must match the path-implied scope (`global/` `domains/` `projects/`) — precedence comes from scope, so scope lies are errors |"
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-machine-contract-md-004

The `SCOPE` check enforces that frontmatter `scope:` must match the path-implied scope.
