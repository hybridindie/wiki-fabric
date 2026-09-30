---
type: pattern
description: "Upstream freshness cannot depend on anyone's commit cadence — schedule the drift check where the corpus lives."
id: "pattern-example-freshness-cadence"
title: "Freshness needs a cadence that outlives machine habits"
scope: global
domain: [agent-systems]
status: candidate
maturity: 1
maturity_evidence:
  - "[[ee-example-freshness]]"
applicability:
  includes:
    - a shared corpus synced across >1 machine (team mode)
    - claims validated against upstream revisions that keep moving
  excludes:
    - single-machine, single-project fabrics where the hook covers every change
    - sources that are immutable by construction (frozen docs, gitignored exports)
problem: "Per-commit hooks are the freshness guarantee's layer 1, but they run on active machines only. A team whose machines all go quiet carries silently stale claims — the corpus is the source of truth, so the staleness propagates on next sync."
forces:
  - "nobody's habits should be load-bearing for correctness"
  - "CI is the only machine that never sleeps"
  - "human gates must stay: evidence capture ≠ claim rewriting"
solution: "Run a scheduled freshness cycle where the corpus lives (corpus CI): capture upstream PR/issue history with sha256-gated writes, mechanically re-verify quotes against locators, push refreshed evidence — teammates pick it up on normal sync pull. Stale/contested states are the representation; the cycle proposes, humans decide."
consequences:
  benefits:
    - "drift window drops from unbounded (all machines dormant) to the CI cadence"
    - "re-verification is mechanical (0 tokens) — safe to run nightly"
  costs:
    - "needs upstream repos readable from CI (public free; private: token)"
    - "another workflow in the corpus repo"
evidence:
  - ref: "[[ee-example-freshness]]"
    kind: direct-experience
    outcome: positive
counterexamples:
  - "Single-machine fabrics: the hook already covers every commit; a scheduled cycle adds CI churn without a staleness win."
# SLOW-REGION (SkillOpt S4): `applicability.excludes` and `counterexamples`
# are protected slow-lane content — bulk ingest/synthesis edits to them fail
# lint unless the change records a slow-update justification in `verified`.
related:
  - "[[ee-example-freshness]]"
review_after: 2026-12-29
tags: [freshness, sync, ci, agent]
created: 2026-09-30
---

# Pattern: freshness needs a cadence that outlives machine habits

**Solution in one line:** schedule the drift check where the corpus lives.

The event behind it ([ee-example-freshness]) is a real audit finding that
became `wf freshness` + a scaffolded corpus-CI workflow — the pattern page
is the promoted form, at maturity 1 (one project). It becomes
`status: standard` only with a second independent project replicating it.

[ee-example-freshness]: <!-- wikilink target: experience-events page -->