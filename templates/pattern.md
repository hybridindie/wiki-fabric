---
type: pattern
id: pattern-<slug>
title: <Pattern Title>
scope: global
domain: [agent-systems]
status: candidate
maturity: 1
maturity_evidence: []
applicability:
  includes:
    - <condition 1>
    - <condition 2>
  excludes:
    - <exclusion 1>
problem: <One-paragraph problem statement>
forces:
  - <force 1>
  - <force 2>
solution: <One-paragraph solution>
consequences:
  benefits:
    - <benefit 1>
    - <benefit 2>
  costs:
    - <cost 1>
evidence:
  - ref: "[[ee-<experience-event-slug>]]"
    kind: direct-experience
    outcome: positive
  - ref: "[[ee-<experience-event-slug>]]"
    kind: direct-experience
    outcome: positive
counterexamples: []
related:
  - "[[pattern-<related-slug>]]"
  - "[[anti-pattern-<related-slug>]]"
review_after: {{date:YYYY-MM-DD, +90 days}}
tags: [<tag1>, <tag2>]
created: {{date:YYYY-MM-DD}}
updated: {{date:YYYY-MM-DD}}
---

# Pattern: <Pattern Title>

> **Status: candidate, maturity 1** — one project, pending replication.

## Pattern

> **Context:** <when this applies>
> **Problem:** <the recurring problem>
> **Forces:**
> - <force 1>
> - <force 2>
> **Solution:** <the recommended approach>
> **Consequences:**
> - **Benefits:** <benefits>
> - **Costs:** <costs>

## Evidence

| Experience Event | Kind | Outcome |
|------------------|------|---------|
| [[ee-<slug>]] | direct-experience | positive |

## Applicability

**Applies when:**
- <condition 1>
- <condition 2>

**Does not apply when:**
- <exclusion 1>

## Counterexamples

None yet.

## Related

- [[anti-pattern-<slug>]] — the failure mode this pattern prevents
- [[skill-<slug>]] — the executable procedure

## Review

After: {{date:YYYY-MM-DD, +90 days}}
Owner: user