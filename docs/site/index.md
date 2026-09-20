---
layout: home

hero:
  name: 'Wiki Fabric'
  text: 'Git-native knowledge governance for AI coding agents'
  tagline: Project memory that is scoped by precedence, traceable to evidence, enforced by CI — and provably delivered before an agent writes code.
  actions:
    - theme: brand
      text: Why Wiki Fabric
      link: ./why
    - theme: alt
      text: Getting Started
      link: ./getting-started
    - theme: alt
      text: GitHub
      link: https://github.com/hybridindie/wiki-fabric

features:
  - title: Compiles sources into verified claims
    details: LLM extracts atomic assertions with line-level locators and verbatim quotes. Provenance is mandatory — lint refuses claims without sources.
  - title: Promotes patterns with measured maturity
    details: Experience events are deterministically clustered into dossiers. Promotion requires ≥2 independent projects and human review.
  - title: Enforces scope precedence at task time
    details: wf context compiles project decisions > domain patterns > global policies into a manifest where every inclusion and exclusion carries a reason.
  - title: Measures behavior, not vibes
    details: Behavior evals verify the knowledge actually changes agent decisions. The compiler has its own golden-corpus eval. CI fails on regression.
---

## The problem, in one paragraph

When you ask an AI coding agent to build something, it starts from zero
knowledge about *your* project every session. It doesn't know that your team
already tried a shared token cache last year and it caused a security incident.
It doesn't know the auth service made a binding decision to use rotating
refresh tokens. It doesn't know which of your conventions are rules versus
suggestions. So it guesses — confidently — and you either review every line it
writes or you get burned. Traditional wikis and notes apps don't fix this,
because nothing forces the agent to *read* them, and nothing proves what it
read actually changed its behavior.

## The proof in one session

Here is the entire value proposition, runnable in 30 seconds with no install:

```bash
bash scripts/demo.sh
```

The demo does four things:

**1. Builds a tiny fabric.** Three short markdown files — the kind of
knowledge every team already has but never structures:

- A **pattern**: "Rotate tokens on refresh" — a rule learned from real work,
  with the evidence behind it
- An **anti-pattern**: "Do NOT build a shared token cache" — a failure mode
  observed in **two independent projects**, with the measured outcome and the
  misleading fix called out ("just add a TTL" doesn't prevent cross-session
  reuse)
- A **project decision**: "The auth service uses rotating refresh tokens" —
  binding for that one service, with the rationale
- An **experience event**: the raw "what happened when we tried it" record the
  anti-pattern was mined from

**2. Asks the agent's question.** A task goes in: *"Add token refresh to the
auth service."* Out comes a **context manifest** — a deterministic, 0-token
compilation of exactly the knowledge that task needs:

```text
## Selected

### Project (highest precedence)
- [[decision-rotation-over-sessions]] — project match: auth-service
- [[ee-shared-cache-bleed]] — project match: auth-service

### Global
- [[anti-pattern-shared-token-cache]] — global pattern match: token
- [[pattern-token-rotation]] — global pattern match: refresh, token

## Excluded
- `patterns/pattern-superseded.md` — superseded
- `patterns/pattern-stale.md` — stale: review_after overdue 255 days
```

Every inclusion carries a **reason** (`project match: auth-service`). Every
exclusion carries one too — a superseded page is filtered out *before* it can
mislead, and a page overdue for review is dropped rather than trusted.

**3. Shows what the LLM would actually receive.** The manifest compiles into
the agent's prompt — the banned approach is named *before any code exists*:

```text
## [BINDING DECISION] Auth service uses rotating refresh tokens,
## not session extension
Reason: project match: auth-service
Session-extension proposals should be redirected.

## [DO NOT] Shared token cache across service instances
Reason: global pattern match: add, the, token
**Observed failure** (2 independent projects): ... caused cross-session
token bleed and audit failures.
**Misleading fix:** "just add TTL to the cache" — TTL does not prevent
cross-session reuse; it only delays it.
**Instead:** per-session cache, invalidated on rotation.

## [PATTERN] Rotate tokens on refresh
Reason: global pattern match: refresh, the, token
```

**4. Asserts the delivery.** The demo checks its own output — four assertions
that the knowledge actually changed the agent's instructions:

```text
✓ anti-pattern warning delivered: agent is told NOT to build a shared token cache
✓ domain pattern delivered: rotate-on-refresh named
✓ project decision delivered: binding, highest precedence
✓ correct alternative delivered: per-session cache

PROOF: without the fabric, an LLM would plausibly implement the banned
shared cache. With the manifest, the banned approach is named in the
prompt BEFORE code is written.
```

### Why this matters if you've never used a "second brain" or LLM wiki

The naive fix for "my agent doesn't know our conventions" is to paste a big
markdown file into the prompt. That fails in three predictable ways: the file
grows until it's mostly stale, nothing verifies the agent actually absorbed
it, and contradictions accumulate silently. Wiki Fabric's answer is
structural:

- **Knowledge is small and typed**, not one big document — each rule carries
  its evidence, its status (`supported`/`superseded`), and its scope
  (global / domain / single project)
- **Delivery is compiled, not hoped for** — `wf context` selects by precedence
  (project beats domain beats global) and gives every selection a reason
- **Stale knowledge is filtered, not delivered** — the `pattern-stale` page
  above was excluded because its `review_after` date passed; the demo proves
  staleness is enforced, not aspirational
- **Behavior is measured** — the four `✓` assertions are the same shape as
  the behavior evals that run in CI, so "the knowledge changed the decision"
  is a test, not a claim

And it compounds: the experience event behind that anti-pattern was mined
from two projects' real failures (that's what "maturity 2" means — a pattern
isn't *recommended* until it's been observed in ≥2 independent projects, and
never auto-promoted: a human approves every promotion). One session's lesson
becomes every future session's starting context.

Run it yourself: `bash scripts/demo.sh --json` for the machine-checkable
manifest, or continue to [Getting Started](./getting-started).

> [!WARNING]
> **Very early alpha — expect breaking changes.** The core loop works
> end-to-end (verified on real projects), but schemas move without migration
> scripts and nothing is packaged yet. Useful today if you want to shape the
> direction; not yet load-bearing team infrastructure.