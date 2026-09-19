---
type: index
title: "OKF v0.2 conformance"
description: "The portable knowledge-bundle standard, trust tiers, attested computations"
created: 2026-09-19
updated: 2026-09-19
---

# OKF v0.2: The Fabric Speaks the Standard

OKF (Open Knowledge Format) v0.2 is the interoperability layer: your fabric reads and writes the standard bundle format. Governance stays local; portability is free.

Wiki Fabric is a **conformant OKF v0.2 bundle** — verified by our conformance
linter (`lint --okf`) and the external `okflint` validator. That means any OKF
consumer (Google's Knowledge Catalog, viz.html, Kiso static sites, OpenWiki, Roteiro)
can read your fabric without wiki-fabric tooling — and you can consume theirs.

### Trust & provenance (portable)

```yaml
---
type: claim
statement: "..."
generated: { by: "agent/you/deepseek-v4.1-flash:cloud", at: "2026-09-17T..." }
verified:
  - by: "process:locator-verification"
    at: "2026-09-17T..."
---
```

- **Actors** (§7): `agent/<owner>/<model>` · `human:<id>` · `process:<id>`
- **Trust tiers** (§5.3): every `wf context` manifest item carries
  `trust: human-reviewed > machine-confirmed > unverified` — advisory weighting at task time
- **Promotion gate** (§5.2 + §10): `maturity >= 2` requires a `human:` verifier — lint-enforced

### Attested computations (§10)

Deterministic fabric operations are declared as sanctioned computations with
executors and attesters, so a consumer can confirm a verdict ("recall 0.89 PASS")
was produced the declared way:

```text
global/computations/     # the contracts (runtime, parameters, executor, attester)
references/skills/       # how to run them
references/attesters/    # deterministic receipt checks (no LLM)
```

`promote` refuses to promote without a fresh attestation from the eval computation.

### Exchange

```bash
wf okf export --out ./bundle --scope global   # deterministic portable bundle
wf okf import  ./their-bundle --scope team-a  # external knowledge as immutable evidence
```

Export is byte-deterministic and okflint-conformant. Import records trust tiers
but never inherits them: external concepts land as captures with source records
(kind: okf-bundle), screened for prompt injection, quarantined on suspicion —
and promotion still requires the human-gated pipeline.

---
