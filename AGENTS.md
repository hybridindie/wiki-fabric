---
title: AGENTS.md (schema)
type: index
---

# Global Wiki Fabric — Evidence-First Knowledge Base with Cross-Project Promotion

This is the **global wiki fabric** — a single, shared knowledge base that lives outside any project. All projects connect to this one fabric, reading and writing to their own namespace within it. The fabric is the persistent memory layer that compounds across all projects.

**Location:** `~/wiki-fabric` (or wherever you installed it). **Not inside any project.**

---

## Architecture: Global Fabric + Project Overlays

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GLOBAL WIKI FABRIC (~/.wiki-fabric)                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  evidence/raw/              # Immutable captures from upstream repos        │
│    ├── project-a/                                                           │
│    ├── project-b/                                                           │
│    └── ...                    # One directory per captured repo             │
│                                                                             │
│  evidence/                      # Compiled knowledge base                   │
│    ├── sources/                 # type: source — one record per raw capture │
│    ├── source-summaries/        # type: source-summary — faithful summaries │
│    ├── claims/                  # type: claim — atomic assertions + refs   │
│    ├── experiments/             # type: experiment — test contracts        │
│    ├── traces/change-sets/      # type: change-set — proposed edits        │
│    └── _inbox/                  # unprocessed captures awaiting ingest     │
│                                                                             │
│  projects/                   # PROJECT NAMESPACES (one per project)        │
│    ├── project-a/              # Project namespace                         │
│    │    ├── experience-events/ # type: experience-event                    │
│    │    └── decisions/         # type: decision (ADR-like)                 │
│    ├── project-b/              # Another project namespace                 │
│    │    ├── experience-events/                                                │
│    │    └── decisions/                                                        │
│    ├── project-c/              # Another project namespace                  │
│    │    ├── experience-events/                                                │
│    │    └── decisions/                                                        │
│    ├── my-new-project/         # New project adds its namespace here       │
│    │    ├── experience-events/                                                │
│    │    └── decisions/                                                        │
│    └── ...                     # Unlimited project namespaces              │
│                                                                             │
│  domains/                    # Cross-project domain knowledge              │
│    ├── agent-systems/          # Domain: agent systems                     │
│    │    ├── concepts/          # type: concept — stable explanations      │
│    │    ├── questions/         # type: question — open research           │
│    │    └── syntheses/         # type: synthesis — timed answers          │
│    ├── godot-systems/          # Domain: Godot engine systems             │
│    │    ├── concepts/                                                    │
│    │    ├── questions/                                                   │
│    │    └── syntheses/                                                   │
│    └── ...                     # Unlimited domains                       │
│                                                                             │
│  global/                     # Cross-project reusable assets             │
│    ├── patterns/               # type: pattern — maturity 0–3             │
│    ├── anti-patterns/          # type: anti-pattern — failure modes      │
│    ├── skills/                 # type: skill — reusable procedures       │
│    ├── playbooks/              # type: playbook — multi-step ops         │
│    ├── decision-rules/         # type: rule — enforceable invariants     │
│    ├── entities/               # type: entity — projects, orgs, models  │
│    ├── ontologies/             # type: ontology — domain taxonomies     │
│    └── templates/              # type: template — reusable shapes       │
│                                                                             │
│  registry/                   # Fabric metadata                            │
│    ├── catalog.json            # Machine registry (auto-generated)       │
│    ├── log.md                  # Append-only operation timeline (§9)     │
│    ├── catalog.json        # Promoted patterns index                │
│    ├── catalog.json           # Promoted rules index                   │
│    ├── catalog.json          # Promoted skills index                  │
│    ├── promotion-queue.md      # Promotion pipeline queue               │
│    ├── promotions/             # Promotion dossiers                     │
│    └── epics/                  # Epic/story planning pages               │
│                                                                             │
│  global/computations/        # Attested Computation concepts (§10)        │
│  references/                 # Executor skills + deterministic attesters  │
│                                                                             │
│  index.md                    # OKF bundle root (okf_version declaration)  │
│  okf-base.yaml               # okflint profile manifest (cross-check)     │
│                                                                             │
│  schemas/                    # Contracts & ontology                      │
│    ├── frontmatter.md          # Per-type frontmatter contracts         │
│    └── ontology.md             # Domains, tags, scope mapping           │
│                                                                             │
│  scripts/                    # Deterministic tooling                    │
│    ├── lint.py                 # 14 deterministic checks               │
│    └── ...                                                          │
│                                                                             │
│  evaluations/                # Compiler evaluation corpus               │
│    ├── fixtures/               # Test source fixtures                   │
│    ├── expected/               # Expected claim/concept/contradiction   │
│    ├── questions.yaml          # Golden questions with must_cite       │
│    └── rubric.md               # Metrics, protocol, pass thresholds   │
│                                                                             │
│  .opencode/skills/             # Opencode skills                        │
│    ├── ingest/                 # 10-step ingest protocol               │
│    ├── lint/                   # Deterministic lint runner             │
│    ├── query/                  # Structured answer protocol            │
│    ├── promote/                # Cross-project promotion pipeline     │
│    └── refresh/                # Upstream capture → re-ingest         │
│                                                                             │
│  AGENTS.md                    # This schema (global)                   │
│  opencode.json.template        # Project overlay template             │
│  .wiki-overlay.md.template     # Project overlay template            │
│  scripts/bootstrap-fabric.sh   # One-time global install script       │
└─────────────────────────────────────────────────────────────────────────────┘
```

### How Projects Connect

Each project has a **project overlay** (`.wiki-overlay.md`) that tells the agent:
- Which project namespace to use (`projects/my-project/`)
- Which domains to load (`agent-systems`, `godot-systems`, etc.)
- Which global skills to auto-load
- Project-specific source repos to refresh from

The agent loads **global fabric + project overlay** at session start. No per-project wiki copy.

---

## Two Extensions Over Base Pattern

1. **Evidence-first**: Every non-trivial assertion traces to a stable source locator; unsupported claims cannot become canonical.
2. **Global memory fabric**: Reusable knowledge is promoted from project-level experience to domain principles to global patterns via a reviewable lifecycle. Projects emit `experience-event` artifacts into their namespace; the fabric mines, clusters, and promotes them globally. **One fabric, many project namespaces.**

---

## Layers and Ownership

| Layer | Path | Owned by | Rules |
|---|---|---|---|
| **Raw** | `evidence/raw/` | user | Immutable. Capture by copy from source repos. Only content hashes (in source records) may update on refresh — never edit a raw file in place. |
| **Evidence** | `evidence/` | LLM | Source records, summaries, claims, experiments, change-sets. Compiled knowledge base. |
| **Project** | `projects/<repo>/` | LLM + user | Project-scoped experience events, decisions (ADR-like). One namespace per project. |
| **Domain** | `domains/<domain>/` | LLM | Concepts, questions, syntheses scoped to a technical domain. Cross-project. |
| **Global** | `global/` | LLM (proposal) + user (promotion) | Patterns, anti-patterns, skills, playbooks, decision-rules, entities, templates. Cross-project. |
| **Registry** | `registry/` | LLM | Indexes, promotion queue, append-only log. |
| **Schema** | `AGENTS.md` | shared | This file. Update when the pattern changes; log the change in `registry/log.md`. |

---

## Directory Map

See the ASCII tree above. Key principles:
- **One global fabric** at `~/wiki-fabric` (or wherever installed)
- **Projects are namespaces** under `projects/<repo>/` — not copies
- **Global assets** under `global/` are shared by all projects
- **Domains** are cross-project knowledge areas
- **Raw captures** under `evidence/raw/<repo>/` from upstream repos
- **Git history captures** under `evidence/raw/<repo>/git/` (PR/issue threads, high-signal commits via `capture-git.py`) — same immutable rules; PR/commit SHA are valid locators

---

## Note Types

Full frontmatter contracts live in `schemas/frontmatter.md`. One line each:

| Type | Home | Purpose |
|---|---|---|
| `source` | `evidence/sources/` | Immutable bibliographic record of one raw capture (path, sha256, kind, captured date) |
| `source-summary` | `evidence/source-summaries/` | Faithful summary of one source with line/section locators; no inference |
| `claim` | `evidence/claims/` | Atomic assertion with status, confidence, evidence refs, temporal fields |
| `entity` | `global/entities/` | Project / org / model / library / person / paper |
| `concept` | `concepts/` or `domains/<d>/concepts/` | Stable explanation built ONLY from linked claims |
| `question` | `domains/<d>/questions/` | Unresolved research question with priority + rationale |
| `synthesis` | `syntheses/` | Timed answer/comparison citing claims (an audience projection) |
| `decision` | `projects/<p>/decisions/` | ADR-like record of a project's technical choice |
| `experience-event` | `projects/<p>/experience-events/` | Structured observation: problem, intervention, conditions, outcomes |
| `pattern` | `patterns/` | Reusable context→problem→forces→solution with maturity + evidence lineage |
| `anti-pattern` | `anti-patterns/` | Repeated failure mode; detect and warn |
| `skill` | `skills/` | Reusable procedure with inputs/outputs |
| `experiment` | `evidence/experiments/` | Executable test contract: hypothesis, environment, metrics, results |
| `change-set` | `evidence/traces/change-sets/` | Agent-proposed edit batch, human-reviewed before canonical write |
| `promotion-dossier` | `registry/promotions/` | Proposal to promote a project finding to a global pattern |

**Scope field**: Every note has an implicit or explicit scope:
- `global` — `global/`, `registry/`, `schemas/`, `evaluations/`
- `domain` — `domains/<domain>/`
- `project` — `projects/<repo>/`

Naming: English kebab-case filenames. Wikilinks kebab-case `[[stem]]` by filename base; broken links are legal stubs (next lint step creates them), except claims and source refs which must resolve.

---

## Provenance Rules (Hard Invariants)

1. Every `claim` carries `source_refs`: `source` + `locator` + `quote` + `supports` for each supporting/contradicting record.
2. A `claim` with any `source_refs` is `status: supported` or better; with none it is `status: proposed`, `confidence: low`, and must not be cited by a `concept` or promoted to a `pattern`.
3. `concept` pages draw only from linked claims — never from raw prose.
4. Locators must be auditable: page/section/figure for PDFs, line ranges for captured transcripts (e.g. `L18-20`), commit SHA / issue number for code.
5. Content hash: each `source` record stores `sha256:` of its raw file. A changed hash = a new capture event, not an overwrite.

### Claim Frontmatter (Core)

```yaml
---
type: claim
id: claim-<slug>
statement: "..."
status: proposed | supported | contested | superseded | retracted
confidence: low | medium | high
evidence_strength: primary | secondary | tertiary
source_refs:
   - source: "[[src-...]]"
    locator: "L18-20"
    quote: "..."
    supports: true          # omit / false for contradicting refs
