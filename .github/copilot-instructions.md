## wiki-fabric (copilot)
## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace; the fabric lives at `~/.local/share/wiki-fabric/` by default — `WIKI_FABRIC_DIR` overrides).

Rules:
- Before starting a task, run `wf context --task "<task>"` (0 tokens) — it compiles a scoped manifest of relevant claims, patterns, and decisions (project > domain > global precedence) with exclusion reasons.
- For codebase/architecture questions, run `wf query "<question>"` (0 tokens) before grepping — evidence-backed answers with locators.
- Health before commit: `wf lint` (0-error gate). Status: `wf status`. Before mutating the repo, confirm it is clean: `git status --porcelain` should be empty — if it lists many uncommitted changes (a dirty restructure), surface that to the user rather than branching/committing over it. If `wf status` reports a STALE installed CLI, run the harness script directly (`bash scripts/wiki-fabric.sh ...`) or `wf update` before relying on `wf` subcommands.
- After solving a non-trivial problem, log it: `wf log --project <slug>` — experience events feed cross-project pattern mining.
- Never re-ingest a source whose sha256 is already recorded — the CLI skips it and tells you.
- Promotion is human-gated: `wf` proposes dossiers, only you promote.
- At session start, run `wf gate` — it aggregates every pending human decision (overdue/stale claims, promotion dossiers awaiting review, newly-proposed domains) into one report. Surface whichever are actionable to the user before proceeding. Resolve with: `wf review --auto-reverify`, `wf promote --promote <dossier>`, `python3 scripts/cmd/promote-domains.py --apply <dossier>`. If the git hook ran, it already persisted these to `registry/pending-gate.md` — read that instead of running commands (0 tokens).
- **Procedures on demand:** run `wf skill <name>` before these workflows — `ingest`, `promote`, `refresh`. `wf skill --list` summarizes them. Read the procedure before running the workflow the first time in a session.

CLI: `wf help` | When graphify is also installed: graphify owns code-symbol/call-graph questions; wiki-fabric owns evidence-backed knowledge (`wf query` — claims with doc locators). Prefer `wf context` for task scoping. They complement — neither replaces the other.
<!-- /wiki-fabric:copilot -->
