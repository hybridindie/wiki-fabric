---
type: registry
title: Story — OKF conformance baseline (lint --okf)
id: story-okf-01-conformance-baseline
status: proposed
epic: "[[epic-okf-alignment]]"
priority: high
estimate: S
github_issue: https://github.com/hybridindie/wiki-fabric/issues/2
created: 2026-09-16
updated: 2026-09-16
---

# Story: OKF conformance baseline

## As a
fabric maintainer publishing wiki-fabric publicly

## I want
`python3 scripts/lint.py . --okf` to report conformance against OKF v0.2 §11

## So that
I know the fabric is a conformant OKF bundle today, can gate CI on it, and can
cross-check with `okflint` without fabric-specific noise.

## Acceptance criteria

- [ ] `lint.py --okf` implements OKF v0.2 §11 conformance exactly:
  1. every non-reserved `.md` has parseable YAML frontmatter
  2. every frontmatter has non-empty `type`
  3. `index.md`/`log.md` (when present) follow §8/§9 shape (ISO-8601 date headings in log)
- [ ] `--okf` mode suppresses wiki-fabric-specific errors (orphans, hash checks, maturity gates) — those are our profile, not OKF core
- [ ] `lint.py --format json` gains an `okf_conformance: {conformant: bool, violations: [...]}` block
- [ ] CI runs both modes: `lint.py .` (full profile) and `lint.py . --okf` (interop gate)
- [ ] A fixture bundle under `evaluations/okf/` exercises each conformance rule (incl. one deliberate violation per rule, tested to fail)
- [ ] Run `okflint` (external, `uv tool install okflint`) against the fabric as a second opinion; record divergences in the story page

## Notes

- OKF conformance is deliberately permissive; our lint is stricter. `--okf` is the *floor*, the default mode is the *ceiling*.
- `okf_version: "0.2"` in root `index.md` frontmatter (the only frontmatter allowed in an index) is added here.

## Log

- 2026-09-16 — **Creation**: story opened.