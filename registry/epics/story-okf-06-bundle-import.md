---
type: registry
title: Story — wf okf import (external OKF bundle → external source)
id: story-okf-06-bundle-import
status: proposed
epic: "[[epic-okf-alignment]]"
priority: low
estimate: M
depends_on: "[[story-okf-05-bundle-export]]"
github_issue: https://github.com/hybridindie/wiki-fabric/issues/7
created: 2026-09-16
updated: 2026-09-16
---

# Story: `wf okf import` — consume external OKF bundles as evidence

## As a
the fabric, ingesting knowledge produced elsewhere (another team's bundle, a
public dataset catalog, an OpenWiki wiki)

## I want
`wf okf import <bundle-path> --as <namespace>` to ingest a conformant OKF
bundle as an *external source* — captured like any upstream repo, never
inherited as fabric-canonical content

## So that
cross-organization knowledge flows in through the same evidence-first pipeline:
external claims stay external until captured, hash-anchored, and (optionally)
re-extracted by our compiler pipeline.

## Acceptance criteria

- [ ] `scripts/okf_import.py` + `wf okf import <bundle> [--scope <name>] [--extract-claims]`
- [ ] Trust tier of the upstream bundle recorded but **not inherited** (pattern from Roteiro): imported concepts land under `evidence/raw/<scope>-okf/` as immutable captures with a `source` record each (`kind: okf-bundle`, `resource` = original path/URL, sha256)
- [ ] Import runs the okf-guard-style content screen before writing (prompt-injection/hidden-content scan of concept bodies; quarantine verdicts go to `evidence/_inbox/` for human review, never straight into claims)
- [ ] Trust tiers from `verified`/`generated` frontmatter recorded on the source record (`imported_trust_tier`) and surfaced in `context.py`/`query.py` results as *lower-precedence* evidence (external, machine-confirmed unless human-verified)
- [ ] Claim extraction optional: `--extract-claims` runs the normal compiler path (locators point into the imported concept files under raw/)
- [ ] Unknown types tolerated per OKF §11 (treated as generic concepts, cataloged, not rejected)
- [ ] Provenance: imported pages carry `generated.by` from the *upstream* actor convention (`<producer>/<version>`, `human:<id>`, `process:<id>` — all three accepted)
- [ ] `registry/log.md` records the import (bundle path, okf_version, concept count, trust tier distribution)

## Notes

- Import is the exchange half of OKF's value proposition: bundles flow *in* as
  evidence, never as canonical fabric pages. Promotion of imported findings still
  goes through the human-gated promotion pipeline — OKF trust tiers inform, they
  never grant authority (§5.3 "advisory signals, not access control").

## Log

- 2026-09-16 — **Creation**: story opened.