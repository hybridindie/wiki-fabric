---
title: "Obsidian — the two-way vault"
description: "Human wiki edits flow back as evidence; generated notes mirror into Obsidian"
type: index
---

# Obsidian (two-way vault)

The wiki has two audiences: agents (the corpus) and humans (the vault).
This integration makes the human side **two-way**: your hand-edits become
evidence, and generated notes mirror into Obsidian so you read and curate
in a real editor.

## Setup

```yaml
integrations:
  obsidian:
    enabled: true
    api_url: https://127.0.0.1:27124
    api_key_env: OBSIDIAN_REST_KEY
```

Requires the [Obsidian Local REST API](https://github.com/coddingtonbear/obsidian-local-rest-api)
community plugin (install once into the vault, enable HTTPS + key). The key
resolves: env var named by `api_key_env` → the plugin's own `data.json`
(gitignored) → not configured (`wf integrations` says which source).

## What changes when it's on

**1. Harvest-before-export (0 tokens).** `wf export wiki` compares the
current vault notes against the export manifest (path→hash recorded at the
previous export). Notes *you* changed land in
`evidence/raw/<project>/obsidian/` with capture provenance — **your edits
become evidence** instead of being silently overwritten by regeneration.
The manifest baseline is established on the first run.

**2. `--push` mirrors generated notes** through the Local REST API
(Obsidian must be running) — the wiki appears in your vault as readable,
linkable notes.

**3. `wf integrations` shows the state**: server reachability, key source,
manifest state, pending-harvest count.

## The contract

- **Off by default**; off = plain file-copy export exactly as the core docs
  describe.
- Harvest is *evidence capture* — your edits enter the fabric the same way
  any captured source does: via the change-set flow, human review, sha256
  anti-loop. The fabric never lets a regeneration clobber a human edit
  without recording it first.
- Generated notes are *views*; the canonical chain stays
  evidence → corpus → vault (see [Publish](../core-workflows#9-publish-the-wiki)).

## When it earns its keep

- You (or teammates) actually read/curate the wiki by hand in Obsidian —
  two-way harvest protects those edits.
- **Skip it** when the wiki is generated-read-only for you (agent-only
  consumption) — the REST API requirement would be dead weight.

Obsidian status is also wired into `wf status`'s integrations section and
`wf integrations` — reachability, key source, and pending harvest are one
look away.