last_verified: YYYY-MM-DD
temporal:
   asserted_at: "..."       # when the source made the claim
   observed_at:  "..."      # when evidence was measured
   applies_when: "..."      # conditions: version/hardware/config
relations:
   - {type: supports|contradicts|refines|supersedes|depends_on, target: "[[claim-...]]"}
---
```

---

## Workflow

### Ingest Protocol (from `evidence/_inbox/` or a named `raw/` file)

1. Compute sha256; create/update the `source` record in `evidence/sources/`.
2. Write the `source-summary` — faithful, with locators, no inference.
3. Extract candidate `claim` pages (atomic, one proposition each) under `evidence/claims/`.
4. Retrieve affected claims, concepts, entities, decisions via `registry/catalog.json` then links (see retrieval policy).
5. Classify each new claim's effect: `add | support | weaken | contradict | supersede | no-action`.
6. Open a `change-set` in `evidence/traces/change-sets/<date-slug>/` with `manifest.md` (sources+hashes, pages created/updated/merged, new claims, newly detected contradictions, any source-less assertions, reason for each edit) and `diff.md`.
7. Run `python3 scripts/lint.py` (deterministic layer). Fix all errors.
4. Human gate: **ask for review before merging the change-set into canonical pages unless the change touches only staging pages** (new claims/summaries in `evidence/` are staging; canonical = `domains/`, `global/`, `projects/*/decisions/`).
5. Merge: apply manifest to canonical pages; append to `registry/log.md` in OKF §9 shape:
   `## YYYY-MM-DD` heading + `* **ingest | <slug>**` entry (one heading per day).
6. Commit: one ingest = one git commit; message names the change-set slug and includes the raw sha256 prefix.

### Query Protocol

For consequential questions, answer in this shape (file it as a `synthesis` if worth reusing):

```markdown
## Bottom line
## Evidence        # each claim cited with [[src-..]] + locator
## Caveats and conditions
## Confidence      # e.g. "Medium — 3 primary sources agree, not replicated on target config"
## Suggested next action
```

**Retrieval policy** — pick by query type, and record what was selected and why (explainability) when filing the answer:

| Query type | Retrieval |
|---|---|
| Exact repo/API/API-surface question | Lexical: `registry/catalog.json` → source record → raw |
| "What did we decide?" | `projects/*/decisions/` + recency-weighted synthesis |
| Cross-source conceptual synthesis | Claims → graph expansion via `relations` → linked sources |
| Claim verification | Claim registry + explicit locators only |
| Comparison (A vs B) | Experiment index filtered by environment/metrics |
| "What to investigate next?" | `questions/` + unresolved contradictions |

### Lint Protocol

**Deterministic first** (`scripts/lint.py`, 0 tokens): malformed frontmatter, broken wikilinks, duplicate ids, claims without evidence, circular `supersedes`, orphans, source hash drift, missing index entries.

**Semantic second** (LLM): duplicate concepts under different names, near-contradictions, weak synthesis, taxonomy drift, unasked-but-important gaps. **Evidence audit**: sample generated sentences, verify entailed by cited passage, not merely on-topic.

**Trust score (operational dashboard, not truth)**:
`T = w1·provenance_coverage + w2·review_coverage + w3·freshness + w4·link_integrity − w5·unresolved_contradictions`.

### Refresh Protocol

`refresh <repo>` — re-copy markdown from the source repo into `evidence/raw/<repo>/`; any file whose hash differs from its `source` record triggers a new ingest event (append, never overwrite).

**Automation — `wf hook`** (opt-in, per project): installs a git `post-commit` hook that
captures upstream doc drift and ingests it in the background (detached; never blocks the commit):

```bash
wf hook install                     # capture+ingest drift on commit (no LLM)
wf hook install --extract-claims    # also run LLM claim extraction on drift
wf hook status | uninstall
```

Hook semantics (mirrors graphify's hook design):
- **Drift-gated**: capture reports sha256 drift (`N new, M changed`); ingest runs only when drift exists — zero LLM cost on unchanged docs.
- **Self-skipping**: commits touching only fabric-owned paths (`evidence/`, `registry/`, `patterns/`, …) or non-md files never trigger capture (no rebuild loop).
- **Guards**: skips rebase/merge/cherry-pick, linked worktrees, and honors `WIKI_SKIP_HOOK=1`.
- **Detached**: output goes to `~/.cache/wiki-fabric-hook.log`; a failed hook never fails the commit.
- Coexists with other hooks: marker-delimited block appended after existing hook content (graphify's hook chains cleanly — keep its first line non-`exec` so later blocks still run).
- Bootstrap wires it at project setup: `wf bootstrap <path> --hook [--hook-extract-claims]`.

**Always-on instructions — `wf claude install`**: writes a managed `## wiki-fabric` block into
project `AGENTS.md`/`CLAUDE.md` (or `--user` → `~/.claude/CLAUDE.md`) instructing agents to run
`wf context` before tasks, `wf query` before grepping, and `wf log` after solving problems.
Marker-delimited, idempotent, refresh-safe (`wf claude uninstall` removes it).

