---
type: registry
title: OKF v0.2 Alignment (epic + status)
id: okf-alignment
status: done
priority: high
spec: https://okf.md/spec/
spec_source: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/okf/SPEC.md
spec_version: "0.2"
github_issue: https://github.com/hybridindie/wiki-fabric/issues/1
created: 2026-09-16
updated: 2026-09-23
tags: [okf, provenance, attested-computation, bundle]
---

# OKF v0.2 Alignment — Epic & Status

Consolidated epic + story pages for aligning wiki-fabric with the
[Open Knowledge Format v0.2](https://okf.md/spec/) (Google, Jul 2026).

## Why

OKF standardizes what wiki-fabric already does: a directory of markdown files
with YAML frontmatter, readable by humans and agents, distributed via git.
Aligning buys:

1. **Interop** — the fabric becomes consumable by any OKF reader, and fabric
   tools can consume external OKF bundles.
2. **Provenance standard** — OKF v0.2's `sources`/`generated`/`verified` trust
   family formalizes our provenance invariants.
3. **Attested Computation** — a prescribed type formalizing "deterministic
   computation backing a claim."
4. **Ecosystem leverage** — validators (`okflint`), publishers (`Kiso`),
   generators work on conformant bundles for free.

## Strategy

**Dual-conformance, not replacement.** wiki-fabric's schema is a strict superset
of OKF's (type + frontmatter + links + log). The fabric remains the system of
record with richer invariants (locators, maturity gates, hash-anchored sources).

1. Every fabric page *is* a conformant OKF concept (frontmatter superset).
2. `wf okf export` renders any scope as a portable OKF bundle.
3. `wf okf import` reads external bundles as external sources with trust tiers.
4. Lint has an `--okf` mode: OKF-conformance errors gate; fabric-specific rules
   stay in the default profile.

## Status

The OKF alignment work is **shipped** (as of 2026-09-23). Story-level acceptance
checklists are superseded; the shipped artifacts are:

| Delivery area | Shipped where |
|---|---|
| `lint --okf` (OKF v0.2 §11 conformance floor) + `--format json` block | `scripts/cmd/lint.py` |
| `okf_version: "0.2"` in root `index.md` | `index.md` |
| `wf okf export` → portable bundle | `scripts/cmd/okf_export.py` |
| `wf okf import` → external source (trust tier recorded, not inherited) | `scripts/cmd/okf_import.py` |
| Attested Computation pages | `global/computations/ac-*.md` |
| Attesters (deterministic receipt checks) | `references/attesters/check-golden-eval.py`, `check-zero-errors.py` |
| Executor skills | `references/skills/run-golden-eval.md`, `run-profile-lint.md` |
| Actor convention `agent/<owner>/<model>` / `human:<id>` / `process:<id>` | `fabric_config.py` (`actor()`), `scripts/lib/` |
| OKF-recommended fields (`description`, `tags`, `status`, `stale_after`) | `schemas/frontmatter.md` |
| Type vocabulary stays closed | `scripts/cmd/lint.py` `VALID_TYPES` (governed ontology) |

> These were the old story IDs; they are now consolidated here and removed as
> individual pages: story-okf-01 (-baseline), 02 (-frontmatter-alignment),
> 03 (-trust-provenance), 04 (-attested-computation), 05 (-bundle-export),
> 06 (-bundle-import).

## Gap Analysis (original schema vs OKF v0.2)

| OKF v0.2 concept | wiki-fabric today | Gap | Resolved |
|---|---|---|---|
| Bundle = dir of md + frontmatter | identical | none | ✅ |
| Required `type` | `VALID_TYPES` closed enum | stricter than OKF open vocab | ✅ closed-vocab decision |
| `title`, `description`, `tags` | `title` ✅; `description`/`tags` added | partial → added | ✅ |
| `resource` (canonical URI) | `source_path` into raw/ | source path IS the resource | ✅ |
| `sources[]` provenance | claims use `source_refs` (locator+quote superset) | richer; non-claim types got `sources` | ✅ |
| `generated: {by, at}` | `created`/`updated` only | added actor family | ✅ |
| `verified[]` trust tier | `last_verified` date only | added verifier actor | ✅ |
| `status` draft/stable/deprecated | per-type statuses | common lifecycle field added | ✅ |
| `stale_after` | `review_after` (warning) | added machine-checkable instant | ✅ |
| `index.md` / `log.md` reserved | `registry/index.md` + `registry/log.md` | none | ✅ |
| Markdown links vs wikilinks | `[[wikilinks]]` | converted at export boundary only | ✅ (Obsidian keeps wikilinks) |
| Per-claim footnotes keyed to sources[].id | `source_refs` | rendered at export | ✅ |
| Attested Computation type | `experiment` (results) | AC = sanctioned computation; shipped under `global/computations/` | ✅ |
| `references/` convention | none | added for executors/attesters | ✅ |
| OKF conformance | 14-check lint | `--okf` floor added | ✅ |
| `okf_version` in root index | none | added | ✅ |

## Non-Goals (still held)

- Migrating content files to OKF-only shape (breaking change; loses locator richness).
- Adopting OKF's untyped markdown links *inside* the fabric (Obsidian wikilinks
  stay; conversion happens only at export).
- Knowledge Catalog / GCP tooling integration (no GCP dependency).

## Log

- 2026-09-16 — Epic opened after OKF v0.2 spec review; gap analysis recorded.
- 2026-09-23 — Shipped: all story deliverables implemented and tested; 6 story
  pages + epic page consolidated into this single reference (was 7 files).
