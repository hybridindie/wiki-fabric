---
type: claim
id: claim-wiki-fabric-readme-md-008
statement: "Wiki Fabric includes features like judgment gate, newest-wins contradiction sweep, and tracker capture."
description: "Wiki Fabric includes features like judgment gate, newest-wins contradiction sweep, and tracker capture."
resource: "[[src-wiki-fabric-readme-md]]"
generated: { by: "agent/eval/qwen2.5-coder:7b", at: "2026-10-08T07:24:56Z" }
verified:
  - by: "process:locator-verification"
    at: "2026-10-08T07:24:56Z"
status: supported
confidence: high
project: "wiki-fabric"
evidence_strength: primary
source_refs:
  - source: "[[src-wiki-fabric-readme-md]]"
    locator: "L72-L74"
    quote: "**Works today:** capture → ingest → query → promote loop (claims carry provenance edges from chats/PRs); **activity-bounded git capture** (window shrinks to fit an active repo's budget — shrink-not-truncate; `--until` backfills; threads paginate with flagged truncation + state provenance; `tuning.git_history` + per-repo knobs); **budgeted ingest** + the mechanical **sha256-drift ⇒ contested** staleness trigger; **source staleness tiers + `--verify-sources` lifecycle** (upstream-gone ⇒ `expired` tombstone); deterministic context compiler + delivery receipts; locator re-verification; chat-mined gated pattern candidates; **physical domain homes** (`domains/<domain>/{concepts,questions,syntheses}`, ontology alias-mapped); **ontology as living vocabulary** (shared parser, VOCABULARY/IDENTITY lint gates, canonical repo slugs — one project, one slug, everywhere incl. the corpus trees); layout single-truth + guard (commit-time in the hook); **commit-drift ritual** (plane-classified hook-drift commits); promotion-queue + questions scaffolds; contribution-freshness gate signal; judgment tier (refinement + effect verification + opt-in re-rank); team sync (PR mode, corpus pull); hooks incl. merge-time capture; Obsidian bridge; MCP server; **CLI surface**: shell completions (bash/zsh/fish), `wf help <cmd>` → argparse, `--version`, typo suggestions, one-liners for all verbs, `--json` machine surfaces (`status`/`ingest`/`review`/`projects`), **exit-code discipline** (drift 2 / unknown-slug 3 — loud for hooks/CI), `wf projects` inventory; OKF v0.2 export/import; wiki generation + publish + utility write-back. **judgment gate (G-J)** (only a calibrated judge proposes; judge swaps refuse until re-calibrated); **newest-wins contradiction sweep** (contradiction-based staleness — same-source `contradicts` + newer capture mechanically demotes the older claim, restore-able); **tracker capture** (`wf capture issues` — the WHY channel, `kind: issue-record` thread nodes); **chat-mining cadence + judged near-miss refinement** (corpus CI weekly; judged merge of paraphrase takeaways into inbox candidates); **gate push coverage** (escalation aging + the daily digest); **judged auto-apply tier** (`promote-patterns --auto` — deterministic preconditions + one calibrated judgment per candidate, confident applies (stamped + reversible via `--unapply`), near-band escalates, off until opted in); **SECRETS lint** (credential-shaped strings in corpus content block the commit gate — the Memory Defense lesson, deterministic, matches masked in output); **contradiction synthesis** (concept definitions render the evolution — prior state folded in, disputed → open_questions); **delta-mode wiki refresh** (unchanged generation-inputs keep the previous file byte-identical at 0 tokens; changed inputs patch incrementally with mechanically-spliced untouched sections; `--full`/`--check`); **temporal retrieval axis** (`wf query --type changed` orders the answer earliest→latest by capture date). CI proves all of it ([what the pipelines show](docs/site/ci.md))."
    supports: true
last_verified: 2026-10-08
relations: []
---

# claim-wiki-fabric-readme-md-008

Wiki Fabric includes features like judgment gate, newest-wins contradiction sweep, and tracker capture.
