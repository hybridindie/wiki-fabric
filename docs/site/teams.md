---
type: index
title: "Teams: sharing the vault"
description: "Multi-machine and multi-person operation — the standalone corpus repo, joining (both paths), sync modes, and governance gates"
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
2. Publishes your fabric's corpus as the source of truth: `sync init` makes
   the corpus a standalone git repo (`<fabric>/corpus/.git`), commits the
   content, and pushes to the remote's `main` — the remote's root becomes
   exactly the corpus content.
3. Scaffolds the helper surfaces: `AGENTS.md` sync marker, `registry/promotion-queue.md` (the human-maintained promotion checklist), and `questions/`.
4. Prints the teammate one-liner to send to your team.

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

What happens:

1. The harness installs to **`~/.wiki-fabric`** (the standard home — never
   littered into whatever directory you ran the command from) and the `wf`
   shim to `~/.local/bin`.
2. The fabric dir is created (`$WIKI_FABRIC_DIR` or `~/.local/share/wiki-fabric`)
   with its config + skeleton.
3. The remote is probed (`git ls-remote … refs/heads/main`): a corpus exists
   ⇒ **`corpus/` is cloned from the team repo** — the clone *is* the corpus
   (its origin pre-wired for your first `sync push`). No corpus on the
   remote ⇒ you're the lead; your (empty) corpus publishes.

The one-liner below is the POSIX-only fallback (macOS/Linux — the bash
installer needs a POSIX shell and doesn't run on Windows):

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- \
  --corpus git@github.com:your-org/wiki-fabric-corpus.git \
  --vault ~/knowledge/vault
```

### Join B — existing install (the two-step)

You already have a harness + a fabric (used it solo first):

```bash
wf sync migrate git@github.com:your-org/wiki-fabric-corpus.git   # legacy layout → standalone corpus repo
# — or, if the corpus is already standalone:
git -C <fabric>/corpus remote add corpus git@github.com:your-org/wiki-fabric-corpus.git
wf sync pull
```

`wf sync pull` merges `origin/main` into your local corpus main; anything
that conflicts lands in the review queue (below) rather than blocking the
join.

### What "joining" does NOT do

- It does **not** touch your harness (that's `wf update`'s job, separate).
- It does **not** copy your machine config — keys, model overrides, and
  `owner` stay machine-local (see [config layering](#config-layering-who-gets-what)).
- It does **not** fork your git history into a submodule or a separate
  checkout — the corpus *is* your fabric's content, now wired to a remote.

## The branch model: there isn't one

**The corpus is a standalone git repo** — `corpus/` inside your fabric
directory *is* the team repo, cloned or initialized in place. The remote's
root is the corpus content exactly; sync is plain git against it:

```text
   fabric/
     ├─ fabric.yaml      machine-local (gitignored, own shell history)
     └─ corpus/          ← THE team repo (a .git of its own)
          ├─ registry/
          ├─ patterns/
          └─ projects/   ← remote root == exactly this
```

| Operation | What runs | Notes |
|---|---|---|
| `wf sync push` (solo) | commit + `git push origin main` — rejected when the remote moved (pull first, never force) | local main ⇆ remote main |
| `wf sync pull` | `git fetch` + `git merge origin/main` into local main | conflicts → review queue |
| `wf sync commit-drift [--dry-run]` | stage + commit hook-accumulated drift with a plane-classified summary (never pushes) | clean worktree |
| `wf sync push` (team) | one **per-push branch** `sync/<machine>-<stamp>` + a PR against `main` | the PR is the receipt; evidence-only auto-merges on green CI |
| teammate join | `wf install --corpus URL` **clones the corpus** — content arrives as the clone; origin pre-wired | no checkout gymnastics |

**Why no branches beyond main:** the corpus is *content* — there's no dev
vs release version of a fact, so a second long-lived branch would be a
second queue with no meaning. Governance lives in the gates (review queue,
CI lint, conflict block), not in branch topology. The old model (your local
main mirrored onto a remote `corpus` branch — the team's tip under an
alias) was retired 2026-10-01; `wf sync migrate` moves an existing fabric
to the standalone layout in one command.

## Day-to-day sync

```bash
wf sync status        # ahead/behind vs the remote (plus uncommitted changes + conflicts)
wf sync commit-drift  # stage + commit hook-accumulated drift (plane-classified; never pushes)
wf sync push -m "ingested upstream docs"   # commit + push (rejected if remote moved — pull first)
wf sync pull          # fetch + merge; conflicts → review queue
wf sync resolve <c> --strategy ours|theirs|union   # interactive diff resolver
wf sync migrate [url] # one-time: legacy layout → standalone corpus repo
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
| **Knowledge** (claims, patterns, decisions, relationships) | the **corpus** — a standalone git repo, synchronized as ordinary content | yes — via `wf sync` |

The merge rule: explicit `fabric.yaml` keys win over the overlay, so a
teammate can differ locally without touching shared config. The model decision
is made once in the owner's `fabric.yaml`, written into the overlay by
`wf bootstrap`, and travels with the project — nothing re-asks on another
machine. Keys never leave the machine.