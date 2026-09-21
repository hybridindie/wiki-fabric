---
type: skill
name: wiki-fabric-always-on
description: "Always-on instructions block installed into agent harness instruction files by wf harness install"
---

## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace; the fabric lives at `~/.local/share/wiki-fabric/` by default — `WIKI_FABRIC_DIR` overrides).

Rules:
- Before starting a task, run `wf context --task "<task>"` (0 tokens) — it compiles a scoped manifest of relevant claims, patterns, and decisions (project > domain > global precedence) with exclusion reasons.
- For codebase/architecture questions, run `wf query "<question>"` (0 tokens) before grepping — evidence-backed answers with locators.
- Health before commit: `wf lint` (0-error gate). Status: `wf status`.
- After solving a non-trivial problem, log it: `wf log --project <slug>` — experience events feed cross-project pattern mining.
- Never re-ingest a source whose sha256 is already recorded — the CLI skips it and tells you.
- Promotion is human-gated: `wf` proposes dossiers, only you promote.
- **Procedures on demand:** run `wf skill <name>` before these workflows — `ingest` (compile a source into claims), `promote` (cross-project pattern mining), `refresh` (re-capture upstream). `wf skill --list` summarizes them. Read the procedure before running the workflow the first time in a session.

CLI: `wf help` | When graphify is also installed: graphify owns code-symbol/call-graph questions; wiki-fabric owns evidence-backed knowledge (`wf query` — claims with doc locators). Prefer `wf context` for task scoping. They complement — neither replaces the other.