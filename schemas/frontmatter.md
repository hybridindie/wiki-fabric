---
title: Frontmatter Contracts
type: registry
---

# Frontmatter Contracts

Per-type required fields. A page lacking required fields fails `scripts/cmd/lint.py`.

## Common (all pages)

| Field | Type | Notes |
|---|---|---|
| `type` | enum | one of: `source`, `source-summary`, `claim`, `concept`, `question`, `synthesis`, `decision`, `experience-event`, `commitment`, `pattern`, `anti-pattern`, `experiment`, `change-set`, `promotion-dossier`, `ontology`, `registry`, `index`, `log` |
| `title` | string | human-readable |
| `description` | string | **OKF-recommended.** One-line summary for index entries, search snippets, previews. Present on ALL types. |
| `tags` | list[string] | **OKF-recommended.** Cross-cutting categorization, lowercase kebab-case. |
| `status` | enum | **OKF-recommended.** Page lifecycle: `draft` | `stable` | `deprecated`. Absent ⇒ `stable`. See type mapping below. |
| `stale_after` | ISO-8601 datetime | **OKF-recommended.** Content is stale on/after this instant (`now >= stale_after`). Absolute instant, not a TTL. Machine-checkable complement to `review_after`. |
| `resource` | URI or path | **OKF-recommended.** Canonical locator of the underlying asset. |
| `created` | `YYYY-MM-DD` | first authoring date |
| `updated` | `YYYY-MM-DD` | last edit |

### OKF field semantics (decisions)

- **`description` vs `summary`**: `description` is the one-line index/search summary present on ALL types. `summary` remains a `source`-only field carrying the `[[source-summary]]` link — different job, no collision.
- **`resource`**: on `source` pages it equals `source_path` (bundle-relative path into `evidence/raw/`); on `entity`/`concept` pages it is the upstream URL when one exists; absent for purely abstract pages. OKF §6.2: absolute URL, `/`-rooted, or relative path.
- **`status` mapping**: page `status` is the OKF lifecycle (`draft|stable|deprecated`). It is distinct from type-specific workflow statuses — where a type already has a status field with a *different* vocabulary (claim, decision, change-set, experiment, promotion-dossier), the type-specific field keeps its name and meaning and the OKF lifecycle `status` is **omitted** (no collision). Types whose native status IS the lifecycle (pattern, anti-pattern) map directly.
- **`stale_after`**: machine-checkable staleness. `review_after` (date-only, human review reminder) and `stale_after` (instant, consumer gate) may coexist; lint warns on overdue `stale_after` the same as REVIEW-AFTER.
- **Type vocabulary stays closed** (`VALID_TYPES` in `lint.py`). OKF permits open types; we tolerate unknown types on import (see «OKF Alignment», `registry/epics/okf-alignment.md`) and expect consumers to tolerate ours. Closed vocab is a governed-ontology feature, not an OKF violation.

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

## `commitment`

Prospective memory: a deferred obligation the fabric must resurface when its
trigger condition plausibly matches a task (see [Task Context](../docs/site/context.md)).

| Field | Notes |
|---|---|
| `id` | `commitment-<slug>` |
| `project` | repo short-name (commitments are project-scoped) |
| `trigger` | free-text condition/state that should surface it — **required** |
| `owner` | actor convention (`human:<id>` \| `agent/<owner>/<model>`) — **required** |
| `status` | `open \| done \| cancelled \| superseded` |
| `due` | `YYYY-MM-DD` — overdue commitments warn at task time |
| `linked_episode` | `[[experience-event-...]]` the obligation arose from |
| `source_refs` | evidence for why the obligation exists |
| `superseded_by` | (if `status: superseded`) |

**Invariants** (lint `COMMITMENT`):
- `trigger` and `owner` are required — an unowned or untriggerable commitment
  can never resurface, defeating the kind.
- `status: superseded` ⇒ `superseded_by`.
- `done`/`cancelled` commitments are excluded from context compilation.

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

## `attested-computation` (OKF v0.2 §10)

| Field | Notes |
|---|---|
| `id` | `ac-<slug>` |
| `runtime` | `python` \| `bash` \| `shell` — what executes the computation |
| `parameters` | list of `{name, type, required}` — typed, named holes the agent may fill |
| `computation` | optional path to the computation file (else body `# Computation` fence) |
| `executor` | `{resource, receipt}` — run instructions + required receipt fields |
| `attester` | `{resource}` — deterministic (no-LLM) check over the receipt |
| `generated` | actor that produced the computation |
| `verified` | human sign-off on the definition |

**Attestation vs verification** (§10.6): `verified` confirms the definition
matches policy (doc-level, slow, in-bundle); attestation confirms a single RUN
produced the value the sanctioned way (per-call, runtime, receipt-based, never
stored in the bundle). Receipt/verdict shapes are a fabric profile choice
(minimal JSON), pending the spec's §12 deferred work.

**Gate wiring**: `promote.py`/`mine-promotions.py` refuse without a fresh
receipt from the eval attested computation (compiler-eval policy).

## `entity` (reference-only)

| Field | Notes |
|---|---|
| `title` | symbol name |
| `resource` | optional upstream URL |
| `tags` | repo/domain tags |

Auto-generated by `scripts/cmd/build-entity-index.py` (symbol → file:line). Excluded
from wikilink checks; reference-only.

## `skill`, `wiki-article`

| Type | Required | Notes |
|---|---|---|
| `skill` | `type`, `name`, `description` | opencode skill files (`system/skills/*/SKILL.md`) carry `type: skill` |
| `wiki-article` | `type`, `title`, `generated` | OpenWiki-style page (LangChain-OpenWiki anatomy). Written by `wf export wiki` into the vault. Carries: `generated: {by, at}` (provenance), optional `sources` (`[[src-...]]` backtrace), and `cites` (`[[claim-...]]` list). Body enforces a `SUMMARY:` lead + `## Key Takeaways` + `## Sources`. Machine value is emitted separately as `registry/wiki-graph.json`; wiki prose is excluded from `wf query`/`wf context` retrieval. |
