---
type: claim
id: claim-wiki-fabric-docs-site-machine-contract-md-002
statement: "Lint report codes are stable."
description: "Lint report codes are stable."
resource: "[[src-wiki-fabric-docs-site-machine-contract-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T08:25:42Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T08:25:42Z"
status: supported
confidence: high
project: "wiki-fabric"
evidence_strength: primary
source_refs:
  - source: "[[src-wiki-fabric-docs-site-machine-contract-md]]"
    locator: "L19-L42"
    quote: "The lint report codes are stable: `FRONTMATTER`, `BROKEN-LINK`, `SCOPE`,\n`REVIEW-AFTER`, `CLAIM`, `CONCEPT`, `PATTERN`, `COMMITMENT`, `DUP-ID`, `SOURCE`,\n`SOURCE-DRIFT`, `SOURCE-EMPTY`, `SYNC-CONFLICT`, `ORPHAN`, `LLM-CONFIG`, `GENERATED`,\n`STALE-AFTER`, `TRUST-TIER`, `IGNORE-CONFIG`, `VERIFIED`, `TYPE`, `PROPOSED-TYPE`,\n`RECEIPT`, `QUESTION`, `SLOW-REGION`, plus `LAYOUT-GUARD` (corpus path\nre-spelled outside `scripts/lib/layout.py` — enforced at COMMIT time in the\nharness hook body v6, at test time by the full AST guard),\n`VOCABULARY` (a `domain:`\ndeclaration resolving to no ontology domain — the alias map is the binding),\n`IDENTITY` (canonical repo-slug collisions error; non-canonical namespace\nspellings advise), **`JUDGMENT-GATE`** (a judged surface refused: no PASS\n`judgment-eval` receipt for the current judge identity — G-J, the compiler\nG4 gate's analog; the deterministic fallback stands loudly),\n**`CONTRADICTION-STAMP`** (a claim mechanically demoted by the newest-wins\nsweep, #175: `contradicted-by:` frontmatter stamp + `status: contested` —\nrestores when the contradictor loses support),\n**`SECRETS`** (a credential-shaped string in a corpus content page, #188 —\nerror tier, blocks the commit gate: rotate, redact, re-ingest; matches are\nmasked in output, `evidence/raw/` exempt as the immutable capture plane),\nplus the OKF-floor `OKF-*` codes (`--okf` mode). The rest are structural — `FRONTMATTER`\n(malformed metadata), `BROKEN-LINK`, `DUP-ID`, `SOURCE` — and each message\nnames the offending page and field."
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-machine-contract-md-002

Lint report codes are stable.
