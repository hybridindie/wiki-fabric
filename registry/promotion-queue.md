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
| (empty) | | | |

## Review checklist (per dossier)

1. Independence: do the supporting experience-events share a lineage? (No → OK.)
2. Evidence: are claims in `source_refs` actually entailed by cited locators?
3. Applicability: are `includes`/`excludes` conditions correct and non-vacuous?
4. Counterexamples: listed and acknowledged?
5. Tradeoff: cost/benefit stated?
6. Asset changes: which `global/` entries does promotion create/update?
7. Owner: configured owner from `fabric.yaml`. Promote only when all pass.