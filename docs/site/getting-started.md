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
# One-liner: installs uv if missing, clones to ~/Development/wiki-fabric,
# sets up the venv, installs the wf CLI at ~/.local/bin/
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash
```

Install flags:

| Flag | Effect |
|------|--------|
| `--corpus <git-url>` | Wire team corpus sync at install time (see [Team Sync](./sync)) |
| `--with-graphify` | Enable the graphify integration (see [Integrations](./integrations)) |
| `--dir <path>` | Install location (default `~/Development/wiki-fabric`) |
| `--repo <url>` | Install from a fork |
| `--interactive` | Walk through provider/model/routing config (prompts for everything — see [Configuration](./configuration)) |
| `--no-vault` | Skip the Obsidian vault symlink |

**What the one-liner actually does:** checks for **uv** (Astral's Python
package manager) and installs it if missing, clones the repo, creates a
`.venv` inside the fabric, installs Python deps from `requirements.txt`
(pyyaml, openai, anthropic) with `uv pip`, and symlinks `wf` into
`~/.local/bin/`. Everything Python runs inside that venv — no system pip
pollution, no version drift. If uv can't be installed, `wf` falls back to plain
`python3` (core CLI works; LLM features need `pip install -r
requirements.txt`). `wf update` re-syncs deps when `requirements.txt` changes.

All `wf` commands also work without any install — the scripts in `scripts/`
run with plain `python3` from a clone.

### Manual install (equivalent)

```bash
git clone https://github.com/hybridindie/wiki-fabric ~/Development/wiki-fabric
cd ~/Development/wiki-fabric
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
wf capture my-project                 # pull docs from upstream repos → evidence/raw/
wf ingest evidence/raw/my-project/docs/readme.md --extract-claims
wf query "Why does my code batch writes?"
wf log --project my-project --problem "..." --intervention "..." --outcomes "..."
```

`wf bootstrap` writes `.wiki-overlay.md` into the project, creates its
namespace in the fabric, and additively merges agent config (never overwrites
your MCP setup). Then [Core Workflows](./core-workflows) takes over: capture →
ingest → query, with scenarios for onboarding, dependency audits, and
compiling PR history.

### Automate the loop (opt-in)

```bash
wf hook install --extract-claims   # doc-drift commits auto-capture + auto-ingest
wf claude install                  # always-on instructions in AGENTS.md/CLAUDE.md
```

## Requirements

| | |
|---|---|
| Python | 3.11+ (uv installs its own) |
| git | any recent version |
| LLM endpoint | anything OpenAI-compatible — Ollama (`curl -fsSL https://ollama.com/install.sh \| sh`) is the zero-config default; see [Configuration](./configuration) for OpenAI/OpenRouter/etc. |
| On-device models (optional) | `pip install -e ".[local]"` — GGUF anywhere, MLX on Apple Silicon |
| Platform | macOS / Linux (Windows untested; git hooks are POSIX-verified only) |

## Next steps

- [Configuration](./configuration) — pick providers, set model tiers, route sensitive repos on-device
- [Core Workflows](./core-workflows) — the full loop with scenarios
- [Task Context](./context) — what the agent receives at task time
- [Team Sync](./sync) — share the corpus with a team

---

Next: [Once installed, walk the core workflows](./core-workflows)
