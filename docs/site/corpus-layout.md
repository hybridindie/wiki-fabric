---
type: doc
title: "Corpus layout — where every artifact lives"
description: "Single-truth map of corpus content dirs, their producers and consumers, and the layout module that guards the names"
created: 2026-10-01
updated: 2026-10-01
---

# Corpus layout

Every second-level content dir name is declared once in
`scripts/lib/layout.py` (`SEGMENTS`). Scripts compose paths through that
module — re-spelling `"evidence/claims"` at a call site is the bug class this
module exists to kill. `layout.seg()` **raises on undeclared names**, so a
new dir must be added to `SEGMENTS` first (plus the coordination points in
"Adding a directory" below).

Corpus root resolution is `fabric_config.CORPUS_ROOT` (`VAULT_ROOT` is a
legacy alias for the same value).

## The tree

| Path | Artifact | Producer(s) | Consumers |
|---|---|---|---|
| `evidence/raw/<slug>/` | immutable captures (docs + `git/` PRs/issues/commits + `chats/` sessions + `obsidian/` harvests) | capture, capture-git, capture-chat, hooks | ingest (`--changed`), threads index, lint SOURCE-DRIFT, review --verify-locators |
| `evidence/raw/<scope>-okf/` | imported OKF bundles | okf import | ingest `--pending <scope>-okf` |
| `evidence/sources/src-*.md` | source records (sha256, resource locator) | ingest, okf import | review, propose-domains, lint, threads |
| `evidence/source-summaries/sum-*.md` | faithful summaries with locators | ingest | retrieval, lint SOURCE-EMPTY |
| `evidence/claims/claim-<slug>-NNN.md` | atomic claims with source_refs | ingest | query, context, synthesize, export, lint, judgment, embed index |
| `evidence/insights/` | chat-mined insight pages (type: synthesis) | mine-chats | review scan |
| `evidence/traces/change-sets/<date>-<slug>/` | staging manifests + diffs (human gate) | ingest | apply-changeset, sync PR body |
| `evidence/traces/wiki-runs/` | wiki-generation run checkpoints | wiki-generate | resume protocol |
| `evidence/_inbox/<scope>-okf/` | quarantine for foreign-bundle content needing review | okf import | human |
| `evidence/experiments/` | typed experiment records (with baselines) | — (reserved; policy + template exist) | lint, sync plane |
| `patterns/` + `patterns/_inbox/` + `patterns/_rejected/` | canonical patterns; staged candidates; rejection tombstones | mine-chats --propose (staging), promote-patterns --apply, promote | mining suppression, context, gate |
| `anti-patterns/` | canonical anti-patterns (type: anti-pattern) | promote-patterns --apply | promote.py, lint, retrieval |
| `skills/` | durable procedures promoted as fabric skills | promotion pipeline | context |
| `concepts/` | synthesized concepts built from claims | synthesize | export, harvest-questions, retrieval |
| `domains/ontology.md` | domain vocabulary (human-gated merges) | promote-domains | domain detection, lint scope |
| `projects/<slug>/` | namespace pages: README, `decisions/`, `experience-events/ee-*.md`, `commitments/`, `receipts/` | bootstrap-project, log-experience, wf context | mine-promotions, context precedence, lint SCOPE |
| `registry/catalog.json` | page index (derived) | rebuild-index | query, context, dispatch status |
| `registry/threads.json` | PR/issue/chat thread graph (derived) | rebuild-index | query, thread, mining |
| `registry/log.md` | append-only operation timeline (OKF §9) | ingest, promote, okf import, sync | lint §9, doctor |
| `registry/promotions/` | promotion dossiers (human-gated) | mine-promotions | promote, gate |
| `registry/effects/*.effects.json` | judged-effect verdict artifacts (machine, never beside pages) | verify-effects | ingest agent |
| `registry/receipts/` | context delivery receipts | wf context --write-receipt | gate --deliveries, mining |
| `registry/pending-gate.md` | cached gate report for session start | wf gate (via hooks) | agents |
| `registry/conflicts/` | sync conflict records | sync pull | lint SYNC-CONFLICT |
| `registry/question-proposals/` | harvested open questions (gated) | harvest-questions | promote-questions |
| `registry/wiki-graph.json` | machine edge layer behind the wiki | export | machine contract |
| `registry/wiki-export-manifest.json` | obsidian export ledger | obsidian bridge | harvest-before-export |
| `global/entities/` | entity index pages (derived, gitignored) | build-entity-index | dispatch status |
| `global/graphs/` | per-repo graphify graphs + hashes | graphify-bridge | --diff staleness, deep dives |
| `syntheses/` | saved query answers (excluded from retrieval) | query --save | humans |
| `questions/` | promoted question pages (open → answered) | promote-questions | query gaps, gate |
| `wiki/` | human-facing generated wiki (output vault) | export-wiki, wiki-generate | humans / Obsidian |

## Naming prefixes (the join contract)

`src-` / `sum-` / `claim-<raw-rel-slug>` (≤80 chars, shared by `layout.claims_for_source`)
/ `ee-` / `pattern-` / `anti-pattern-` / `concept-` / `promotion-` / `tombstone-` /
`entity-` / `question-` / `change-set-` / `receipt-` — declared in `layout.PREFIXES`.
Producers and consumers both derive slugs through layout helpers; the
claim↔source join depends on `claim-` + the raw rel path, so raw paths under
`evidence/raw/` should never be renamed casually.

## Rules

1. **Raw is immutable** — `evidence/raw/` is never edited in place; re-capture.
2. **Machine artifacts never sit beside pages** — only `.md` pages live in
   content dirs; json/verdict artifacts go to `registry/` subdirs (effects,
   receipts, indexes). `.last-capture` markers inside raw are the one
   sanctioned exception (state for the sha256-gated capture loop).
3. **Immutable vs derived:** raw/ + sources/ = recorded evidence; claims/ +
   concepts/ = derived atoms; registry/ + global/entities = derived indexes.
   Derived content is regenerable; recorded evidence is not.
4. **Type decides the dir** — anti-pattern candidates in `patterns/_inbox/`
   apply to `anti-patterns/` (not `patterns/`); promoted dossiers land in
   `registry/promotions/`.
5. **Sync planes** (`sync_lib/policy.py`): evidence-plane (raw, sources,
   summaries, insights, traces, inbox) vs atom-plane (claims, patterns,
   concepts, projects). Layout changes must keep both classified.

## Adding a directory

 coordination checklist (all deterministic, 0 tokens):
- `layout.SEGMENTS` (+ accessor + `PREFIXES` if the page type has an id shape)
- `scripts/cmd/lint.py` — `VALID_TYPES` (if a new page type), `CONCEPT_DIR_PREFIXES`
- `scripts/lib/wf_common.py` — `SKIP_PARTS` if non-concept
- `scripts/lib/sync_lib/policy.py` — plane classification
- `scripts/cmd/rebuild-index.py` — `scan_vault` category
- `scripts/harness/hooks.py` — `_FABRIC_OUTPUT_DIRS` (drift capture matching)
- `scripts/okf-base.yaml` — okflint per-type fields; export scope roots in
  `scripts/cmd/okf_export.py`

## History

- 2026-10-01: layout.py introduced (Tier-2 single truth); anti-pattern
  apply-path bug fixed (candidates were unconditionally dropped into
  patterns/); promote-queue update made fail-soft; effects verdicts moved to
  registry/effects/; canonical layout doc created (this file).