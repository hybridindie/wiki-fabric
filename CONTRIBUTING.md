# Contributing to Wiki Fabric

> **The fabric is a compiler, not a wiki.** We maintain the *compiler* (the agent that maintains the wiki), not just the artifacts.

---

## How to Contribute

> Prefer the CLI over the manual recipe below: `wf bootstrap`, `wf capture`,
> `wf ingest`, `wf query`, `wf log` automate most of this. The manual flow is
> documented for understanding and for when the CLI is unavailable.

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
wf lint
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
# 3. On approval: write patterns/<slug>.md, update indexes, lint, commit
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
- **Import shared modules, don't copy them** — `fabric_config.py`,
  `extract_backends.py`, `wf_common.py`, `eval_core.py`, `local_llm.py` are
  the canonical homes for config, extraction, frontmatter parsing, eval
  scoring, and on-device generation. A local copy of one of these helpers is
  a bug waiting to drift (tests guard the import shape).

---

## Git Discipline

- **One ingest = one commit** — message: `ingest <change-set-slug> (raw <sha8>)`
- **Log entries in OKF §9 shape** — `## YYYY-MM-DD` heading + `* **<op> | <subject>**` bullets
- **One promotion = one commit** — message: `promote <pattern-id> (maturity N)`
- **Never rewrite history** — the log is the history
- **Raw is immutable** — never edit `evidence/raw/` in place; re-capture on refresh

---

## Lint Before Commit

```bash
wf lint            # must be 0 errors (full profile — the ceiling)
wf lint --okf      # must be conformant (OKF v0.2 floor — CI-gated)
```

The default profile enforces fabric invariants (locators, maturity gates, hash
anchors). The `--okf` mode is the OKF v0.2 §11 conformance floor; external
`okflint validate --manifest okf-base.yaml` cross-checks it in CI.

## Tests

Run before changing any script:

```bash
python3 -m pytest tests/ -q                # full suite
python3 -m pytest tests/ -m "not live" -q  # fast: skips on-device model tests
bash scripts/smoke-test.sh                 # end-to-end CLI checks (isolated temp fabric)
```

Tests marked `live` run real on-device models (GGUF/MLX); they self-skip when
the model isn't cached or the platform lacks the backend. CI enforces the fast
suite plus `python3 -m py_compile` on every script. A PR that fails
`smoke-test.sh` or drops unit tests below passing will not merge.

---

## Evaluation Discipline

Before changing the compiler (agent prompts, ingest logic, skills):

1. Run full evaluation suite on sandbox copy
2. Must not drop below prior run on any metric
3. Record scores in `registry/log.md`

---

## Versioning (alpha reality)

- **The project is pre-1.0.** No stable release exists; do not treat any version as a stability promise.
- **Package version** (`pyproject.toml`): `0.x.y` — bumped on notable changes, resets allowed while alpha.
- **Fabric structure**: changes freely; no version contract until 1.0.
- **Skills/patterns**: `x.y.z` in frontmatter `version:` if you want per-page tracking (optional).
- **Releases**: none yet. When a first tagged release lands, it will be `0.1.0`, not 1.0 — 1.0 is reserved for a stable, documented, tested public contract.

---

## Questions?

Read `AGENTS.md` (master schema) or `schemas/frontmatter.md` (contracts) first. The fabric is self-documenting — if something isn't clear, that's a bug in the fabric.