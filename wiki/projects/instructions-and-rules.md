---
type: index
title: "instructions-and-rules: What We Learned"
review_after: 2027-03-20
---

# instructions-and-rules — Project Retrospective

`instructions-and-rules` is the genesis repository that generates AI assistant harnesses for `.claude/`, `.github/`, and `.opencode/` from a single set of shared constitutional articles [1]. It is not a consumer of harnesses; it is the thing that produces them. It also hosts the Epic Scoping Skills as its own installed harness [2], which means the repository is simultaneously a generator and a live example of what it generates. That dual role is why it matters: the same single-source/thin-wrapper pattern governs both systems [3], so any drift in the pattern shows up twice.

## What was built

Two rendering pipelines share one architecture.

The genesis harness keeps its source in `templates/_shared/`, which `bootstrap.sh` renders into target projects [4]. The Epic Scoping Skills keep their source in `.agents/`, which renders into thin wrappers in `.claude/`, `.opencode/`, and `.github/` [5]. The golden rule for both is the same: edit content in `.agents/` for epic skills or `templates/_shared/` for genesis [6], and never duplicate content into a wrapper [7].

Around that core sit several supporting mechanisms:

- A `doctrine/` layer for shared rules referenced by multiple files, which are referenced rather than restated [8].
- On-demand reference sections that are deliberately not auto-loaded [9].
- A post-bootstrap flow: `bootstrap.sh` (render) → `/harness-eval` (trim + suggest) → `/customize-harness` (domain tailoring) [10].
- Thin skill wrappers that act as pointers, with the model reading the `.agents/` body only when the skill is invoked [11]. Doctrine files in `.agents/doctrine/` are read on demand when a skill references them [12].
- `AGENTS.md` as the home for shared, tool-agnostic project context — what the repo is, how the genesis bootstrap works, the source structure, and the Epic Scoping Skills [13]. Only Claude-Code-specific notes belong in the Claude file [14].
- Claude-specific harness assets (skills, hooks, scripts) under `templates/claude-code/.claude/` [15], which are generated output wherever they are mirrored from `templates/_shared/` [16].
- A drift policy documented in `AGENTS.md` [17], enforced by a Claude Code hook invoked as `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh` [18].
- Extension recipes for each primitive type: articles [20], agents [21], commands [22], and shared doctrine [23].

## Constraints discovered

The hard limits are mostly about where content is allowed to live.

Wrappers are output. `templates/_shared/` is the single source, and the platform-specific files under `templates/claude-code/.claude/agents/`, `templates/claude-code/.claude/commands/`, `templates/github-copilot/.github/agents/`, and `templates/github-copilot/.github/prompts/` are generated output that must not be edited directly [30]. The same applies to mirrored Claude assets [16].

On-demand sections are not auto-loaded [9]. That is a real constraint on authoring: if a rule is not referenced from a file the model actually reads, it will not be seen. This is why doctrine is referenced by articles and agents rather than restated [8], and why doctrine is not mirrored to Copilot at all [23].

The drift check has an execution precondition: it must be run from the repo root with a bootstrapped harness in scope [19][24]. It is not a check that works from an arbitrary working directory.

Versioning is scoped rather than global. Epic-scoping files under `.agents/` carry a `version: x.y.z` field in their header comment [25]. A patch bump covers typo, wording, or formatting fixes that do not change behavior [26]. A minor bump covers content additions or behavioral changes — a new phase, new rule, new response state, or a doctrine reference added or removed [27]. A major bump covers a workflow restructure that breaks existing handoffs or response-state contracts [28]. Each file versions independently, with `doctrine/` and `skills/` versioned separately so bumping a skill does not require bumping the doctrine it references, and vice versa [29].

## Patterns that emerged

The load-bearing pattern is single source plus thin wrapper, applied identically to two systems [3][4][5]. Everything else follows from it: reference over restate [8], on-demand loading instead of eager loading [11][12], and a registry file (`mirror-pairs.json`) that records what mirrors where [20][21][22][23].

The registry is the coordination point. Adding an article means adding a `.md` file to `templates/_shared/articles/`, adding an entry in `mirror-pairs.json`, and running bootstrap to test [20]. Adding an agent means a file in `templates/_shared/agents/` plus an `agent_entries` entry [21]. Adding a command means a file in `templates/_shared/commands/` plus a `command_entries` entry [22]. Shared doctrine requires a `doctrine_entries` entry with `source_file` and `render_dir` set to `.claude/rules/doctrine` [23].

This project's evidence contributed to four promoted patterns: [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]].

## Decisions made

Three decisions shape the repository.

First, `AGENTS.md` is the tool-agnostic home for project context, and Claude-specific notes are kept out of it [13][14]. This keeps the shared description usable by any assistant harness rather than tied to one vendor.

Second, doctrine is referenced, not mirrored to Copilot [23]. The alternative — duplicating doctrine into every platform — would have violated the no-duplication rule [7] and created a second place to drift.

Third, the post-bootstrap flow is staged rather than one-shot: render, then evaluate and trim, then customize for the domain [10]. Rendering and tailoring are separate concerns with separate commands.

## Current state

The evidence base for this retrospective does not record claim counts or graph metrics, so no numbers are asserted here. What is documented is the operational state: two rendering pipelines, a registry-driven mirror map, a drift hook with a documented invocation, and per-file versioning with explicit bump semantics.

What remains open is the ongoing cost of the golden rule. Every new primitive requires a source file plus a registry entry plus a bootstrap test run [20][21][22][23], and every drift check requires a bootstrapped harness in scope [19][24]. The architecture is stable; the discipline it demands is continuous.

---

_Generated from the evidence fabric on 2026-09-21. 150 current claim(s) from 150 analyzed sources._
