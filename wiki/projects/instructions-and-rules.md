---
type: index
title: "instructions-and-rules: What We Learned"
review_after: 2027-03-20
---

# instructions-and-rules: What We Learned

## Current state

137 verified claim(s) from 137 analyzed sources.

## Key findings

- The repository generates AI assistant harnesses for `.claude/`, `.github/`, and `.opencode/` from a single set of shared constitutional arti [1]
- The repository hosts the Epic Scoping Skills as its own installed harness." [2]
- Two systems in the repository share the same single-source/thin-wrapper pattern." [3]
- The Genesis harness renders `templates/_shared/` into target projects via `bootstrap.sh` and contains constitutional articles, agents, comma [4]
- The Epic Scoping Skills system uses `.agents/` as its source directory with thin wrappers in `.claude/`, `.opencode/`, and `.github/`, conta [5]
- The golden rule prohibits duplicating content into a wrapper; content must be edited in `.agents/` or `templates/_shared/`, and only frontma [6]
- Shared rules referenced by multiple files live in a `doctrine/` layer and must be referenced rather than restated." [7]
- On-demand reference sections in the repository are not auto-loaded and must be read explicitly when needed." [8]
- The post-bootstrap flow proceeds as `bootstrap.sh` (render) → `/harness-eval` (trim + suggest) → `/customize-harness` (domain tailoring)." [9]
- Each skill wrapper is a thin pointer; the model reads the `.agents/` body on-demand only when the skill is invoked." [10]
- Doctrine files located at `.agents/doctrine/` are read on-demand when a skill references them." [11]
- The shared, tool-agnostic project context (repo description, genesis bootstrap, source structure, Epic Scoping Skills) is defined in AGENTS. [12]
- Only Claude-Code-specific notes belong in CLAUDE.md; all other shared context is delegated to AGENTS.md." [13]
- Claude-specific harness assets (skills, hooks, scripts) are stored under the path templates/claude-code/.claude/." [14]
- The Claude-specific harness assets are generated output mirrored from templates/_shared/, not authored independently." [15]

