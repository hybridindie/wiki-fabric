---
type: index
title: "instructions-and-rules: What We Learned"
review_after: 2027-03-20
---

# instructions-and-rules: What We Learned

## Current state

150 verified claim(s) from 150 analyzed sources.

## Key findings

- This repository is the genesis repository that generates AI assistant harnesses for .claude/, .github/, and .opencode/ from a single set of  [1]
- The repository also hosts the Epic Scoping Skills as its own installed harness." [2]
- Two systems share the same single-source/thin-wrapper pattern." [3]
- The genesis harness uses templates/_shared/ rendered into target projects by bootstrap.sh." [4]
- Epic Scoping Skills use .agents/ as the source rendered into thin wrappers in .claude/, .opencode/, and .github/." [5]
- The golden rule is to edit content in .agents/ for epic skills or templates/_shared/ for genesis." [6]
- Content must never be duplicated into a wrapper." [7]
- Shared rules referenced by multiple files live in a doctrine/ layer and should be referenced rather than restated." [8]
- The on-demand reference sections are not auto-loaded." [9]
- The post-bootstrap flow is bootstrap.sh (render) → /harness-eval (trim + suggest) → /customize-harness (domain tailoring)." [10]
- Each skill wrapper is a thin pointer, and the model reads the .agents/ body on-demand when the skill is invoked." [11]
- Doctrine files in .agents/doctrine/ are read on-demand when a skill references them." [12]
- The shared, tool-agnostic project context — covering what this repo is, how the genesis bootstrap works, the source structure, and the Epic  [13]
- Only Claude-Code-specific notes belong in this file." [14]
- Claude-specific harness assets (skills, hooks, scripts) live under `templates/claude-code/.claude/`." [15]

