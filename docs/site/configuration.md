---
type: index
title: "Configuration — LLM providers, routing, and fabric.yaml"
description: "Every knob: OpenAI-compatible providers, model tiers, per-stage routing, ignores, integrations"
created: 2026-09-19
updated: 2026-09-19
---

# Configuration

Install first: [Getting Started](./getting-started). Everything in wiki-fabric is configured through one gitignored file,
`fabric.yaml` (template: [`fabric.yaml.example`](https://github.com/hybridindie/wiki-fabric/blob/main/fabric.yaml.example)),
plus environment variables that override it per-run.

## The complete fabric.yaml (annotated)

A full-featured example showing every key in context. Copy the sections you
need — every field is optional except `owner`; defaults come from
`fabric_config.py` ([the source of truth for defaults](https://github.com/hybridindie/wiki-fabric/blob/main/scripts/fabric_config.py)).

```yaml
# ─── Identity ────────────────────────────────────────────────────────────────
owner: your-name                    # your handle; used in actor conventions
                                    # (agent/<owner>/<model>) across all pages

# ─── LLM: three model roles ─────────────────────────────────────────────────
llm:
  # Endpoint: any OpenAI-compatible /v1 API (Ollama, OpenAI, OpenRouter,
  # Together, LM Studio, vLLM, llama.cpp server). See provider table above.
  base_url: http://localhost:11434/v1
  api_key: ollama                   # Ollama ignores it; cloud providers need a real key
  model: qwen2.5-coder:7b           # OPS model — cheap queries, capture, status

  # COMPILER model — claim extraction, synthesis, promotion mining.
  # The most consequential knob: the fabric's canonical evidence is compiled
  # by this model, and swapping it requires a recorded compiler eval.
  compiler_model: deepseek-v4.1-flash:cloud

  # LOCAL model — resolves repos.<slug>.<stage>: "local" routes (on-device,
  # zero egress). Defaults per platform if unset:
  #   Apple Silicon: mlx-community/gemma-4-e4b-it-4bit   (MLX, ~2.5 GB)
  #   elsewhere:     unsloth/gemma-4-e4b-it-GGUF         (GGUF, ~4 GB Q4_K_M)
  # Missing models are offered for download at first use (human-gated y/N),
  # or pre-fetch with: wf models ensure [--yes]
  local_model: mlx-community/gemma-4-e4b-it-4bit

# ─── Connected repos (namespaces) ───────────────────────────────────────────
repos:
  # Every connected project gets an entry. path is relative to the fabric
  # root (or absolute). The fabric itself can be its own namespace ("path: .")
  wiki-fabric:
    path: .
    graph_dir: graphify-out         # optional: per-repo graphify graph dir

  my-oss-project:
    path: ../my-oss-project         # all stages cloud (default) — fastest

  my-private-repo:                  # privacy tiering per stage
    path: ../my-private-repo
    graph_dir: graphify-out
    extract: local                  # raw docs never leave the machine (highest sensitivity)
    synthesize: local               # extracted claims stay local too
    dossier: cloud                  # experience events are safe for cloud
    # Values per stage: "cloud" (default) | "local" (uses llm.local_model)
    #   | an explicit model id (e.g. "qwen2.5-coder:7b" or an HF id)
    # Stages: extract (sees raw docs) · synthesize (sanitized claims)
    #         · dossier (experience events)

  # OpenAI directly instead of Ollama? Override per-fabric or per-repo:
  # llm:
  #   base_url: https://api.openai.com/v1
  #   api_key: sk-your-key-here
  #   compiler_model: gpt-4o

# ─── Ignores (exclude-side filter) ──────────────────────────────────────────
# Applied by capture, entity index, context, lint, rebuild-index, okf export.
# One list, auto-classified: globs by default, regex when metacharacters
# appear, `regex:` prefix as escape hatch.
ignore:
  patterns:
    - "vendor/**"                  # glob: fnmatch-style, ** crosses dirs
    - "docs/generated/**"
    - "**/*.min.js"
    - "_archive\\d+/"              # regex: \d triggers auto-classification
    - "regex:^node_modules/"       # regex: prefix forces regex matching
  projects:                        # per-repo patterns, unioned with global
    my-godot-game:
      patterns:
        - "addons/generated/**"

# ─── Optional integrations (all off by default) ─────────────────────────────
integrations:
  graphify:
    enabled: false                 # true → call-graph staleness, claim
    graph_dir: graphify-out        #        enrichment, query graph expansion
  embeddings:
    enabled: false                 # planned: semantic re-ranking of retrieval
    model: all-MiniLM-L6-v2

# ─── Domain taxonomy ────────────────────────────────────────────────────────
# Drives classification + context scoping. Grow with propose-domains.py.
domains:
  agent-systems:
    signals: [agent, mcp, fastmcp, opencode, claude]
  web-systems:
    signals: [fastapi, flask, react, nextjs, supabase, postgresql]
```

**Cheat sheet — who reads what:**

| Key | Read by |
|-----|---------|
| `llm.model` | query synthesis, capture, status |
| `llm.compiler_model` | ingest extraction, synthesize, mine-promotions, compiler-eval gate |
| `llm.local_model` | any `local` route (extract/synthesize/dossier) |
| `repos.<slug>.path` | capture, entity index, graphify bridge, hooks |
| `repos.<slug>.<stage>` | ingest, synthesize, mine-promotions routing |
| `ignore.patterns` / `.globs` / `.regexes` | capture, context, lint, rebuild-index, okf export |
| `integrations.*` | graphify bridge, skills |
| `domains.*` | classification, context scoping, propose-domains |

## LLM providers (any OpenAI-compatible endpoint)

The fabric talks to **any OpenAI-compatible `/v1` endpoint**. Set it once in `fabric.yaml`:

```yaml
llm:
  base_url: http://localhost:11434/v1   # any OpenAI-compatible endpoint
  api_key: ollama                        # Ollama ignores this; cloud providers need a real key
  model: qwen2.5-coder:7b               # ops model (see "Model tiers" below)
```

Tested endpoints:

| Provider | `base_url` | Notes |
|----------|-----------|-------|
| **Ollama** (default) | `http://localhost:11434/v1` | `api_key: ollama` (ignored) |
| **OpenAI** | `https://api.openai.com/v1` | `api_key: sk-...` |
| **OpenRouter** | `https://openrouter.ai/api/v1` | 400+ models, one key |
| **Together AI** | `https://api.together.xyz/v1` | open models, cheap |
| **LM Studio** | `http://localhost:1234/v1` | local server |
| **vLLM** | `http://localhost:8000/v1` | self-hosted |
| **llama.cpp server** | `http://localhost:8080/v1` | self-hosted |

```yaml
# Example — OpenAI directly:
llm:
  base_url: https://api.openai.com/v1
  api_key: sk-your-key-here
  compiler_model: gpt-4o
```

### Environment variables (override fabric.yaml per-run)

| Variable | Default | Purpose |
|----------|---------|---------|
| `WIKI_LLM_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible endpoint |
| `WIKI_LLM_API_KEY` | `ollama` | API key |
| `WIKI_LLM_MODEL` | `qwen2.5-coder:7b` | Ops model name |
| `WIKI_LLM_COMPILER_MODEL` | `deepseek-v4.1-flash:cloud` | Compiler model name |
| `WIKI_LLM_LOCAL_MODEL` | platform-split (below) | On-device model id |
| `WIKI_LLM_TIMEOUT` | `600` | Request timeout (seconds) |
| `WIKI_LLM_BACKEND` | — | Set to `mlx` to force the on-device backend |
| `WIKI_MLX_MODEL` | — | Explicit on-device model (wins over `llm.local_model`) |
| `WIKI_MLX_REASONING` | `low` | Reasoning effort for templates that accept it |
| `WIKI_LOCAL_MAX_TOKENS` | `4096` | Synthesis token budget on-device |
| `WIKI_LOCAL_N_CTX` | `16384` | GGUF context window |
| `WIKI_INGEST_WORKERS` | `1` | Concurrent extraction threads (cloud tolerates 6–12) |
| `HF_HOME` / `HF_HUB_CACHE` | `~/.cache/huggingface` | Where local models are cached |

## Model tiers: ops vs compiler vs local

Three model roles, each independently configurable:

| Setting | Default | Used for |
|---------|---------|----------|
| `llm.model` | `qwen2.5-coder:7b` | ops: capture, status, cheap query synthesis |
| `llm.compiler_model` | `deepseek-v4.1-flash:cloud` | claim extraction, synthesis, promotion mining (compiler work) |
| `llm.local_model` | `mlx-community/gemma-4-e4b-it-4bit` (Apple Silicon) / `unsloth/gemma-4-e4b-it-GGUF` (other) | resolves `repos.<slug>.<stage>: local` routes |

**Why a separate compiler model?** Claim extraction compiles sources into
canonical evidence — the fabric's most sensitive operation. Cross-model
extraction disagreement is capability-correlated, so compiler work runs on the
most capable model, and swapping it requires a recorded compiler eval
([Model Policy & Evals](./evals)).

## On-device (local) routes: privacy tiering

Per-repo, per-stage routing sends sensitive work to on-device models:

```yaml
repos:
  my-private-repo:
    path: ../my-private-repo
    extract: local      # raw docs never leave the machine
    synthesize: local   # extracted claims stay local too
    dossier: cloud      # experience events are safe for cloud
```

Stages: `extract` (sees raw docs — highest sensitivity), `synthesize`
(sanitized statements), `dossier` (experience events). Values: `"cloud"`
(default) · `"local"` (on-device via `llm.local_model`) · any explicit model id.

**Backends, chosen by model-id shape:**

| Backend | Runs on | Model ids |
|---------|---------|-----------|
| **GGUF** (llama-cpp-python) | macOS / Linux / Windows — the universal testing default | `*.gguf` ids, e.g. `unsloth/gemma-4-e4b-it-GGUF` |
| **MLX** (mlx-lm) | Apple Silicon only — fastest on M-series | `mlx-community/*` ids, e.g. `mlx-community/gemma-4-e4b-it-4bit` |

Chat-tuned models (gemma etc.) run through their chat template automatically.
Missing models are **offered for download at first use** (human-gated y/N, only
the preferred quantization split is fetched), or pre-fetch:

```bash
wf models ensure [--yes]      # check + offer download; --check exits 0/1 for scripts
```

Install the backends: `pip install -e ".[local]"`.

**Quality expectations:** the default local models pass the golden-corpus eval
(recall 0.89, quote-verbatim 0.96) and agree with the cloud compiler at G4
0.68–0.78 — the full local-vs-cloud test story with numbers lives in
[Model Policy & Evals](./evals#local-vs-cloud-what-the-small-model-tests-actually-showed).

## Connecting repos: config lives in the project

Every project carries its own config in `.wiki-overlay.md` (written by
`wf bootstrap`, **versioned with the project repo**) — identity, domains,
capture globs, and the LLM `routing:` block:

```yaml
# /path/to/my-project/.wiki-overlay.md (frontmatter)
project: my-project
namespace: my-project
routing:
  extract: local      # raw docs never leave the machine
  synthesize: local
  dossier: cloud
```

The fabric **discovers** these automatically: it scans its sibling directories
for `.wiki-overlay.md` files (respects `namespace:` for the slug), so a
bootstrap'd project appears in `wf status` with no fabric.yaml edit. Explicit
`repos:` entries merge **over** the overlay — explicit keys win:

```yaml
repos:
  # auto_discover: siblings is the default (set false to disable)
  # Only exceptions need entries here:
  my-private-repo:
    path: ../elsewhere/my-private-repo   # non-sibling location
    extract: local                        # explicit routing overrides overlay
  wiki-fabric:
    path: .                               # the fabric itself
```

Stages: `extract` (sees raw docs — highest sensitivity), `synthesize`
(sanitized statements), `dossier` (experience events). Values: `"cloud"`
(default) · `"local"` (on-device via `llm.local_model`) · any explicit model id.

Migrating an existing fabric: `wf repos migrate --dry-run` shows which
per-repo keys would move into overlays; `--apply` writes them. fabric.yaml is
never modified automatically — prune the moved keys once verified.

The vault mirrors each project's effective config as a generated
`projects/<slug>/overlay.yml` view (refreshed by `wf vault`/`wf bootstrap`;
see [CLI Reference](./cli#vault-status-commands-the-human-views)).

## Ignoring files

Exclusion filter applied by capture, entity index, context, lint, rebuild-index,
and okf export.

**One list, auto-classified** (preferred — `ignore.patterns`):

```yaml
ignore:
  patterns:
    - "vendor/**"              # glob (default): fnmatch-style, ** crosses directories
    - "docs/generated/**"
    - "**/*.min.js"
    - "_archive\\d+/"          # regex — auto-detected by metacharacters (\d)
    - "regex:^temp-\\d+\\.tmp$"  # `regex:` prefix forces regex (escape hatch)
```

**Classification rules** for `patterns` entries:

1. `regex:` / `re:` prefix → regex (prefix stripped) — use this for ambiguous strings
2. contains a regex-only metacharacter (`\` `(` `)` `{` `}` `+` `|` `^`) → regex (`re.search` on the posix path)
3. anything else → glob (`fnmatch` on the full path or basename; `**` crosses directories)

**The explicit keys still work** and win for ambiguous strings:

```yaml
ignore:
  globs:                      # always fnmatch-style
    - "vendor/**"
  regexes:                    # always re.search
    - "_archive\\d+/"
  projects:                   # per-repo patterns, merged (union) with global
    my-godot-game:
      patterns:               # unified key works here too
        - "addons/generated/**"
      globs:
        - "addons/third-party/**"
```

Invalid regexes don't crash anything (they're skipped at match time) but
**lint flags them** as `IGNORE-CONFIG` errors — so typos surface at the
0-error gate instead of silently never matching.

## Integrations

All off by default; see [Optional Integrations](./integrations):

```yaml
integrations:
  graphify:
    enabled: true        # call-graph staleness, claim enrichment, graph expansion
    graph_dir: graphify-out
  embeddings:
    enabled: false       # semantic re-ranking (planned)
    model: all-MiniLM-L6-v2
```

## Domains

Domain taxonomy drives classification and context scoping. Start with the
defaults, grow with `python3 scripts/propose-domains.py` (suggests new domains
from evidence signals):

```yaml
domains:
  agent-systems:
    signals: [agent, mcp, fastmcp, opencode, claude]
  web-systems:
    signals: [fastapi, flask, react, nextjs, supabase, postgresql]
```
## Security & privacy

**Where secrets live.** API keys go in `fabric.yaml` only — the file is
gitignored, and the repo's `.gitignore` ships with that exclusion. Never put
keys in `fabric.yaml.example` (committed), page frontmatter, or claims. The
fabric's own pages never store credentials; lint has no secret scanner yet
(roadmap), so the discipline is: keys only in the config file or env vars.

**What data flows where.** The fabric sends *content* to exactly two places:

| Operation | What leaves the machine | To where |
|-----------|------------------------|----------|
| `ingest --extract-claims` on a **cloud-routed** repo | raw document text | your `base_url` endpoint |
| `ingest --extract-claims` on a **`extract: local`** repo | nothing (on-device) | — |
| `synthesize.py` cloud route | sanitized claim statements | your endpoint |
| `synthesize.py` local route | nothing | — |
| `mine-promotions.py` dossier | experience events (cloud route) | your endpoint |
| `wf query` | **nothing** — deterministic retrieval, 0 tokens | — |
| `wf context` | **nothing** — deterministic compilation | — |
| `wf models ensure` | model download request | huggingface.co (metadata + weights only) |

The threat model for sensitive repos: **raw documents are the highest
sensitivity tier** (they may contain internal URLs, credentials-in-comments,
customer names). That's why `extract` is the stage you route `local` — a
private repo's raw docs never reach a cloud endpoint. Synthesized claims are
deliberately sanitized statements, so `synthesize: local` is a second lock;
`dossier` input (experience events) is usually safe for cloud.

**Practical setup for mixed fleets:**

```yaml
# cloud compiler for everything...
llm:
  compiler_model: deepseek-v4.1-flash:cloud

repos:
  public-oss-project: {}            # all stages cloud — fast
  internal-project:
    extract: local                  # raw docs never leave
    synthesize: local               # claims stay local too
    dossier: cloud                  # experience events are fine
```

**Inbound content is screened too.** `wf okf import` runs a deterministic
injection screen on every imported page (zero-width chars, control chars,
"ignore previous instructions" patterns); hits are quarantined to
`evidence/_inbox/<scope>-okf/` for human review instead of entering the
fabric. Trust tiers are recorded, never inherited — see
[OKF v0.2](./okf).

**Team sync** pushes knowledge content to a git remote you own. Use a private
repo for anything sensitive; the harness (scripts/schemas) never syncs.

---

Next: [See the workflows this config drives](./core-workflows)
