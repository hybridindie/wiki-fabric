---
name: promote
description: Run the promotion pipeline — cluster experience-events, generate promotion dossiers, present for human review, merge promoted patterns/anti-patterns to global/.
---

# Promote Skill

Runs the cross-project promotion pipeline from AGENTS.md: experience-events → clustering → dossier → human review → global pattern/anti-pattern/skill.

## When to Use

- Scheduled (weekly) or on demand: "run promotion"
- After new experience-events are added to `projects/*/experience-events/`

## Procedure

### 1. Cluster Experience Events
- Read all `projects/*/experience-events/*.md`
- Group by shared:
  - Semantic similarity of `observed_problem` + `intervention`
  - Shared ontology tags (`agent`, `threading`, `godot`, `benchmark`, etc.)
  - Similar causal structure (problem → intervention → outcome)
  - Explicit links from retrospectives to candidate pattern

### 2. Generate Promotion Dossiers
For each cluster, create `registry/promotions/<date>-<slug>/dossier.md`:
- **Candidate pattern** (link to proposed `global/patterns/pattern-<slug>.md` or anti-pattern)
- **Supporting experiences** — list of `[[ee-...]]` with outcomes
- **Shared conditions** — what must be true for pattern to apply
- **Confounding factors** — differences that may limit generality
- **Proposed boundary** — `applicability.includes` / `excludes`
- **Proposed asset changes** — new global pattern, updated skill, updated template, new anti-pattern
- **Required review** — human owner (you), 7-point checklist from `registry/promotion-queue.md`

### 3. Update Promotion Queue
Append to `registry/promotion-queue.md`:
| Pattern | Maturity | Evidence lineage | Dossier |
|---|---|---|---|
| [[pattern-<slug>]] | 2 (replicated) | 2 independent projects | [[promotion-<slug>]] |

### 4. Human Review
Present each dossier with the 7-point checklist:
1. Independence: do supporting events share a lineage?
2. Evidence: are claims in `source_refs` entailed by cited locators?
3. Applicability: are `includes`/`excludes` non-vacuous?
4. Counterexamples: listed and acknowledged?
5. Tradeoff: cost/benefit stated?
6. Asset changes: which `global/` entries created/updated?
7. Owner: you — promote only when all pass.

### 5. Promote
On approval:
- Write `global/patterns/pattern-<slug>.md` (or anti-pattern) with `status: recommended`, `maturity: 2`
- Write `global/skills/<slug>.md` + `global/templates/<slug>.md` if asset changes include skill/template
- Update `registry/pattern-index.md`, `registry/skill-index.md`, `registry/promotion-queue.md`
- Run `python3 scripts/lint.py .` — must pass
- Commit: `git add -A && git commit -m "promote <pattern-id> (maturity N)"`

### 6. Feedback Loop
For promoted patterns, track in the pattern page:
```yaml
usage:
  retrieved_count: 0
  applied_count: 0
  explicit_override_count: 0
  successful_outcomes: 0
  last_validated: <today>
```

## Output

- New dossier(s) in `registry/promotions/`
- Updated `registry/promotion-queue.md`
- On promotion: new global pattern/anti-pattern/skill/template, updated indexes, lint pass, commit

## Error Handling

- No auto-promotion — human gate is mandatory
- If cluster has <2 independent projects → keep as candidate (maturity 1), re-evaluate later
- If lint fails after promotion → rollback, fix, re-promote