---
type: claim
id: claim-wiki-fabric-docs-site-architecture-md-005
statement: "Shared logic lives in the scripts/lib/ modules."
description: "Shared logic lives in the scripts/lib/ modules."
resource: "[[src-wiki-fabric-docs-site-architecture-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:41:27Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T07:41:27Z"
status: supported
confidence: medium
project: "wiki-fabric"
evidence_strength: secondary
source_refs:
  - source: "[[src-wiki-fabric-docs-site-architecture-md]]"
    locator: "L69-L75"
    quote: "shared logic lives in the `scripts/lib/` modules (`fabric_config`,\n`extract_backends`, `local_llm`, `wf_common`, `eval_core`, `judgment`,\n`embed_index`, `tombstones`, `layout` — corpus-path single truth,\n`ontology` — vocabulary single truth) — import, don't copy (anti-loop rule 7\nin [AGENTS.md](https://github.com/hybridindie/wiki-fabric/blob/main/AGENTS.md))."
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-architecture-md-005

Shared logic lives in the scripts/lib/ modules.
