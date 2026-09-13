---
name: ingest
description: Ingest a raw source into the global evidence fabric — creates source record, faithful summary, extracts claims, opens a change-set for review.
---

# Ingest Skill (Global Architecture)

Handles the 10-step ingest protocol from AGENTS.md. Writes to the project's namespace in the global fabric.

## When to Use

User says "ingest <source-path>" or "add this source" where source-path is under `evidence/raw/`.

## Procedure

### 1. Resolve Project Context
Read project's `.wiki-overlay.md` → get `namespace` (e.g., `my-project`).
All project-scoped writes go to `projects/<namespace>/`.

### 2. Resolve Source
Read the raw file at `evidence/raw/<path>`. Compute SHA256.

### 3. Create Source Record
Write `evidence/sources/src-<slug>.md` (global, shared across projects) with frontmatter:
- `type: source`
- `sha256: <hash>`
- `source_path: evidence/raw/<path>`
- `captured: <today>`
- `summary: "[[sum-<slug>]]"`

### 4. Write Source Summary
Write `evidence/source-summaries/sum-<slug>.md` — faithful, locator-rich, no inference.

### 5. Extract Claims
Identify atomic propositions from the summary. For each:
- Write `evidence/claims/claim-<slug>.md` (global, shared) with `status: proposed` (no refs yet) or `supported` (with `source_refs` pointing back to the source record + locator + quote).

### 6. Resolve Affected
Search `registry/index.md` then wikilinks to find existing claims/concepts/entities that may be supported/weakened/contradicted/superseded.

### 7. Open Change-Set
Create `evidence/traces/change-sets/<date>-<slug>/` with:
- `manifest.md` — sources+hashes, pages created/updated, new claims, detected contradictions, any source-less assertions, reason for each edit
- `diff.md` — unified diff of proposed changes

### 8. Run Deterministic Lint
`python3 scripts/lint.py .` — must pass (0 errors).

### 9. Human Gate
Present manifest + diff. Ask for approval before merging into canonical pages:
- **Global canonical**: `domains/`, `global/`
- **Project canonical**: `projects/<namespace>/decisions/`
- **Staging** (no gate needed): `evidence/claims/`, `evidence/source-summaries/`, `projects/<namespace>/experience-events/`

### 10. Merge
Apply manifest to canonical pages; append `## [YYYY-MM-DD] ingest | <slug>` to `registry/log.md`.

### 11. Commit
`git add -A && git commit -m "ingest <change-set-slug> (raw <sha8>)"`.

## Project Namespace Writes

| Content | Location |
|---------|----------|
| Source records | `evidence/sources/` (global, shared) |
| Source summaries | `evidence/source-summaries/` (global, shared) |
| Claims | `evidence/claims/` (global, shared) |
| Experience events | `projects/<namespace>/experience-events/` |
| Decisions (ADRs) | `projects/<namespace>/decisions/` |
| Concepts | `domains/<domain>/concepts/` (global) |
| Syntheses | `domains/<domain>/syntheses/` (global) |
| Patterns/skills | `global/patterns/`, `global/skills/` (global) |

## Error Handling

- If raw file missing → error
- If lint fails → show errors, do not proceed to human gate
- If change-set already exists for same slug → append sequence number
- If project namespace missing → create `projects/<namespace>/` with subdirs

## Output

- New pages under `evidence/sources/`, `evidence/source-summaries/`, `evidence/claims/`
- Change-set directory ready for review
- Updated `registry/index.md` (catalog) and `registry/log.md` (append-only)