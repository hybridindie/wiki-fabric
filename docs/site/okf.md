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

#### Writing provenance: the actor convention

Every page's `generated.by` (and every `verified.by`) records *who* produced
it, in one of three forms — lint rejects anything else:

| Form | When your tooling writes it | Example |
|------|----------------------------|---------|
| `agent/<owner>/<model>` | an LLM produced the content — name the model that did | `agent/hybridindie/deepseek-v4.1-flash:cloud` |
| `human:<id>` | a person wrote or verified it | `human:jane` |
| `process:<id>` | deterministic tooling (hooks, CI, attesters) — model-independent by design | `process:locator-verification` |

The `<owner>` in agent actors is the fabric `owner` (fabric.yaml). Practical
rules for agent authors:

- Claim pages minted by extraction carry the compiler model — that's the
  audit trail for "which model asserted this".
- Pages a human edited by hand get `verified: [{by: human:<id>, at: ...}]`
  added — that's what pushes trust tier to `human-reviewed` and what the
  maturity gate requires at maturity ≥ 2.
- Never fake a `process:` actor for LLM output; the tier system only means
  something if actors are honest.
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
wf okf export --out ./bundle [--scope all|global|<project|domain-slug>]
wf okf import  ./their-bundle --scope team-a [--extract-claims]
```

#### Export: your fabric as a portable bundle

`export` renders the fabric (or one scope's slice of it) as a directory of
markdown + frontmatter that any OKF consumer can read. It is **byte-deterministic**
— same fabric state, same bytes — and validated by the external `okflint`
validator in CI, so a bundle from anyone is checkable without wiki-fabric.

| Scope | Exports |
|-------|---------|
| `all` (default) | everything the fabric owns |
| `global` | patterns, anti-patterns, skills, entities, principles |
| `<project-slug>` | that project's claims, experience events, decisions |
| `<domain-slug>` | that domain's concepts, questions, syntheses |

Wikilinks are rewritten to travel inside the bundle (dangling links don't ship).
Raw captures ride along under `references/` (OKF §6.3: external material
mirrors verbatim, never becomes a concept).

#### Import: external knowledge as *quarantined evidence*

`import` never writes concepts directly into your fabric. Each imported page
becomes a **raw capture** (`evidence/raw/<scope>-okf/`) with a source record
(`kind: okf-bundle`), so it enters through the same compile pipeline as any
other external document:

1. **Injection screen** — deterministic scan for zero-width characters,
   control characters, and directive patterns ("ignore previous instructions",
   "system prompt", ...). Hits are **quarantined** to
   `evidence/_inbox/<scope>-okf/` for human review, never silently ingested.
2. **Trust recorded, not inherited** — each page carries
   `imported_trust_tier` (`human-reviewed` / `machine-confirmed` /
   `unverified`) computed from *its* `verified` fields. The tier is
   metadata for your weighting — it grants nothing.
3. **Promotion still gated** — imported concepts become canonical only via
   the human-gated pipeline (capture → ingest → change-set → lint → merge).
   With `--extract-claims`, the compiler runs on the imported material
   immediately (honoring per-scope routing).

```bash
# Consume a team bundle and compile it
wf okf import ~/bundles/team-a --scope team-a --extract-claims
```

Use cases: consuming another team's curated fabric, archiving a fabric snapshot,
feeding a curated external corpus (e.g. vendor docs someone exported) through
your governance instead of around it.

---

---

Next: [The contract surface CI consumes](./machine-contract)
