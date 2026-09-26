---
type: index
title: "Teams: sharing the vault"
description: "Multi-machine and multi-person operation — corpus ownership, joining, syncing, and governance gates"
created: 2026-09-26
updated: 2026-09-26
---

# Teams: Sharing the Vault

A fabric starts as one person's knowledge on one machine. The moment it
becomes useful, the next question is: **how does a teammate get it, and how
does the team keep it true?** This page is the team story end to end —
setup, joining, day-to-day sync, and how disagreements are resolved. The
command reference lives in [Team Sync](./sync); this page explains the
model and the flows.

## The model: one corpus, many machines

The fabric separates two trees, and the team story lives in the split:

- **The harness** is the tooling — code, tests, schemas. It ships from this
  repo and is identical on every machine.
- **The corpus** is the shared knowledge — claims, patterns, decisions,
  events, receipts. It lives in the **vault** (a git repo of its own) and is
  the *source of truth* for the team.

The vault is git-native by design: the same primitives that govern code —
branches, diffs, review, CI — govern knowledge. Teammates don't copy files
or reconcile notes by hand; they pull a branch.

## Roles: lead machine and teammates

| Role | Who | What happens |
|---|---|---|
| **Lead machine** | Whoever runs the first project (or owns the existing corpus) | Creates/adopts the corpus repo and publishes the corpus as the source of truth |
| **Teammates** | Everyone else | One command inherits the team's knowledge at install time |

The direction is decided automatically by `install --corpus` — a two-way
gate, not a mode you configure:

| Condition | Path |
|---|---|
| Remote carries a corpus branch, local corpus has no knowledge content | **Teammate join** — the remote corpus is fetched and checked out; the fabric carries the team's knowledge from the first command |
| Remote has no corpus, or local content wins | **Lead machine** — the local corpus publishes as the source of truth |

## First-time setup (lead machine)

```bash
wf sync setup
```

One command, using the **gh CLI** (detected at run time — install gh and
`gh auth login` if missing):

1. Creates the corpus repo — `<owner>/wiki-fabric-corpus`, **private** by
   default (`--public` to flip). Prompts before creating unless `-y`.
2. Publishes your fabric's corpus as the source of truth (`sync init` +
   push).
3. Prints the teammate one-liner to send to your team.

If gh isn't available, setup prints the manual path (`gh repo create` by
hand, or `wf sync init <url>` pointing at an existing repo). The corpus
holds your project knowledge — the privacy default is deliberate.

## Joining (teammates)

One command — install pulls the corpus when the remote already carries one
(`--vault` pins where the vault shell lives on *their* machine):

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- \
  --corpus git@github.com:your-org/wiki-fabric-corpus.git \
  --vault ~/knowledge/vault
```

Manual join (existing install): wire the remote and pull.

```bash
git remote add corpus git@github.com:your-org/wiki-fabric-corpus.git
wf sync pull
```

**Where things live** is chosen per machine: `--dir` places the harness
clone, `--vault` places the Obsidian shell. The knowledge content follows
the fabric dir; the vault shell is the human-readable view.

## Day-to-day sync

```bash
wf sync status        # ahead/behind + uncommitted corpus changes + conflicts
wf sync push -m "ingested upstream docs"   # commit + push corpus changes
wf sync pull          # fetch + merge; conflicts → review queue
```

The freshness loop runs underneath on every machine: hooks capture doc and
code drift per commit, the graphify cycle keeps navigation fresh, and the
gate manifest accumulates pending decisions. Sync moves the *corpus*
between machines — the loop never stops being local.

## New projects propagate

When you `wf bootstrap` a project into a corpus-wired fabric, the bootstrap
writes `projects/<slug>/README.md` into the namespace — that README syncs
to the corpus, so teammates see *what* the new project is the moment it
lands. `wf sync status` lists namespaces waiting on the remote; `wf sync
pull` announces each one it delivers. Nothing to configure on their side.

## CI guards the shared truth

The corpus repo carries its own CI (scaffolded automatically by `sync
setup`/`init` — never hand-made): on every push,

- **Lint 0-error gate** + OKF v0.2 conformance floor run against the corpus
- **Catalog freshness** — a stale `catalog.json` fails with the fix command
- **Sync-conflict block** — unresolved disagreements fail the build, so they
  can't silently enter the shared truth

Both sides of the system are self-governing: the harness repo proves its
*code* on every PR; the corpus repo proves its *knowledge* on every push.

## Conflict policy: review queue, never silent overwrite

When two machines change the same file, `wf sync pull` aborts the merge and
writes a conflict record to `registry/conflicts/<date>/` containing *both*
versions (ours vs theirs) side by side. Unresolved conflicts make `wf lint`
fail (SYNC-CONFLICT errors) and block `wf sync push`. Resolve by picking
the correct version for the source page, delete the conflict file, then
push — a disagreement can't sneak into the shared truth.

## Privacy posture

- The corpus repo is **private by default** — it holds your project knowledge.
- Per-repo, per-stage model routing decides what touched a cloud model;
  the corpus itself records provenance either way (see
  [Model splits](./why#model-splits-different-models-for-different-cognitive-tasks)).
- Fully-local fabrics work entirely offline before and after sync — the
  corpus sync is for teams, not for the loop.
