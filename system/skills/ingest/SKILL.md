---
type: skill
name: ingest
description: Ingest a raw source into the evidence fabric via `wf ingest` — creates source record, faithful summary, extracts claims, opens a change-set for review. Handles docs and git-history captures (PR/issue threads, commits).
---

# Ingest Skill

Runs the ingest pipeline from AGENTS.md. CLI-first: use `wf ingest` (or
`python3 scripts/ingest.py`) — the script handles source records, hashes, and
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
```

## Procedure

### 1. Check Before Ingesting (anti-loop)
- Is a `source` record with the same sha256 already in `evidence/sources/`? If yes → skip, tell the user.
- LLM extraction is the most expensive operation in the fabric — never re-ingest an unchanged source.

### 2. Run the CLI
`wf ingest <source> --extract-claims` creates:
- `evidence/sources/src-<slug>.md` — type: source, with sha256 + captured date
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

### 4a. If graphify is ACTIVE: enrich claims with code provenance
When `fabric.yaml` has `integrations.graphify.enabled: true`, run
`python3 scripts/graphify-bridge.py --enrich` after writing claims — this
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
| Concepts | `concepts/` or `domains/<domain>/concepts/` | global |
| Experience events | `projects/<namespace>/experience-events/` | project |
| Decisions (ADRs) | `projects/<namespace>/decisions/` | project |
| Syntheses | `syntheses/` | global |
| Patterns / anti-patterns / skills | `patterns/`, `anti-patterns/`, `skills/` | global |

## Error Handling

- Raw file missing → error, stop
- Lint fails → show errors, do not proceed to human gate
- Change-set slug collision → append sequence number
- `--extract-claims` fails (LLM unreachable) → ingest without extraction (source record + summary only), note in manifest

## Output

- New pages under `evidence/sources/`, `evidence/source-summaries/`, `evidence/claims/`
- Change-set directory ready for review
- Updated `registry/index.md` (via rebuild-index.py)