---
type: claim
id: claim-wiki-fabric-readme-md-007
statement: "Wiki Fabric provides a CLI surface with shell completions and machine surfaces."
description: "Wiki Fabric provides a CLI surface with shell completions and machine surfaces."
resource: "[[src-wiki-fabric-readme-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:24:56Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T07:24:56Z"
status: supported
confidence: high
project: "wiki-fabric"
evidence_strength: primary
source_refs:
  - source: "[[src-wiki-fabric-readme-md]]"
    locator: "L62-L64"
    quote: "The CLI surface: shell completions (bash/zsh/fish), `wf help <cmd>` → argparse, `--version`, typo suggestions, one-liners for all verbs, `--json` machine surfaces (`status`/`ingest`/`review`/`projects`), **exit-code discipline** (drift 2 / unknown-slug 3 — loud for hooks/CI), `wf projects` inventory; OKF v0.2 export/import; wiki generation + publish + utility write-back."
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-readme-md-007

Wiki Fabric provides a CLI surface with shell completions and machine surfaces.
