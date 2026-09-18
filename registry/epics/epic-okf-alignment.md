---
type: registry
title: Epic — OKF v0.2 Alignment
id: epic-okf-alignment
status: proposed
priority: high
spec: https://okf.md/spec/
spec_source: https://github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/okf/SPEC.md
spec_version: "0.2"
github_issue: https://github.com/hybridindie/wiki-fabric/issues/1
created: 2026-09-16
updated: 2026-09-16
stories:
  - "[[story-okf-01-conformance-baseline]]"
  - "[[story-okf-02-frontmatter-alignment]]"
  - "[[story-okf-03-trust-provenance]]"
  - "[[story-okf-04-attested-computation]]"
  - "[[story-okf-05-bundle-export]]"
  - "[[story-okf-06-bundle-import]]"
  - "[[story-okf-07-tooling-interop]]"
---

# Epic: OKF v0.2 Alignment

## Why

The [Open Knowledge Format](https://okf.md/spec/) (Google, v0.2 Jul 2026) standardizes
exactly what wiki-fabric already does: a directory of markdown files with YAML
frontmatter, readable by humans and agents, distributed via git. Aligning buys:

1. **Interop** — our fabric becomes consumable by any OKF reader (Knowledge Catalog, viz.html, okflint, OpenWiki, Roteiro) and our tools can consume external OKF bundles.
2. **Provenance standard** — OKF v0.2's `sources`/`generated`/`verified` trust family is a formalized version of our provenance invariants; adopting it makes the fabric legible to outside consumers instead of idiosyncratic.
3. **Attested Computation** — a prescribed type that formalizes "deterministic computation backing a claim" — exactly our `experiment` type's role, but with a portable contract (runtime, parameters, executor, attester).
4. **Ecosystem leverage** — validators (`okflint`, `okf-schema`), publishers (Kiso), generators (superops-team/okf) work on conformant bundles for free.

## Gap Analysis (current schema vs OKF v0.2)

| OKF v0.2 concept | wiki-fabric today | Gap | Verdict |
|---|---|---|---|
| Bundle = dir of md + frontmatter | ✅ identical | none | conformant by accident |
| Required `type` on every doc | ✅ VALID_TYPES enum | we are *stricter* (closed enum vs open vocabulary) | story 2 decides open-vs-closed |
| `title`, `description`, `tags` | title ✅; description ❌ (we use `summary` on some types); tags ❌ | partial | story 2 |
| `resource` (canonical URI) | ❌ (we use `source_path` into raw/) | partial — raw/ paths ARE the resource | story 2 |
| `sources[]` provenance family | claims use `source_refs` (richer: locator+quote) | our claim refs are a superset; non-claim types have no provenance | story 3 |
| `generated: {by, at}` | ❌ (only `created`/`updated` dates, no actor) | missing — this is the agent-provenance gap | story 3 |
| `verified[]` (trust tier) | claims have `last_verified` date but no verifier actor | partial | story 3 |
| `status` (draft/stable/deprecated) | per-type statuses exist but no common lifecycle field | partial | story 2 |
| `stale_after` | `review_after` (date, warning-level lint) | near-equivalent | story 2 |
| `index.md` / `log.md` reserved names | ✅ registry/index.md + registry/log.md (+ rebuild-index.py generator) | none | conformant |
| Markdown links (bundle-relative) | ❌ we use `[[wikilinks]]` | divergence — OKF plugin flags wikilinks; Obsidian needs them | story 2 (dual-link or converter) |
| Per-claim footnotes keyed to sources[].id | claims use structured `source_refs` | ours is stronger (machine-readable, locator-checked) | keep ours; expose as OKF-compatible |
| `# Citations` body section | ❌ (frontmatter-only) | n/a in v0.2 (superseded by `sources`) | none |
| Attested Computation type | `experiment` (hypothesis/metrics/results) | different shape — experiment records results; AC declares a *sanctioned computation* | story 4 |
| `references/` convention | ❌ | new dir for executors/attesters | story 4 |
| Conformance = frontmatter + type | lint.py has 14 checks (stricter) | we exceed; need an OKF-conformance view | story 1 |
| `okf_version` in root index | ❌ | trivial | story 1 |

## Strategy

**Dual-conformance, not replacement.** wiki-fabric's schema is a strict superset of
OKF's (type + frontmatter + links + log). The fabric remains the system of record
with its richer invariants (locators, maturity gates, hash-anchored sources).
OKF alignment means:

1. Every fabric page *is* a conformant OKF concept (frontmatter superset).
2. `wf okf export` renders any scope of the fabric as a portable OKF bundle.
3. `wf okf import` reads external bundles as external sources with trust tiers.
4. Lint grows an `--okf` mode: OKF-conformance errors gate, fabric-specific rules stay wiki-fabric's.

## Non-Goals

- Migrating content files to OKF-only shape (breaking change, loses locator richness).
- Adopting OKF's untyped markdown links *inside* the fabric (Obsidian wikilinks stay; conversion happens at export).
- Knowledge Catalog / GCP tooling integration (no GCP dependency).

## Stories

| Story | Deliverable | Depends on |
|---|---|---|
| [[story-okf-01-conformance-baseline]] | lint `--okf` mode + okflint cross-check | — |
| [[story-okf-02-frontmatter-alignment]] | schema field alignment (description/tags/resource/status/okf_version) | 1 |
| [[story-okf-03-trust-provenance]] | generated/verified/sources families wired into ingest/promote/hooks | 2 |
| [[story-okf-04-attested-computation]] | Attested Computation type + executor/attester for evals | 3 |
| [[story-okf-05-bundle-export]] | `wf okf export` → portable bundle | 1–3 |
| [[story-okf-06-bundle-import]] | `wf okf import` → external bundle as source | 5 |

## Log

- 2026-09-16 — **Creation**: epic opened after OKF v0.2 spec review; gap analysis recorded above.