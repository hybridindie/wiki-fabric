---
name: refresh
description: Re-capture knowledge-bearing markdown from source repos (defined in .wiki-overlay.md) into global evidence/raw/, re-ingest changed files.
---

# Refresh Skill (Global Architecture)

Re-captures knowledge-bearing markdown from upstream source repos (defined in project's `.wiki-overlay.md`) into global `evidence/raw/<repo>/`, then re-ingests any files whose content hash has changed.

## When to Use

- After upstream work: "refresh my-upstream-lib"
- Scheduled (e.g., weekly)
- When `.wiki-overlay.md` source_repos changes

## Procedure

### 1. Identify Source Repos
Read project's `.wiki-overlay.md` → `source_repos` array.
Each entry has:
- `path`: path to upstream repo (e.g., `../my-upstream-lib`)
- `raw_path`: target under global `evidence/raw/<repo-slug>/`
- `globs`: file patterns to capture

### 2. Capture Knowledge-Bearing Files
For each repo in `.wiki-overlay.md`:
- Copy matching files from `path` to `evidence/raw/<repo-slug>/`
- Preserve directory structure
- Skip directories not matching `globs` (code, build artifacts, .git, etc.)

### 3. Detect Changes
For each captured file:
- Compute new SHA256
- Compare to `evidence/sources/src-<slug>.md` frontmatter `sha256:`
- If different → mark for re-ingest
- If new file (no source record) → mark for new ingest
- If file deleted upstream → keep local copy (raw is immutable); source record status stays `ingested`

### 4. Re-ingest Changed
For each changed/new file:
- Run `ingest` skill on that specific source path
- Each produces its own change-set
- Merge sequentially (or batch if related)

### 5. Log
Append `## [YYYY-MM-DD] refresh | <repo> (<n> changed, <m> new)` to `registry/log.md`.

## Example .wiki-overlay.md Entry

```yaml
source_repos:
  - path: ../my-upstream-lib
    raw_path: evidence/raw/my-upstream-lib
    globs:
      - "*.md"
      - "docs/**/*.md"
  - path: ../another-repo
    raw_path: evidence/raw/another-repo
    globs:
      - "*.md"
      - "docs/**/*.md"
```

## Error Handling

- If upstream file deleted → keep local copy (raw is immutable snapshot); source record status stays `ingested`
- If lint fails on re-ingest → report errors, do not merge, keep change-set open
- If raw copy fails → error, stop

## Output

- Updated `evidence/raw/` snapshot (global)
- One or more change-sets for re-ingest
- Updated `registry/log.md`