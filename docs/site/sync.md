---
type: index
title: "Team Sync — share the corpus"
description: "One fabric per machine, one corpus shared via git"
created: 2026-09-19
updated: 2026-09-19
---

# Team Sync

Team sync is the deployment story: one fabric per machine, one corpus shared via git. Configure the corpus remote in [Configuration](./configuration) or at install time.

One fabric per machine, **one corpus shared via git**. Throughout the docs:
**the fabric** is your local knowledge base; **the corpus** is the shared
subset of it that syncs to your team remote. `wf sync` pushes/pulls that
content (claims, sources, patterns, experience events, registry) to a git
remote — a private GitHub repo works well. The harness (scripts, schemas)
stays per-machine and updates via `wf update` from the public repo; content
and code have different lifecycles and remotes.

```bash
# One-time: point your fabric at the shared corpus remote
# (or pass --corpus <git-url> to the installer and this is done for you)
wf sync init git@github.com:your-org/wiki-fabric-corpus.git

# Day-to-day, on any machine:
wf sync status        # ahead/behind + uncommitted corpus changes + conflicts
wf sync push -m "ingested upstream docs"   # commit + push corpus changes
wf sync pull          # fetch + merge; conflicts → review queue

# A teammate joins — one command (install pulls the corpus when the
# remote already carries one; --vault pins where the vault shell lives):
curl -fsSL https://raw.githubusercontent.com/hybridindie/wiki-fabric/main/scripts/wiki-fabric.sh | bash -s -- \
  --corpus git@github.com:your-org/wiki-fabric-corpus.git \
  --vault ~/knowledge/vault

# Manual join (existing install): wire the remote + pull
git remote add corpus git@github.com:your-org/wiki-fabric-corpus.git
wf sync pull
```

## How bootstrap meets the corpus

**Bootstrap meets the corpus:** when you `wf bootstrap` a project into a
fabric with a corpus remote, the bootstrap writes a small
`projects/<slug>/README.md` (title, owner, date, upstream sources) into the
namespace — that README syncs to the corpus, so teammates see *what* the new
project is the moment it lands. Bootstrap prints whether the project is
local-only or corpus-wired, and `wf sync status` lists new namespaces waiting
on the remote ("New projects on the corpus (pull to receive)"); `wf sync pull`
announces each namespace it delivers, with owner. Teammates discover
new projects by pulling — nothing to configure on their side.

## Install-time join: two-way gate

`install --corpus` decides the direction automatically:

| Condition | What happens |
|---|---|
| Remote carries a corpus branch, local corpus has no knowledge content (.md claims/ontology) | **Teammate join** — the remote corpus is fetched and checked out; the fabric carries the team's knowledge from the first command |
| Remote has no corpus (or local corpus has content) | **Lead machine** — `sync init` publishes the local corpus as the source of truth |

The freshness loop then applies on both sides: hooks capture drift per commit, `wf sync push/pull` move it to/from the team remote.

## Conflict policy: review queue, never silent overwrite

When two machines changed the same file, `wf sync pull` aborts the merge and
writes a conflict record to `registry/conflicts/<date>/` containing *both*
versions (ours vs theirs) side by side. The fabric stays clean; you decide. Unresolved conflicts
make `wf lint` fail (SYNC-CONFLICT errors) and block `wf sync push`, so a
disagreement can't sneak into the shared truth. Resolve by picking the correct
version for the source page, delete the conflict file, then push.

## Why a separate remote from this public repo

This repo is the public
harness; your corpus is your private knowledge. Keeping them on different
remotes means `wf update` (harness) never touches team content, and `wf sync`
never publishes your corpus to a public URL.

---

---

Next: [How It Works: Staying in Sync (Hooks & CI)](./how-sync)
