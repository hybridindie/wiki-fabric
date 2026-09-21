---
type: index
title: "CLI & Scripts Reference"
description: "wf commands, note types, scripts, shared modules"
created: 2026-09-19
updated: 2026-09-19
---

# CLI & Scripts Reference


Every `wf` command, every page type, and the module layout of the harness. For configuration (providers, routing), see [Configuration](./configuration).

## Note Types

Every page in the fabric is one of twelve types. The type drives what lint
demands of it and who can change its status — that's how a claim and a pattern
can have different trust rules. The ones you'll touch daily are `claim`,
`experience-event`, `pattern`, and `decision`.

| Type | Location | Purpose |
|------|----------|---------|
| `source` | `evidence/sources/` | Immutable bibliographic record + sha256 |
| `source-summary` | `evidence/source-summaries/` | Faithful summary with locators, no inference |
| `claim` | `evidence/claims/` | Atomic assertion with `source_refs` (locator + quote) + `code_symbols` + `graph_edges` |
| `concept` | `concepts/` or `domains/<d>/concepts/` | Stable explanation built ONLY from linked claims |
| `experience-event` | `projects/<p>/experience-events/` | Structured observation: problem → intervention → outcome |
| `pattern` | `patterns/` | Reusable context→problem→forces→solution (maturity 0–3) |
| `anti-pattern` | `anti-patterns/` | Repeated failure mode; detect and warn |
| `skill` | `skills/` | Reusable procedure with inputs/outputs |
| `decision` | `projects/<p>/decisions/` | ADR-like technical choice record |
| `entity` | `global/entities/` | Code-symbol index from AST parsing |
| `change-set` | `evidence/traces/change-sets/` | Agent-proposed edit batch for human review |
| `synthesis` | `syntheses/` | Query answer filed for reuse |

**See `schemas/frontmatter.md` for full contracts.**

### Lifecycle: how pages move through statuses

Types carry a status vocabulary, and transitions are gated — some by lint,
some by humans. The two lifecycles you interact with daily:

**Claims** (evidence lifecycle):

```text
proposed ──(locator verified)──> supported ──(newer claim wins)──> superseded
    │                                │
    └──(evidence contradicts)──> contested          retracted (bad quote/source)
```

- `proposed`: extracted but unverified (no `source_refs` required yet)
- `supported`: locator-verified, quote verbatim — lint *demands* source_refs
- `contested`: contradicted by another claim — both stay visible with
  `contradicts` relations; a human settles it, a model never averages it
- `superseded`: requires `superseded_by: [[claim-...]]` — chains can't loop

**Patterns (maturity ladder):**

```text
candidate (m0-m1) ──(observed in ≥2 independent projects)──> recommended (m2) ──(human review)──> standard (m3)
      │                                                                                      │
      └────────────────────── deprecated ←──────────── any time ─────────────────────────────┘
```

- `recommended` is **lint-enforced** to have maturity ≥ 2 and evidence from
  ≥2 independent projects (independent = the observations came from different codebases, not one project copied to another (the independence rule))
- `standard` requires a `human:` verifier — the machine can never bless a
  pattern into load-bearing status
- `deprecated` keeps the page for history; context compilation stops selecting it

Who does what: **agents** propose (claims, change-sets, dossiers — always
staged, never merged silently); **humans** promote (merge change-sets, approve
dossiers, set `standard`). The gates are where governance lives.

---

## CLI Reference (`wf`)

The `wf` command is the single entry point for controlling the fabric. It installs to `~/.local/bin/wf` (alias `wiki-fabric`).

| Command | Purpose |
|---------|---------|
| `wf install [--repo URL] [--dir DIR]` | Clone + set up the fabric |
| `wf update` | Pull latest, rebuild entity index + catalog, lint, refresh installed CLI + project hooks |
| `wf status` | Fabric health + inventory counts |
| `wf vault [PATH]` | Create Obsidian vault (symlinks) |
| `wf bootstrap <project-path>` | Connect a project to the fabric |
| `wf capture <project-slug> [--repo PATH]` | Capture upstream repo docs → `evidence/raw/` |
| `wf capture <project-slug> --git <owner/name-or-path>` | Capture PR/issue threads + high-signal commits → `evidence/raw/<slug>/git/` (add `--since 6m`, `--limit 30`, `--churn`) |
| `wf ingest <source> [--extract-claims]` | Ingest a source (LLM claim extraction) |
| `wf query "<question>"` | Ask the fabric a question |
| `wf log --project <slug> ...` | Log an experience event |
| `wf hook {install\|uninstall\|status}` | Git post-commit auto-capture+ingest (`--extract-claims` for LLM on drift) |
| `wf claude legacy` | Pre-harness always-on installer (`always_on.py`; superseded by `wf harness install`) |
| `wf okf export --out DIR [--scope S]` | Export the fabric as a deterministic portable OKF v0.2 bundle |
| `wf okf import <bundle> [--scope S]` | Ingest an external OKF bundle as immutable evidence (trust recorded, not inherited) |
| `wf sync {init\|status\|push\|pull}` | Share the corpus with a team via a git remote |
| `wf skill [--list] [<name>]` | Print the procedure for a workflow (`ingest`, `promote`, `refresh`) — universal across all agent harnesses |
| `wf harness {install\|status} [--all\|--only k1,k2] [--force]` | Install always-on + skills into detected agent harnesses (11 supported; `wf claude` is the legacy alias) |
| `wf models ensure [--model ID] [--yes]` | Check `llm.local_model` is cached; offer human-gated download (`--check` exits 0/1 without prompting) |
| `wf lint [--okf] [--format json]` | Deterministic linter (full profile; `--okf` = OKF conformance floor; JSON for CI) |

