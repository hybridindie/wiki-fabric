---
type: log
title: Log
created: 2026-09-13
updated: 2026-09-13
---

# Log

Append-only timeline. One `## [YYYY-MM-DD] <op> | <subject>` entry per operation
(`ingest`, `refresh`, `promote`, `schema-change`).
## [2026-09-13] ingest | test-g-sample-md

- Ingested sample.md (sha256 9e389fa6f9c1...)
- Extracted 0 claims
- Change-set: evidence/traces/change-sets/2026-09-13-test-g-sample-md

## [2026-09-13] eval-behavior | utility 100% (4/4)

- be1-avoid-anti-pattern: PASS
- be2-project-over-global: PASS
- be3-stale-demoted: PASS
- be4-escalate-gap: PASS
