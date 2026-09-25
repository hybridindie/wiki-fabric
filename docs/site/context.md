---
type: index
title: "Task Context — deterministic context assembly"
description: "How wf context compiles scoped, reasoned manifests"
created: 2026-09-19
updated: 2026-09-25
---

# Task Context: Deterministic Context Assembly

This page is the deep-dive on the command the whole loop feeds: after you capture → ingest → query ([Core Workflows](./core-workflows)), `wf context` is what the agent actually receives before writing code.

Before an agent starts work, compile exactly the knowledge it needs — no
recursive filesystem scanning, no dumping the whole corpus, no LLM retrieval:

```bash
wf context --task "Add token rotation to the OAuth service" --paths services/auth
```

## What the manifest guarantees

Output is a **context manifest** with three properties:

1. **Scoped by precedence** — project decisions (highest) → domain patterns →
   global policies. Conflicts resolve top-down; the agent cites the artifact it followed.
2. **Explainable by construction** — every selected item carries a reason
   (`project match: auth-service`, `domain match: oauth, rotation`, `global pattern match: token`).
   Every *excluded* item carries a reason too (`superseded`, `stale: review_after overdue 255 days`,
   `beyond --max`).
3. **Deterministic, 0 tokens** — pure string ops over the corpus. Same task,
   same manifest. Honors `--project` pinning, `--paths` code-path hints,
   `--max`, and `--format json` for harnesses.

```markdown
## Selected

### Project (highest precedence)
- [[decision-rotation]] — *project match: auth-service*

### Domain
- [[concept-rotation]] — *domain match: oauth, rotation*

### Global
- [[pattern-token-rotation]] — *global pattern match: oauth, token*

## Excluded
- `patterns/pattern-old-writer.md` — superseded
- `patterns/pattern-stale.md` — stale: review_after overdue 255 days
```

This is the payoff of the scope model: `global/` + `domains/` + `projects/`
are not filing categories — they are the priority layers of task-time context
assembly, enforced by the P1 contract (SCOPE, REVIEW-AFTER, status filters).

## Boundary: knowledge vs. live evidence

The manifest deliberately contains **knowledge and policy only** — not code
slices, diffs, test output, or task working state. That's a design decision,
not a gap:

- **Live evidence is the harness's job.** The agent already reads code, runs
  tests, and holds its own working state. Duplicating that here would make the
  manifest stale the moment a file changes and would couple the fabric to one
  harness's notion of "current".
- **Determinism depends on the boundary.** `wf context` is 0-token, pure
  string ops over the corpus. Live evidence is per-session and volatile; the
  manifest stays stable and re-runnable.
- **Structure is available when needed.** Call-graph neighborhoods and symbol
  proximity (via the optional Graphify integration) can inform *which* claims
  are selected — but the code itself is delivered by the harness, not embedded
  in the manifest.

The manifest answers "what does the fabric know that the agent must be told
before writing code?" Everything else — RAM, diffs, working state — is the
runtime's half of the memory/context split.

## Commitments: prospective memory at task time

Open **commitments** (type `commitment`, `status: open` — a deferred
obligation like "after the schema migration passes, update the contract
test") surface in the manifest when their `trigger` plausibly matches the
task, at **P1-project** precedence: a pending obligation binds the current
task like a decision does. The reason reads `prospective match: <tokens>`,
and an overdue `due` date adds a warning. `done`/`cancelled` commitments are
excluded — completed obligations don't bind future work. See
[schemas/frontmatter.md](https://github.com/hybridindie/wiki-fabric/blob/main/schemas/frontmatter.md)
for the contract.

## Receipts: make delivery auditable

Add `--write-receipt` to persist the manifest as a **context receipt**
(`wiki-fabric/receipt-v1`):

```bash
wf context --task "Add token rotation to the OAuth service" --write-receipt
# stderr: receipt: <fabric>/registry/receipts/receipt-3f9c2b1a77d0.json (receipt-3f9c2b1a77d0)
```

- The receipt is the full manifest payload + provenance fields, written to
  `projects/<p>/receipts/` (pinned) or `registry/receipts/` (unpinned).
- Its id is derived from the manifest content — same corpus + task gives the
  same id, so re-runs overwrite in place and are byte-identical.
- The receipt path goes to stderr; the manifest on stdout is unchanged.
- `wf lint` validates the envelope (`RECEIPT` code); behavior eval `be5`
  proves delivery through a persisted receipt.

---

---

Next: [Full command reference](./cli)
