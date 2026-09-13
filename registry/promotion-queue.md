---
type: registry
title: Promotion Queue
updated: 2026-09-13
---

# Promotion Queue

Candidates awaiting human promotion. **No auto-promotion** — only the user sets
`status: recommended`/`standard` on pattern pages.

| Pattern | Maturity | Evidence lineage | Dossier |
|---|---|---|---|
| [[pattern-single-writer-with-parity-check]] | 2 (recommended) | 2 independent projects | [[promotion-single-writer-with-parity-check]] |
| [[pattern-consolidate-validation]] | 2 (candidate) | 2 independent projects (alpaca-agents, nomokailist) | [[promotion-consolidate-validation]] |
| [[anti-pattern-unverified-parallel-writes]] | 2 (recommended) | same 2 projects | (above) |
| [[anti-pattern-scattered-validation]] | 2 (candidate) | same 2 projects | (above) |

## Review checklist (per dossier)

1. Independence: do the supporting experience-events share a lineage? (No → OK.)
2. Evidence: are claims in `source_refs` actually entailed by cited locators?
3. Applicability: are `includes`/`excludes` conditions correct and non-vacuous?
4. Counterexamples: listed and acknowledged?
5. Tradeoff: cost/benefit stated?
6. Asset changes: which `global/` entries does promotion create/update?
7. Owner: configured owner from `fabric.yaml`. Promote only when all pass.