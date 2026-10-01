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

```bash
$ wf skill --list
Available skills (wf skill <name> prints the full procedure):

  ingest     Ingest a raw source into the evidence fabric via `wf ingest` —
             creates source record, faithful summary, extracts claims, opens
             a change-set for review...
  promote    Run the promotion pipeline via `wf mine promotions` + `wf promote`
             — cluster experience-events deterministically, generate dossiers...

$ wf skill ingest      # prints the procedure (agents: read BEFORE the first
                       # ingest this session — it is the step contract)
```

**The harness loop in one pass** — what an agent session looks like when the
fabric is installed (the always-on block arrives at session start; the agent
runs these in order):

```text
SESSION START (from the always-on block, 0 tokens)
  → wf context --task "<task>" --write-receipt   # scoped manifest + receipt id
  → [optional] wf query "<question>"             # evidence-backed answers

DO THE WORK (code changes land via the normal commit)

END OF SESSION
  → wf log --project <slug> --receipt <receipt-id>   # outcome against delivery
  → wf gate                                          # what needs a human? surface it
```

The git hook fires on commit (drift capture, 0 tokens for unchanged files);
graphify rebuilds on its own plugin (branch switches), not the agent's
attention. Everything the agent prints is either manifest-shaped or a
gate report — you never reverse-engineer state from prose.

**Why procedures in files, not prompts in code:** the skill file versions
with the harness (a changed workflow = a changed file = the next session
reads the new contract), and it's readable by any agent harness with zero
integration — that's the "universal loader" row above.

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