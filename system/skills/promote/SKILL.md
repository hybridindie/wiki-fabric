---
type: skill
name: promote
description: Run the promotion pipeline via `mine-promotions.py` + `promote.py` — cluster experience-events deterministically, generate dossiers, human review, merge promoted patterns to patterns/ anti-patterns/ skills/.
---

# Promote Skill

Runs the cross-project promotion pipeline from AGENTS.md:
experience-events → deterministic clustering (+judged near-miss refinement
when the judgment tier is enabled) → dossier → human review →
pattern/anti-pattern/skill.

CLI-first: clustering is keyword-Jaccard (0 tokens); near-miss pairs get
judged "same recurring pattern?" refinement automatically when
`integrations.judgment` is enabled (`--judge` forces it on, `--no-judge` opts
out); the LLM writes/refines the dossier only after the cluster is confirmed;
promotion requires the human gate.

## When to Use

- On demand: "run promotion" / "mine patterns"
- After new experience-events are added to `projects/*/experience-events/`
- Cadence: on demand or weekly — not per edit

## CLI Commands

```bash
# Dry-run the clustering (0 tokens — shows candidate clusters + judgments)
wf mine promotions --dry-run     # add --judge to force, --no-judge to opt out

# Generate dossiers for confirmed clusters
wf mine promotions

# List dossiers, then promote after human review
wf promote --list
wf promote --promote <dossier-file>.md

# Write usage counts onto pattern pages (deterministic, 0 tokens)
wf utility
```

## Procedure

### 1. Cluster Experience Events (deterministic + judged refinement)
Run `mine-promotions.py --dry-run`. Clusters form by shared ontology tags,
keyword Jaccard of `observed_problem` + `intervention`, and causal shape.
Near-miss pairs are refined by the judgment tier when enabled — the report
names each judged verdict with its probability, and tombstoned/rejected
clusters are suppressed (named in the report; see tombstones in
`patterns/_rejected/` for the rejection reasons).
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

**Compiler gate:** promotion refuses while the current compiler model lacks a
recorded golden-corpus eval (G4). A model swap is a compiler change —
re-evaluate first: `wf eval stability --models <model> --record`.

### 5. Promote
On approval:
```bash
wf promote --promote <dossier-file>.md
wf lint
```
This writes `patterns/pattern-<slug>.md` (or `anti-patterns/`, `skills/`) with
`status: recommended`, updates `registry/catalog.json` (regenerated),
`registry/promotion-queue.md`, then one commit:
`git add -A && git commit -m "promote <pattern-id> (maturity N)"`.

**Protected slow-lane content**: if the cluster's new pattern content differs
from an existing pattern's protected `applicability`/`counterexamples`, the
miner proposes `pattern-<slug>.revision.md` for slow-lane review instead of
overwriting — apply it through the slow-update path (record the
justification in `verified`).

### 6. Rejection → Tombstone Buffer
Reject with a reason (`--reject <dossier> --reject-reason "…"`): the dossier
is retained and a tombstone lands in `patterns/_rejected/`. The miner reads
active tombstones and **suppresses matching clusters** in future runs,
naming the tombstone. Suppressions are reviewable (annotated on the
tombstone) and reversible (`status: inactive`) — the buffer is negative
evidence, not erasure.

```bash
wf gate        # tombstone-suppressed clusters + dossiers awaiting review
```

### 7. Feedback Loop (deterministic)
Run `wf utility` — the receipt↔outcome join reads experience events' receipts
+ outcomes and writes usage counts (`retrieved_count`, `applied_count`,
`successful_outcomes`, `last_validated`) onto pattern/skill pages — 0 tokens,
idempotent. A pattern read but never applied is too abstract — narrow or
repackage it.

## Error Handling

- Cluster has <2 independent projects → keep as candidate (maturity 1), re-evaluate later
- Lint fails after promotion → rollback, fix, re-promote
- Dossier references missing experience events → fix links before review
- Compiler gate refuses → run the G4 eval for the current compiler model
- SLOW-REGION lint error → the pattern's protected content changed without
  justification; review and record the slow-update reason

## Output

- Dossier(s) in `registry/promotions/` (rejected → tombstones in `patterns/_rejected/`)
- Updated `registry/promotion-queue.md`
- Updated usage counts on pattern pages (via `wf utility`)
- On promotion: new pattern/anti-pattern/skill in `patterns/`/`anti-patterns/`/`skills/`, updated indexes, lint pass, one commit
