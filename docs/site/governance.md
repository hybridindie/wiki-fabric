---
type: index
title: "Governance — the answers, enforced"
description: "The hard questions for agent-maintained knowledge and where the fabric answers them"
created: 2026-09-19
updated: 2026-09-27
---

# Governance: The Answers, Enforced

Agent-maintained knowledge raises hard questions: who verified this? does it
still hold? how do you know the agent followed it? Each answer below points at
the mechanism that enforces it — not a policy sentence. Two terms recur:
**source_refs** — the per-claim citation (source file, locator, verbatim
quote) — and **change-sets** — proposed edits staged for human approval before
they touch canonical pages.


| Question | The fabric's answer | Where it lives |
|----------|--------------------|----------------|
| Does every claim have a source or evidence type? | Claims without `source_refs` can't be `supported`; locators + verbatim quotes mandatory | lint `CLAIM` checks; provenance rules in AGENTS.md |
| What changes when source documents change? | sha256 per capture; hash drift flags exactly which claims are affected; re-ingest produces a change-set, never silent overwrite | lint `SOURCE-DRIFT`; refresh workflow |
| Canonical policy vs. tentative research? | Status taxonomy: `proposed` → `supported` → `contested` → `superseded` → `retracted`; patterns carry maturity 0–3 | frontmatter contracts; lint gates |
| What wins when global and project rules conflict? | Precedence: project > domain > global, enforced at manifest compile time and validated against path scope | `wf context`; lint `SCOPE` |
| How does an agent propose a knowledge mutation? | Change-sets (manifest + diff), staging→canonical flow, human gate before canonical writes | ingest workflow; `apply_changeset.py` (`wf apply-changeset`) |
| Which artifacts require human review? | Pattern promotion (7-point checklist), canonical merges, corpus conflicts (`SYNC-CONFLICT` blocks push) | promotion-queue; sync protocol |
| How do we find stale pages after a dependency upgrade? | `review_after` dates lint-checked, sha256 staleness from capture drift, graphify AST diff flags code changes | lint `REVIEW-AFTER`; `graphify-bridge --diff` |
| Do patterns know where they fail? | `recommended`/`standard` patterns without `counterexamples` warn (boundaries expected); delivered patterns render "does not apply" | lint `PATTERN`; `wf context` |
| Are the locators still true? | `wf review --verify-locators` re-checks every claim's quote against its raw source: rewrite/repair/restore/contest — the verification stamp means something | #111/#130 pass |
| What does the fabric NOT know? | Concept open-questions harvest into gated question pages (open → answered via `answers` relations); surfaced by the gate + query | #88 loop; lint `QUESTION` |

None of these are promises in a README — each is a lint check or workflow gate in CI right now.

## The human gate in practice: one change-set, three commands

The same governance question — "does the agent follow it?" — is answerable
by watching any session's change-set flow. Real outputs from this repo:

```bash
$ wf gate                    # ONE report of everything awaiting a human
gate: nothing pending — fabric is current (HITL queues empty)
# (with work pending it lists stale claims, promotion dossiers,
#  domain proposals, open change-sets — each with its deadline)

$ wf apply-changeset <slug> --dry-run    # inspect BEFORE anything canonical
Pages to create: 2
[DRY RUN] Would apply git apply: .../change-sets/.../diff.md
[DRY RUN] no changes written

$ wf lint                    # the 0-error gate before any commit
0 error(s), 6314 warning(s)  # warnings are advisory; errors fail the commit
```

### The scoped auto-promote exception (#190)

The human gate is absolute for dossiers, claims, domains, and questions. For
**inbox pattern candidates** — the trivially-promotable class — a fabric may
opt into the judged-confident tier:

```yaml
tuning:
  promotion:
    auto_apply: true         # OFF by default — a policy change must be explicit
    auto_threshold: 0.90     # calibration-sensitive: overrides travel with provenance (G-J)
```

`wf promote-patterns --auto` then bands each candidate: deterministic
preconditions first (candidate type, complete provenance, age ≥ 1d, no
judged-different verdict — one refusal means the human), then ONE calibrated
judgment call. `p ≥ auto_threshold` applies (the same deterministic move,
stamped `auto_applied: {judge, prob, at}` and logged — reversible with
`promote-patterns --unapply`); the near-band below the floor escalates to the
human gate; further below stays in the inbox with the verdict recorded. The
gate's `auto-applies` INFO section lists recent applies (never actionable
alone) — auto-promote downgrades rows, it never silences the gate. The judge
proposes, never writes: the apply is a file move, the candidate text is
untouched.

`wf skill ingest` / `wf skill promote` print the full agent-facing
procedures — so any harness (Claude Code, opencode, Codex) runs the same
governed loop without the human dictating steps each time.
