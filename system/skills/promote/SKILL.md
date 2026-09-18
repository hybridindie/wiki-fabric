---
type: skill
name: promote
description: Run the promotion pipeline via `mine-promotions.py` + `promote.py` — cluster experience-events deterministically, generate dossiers, human review, merge promoted patterns to patterns/ anti-patterns/ skills/.
---

# Promote Skill

Runs the cross-project promotion pipeline from AGENTS.md:
experience-events → deterministic clustering → dossier → human review → pattern/anti-pattern/skill.

CLI-first: clustering is deterministic (keyword Jaccard, 0 tokens); the LLM
writes/refines the dossier only after the cluster is confirmed; promotion
requires the human gate.

## When to Use

- On demand: "run promotion" / "mine patterns"
- After new experience-events are added to `projects/*/experience-events/`
- Cadence: on demand or weekly — not per edit

## CLI Commands

```bash
# Dry-run the clustering (0 tokens — shows candidate clusters)
python3 scripts/mine-promotions.py --dry-run

# Generate dossiers for confirmed clusters
python3 scripts/mine-promotions.py

# List dossiers, then promote after human review
python3 scripts/promote.py --list
python3 scripts/promote.py --promote <dossier-file>.md
```

## Procedure

### 1. Cluster Experience Events (deterministic)
Run `mine-promotions.py --dry-run`. Clusters form by shared ontology tags,
semantic similarity of `observed_problem` + `intervention`, and causal shape.
Independence rule: two events sharing one lineage count as ONE evidence —
a cluster needs ≥2 independent projects to be promotion-eligible.

### 2. Generate Dossiers
For each confirmed cluster, `mine-promotions.py` creates a dossier in
`registry/promotions/`. Refine it (LLM judgment): verify supporting `[[ee-...]]`
links, conditions, confounding factors, proposed `applicability.includes/excludes`,
counterexamples, and tradeoffs. A dossier generated from placeholders
(`<experience-event-slug>`) needs real links before review.

**If graphify is ACTIVE** (`fabric.yaml` → `integrations.graphify.enabled: true`),
dossiers for code-adjacent patterns should cite graph evidence (call-graph
support for the claimed coupling) via `graphify-bridge.py --enrich` before
review. When graphify is inactive, dossiers rest on experience-event outcomes
alone.

### 3. Update Promotion Queue
Append the candidate to `registry/promotion-queue.md` (pattern, maturity, evidence lineage, dossier link).

### 4. Human Review (mandatory, no auto-promotion)
Present each dossier with the 7-point checklist:
1. Independence: do supporting events share a lineage?
2. Evidence: are claims in `source_refs` entailed by cited locators?
3. Applicability: are `includes`/`excludes` non-vacuous?
4. Counterexamples: listed and acknowledged?
5. Tradeoff: cost/benefit stated?
6. Asset changes: which `patterns/`/`skills/`/`templates/` entries created/updated?
7. Owner: the user — promote only when all pass.

Only the user (or an explicitly governed agent) sets `status: recommended`/`standard`.

### 5. Promote
On approval:
```bash
python3 scripts/promote.py --promote <dossier-file>.md
wf lint
```
This writes `patterns/pattern-<slug>.md` (or `anti-patterns/`, `skills/`) with
`status: recommended`, updates `registry/pattern-index.md`, `registry/skill-index.md`,
`registry/promotion-queue.md`, then one commit:
`git add -A && git commit -m "promote <pattern-id> (maturity N)"`.

### 6. Feedback Loop
Track reuse in the pattern page:
```yaml
usage:
  retrieved_count: 0
  applied_count: 0
  explicit_override_count: 0
  successful_outcomes: 0
  last_validated: <today>
```
A pattern read but never applied is too abstract — narrow or repackage it.

## Error Handling

- Cluster has <2 independent projects → keep as candidate (maturity 1), re-evaluate later
- Lint fails after promotion → rollback, fix, re-promote
- Dossier references missing experience events → fix links before review

## Output

- Dossier(s) in `registry/promotions/`
- Updated `registry/promotion-queue.md`
- On promotion: new pattern/anti-pattern/skill in `patterns/`/`anti-patterns/`/`skills/`, updated indexes, lint pass, one commit