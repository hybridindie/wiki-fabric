---
type: index
title: "How It Works: Trust, Freshness & Governance"
description: "How the fabric stays trustworthy when agents write most of it"
created: 2026-09-20
updated: 2026-09-20
---

# How It Works: Trust & Governance

An agent-maintained knowledge base has a hard question at its center: if
agents write most of the pages, why would you trust any of it? Wiki Fabric's
answer is to make every trust claim *machine-checkable* — this page walks
through the mechanisms.

## Provenance: every statement carries its receipt

A claim without a citation can't be `supported` — lint refuses it. The
receipt has three parts: which **source file**, which **locator** (exact
lines), and the **verbatim quote**. The quote is verified against the source
text deterministically, so "the model asserted this" and "the source actually
says this" are separate, auditable facts.

## Actors: the audit trail

Every page records who produced it:

- `agent/<owner>/<model>` — an LLM wrote it; the model that did is in the
  actor string, because extraction quality is capability-correlated and model
  swaps change the evidence's character
- `human:<id>` — a person wrote or verified it; this is what lifts trust tier
- `process:<id>` — deterministic tooling (hooks, locator verification,
  attesters); model-independent by design

The rule that makes the system honest: never fake a `process:` actor for LLM
output. The tiers only mean something if the actors are honest.

## Freshness: three declarations, one linter

Pages carry **`review_after`** (a human should re-check this by a date) and
**`stale_after`** (a machine gate: don't trust after this instant). Overdue
pages don't just get noted — `wf context` *filters them out of manifests*, and
lint escalates from warning to error as the debt grows. Source-level drift is
separate: capture's sha256 catches a dependency's docs changing under existing
claims, and the graphify AST diff catches renames invalidating code-referencing
claims.

## The compiler-eval gate

Why can't you just swap in a better model? Because the fabric's canonical
evidence is *compiled by* the compiler model — swap it and every claim's
character changes. So `promote.py` and `mine-promotions.py` refuse to run
unless `registry/log.md` contains a recorded eval naming the current compiler
model. Model swaps are compiler changes; compiler changes require
re-evaluation. That's the G4 lesson enforced as a hard gate instead of a docs
sentence.

## Attested computations: proving the verdict

Deterministic fabric operations can be declared as **attested computations**
(OKF §10): the contract states the runtime, parameters, executor, and
attester. A run produces a receipt; the attester — deterministic, no LLM —
confirms the run was produced the declared way. This is how "recall 0.89
PASS" becomes checkable: the receipt proves the value was produced the
sanctioned way, per call, never stored in the bundle.

## What happens when trust fails

The linter is loud by design: broken links and unsupported claims are errors;
orphans and overdue reviews are warnings that surface in `wf status`. When
external content arrives via `wf okf import`, a deterministic screen checks
for injection patterns and quarantines suspicion to `evidence/_inbox/` —
external knowledge enters as evidence to compile, never directly as truth.

Next: [CLI & Scripts Reference](./cli)
