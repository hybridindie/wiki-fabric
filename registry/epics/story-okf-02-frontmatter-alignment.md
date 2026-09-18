---
type: registry
title: Story — Frontmatter alignment (description/tags/resource/status/okf_version)
id: story-okf-02-frontmatter-alignment
status: proposed
epic: "[[epic-okf-alignment]]"
priority: high
estimate: M
depends_on: "[[story-okf-01-conformance-baseline]]"
github_issue: https://github.com/hybridindie/wiki-fabric/issues/3
created: 2026-09-16
updated: 2026-09-16
---

# Story: Frontmatter alignment with OKF recommended fields

## As a
consumer of the fabric (external OKF tooling, or another agent)

## I want
every fabric page to carry OKF's recommended fields (`title`, `description`,
`tags`, `resource`, `status`, `stale_after`)

## So that
index generators, search snippets, and external readers work on fabric pages
without wiki-fabric-specific parsing.

## Acceptance criteria

- [ ] `schemas/frontmatter.md` gains a "Common OKF-recommended" table: `description` (one-line summary), `tags` (list), `status` (`draft|stable|deprecated`), `stale_after` (ISO-8601 instant)
- [ ] `description` semantics decided: alias of, or distinct from, `summary` (recommendation: `description` = one-line index/search summary on ALL types; `summary` stays source-only as the faithful-summary link)
- [ ] `resource` field added: for `source` pages it is the `source_path` (raw/ bundle-relative path); for entity/concept pages it is the upstream URL when one exists
- [ ] `status` mapping per type decided and documented (e.g. claim `status` enum is richer — OKF `status` stays absent on claims to avoid collision; pattern/anti-pattern/experiment map explicitly)
- [ ] `stale_after` adopted as the machine-checkable complement to `review_after` (date-only) — lint warns on `now >= stale_after`, consistent with our REVIEW-AFTER check
- [ ] Templates updated (all 10) to include the new common fields
- [ ] `rebuild-index.py` includes `description` in index entries (OKF §8: entries SHOULD include description)
- [ ] ingest.py / log-experience.py / promote.py write the new fields on generated pages
- [ ] Decision recorded: **type vocabulary stays closed** (our VALID_TYPES enum) — OKF permits open types, consumers must tolerate ours; we tolerate unknown types on import (story 6)

## Notes

- Our type enum is stricter than OKF requires; OKF v0.2 §11 only requires non-empty `type`. Closed vocab is a fabric feature (governed ontology), not a violation.
- Wikilinks stay for intra-fabric references; OKF markdown links are an export concern (story 5), not a rewrite.

## Log

- 2026-09-16 — **Creation**: story opened.