Environment: `WIKI_FABRIC_REPO` overrides the source repo URL.

---

## Scripts Reference

Pipeline scripts (each runs standalone: `python3 scripts/<script>.py --help`):

| Script | Purpose | LLM Cost |
|--------|---------|----------|
| `ingest.py` | Source → source record → claims (LLM extraction) | 1 call per source |
| `query.py` | Question → evidence-backed answer | 0 tokens (lexical + graph) |
| `context.py` | Task → scoped context manifest with reasons | 0 tokens (deterministic) |
| `lint.py` | Deterministic checks (incl. `--okf` floor, `llm.local_model` validation) | 0 tokens |
| `eval.py` | Golden-corpus evaluation | 1 call per fixture |
| `synthesize.py` | Claims → concept pages (cloud or on-device route) | 1 call per concept |
| `log-experience.py` | Capture experience event | 0 tokens |
| `mine-promotions.py` | Cluster experience events → dossiers (honors `dossier` route) | 0 tokens |
| `promote.py` | Manage promotion dossiers | 0 tokens |
| `rebuild-index.py` | Rebuild registry index from files | 0 tokens |
| `propose-domains.py` | Discover new domains from evidence | 0 tokens |
| `build-entity-index.py` | AST entity index from source repos | 0 tokens |
| `graphify-bridge.py` | Optional graphify integration (update/import/enrich/diff) | 0 tokens |
| `bootstrap-project.py` | Connect new project to fabric | 0 tokens |
| `ensure-local-model.py` | Check/download `llm.local_model` (`wf models ensure`) | 0 tokens |
| `bootstrap-fabric.sh` | One-time global install | 0 tokens |
| `apply-changeset.sh` | Apply a change-set (the change-set apply script) | 0 tokens |

Shared modules (imported by the scripts above; not entry points):

| Module | Purpose |
|--------|---------|
| `fabric_config.py` | fabric.yaml loading (memoized), stage routing, actor conventions, local-model resolution/download |
| `extract_backends.py` | Claim-extraction layer: prompt building, 4 LLM backends (OpenAI-compatible/Anthropic/opencode/on-device), JSON repair, locator verification |
| `local_llm.py` | On-device generation: backend dispatch (GGUF via llama-cpp, MLX via mlx-lm), serialized model cache |
| `wf_common.py` | Shared helpers: `parse_frontmatter`, `norm`, `slugify`, hashing, timestamps |
| `eval_core.py` | Eval scoring primitives: `concept_match`, `jaccard`, `fuzzy_coverage`, `tokens` |

---

---

## Fabric Inventory

Counts live in your fabric, not the repo. Check yours anytime:

```bash
wf status
```

The repo ships only the harness — templates, examples (`templates/examples/`), schemas, and scripts. Your claims, captures, and patterns accumulate locally as you connect projects.

---

## Vault & status commands (the human views)

### `wf vault [PATH] [--check]` — browse the fabric in Obsidian

Creates a directory of **symlinks** to the fabric's human-readable content
(`AGENTS.md`, `concepts/`, `patterns/`, `skills/`, `evidence/`, ...). Obsidian
follows symlinks, so you browse and graph the real files with zero duplication
— edit in the vault, and you're editing the fabric. Default location is
beside the fabric (`<fabric-parent>/vault`); pass a path to override; existing
`.obsidian/` workspace config is preserved.

**Freshness guarantee, three layers:**

1. **View freshness — structural.** The vault holds symlinks, not copies: a
   fabric write is visible immediately. The vault cannot go stale.
2. **Structural freshness — `wf vault` is idempotent and self-healing**:
   repairs broken links, links new top-level dirs, and regenerates each
   project's `projects/<slug>/overlay.yml` view (the fabric-side snapshot of
   the project's overlay config). It runs automatically on `wf bootstrap`,
   `wf update`, and can be audited anytime:
   `wf vault --check` (exit 1 on drift — CI-friendly).
3. **Content freshness — governance, not the vault**: sha256 drift,
   `review_after` gates, graphify AST diff (see [Governance](./governance)).

`wf status` shows the vault verdict (`fresh` / `structure drift — run: wf vault`)
inline, so staleness is one glance away.

### `wf repos migrate` — config-per-project migration

Moves explicit per-repo routing keys from fabric.yaml into each project's
`.wiki-overlay.md` (`--dry-run` to preview, `--apply` to write). fabric.yaml
stays untouched — prune by hand after verifying. New projects don't need it:
`wf bootstrap --extract local` writes routing directly.

### `wf status` — the health dashboard

One screen answering "is my fabric healthy": fabric + vault locations, the
three models (ops / compiler / local, with the local model's cache state),
inventory counts (claims, sources, concepts, patterns, projects, entities),
lint verdict, graphify import state.

### `wf integrations` — what's active

Lists optional integrations with their state and effect:

```text
✓ graphify: ENABLED (call-graph staleness, claim enrichment, graph expansion)
     commands: graphify-bridge.py --all | --diff | --status
```

Inactive integrations print their enable command and what they'd change —
so the dashboard doubles as documentation of the delta (full table in
[Integrations](./integrations)).

---

Next: [Something not working? Troubleshooting](./troubleshooting)
