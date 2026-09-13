---
type: registry
title: Contributing to Wiki Fabric
updated: 2026-09-11
---
# Contributing to Wiki Fabric

> **The fabric is a compiler, not a wiki.** We maintain the *compiler* (the agent that maintains the wiki), not just the artifacts.

---

## How to Contribute

### 1. Ingest a New Source

```bash
# 1. Place raw file in evidence/raw/<repo>/<file>.md
# 2. Compute hash
sha256sum evidence/raw/<repo>/<file>.md

# 3. Create source record
# evidence/sources/src-<slug>.md
# - type: source
# - sha256: <hash>
# - source_path: evidence/raw/<repo>/<file>.md
# - summary: "[[sum-<slug>]]"

# 4. Write faithful summary
# evidence/source-summaries/sum-<slug>.md
# - type: source-summary
# - source: "[[src-<slug>]]"
# - faithful, locator-rich, NO inference

# 5. Extract claims (atomic, one per page)
# evidence/claims/claim-<slug>.md
# - type: claim
# - id: claim-<slug>
# - statement: "..."
# - source_refs with locator + quote
# - status: proposed|supported|contested|superseded|retracted

# 6. Open change-set
# evidence/traces/change-sets/<date>-<slug>/
#   - manifest.md (sources+hashes, pages, new claims, contradictions)
#   - diff.md (unified diff)

# 7. Lint → Human gate → Merge → Log → Commit
python3 scripts/lint.py .
```

### 2. Run Evaluation Fixtures

```bash
# In a sandbox copy:
cp -r evaluations/fixtures/source-a.md evidence/_inbox/
# Run ingest skill on it
# Verify against evaluations/expected/claims.yaml
# Run golden questions per evaluations/questions.yaml
# Score per evaluations/rubric.md
```

### 3. Promote a Pattern

```bash
# 1. Run promote skill (clusters experience-events → dossiers)
# 2. Review dossier against 7-point checklist:
#    1. Independence: no shared lineage
#    2. Evidence: locators entailed
#    3. Applicability: non-vacuous includes/excludes
#    4. Counterexamples: listed
#    5. Tradeoff: cost/benefit stated
#    6. Asset changes: which global/ entries
#    7. Owner review
# 5. On approval: write global/patterns/..., update indexes, lint, commit
```

### 3. Add a Skill

```bash
mkdir -p .opencode/skills/<skill-name>
# Create SKILL.md with:
# ---
# name: <name>
# description: <when to use>
# ---
# # Procedure
# ...
```

---

## Code Style

- **Markdown only** — no HTML in content
- **Wikilinks** `[[stem]]` for internal links
- **Frontmatter first** — every page starts with YAML
- **Locators required** — every claim needs `locator` + `quote`
- **4-space indent** — Python/scripts use 4 spaces
- **No tabs** — spaces only

---

## Git Discipline

- **One ingest = one commit** — message: `ingest <change-set-slug> (raw <sha8>)`
- **One promotion = one commit** — message: `promote <pattern-id> (maturity N)`
- **Never rewrite history** — the log is the history
- **Raw is immutable** — never edit `evidence/raw/` in place; re-capture on refresh

---

## Lint Before Commit

```bash
python3 scripts/lint.py .  # must be 0 errors
```

---

## Evaluation Discipline

Before changing the compiler (agent prompts, ingest logic, skills):

1. Run full evaluation suite on sandbox copy
2. Must not drop below prior run on any metric
3. Record scores in `registry/log.md`

---

## Versioning

- **Fabric structure**: CalVer `YYYY.MM.DD`
- **Skills/patterns**: semantic `x.y.z` in frontmatter `version:`
- **Schemas**: bump minor on additive, major on breaking

---

## Questions?

Read `AGENTS.md` (master schema) or `schemas/frontmatter.md` (contracts) first. The fabric is self-documenting — if something isn't clear, that's a bug in the fabric.