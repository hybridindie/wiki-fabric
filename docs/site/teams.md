---
type: index
title: "Teams: sharing the vault"
description: "Multi-machine and multi-person operation — the corpus repo, joining (both paths), branch model, sync modes, and governance gates"
created: 2026-09-26
updated: 2026-10-01
---

# Teams: Sharing the Vault

A fabric starts as one person's knowledge on one machine. The moment it
becomes useful, the next question is: **how does a teammate get it, and how
does the team keep it true?** This page is the team story end to end. The
command reference lives in [Team Sync](/sync); this page explains the model,
the branches, and the flows.

## The model: one corpus, many machines

The fabric separates two trees, and the team story lives in the split:

- **The harness** is the tooling — code, tests, schemas. It ships from this
  repo and is identical on every machine. Updates via `wf update` (or
  `uv tool upgrade`).
- **The corpus** is the shared knowledge — claims, patterns, decisions,
  events, receipts. It's a **git repo of its own** (the vault), and it is
  the *source of truth* for the team.

Everything about team distribution is git primitives under the hood: the
corpus remote is just a git remote named `corpus`; knowledge moves on
**one branch, `corpus`**; conflicts are real git merge conflicts with a
review UI on top (`wf sync resolve`).

## Roles

| Role | Who | What happens |
|---|---|---|
| **Lead machine** | Whoever runs the first project (or owns the existing corpus) | Creates/adopts the corpus repo and publishes the corpus as the source of truth |
| **Teammates** | Everyone else | One command inherits the team's knowledge |

## First-time setup (lead)

```bash
wf sync setup
```

One command, using the **gh CLI** (detected at run time — install gh and
`gh auth login` if missing):

1. Creates the corpus repo — `<owner>/wiki-fabric-corpus`, **private** by
   default (`--public` to flip). Prompts before creating unless `--yes`.
2. Publishes your fabric's corpus as the source of truth: your local HEAD
   is pushed to the remote's **`corpus` branch** (`git push corpus HEAD:refs/heads/corpus`).
3. Prints the teammate one-liner to send to your team.

If gh isn't available, `setup` prints the manual path (`gh repo create` by
hand, or `wf sync init <url>` pointing at an existing repo — then push).
The corpus holds your project knowledge; the privacy default is deliberate.

## Joining as a teammate

There are two joins, and which one applies depends on what you already
have. The confusion usually starts here, so both are spelled out:

### Join A — fresh machine (you have nothing yet)

```bash
uv tool install wiki-fabric --with mcp     # the tool (all platforms, incl. Windows)
wf install --corpus git@github.com:your-org/wiki-fabric-corpus.git \
    --vault ~/knowledge/vault              # the fabric + the team join
```

