---
type: index
title: "instructions-and-rules: What We Learned"
review_after: 2027-03-20
---

# Project Retrospective: instructions-and-rules

## What this project is

The `instructions-and-rules` repository is the genesis repository for AI assistant harnesses. It generates the `.claude/`, `.github/`, and `.opencode/` harness trees for target projects from a single set of shared constitutional articles. It also hosts the Epic Scoping Skills as its own installed harness, which makes the repo both a generator and a consumer of the pattern it generates.

Two systems live here and share one architecture. The genesis harness renders `templates/_shared/` into target projects via `bootstrap.sh`. The Epic Scoping Skills render `.agents/` into thin wrappers under `.claude/`, `.opencode/`, and `.github/`. Same single-source/thin-wrapper shape, applied twice.

## Constraints discovered

The single-source rule is not a preference, it is a hard constraint. Content must never be duplicated into a wrapper. The golden rule is to edit content in `.agents/` for epic skills, or `templates/_shared/` for genesis. Everything else is generated output. `templates/_shared/` is the source; `templates/claude-code/.claude/agents/`, `templates/claude-code/.claude/commands/`, `templates/github-copilot/.github/agents/`, and `templates/github-copilot/.github/prompts/` are generated and must not be edited directly.

A second constraint is that on-demand reference sections are not auto-loaded. Each skill wrapper is a thin pointer, and the model reads the `.agents/` body when the skill is invoked. Doctrine files in `.agents/doctrine/` are read only when a skill references them. Anything that must always be in context therefore has to live in `AGENTS.md`, not in a doctrine file.

Third: shared rules referenced by multiple files belong in a `doctrine/` layer and should be referenced rather than restated. Restating them recreates exactly the duplication the architecture exists to prevent.

## Patterns that emerged

The thin-wrapper pattern is the load-bearing idea. The body lives in one place; the wrapper points at it. Because the same shape appears in both systems, the golden rule can be stated once and applied to both.

Mirroring is declared, not inferred. `mirror-pairs.json` is the registry. Articles, agents, commands, and doctrine each get an entry. Doctrine entries set `source_file` and `render_dir` to `.claude/rules/doctrine`, and doctrine is referenced by articles and agents rather than mirrored to Copilot.

Versioning is per-file. Epic-scoping files under `.agents/` carry a `version: x.y.z` header. A patch bump covers typo, wording, or formatting fixes that do not change behavior. A minor bump covers content additions or behavioral changes — a new phase, a new rule, a new response state, or a doctrine reference added or removed. A major bump covers a workflow restructure that breaks existing handoffs or response-state contracts. Doctrine and skills version independently, so bumping a skill does not require bumping the doctrine it references, and vice versa.

## Decisions made

`AGENTS.md` holds the shared, tool-agnostic project context: what the repo is, how the genesis bootstrap works, the source structure, and the Epic Scoping Skills. Only Claude-Code-specific notes belong in the Claude-specific file. Claude-specific harness assets live under `templates/claude-code/.claude/` and are generated output where mirrored from `templates/_shared/`.

Drift is checked by a Claude Code hook invoked as `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh`, run from repo root with a bootstrapped harness in scope. The drift policy itself lives in `AGENTS.md`.

The post-bootstrap flow is fixed: `bootstrap.sh` renders, `/harness-eval` trims and suggests, `/customize-harness` does domain tailoring.

## Current state

The repository is stable and self-consistent. The graph covers the genesis harness, the Epic Scoping Skills, the doctrine layer, and the mirror registry. No related topic articles were linked at the time of writing, so no wikilinks are emitted here; the mechanics above are described inline instead.

---

_Generated from the evidence fabric on 2026-09-21. 150 current claim(s) from 150 analyzed sources._
