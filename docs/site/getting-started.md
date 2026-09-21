---
type: index
title: "Getting Started — install, quickstart, first loop"
description: "Install the wf CLI, see the demo proof, connect your first project"
created: 2026-09-19
updated: 2026-09-19
---

# Getting Started

Three ways in, by commitment level: **run the demo** (30 seconds, no install),
**install the CLI** (one command), or **connect your first project** (the real
loop). Alpha reality check: the demo is deterministic and works everywhere;
real-fabric setup is the alpha part — expect rough edges, and file issues for
anything that bites.

## 1. The 30-second proof (no install)

```bash
git clone https://github.com/hybridindie/wiki-fabric
cd wiki-fabric
bash scripts/demo.sh
```

The demo builds a throwaway fabric with one pattern, one anti-pattern, and one
project decision — then compiles a task context showing the agent being *told*
to avoid a banned approach before writing code. See the transcript on the
[homepage](./). Run `bash scripts/demo.sh --json` for the machine-checkable
manifest.

## 2. Install the `wf` CLI

```bash
# One-liner: installs uv if missing, clones the harness to ./wiki-fabric
# (CWD), creates the fabric at ~/.local/share/wiki-fabric, installs the wf CLI
# at ~/.local/bin/
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash
```

Install flags:

| Flag | Effect |
|------|--------|
| `--corpus <git-url>` | Point the fabric at a team-shared corpus (the shared knowledge content, synced via git — see [Team Sync](./sync)) |
| `--with-graphify` | Enable the graphify integration (see [Integrations](./integrations)) |
| `--dir <path>` | Harness clone location (default `./wiki-fabric` — the current directory) |
| `--repo <url>` | Install from a fork |
| `--interactive` | Walk through provider/model/routing config (prompts for everything — see [Configuration](./configuration)) |
| `--no-vault` | Skip the Obsidian vault symlink |

**What the one-liner actually does:** checks for **uv** (Astral's Python
package manager) and installs it if missing, clones the **harness** (the code —
this repo) to `./wiki-fabric` (your current directory — use `--dir` to choose
another spot), creates the **fabric** (your content
+ config) at `~/.local/share/wiki-fabric/` (XDG data dir), sets up the venv in
the harness, and symlinks `wf` into `~/.local/bin/`. Everything Python runs
inside that venv — no system pip pollution, no version drift. If uv can't be
installed, `wf` falls back to plain `python3` (core CLI works; LLM features
need `pip install -r requirements.txt`). `wf update` re-syncs deps when
`requirements.txt` changes.

**Harness vs fabric:** the harness clone never holds your knowledge — it's a
git clone of this public repo, refreshed by `wf update` (git pull). Your
content (`evidence/`, `projects/`, `patterns/`, `fabric.yaml`, ...) lives in
the fabric dir and syncs via [Team Sync](./sync) to a remote you own. Set
`WIKI_FABRIC_DIR` to relocate the fabric.

All `wf` commands also work without any install — the scripts in `scripts/`
run with plain `python3` from a clone (dev mode: a clone holding a
`fabric.yaml` doubles as its own fabric).

### Manual install (equivalent)

```bash
git clone https://github.com/hybridindie/wiki-fabric wiki-fabric
cd wiki-fabric
uv venv && uv pip install -r requirements.txt
mkdir -p ~/.local/bin
ln -sf "$PWD/scripts/wiki-fabric.sh" ~/.local/bin/wf
wf status
```

### Keeping up to date

```bash
wf update            # pull latest + rebuild index + re-sync deps
wf update --with-graphify   # also enable the graphify integration
```

## 3. Verify the install

```bash
wf status                            # fabric health + inventory
python3 -m pytest tests/ -m "not live" -q   # fast test suite
bash scripts/smoke-test.sh           # end-to-end CLI checks in a throwaway fabric
wf lint                              # fabric self-lint (0-error gate)
```

