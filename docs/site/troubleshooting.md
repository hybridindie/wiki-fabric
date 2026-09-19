---
type: index
title: "Troubleshooting"
description: "Common failure modes and fixes — backends, downloads, providers, hooks"
created: 2026-09-19
updated: 2026-09-19
---

# Troubleshooting

Symptom-first index of the failure modes we know about. Anything not here —
[file an issue](https://github.com/hybridindie/wiki-fabric/issues).

## Installation & environment

### `wf` command not found after install

The one-liner symlinks `wf` into `~/.local/bin/`. If that directory isn't on
your `PATH`:

```bash
export PATH="$HOME/.local/bin:$PATH"   # add to .zshrc / .bashrc
```

### uv can't be installed → fallback mode

`wf` falls back to plain `python3` when uv is unavailable. Core commands
(status, query, context, lint) work; LLM-dependent commands need deps:

```bash
pip install -r requirements.txt   # pyyaml, openai, anthropic
```

### Tests fail with `ModuleNotFoundError: huggingface_hub`

The fast venv (`requirements.txt`) doesn't include model-backend deps by
design. The ensure/download tests skip automatically. To run them:

```bash
pip install -e ".[local]"         # huggingface_hub + backend for your platform
python3 -m pytest tests/test_local_model.py -m live
```

## LLM providers

### `OpenAI-compatible extraction failed: <error>`

Check, in order:

1. Endpoint reachable: `curl $WIKI_LLM_BASE_URL/models` (or the `base_url` from fabric.yaml)
2. Model name spelled as the server expects — Ollama needs the exact tag (`qwen2.5-coder:7b`); OpenRouter/OpenAI take their own ids
3. `WIKI_LLM_TIMEOUT` (default 600s) — reasoning models on long extractions may need more
4. API key: Ollama ignores it; anything else needs a real key

Extraction chains through fallbacks automatically
(OpenAI-compatible → Anthropic → opencode CLI). The stderr messages tell you
which layer failed.

### Reasoning models return 0 claims

DeepSeek-style reasoning models can spend the whole token budget thinking and
never emit the JSON array. The extractor already retries on
`finish_reason=length` — if you still get zero claims, lower
`WIKI_MLX_REASONING=low` (on-device) or pick a non-reasoning compiler model.

## On-device models (GGUF / MLX)

### `mlx backend unavailable` / `mlx-lm not installed`

mlx-lm only exists on Apple Silicon macOS. On other platforms use the GGUF
backend: set `llm.local_model: unsloth/gemma-4-e4b-it-GGUF` (or any `*.gguf`
id) in fabric.yaml — llama-cpp-python runs everywhere. Install:

```bash
pip install -e ".[local]"
```

### `local model '<id>' not found locally; download with: wf models ensure`

The model isn't in your HuggingFace cache. Interactive runs offer a y/N prompt
automatically; non-interactive environments (CI, scripts) print the hint and
continue. Pre-fetch explicitly:

```bash
wf models ensure --yes            # download llm.local_model without prompting
wf models ensure --model <hf-id>  # specific model
wf models ensure --check          # exit 0/1 for scripts, no prompt
```

### `no .gguf file found for '<id>'`

GGUF repos ship many quantization splits; the resolver prefers Q4_K_M at the
repo root. If your repo keeps quants in subdirectories, download the file
manually and point `llm.local_model` at a **local path** instead of an HF id.

### `download failed: 401/403` (private/gated models)

Gated HF repos need a token: `export HF_TOKEN=...` (huggingface_hub reads it),
or download manually and point `llm.local_model` at the local directory.

### GGUF output is empty / synthesis falls back

Some chat-tuned models return nothing from raw text completion. The on-device
backend routes chat-tuned models through their chat template automatically —
if you hit this with an explicit local dir (not an HF id), make sure the dir
contains the model's `*.gguf` plus tokenizer files. The failure path prints
`local synthesis failed ... — falling back`; extraction then uses your cloud
compiler model (check stderr to confirm which backend actually ran).

## Git hooks

### Hook doesn't fire / capture never runs

```bash
wf hook status    # per-repo hook state
```

- The hook skips commits touching only fabric-owned paths (`evidence/`,
  `registry/`, …) — that's the anti-loop rule, not a bug.
- `WIKI_SKIP_HOOK=1 git commit ...` skips once per command.
- Hook output goes to `~/.cache/wiki-fabric-hook.log` (detached; commit
  returns instantly).

### Hook triggered ingest on every commit

You installed with `--extract-claims`; each drift commit runs an LLM call.
Re-install without the flag for capture-only (0 tokens), ingest manually with
`wf ingest --changed <slug> --extract-claims` when you want extraction.

## Config & lint

### `LLM-CONFIG llm.local_model: '...' does not look like an on-device model id`

Ollama-style tags (`qwen2.5-coder:7b`) and provider-namespaced ids
(`openai/gpt-4o`) can't run on-device. Use an HF id (`mlx-community/*`,
`unsloth/*`), a `*.gguf` file, or an existing local path.

### Lint passes locally, okflint fails in CI

The external validator reads `okf-base.yaml`. If you added a new
generated/non-fabric directory (like a docs build), add it to
`exclude_patterns` in [okf-base.yaml](https://github.com/hybridindie/wiki-fabric/blob/main/okf-base.yaml)
so the two linters agree on what's a concept page.

### `SOURCE-DRIFT` errors after re-capture

Hash drift means the raw file changed since its claims were extracted —
exactly the signal the fabric is designed to catch. Re-ingest the affected
sources (`wf ingest --changed <slug>`) to produce a change-set, then review
and merge.

## Where to look when something else breaks

- `wf status` — health, inventory, all three models, lint summary
- `~/.cache/wiki-fabric-hook.log` — hook activity
- `registry/log.md` — the fabric's own operation timeline
- stderr: every extraction/backend fallback prints why it fell back

---

Next: [Back to Configuration](./configuration)
