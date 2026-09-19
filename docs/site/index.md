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

## The proof in one session

A fabric containing one pattern, one anti-pattern, and one project decision changes what an agent is *told* before it writes code:

```text
▸ Agent asks for task context: "Add token refresh to the auth service"

## Selected
### Project (highest precedence)
- [[decision-rotation-over-sessions]] — project match: auth-service
### Global
- [[anti-pattern-shared-token-cache]] — global pattern match: token
- [[pattern-token-rotation]] — global pattern match: refresh, token

## Excluded
- `patterns/pattern-superseded.md` — superseded
- `patterns/pattern-stale.md` — stale: review_after overdue 255 days

✓ anti-pattern warning delivered: agent is told NOT to build a shared token cache
✓ project decision delivered: binding, highest precedence
✓ correct alternative delivered: per-session cache

PROOF: without the fabric, an LLM would plausibly implement the banned shared cache.
With the manifest, the banned approach is named in the prompt BEFORE code is written.
```

Run it yourself with `bash scripts/demo.sh` — no install required.

> [!WARNING]
> **Very early alpha — expect breaking changes.** The core loop works
> end-to-end (verified on real projects), but schemas move without migration
> scripts and nothing is packaged yet. Useful today if you want to shape the
> direction; not yet load-bearing team infrastructure.