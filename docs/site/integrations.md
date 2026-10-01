---
type: index
title: "Optional Integrations"
description: "Graphify, judgment, embeddings, obsidian, MCP — each with its own deep page (pros/cons, examples, setup)"
---

# Optional Integrations

Integrations add capabilities on top of the core loop, declared in
`fabric.yaml` ([Configuration](/configuration)) — and they are **never
load-bearing**: with every integration off, every command behaves exactly as
the core docs describe. The design rule: *integrations add capabilities;
they are never load-bearing.*

## One page per integration (deep dives)

| Integration | Page | One-line |
|-------------|------|----------|
| **judgment** | [Judgment — the decision-model tier](/integrations/judgment) | typed calibrated judging: Jev cloud / Laya on-device / **Tev1+Nimble via ollama** / generic — pros, cons, measured numbers |
| **graphify** | [Code call-graph](/integrations/graphify) | AST provenance, stale-claim detection after refactors, code navigation |
| **embeddings** | [Semantic re-rank](/integrations/embeddings) | offline cosine fusion for query ranking (measured value conditions) |
| **obsidian** | [Two-way vault](/integrations/obsidian) | human edits → evidence; generated notes → your vault |
| **MCP** | [wf-mcp server](/integrations/mcp) | the 0-token core surface as native tools for any MCP client |
| **team sync** | [Team Sync](/sync) + [the freshness cycle](/how-sync#the-scheduled-upstream-freshness-cycle) | corpus sharing via git; scheduled upstream drift capture |

## The quick matrix

| Integration | When active | Cost | Ship it when… |
|-------------|-------------|------|---------------|
| **judgment** | mining near-miss refinement; `wf verify-effects` second opinion; eval gates; retrieval fusion | on-device (0) or ~$0.0004/call (Jev) | mining gets real traffic; self-preference risk matters; fusion rerank wanted → [page](/integrations/judgment#where-it-runs-all-live) |
| **graphify** | doc→code provenance; AST stale-claim detection; code-navigation block | 0 tokens (AST) | docs reference code symbols; refactors rename code → [page](/integrations/graphify#the-four-capabilities) |
| **embeddings** | semantic re-rank on top-40 | ~5 ms/query offline (fastembed) | corpus > ~2k claims; word divergence across projects → [page](/integrations/embeddings#when-it-earns-its-keep) |
| **obsidian** | two-way: harvest human edits as evidence; mirror notes via REST API | 0 tokens | humans curate the wiki by hand → [page](/integrations/obsidian#the-contract) |
| **MCP** | core surface as native tools | 0 tokens | your harness speaks MCP; multi-client setups → [page](/integrations/mcp#tool-surface) |

All off by default; each page carries **pros/cons, measured examples, and
the exact setup** — plus the degrade contract (server down / route off ⇒
deterministic behavior stands).

## The loudness contract (gate notifications)

Pending human decisions — the things integrations like judgment *propose* —
reach you where you stand:

- **Terminal banner + bell** (the no-setup default): every command that
  *creates* a pending decision prints
  `human decisions pending — promotions: 1 (wf gate)`;
  **`wf status`** carries a persistent `⚠ Gate: pending … → wf gate` line.
- **macOS notification center** (default on darwin) and **webhooks**
  (`WF_GATE_WEBHOOK_URL`) — adapter config below.
- Payload: selection facts (what, why, evidence), never hidden reasoning.
  Fire-and-forget: notification failure never fails the emitting command;
  the durable record is always `registry/pending-gate.md` + the queues.

```yaml
notify:                  # optional; absent = terminal (default) + macOS bump
  - kind: webhook
    url_env: WF_GATE_WEBHOOK_URL
  - kind: macos
  - kind: terminal
# notify: []             # silence everything — the manifest stays the record
```

## Agent harnesses

Wiki Fabric installs into any agent harness — see the matrix in
[Getting Started](/getting-started#agent-harness-support). `wf harness
install` detects what you use and writes the always-on block + skills in
each tool's native format; `wf harness status` shows the current state.

**Session capture** (`wf capture chat <slug>`) covers four harnesses:
Claude Code, opencode, OpenAI Codex CLI, and Gemini CLI. Formats were built
from the harnesses' own storage schemas (verified against
`google-gemini/gemini-cli`'s `chatRecordingTypes.ts` and claude-mem's
transcript schema). Design note vs claude-mem's approach: they capture via
*hooks* (SessionStart/UserPromptSubmit/PreToolUse events) — real-time but
plugin-dependent; wiki-fabric reads the *session stores* the harnesses write
anyway — zero install requirements, sha256 anti-loop, and thread-index
frontmatter on every capture.

## Enabling

```bash
wf integrations                    # show what's active and what each changes
wf install --with-graphify         # enable at install time
wf update --with-graphify          # enable on an existing fabric
```