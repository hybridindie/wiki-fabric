---
type: doc
title: "CI — what the pipelines prove"
description: "The five harness workflows, their gates, and the runner-shape contracts each encodes"
created: 2026-10-03
updated: 2026-10-03
---

# CI — what the pipelines prove

Wiki Fabric runs two distinct CI planes. The **harness CI** (this repo,
`.github/workflows/`) proves the TOOL on every push. The **corpus CI**
(scaffolded into each fabric/corpus by `wf sync init`/`sync setup`) proves the
KNOWLEDGE on a cadence. They share verbs but not scope — a green harness CI
says nothing about your corpus's freshness, and vice versa.

## The harness workflows

| Workflow | Trigger | What it owns |
|---|---|---|
| `ci.yml` | push main, PR | the full gate battery (below) |
| `publish.yml` | tag `v*` | prep-package → wheel-smoke → PyPI |
| `fabric-refresh.yml` | push (opt-in) | the harness fabric self-captures its own doc drift (`WIKI_FABRIC_REFRESH=1` repo variable) |
| `wiki-publish.yml` | push (opt-in) | regenerate + publish the generated wiki (daily on the corpus CI when scaffolded) |
| `deploy-docs.yml` | push main | build the docs site → GitHub Pages |

## ci.yml gates (every matrix entry: 3.11 / 3.12 / 3.13)

All gates are **0-token** — deterministic code, no model in the loop.

| Gate | What it proves |
|---|---|
| Unit tests (`pytest tests/ -q`) | script logic: parsing, routing, discovery, merge, exit contracts, layout/identity guards |
| Smoke test (`scripts/smoke-test.sh`) | the CLI works end-to-end in a throwaway fabric (18 checks: install shape, lint, ingest anti-loop, capture-git, query, mining, context + receipts, evals) |
| Behavior eval (`wf eval behavior`) | the context manifest actually delivers the right knowledge (banned approaches named, correct alternatives present) — the P4 proof |
| Stability eval (`wf eval stability --skip-llm`) | deterministic operations are byte-deterministic (20 context runs identical; catalog identical across rebuilds) |
| Fabric lint (seeded corpus) | the 0-error lint gate passes on a canonical empty fabric |
| OKF v0.2 floor (`wf lint --okf`, 3.12 only) | the bundle conforms to its own published contract |
| OKF cross-check (`okflint validate`, 3.12 only) | the EXTERNAL validator agrees — self-conformance never grades its own homework |
| Wheel smoke (`scripts/pkg/wheel-smoke.sh`, 3.12 only) | the packaged wheel installs into a clean venv and works against a fresh fabric (the `_harness` staging shape — catches packaging drift before a tag publishes broken data) |

## The runner-shape contracts (the why behind each step)

Each step encodes a discovered failure mode; they're contracts, not preferences:

- **Seeded corpora everywhere.** On a bare runner nothing fabric-shaped
  exists — `CORPUS_ROOT` falls back to `site-packages/../vault/corpus`
  (nonexistent). Lint targets that don't exist fail loudly (the missing-target
  guard, 2026-09-30 audit) — so both lint steps seed a skeleton via
  `uv run wf install --dir $SEED` first. Step envs don't share variables, so
  each step seeds its OWN skeleton (`SEED` is per-step).
- **`fetch-depth: 30`.** The capture-git smoke reads this repo's own commit
  history as its fixture; a depth-1 checkout would silently have nothing to
  filter.
- **The smoke fabric copies `fabric.yaml` when it exists — and creates it
  when it doesn't** (gitignored in CI). The fixture project
  (`smoke-project`) registers itself as a connected repo, because
  `capture-git`'s unknown-slug guard (#167) refuses unconnected slugs and
  the harness's own `.wiki-overlay.md` makes `wiki-fabric` discovered even
  on an empty config — the "empty config = guard off" assumption doesn't
  hold.
- **okflint is the external validator.** `okf-base.yaml` declares the
  per-type floor; `okflint validate --manifest` re-proves it from outside
  the codebase (the OKF conformance check can't certify itself).
- **Wheel smoke runs before publish, not after.** Package drift (missing
  staged assets, broken packaged-mode path resolution) is exactly the class
  a tag publishes forever.
- **Exit-code contracts are load-bearing**: capture `2 = drift, 3 = unknown
  slug`; freshness `0 = clean, 1 = drift recorded, 2 = hard failure`; gate
  `1 = actionable`. Hook/CI consumers key off these — never "improve" an
  exit code without reading the docs table in cli.md first.

## Publishing (publish.yml)

Tagging `v*` triggers: `prep-package.py` (stage the harness tree into
`src/wiki_fabric/_harness` — the wheel ships the corpus scripts as package
data) → the wheel smoke in skip-build mode → PyPI. The `HOOK_VERSION`
contract means packaged upgrades refresh installed hooks on `wf update`; see
[Upgrading wf](./upgrading).

## The corpus CI (the other plane)

The freshness scaffolds live in the CORPUS repo, not here:

- `freshness.yml` — daily `wf freshness` (opt-in per repo variable
  `WIKI_FABRIC_FRESHNESS=1`): capture-git `--since-state` + mechanical
  re-verify; commits refreshed evidence, never auto-pushes beyond the corpus
  remote.
- `wiki-publish.yml` — daily wiki generation; the
  `wiki-export-manifest.json` hash means an unchanged wiki commits nothing.

See [Teams: Sharing the Vault](./teams) and [How Sync Works](./how-sync) for
that plane's operation.

## Running the gates locally

```bash
python3 -m pytest tests/ -q -m "not live"   # unit (live-marked tests self-skip w/o cached models)
bash scripts/smoke-test.sh                  # isolated temp fabric by default
uv run wf eval behavior
uv run wf eval stability --skip-llm
uv run wf lint                              # corpus (dev layout: the sibling vault)
uv run wf lint --okf
bash scripts/pkg/wheel-smoke.sh             # build + clean-venv + fresh-fabric
```