---
type: claim
id: claim-example-cache-invalidation
statement: "Cache entries must be invalidated on any write to prevent stale reads."
status: supported
confidence: high
evidence_strength: primary
source_refs:
  - source: "[[src-example-design-doc]]"
    locator: "§3, p. 5"
    quote: "The cache must be invalidated after any mutation to prevent reads returning stale data."
    supports: true
last_verified: 2026-01-01
relations: []
---

# claim-example-cache-invalidation

Example claim showing the expected format: atomic statement, locator pointing to the exact location, verbatim quote from the source.