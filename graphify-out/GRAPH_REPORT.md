# Graph Report - wiki-fabric  (2026-09-21)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 1498 nodes · 2289 edges · 125 communities (103 shown, 20 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 102 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `83cb3517`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ingest.py
- commit_is_interesting
- mine-promotions.py
- hooks.py
- Domain Ontology
- generate
- eval-stability.py
- TestSiblingDiscovery
- actor
- test_okf.py
- bootstrap-project.py
- graphify-bridge.py
- lint.py
- sync.py
- test_lint_ingest.py
- TestScopeValidation
- context.py
- _page
- TestGraphifyBridgeCommands
- Troubleshooting
- Log
- get_ignores
- get_config
- Frontmatter Contracts
- wiki-fabric.sh
- test_wf_common.py
- Experiment: <Experiment Title>
- Procedure
- README.md
- package.json
- fabric_config.py
- propose-domains.py
- Contributing to Wiki Fabric
- architecture.md
- resolve_repo_path
- parse_frontmatter
- synthesize.py
- query.py
- Procedure
- eval-behavior.py
- okf_export.py
- Procedure
- test_sync.py
- eval-real-repo.py
- Decision: <title>
- TestExport
- CLI & Scripts Reference
- Configuration
- repos-migrate.py
- wf_common.py
- Daily Note: {{date:YYYY-MM-DD}}
- Skill: <Skill Name>
- TestRunner
- Behavior Evals & Model Policy
- Getting Started
- eval.py
- rebuild-index.py
- Query Skill
- TestMetrics
- Wiki Fabric
- always_on.py
- conformant/index.md
- _run_demo
- index.md
- Core Workflows
- looks_like_local_model
- TestLintLlmConfig
- norm
- Lint Skill
- Concept: <Concept Title>
- Experience Event: <brief-title>
- Pattern: <Pattern Title>
- _make_bundle
- Wiki Fabric — Agent Instructions
- How It Works: The Compiler
- How It Works: The Compounding Loop
- How It Works: Trust & Governance
- OKF v0.2: The Fabric Speaks the Standard
- Epic: OKF v0.2 Alignment
- Story: OKF conformance baseline
- Story: Frontmatter alignment with OKF recommended fields
- Story: Adopt OKF v0.2 trust + provenance families
- Story: Attested Computation — formalize eval/promotion as attestable runs
- Story: `wf okf export` — render the fabric as a portable OKF bundle
- Story: `wf okf import` — consume external OKF bundles as evidence
- check_actors
- Literature Note: <title>
- Evaluation Rubric
- _classify_ignore_pattern
- Context Skill
- How It Works: The Corpus & Connected Projects
- Optional Integrations
- Fixture A — harness performance excerpt
- Fixture C — two sources that contradict (test contradiction detection)
- demo.sh
- Quick Capture: {{value:title}}
- Architecture
- How It Works: Staying in Sync
- site/index.md
- The registry
- Team Sync
- smoke-test.sh
- cluster_by_concept
- check-golden-eval.py
- Promotion Queue
- wiki-fabric always-on block — written into CLAUDE.md / AGENTS.md by `wf claude install`
- wiki-fabric.js
- Log
- index-frontmatter/index.md
- source-b.md
- ac-fabric-profile-lint.md
- ac-golden-corpus-eval.md
- ac-locator-verification.md
- check-zero-errors.py
- run-golden-eval.md
- run-profile-lint.md
- Common (all pages)
- apply-changeset.sh
- setup-vault.sh
- claim-example-cache-invalidation.md
- experience-event-example.md
- no-frontmatter/note.md
- wiki-fabric

