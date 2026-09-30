---
type: experience-event
title: "Freshness cycle caught upstream drift on dormant machines"
project: example-project
domain: [agent-systems]
observed_problem: "Connected repos went uncaptured 9 days while every machine was busy; the team corpus carried claims validated against pre-drift revisions. Hooks did not run because hooks run on commits — a dormant machine makes no commits."
intervention: "The scheduled upstream-freshness cycle (wf freshness on the corpus CI): capture-git --since-state + mechanical auto-reverify per connected repo, nightly; refreshed evidence lands in the team corpus via sync."
conditions:
    task_class: infra-ops
    runtime: corpus-CI
outcomes:
    drift_window: "unbounded→1d"
    tokens_per_run: "0"
verified:
    - by: "human:owner"
      at: "2026-09-30"
      outcome: "captured, works"
last_verified: 2026-09-30
relations:
    - target: "[[pattern-example-freshness-cadence]]"
      type: "supports"
---

# Experience event: the freshness cycle

What happened: the freshness guarantee had a hole nobody could see — the
per-commit hook is layer 1, but dormant machines make no commits, so the
team corpus aged past its evidence with nothing noticing. The audit found
it; the cycle closed it.

Evidence-plane note: the cycle never rewrites claims. It captures upstream
PR/issue records (sha256-gated, dedup) and mechanically re-verifies quotes
against their recorded locators. Anything judgment-shaped stays human-gated.