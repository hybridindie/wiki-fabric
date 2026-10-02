---
type: doc
title: "Upgrading wf — tool, skills, hooks, corpus"
description: "The full upgrade ritual: what each command refreshes, what it deliberately doesn't touch, and how to verify"
created: 2026-10-02
updated: 2026-10-02
---

# Upgrading wf

The tool and the fabric upgrade on separate rails: the **tool** (code: CLI,
scripts, schemas, skills) via uv/git; the **corpus** (your knowledge) only via
`wf sync`. An upgrade of one never touches the other — and the helpers (skill
copies, hooks, indexes) are refreshed *deliberately*, because each is a
point-in-time embed of harness content.

## The full ritual

```bash
# 1. Tool (packaged installs — the normal mode)
wf update                 # tells you this is uv-owned; prints the next line
uv tool upgrade wiki-fabric

# (dev checkouts instead:)
#   wf update             # git pull --rebase on the harness clone

# 2. Refresh helpers after the tool lands
wf update                 # idempotent post-upgrade pass: hook reinstall
                          # (--repos-from-config) + entity index + catalog rebuild
wf harness install --force --all
                          # refresh COPIED skills + instruction files into every
                          # detected harness (.claude/skills, .opencode/skill,
                          # AGENTS.md/CLAUDE.md/PI.md/copilot-instructions, ...)
wf hook status            # per repo: hook presence + version

# 3. Corpus drift the upgrade surfaced (plane-classified; never pushes)
wf sync commit-drift

# 4. Verify
wf status                 # CLI freshness, capture provenance, lint + gate summary
wf lint                   # 0-error gate; new gates may surface warnings on legacy content
wf gate                   # HITL queues + dark knowledge sources
```

## What each surface refreshes — and why it's your job

| Surface | Refresh command | Why manual |
|---|---|---|
| Tool itself | `uv tool upgrade wiki-fabric` (or `wf update` in dev) | uv owns the packaged install |
| Hook bodies | `wf hook install` (one repo) / `python3 scripts/harness/hooks.py reinstall --repos-from-config` (all repos) — fires when `HOOK_VERSION` advances | hook bodies are EMBedded into the shell hook at install time (the python runs detached from a baked base64 blob); a body change without a version bump would never reach installed repos |
| Skill copies | `wf harness install --force --all` | copies skip existing files without `--force` (idempotent install); refresh is opt-in |
| Entity index / catalog / threads | `wf update` does it; manual: `wf rebuild-index` | derived, regenerable |
| Your content | `wf sync pull` (incoming) / `wf sync push` (outgoing) | the corpus is git content, never shipped in the wheel |

**Version-gating rules** (maintained by the harness):
- `HOOK_VERSION` (scripts/harness/hooks.py) — **must bump on any hook-body
  change**; installed hooks compare the version line and skip matching
  versions. v5 = canonical `WF_SLUG` fold.
- `wf status` reports `CLI: STALE` when the installed `wf` differs from the
  harness clone — dev-mode reminder that `wf update` is due.
- Package smoke (`scripts/pkg/wheel-smoke.sh`) runs before each release:
  packaged imports (the `_harness` lib tree), fabric-content leakage, and the
  shared-lib import shape. It caught the `0.4.0` packaged-layout
  `ModuleNotFoundError` before the `0.4.1` cut.

## Schemas + migrations

Schemas move without migration scripts in places (alpha contract). Upgrade
paths that DID ship a migration tool this cycle: `scripts/cmd
/relocate-concepts.py` (physical domain homes), `wf repos migrate`
(routing → overlays), and the deterministic `review --verify-sources` run
(stamps `review_after` on pre-tier source records). After a major upgrade,
run `wf lint` once: the new gates (VOCABULARY / IDENTITY / LAYOUT-GUARD)
tell you exactly which legacy pages/configs need a decision — warnings
first, no silent behavior changes.

## Rollback

The tool: `uv tool install wiki-fabric==<prev>`. The corpus: git (revert the
commit, `wf sync push`). Hooks: `wf hook uninstall` + `wf hook install`
(older harness checkout). The corpus is never the casualty of a tool
rollback — content and code are separate git histories by design.