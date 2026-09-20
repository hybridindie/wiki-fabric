---
type: index
title: "Task Context — deterministic context assembly"
description: "How wf context compiles scoped, reasoned manifests"
created: 2026-09-19
updated: 2026-09-19
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

---

---

Next: [Full command reference](./cli)
