# Wiki Fabric

[![CI](https://github.com/hybridindie/wiki-fabric/actions/workflows/ci.yml/badge.svg)](https://github.com/hybridindie/wiki-fabric/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-wiki--fabric.site-blue)](https://hybridindie.github.io/wiki-fabric/)

> **Git-native, testable knowledge governance for AI coding agents.**
> Project memory that is scoped by precedence, traceable to evidence, enforced by CI — and *provably delivered* before an agent writes code.

**Positioning in one line:** Wiki Fabric treats repository knowledge as operational infrastructure for agents — a governed context layer, not a note vault. Where generic "LLM wiki" projects stop at self-maintaining Markdown, Wiki Fabric adds the three things that make knowledge *trustworthy at task time*: scope with precedence, provenance with staleness gates, and behavior evaluations that measure whether the knowledge changed the agent's decision. It is one substrate of agent memory — the durable, Git-governed one — not the whole capability: the agent's context window and working state remain the harness's to manage. And it is **local-first, cloud-optional**: the daily loop runs on-device with zero tokens; LLM stages route per-repo, per-stage (privacy tiering) when you want them.

> [!WARNING]
> **Very early alpha — expect breaking changes.** The core loop works end-to-end
> (capture → ingest → query → promote, verified on real projects), but schemas
> move without migration scripts, claim-extraction quality varies by model,
> team sync is single-node-first, and nothing is packaged yet (clone-and-run
> with `uv`; Windows untested). Useful today if you want to shape the
> direction — not yet load-bearing team infrastructure.

## Quick start

```bash
# See the value in 5 seconds (no install):
bash scripts/demo.sh

# Install (installs uv if missing, then the `wf` CLI at ~/.local/bin/):
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash

# Teammate: pulls the team corpus automatically when the remote carries one
# (--vault <path> pins where the vault shell lives):
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- --corpus git@github.com:your-org/wiki-fabric-corpus.git

wf status                        # fabric health
wf bootstrap /path/to/my-project # connect a project (--extract local for privacy)
wf capture my-project            # pull docs from upstream repos → evidence/raw/
wf ingest evidence/raw/my-project/docs/readme.md --extract-claims
wf query "Why does my code batch writes?"
wf context --task "Add token rotation to the OAuth service"
wf log --project my-project --problem "..." --intervention "..." --outcomes "..."
```

The daily loop — connect → capture → ingest → validate → context → work → mine/review — compounding at step 7 into step 5's context for the next project. Full walkthrough, flags, and requirements: **[Getting Started](https://hybridindie.github.io/wiki-fabric/getting-started.html)**.

## What it is

Two trees: the **harness** (tooling, this repo) and the **fabric** (your knowledge — gitignored, lives in the corpus/vault; teammates pull it at install). The harness ships: the knowledge format (claims with locators, patterns, decisions, commitments), the deterministic context compiler (`wf context` — every inclusion/exclusion carries a reason, persisted receipts), contract enforcement (lint + CI gate), behavior evaluations, and the self-building domain vocabulary. Optional integrations: graphify (call-graph staleness + code navigation), judgment tier (decision-model eval gates), embeddings (planned), team sync. See [Architecture](docs/site/architecture.md) for the pipeline and [Core Workflows](docs/site/core-workflows.md) for the loop with scenarios.

## Documentation

Full docs at **[hybridindie.github.io/wiki-fabric](https://hybridindie.github.io/wiki-fabric/)** — with search.

| Start here | Then |
|-----|----------|
| [Getting Started](docs/site/getting-started.md) · [Why not just a wiki or RAG?](docs/site/why.md) | [Architecture](docs/site/architecture.md) · [Core Workflows](docs/site/core-workflows.md) · [Task Context](docs/site/context.md) |
| [Configuration](docs/site/configuration.md) · [CLI Reference](docs/site/cli.md) | [Model policy & evals](docs/site/evals.md) · [Governance](docs/site/governance.md) · [Team Sync](docs/site/sync.md) |
| [OKF v0.2](docs/site/okf.md) · [Machine-Readable Contract](docs/site/machine-contract.md) | [Integrations](docs/site/integrations.md) · [Troubleshooting](docs/site/troubleshooting.md) |

## Status

- **Works today:** capture → ingest → query → promote loop; deterministic context compiler; persisted context receipts; prospective-memory commitments; judgment tier (`--judge` eval gates); git-hooks automation; team sync with teammate corpus pull; OKF v0.2 export/import.
- **Next:** judgment-informed context re-ranking, compiler-eval judged mode in eval.py, MCP server, multi-harness skill packs, embeddings re-ranking.
- **Contributing:** see [CONTRIBUTING.md](CONTRIBUTING.md). The fabric self-documents — if something isn't clear, that's a bug in the fabric; issues welcome.

## License

MIT — see [LICENSE](LICENSE).