## God Nodes (most connected - your core abstractions)
1. `get_config()` - 57 edges
2. `parse_frontmatter()` - 29 edges
3. `get_ignores()` - 23 edges
4. `is_ignored()` - 22 edges
5. `Log` - 22 edges
6. `ensure_local_model()` - 21 edges
7. `Frontmatter Contracts` - 20 edges
8. `get_stage_route()` - 18 edges
9. `get_local_model()` - 16 edges
10. `get_all_repo_names()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `_mlx_available()` --calls--> `find_local_model_path()`  [INFERRED]
  tests/test_local_model.py → scripts/fabric_config.py
- `_gguf_available()` --calls--> `_resolve_gguf_path()`  [INFERRED]
  tests/test_local_model.py → scripts/local_llm.py
- `main()` --calls--> `extract_claims()`  [INFERRED]
  scripts/eval.py → scripts/extract_backends.py
- `get_config_safe()` --calls--> `get_config()`  [EXTRACTED]
  scripts/capture.py → scripts/fabric_config.py
- `extract_claims()` --calls--> `looks_like_local_model()`  [EXTRACTED]
  scripts/extract_backends.py → scripts/fabric_config.py

## Import Cycles
- None detected.

## Communities (125 total, 20 thin omitted)

### Community 0 - "ingest.py"
Cohesion: 0.06
Nodes (55): build_prompt(), extract_claims(), extract_claims_anthropic(), extract_claims_mlx(), extract_claims_openai_compatible(), _call(), extract_claims_opencode(), _json_repair_load() (+47 more)

### Community 1 - "commit_is_interesting"
Cohesion: 0.07
Nodes (21): capture_github(), capture_local(), churn_report(), commit_is_interesting(), gh(), git(), main(), Write a captured markdown file if content is new or changed. (+13 more)

### Community 2 - "mine-promotions.py"
Cohesion: 0.08
Nodes (34): get_stage_route(), is_local_route(), Resolve the LLM model for a workflow stage in a repo. Routing keys (per-repo…, True when the stage's route resolves to an on-device model (MLX/GGUF)., cluster_events(), cluster_events_keyword(), cluster_events_semantic(), escape_yaml() (+26 more)

### Community 3 - "hooks.py"
Cohesion: 0.09
Nodes (21): _find_fabric_dir(), _git_root(), _hooks_dir(), install(), _install_hook(), _installed_version(), Path, Nearest .git dir, or None. (+13 more)

### Community 4 - "Domain Ontology"
Cohesion: 0.29
Nodes (6): Domain Ontology, Domains, Independence rule, Retrieval signal types, Scope → home mapping, Shared tag set (lowercase)

### Community 5 - "generate"
Cohesion: 0.08
Nodes (24): find_local_model_path(), Return a local filesystem path when model_id points at a local dir, or a cached…, _apply_template(), backend_for(), generate(), _gguf_chat_or_complete(), _load(), GGUF: chat-tuned models (gemma etc.) return empty text from raw completion… (+16 more)

### Community 6 - "eval-stability.py"
Cohesion: 0.10
Nodes (30): fuzzy_coverage(), jaccard(), Token-set Jaccard similarity. Two empty sets are identical (1.0)., Mean best token-Jaccard of each source statement against target_set — robust to…, Stemming-ish token set for term-coverage scoring (was eval-pr-replay)., tokens(), compile_manifest(), fetch_pr() (+22 more)

### Community 7 - "TestSiblingDiscovery"
Cohesion: 0.09
Nodes (8): _make_world(), Tests for overlay-as-config: sibling discovery, routing merge, vault refresh., FABRIC_ROOT chain: WIKI_FABRIC_DIR > XDG default > harness (dev)., Fabric + two sibling projects with overlays; returns (fabric, projects)., TestFabricRootResolution, TestReposMigrate, TestSiblingDiscovery, TestVaultRefresh

### Community 8 - "actor"
Cohesion: 0.09
Nodes (31): actor(), compiler_eval_recorded(), get_owner(), Return the configured owner name., OKF v0.2 §7 actor convention string. kind="agent" -> agent/<script-…, True when registry/log.md contains a PASS compiler eval for the current…, _actor(), get_projects() (+23 more)

### Community 9 - "test_okf.py"
Cohesion: 0.10
Nodes (10): Tests for lint.py --okf (OKF v0.2 §11 conformance floor). Run: python3 -m…, Attester reads registry/log.md from the fabric root; seed a receipt in a temp…, Self-contained: copy the repo harness into tmp (no evidence content), seed a…, OKF §5.5 stale_after lint checks., _run_okf(), TestAttestedComputation, TestConformantBundle, TestMainBundle (+2 more)

### Community 10 - "bootstrap-project.py"
Cohesion: 0.11
Nodes (27): detect_available_domains(), detect_available_skills(), find_fabric_root(), get_corpus_remote(), git_config(), main(), prompt_multi(), prompt_with_default() (+19 more)

### Community 11 - "graphify-bridge.py"
Cohesion: 0.16
Nodes (25): get_integrations(), get_repo_graph_dir(), is_integration_active(), Merged integrations dict with defaults (enabled: False)., True when an optional integration is explicitly enabled in fabric.yaml., Get the graphify graph directory for a repo. Priority: explicit repo graph_dir…, cmd_diff(), cmd_enrich() (+17 more)

### Community 12 - "lint.py"
Cohesion: 0.13
Nodes (23): check_stale_after(), check_staleness(), check_status_collision(), _ignores(), is_placeholder(), is_tpl(), main(), md_files() (+15 more)

### Community 13 - "sync.py"
Cohesion: 0.21
Nodes (23): cmd_init(), cmd_pull(), cmd_push(), cmd_status(), content_changes(), describe_namespaces(), get_remote(), git_status() (+15 more)

### Community 14 - "test_lint_ingest.py"
Cohesion: 0.08
Nodes (6): Unit tests for lint.py helpers and ingest.py parsing logic. Run: python3 -m…, Regression: README/CONTRIBUTING are visitor-facing repo pages — no frontmatter…, TestIngestLineNumbers, TestIngestSlug, TestLintFrontmatter, TestLintHelpers

### Community 15 - "TestScopeValidation"
Cohesion: 0.10
Nodes (5): Unit tests for P1 lint additions: --format json, staleness, scope validation,…, TestJsonOutput, TestRegistryJson, TestScopeValidation, TestStaleness

### Community 16 - "context.py"
Cohesion: 0.13
Nodes (17): integrations_state(), is_stale(), load_corpus(), main(), Deterministic selection: project > domain > global, each with a reason. Returns…, OKF v0.2 §5.3 trust tier from verified[]: human-reviewed > machine-confirmed >…, Report optional-integration state for manifest transparency., Load all catalogable corpus pages with derived scope. (+9 more)

### Community 17 - "_page"
Cohesion: 0.13
Nodes (5): _FakePage, _page(), Unit tests for context.py — task-aware context manifest compilation. Run:…, TestOutputs, TestSelection

### Community 18 - "TestGraphifyBridgeCommands"
Cohesion: 0.11
Nodes (7): Unit tests for optional-integration gating (graphify, embeddings)., Happy-path coverage for the bridge commands (the REPO_CONFIG regression shipped…, graphify-bridge gate: runs against a temp fabric whose fabric.yaml enables…, The gate: a fabric with graphify disabled gets the enable message, not a crash., TestGraphifyBridgeCommands, TestGraphifyGate, TestIntegrationConfig

### Community 19 - "Troubleshooting"
Cohesion: 0.09
Nodes (22): Config & lint, `download failed: 401/403` (private/gated models), GGUF output is empty / synthesis falls back, Git hooks, Hook doesn't fire / capture never runs, Hook triggered ingest on every commit, Installation & environment, Lint passes locally, okflint fails in CI (+14 more)

### Community 20 - "Log"
Cohesion: 0.09
Nodes (22): 2026-09-18, 2026-09-18, 2026-09-18, 2026-09-18, 2026-09-18, 2026-09-18, 2026-09-18, 2026-09-18 (+14 more)

### Community 21 - "get_ignores"
Cohesion: 0.23
Nodes (8): get_ignores(), is_ignored(), Return merged ignore patterns from fabric.yaml. Schema: ignore: patterns:…, Shared ignore predicate. globs are fnmatch-style with ** support: '**' crosses…, fabric.yaml ignore section (globs + regexes + per-repo merge)., TestIgnores, ignore.patterns: one list, auto-classified (glob default, regex on…, TestUnifiedIgnorePatterns

### Community 22 - "get_config"
Cohesion: 0.15
Nodes (14): main(), get_all_repo_names(), get_config(), Load fabric.yaml, merged with defaults. Returns dict. Memoized per process,…, Return list of configured repo names (explicit + discovered)., Reinstall outdated hook blocks in connected repos (wf update calls this)., reinstall(), default_vault_path() (+6 more)

### Community 23 - "Frontmatter Contracts"
Cohesion: 0.11
Nodes (19): `anti-pattern`, `attested-computation` (OKF v0.2 §10), `change-set`, `claim`, `concept`, `decision`, `entity` (reference-only), `experience-event` (+11 more)

### Community 24 - "wiki-fabric.sh"
Cohesion: 0.37
Nodes (19): cmd_bootstrap(), cmd_install(), cmd_status(), cmd_update(), cmd_vault(), ensure_directories(), ensure_fabric_yaml(), ensure_uv() (+11 more)

### Community 25 - "test_wf_common.py"
Cohesion: 0.13
Nodes (6): Tests for wf_common shared helpers + adoption across scripts., The duplication fix: these scripts must import from wf_common, not re-define…, bootstrap-project's slugify collapses double dashes — intentionally local., TestLintIgnoreConfig, TestParseFrontmatter, TestScriptsUseSharedHelpers

### Community 26 - "Experiment: <Experiment Title>"
Cohesion: 0.11
Nodes (17): Analysis, Artifacts, Baseline Pairing Verifier Protocol, Baseline (Reference Implementation), Conclusion, Experiment: <Experiment Title>, Hypothesis, Metrics (+9 more)

### Community 27 - "Procedure"
Cohesion: 0.12
Nodes (16): 1. Check Before Ingesting (anti-loop), 2. Run the CLI, 3. Verify Extraction (LLM judgment), 4. Classify Effects, 4a. If graphify is ACTIVE: enrich claims with code provenance, 5. Open Change-Set, 6. Lint, 7. Human Gate (+8 more)

### Community 28 - "README.md"
Cohesion: 0.33
Nodes (3): Task Context: Deterministic Context Assembly, What the manifest guarantees, Governance: The Answers, Enforced

### Community 29 - "package.json"
Cohesion: 0.13
Nodes (14): dependencies, mermaid, vitepress-plugin-mermaid, devDependencies, vitepress, name, private, scripts (+6 more)

### Community 30 - "fabric_config.py"
Cohesion: 0.14
Nodes (15): _config_fingerprint(), get_config_clear_cache(), get_discovered_repos(), get_repo_config(), _merge_user_config(), _overlay_fingerprint(), Shared configuration for wiki-fabric scripts. Reads fabric.yaml from the fabric…, Cheap identity of the config inputs: file mtime+size and the env vars that… (+7 more)

### Community 31 - "propose-domains.py"
Cohesion: 0.20
Nodes (15): build_signal_lookup(), compute_domain_scores(), load_ontology_domains(), main(), match_signal(), Scan claim tags for domain signals., Scan source records for domain signals., Parse existing domains from ontology.md. (+7 more)

### Community 32 - "Contributing to Wiki Fabric"
Cohesion: 0.14
Nodes (13): 1. Ingest a New Source, 2. Run Evaluation Fixtures, 3. Add a Skill, 3. Promote a Pattern, Code Style, Contributing to Wiki Fabric, Evaluation Discipline, Git Discipline (+5 more)

### Community 33 - "architecture.md"
Cohesion: 0.20
Nodes (6): Context compilation: precedence at work, How It Works: Retrieval & Delivery, Query: the question with a citation, Why deterministic matters, What Is This?, Why Not Just a Wiki, Notes App, or RAG (Retrieval-Augmented Generation)?

### Community 34 - "resolve_repo_path"
Cohesion: 0.21
Nodes (13): enrich_claims_with_code_locators(), extract_gdscript(), extract_python_symbols(), index_repo(), main(), Walk a repo and extract all code symbols. fabric.yaml ignore rules apply., Group symbols by module/file and write entity pages., Post-process: enrich claims that mention indexed code symbols. (+5 more)

### Community 35 - "parse_frontmatter"
Cohesion: 0.23
Nodes (13): capture_project(), get_config_safe(), get_source_repos(), main(), match_globs(), process_sources(), Copy files from source repos into evidence/raw/<slug>/. Relative `path:`…, Read source_repos from the project's .wiki-overlay.md in the fabric. (+5 more)

### Community 36 - "synthesize.py"
Cohesion: 0.21
Nodes (13): llm_config(), Read LLM config from fabric.yaml + env overrides. compiler=True routes to the…, generate_concept_slug(), load_claims(), load_existing_concepts(), main(), Generate a concept slug from the cluster's common theme., Use LLM to synthesize a concept from a cluster of claims. Backend:… (+5 more)

### Community 37 - "query.py"
Cohesion: 0.21
Nodes (13): expand_graph(), generate_answer(), load_pages(), load_relations(), main(), Load claim relations for graph expansion., Expand results through claim relations (graph expansion)., Produce a structured answer per the query protocol. (+5 more)

### Community 38 - "Procedure"
Cohesion: 0.14
Nodes (13): 1. Identify Sources, 2. Capture, 3. Detect Changes, 3a. If graphify is ACTIVE: staleness diff first, 4. Re-ingest Changed Only (anti-loop), 5. Log + Commit, CLI Commands, Error Handling (+5 more)

### Community 39 - "eval-behavior.py"
Cohesion: 0.26
Nodes (12): assemble_prompt(), compile_manifest(), llm_probe(), load_fixture(), main(), Manifest-level compliance checks (no LLM needed)., Copy the harness (scripts/schemas) into a fresh temp fabric, then write seed…, Agent prompt assembled from the manifest (same shape as demo.sh). (+4 more)

### Community 40 - "okf_export.py"
Cohesion: 0.26
Nodes (12): convert_links(), repl(), export(), _fm_link(), main(), Inline-link resolver for YAML scalars: replace [[stem]] with the path., Stem -> list of bundle-relative paths (first wins on export)., [[stem]] -> [stem](/path.md); unknown stems stay as plain text. (+4 more)

### Community 41 - "Procedure"
Cohesion: 0.15
Nodes (12): 1. Cluster Experience Events (deterministic), 2. Generate Dossiers, 3. Update Promotion Queue, 4. Human Review (mandatory, no auto-promotion), 5. Promote, 6. Feedback Loop, CLI Commands, Error Handling (+4 more)

### Community 42 - "test_sync.py"
Cohesion: 0.15
Nodes (4): Unit tests for sync.py — corpus sharing logic. Run: python3 -m pytest…, TestConflicts, TestContentChanges, TestContentPathFilter

### Community 43 - "eval-real-repo.py"
Cohesion: 0.26
Nodes (11): capture_docs(), entity_index_stats(), ingest_claim(), main(), manifest_stats(), LLM claim extraction for one doc. Returns parsed claims count., Graphify tier: run the AST entity index against the connected repo (by name,…, Copy the harness into a fresh fabric with integrations enabled. (+3 more)

### Community 44 - "Decision: <title>"
Cohesion: 0.17
Nodes (11): Consequences, Context, Decision, Decision: <title>, Negative, Positive, Rationale, Related Claims (+3 more)

### Community 45 - "TestExport"
Cohesion: 0.35
Nodes (3): Tests for okf_export.py (Story 5 — wf okf export)., Copy the harness into tmp, then seed one source + one claim there. Never…, TestExport

### Community 46 - "CLI & Scripts Reference"
Cohesion: 0.18
Nodes (11): CLI Reference (`wf`), CLI & Scripts Reference, Fabric Inventory, Lifecycle: how pages move through statuses, Note Types, Scripts Reference, Vault & status commands (the human views), `wf integrations` — what's active (+3 more)

### Community 47 - "Configuration"
Cohesion: 0.18
Nodes (11): Configuration, Connecting repos: config lives in the project, Domains, Environment variables (override fabric.yaml per-run), Ignoring files, Integrations, LLM providers (any OpenAI-compatible endpoint), Model tiers: ops vs compiler vs local (+3 more)

### Community 48 - "repos-migrate.py"
Cohesion: 0.29
Nodes (10): _find_config_file(), Find fabric.yaml in fabric root or home directory., apply_moves(), main(), overlay_path_for(), plan(), prune_fabric_yaml(), Return [(slug, keys_to_move, overlay_path_or_None)]. (+2 more)

### Community 49 - "wf_common.py"
Cohesion: 0.18
Nodes (7): now_iso_utc(), Hex sha256 of a file's bytes (ingest/capture/lint/okf_export)., Local-date ISO string (frontmatter `created`/`updated`/`captured`)., ISO-8601 instant with explicit UTC offset (OKF §5)., sha256_file(), today(), TestHelpers

### Community 50 - "Daily Note: {{date:YYYY-MM-DD}}"
Cohesion: 0.18
Nodes (10): Daily Note: {{date:YYYY-MM-DD}}, 📝 Decisions Made, 📤 Experience Events to Capture, 📝 Fabric Queries, 🔍 Fabric Queries Run, 📥 Inbox, 💡 Insights / Observations, 📊 Metrics (+2 more)

### Community 51 - "Skill: <Skill Name>"
Cohesion: 0.18
Nodes (10): 1. <Step Name>, 2. <Step Name>, Error Handling, Example, Inputs, Outputs, Procedure, Related (+2 more)

### Community 52 - "TestRunner"
Cohesion: 0.18
Nodes (4): Unit tests for eval-behavior.py — the P4 behavior evaluation runner. Run:…, Seeds alone (no repo content dirs) must produce a working manifest., TestRunner, TestSeedIsolation

### Community 53 - "Behavior Evals & Model Policy"
Cohesion: 0.20
Nodes (10): Behavior Evals & Model Policy, Local vs cloud: what the small-model tests actually showed, Model policy: ops vs compiler models, Policy consequences, PR replay evaluation, Real-repo evaluation, Stability & sensitivity evaluation, The benchmark (+2 more)

### Community 54 - "Getting Started"
Cohesion: 0.20
Nodes (10): 1. The 30-second proof (no install), 2. Install the `wf` CLI, 3. Verify the install, 4. Connect your first project, Automate the loop (opt-in), Getting Started, Keeping up to date, Manual install (equivalent) (+2 more)

### Community 55 - "eval.py"
Cohesion: 0.29
Nodes (9): concept_match(), Loose semantic match: check for key concept overlap. Previously in eval.py;…, extract_contradictions(), extract_expected(), main(), Parse expected/claims.yaml into structured golden claims., Parse expected/contradictions.yaml., Score a single fixture's extraction against golden expectations. (+1 more)

### Community 56 - "rebuild-index.py"
Cohesion: 0.27
Nodes (8): build_catalog(), first_summary_line(), main(), Single machine registry: registry/catalog.json. Replaces: catalog.md,…, Extract a one-line summary from the body, stripping wikilinks., Walk the vault and categorize pages by directory., scan_vault(), write_catalog()

### Community 57 - "Query Skill"
Cohesion: 0.20
Nodes (9): Answer Format, Anti-patterns to Avoid, CLI Commands, Explainability, Output, Procedure, Query Skill, Query Types (route by type) (+1 more)

### Community 58 - "TestMetrics"
Cohesion: 0.20
Nodes (3): Unit tests for eval-stability.py — reproducibility and sensitivity gates., TestCIGate, TestMetrics

### Community 59 - "Wiki Fabric"
Cohesion: 0.22
Nodes (9): Documentation, License, Quick Start, Repository layout, Status & roadmap, The Loop (one page, start to finish), The one-session proof, Verify the install (+1 more)

### Community 60 - "always_on.py"
Cohesion: 0.53
Nodes (8): _block_text(), _has_marker(), install(), main(), Path, status(), _target(), uninstall()

### Community 61 - "conformant/index.md"
Cohesion: 0.22
Nodes (5): Conformant Fixture, 2026-09-16, 2026-09-17, Update Log, Schema

### Community 62 - "_run_demo"
Cohesion: 0.36
Nodes (3): Unit tests for demo.sh — the P0 one-session value proof. The demo must fail…, _run_demo(), TestDemo

### Community 63 - "index.md"
Cohesion: 0.25
Nodes (4): Bundle Map, Concepts, Logs, Wiki Fabric — Knowledge Bundle

### Community 64 - "Core Workflows"
Cohesion: 0.25
Nodes (8): 1. Ingest: Source → Claims, 1a. Git History Capture: PRs, Issues, Commits → Raw Evidence, 2. Query: Question → Evidence-Backed Answer, 3. Experience → Pattern → Skill (Compounding Loop), 4. Bootstrapping: Connect a New Project, 5. Maintenance, 6. Hooks: The Loop Runs Itself (opt-in), Core Workflows

### Community 65 - "looks_like_local_model"
Cohesion: 0.39
Nodes (3): looks_like_local_model(), Heuristic: True when a model string should run on-device. Matches the local…, TestLooksLikeLocalModel

### Community 66 - "TestLintLlmConfig"
Cohesion: 0.39
Nodes (3): check_llm_config(), Deterministic fabric.yaml llm.* checks. Returns list of problems. Shape rules:…, TestLintLlmConfig

### Community 67 - "norm"
Cohesion: 0.29
Nodes (8): concept_match(), Score how well a piece of text matches a query by concept overlap., cluster_claims(), find(), union(), Cluster claims by concept-overlap of their statements., norm(), Normalize free text for fuzzy matching (query/synthesize/eval).

### Community 68 - "Lint Skill"
Cohesion: 0.25
Nodes (7): CLI Commands, Integration, Lint Skill, Output Format, Procedure, What It Checks, When to Use

### Community 69 - "Concept: <Concept Title>"
Cohesion: 0.25
Nodes (7): Applicability, Concept: <Concept Title>, Definition, Open Questions, Relationships, Source Locators, Supporting Claims

### Community 70 - "Experience Event: <brief-title>"
Cohesion: 0.25
Nodes (7): Conditions, Confidence, Evidence, Experience Event: <brief-title>, Intervention, Observed Problem, Outcomes

### Community 71 - "Pattern: <Pattern Title>"
Cohesion: 0.25
Nodes (7): Applicability, Counterexamples, Evidence, Pattern, Pattern: <Pattern Title>, Related, Review

### Community 72 - "_make_bundle"
Cohesion: 0.39
Nodes (3): _make_bundle(), Tests for okf_import.py (Story 6 — wf okf import)., TestImport

### Community 73 - "Wiki Fabric — Agent Instructions"
Cohesion: 0.29
Nodes (7): Anti-Loop Rules, Common Tasks, Non-Negotiable Rules, Tests, When NOT to use the LLM, Where Things Live, Wiki Fabric — Agent Instructions

### Community 74 - "How It Works: The Compiler"
Cohesion: 0.29
Nodes (7): Before the LLM sees anything, How It Works: The Compiler, One prompt, one contract, The human gate, The repair pass: why models get credit for honesty, Verification, not trust, Why the anti-loop matters

### Community 75 - "How It Works: The Compounding Loop"
Cohesion: 0.29
Nodes (7): How It Works: The Compounding Loop, Step 1: The honest record, Step 2: Deterministic mining, Step 3: The dossier, Step 4: The human gate, What compounding looks like, Why independence is the whole trick

### Community 76 - "How It Works: Trust & Governance"
Cohesion: 0.29
Nodes (7): Actors: the audit trail, Attested computations: proving the verdict, Freshness: three declarations, one linter, How It Works: Trust & Governance, Provenance: every statement carries its receipt, The compiler-eval gate, What happens when trust fails

### Community 77 - "OKF v0.2: The Fabric Speaks the Standard"
Cohesion: 0.29
Nodes (7): Attested computations (§10), Exchange, Export: your fabric as a portable bundle, Import: external knowledge as *quarantined evidence*, OKF v0.2: The Fabric Speaks the Standard, Trust & provenance (portable), Writing provenance: the actor convention

### Community 79 - "Epic: OKF v0.2 Alignment"
Cohesion: 0.29
Nodes (7): Epic: OKF v0.2 Alignment, Gap Analysis (current schema vs OKF v0.2), Log, Non-Goals, Stories, Strategy, Why

### Community 80 - "Story: OKF conformance baseline"
Cohesion: 0.29
Nodes (7): Acceptance criteria, As a, I want, Log, Notes, So that, Story: OKF conformance baseline

### Community 81 - "Story: Frontmatter alignment with OKF recommended fields"
Cohesion: 0.29
Nodes (7): Acceptance criteria, As a, I want, Log, Notes, So that, Story: Frontmatter alignment with OKF recommended fields

### Community 82 - "Story: Adopt OKF v0.2 trust + provenance families"
Cohesion: 0.29
Nodes (7): Acceptance criteria, As a, I want, Log, Notes, So that, Story: Adopt OKF v0.2 trust + provenance families

### Community 83 - "Story: Attested Computation — formalize eval/promotion as attestable runs"
Cohesion: 0.29
Nodes (7): Acceptance criteria, As a, I want, Log, Notes, So that, Story: Attested Computation — formalize eval/promotion as attestable runs

### Community 84 - "Story: `wf okf export` — render the fabric as a portable OKF bundle"
Cohesion: 0.29
Nodes (7): Acceptance criteria, As a, I want, Log, Notes, So that, Story: `wf okf export` — render the fabric as a portable OKF bundle

### Community 85 - "Story: `wf okf import` — consume external OKF bundles as evidence"
Cohesion: 0.29
Nodes (7): Acceptance criteria, As a, I want, Log, Notes, So that, Story: `wf okf import` — consume external OKF bundles as evidence

### Community 86 - "check_actors"
Cohesion: 0.33
Nodes (4): check_actors(), OKF §7 actor convention + §5.2 trust fields (best-effort, warning-level)., OKF §7 actor convention + §5.2 trust fields., TestActors

### Community 87 - "Literature Note: <title>"
Cohesion: 0.29
Nodes (6): Key Claims, Key Insights, Literature Note: <title>, Questions Raised, Source, To Ingest

### Community 88 - "Evaluation Rubric"
Cohesion: 0.33
Nodes (5): Evaluation Rubric, Metrics (from the source document), Pass thresholds (initial), Run protocol, What this is for

### Community 89 - "_classify_ignore_pattern"
Cohesion: 0.40
Nodes (5): _classify_ignore_pattern(), Auto-classify an ignore pattern as "glob" or "regex". Explicit prefix wins: a…, check_ignore_config(), _scan(), Deterministic ignore.* checks. Invalid regex patterns are skipped silently by…

### Community 90 - "Context Skill"
Cohesion: 0.33
Nodes (5): Context Skill, Reading the Manifest, Rules, Usage, When to Use

### Community 91 - "How It Works: The Corpus & Connected Projects"
Cohesion: 0.40
Nodes (5): Discovery: the fabric finds projects itself, How It Works: The Corpus & Connected Projects, The corpus: the fabric's shareable half, The overlay: a project's whole relationship with the fabric, Three kinds of tree

### Community 92 - "Optional Integrations"
Cohesion: 0.40
Nodes (5): Enabling, Optional Integrations, Skill deltas when graphify is active, The fabric's self-graph, What each integration does

### Community 93 - "Fixture A — harness performance excerpt"
Cohesion: 0.40
Nodes (4): 1. Batch arbitrary commands — `composite_run_commands` (#167), 2. Pipeline independent reads — `gather_reads` (#169), 3. Cache stable reads — `ReadCache` (#170), Fixture A — harness performance excerpt

### Community 94 - "Fixture C — two sources that contradict (test contradiction detection)"
Cohesion: 0.40
Nodes (4): Expected behavior, Fixture C — two sources that contradict (test contradiction detection), Source C1: an engineering blog (secondary), Source C2: a primary paper abstract (primary)

### Community 95 - "demo.sh"
Cohesion: 0.70
Nodes (4): die(), pass(), demo.sh script, step()

### Community 96 - "Quick Capture: {{value:title}}"
Cohesion: 0.40
Nodes (4): Quick Capture: {{value:title}}, Quick Links, Raw Input, To Process

### Community 97 - "Architecture"
Cohesion: 0.50
Nodes (4): Architecture, Module map, Reading order, The pipeline

### Community 98 - "How It Works: Staying in Sync"
Cohesion: 0.50
Nodes (4): CI: the fabric checks its own homework, How It Works: Staying in Sync, The freshness contract, end to end, The hook loop: drift → capture → compile

### Community 99 - "site/index.md"
Cohesion: 0.50
Nodes (3): The problem, in one paragraph, The proof in one session, Why this matters if you've never used a "second brain" or LLM wiki

### Community 100 - "The registry"
Cohesion: 0.50
Nodes (4): Machine-Readable Contract, `registry/catalog.json` — what knowledge exists, `registry/log.md` — the append-only timeline, The registry

### Community 101 - "Team Sync"
Cohesion: 0.50
Nodes (4): Conflict policy: review queue, never silent overwrite, How bootstrap meets the corpus, Team Sync, Why a separate remote from this public repo

### Community 102 - "smoke-test.sh"
Cohesion: 0.83
Nodes (3): fail(), pass(), smoke-test.sh script

### Community 103 - "cluster_by_concept"
Cohesion: 0.67
Nodes (4): cluster_by_concept(), find(), union(), Cluster claims by concept-overlap (extracted for testability).

## Knowledge Gaps
- **376 isolated node(s):** ``registry/catalog.json` — what knowledge exists`, ``registry/log.md` — the append-only timeline`, `Conflict policy: review queue, never silent overwrite`, `How bootstrap meets the corpus`, `Why a separate remote from this public repo` (+371 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 753 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_config()` connect `get_config` to `ingest.py`, `resolve_repo_path`, `parse_frontmatter`, `synthesize.py`, `hooks.py`, `mine-promotions.py`, `actor`, `bootstrap-project.py`, `graphify-bridge.py`, `lint.py`, `context.py`, `repos-migrate.py`, `rebuild-index.py`, `fabric_config.py`, `propose-domains.py`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Why does `get_local_model()` connect `ingest.py` to `mine-promotions.py`, `synthesize.py`, `TestSiblingDiscovery`, `get_config`, `fabric_config.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `get_config()` (e.g. with `.test_cache_invalidation_on_env_change()` and `.test_defaults_not_mutated_by_get_config()`) actually correct?**
  _`get_config()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `get_ignores()` (e.g. with `.test_glob_starstar()` and `.test_no_section_noop()`) actually correct?**
  _`get_ignores()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `is_ignored()` (e.g. with `.test_glob_starstar()` and `.test_no_section_noop()`) actually correct?**
  _`is_ignored()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects ``registry/catalog.json` — what knowledge exists`, ``registry/log.md` — the append-only timeline`, `Conflict policy: review queue, never silent overwrite` to the rest of the system?**
  _376 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ingest.py` be split into smaller, more focused modules?**
  _Cohesion score 0.05547785547785548 - nodes in this community are weakly interconnected._