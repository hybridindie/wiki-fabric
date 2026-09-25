---
title: AGENTS.md
type: index
---

# Wiki Fabric — Agent Instructions

Wiki Fabric is a git-native knowledge base that compounds across projects. It is a
**conformant OKF v0.2 bundle**: markdown + YAML frontmatter, readable by any
agent without special tooling. Projects connect as namespaces; a global fabric
lives outside them (typically a sibling `wiki-fabric/` directory) and is the
persistent memory layer.

## Non-Negotiable Rules

1. **Every claim traces to evidence.** Each claim has `source_refs` with
   `source` + `locator` + `quote`. No evidence, no citation by a concept or
   pattern.
2. **Never re-ingest an unchanged source.** Check sha256 first
   (`wf ingest --changed <slug>` only ingests drift).
3. **Lint 0 errors before every commit.** `wf lint` (full profile) and
   `wf lint --okf` (OKF §11 floor) must both pass.
4. **Extraction is spending; retrieval is free.** Deterministic walkers
   (query, context, lint) cost 0 tokens. The LLM is only invoked for
   extraction and synthesis.
5. **Human gate before canonical writes.** Stage in `evidence/`, present the
   change-set manifest, ask before merging into canonical pages.
6. **Raw is immutable.** Never edit `evidence/raw/` in place; re-capture.
7. **Actor convention**: `agent/<owner>/<model>`, `human:<id>`,
   `process:<id>`. Lint rejects malformed actors.
8. **No secrets in content.** `fabric.yaml` is gitignored; never commit
   API keys, tokens, or credentials.

## Before you start

- **Check for a dirty tree first.** `git status --porcelain` must be empty (or
  intentionally staged) before branching/committing — a large uncommitted
  restructure is easy to clobber. Surface dirtiness to the user, don't `git
  clean`/`checkout` over it.
- **Confirm the CLI is current.** `wf status` reports `CLI: STALE` when the
  installed `wf` differs from the harness. Until synced (`wf update`), run the
  harness script directly: `bash scripts/wiki-fabric.sh <cmd> ...`.
- **Session start:** run `wf gate` — surfaces pending human decisions (claims,
  promotion dossiers, domain proposals). See the always-on block.

## Common Tasks

| Task | Command | LLM cost | Notes |
|------|---------|----------|-------|
| Compile task context | `wf context --task "<task>"` | **0** | Deterministic manifest: claims, patterns, decisions, skills |
| Answer a question | `wf query "<question>"` | **0** | Evidence-backed answer with locators |
| Capture upstream docs | `wf capture <slug>` | 0 | Copies from source repos → `evidence/raw/` |
| Ingest a source | `wf ingest <path> [--extract-claims]` | 1 call | Source record + summary + claims |
| Detect drift | `graphify-bridge.py --diff` | 0 | Only when graphify integration is enabled |
| Verify a computation | `references/attesters/*.py` | **0** | Deterministic receipt checks (no LLM) |
| Export portable bundle | `wf okf export` | **0** | Deterministic, okflint-conformant output |
| Route extraction/synthesis | `repos.<slug>.extract` / `.synthesize` / `.dossier` | — | Per-repo, per-stage: `"cloud"` (default) or `"local"` (on-device — MLX on Apple Silicon, GGUF elsewhere; model = `llm.local_model`) — privacy + quality tiering |
| Ensure local model | `wf models ensure [--yes]` | 0 | Check `llm.local_model` is cached; offer human-gated download (`--check` for scripts) |
| Import external bundle | `wf okf import <bundle>` | 0 or 1/doc | Trust recorded, not inherited |
| Log an experience | `wf log --project <slug>` | 0 | Feeds cross-project mining |
| Health check | `wf lint` | **0** | 0-error gate before commit |

## When NOT to use the LLM

- **Never call the LLM to search the fabric** — `query.py` and `context.py`
  retrieve via lexical + graph expansion (0 tokens).
- **Never call the LLM to cluster claims** — `mine-promotions.py` uses
  keyword-based Jaccard clustering; the LLM only writes the dossier.
- **Never call the LLM to check code symbols** — `build-entity-index.py`
  uses AST parsing.
- **Never call the LLM to check conformance** — `lint --okf` and
  `okflint` are deterministic.

## Anti-Loop Rules

1. **Ingest once** — matching sha256 = skip.
2. **Query before ingest** — check the catalog for an existing record.
3. **Lint before commit** — `wf lint` must return 0 errors.
4. **Ask before canonical edits** — stage in `evidence/` first, present
   the manifest + diff for review.
5. **One operation per commit** — don't batch ingest + promote + synthesize.
6. **Compiler model policy** — claim extraction, synthesis, and promotion
   mining run on `llm.compiler_model`. Model swaps require a recorded
   compiler eval (G4). `promote`/`mine` refuse without it.
7. **Import shared modules, don't re-implement** — `fabric_config.py`
   (config/routing/actors), `extract_backends.py` (claim extraction),
   `wf_common.py` (frontmatter/norm/slugify), `eval_core.py` (scoring
   primitives), `local_llm.py` (on-device generation). A local copy of one of
   these helpers is a bug waiting to drift; lint/tests guard the import shape.

## Where Things Live

Two trees: the **harness** (shipped here) and the **fabric** (gitignored user
content; fresh clones carry `.gitkeep`ed skeletons of the content dirs).

- **Content (fabric)**: `evidence/` (sources, summaries, claims), `patterns/`,
  `skills/`, `concepts/`, `domains/`, `projects/` — these paths are the OKF
  bundle layout and are load-bearing (scope model, lint, okflint)
- **Registry (fabric+harness)**: `registry/catalog.json` (auto-generated),
  `registry/log.md` (append-only timeline, OKF §9 shape)
- **Schemas**: `schemas/frontmatter.md` (per-type contracts),
  `schemas/ontology.md` (domain taxonomy)
- **Evaluations**: `evaluations/` (golden corpus, behavior fixtures)
- **Attested computations**: `global/computations/` (contracts)
- **Attesters + executor skills**: `references/attesters/`, `references/skills/`
- **Agent-facing assets**: `system/skills/` (ingest, promote — loaded via
  `wf skill <name>` on any harness), `system/always-on/`,
  `system/opencode/plugins/`
- **Templates + examples**: `templates/` (page scaffolds), `templates/examples/`
- **Project overlay**: `.wiki-overlay.md` in each connected project root
  (per-project config — routing, identity; discovered by the fabric)
- **Git hooks (required per project)**: `wf hook install` — post-commit
  captures doc drift (sha256-gated), post-merge re-syncs; the freshness
  guarantee depends on them
- **Shared modules**: `scripts/lib/fabric_config.py`, `scripts/lib/extract_backends.py`,
  `scripts/lib/local_llm.py`, `scripts/lib/wf_common.py`, `scripts/lib/eval_core.py`
  (see README Scripts Reference for the map)

## Tests

- `python3 -m pytest tests/ -q` — full suite.
- Tests marked `live` run real on-device models (GGUF/MLX); skip on slow
  machines with `pytest -m "not live"`. They self-skip when the model isn't
  cached or the platform lacks the backend.

See `README.md` for the full architecture, OKF conformance details, and
the promotion pipeline narrative.
