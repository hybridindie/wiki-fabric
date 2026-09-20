# Wiki Fabric

[![CI](https://github.com/hybridindie/wiki-fabric/actions/workflows/ci.yml/badge.svg)](https://github.com/hybridindie/wiki-fabric/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-wiki--fabric.site-blue)](https://hybridindie.github.io/wiki-fabric/)

> **Git-native, testable knowledge governance for AI coding agents.**
> Project memory that is scoped by precedence, traceable to evidence, enforced by CI — and *provably delivered* before an agent writes code.

**Positioning in one line:** Wiki Fabric treats repository knowledge as operational infrastructure for agents — a governed context layer, not a note vault. Where generic "LLM wiki" projects stop at self-maintaining Markdown, Wiki Fabric adds the three things that make knowledge *trustworthy at task time*: scope with precedence, provenance with staleness gates, and behavior evaluations that measure whether the knowledge changed the agent's decision.

> [!WARNING]
> **Very early alpha — expect breaking changes.** The core loop works end-to-end
> (capture → ingest → query → promote, verified on real projects), but schemas
> move without migration scripts, claim-extraction quality varies by model,
> team sync is single-node-first, and nothing is packaged yet (clone-and-run
> with `uv`; Windows untested). Useful today if you want to shape the
> direction — not yet load-bearing team infrastructure.

---

## The one-session proof

A fabric containing one pattern, one anti-pattern, and one project decision changes what an agent is *told* before it writes code:

```bash
bash scripts/demo.sh
```

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

Every inclusion and exclusion carries a reason; delivery is deterministic, 0 tokens. Run `bash scripts/demo.sh --json` for the machine-checkable manifest.

**What is core vs. optional:**

| Layer | Status |
|-------|--------|
| Knowledge format (claims with locators, patterns, decisions, scopes) | **core format** |
| `wf context` — task manifest compiler | **core** |
| Contract enforcement (`lint.py` + JSON, CI gate) | **core** |
| Behavior evaluations (`eval-behavior.py`) | **core** |
| `wf` CLI, uv install | reference implementation |
| **Graphify** (call-graph staleness, claim enrichment, graph expansion) | **optional integration** — off by default |
| **Embeddings** (semantic re-ranking) | **optional integration** — off by default, planned |
| Git history capture, corpus team sync | integrations |
| MCP server, multi-harness skill packs | roadmap |

---

## The Loop (one page, start to finish)

The daily-use cycle — each step is a command, every step is checked:

| # | Step | Command | Enforced by |
|---|------|---------|-------------|
| 1 | **Connect** a project | `wf bootstrap /path/to/project` | namespace created, README written to corpus |
| 2 | **Capture** knowledge | `wf capture p --git owner/repo` | immutable raw + sha256 |
| 3 | **Compile** sources → claims | `wf ingest <src> --extract-claims` | change-set + lint gate |
| 4 | **Validate** | `wf lint` | 0 errors before merge |
| 5 | **Compile task context** | `wf context --task "..."` | manifest with reasons + precedence |
| 6 | **Agent works, then learns** | `wf log --project p ...` | experience event captured |
| 7 | **Mine + review** | `mine-promotions` → human gate → `promote` | maturity gates, no auto-promotion |

Then loop: step 7's promoted pattern is step 5's context for the next project — that's the compounding. CI proves every arrow in this table.

---

## Quick Start

> Alpha reality check: the demo below is deterministic and works everywhere.
> Real-fabric setup (`wf bootstrap` + ingest + extraction) is the alpha part —
> expect rough edges, and file issues for anything that bites.

Full walkthrough: **[Getting Started](https://hybridindie.github.io/wiki-fabric/getting-started.html)** (install flags, manual install, first loop).

```bash
# See the value in 5 seconds (no install):
bash scripts/demo.sh

# One-liner install (installs uv if missing, then the `wf` CLI at ~/.local/bin/)
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash

# With team corpus sync wired in from the start:
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- --corpus git@github.com:your-org/wiki-fabric-corpus.git

wf status                              # check fabric health
wf bootstrap /path/to/my-project       # connect a project (auto-discovered; --extract local for privacy)
wf capture my-project                  # pull docs from upstream repos → evidence/raw/
wf ingest evidence/raw/my-project/docs/readme.md --extract-claims
wf query "Why does my code batch writes?"
wf log --project my-project --problem "..." --intervention "..." --outcomes "..."

# Automate the refresh loop (opt-in, per project):
wf hook install --extract-claims       # doc-drift commits auto-capture + auto-ingest
wf claude install                      # always-on instructions in AGENTS.md/CLAUDE.md
```

The one-liner installs **uv** if missing, creates a `.venv` inside the fabric,
and installs Python deps from `requirements.txt` (pyyaml, openai, anthropic)
with `uv pip`. Everything Python runs inside that venv. If uv can't be
installed, `wf` falls back to plain `python3`. `wf update` re-syncs deps when
`requirements.txt` changes. All `wf` commands also work without the install —
the scripts in `scripts/` run with plain `python3`. Install flags, manual
install, and requirements: [Getting Started](docs/site/getting-started.md).

### Verify the install

```bash
python3 -m pytest tests/ -q                # full suite (includes live-model tests)
python3 -m pytest tests/ -m "not live" -q  # fast suite: skips on-device model tests
bash scripts/smoke-test.sh                 # end-to-end CLI checks in a throwaway fabric
wf lint                                    # fabric self-lint (0-error gate)
```

Tests marked `live` run real on-device models (GGUF/MLX) and self-skip when the
model isn't cached or the platform lacks the backend.

---

## Repository layout

Two kinds of tree live here: the **harness** (tooling, shipped in this repo) and the **fabric** (your knowledge, gitignored — lives in your corpus/vault).

| Path | Kind | What it is |
|------|------|-----------|
| `README.md` `AGENTS.md` `CONTRIBUTING.md` `LICENSE` `index.md` | harness | entry points (index.md is the OKF root index) |
| `pyproject.toml` `requirements.txt` `okf-base.yaml` | harness | Python packaging, deps, okflint profile |
| `scripts/` | harness | the pipeline: ingest, query, context, lint, promote, sync, hooks |
| `tests/` | harness | 220+ unit tests (`-m "not live"` for fast suite) |
| `docs/site/` | harness | this documentation (VitePress, deployed to Pages) |
| `system/` | harness | agent-facing assets: `skills/` (6 SKILL.md), `always-on/`, `opencode/plugins/` |
| `schemas/` | harness | frontmatter contracts (`frontmatter.md`) + domain ontology |
| `templates/` | harness | page scaffolds (`pattern.md`, `decision.md`, ...) + `examples/` |
| `references/` | harness | attesters (deterministic receipt checks) + executor skills |
| `evaluations/` | harness | golden corpus, behavior fixtures, eval scripts' data |
| `global/computations/` | harness | attested-computation contracts (OKF §10) |
| `evidence/` | **fabric** | captured sources, summaries, claims (gitignored) |
| `projects/` | **fabric** | per-project namespaces (gitignored) |
| `patterns/` `concepts/` `skills/` `anti-patterns/` `domains/` `syntheses/` | **fabric** | canonical knowledge (gitignored) |
| `registry/` | fabric+harness | `promotion-queue.md` tracked; `log.md`, `catalog.json` generated |
| `fabric.yaml` | yours | config (gitignored — see [Configuration](docs/site/configuration.md)) |
| `graphify-out/` | generated | the self knowledge graph |

Fresh clones ship the harness plus the layout skeleton (`.gitkeep`ed content dirs); your knowledge accumulates locally and syncs via [Team Sync](docs/site/sync.md).

---

## Documentation

Full docs at **[hybridindie.github.io/wiki-fabric](https://hybridindie.github.io/wiki-fabric/)** — with search.

| Doc | Contents |
|-----|----------|
| [Getting Started](docs/site/getting-started.md) | Install, quickstart, first loop, requirements |
| [Why not just a wiki or RAG?](docs/site/why.md) | Failure modes of the alternatives, and the core bet |
| [Architecture](docs/site/architecture.md) | The pipeline, module map, reading order |
| [Core Workflows](docs/site/core-workflows.md) | Ingest, git-history capture, query, experience → pattern, bootstrap, maintenance, hooks — with scenarios |
| [Configuration](docs/site/configuration.md) | **OpenAI-compatible providers, env vars, model tiers, per-stage routing, ignores** |
| [Task Context](docs/site/context.md) | `wf context` — the deterministic manifest compiler |
| [CLI & Scripts Reference](docs/site/cli.md) | Every `wf` command, note types, scripts + shared modules |
| [Model policy & evals](docs/site/evals.md) | Compiler-eval gate, behavior evals, stability, PR replay, real-repo |
| [OKF v0.2 conformance](docs/site/okf.md) | The portable-bundle standard, trust tiers, attested computations |
| [Governance](docs/site/governance.md) | The hard questions, and where the fabric answers them |
| [Machine-Readable Contract](docs/site/machine-contract.md) | Lint codes, `registry/catalog.json`, CI consumption |
| [Optional Integrations](docs/site/integrations.md) | Graphify (0-token call-graph intelligence), embeddings |
| [Team Sync](docs/site/sync.md) | Share the corpus as source of truth via git |
| [Troubleshooting](docs/site/troubleshooting.md) | Common failure modes and fixes |

---

## Status & roadmap

- **Works today:** capture → ingest → query → promote loop; deterministic context compiler; behavior evals; git-hooks automation; team sync; OKF v0.2 export/import.
- **Next:** MCP server, multi-harness skill packs, embeddings re-ranking.
- **Contributing:** see [CONTRIBUTING.md](CONTRIBUTING.md). The fabric self-documents — if something isn't clear, that's a bug in the fabric; issues welcome.

## License

MIT — see [LICENSE](LICENSE).