Tests marked `live` (run with plain `pytest tests/ -q`) exercise real on-device
models and self-skip when the model isn't cached or the platform lacks the
backend.

## 4. Connect your first project

```bash
# One-time: pick your LLM provider if Ollama isn't your choice
# (see Configuration — or run `wf install --interactive` to be prompted)

wf bootstrap /path/to/my-project      # connect a project (auto-discovered; --extract local for privacy)
                                       # (hook installed automatically by bootstrap; --no-hook skips)
wf capture my-project                 # pull docs from upstream repos → evidence/raw/
wf capture chat my-project            # capture agent chat sessions → evidence/raw/my-project/chats/
wf ingest evidence/raw/my-project/docs/readme.md --extract-claims
wf query "Why does my code batch writes?"
wf log --project my-project --problem "..." --intervention "..." --outcomes "..."   # log an experience event: problem → what you did → measured outcome
```

`wf bootstrap` writes `.wiki-overlay.md` into the project, creates its
namespace in the fabric, and additively merges agent config (never overwrites
your MCP setup). Then [Core Workflows](./core-workflows) takes over: capture →
ingest → query, with scenarios for onboarding, dependency audits, and
compiling PR history.

### Automate the loop (opt-in)

```bash
wf harness install                 # configure every detected agent harness
                                   # (--all for the full matrix; --only claude,copilot)
wf hook install --extract-claims   # doc-drift commits auto-capture + auto-ingest
```

## Requirements

| | |
|---|---|
| Python | 3.11+ (uv installs its own) |
| git | any recent version |
| LLM endpoint | anything OpenAI-compatible — Ollama (`curl -fsSL https://ollama.com/install.sh \| sh`) is the zero-config default; see [Configuration](./configuration) for OpenAI/OpenRouter/etc. |
| On-device models (optional) | `pip install -e ".[local]"` — GGUF anywhere, MLX on Apple Silicon |
| **Git hooks** | **required for the freshness guarantee** — `wf hook install` per project (drift-gated: unchanged docs cost 0 tokens; LLM only with `--extract-claims`) |
| Platform | macOS / Linux (Windows untested; git hooks are POSIX-verified only) |

## Agent harness support

`wf harness install` configures every agent tool it detects (or `--all`):

| Harness | Always-on instructions | Skills |
|---------|----------------------|--------|
| Claude Code | `CLAUDE.md` + `AGENTS.md` | `.claude/skills/` (native skills) |
| opencode | `AGENTS.md` + `opencode.json` merge | `.opencode/skill/` + plugin |
| OpenAI Codex CLI | `AGENTS.md` (native) | — |
| GitHub Copilot | `.github/copilot-instructions.md` | — |
| Gemini CLI | `GEMINI.md` | — |
| Cursor | `.cursor/rules/wiki-fabric.mdc` | — |
| Pi | `AGENTS.md` / `PI.md` | — |
| Aider / Zed / Cline / Windsurf | `CONVENTIONS.md` / `.rules` / `.clinerules/` / `.windsurf/rules/` | — |

The instruction content is identical everywhere — the same always-on block,
which includes the procedures pointer (`wf skill <name>`). Workflow
**procedures** (`ingest`, `promote`, `refresh`) are printed on demand by
`wf skill <name>` — a universal mechanism that works on every harness, no
skill support required. Only Claude Code and opencode additionally get native
skill folders (lazy-loaded, where that's a real feature). The conditional
logic that used to live only in skill prose (graphify enrichment hints,
anti-loop reminders) now lives in the commands themselves — `wf` tells you the
next step when it matters.

## Next steps

- [Configuration](./configuration) — pick providers, set model tiers, route sensitive repos on-device
- [Core Workflows](./core-workflows) — the full loop with scenarios
- [Task Context](./context) — what the agent receives at task time
- [Team Sync](./sync) — share the corpus with a team

---

Next: [Once installed, walk the core workflows](./core-workflows)
