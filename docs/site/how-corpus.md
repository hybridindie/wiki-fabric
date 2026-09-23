---
type: index
title: "How It Works: The Corpus & Connected Projects"
description: "How the fabric relates to your code repos — namespaces, overlays, discovery, and who owns what"
created: 2026-09-20
updated: 2026-09-20
---

# How It Works: The Corpus & Connected Projects

This page tells the story of the *geometry*: where knowledge lives, how your
code repos relate to it, and what happens on each machine when a team shares
one fabric.

## Three kinds of tree

The system is deliberately split into three locations, each with one job:

| Location | What lives there | How it updates |
|----------|-----------------|----------------|
| **The harness** — this repo's clone | code: scripts, schemas, skills | `wf update` (git pull of the public repo) |
| **The fabric** — `~/.local/share/wiki-fabric/` | your content: `evidence/`, `projects/`, `patterns/`, plus `fabric.yaml` | you (and hooks) write; `wf sync` shares |
| **Your code repos** | the projects being documented: source code + a tiny `.wiki-overlay.md` | normal development; the overlay versions with the code |

The harness never holds your knowledge. Your projects never hold the fabric.
The only thing a project repo carries is its **overlay** — and that's on
purpose: routing decisions about *this project's* sensitivity (`extract:
local`) belong next to this project's code, where they version with it and
ride along to every clone.

## The overlay: a project's whole relationship with the fabric

`wf bootstrap /path/to/project` writes one file into the project:

```yaml
# .wiki-overlay.md (frontmatter, in the project repo)
project: my-project
namespace: my-project        # the project's folder inside the fabric
domains: [agent-systems]
source_repos:                # what to capture
  - path: .
    raw_path: evidence/raw/my-project
    globs: ["*.md", "docs/**/*.md"]
routing:                     # where each stage's LLM work runs
  extract: local
  synthesize: local
```

Everything the fabric needs to know about the project is in that file — and
because it's just a file in the repo, a teammate's clone carries the same
configuration. The fabric's side of the relationship is generated: a
namespace folder `projects/my-project/` holding the README, experience
events, and decisions, plus an `overlay.yml` view for the vault.

## Discovery: the fabric finds projects itself

The fabric scans its **sibling directories** for `.wiki-overlay.md` files.
Bootstrap a project anywhere beside the fabric and it's part of the fabric on
the next `wf` command — no fabric.yaml edit, no shared config to update. The
slug comes from the overlay's `namespace:`, the path from the directory.
Explicit `repos:` entries in fabric.yaml still exist for exceptions (a repo
that isn't a sibling, or routing that must override the overlay) and always
win over discovered values.

The vault is the utility's standalone **output**, not a mirror: generated wiki
content lands there (`wf export wiki`), and it never copies or symlinks the
corpus in. A machine can have multiple vaults by pointing `vault.path` at
different targets, and the vault's freshness is auditable with `wf vault --check`.

## The corpus: the fabric's shareable half

`wf sync` treats the fabric as two halves. **Content** — claims, sources,
summaries, patterns, projects, registry — syncs to a git remote you own (a
private GitHub repo). **Harness** — scripts, schemas — never syncs; it
updates from the public repo. When a teammate bootstraps a new project into
their fabric, `wf sync push` publishes the namespace with a README describing
it; teammates' `wf sync pull` announces it and delivers it. Nothing to
configure on their side. When two machines changed the same file, the pull
aborts and writes a conflict record — both versions side by side, lint fails
until a human resolves it.

Next: [How It Works: Staying in Sync (Hooks & CI)](./how-sync)
