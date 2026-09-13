---
name: lint
description: Run deterministic linter (scripts/lint.py) — validates frontmatter, wikilinks, claims, duplicates, source hashes, orphans, pattern maturity gates.
---

# Lint Skill

Runs the deterministic linter (`scripts/lint.py`) and reports results.

## When to Use

- After any ingest or edit batch
- Before committing
- On demand: "lint the vault"

## Procedure

1. Run `python3 scripts/lint.py .`
2. If errors > 0:
   - Report each error with file + message
   - Stop; do not proceed to commit
3. If warnings > 0:
   - Report warnings (orphans, pattern maturity <2, etc.)
   - Continue; warnings are advisory
4. If clean:
   - Report "OK — clean"
   - OK to proceed to commit

## Sub-commands

- `lint` — full check (errors + warnings)
- `lint --orphans` — show only orphan warnings
- `lint --hash <path>` — print sha256 of a raw file

## Output Format

```
# Lint — vault  (pages N, yaml True)
ERROR   <rel>: <message>
WARN    <rel>: <message>
OK — clean
```

## Integration

- Called automatically by `ingest` skill after change-set creation
- Called by `promote` skill before merging promoted pattern
- Can be run standalone anytime