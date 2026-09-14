---
name: refresh
description: Re-capture from upstream repos via `wf capture` (docs) and `wf capture --git` (PR/issue history) into evidence/raw/, then re-ingest only files whose sha256 changed.
---

# Refresh Skill

Keeps the fabric current. CLI-first: `wf capture` for docs, `wf capture --git`
for PR/issue history, then `wf ingest` only what changed (sha256 drift). Raw is
append-only-capture — never edit a captured file in place.

## When to Use

- After upstream work: "refresh my-project"
- Scheduled (e.g., weekly) or before a consequential query
- When `.wiki-overlay.md` `source_repos` changes
- **If graphify integration is enabled** (`fabric.yaml` → `integrations.graphify.enabled: true`): also after upstream code changes — the graphify staleness diff tells you which claims need re-ingest. Skip this step when graphify is inactive.

## CLI Commands

```bash
# Re-capture docs from all source_repos in .wiki-overlay.md
wf capture <project-slug>

# Preview without writing
wf capture <project-slug> --dry-run

# Re-capture PR/issue history from GitHub (gh CLI)
wf capture <project-slug> --git owner/repo --since 6m --limit 30

# From a local repo: high-signal commits + churn ranking
wf capture <project-slug> --git /path/to/repo --churn

# Then ingest only what changed (the capture output says: N new, M changed)
wf ingest 'evidence/raw/<project>/git/'*.md --extract-claims
```

## Procedure

### 1. Identify Sources
Read the project's `.wiki-overlay.md` → `source_repos` (each entry: `path`,
`raw_path`, `globs`). For git history, the repo is `--git`'s argument.

### 2. Capture
`wf capture <slug>` copies matching files into `evidence/raw/<slug>/`
(preserving structure), computing sha256 per file. It reports
`N new, M changed, K unchanged` — this drives step 4.

### 3. Detect Changes
- sha256 differs from the `source` record → changed, mark for re-ingest
- New file with no source record → new ingest
- File deleted upstream → keep the local copy (raw is immutable); note in log

### 3a. If graphify is ACTIVE: staleness diff first
When `fabric.yaml` has `integrations.graphify.enabled: true`, run
`python3 scripts/graphify-bridge.py --diff` before step 4 — the graph hash
diff flags claims whose code symbols changed, prioritizing which sources to
re-ingest. When graphify is inactive, skip this step (sha256 drift in step 3
is the only staleness signal).

### 4. Re-ingest Changed Only (anti-loop)
Never re-ingest unchanged sources — LLM extraction is the most expensive
operation in the fabric. For each changed/new file, run the `ingest` skill
(its own change-set per source, or one batched change-set if related).
Git captures (`pr-<n>.md`, `issue-<n>.md`, `commit-<sha>.md`) ingest the same
way; PR/issue number or commit SHA is the claim locator.

### 5. Log + Commit
One ingest batch = one commit (message: `ingest <change-set-slug> (raw <sha8>)`).

## Example .wiki-overlay.md Entry

```yaml
source_repos:
  - path: ../my-upstream-lib
    raw_path: evidence/raw/my-upstream-lib
    globs:
      - "*.md"
      - "docs/**/*.md"
```

## Error Handling

- Upstream file deleted → keep local copy (raw is immutable); note in log
- Lint fails on re-ingest → report errors, do not merge, keep change-set open
- Capture reports 0 changed → stop; do not run ingest (nothing to do)
- `gh` unavailable or unauthenticated for `--git` → falls back to error; capture docs instead

## Output

- Updated `evidence/raw/` snapshot (new + changed files only)
- One or more change-sets for re-ingest
- Updated `registry/index.md` after merge