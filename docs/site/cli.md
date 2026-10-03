---
type: index
title: "CLI & Scripts Reference"
description: "wf commands, note types, scripts, shared modules"
created: 2026-09-19
updated: 2026-09-27
---

# CLI & Scripts Reference


Every `wf` command, every page type, and the module layout of the harness. For configuration (providers, routing), see [Configuration](./configuration).

## Note Types

Every page in the fabric is one of 24 types (VALID_TYPES in lint.py — the corpus has grown; the lint code is the source of truth). The type drives what lint
demands of it and who can change its status — that's how a claim and a pattern
can have different trust rules. The ones you'll touch daily are `claim`,
`experience-event`, `pattern`, and `decision`.

| Type | Location | Purpose |
|------|----------|---------|
| `source` | `evidence/sources/` | Immutable bibliographic record + sha256 |
| └ capture kinds | `evidence/raw/<slug>/git/`, `evidence/raw/<slug>/chats/` | `kind:`-discriminated capture shapes (#156): `pr-record` (github route — `source_repo`/`pr`/`pr_state`/`merged_at`, thread-graph node), `commit` (local route — sha + date + message, metadata only), `chat-session` (`session`/`harness`/`session_started`/`files_touched`/`related_sessions`). Contracts: schemas/frontmatter.md §source |
| `source-summary` | `evidence/source-summaries/` | Faithful summary with locators, no inference |
| `claim` | `evidence/claims/` | Atomic assertion with `source_refs` (locator + quote) + `code_symbols` + `graph_edges` |
| `concept` | `concepts/` (unbound) or `domains/<domain>/concepts/` (bound; canonical via the ontology alias map) | Stable explanation built ONLY from linked claims |
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
| `uv tool install wiki-fabric` | Install the tool (one line, atomic — the packaged mode; `--with mcp` adds the MCP server) |
| `wf install [--dir DIR] [--with-graphify]` | Create the fabric content skeleton + starter `fabric.yaml` at `WIKI_FABRIC_DIR` (or cwd); the corpus is content — sync it with `wf sync setup/init` |
| `wf update` | Dev mode: pull the harness + rebuild hooks/index/catalog. Packaged mode: hints `uv tool upgrade wiki-fabric` (content updates are `wf sync pull`, not tool updates) |
| `wf status` | Fabric health + inventory counts |
| `wf doctor [--json]` | Environment diagnosis: endpoint reachability, model resolution (phantom compiler_model), compiler-eval readiness, judgment-tier availability, vault drift, gate — each failure names its fix |
| `wf completions {bash\|zsh\|fish}` | Emit a shell completion script on stdout — verbs + subcommands (`mine chats\|promotions`, `eval behavior\|…`, `sync …`) + common flags per verb. Install: `eval "$(wf completions bash)"` (bash); `wf completions zsh > "${fpath[1]}/_wf" && compinit` (zsh); `wf completions fish > ~/.config/fish/completions/wf.fish` (fish). Static generation — never breaks offline |
| `wf status --json` | The inventory/provenance surface as JSON for agents/hooks: fabric/vault paths, CLI mode, LLM config, inventory counts + connected repos, per-repo capture provenance (last capture, window, git/chats counts), lint health, gate sections, graphify state |
| `wf projects [--json]` | Connected repos one-per-block: slug, path, owner, extract route, capture counts (raw/git/chats/claims), last git capture + window; `--json` for agents |
| `wf overlay-track [--dry-run]` | Track every connected project's `.wiki-overlay.md` in its repo (H4 sweep): stages + commits untracked overlays — a second machine's clone then carries the config. Idempotent; tracked repos skip. Lint (`OVERLAY-UNTRACKED`) + doctor name anything left |
| `wf vault [PATH]` | Scaffold/audit the Obsidian output vault |
| `wf update` | Tool upgrade + auxiliary refresh (hooks reinstall from config, entity index, catalog) — packaged mode prints `uv tool upgrade wiki-fabric`; see [Upgrading wf](./upgrading) |
| `wf bootstrap <project-path>` | Connect a project to the fabric |
| `wf capture <project-slug> [--repo PATH]` | Capture upstream repo docs → `evidence/raw/`. Exit codes: 0 nothing new, 2 drift captured, 3 unknown project slug (with the connected-project list — hooks/CI can detect a typo) |
| `wf capture <project-slug> --git <owner/name-or-path>` | Capture PR/issue threads + high-signal commits → `evidence/raw/<slug>/git/` (`--since 6m` window, `--limit 30` BUDGET — the window auto-shrinks to fit an active repo, never truncates; `--until` backfill bound; threads paginate + flag truncation, the count persists in `.last-capture` as `truncated=N` and surfaces in `wf status`; `--churn`; `--since-state` incremental hooks; knobs: `tuning.git_history` + `repos.<slug>.git_history`). Unknown slug exits 3 (the #167 table). **`--until` does not compose with `--since-state`** — separate flows by design: `--since-state` means "incremental from the recorded base" (the recurring path), `--until` means "one bounded backfill slice" (an explicit, opt-in window override); composing them would put two bounds on the same axis. Never captured + want the slice? Run one `--until` slice first, then `--since-state` picks up from there |
| `wf capture chat <project-slug>` | Capture agent chat sessions → `evidence/raw/<slug>/chats/` (harnesses: claude, opencode, codex, gemini — auto-detects; `--since 90d`, `--min-turns`, `--harness <name>`) |
| `wf capture issues <project-slug> --tracker github --repo owner/name` | Capture tracker issues + comment threads → `evidence/raw/<slug>/issues/` (#176; `kind: issue-record` thread nodes): `--since 6m` updatedAt window + budget (shrink-not-truncate), `--since-state` incremental (own state stamp `<slug>-issues`), `--until` backfill slice (separate flow), `--no-comments`; deterministic density pre-filter (threads/rationale/acceptance-criteria kept, chores skipped). The WHY channel: PRs carry what, chats how, issues why (spike: 44 claims/3 issues, ~7% metadata noise) |
| `wf context --task "<task>" [--project <slug>] [--paths P] [--write-receipt] [--format json] [--judge-borderline]` | Compile the task-scoped context manifest (0 tokens; `--write-receipt` persists a delivery receipt). `--judge-borderline`: opt-in judged re-rank of borderline beyond-`--max` candidates (needs `integrations.judgment`; per-item receipt record) |
| `wf ingest <source> [--extract-claims]` | Ingest a source (LLM claim extraction; claims carry provenance edges from chat/PR captures) |
| `wf ingest --changed <slug> [--budget N]` | Ingest only NEW/CHANGED raw files for a project (sha256 anti-loop; `--budget`/`tuning.ingest.budget` caps the run — re-run continues). Drift before ingest: old-revision claims mechanically flip contested+stale_after (0 tokens) |
| `wf ingest --pending <slug> [--budget N]` | Claim-extract recorded-but-unextracted sources (anti-loop safe; budgeted like --changed) |
| `wf ingest --reclaim <slug>` | Recover zero-claim ingested sources → back to pending (silent-orphan recovery, #93) |
| `wf query "<question>" [--no-rerank]` | Ask the fabric a question (lexical + graph expansion; lineage-shaped queries gain an evidence-graph provenance section; graphify symbol discovery when enabled; optional System One fusion rerank — a local decision model reorders the top candidates, latency-budgeted, silent fall-back to lexical order) |
| `wf freshness [--dry-run] [projects...]` | Scheduled upstream-freshness cycle (0 tokens): capture-git `--since-state` + mechanical auto-reverify per connected repo — **including the newest-wins contradiction sweep** (#175; a demotion is gate-worthy drift); scheduled on the corpus CI by `sync setup/init` (opt-in var `WIKI_FABRIC_FRESHNESS=1`); drift flags land in `wf gate`. Exit: 0 clean, 1 drift recorded, 2 hard failure (no fabric / unknown slug — the connected list names the fix) |
| `wf thread <session-or-claim-id> [--stats] [--json]` | Evidence-graph thread lookup: claims citing the session/PR, files touched, continuation edges |
| `wf log --project <slug> ...` | Log an experience event |
| `wf remember <project> --note "..." [--kind feedback|project|user|reference]` | **Friction-free memory note** (#177 S6 — the auto-memory lesson): one line, 0 tokens, no LLM, no claim ceremony. Mining reads standing notes (a repeated note becomes a promotion candidate); ephemeral - auto-expiry (feedback 45d / project 30d / user 90d / reference 90d; `--expire` sweeps, `--dry-run` reports). `--list` shows standing notes |
| `wf hook {install\|uninstall\|status\|reinstall}` | Git post-commit auto-capture+ingest (`--extract-claims` for LLM on drift). The commit body (v6) also runs the commit-time LAYOUT-GUARD on the harness repo's own scripts — a corpus-path re-spell fails the commit with the fix pointer, not at the next test run |
| `wf claude legacy` | Pre-harness always-on installer (`always_on.py`; superseded by `wf harness install`) |
| `wf okf export --out DIR [--scope S]` | Export the fabric as a deterministic portable OKF v0.2 bundle |
| `wf okf import <bundle> [--scope S]` | Ingest an external OKF bundle as immutable evidence (trust recorded, not inherited) |
| `wf sync {setup\|init\|status\|push\|pull\|resolve\|commit-drift}` | Share the corpus with a team — `setup` uses the gh CLI to create + publish the corpus repo; `resolve` without `--strategy` runs the interactive resolver (diff + pick ours/theirs/union/skip). Team mode (`sync.mode: team`) opens one PR per push — evidence auto-merges on green CI, atoms wait for human review; `sync push --pr` opts in per-invocation; `commit-drift` stages + commits hook-accumulated drift with a plane-classified summary (never pushes); init/setup scaffold `promotion-queue.md` + `questions/` | The full upgrade ritual (tool → skills → hooks → corpus verify) lives in [Upgrading wf](./upgrading).
| `wf skill [--list] [<name>]` | Print the procedure for a workflow (`ingest`, `promote`) — universal across all agent harnesses |
| `wf harness {install\|status} [--all\|--only k1,k2] [--force]` | Install always-on + skills into detected agent harnesses (11 supported; `wf claude` is the legacy alias) |
| `wf models ensure [--model ID] [--yes]` | Check `llm.local_model` is cached; offer human-gated download (`--check` exits 0/1 without prompting) |
| `wf review --check [--project <slug>]` | Staleness report: current, due for review, overdue, stale |
| `wf review --verify <claim-id>` | Re-verify a claim (stamps last_verified, rolls review_after forward by tier) |
| `wf review --auto-reverify` | Mechanically re-verify all overdue claims (sha256 + quote check, 0 tokens) |
| `wf review --verify-sources [--dry-run]` | Mechanically drive the SOURCE lifecycle (#160): sha256 recompute per record — fresh rolls `review_after` (capture-kind tier: pr/commit 30d, chats 45d, docs 180d), upstream-drifted stamps `stale_after`, upstream-DELETED expires the record (`status: expired` — provenance tombstone, excluded from context) (0 tokens) |
| `wf review --contradiction-sweep [--dry-run] [\|--json]` | Newest-wins demotion (#175): a claim contradicted by a STRICTLY NEWER still-supported claim mechanically flips `contested` + `stale_after` (reason line records the contradictor). Carriers: hand-written `contradicts` relations + `registry/effects/` judged verdicts. Restore is automatic when the contradictor loses support (or `--restore-demoted <claim>` by hand); `--demoted` lists the demoted set. Equal clocks never demote (intra-batch reads stay human-owned). Exit 1 when a demotion landed (gate-worthy) |
| `wf review --verify-locators` | Re-check every claim's locator against its raw source: rewrite drifted locators, repair backtick-elision quotes, restore wrongly-contested claims, strip stamps + contest vanished quotes (0 tokens, #109) |
| `wf gate [--quiet\|--json\|--write-manifest\|--deliveries]` | Aggregate every pending human decision (overdue/stale claims, promotion dossiers, domain proposals, pattern candidates, open questions, + knowledge sources going dark — projects with no contribution in 30d, info tier) into one report. Exit 1 when anything is actionable. `--write-manifest` persists `registry/pending-gate.md`; `--deliveries` surfaces recent context receipts (was the manifest right?) |
| `wf relocate-concepts [--dry-run]` | Move domain-bound concepts to their physical homes `domains/<domain>/concepts/` (S1 migration; deterministic, idempotent, alias-folded, 0 tokens) |
| `wf promote-domains {list\|--apply <dossier>}` | Human-gated merge of an approved domain proposal into `domains/ontology.md` |
| `wf propose-domains [--dry-run]` | Propose new domains from corpus clusters (0 tokens; staged for human review) |
| `wf harvest-questions [--project <slug>] [--dry-run]` | Harvest concept open-questions → staged question pages (priority from claim confidence, 0 tokens) |
| `wf promote-questions {--list\|--open\|--apply <id>\|--reject <id> --reason}` | Human-gated apply/reject of harvested questions (`--open` lists canonical open questions) |
| `wf verify-effects <claim.md>... [--source <slug>] [--max-pairs N]` | Judged effect verification at ingest (independent second opinion; writes `<claim>.effects.json`) |
| `wf wiki-generate {begin\|next\|submit\|finish\|status\|inspect}` | Wiki-generation bookkeeper (writer/bookkeeper split): durable page queue, sparse claim deltas, citation validation, run checkpoints |
| `wf publish [--out DIR]` | Publish the wiki as a static site (Quartz v4, pinned revision; graph view + search) |
| `wf utility [--dry-run\|--json]` | Receipt↔outcome join → usage counts on pattern pages (0 tokens) |
| `wf integrations` | Show optional-integration state (graphify, obsidian, judgment, embeddings) + what each changes |
| `wf export wiki [--mode mechanical\|llm\|hybrid] [--project <slug>]` | Generate the human-layer wiki: topic articles, project retrospectives, staleness dashboard. Writes OpenWiki-style pages (SUMMARY lead, Key Takeaways, Sources backtrace, provenance stamp), validates/repairs Mermaid diagrams, and emits the citation graph (`registry/wiki-graph.json`). Browse the [[wikilinks]] in Obsidian's native Graph view. |
| `wf export-viz [--out DIR]` | Export the static wiki-graph viewer (#177 S5): self-contained `index.html` + `graph.json` (the citation graph the export builds) - static-host ready, no live reload |
| `wf mine chats <project> [--llm] [--propose] [--dry-run]` | Distill captured chat transcripts into durable takeaways (transients filtered); `--propose` stages pattern/anti-pattern candidates in `patterns/_inbox/` (gated, provenance-cited, idempotent) |
| `wf mine promotions [--judge] [--min-projects N]` | Cluster experience events → promotion dossiers (deterministic, 0 tokens; `--judge` for the near-miss judgment tier) |
| `wf promote-patterns {--list\|--apply <id>\|--reject <id> --reason}` | Human-gated apply/reject of chat-mined pattern candidates |
| `wf version` | Show wf version + CLI sync state (installed `~/.local/bin/wf` vs harness script) |
| `wf --version` / `wf -v` | Same version one-liner as a flag (packaged mode: version + harness root) |
| `wf help <command>` | Per-verb help — routes to the underlying script's argparse (`wf help ingest` = `wf ingest --help`); unknown names get nearest-verb suggestions |
| `wf repos migrate [--dry-run\|--apply\|--prune]` | Move per-repo routing from fabric.yaml into project overlays |
| `wf lint [--okf] [--format json]` | Deterministic linter (full profile; `--okf` = OKF conformance floor; JSON for CI) |

## MCP Server

`wf-mcp` (installed with `uv tool install wiki-fabric --with mcp`) exposes the fabric's core surface as native MCP tools for any MCP client:

| Tool | Wraps | Cost |
|---|---|---|
| `fabric_query` | `wf query` | 0 tokens |
| `fabric_context` | `wf context` | 0 tokens |
| `fabric_gate` | `wf gate` | 0 tokens |
| `fabric_thread` | `wf thread` | 0 tokens |
| `fabric_log` | `wf log` | the mining intake |
| `wiki_begin` | `wf wiki-generate begin` | 0 tokens (deterministic outline) |
| `wiki_next` | `wf wiki-generate next` | 0 tokens (next page job) |
| `wiki_submit_page` | `wf wiki-generate submit` | 0 tokens (validates + persists) |
| `wiki_finish` / `wiki_status` / `wiki_inspect_page_claims` | `wf wiki-generate …` | 0 tokens |

Mutations beyond `log` used to stay CLI-gated; the wiki-generation tools are
the one deliberate extension — the writer/bookkeeper split (`#144`): the host

## Exit-code contracts

Hook/CI shell-outs key off these — the table is the contract (don't renumber
without reading how consumers parse, test_shim_parity-style, first):

| Verb / script | Code | Meaning |
|---|---|---|
| `wf capture` | 0 | nothing new |
| | 2 | drift captured (hooks may trigger ingest) |
| | 3 | unknown project slug (+ connected list, closest-match hint) |
| | (1) | other errors (repo path missing) |
| `wf capture --git` (capture-git) | 0 | nothing new |
| | 2 | drift captured |
| | 3 | unknown project slug (+ connected list) |
| `wf capture issues` | 0 | nothing new |
| | 2 | drift captured |
| | 3 | unknown project slug (+ connected list) |
| `wf freshness` | 0 | clean (no drift) |
| | 1 | drift found + recorded (gate-worthy) |
| | 2 | hard failure (no fabric, unknown slug) |
| `wf gate` | 0 | nothing pending |
| | 1 | actionable items want a human |
| `wf models ensure --check` | 0/1 | model cached / needs download (script-friendly, no prompt) |
| `wf review --verify-sources` | 0 | source lifecycle driven (refresh/stamp/expire counts reported) |
| `wf review --contradiction-sweep` | 0 | no demotion |
| | 1 | a demotion landed (gate-worthy) |
agent writes prose, the MCP tool validates citations and reconciles claim
deltas deterministically (the bookkeeper makes no model calls). Claude Code: `claude mcp add wf-mcp wf-mcp`; Claude Desktop/Cursor: stdio-server config pointing at `wf-mcp`.

Environment: `WIKI_FABRIC_REPO` overrides the source repo URL.

---

## Scripts Reference

Scripts live in four subdirectories of `scripts/` — `cmd/` (entrypoints), `eval/`,
`harness/`, and shared `lib/`. Each runs standalone (`<name>.py --help`) — but the `wf` verbs are the user surface: `wf eval {behavior|stability|golden|real|pr}`, `wf graphify {all|import|enrich|diff|status}` wrap the eval/bridge scripts.

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
| `log-experience.py` | Capture experience event (`wf log`) | 0 |
| `mine-promotions.py` | Cluster experience events → dossiers (`wf mine promotions`) | 0 |
| `promote.py` | Manage pattern promotion dossiers (`wf promote`) | 0 |
| `propose-domains.py` | Discover + propose new domains (pending-review dossiers) | 0 |
| `promote-domains.py` | Human-gated merge of a proposed domain into the ontology | 0 |
| `gate.py` | Aggregate pending HITL decisions + notify adapters (`wf gate`) | +`--write-manifest`/notify |
| `rebuild-index.py` | Rebuild `registry/catalog.json` from files (`wf rebuild-index`) | 0 |
| `relocate-concepts.py` | Domain-bound concepts → `domains/<domain>/concepts/` (S1 migration; deterministic, idempotent) | 0 |
| `build-entity-index.py` | AST entity index from source repos | 0 |
| `bootstrap-project.py` | Connect a new project to the fabric (`wf bootstrap`) | 0 |
| `ensure-local-model.py` | Check/download `llm.local_model` (`wf models ensure`) | 0 |
| `review.py` | Staleness scan + re-verify loop (`wf review`) | 0 |
| `export-wiki.py` | Human-layer wiki renderer (topics, projects, staleness, deep dives) | 0–1 per topic |
| `wiki_generate.py` | Wiki-generation bookkeeper — durable queue, claim deltas, citation validation (`wf wiki-generate`) | 0 |
| `verify-effects.py` | Judged effect verification at ingest (`wf verify-effects`) | n judgment calls |
| `publish-wiki.py` | Static-site publisher (Quartz v4, `wf publish`) | 0 |
| `utility.py` | Receipt↔outcome join → usage counts (`wf utility`) | 0 |
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
| `fabric_config.py` | fabric.yaml loading, stage routing, actor conventions, local model, canonical repo keys (#158) |
| `layout.py` | Corpus layout single truth: `SEGMENTS` + accessors + the claim-prefix join contract; `seg()` raises on undeclared names (re-spelling is the drift class) |
| `ontology.py` | Ontology vocabulary single truth: `## Domains`/`## Aliases`/`## Shared tag set` → `canonicalize()` (alias-fold; unknown binds nothing), `all_spellings()` |
| `extract_backends.py` | Claim-extraction layer: prompt building, 4 LLM backends, JSON repair |
| `local_llm.py` | On-device generation (GGUF/MLX), serialized model cache |
| `wf_common.py` | Shared helpers: `parse_frontmatter`, `norm`, `slugify`, `project_slug` (THE canonical underscore→kebab fold), hashing |
| `eval_core.py` | Eval scoring primitives: `concept_match`, `jaccard`, `fuzzy_coverage` |
| `judgment.py` | Judgment tier backends (Jev cloud / Laya-MLX / upstream laya / generic), typed questions, graceful degradation |
| `embed_index.py` | Hash-gated offline embedding index (`registry/embed-index.json`) + query-side embedding |
| `tombstones.py` | Rejected-proposal buffer (SkillOpt S3): tombstones + cluster matching for the miner |
| `deepdives.py` | Graphify-rendered project deep dives (architecture/components/tour, 0 tokens) |
| `obsidian_bridge.py` | Two-way vault bridge: harvest/push/export manifest |

Shell scripts remain at `scripts/` root only where shell is the right tool — `wiki-fabric.sh` (the curl-piped installer + dev dispatch), `demo.sh`, and `smoke-test.sh`. The change-set merge (`wf apply-changeset`) and vault scaffold are python now — cross-platform, testable in pytest.

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
