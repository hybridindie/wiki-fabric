---
type: index
title: "Team Sync — share the corpus"
description: "One fabric per machine, one corpus shared via git"
created: 2026-09-19
updated: 2026-09-28
---

# Team Sync (Command Reference)

> The team *story* — roles, the two-way join gate, conflict policy, CI on the
> corpus — is in [Teams: Sharing the Vault](./teams). This page is the command
> reference.

Team sync is the deployment story: one fabric per machine, one corpus shared
via git. Configure the corpus remote in [Configuration](./configuration) or at
install time.

One fabric per machine, **one corpus shared via git**. Throughout the docs:
**the fabric** is your local knowledge base; **the corpus** is the shared
subset of it that syncs to your team remote. `wf sync` pushes/pulls that
content (claims, sources, patterns, experience events, registry) to a git
remote — a private GitHub repo works well. The harness (scripts, schemas)
stays per-machine and updates via `wf update` from the public repo; content
and code have different lifecycles and remotes.

## First-time setup: `wf sync setup`

`wf sync setup` is the initial-setup step that makes the fabric a team
system. It uses the **gh CLI** (checked at run time — install gh and run
`gh auth login` if missing) to:

1. Create the corpus repo — `<owner>/wiki-fabric-corpus`, **private** by
   default (`--public` to flip). Prompts before creating unless `-y`.
2. Publish your fabric's corpus as the source of truth (`sync init` + push).
3. Print the teammate one-liner — teammates inherit the team's knowledge
   from their first install command.

If gh isn't available, setup prints the manual path instead
(`gh repo create` by hand, or `wf sync init <url>` pointing at an existing
repo). The corpus holds your project knowledge — the privacy default is
deliberate. Note: `wf sync setup`/`init` scaffold `AGENTS.md` at the
fabric/vault root if it lacks one (a fresh fabric needs the marker to sync).

## Day-to-day, on any machine

```bash
wf sync status        # ahead/behind + uncommitted corpus changes + conflicts
wf sync push -m "ingested upstream docs"   # commit + push corpus changes
wf sync pull          # fetch + merge; conflicts → review queue
```

**Branches, in one table:** knowledge lives on the remote's **`corpus`
branch only**. Your local fabric works on its own `main`; push does
`git push corpus HEAD:refs/heads/corpus` (rejected — never force-pushed —
when the remote moved; pull first), pull does
`git merge corpus/corpus --allow-unrelated-histories` into your main. Team
mode adds one **per-push branch** `sync/<machine>-<stamp>` whose PR squash
merges back to `corpus`. Full model + rationale:
[Teams › The branch model](/teams#the-branch-model).

**Team mode (PR-gated distribution):** `fabric.yaml → sync: {mode: team,
evidence_prs: auto}`. Every push opens one PR (branch `sync/<machine>-<stamp>`,
body carries the change-set receipts + files classified by plane).
Evidence-plane-only PRs auto-merge when CI is green; anything touching atoms
(claims, patterns, decisions, projects) waits for human review — never
auto-merged. Per-invocation: `--pr` opts in even solo; `--no-pr` opts out even
team mode.

**A teammate joins** — one command (install pulls the corpus when the remote
already carries one; `--vault` pins where the vault shell lives):

```bash
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- \
  --corpus git@github.com:your-org/wiki-fabric-corpus.git \
  --vault ~/knowledge/vault
```

Manual join (existing install): wire the remote + pull:

```bash
git remote add corpus git@github.com:your-org/wiki-fabric-corpus.git
wf sync pull
```

> Config layering (who gets routing vs keys vs knowledge): see
> [Teams › Config layering](./teams#config-layering-who-gets-what).
> Short version: routing travels with the project overlay, keys/owner stay
> machine-local, knowledge syncs with the corpus.

## How bootstrap meets the corpus

When you `wf bootstrap` a project into a fabric with a corpus remote, the
bootstrap writes a small `projects/<slug>/README.md` (title, owner, date,
upstream sources) into the namespace — that README syncs to the corpus, so
teammates see *what* the new project is the moment it lands. Bootstrap prints
whether the project is local-only or corpus-wired, and `wf sync status` lists
new namespaces waiting on the remote ("New projects on the corpus (pull to
receive)"); `wf sync pull` announces each namespace it delivers, with owner.
Teammates discover new projects by pulling — nothing to configure on their
side.

## Install-time join: two-way gate

`install --corpus` decides the join direction **automatically, by content**:
the remote is probed with `git ls-remote`; a `corpus` branch that exists
while the local corpus has no knowledge content ⇒ **teammate join** (fetch +
checkout of the corpus branch — your local `main` becomes the corpus
content); otherwise ⇒ **lead machine** (`sync init` publishes the local
corpus). The full flow — both join paths, what checkout actually does, what
joining does NOT do — is on [Teams › Joining](/teams#joining-as-a-teammate).

The freshness loop then applies on both sides: hooks capture drift per commit,
`wf sync push/pull` move it to/from the team remote — and `wf freshness`
(the scheduled cycle) closes the dormant-machine hole.

## Conflict policy: review queue, never silent overwrite

When two machines changed the same file, `wf sync pull` aborts the merge and
writes a conflict record to `registry/conflicts/<date>/` containing *both*
versions (ours vs theirs) side by side. The fabric stays clean; you decide.
Unresolved conflicts make `wf lint` fail (SYNC-CONFLICT errors) and block
`wf sync push`, so a disagreement can't sneak into the shared truth.

Resolving:

```bash
wf sync resolve <conflict-file>                # interactive: diff + pick
wf sync resolve <conflict-file> --strategy ours|theirs|union   # scripted
```

The interactive flow shows a unified diff of both versions and prompts —
`ours` (keep this machine's), `theirs` (take the teammate's), `union` (keep
both, marked for later dedup), `skip` (leave pending — the gate stays up).
The conflict record is consumed on resolve; the resolution is committed so
the next push carries it.

## Why a separate remote from this public repo

This repo is the public harness; your corpus is your private knowledge.
Keeping them on different remotes means `wf update` (harness) never touches
team content, and `wf sync` never publishes your corpus to a public URL.
