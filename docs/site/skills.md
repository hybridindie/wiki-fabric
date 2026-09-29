---
type: index
title: "Skills — on-demand procedures for agent harnesses"
description: "The wf skill loader: ingest and promote procedures, harness-specific folders vs universal loader, sync contract"
created: 2026-09-28
updated: "{{date:YYYY-MM-DD}}"
---

# Skills

Skills are **on-demand procedures** the agent reads before running a workflow
the first time in a session. They are markdown files — readable by any agent,
no special format. Two are shipped:

| Skill | Reads before | Covers |
|---|---|---|
| **`ingest`** | `wf ingest` | anti-loop sha256 check, CLI batch modes (`--changed`/`--pending`/`--reclaim`), claim extraction, judged effect verification (`wf verify-effects`, step 4b), change-set flow, recovery paths |
| **`promote`** | `wf mine promotions` + `wf promote` | deterministic clustering + judged refinement, dossiers, the 7-point review checklist, the compiler gate, tombstone/suppression buffer, `wf utility` write-back, SLOW-REGION revision proposals |

Run `wf skill --list` to list them; `wf skill <name>` to print the full
procedure. The procedure is the contract — it carries the anti-loop rules and
the step order that the CLI only partially enforces.

## How skills reach your harness

| Surface | Mechanism | Who gets it |
|---|---|---|
| Universal loader (`wf skill <name>`) | prints the procedure on demand | **every** harness — no skill support required |
| Native skill folders | `wf harness install` copies `system/skills/<name>/SKILL.md` into Claude Code (`.claude/skills/`) and opencode (`.opencode/skill/`) | only those two |

The content is identical everywhere — the same always-on block (in
`AGENTS.md`/`CLAUDE.md`) points at `wf skill <name>`, so harnesses without
native skill folders get the same procedures on demand.

## Sync contract

`.opencode/skill/` and `.claude/skills/` copies are **generated** —
`wf harness install` writes them from `system/skills/` (the canonical source).
If a skill file changes, re-run install (use `--force` to rewrite existing
copies) and commit both together. Committed copies exist so fresh installs
carry the current procedures; they are not hand-maintained.

## Which commands have no skill (and why)

Command-wrapper skills (`context`, `lint`, `query`, a vault refresh) were
deliberately removed: the CLI itself + its `--help` + the docs pages are the
contract for command-shaped work, and duplicating commands as prose created
drift (the deleted `refresh` skill advertised itself in three docs after its
code had been removed). Skills exist only where **judgment-based multi-step
procedures** benefit from an in-context read: the two promotion/ingest
workflows carry anti-loop rules and gate order that prose explains better
than flags do.

## Links

- [How It Works: The Compiler](./how-compiler) — the ingest story in depth
- [How It Works: The Compounding Loop](./how-compounding) — the promotion narrative

---

Next: [Configuration](./configuration)