**Session nudge — opencode plugin**: `bootstrap` installs `.opencode/plugins/wiki-fabric.js`
(modeled on graphify's plugin) which prepends a one-time reminder to the first bash call of a
session: prefer `wf context`/`wf query` over grep.

---

## Promotion Pipeline (Cross-Project)

```text
experience-event (project) → cluster (mining) → promotion-dossier
→ human review → pattern/anti-pattern/rule/skill with maturity 2+ → measured reuse
```

**Maturity** (evidence threshold → permission):

| Level | Threshold | Agents may |
|---|---|---|
| 0 hypothesis | idea / external source only | mention as question |
| 1 observed | one project/incident/experiment | suggest with local-context disclaimer |
| 2 replicated | ≥2 **independent** projects or controlled eval | recommend when `applicability` matches |
| 3 standard | repeated positive evidence + known tradeoffs + owner review | load by default |
| deprecated | superseded / disproven | surface as caution only |

**Independence**: two notes sharing one lineage (same source copied into two repos) count as one evidence. State the lineage. **Mining cadence**: on demand or weekly — not per edit. **No auto-promotion**: a `promotion-dossier` is proposed; only the user (or an explicitly governed agent) sets `status: recommended`/`standard`. **Feedback loop**: record reuse outcomes (`applied`, `overridden`, `outcome`) in the pattern page; a pattern read but never applied is too abstract — narrow or repackage.

---

## Git Policy

- One ingest = one commit; message: `ingest <change-set-slug> (raw <sha8>)`.
- Promotion = one commit; message: `promote <pattern-id> (maturity N)`.
- `registry/log.md` is append-only and tracked in the harness repo (seeded at bootstrap; created on ingest if missing). Entries use OKF §9 shape: `## YYYY-MM-DD` headings with `* **<op> | <subject>**` bullet lines. Raw is append-only-capture (new file, new hash).
- Never `git commit` a change-set that failed `scripts/lint.py`.
- **Team sync** (`wf sync`): corpus content shares to a dedicated `corpus` git remote (branch `corpus`); the harness remote is separate. Same-path edits from two machines become `registry/conflicts/<date>/` dossiers; unresolved conflicts fail lint and block `sync push`.

**Public harness repo vs. private fabric install:** this repo ships the harness
(scripts, schemas, templates, examples). In a personal fabric install, user
content (claims, captures, patterns, experience events) is typically gitignored;
in a shared/content-tracking install, it is committed. Either way, the git
policies above apply — but a public clone should never receive your personal
captures.

---

## OKF v0.2 Alignment

This fabric IS a conformant [OKF v0.2](https://okf.md/spec/) bundle (verified by
`lint --okf` and external `okflint validate --manifest okf-base.yaml`). Rules:

| Concept | Meaning | Enforcement |
|---|---|---|
| **Actor convention** (§7) | `agent/<owner>/<model>` for LLM-driven scripts, `human:<id>` for people, `process:<id>` for hooks/CI | `fabric_config.actor()`; lint rejects malformed `generated.by`/`verified.by` |
| **`generated {by, at}`** (§5.2) | who/what produced the content, when | written by ingest/synthesize/promote/mine/log-experience |
| **`verified[]`** | who/what confirmed content against sources | claims: `process:locator-verification`; promotions: `human:<owner>` — lint TRUST-TIER gate: `maturity >= 2` requires a `human:` verifier |
| **Trust tiers** (§5.3) | human-reviewed > machine-confirmed > unverified | advisory; surfaced per-item in `wf context` manifests |
| **`stale_after`** (§5.5) | absolute instant; content stale on/after it | lint STALE-AFTER checks; context demotes stale items |
| **Attested Computation** (§10) | sanctioned computation + executor + deterministic attester | `global/computations/`; promote refuses without attestation |
| **Conformance floor** (§11) | every non-reserved .md has frontmatter with non-empty `type`; `index.md`/`log.md` follow §8/§9 | `lint --okf` (CI-gated; okflint cross-check via `okf-base.yaml`) |

Export: `wf okf export --out DIR [--scope all|global|<slug>]` — deterministic portable bundle.
Import: `wf okf import <bundle> [--scope name]` — external bundles as immutable evidence
(trust recorded, never inherited; prompt-injection screen; quarantine to `evidence/_inbox/`).

---

## Agent Operating Rules (opencode)

### Tool Routing — Which Script for Which Task

**LLM tokens are spent on extraction and synthesis, never on retrieval.** Choose the right tool:

| Task | Tool | LLM Cost | When |
|------|------|----------|------|
| Find claims about X | `query.py` | **0** | "What do we know about X?" — lexical + graph expansion, no LLM |
| Compile task context | `context.py` | **0** | Before a task: scoped manifest (project>domain>global) with selection + exclusion reasons |
| Look up a code symbol | `build-entity-index.py` | **0** | "Where is `gather_reads` defined?" — AST lookup |
| Check fabric health | `lint.py` | **0** | Run after any edit batch, before commit |
| Detect code staleness | `graphify-bridge.py --diff` | **0** | Only when `integrations.graphify.enabled: true` in fabric.yaml (optional integration; skills carry the active/inactive delta) |
| Discover new domains | `propose-domains.py` | **0** | After ingesting new repos |
| Extract claims from source | `ingest.py --extract-claims` | 1 call | New source to compile — runs on the **compiler model** (`llm.compiler_model`, default `deepseek-v4.1-flash:cloud`), not the ops model |
| Synthesize concept | `synthesize.py` | 1 call | New claim cluster needing a concept page |
| Log experience event | `log-experience.py` | **0** | After solving a problem worth remembering |
| Mine cross-project patterns | `mine-promotions.py` | **0** | When ≥2 projects have experience events |
| Rebuild catalog | `rebuild-index.py` | **0** | After any ingest or promotion; writes `registry/catalog.json` (single machine registry) |
| Auto-refresh on commit | `wf hook install` | 0 (no LLM) or 1/doc (with `--extract-claims`) | One-time per project; then every doc-drift commit captures+ingests itself |
| Export portable bundle | `wf okf export` | **0** | Hand knowledge to any OKF consumer; deterministic, okflint-conformant |
| Ingest external bundle | `wf okf import` | 0 or 1/doc (`--extract-claims`) | Consume external OKF bundles as immutable evidence (trust recorded, not inherited) |
| Run an attestation | `references/attesters/*.py` | **0** | Verify a sanctioned computation's receipt before trusting its verdict (§10) |
| Machine-readable lint | `lint.py --format json` | **0** | CI + agent harnesses consume validation results |

### When NOT to use the LLM

- **Never call the LLM to search the fabric** — `query.py` retrieves via concept-overlap scoring and graph expansion. It only invokes the LLM if you ask it to synthesize a new answer to a consequential question (and even then, only when `--save` is used).
- **Never call the LLM to check code symbols** — `build-entity-index.py` uses AST parsing. The entity index is deterministic and auditable.
- **Never call the LLM to cluster claims** — `mine-promotions.py` uses keyword-based Jaccard clustering. The LLM only writes the dossier after the cluster is confirmed.
- **Never re-ingest a source that hasn't changed** — check the sha256 first. LLM extraction is the most expensive operation in the fabric.

### Anti-Loop Rules

1. **Ingest once** — if a source record exists with matching sha256, do not re-ingest. Check `registry/catalog.json`.
2. **Query before ingest** — before extracting claims from a new source, check if the same source is already captured (`evidence/sources/`).
3. **Lint before commit** — always run `scripts/lint.py` before any git commit. If lint fails, fix errors first.
4. **Ask before canonical edits** — stage in `evidence/` first, then present manifest + diff for human review.
5. **One operation per commit** — don't batch ingest + promote + synthesize into one git commit.
6. **Compiler model policy** — claim extraction, synthesis, and promotion mining run on
   `llm.compiler_model` (default `deepseek-v4.1-flash:cloud`), not the ops model.
   `promote.py` and `mine-promotions.py` refuse without a recorded compiler eval for
   the current compiler model (model swaps are compiler changes — eval-stability G4).

### Global Fabric Context

- The global fabric lives at `~/wiki-fabric` (or wherever installed via `bootstrap-fabric.sh`).
- Each project has a `.wiki-overlay.md` that specifies its namespace, domains, skills, and source repos.
- At session start, the agent loads **global AGENTS.md + project `.wiki-overlay.md`**.
- Source repos live at their original locations; `evidence/raw/<repo>/` is a snapshot — refresh it, don't hand-edit it.
- Ask before editing canonical pages; stage in `evidence/` first.
- When uncertain about structure, ask the user before inventing a convention.
- Prefer small, focused pages.

### Project Overlay (`.wiki-overlay.md`)

Each project creates a `.wiki-overlay.md` in its root:

```yaml
---
project: my-project
namespace: my-project              # projects/my-project/ in global fabric
domains:
  - agent-systems
  - godot-systems
skills:
  - serialize-and-verify-writes
  - batch-mutations
source_repos:
  - path: ../my-upstream-repo
    raw_path: evidence/raw/my-upstream-repo
    globs:
      - "*.md"
      - "docs/**/*.md"
---
```

The agent loads **global AGENTS.md + project .wiki-overlay.md** at session start.

---

## Installation (One-Time Global)

```bash
# Run once to install global fabric
bash ~/wiki-fabric/scripts/bootstrap-fabric.sh

# In each project:
cp ~/wiki-fabric/.wiki-overlay.md.template .wiki-overlay.md
# Edit .wiki-overlay.md with project-specific config

# Project's opencode.json should include:
{
  "references": {
    "wiki-fabric": { "path": "~/wiki-fabric", "description": "Global knowledge fabric" }
  },
  "instructions": ["~/wiki-fabric/AGENTS.md", ".wiki-overlay.md"]
}
```

---
