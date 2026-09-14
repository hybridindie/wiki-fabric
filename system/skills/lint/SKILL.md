---
name: lint
description: Run the deterministic linter via `wf lint` (scripts/lint.py) — validates frontmatter, wikilinks, claims, duplicates, source hashes, orphans. 0-error gate before every commit.
---

# Lint Skill

Runs the deterministic linter. CLI-first: use `wf lint` (or
`python3 scripts/lint.py .`). Zero tokens, always run it before committing.

## When to Use

- After any ingest, capture, or edit batch
- Before every commit (hard gate — never commit with lint errors)
- On demand: "lint the vault" / "check fabric health"

## CLI Commands

```bash
wf lint              # full check (same as: python3 scripts/lint.py .)
wf lint --orphans    # show only orphan warnings
wf lint --hash <path>  # print sha256 of a raw file
```

## Procedure

1. Run `wf lint`
2. If errors > 0: report each error with file + message, fix them, re-run. Do not commit.
3. If warnings > 0: report them; warnings are advisory (orphans etc.), continue.
4. If clean: report "OK — clean", safe to commit.

## What It Checks

Deterministic checks (0 tokens): malformed/missing frontmatter (README.md,
CONTRIBUTING.md, LICENSE, templates/ and schemas/ are exempt), broken wikilinks
(inside `[[...]]`, skipping fenced code), unknown `type:` values, duplicate ids,
claims without `source_refs`, circular `supersedes`, orphan pages, source hash
drift, missing index entries, declared `scope:` vs path-implied scope, and
`review_after` staleness.

**If graphify is ACTIVE** (`fabric.yaml` → `integrations.graphify.enabled: true`),
`python3 scripts/graphify-bridge.py --diff` adds a complementary staleness
signal: code symbols referenced by claims that moved or vanished. This is
outside lint.py (it needs the graph) — run it after lint when active.

## Integration

- `ingest` skill runs it after change-set creation (step 6)
- `promote` skill runs it before committing a promoted pattern
- `wf update` runs it at the end of every update
- Can be run standalone anytime

## Output Format

```
# Lint — wiki-fabric  (pages N, yaml True)
ERROR   <rel>: <message>
WARN    <rel>: <message>
OK — clean
```