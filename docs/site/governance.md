---
type: index
title: "Governance — the answers, enforced"
description: "The hard questions for agent-maintained knowledge and where the fabric answers them"
created: 2026-09-19
updated: 2026-09-19
---

# Governance: The Answers, Enforced

Agent-maintained knowledge raises hard questions: who verified this? does it still hold? how do you know the agent followed it? Each answer below points at the mechanism that enforces it — not a policy sentence.

The hard questions for agent-maintained knowledge — with where the fabric answers them:

| Question | The fabric's answer | Where it lives |
|----------|--------------------|----------------|
| Does every claim have a source or evidence type? | Claims without `source_refs` can't be `supported`; locators + verbatim quotes mandatory | lint `CLAIM` checks; provenance rules in AGENTS.md |
| What changes when source documents change? | sha256 per capture; hash drift flags exactly which claims are affected; re-ingest produces a change-set, never silent overwrite | lint `SOURCE-DRIFT`; refresh workflow |
| Canonical policy vs. tentative research? | Status taxonomy: `proposed` → `supported` → `contested` → `superseded` → `retracted`; patterns carry maturity 0–3 | frontmatter contracts; lint gates |
| What wins when global and project rules conflict? | Precedence: project > domain > global, enforced at manifest compile time and validated against path scope | `wf context`; lint `SCOPE` |
| How does an agent propose a knowledge mutation? | Change-sets (manifest + diff), staging→canonical flow, human gate before canonical writes | ingest workflow; `apply-changeset.sh` |
| Which artifacts require human review? | Pattern promotion (7-point checklist), canonical merges, corpus conflicts (`SYNC-CONFLICT` blocks push) | promotion-queue; sync protocol |
| How do we find stale pages after a dependency upgrade? | `review_after` dates lint-checked, sha256 staleness from capture drift, graphify AST diff flags code changes | lint `REVIEW-AFTER`; `graphify-bridge --diff` |

None of these are promises in a README — each is a lint check or workflow gate in CI right now.

---

---

Next: [The machine-readable surface for these answers](./machine-contract)
