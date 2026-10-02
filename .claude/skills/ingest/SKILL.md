---
type: skill
name: ingest
description: Ingest a raw source into the evidence fabric via `wf ingest` — creates source record, faithful summary, extracts claims, opens a change-set for review. Handles docs and git-history captures (PR/issue threads, commits).
---

# Ingest Skill

Runs the ingest pipeline from AGENTS.md. CLI-first: use `wf ingest` (or
`wf ingest`) — the script handles source records, hashes, and
claim extraction; the skill adds judgment for classification and change-sets.

## When to Use

- User says "ingest <source-path>" or "add this source" (path under `evidence/raw/`)
- After `wf capture` / `wf capture --git` produced new files in `evidence/raw/`
- Multiple captured files: batch them (see Batch step)

## CLI Commands

```bash
# Ingest with LLM claim extraction (the normal path)
wf ingest evidence/raw/<project>/<file>.md --extract-claims

# Dry run (shows what would be written, no files touched)
wf ingest --extract-claims --dry-run evidence/raw/<file>.md

# Git-history captures: batch a whole directory
wf ingest 'evidence/raw/<project>/git/'*.md --extract-claims

# Different model
WIKI_LLM_MODEL="llama3.1:70b" wf ingest evidence/raw/<file>.md --extract-claims

# Batch modes (anti-loop is enforced mechanically — the CLI skips unchanged hashes)
wf ingest --changed <project-slug>            # only NEW/CHANGED raw files (what the hook runs)
wf ingest --changed <project-slug> --budget 25  # cap the run (tuning.ingest.budget); re-run continues
wf ingest --pending <project-slug>            # claim-extract recorded-but-unextracted sources
wf ingest --reclaim <project-slug>            # recover zero-claim sourced pages
```

## Procedure

### 1. Check Before Ingesting (anti-loop)
- Is a `source` record with the same sha256 already in `evidence/sources/`? If yes → skip, tell the user.
- Same path with a DIFFERENT sha256 → the source re-captured: the old revision's claims are
  mechanically stamped `stale_after` + flip `contested` BEFORE the new record is written
  (0 tokens). Expect this — don't panic at contested claims after a re-capture; re-extract
  the new revision, then `wf review --auto-reverify` re-grounds what still holds.
- LLM extraction is the most expensive operation in the fabric — never re-ingest an unchanged source.

### 2. Run the CLI
`wf ingest <source> --extract-claims` creates:
- `evidence/sources/src-<slug>.md` — type: source, with sha256, captured date, and `review_after` (staleness tier by capture kind: pr-record/commit 30d, chat-session 45d, docs 180d — #160); location: `evidence/sources/`
- `evidence/source-summaries/sum-<slug>.md` — faithful, locator-rich, no inference
- `evidence/claims/claim-<slug>-NNN.md` — atomic claims with `source_refs` (locator + quote), status: supported

### 3. Verify Extraction (LLM judgment)
Read the generated claims against the source. Check each `locator` + `quote`
actually appears in the raw file. Fix or delete claims that hallucinate.
For git captures (`pr-<n>.md`, `issue-<n>.md`, `commit-<sha>.md`): locators are
the PR number / issue number / commit SHA — e.g. `PR #342 description`.

### 4. Classify Effects
For each new claim, classify its effect on existing knowledge:
`add | support | weaken | contradict | supersede | no-action`
Add `relations` entries (`supports`/`contradicts`/`supersedes`/`depends_on`) where they apply.

**4b. Independent verification (when the judgment tier is active).** Your own
classification is a self-preference risk — the model that extracted the claim
is grading its own work. Run:

```bash
wf verify-effects <new-claim>.md ...
# writes <claim>.effects.json (route, per-pair verdicts, confidence)
```

Reconcile: where the judged verdict agrees with your draft, keep it; where it
disagrees (or confidence is low / near-band), re-read both claims before
finalizing — you own the final relations edit, the tier is the second opinion,
not the decision. When the tier is disabled, step 4 stands alone.

### 4a. If graphify is ACTIVE: enrich claims with code provenance
When `fabric.yaml` has `integrations.graphify.enabled: true`, run
`wf graphify enrich` after writing claims — this
attaches `code_symbols` and `graph_edges` (calls/imports/rationale_for) to
claims, linking documentation to the implementing code. When graphify is
inactive, skip this step: claims carry only source_refs (locator + quote).

### 5. Open Change-Set
Create `evidence/traces/change-sets/<date>-<slug>/` with:
- `manifest.md` — sources+hashes, pages created/updated, new claims, newly detected contradictions, any source-less assertions, reason for each edit
- `diff.md` — unified diff of proposed changes

### 6. Lint
`wf lint` — must be 0 errors before the human gate.

### 7. Human Gate
Present manifest + diff. Ask for approval before merging into canonical pages:
- **Staging** (no gate needed): `evidence/claims/`, `evidence/source-summaries/`
- **Canonical** (gate required): `concepts/`, `domains/`, `patterns/`, `anti-patterns/`, `skills/`, `projects/<namespace>/decisions/`

### 8. Merge + Commit
Apply manifest to canonical pages; run `rebuild-index.py`; then one commit:
`git add -A && git commit -m "ingest <change-set-slug> (raw <sha8>)"`

## Content → Location Map

| Content | Location | Scope |
|---------|----------|-------|
| Source records | `evidence/sources/` | global |
| Source summaries | `evidence/source-summaries/` | global |
| Claims | `evidence/claims/` | global |
| Concepts | `domains/<domain>/concepts/` (domain-bound; canonical via the ontology alias map) or `concepts/` (unbound) | global / domain |
| Experience events | `projects/<namespace>/experience-events/` | project |
| Decisions (ADRs) | `projects/<namespace>/decisions/` | project |
| Questions | `questions/` or `domains/<domain>/questions/` (harvest inherits the concept's domain binding) | global / domain |
| Syntheses | `syntheses/` | global |
| Patterns / anti-patterns / skills | `patterns/`, `anti-patterns/`, `skills/` | global |

## Error Handling

- Raw file missing → error, stop
- Lint fails → show errors, do not proceed to human gate
- Change-set slug collision → append sequence number
- `--extract-claims` fails (LLM unreachable) → ingest without extraction (source record + summary only),
  note in manifest; recover later with `wf ingest --pending <slug>` (retry extraction) or `wf ingest --reclaim <slug>`
  (zero-claim sources)
- Source shows zero claims after a full run → `wf ingest --reclaim <slug>` (the CLI prints this recovery path)
- Bulk run interrupted by budget → re-run the same command; the anti-loop resumes past ingested sources (budget defers, never loses)
- `wf lint` reports `VOCABULARY` on a concept's `domain:` → bind via promote-domains/an ontology alias, or leave unbound (the page stays in `concepts/`)
- Upstream source VANISHED (raw deleted) → `wf review --verify-sources` expires the record (`status: expired`); don't recreate raw — provenance is the tombstone

## Output

- New pages under `evidence/sources/`, `evidence/source-summaries/`, `evidence/claims/`
- Change-set directory ready for review
- Updated `registry/catalog.json` (via rebuild-index.py)
