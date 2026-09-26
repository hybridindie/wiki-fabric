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
| `wf doctor [--json]` | Environment diagnosis: endpoint reachability, model resolution (phantom compiler_model), compiler-eval readiness, judgment-tier availability, vault drift, gate — each failure names its fix |
| `wf vault [PATH]` | Scaffold/audit the Obsidian output vault |
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
| `wf review --check [--project <slug>]` | Staleness report: current, due for review, overdue, stale |
| `wf review --verify <claim-id>` | Re-verify a claim (stamps last_verified, rolls review_after forward by tier) |
| `wf review --auto-reverify` | Mechanically re-verify all overdue claims (sha256 + quote check, 0 tokens) |
| `wf gate [--quiet\|--json\|--write-manifest]` | Aggregate every pending human decision (overdue/stale claims, promotion dossiers, domain proposals) into one report. Exit 1 when anything is actionable. `--write-manifest` persists `registry/pending-gate.md` for the AI harness to read at session start. |
| `wf promote-domains {list\|--apply <dossier>}` | Human-gated merge of an approved domain proposal into `domains/ontology.md` |
| `wf export wiki [--mode m\|llm\|hybrid] [--project <slug>]` | Generate the human-layer wiki: topic articles, project retrospectives, staleness dashboard. Writes OpenWiki-style pages (SUMMARY lead, Key Takeaways, Sources backtrace, provenance stamp), validates/repairs Mermaid diagrams, and emits the citation graph (`registry/wiki-graph.json`). Browse the [[wikilinks]] in Obsidian's native Graph view. |
| `wf mine chats <project> [--llm] [--dry-run]` | Distill captured chat transcripts into durable takeaways (patterns, anti-patterns, workflows; transients filtered) |
| `wf version` | Show wf version + CLI sync state (installed `~/.local/bin/wf` vs harness script) |
| `wf repos migrate [--dry-run\|--apply\|--prune]` | Move per-repo routing from fabric.yaml into project overlays |
| `wf lint [--okf] [--format json]` | Deterministic linter (full profile; `--okf` = OKF conformance floor; JSON for CI) |

Environment: `WIKI_FABRIC_REPO` overrides the source repo URL.

---

## Scripts Reference

Scripts live in four subdirectories of `scripts/` — `cmd/` (entrypoints), `eval/`,
`harness/`, and shared `lib/`. Each runs standalone: `python3 scripts/cmd/<name>.py --help`.

### `cmd/` — CLI commands

| Script | Purpose | LLM Cost |
|--------|---------|----------|
| `capture.py` | Capture upstream repo docs → `evidence/raw/` | 0 |
| `capture-git.py` | Capture git history (PR/issue threads, commits) | 0 |
| `capture-chat.py` | Capture agent-harness chat sessions as chat-transcript evidence | 0 |
| `ingest.py` | Source → source record → claims (LLM extraction) | 1 call per source |
| `query.py` | Question → evidence-backed answer | 0 tokens (lexical + graph) |
| `context.py` | Task → scoped context manifest with reasons (`--write-receipt` persists a receipt-v1 artifact) | 0 tokens |
| `lint.py` | Deterministic checks (incl. `--okf` floor, `llm.local_model`) | 0 |
| `synthesize.py` | Claims → concept pages (cloud or on-device route) | 1 per concept |
| `log-experience.py` | Capture experience event | 0 |
| `mine-promotions.py` | Cluster experience events → dossiers | 0 |
| `promote.py` | Manage pattern promotion dossiers | 0 |
| `propose-domains.py` | Discover + propose new domains (pending-review dossiers) | 0 |
| `promote-domains.py` | Human-gated merge of a proposed domain into the ontology | 0 |
| `gate.py` | Aggregate pending HITL decisions (`wf gate`) | 0 |
| `rebuild-index.py` | Rebuild `registry/catalog.json` from files | 0 |
| `build-entity-index.py` | AST entity index from source repos | 0 |
| `bootstrap-project.py` | Connect a new project to the fabric | 0 |
| `ensure-local-model.py` | Check/download `llm.local_model` (`wf models ensure`) | 0 |
| `review.py` | Staleness scan + re-verify loop (`wf review`) | 0 |
| `export-wiki.py` | Human-layer wiki renderer (topics, projects, staleness) | 0–1 per topic |
| `mine-chats.py` | Distill chat transcripts into durable takeaways | 0 or 1/session |
| `repos-migrate.py` | Move per-repo routing from fabric.yaml into overlays | 0 |
| `okf_export.py` / `okf_import.py` | OKF bundle export / import (`wf okf`) | 0 |

### `harness/` — agent-integration

| Script | Purpose | LLM Cost |
|--------|---------|----------|
| `harnesses.py` | Multi-harness registry + installer (11 agent tools) | 0 |
| `skill.py` | Universal skill loader (prints procedures) | 0 |
| `hooks.py` | Git post-commit/post-merge capture+ingest hooks (code commits also run the graphify cycle when enabled) | 0 |
| `always_on.py` | Legacy always-on installer (superseded by `wf harness install`) | 0 |
| `graphify-bridge.py` | Optional graphify integration (update/import/enrich/diff) | 0 |

### `eval/` — evaluation family

`eval.py`, `eval-behavior.py`, `eval-stability.py`, `eval-pr-replay.py`, `eval-real-repo.py` — golden corpus, behavior, stability, PR-replay, and real-repo evaluations.

### `lib/` — shared modules (imported, not entrypoints)

| Module | Purpose |
|--------|---------|
| `fabric_config.py` | fabric.yaml loading, stage routing, actor conventions, local model |
| `extract_backends.py` | Claim-extraction layer: prompt building, 4 LLM backends, JSON repair |
| `local_llm.py` | On-device generation (GGUF/MLX), serialized model cache |
| `wf_common.py` | Shared helpers: `parse_frontmatter`, `norm`, `slugify`, hashing |
| `eval_core.py` | Eval scoring primitives: `concept_match`, `jaccard`, `fuzzy_coverage` |

Shell scripts stay at `scripts/` root: `wiki-fabric.sh`, `demo.sh`, `smoke-test.sh`, `setup-vault.sh`, `apply-changeset.sh`.

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

### `wf vault [PATH] [--check]` — the vault is standalone OUTPUT

The vault is the **result** of the utility, never a mirror: wiki-fabric reads
the corpus and writes generated content (the rendered wiki) *into* it. It never
copies or symlinks source content (evidence/, claims/, patterns/, projects/,
registry/) into the vault — those live only in the fabric. Because the vault is
standalone output, you can point `vault.path` at several targets to get
multiple vaults on one machine (e.g. work vs personal).

`wf vault` scaffolds the output directory + `.obsidian/` workspace and audits
it: it flags a missing generated wiki, and flags stale leftovers from the
older mirror model (corpus dirs or symlinks that don't belong in an output
vault) — it does **not** delete them. The actual wiki pages are generated by
`wf export wiki` into the vault. `wf vault --check` exits 1 on drift
(CI-friendly).

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
