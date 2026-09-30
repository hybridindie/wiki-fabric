---
type: index
title: "How It Works: Staying in Sync (Hooks & CI)"
description: "How doc drift becomes claims automatically, and what CI proves on every push"
created: 2026-09-20
updated: 2026-09-28
---

# How It Works: Staying in Sync

Knowledge that requires manual maintenance rots. This page covers the two
machines that keep the fabric current without anyone remembering to:
**hooks** (per-project, event-driven) and **CI** (per-push, assertion-driven).

## The hook loop: drift → capture → compile

A project's docs change through normal development — a commit renames a
feature, updates a README, deletes a doc that had claims pointing at it. The
opt-in post-commit hook turns that drift into fabric updates without a
session:

```mermaid
flowchart LR
    C["git commit<br/>(docs changed)"] --> H{"post-commit hook"}
    H -->|"rebase/merge/worktree"| SKIP["skip"]
    H -->|"fabric-owned paths only"| SKIP2["skip — no loop"]
    H -->|"md drift"| CAP["capture --quiet<br/>(sha256 drift gate)"]
    CAP -->|"exit 2 = drift"| ING["ingest --changed slug"]
    CAP -->|"exit 0"| DONE["no drift — done"]
    ING --> LOG["hook log (detached)"]
```

Four design choices make this safe to leave on:

1. **Drift-gated**: capture recomputes sha256 for every tracked source file;
   unchanged files cost zero tokens. Only exit code 2 ("drift") proceeds.
2. **Self-skipping**: commits touching only fabric-owned paths (`evidence/`,
   `registry/`) never re-trigger — the hook can't create a capture/ingest
   loop feeding itself.
3. **Detached**: the hook's work runs in a background process; `git commit`
   returns immediately. Output lands in `~/.cache/wiki-fabric-hook.log`.
4. **LLM-optional**: with plain `wf hook install`, drift is captured and
   *recorded* without claims (0 tokens) — the agent ingests interactively on
   its next session, when you're watching. With
   `wf hook install --extract-claims`, drift also compiles immediately
   (1 call per changed file).

`WIKI_SKIP_HOOK=1 git commit ...` skips once; `wf hook status` shows state.

The hook cycle also runs (`graphify-bridge.py
--import → --enrich → --diff`) after code commits when the integration is
active, and (4) writes the pending-decision manifest
(`registry/pending-gate.md` via `gate.py --write-manifest`) so any harness's
session-start can read pending human decisions without running commands.
The harness fabric itself also self-captures in CI — an opt-in workflow
(`fabric-refresh.yml`, gated on the `WIKI_FABRIC_REFRESH=1` repo variable)
runs the same sha256-gated capture + lint on every push to main.

## Other capture channels

The hook handles doc drift; two more channels feed the fabric, both
sha256-anti-looped:

- **Git history** (`wf capture <slug> --git`, and the post-merge hook which
  runs it automatically — merge is when the *why* exists): PR narratives,
  issue threads, and commits land as `kind: pr-record` evidence. PRs/issues
  capture the why for shipped work. Setup and scenarios live in
  [Core Workflows §2](./core-workflows#2-git-history-capture-prs-issues-commits-raw-evidence).
- **Agent chats** (`wf capture chat <slug>`): claude/opencode/codex/gemini
  session stores, with thread frontmatter (session id, files touched) feeding
  the thread index. Chats capture the why for everything else: debugging
  dead ends, rejected approaches, environment quirks.

Then `wf mine chats <slug> [--llm]` distills transcripts into **durable
takeaways** — patterns (e.g. "red-check every regression test by confirming it
fails against the pre-fix code"), anti-patterns, workflows, constraints —
with explicit transient filtering (CI states, PR counts, "as of today"
snapshots are excluded as low-value). Output lands in
`evidence/insights/<project>/` for human review before anything enters the
promotion pipeline.

## CI: the fabric checks its own homework

The harness repo's CI runs five deterministic gates on every push — each one
a claim about the system, each one verified:

| Gate | What it proves |
|------|----------------|
| **Unit tests** (220+) | script logic: parsing, routing, discovery, merge |
| **Smoke test** | the CLI works end-to-end in a throwaway fabric |
| **Behavior eval** | the context manifest actually delivers the right knowledge (banned approaches named, correct alternatives present) — the P4 proof, zero-LLM |
| **Stability eval** | deterministic operations are byte-deterministic (20 context runs identical; catalog identical across rebuilds) |
| **Fabric lint + OKF floor + okflint** | the bundle conforms to its own contracts *and* the external validator agrees |

Two properties make this meaningful: every gate is **0-token**
(deterministic code, no model in the loop), and the behavior eval is the
homepage's proof in CI form — "the manifest changed the agent's instructions"
is an assertion, not a sentence.

## The freshness contract, end to end

Putting the layers together — what guarantees a teammate's fabric reflects
reality:

1. **A commit changes docs** → the hook captures and compiles the drift
   (minutes, automatically). `wf bootstrap` installs this hook
   automatically (that's what makes it a **requirement**, not a chore) — layer 1 of the guarantee depends on it;
   without it, drift waits for a manual capture.
2. **A dependency updates its docs** → `wf capture` recomputes hashes;
   `SOURCE-DRIFT` lint errors name exactly which claims are affected
3. **A refactor renames code** → graphify's AST diff flags code-referencing
   claims as stale
4. **Knowledge ages** → `review_after` / `stale_after` gates drop it from
   manifests before it misleads
5. **Structure drifts** (new project, moved dir) → `wf vault --check` fails
   loudly; `wf vault` self-heals
6. **Upstream moves while every machine is dormant** → the scheduled
   freshness cycle (`wf freshness`, daily on the corpus CI when
   `WIKI_FABRIC_FRESHNESS=1`): capture-git pulls new upstream PRs/issues
   (sha256-gated) + mechanically re-verifies claims — refreshed evidence
   lands in the team corpus and reaches every machine on `sync pull`
   (see [the freshness cycle](#the-scheduled-upstream-freshness-cycle)).

None of these require remembering to run something. The hooks run on commits;
the lint runs in CI and on every command that could be affected; `wf status`
surfaces whatever needs attention.

## The scheduled upstream-freshness cycle

Hooks capture *local* commit drift on *active* machines. A team whose every
machine is dormant for a week can still carry silently stale claims — so a
cadence that depends on nobody's work habits can't be load-bearing. The
freshness cycle closes that hole:

- **`wf freshness [--dry-run] [projects...]`** (0 tokens): per connected
  project — `capture-git --since-state` (new upstream PRs/issues →
  evidence/raw/, sha256-gated) then `review --auto-reverify` (mechanical
  quote+hash re-verification). Exit 1 = drift captured; the human gate
  (`wf gate`) lists anything that needs a decision.
- **Scheduled on the corpus CI**: `wf sync init`/`sync setup` scaffold
  `.github/workflows/freshness.yml` (daily, opt-in per repo variable
  `WIKI_FABRIC_FRESHNESS=1`). The run commits refreshed evidence and pushes;
  teammates pick it up on the next `wf sync pull`.
- **Evidence-plane only**: the cycle never rewrites claims — stale/contested
  states are the representation; re-extraction stays opt-in per repo
  routing tier.
