---
title: Frontmatter Contracts
type: registry
---

# Frontmatter Contracts

Per-type required fields. A page lacking required fields fails `scripts/lint.py`.

## Common (all pages)

| Field | Type | Notes |
|---|---|---|
| `type` | enum | one of: `source`, `source-summary`, `claim`, `concept`, `question`, `synthesis`, `decision`, `experience-event`, `pattern`, `anti-pattern`, `experiment`, `change-set`, `promotion-dossier`, `ontology`, `registry`, `index`, `log` |
| `title` | string | human-readable |
| `created` | `YYYY-MM-DD` | first authoring date |
| `updated` | `YYYY-MM-DD` | last edit |

## `source`

| Field | Notes |
|---|---|
| `kind` | `doc`, `article`, `chat-transcript`, `test-log`, `pdf`, `video` |
| `source_path` | relative path into `raw/` |
| `sha256` | content hash of the raw file (recomputed on refresh) |
| `captured` | date |
| `summary` | `[[link]]` to the `source-summary` |

## `source-summary`

| Field | Notes |
|---|---|
| `source` | `[[link]]` to the source record |
| `status: pending \| ingested` | `ingested` once a summary exists |
| `title` | faithful, no inference |

## `claim`

| Field | Notes |
|---|---|
| `id` | `claim-<slug>` — globally unique |
| `statement` | one atomic proposition |
| `status` | `proposed \| supported \| contested \| superseded \| retracted` |
| `confidence` | `low \| medium \| high` |
| `evidence_strength` | `primary \| secondary \| tertiary` |
| `source_refs` | list of `{source, locator, quote, supports?}` — **must be non-empty** unless `status: proposed` |
| `last_verified` | `YYYY-MM-DD` |
| `temporal` | `asserted_at`, `observed_at`, `valid_from`, `valid_until`, `applies_when` |
| `relations` | list of `{type: supports\|contradicts\|refines\|supersedes\|depends_on, target: [[claim-...]]}` |

**Invariants**:
- `status != proposed` ⇒ `source_refs` non-empty and every `locator` resolves.
- `status: superseded` ⇒ must have `superseded_by: [[claim-...]]`.
- No circular `supersedes` chains.
- `status: supported` ⇒ at least one `supports: true` ref.

## `concept`

| Field | Notes |
|---|---|
| `claims` | list of `[[claim-...]]` — **concept must draw only from linked claims** |
| `domain` | list |

## `question`

| Field | Notes |
|---|---|
| `priority` | `P0\|P1\|P2` |
| `rationale` | why this matters |
| `related` | list of `[[...]]` |

## `synthesis`

| Field | Notes |
|---|---|
| `question` (or `title`) | the query being answered |
| `claims` | list of `[[claim-...]]` used |
| `confidence` | `low\|medium\|high` with stated rationale |
| `next` | list of follow-ups |

## `decision`

| Field | Notes |
|---|---|
| `status` | `proposed \| accepted \| superseded \| rejected` |
| `context` | |
| `rationale` | |
| `consequences` | |
| `superseded_by` | (if `status: superseded`) |

## `experience-event`

| Field | Notes |
|---|---|
| `project` | repo short-name |
| `domain` | list |
| `observed_problem` | one paragraph |
| `intervention` | one paragraph |
| `conditions` | task_class, runtime, platform, tool, … |
| `outcomes` | dict — happy_path, metrics, etc. |
| `evidence` | list of `[[src-...]]` |
| `lineage` | free text describing the source lineage (for the independence rule) |

## `pattern`

| Field | Notes |
|---|---|
| `id` | `pattern-<slug>` |
| `scope` | `global \| domain \| project` |
| `status` | `candidate \| recommended \| standard \| deprecated` |
| `maturity` | `0\|1\|2\|3` |
| `maturity_evidence` | list of `{project, kind, ref}` |
| `applicability` | `{includes: [...], excludes: [...]}` |
| `problem` | |
| `forces` | |
| `solution` | |
| `consequences` | `{benefits: [...], costs: [...]}` |
| `evidence` | list of `{ref, kind, outcome: positive\|negative\|mixed}` |
| `counterexamples` | list |
| `related` | list |
| `review_after` | `YYYY-MM-DD` |

**Maturity gate**:
- `status: candidate` may have any maturity.
- `status: recommended` ⇒ `maturity >= 2` (two **independent** evidence lineages).
- `status: standard` ⇒ human owner review + `maturity: 3`.

## `anti-pattern`

Same as `pattern` with `status: candidate\|recommended\|deprecated`.

## `experiment`

| Field | Notes |
|---|---|
| `question` | one-line query |
| `hypothesis` | |
| `status` | `planned \| running \| done \| failed` |
| `repo` | `git\|path` to the implementation |
| `commit` | |
| `environment` | dict: model, inference server, gpu, temperature, … |
| `metrics` | list of names |
| `related_claims` | |
| `raw_artifacts` | |
| `results` | `{metric: value}` |

## `change-set`

| Field | Notes |
|---|---|
| `id` | `change-set-<date-slug>` |
| `status` | `open \| merged \| rejected` |
| `scope` | `staging \| canonical` |

## `promotion-dossier`

| Field | Notes |
|---|---|
| `pattern_ref` | `[[pattern-...]]` |
| `anti_pattern_ref` | optional |
| `status` | `pending-review \| recommended \| rejected` |

## `ontology`, `registry`, `index`, `log`

Metadata-only. `status` not required. Free structure inside.

## Wikilink resolution

`[[stem]]` resolves to a page whose **filename base** equals `stem`, OR whose `id`
frontmatter equals `stem` (case-insensitive, hyphen/space tolerant), OR whose `aliases:`
contain `stem`. A page with no resolving target is a **broken link** (lint error).
