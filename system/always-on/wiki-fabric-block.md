# wiki-fabric always-on block — written into CLAUDE.md / AGENTS.md by `wf claude install`

## wiki-fabric

This project is connected to a knowledge fabric (`.wiki-overlay.md` declares the namespace; the fabric lives outside this repo, typically a sibling `wiki-fabric/` directory).

Rules:
- Before starting a task, run `wf context --task "<task>"` (0 tokens) — it compiles a scoped manifest of relevant claims, patterns, decisions, and skills (project > domain > global precedence) with exclusion reasons.
- For codebase/architecture questions, run `wf query "<question>"` (0 tokens) before grepping — it retrieves evidence-backed answers with locators.
- After solving a non-trivial problem, log it: `wf log --project <slug>` — experience events are what the fabric mines for cross-project patterns.
- Doc drift auto-captures on commit when the wf hook is installed (`wf hook status`); captured drift is ingested without LLM unless `WIKI_HOOK_EXTRACT=1`.
- Never re-ingest a source whose sha256 is already recorded (`wf ingest --changed <slug>` only ingests drift).
- Promotion is human-gated: `wf` proposes dossiers, only you promote.

CLI: `wf help` | status: `wf status` | health: `wf lint`
- When graphify is also installed: graphify owns code-symbol/call-graph questions (graphify query), wiki-fabric owns evidence-backed knowledge (wf query — claims with doc locators). Prefer wf context for task scoping; use graphify for symbol graphs. They complement — neither replaces the other.
