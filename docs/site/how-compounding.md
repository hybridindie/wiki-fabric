---
type: index
title: "How It Works: The Compounding Loop (experience → pattern)"
description: "How one project's failure becomes every project's guardrail"
created: 2026-09-20
updated: 2026-09-20
---

# How It Works: The Compounding Loop

The compile pipeline turns sources into knowledge. The compounding loop turns
*experience* into rules — and it's the part that makes the fabric more
valuable every month you use it.

## Step 1: The honest record

After real work, you (or the agent) log an **experience event**:

```bash
wf log --project auth-service \
  --problem "Risk agent had redundant checks" \
  --intervention "Consolidated 3 checks into 1 validator" \
  --outcomes "150ms→23ms latency"
```

Three fields: what went wrong, what you did, what measurably happened. That's
the entire ceremony — and it's deliberately cheap, because capture that costs
effort doesn't happen.

## Step 2: Deterministic mining

`mine-promotions.py` clusters experience events across projects by concept
overlap — keyword Jaccard, no LLM. When the same pattern of
problem → intervention → outcome shows up in **two or more independent
projects**, it stops being one team's anecdote and becomes a candidate rule.

## Step 3: The dossier

Each cluster becomes a **promotion dossier**: the evidence, the conditions
where it held, the boundary where it stopped applying, and the counterexamples.
This is the document a human reviews — it must answer seven questions
(independence, evidence, applicability, counterexamples, tradeoffs, asset
changes, owner review) before anything moves.

## Step 4: The human gate

Promotion is never automatic. A human approves, and the pattern's status moves
`candidate → recommended` — which lint only allows at **maturity ≥ 2**
(observations from ≥2 independent codebases). Nothing reaches `standard`
without a named human verifier. The machine proposes; people bless.

## Why independence is the whole trick

Two projects observing the same failure is evidence. One project's doc copied
to another repo is not — it's the same observation wearing a different
path. The independence rule is what keeps a plausible-sounding rule from
being blessed by a single bad experience echoed twice.

## What compounding looks like

Session one on project five: bootstrap discovers the overlay, the fabric
loads the global fabric plus this project's context — and the agent already
knows the three patterns promoted from your other projects. Nobody pasted
anything. Session forty on project nine inherits all of it. That's the bet:
**an LLM is a good compiler but an unreliable memory** — so the fabric stores
structured, source-anchored claims and spends tokens only where judgment is
needed.

Next: [How It Works: Trust & Governance](./how-trust)
