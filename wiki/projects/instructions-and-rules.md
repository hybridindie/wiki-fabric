---
type: index
title: "instructions-and-rules: What We Learned"
review_after: 2027-03-20
---

# Instructions and Rules: A Retrospective

This repository is the genesis repository that generates AI assistant harnesses for `.claude/`, `.github/`, and `.opencode/` from a single set of shared constitutional articles [1]. It also hosts the Epic Scoping Skills as its own installed harness [2]. Those are two systems, but they share one architecture: the same single-source/thin-wrapper pattern [3]. The point of the project is that a rule should be written once and rendered everywhere, so that three platform harnesses cannot silently diverge from each other or from the intent behind them.

## What was built

The genesis harness keeps its source in `templates/_shared/`, which `bootstrap.sh` renders into target projects [4]. The Epic Scoping Skills keep their source in `.agents/`, which renders into thin wrappers in `.claude/`, `.opencode/`, and `.github/` [5]. The golden rule follows directly: edit content in `.agents/` for epic skills, or in `templates/_shared/` for genesis [6], and never duplicate content into a wrapper [7].

Shared rules that multiple files depend on live in a `doctrine/` layer and are referenced rather than restated [8]. Wrappers stay thin: each skill wrapper is a pointer, and the model reads the `.agents/` body on demand when the skill is invoked [11]. Doctrine files in `.agents/doctrine/` are read on demand when a skill references them [12].

Project context is split by audience. The shared, tool-agnostic description — what the repo is, how the genesis bootstrap works, the source structure, the Epic Scoping Skills — lives in `AGENTS.md` [13]. Only Claude-Code-specific notes belong in the Claude file [14]. Claude-specific harness assets (skills, hooks, scripts) live under `templates/claude-code/.claude/` [15], and those assets are generated output wherever they are mirrored from `templates/_shared/` [16].

The post-bootstrap flow is `bootstrap.sh` (render) → `/harness-eval` (trim and suggest) → `/customize-harness` (domain tailoring) [10]. Drift is policed by a Claude Code hook invoked as `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh` [18], run from the repo root with a bootstrapped harness in scope [19][24]; the policy itself lives in `AGENTS.md` [17].

Extension is deliberately mechanical. A new article means a `.md` file in `templates/_shared/articles/`, an entry in `mirror-pairs.json`, and a bootstrap run to test [20]. A new agent means a `.md` file in `templates/_shared/agents/` plus an `agent_entries` entry [21]. A new command means a `.md` file in `templates/_shared/commands/` plus a `command_entries` entry [22]. Shared doctrine needs a `doctrine_entries` entry with `source_file` and `render_dir` set to `.claude/rules/doctrine`, and is referenced by articles and agents rather than mirrored to Copilot [23].

## Constraints discovered

The on-demand reference sections are not auto-loaded [9]. That is the load-bearing limit behind the thin-wrapper design: content that is not in the wrapper is not in context unless something asks for it, so the wrapper has to point precisely.

Generated output is off-limits for direct edits. The platform-specific files under `templates/claude-code/.claude/agents/`, `templates/claude-code/.claude/commands/`, `templates/github-copilot/.github/agents/`, and `templates/github-copilot/.github/prompts/` are generated and must not be edited directly [30]. Doctrine is not mirrored to Copilot at all; it is referenced [23]. The drift check only means something when run from the repo root with a bootstrapped harness in scope [19][24]. And adding any primitive is inherently a multi-step change — file, registry entry, bootstrap run [20][21][22].

## Patterns that emerged

The dominant pattern is single source with thin wrappers, applied twice [3][4][5] — see [[single-source-thin-wrapper]] and [[harness-bootstrap]]. The second is reference-don't-restate, which is what the doctrine layer exists to enforce [8] — see [[doctrine-layer]]. The third is on-demand loading as a context-budget mechanism rather than an accident [9][11][12] — see [[on-demand-loading]]. The fourth is the registry as the thing that makes drift detectable: `mirror-pairs.json` is what the drift hook checks against [20][21][22][23] — see [[mirror-pairs-registry]] and [[drift-detection]]. Versioning is the fifth: epic-scoping files under `.agents/` carry a `version: x.y.z` field in their header comment [25], with patch for typo/wording/formatting fixes that do not change behavior [26], minor for content additions or behavioral changes such as a new phase, rule, response state, or doctrine reference added or removed [27], and major for workflow restructures that break existing handoffs or response-state contracts [28]. Each file versions independently, with `doctrine/` and `skills/` versioned separately so bumping a skill does not force a bump of the doctrine it references, or vice versa [29] — see [[primitive-versioning]].

These contributed to the promoted patterns [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]].

## Decisions made

The genesis repo was chosen as the origin for all three platform harnesses rather than letting each platform own its own rules [1]. The Epic Scoping Skills were hosted in the same repository as its own installed harness rather than split out [2]. The golden rule — edit the source, never the wrapper [6][7] — was made explicit because the failure mode is silent. A doctrine layer was introduced instead of restating shared rules per file [8]. `AGENTS.md` was designated the home for tool-agnostic context, with the Claude file restricted to Claude-specific notes [13][14]. Drift policy was placed in `AGENTS.md` and enforced by a hook rather than left to review discipline [17][18]. Doctrine was chosen to be referenced by articles and agents rather than mirrored to Copilot [23]. Version bumps were given explicit semantics so that a change's blast radius is legible from the header alone [26][27][28][29].

## Current state

The architecture is settled: two systems, one pattern, one registry, one drift check. What remains open is inherent to the design rather than unfinished. On-demand reference sections still are not auto-loaded [9], so correctness depends on wrappers pointing at the right source. The drift check still requires a bootstrapped harness in scope and a repo-root working directory [19][24]. Adding any primitive still requires touching `mirror-pairs.json` alongside the source file [20][21][22][23]. Doctrine still is not mirrored to Copilot [23]. The evidence assembled here does not carry a claims count or a graph-status snapshot, so no such numbers are asserted; the durable state is the set of rules above and the registry that keeps them honest.

---

_Generated from the evidence fabric on 2026-09-21. 150 current claim(s) from 150 analyzed sources._
