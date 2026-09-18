---
type: registry
title: Story — Trust & provenance families (generated/verified/sources)
id: story-okf-03-trust-provenance
status: proposed
epic: "[[epic-okf-alignment]]"
priority: high
estimate: L
depends_on: "[[story-okf-02-frontmatter-alignment]]"
github_issue: https://github.com/hybridindie/wiki-fabric/issues/4
created: 2026-09-16
updated: 2026-09-16
---

# Story: Adopt OKF v0.2 trust + provenance families

## As a
an agent consuming fabric content at task time

## I want
frontmatter to answer: *where did this come from* (`sources`), *who/what wrote
it and when* (`generated`), *who/what confirmed it* (`verified`), *is it still
current* (`stale_after`)

## So that
I can derive OKF trust tiers (unverified / machine-confirmed / human-reviewed)
and weight retrieval accordingly — the same judgment our trust-score formula
(T = w1·provenance + w2·review − w5·contradictions) approximates.

## Acceptance criteria

- [ ] Actor convention adopted (§7): `agent/<name>/<model>` for fabric scripts, `human:<id>` for owner, `process:<id>` for hooks/cron. `fabric_config.py` gains `actor()` returning the right form per context (owner from fabric.yaml, script name+model from llm config)
- [ ] `generated: {by, at}` written by every generator: `ingest.py` (claims, summaries, change-sets), `synthesize.py`, `promote.py`, `mine-promotions.py`, `log-experience.py`, hooks. Replaces bare `created`/`updated` where actor matters; `created`/`updated` retained (lint checks both)
- [ ] `verified[]` written on: claim pages (human review of extraction), promoted patterns (owner review = the promotion gate), decisions. Actor format enforced by lint
- [ ] Trust-tier derivation added to `query.py` context manifest output (`context.py`): each retrieved page surfaces `trust_tier` — human-reviewed > machine-confirmed > unverified — and the manifest reports the tiers it selected (explainability)
- [ ] `sources[]` family added to non-claim types: concepts/questions/syntheses list their backing `source_refs` in OKF `sources` shape (`id`, `resource` → source page path, `title`, `last_modified` from the source record). Claim `source_refs` stay as-is (superset with locator+quote) and are *rendered* as OKF `sources` + footnotes at export (story 5)
- [ ] `last_modified` on a `sources` entry auto-fills from the referenced source record's sha256/captured date
- [ ] Lint: `generated.by` must match actor convention; `verified[].by` with `human:` prefix required on pages with `maturity >= 2` patterns (ties promotion gate to OKF trust tier)
- [ ] Stale demotion: a page past `stale_after` loses precedence in `context.py` selection (already implemented for `stale` exclusion — extend to `stale_after`)
- [ ] Golden corpus (evaluations/expected/) updated to include the new fields; eval passes

## Notes

- This story is where OKF alignment pays the most: provenance/trust become legible to *any* OKF consumer, and our promotion maturity gate gains a portable expression (pattern with `maturity >= 2` ⇒ must carry a `human:` verification event).
- KL4A's review-gate pattern (human approval recorded per claim) validates this direction; our hook `--extract-claims` flow gains a natural place to record `verified: {by: human:<owner>}` when the user approves a change-set.

## Log

- 2026-09-16 — **Creation**: story opened.