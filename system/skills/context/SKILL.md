---
type: skill
name: context
description: Compile a deterministic task-context manifest via `wf context --task "<task>"` — 0 tokens. Scoped selection of claims, patterns, decisions, and skills (project > domain > global precedence) with exclusion reasons and trust tiers.
---

# Context Skill

Before starting any task, compile its context manifest.

## When to Use

- At session start, for the task at hand
- Before implementing anything non-trivial
- Before answering consequential questions (pair with `wf query`)

## Usage

```bash
wf context --task "<task description>" [--project <slug>] [--paths <code/path> ...] [--max N]
wf context --task "..." --format json   # machine-readable for CI
```

## Reading the Manifest

- **Selected** items are grouped by precedence tier (project > domain > global),
  each with a reason and a trust tier badge (`human-reviewed` >
  `machine-confirmed` > unverified).
- **Excluded** items list why (superseded, deprecated, stale, beyond --max,
  not a context artifact). Exclusions are as informative as inclusions.
- **Precedence**: when artifacts conflict, project > domain > global; cite the
  one you followed.

## Rules

- Run context BEFORE writing code. It is deterministic, free, and fast.
- Do not re-derive context by grepping when the manifest already scoped it.
- Trust tiers are advisory: human-reviewed > machine-confirmed > unverified.
