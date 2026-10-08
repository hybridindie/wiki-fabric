---
type: claim
id: claim-wiki-fabric-docs-site-cli-md-008
statement: "The `wf completions` command generates shell completion scripts."
description: "The `wf completions` command generates shell completion scripts."
resource: "[[src-wiki-fabric-docs-site-cli-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:42:31Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T07:42:31Z"
status: supported
confidence: high
project: "wiki-fabric"
evidence_strength: primary
source_refs:
  - source: "[[src-wiki-fabric-docs-site-cli-md]]"
    locator: "L87-L89"
    quote: "`wf completions {bash\\|zsh\\|fish}` | Emit a shell completion script on stdout — verbs + subcommands (`mine chats\\|promotions`, `eval behavior\\|…`, `sync …`) + common flags per verb. Install: `eval \"$(wf completions bash)\"` (bash); `wf completions zsh > \"${fpath[1]}/_wf\" && compinit` (zsh); `wf completions fish > ~/.config/fish/completions/wf.fish` (fish). Static generation — never breaks offline"
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-docs-site-cli-md-008

The `wf completions` command generates shell completion scripts.