`uv tool install` is the cross-platform path (the CLI is pure-python —
Windows included). The one-liner below is the POSIX fallback (macOS/Linux;
the bash installer needs a POSIX shell and doesn't run on Windows):

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- \
  --corpus git@github.com:your-org/wiki-fabric-corpus.git \
  --vault ~/knowledge/vault
```

What this actually does, step by step (this is *why* the result is correct
on both leader and teammate machines):

1. Installs the harness to **`~/.wiki-fabric`** (the standard home — never littered into whatever directory you ran the command from) and the `wf` shim to `~/.local/bin`.
2. Creates the fabric dir (`$WIKI_FABRIC_DIR` or `~/.local/share/wiki-fabric`)
   and its config + skeleton.
3. **Reads the remote**: `git ls-remote <corpus-url> refs/heads/corpus`.
   - **A corpus branch exists** → *teammate path*: the remote is added, the
     corpus branch is fetched, and your fabric checks it out
     (`git checkout -B main corpus/corpus`) — **your local `main` becomes the
     corpus content**. Your fabric starts already carrying the team's
     knowledge; the corpus remote now tracks it for push/pull.
   - **No corpus branch** → *lead path*: your (empty) local corpus is
     published as the initial source of truth.

The direction is decided **automatically, by content**, not by a mode flag:
remote-has-knowledge beats local-has-nothing. A *lead* re-running install
is protected too — if your local corpus has real content and the remote
doesn't (yet), the local side wins and publishes.

### Join B — existing install (the two-step)

You already have a harness and a fabric (maybe you used the fabric solo
first). Wiring the team corpus is two commands:

```bash
git remote add corpus git@github.com:your-org/wiki-fabric-corpus.git
wf sync pull                      # first pull checks out the corpus branch content
```

`wf sync pull` fetches `corpus/corpus` and **merges it into your local
main** (`--allow-unrelated-histories` — two fabrics that grew independently
can still join safely). Anything that conflicts lands in the review queue
(below) rather than blocking the join.

### What "joining" does NOT do

- It does **not** touch your harness (that's `wf update`'s job, separate).
- It does **not** copy your machine config — keys, model overrides, and
  `owner` stay machine-local (see [config layering](#config-layering-who-gets-what)).
- It does **not** fork your git history into a submodule or a separate
  checkout — the corpus *is* your fabric's content, now wired to a remote.

## The branch model

Knowledge moves on **one named branch: `corpus`** — not on `main`, not on
feature branches. Your local fabric keeps working on its own `main`;
sync is branch-to-branch:

```text
   local fabric (main) ──push──▶ remote (corpus)
        ▲                            │
        └──────merge at pull─────────┘
```

| Operation | What runs | What lands where |
|---|---|---|
| `wf sync push` (solo mode) | commits local corpus changes, then `git push corpus HEAD:refs/heads/corpus` | replaces the **corpus tip** when your history contains the remote's; a rejected push (remote ahead) exits with the pull instruction — never force-pushed |
| `wf sync pull` | `git fetch corpus corpus`, then `git merge corpus/corpus --allow-unrelated-histories` | remote work merges **into your main**; per-file conflicts → `registry/conflicts/<date>/` + review queue |
| `wf sync push` (team mode) | same commit, then pushes a **per-push branch** `sync/<machine>-<yyyymmdd-hhmm>` and opens **one PR** against the corpus branch | the PR is the change-set receipt; evidence-only PRs auto-merge on green CI, anything touching atoms waits for human review |

**Why a per-push branch in team mode:** the PR is the audit artifact — a
reviewable diff, an actor trail, a CI verdict — and squash-merging back to
`corpus` keeps the shared branch linear. Solo mode keeps direct pushes
(sticky default); `--pr` / `--no-pr` override per invocation; `sync.mode:
team` in fabric.yaml flips the default.

**Why one shared branch at all:** the corpus is *content*, not a codebase —
there's no "development" and "release" version of a fact. The governance
gates (review queue, CI lint, conflict block) are what keep a push honest;
a second long-lived branch would just be a second queue with no meaning.

## Day-to-day sync

```bash
wf sync status        # ahead/behind + uncommitted corpus changes + conflicts
wf sync push -m "ingested upstream docs"   # commit + push corpus changes
wf sync pull          # fetch + merge; conflicts → review queue
wf sync resolve <c> --strategy ours|theirs|union   # interactive diff resolver
```

The freshness loop runs underneath on every machine: hooks capture doc and
code drift per commit, `wf freshness` on the corpus CI catches *upstream*
drift while machines sleep, and the gate manifest accumulates pending
decisions. Sync moves the *corpus* between machines — the loop never stops
being local.

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
- **Upstream freshness** (`freshness.yml`, opt-in: repo variable
  `WIKI_FABRIC_FRESHNESS=1`) — daily capture-git + mechanical re-verify

Both sides of the system are self-governing: the harness repo proves its
*code* on every PR; the corpus repo proves its *knowledge* on every push.

## Conflict policy: review queue, never silent overwrite

When two machines change the same file, `wf sync pull` aborts the merge and
writes a conflict record to `registry/conflicts/<date>/` containing *both*
versions (ours vs theirs) side by side. Unresolved conflicts make `wf lint`
fail (SYNC-CONFLICT errors) and block `wf sync push`. Resolve by picking
the correct version for the source page (`wf sync resolve <c> --strategy
ours|theirs|union`), delete the conflict file, then push — a disagreement
can't sneak into the shared truth.

## Privacy posture

- The corpus repo is **private by default** — it holds your project knowledge.
- Per-repo, per-stage model routing decides what touched a cloud model;
  the corpus itself records provenance either way (see
  [Model splits](/why#model-splits-different-models-for-different-cognitive-tasks)).
- Fully-local fabrics work entirely offline before and after sync — the
  corpus sync is for teams, not for the loop.

---

## Config layering: who gets what

| Layer | Lives in | Teammates get it? |
|---|---|---|
| **Identity & keys** (`owner`, API keys) | `secrets.env` (machine-local, gitignored) + shell env / `fabric.yaml` | never — every teammate has their own |
| **API key references** (`api_key_env:` names, no literals) | `fabric.yaml` — shareable | structure yes, secrets no |
| **Shared project routing** (decided stage routing for a repo) | the project's `.wiki-overlay.md` — **versioned with the project repo** | yes — inherited on clone |
| **Machine routing overrides** (privacy tiering that differs per teammate) | `fabric.yaml` `repos.<slug>.*` — machine-local overrides | no — personal only |
| **Knowledge** (claims, patterns, decisions, relationships) | the **corpus** — synchronized on the `corpus` branch | yes — via `wf sync` |

The merge rule: explicit `fabric.yaml` keys win over the overlay, so a
teammate can differ locally without touching shared config. The model decision
is made once in the owner's `fabric.yaml`, written into the overlay by
`wf bootstrap`, and travels with the project — nothing re-asks on another
machine. Keys never leave the machine.