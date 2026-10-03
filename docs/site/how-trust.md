---
type: index
title: "How It Works: Trust, Freshness & Governance"
description: "How the fabric stays trustworthy when agents write most of it"
created: 2026-09-20
updated: 2026-09-27
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

## The judgment gate (G-J): only a calibrated judge proposes

The same lesson applies to the judgment tier — and it matters more, because a
judge that cannot separate truth from noise doesn't just degrade quality, it
silently reshapes proposals (cluster merges, effect verdicts, borderline
promotions). So:

- `scripts/eval/eval-judgment.py --record` calibrates the CURRENT judge
  against separation + mining-spread fixtures (positives ≥ 0.7 / negatives
  ≤ 0.4 / spread ≥ 0.3; paraphrase pairs ≥ 0.9 / unrelated ≤ 0.7 — the 0.8
  mining threshold must sit strictly between). Declared as
  `global/computations/ac-judgment-eval.md`; attested by
  `references/attesters/check-judgment-eval.py`.
- Every judgment call site (mine-promotions clustering + incoherence sweep,
  verify-effects, context borderline re-rank) checks the gate FIRST: no PASS
  receipt for the current judge identity (`judge_kind`, model id) → the
  deterministic keyword/lexical result stands, loudly. A judge swap is a
  judgment change — recalibrate before the tier proposes again.
- The off switch is explicit and logged: `WIKI_JUDGE_GATE=0` skips the check
  (returns "G-J gate SKIPPED") — overrides are visible in output, never
  silent.

Judgment still never writes content; the G-J gate adds the missing half: it
can't even *propose* until its calibration is on record (`wf eval behavior
--judge` is the CI probe; the calibration eval is the model-identity gate).

## Newest-wins: contradiction-based staleness (#175)

Time-staleness is the ladder (`review_after` per capture kind). The OTHER
staleness axis is contradiction: a claim a newer supported claim refutes
shouldn't keep riding as `supported`. The sweep mechanizes it — Graphiti's
newest-wins invariant, git-native:

```bash
wf review --contradiction-sweep          # demote/restore; exit 1 when a demotion lands
wf review --demoted                      # the demoted set
wf review --restore-demoted <claim-id>   # hand-restore (the stamp clears)
```

Carriers are proposals only — a hand-declared `contradicts` relation, or
`registry/effects/` verdicts from `verify-effects` (G-J-gated upstream).
The DECISION is deterministic: the pair's OLDER member loses to the newer
one; equal clocks skip (same-batch reads stay human-owned); the
contradictor must still be `supported` — when IT loses support, the demoted
claim restores automatically on the next sweep. The stamp
(`contradicted-by:` + `status: contested` + `stale_after`) is provenance,
not deletion — the demoted claim keeps its quote and locator.

## Attested computations: proving the verdict

Deterministic fabric operations can be declared as **attested computations**
(OKF §10): the contract states the runtime, parameters, executor, and
attester. A run produces a receipt; the attester — deterministic, no LLM —
confirms the run was produced the declared way. This is how "recall 0.89
PASS" becomes checkable: the receipt proves the value was produced the
sanctioned way, per call, never stored in the bundle.

## Locator verification: the stamp means something

The `process:locator-verification` stamp is applied at extraction (quote
verified against the raw source) and re-checked mechanically:

```bash
wf review --verify-locators   # 0 tokens, deterministic
```

For every claim: the full quote must sit inside the recorded locator's
span. Outcomes: **kept** (stamp stays), **fixed** (locator rewritten to the
tightest containing span), **repaired** (backtick-elision quotes refilled
from the source), **restored** (a previously-contested quote now verifies →
status + stamp back), **contested** (quote vanished from the source → stamp
stripped, status `contested` — the evidence no longer supports it as
written). Each outcome prints; the corpus's grounding is auditable with one
command.

## What happens when trust fails

The linter is loud by design: broken links and unsupported claims are errors;
orphans and overdue reviews are warnings that surface in `wf status`. When
external content arrives via `wf okf import`, a deterministic screen checks
for injection patterns and quarantines suspicion to `evidence/_inbox/` —
external knowledge enters as evidence to compile, never directly as truth.

---

## Slow-lane protection: negative knowledge is durable

Pattern pages accumulate the hard-won "this does NOT apply" boundaries —
`applicability.excludes` and `counterexamples`. Those fields are **protected
slow-lane content**: lint fails (`SLOW-REGION`) any change to them that
arrives without a slow-update justification, the way ingest-driven rewrites
would. Only the human review path records the justification. Mining respects
the same gate — when its new pattern content differs from an existing
pattern's protected content, it proposes a revision for re-review rather than
overwriting. This is the fabric's content-level analogue to trust tiers:
trust is *who verified*, slow-lane is *what may not silently change*.

Next: [Staying in Sync (Hooks & CI)](./how-sync)
