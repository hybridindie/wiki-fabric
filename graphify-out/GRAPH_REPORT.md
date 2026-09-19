# Graph Report - wf-graph-corpus  (2026-09-18)

## Corpus Check
- Corpus is ~47,295 words - fits in a single context window. You may not need a graph.

## Summary
- 539 nodes · 1007 edges · 24 communities (22 shown, 2 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 23 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Config & Local Models
- Golden Eval Harness
- Entity Index
- Actors & Eval Policy
- Docs: Commands & Model Policy
- Lint & Config Validation
- Project Bootstrap
- Ingest & Synthesis
- Graphify Integration
- Team Sync
- Git History Capture
- Task Context
- Stability Evals
- Git Hooks
- Query Engine
- Domain Proposal
- Behavior Evals
- Local LLM Backends
- OKF Export
- PR Replay Evals
- Real-Repo Evals
- Always-On Docs
- Frontmatter Contracts
- Wikilink Rules

## God Nodes (most connected - your core abstractions)
1. `get_config()` - 45 edges
2. `main()` - 15 edges
3. `ensure_local_model()` - 15 edges
4. `main()` - 14 edges
5. `get_stage_route()` - 13 edges
6. `is_local_route()` - 13 edges
7. `get_all_repo_names()` - 12 edges
8. `actor()` - 12 edges
9. `resolve_repo_path()` - 11 edges
10. `get_local_model()` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Evidence Independence Rule` --semantically_similar_to--> `Two-Independent-Projects Rule`  [INFERRED] [semantically similar]
  schemas/ontology.md → README.md
- `get_config_safe()` --calls--> `get_config()`  [EXTRACTED]
  capture.py → fabric_config.py
- `Wiki Fabric` --references--> `Domain Ontology`  [INFERRED]
  README.md → schemas/ontology.md
- `promotion-dossier type` --implements--> `Promotion Pipeline (experience to pattern to skill)`  [INFERRED]
  schemas/frontmatter.md → README.md
- `detect_available_domains()` --calls--> `get_config()`  [EXTRACTED]
  bootstrap-project.py → fabric_config.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Promotion Pipeline Flow (claims to concepts to patterns to dossiers)** — schemas_frontmatter_claim_type, schemas_frontmatter_concept_type, schemas_frontmatter_pattern_type, schemas_frontmatter_promotion_dossier_type, readme_promotion_pipeline [INFERRED 0.95]
- **Trust Governance Mechanisms** — readme_trust_tiers, schemas_frontmatter_maturity_gate, schemas_ontology_independence_rule, readme_provenance_staleness_gates, schemas_frontmatter_stale_after [INFERRED 0.85]

## Communities (24 total, 2 thin omitted)

### Community 0 - "Config & Local Models"
Cohesion: 0.06
Nodes (52): main(), ensure_local_model(), _ensure_lock(), _find_config_file(), find_local_model_path(), get_config(), get_local_model(), get_stage_route() (+44 more)

### Community 1 - "Golden Eval Harness"
Cohesion: 0.06
Nodes (49): concept_match(), extract_contradictions(), extract_expected(), main(), norm(), Normalize text for fuzzy matching., Parse expected/claims.yaml into structured golden claims., Parse expected/contradictions.yaml. (+41 more)

### Community 2 - "Entity Index"
Cohesion: 0.07
Nodes (42): enrich_claims_with_code_locators(), extract_gdscript(), extract_python_symbols(), index_repo(), main(), Walk a repo and extract all code symbols. fabric.yaml ignore rules apply., Group symbols by module/file and write entity pages., Post-process: enrich claims that mention indexed code symbols. (+34 more)

### Community 3 - "Actors & Eval Policy"
Cohesion: 0.09
Nodes (32): actor(), compiler_eval_recorded(), get_owner(), Return the configured owner name., OKF v0.2 §7 actor convention string. kind="agent" -> agent/<script-…, True when registry/log.md contains a PASS compiler eval for the current…, _actor(), get_projects() (+24 more)

### Community 4 - "Docs: Commands & Model Policy"
Cohesion: 0.09
Nodes (31): Behavior Evaluations, Model Policy: Ops vs Compiler, wf context, wf ingest, wf lint, llm.compiler_model, llm.local_model, wf okf export/import (+23 more)

### Community 5 - "Lint & Config Validation"
Cohesion: 0.11
Nodes (29): looks_like_local_model(), Heuristic: True when a model string should run on-device. Matches the local…, check_actors(), check_llm_config(), check_stale_after(), check_staleness(), check_status_collision(), _ignores() (+21 more)

### Community 6 - "Project Bootstrap"
Cohesion: 0.11
Nodes (27): detect_available_domains(), detect_available_skills(), find_fabric_root(), get_corpus_remote(), git_config(), main(), prompt_multi(), prompt_with_default() (+19 more)

### Community 7 - "Ingest & Synthesis"
Cohesion: 0.12
Nodes (25): extract_claims_openai_compatible(), llm_config(), Primary: OpenAI-compatible endpoint (Ollama, OpenAI, vLLM, LM Studio, etc.)., Read LLM config from fabric.yaml + env overrides. compiler=True routes to the…, cluster_by_concept(), find(), union(), cluster_claims() (+17 more)

### Community 8 - "Graphify Integration"
Cohesion: 0.15
Nodes (24): get_integrations(), get_repo_graph_dir(), is_integration_active(), Get the graphify graph directory for a repo., Merged integrations dict with defaults (enabled: False)., True when an optional integration is explicitly enabled in fabric.yaml., cmd_diff(), cmd_enrich() (+16 more)

### Community 9 - "Team Sync"
Cohesion: 0.21
Nodes (23): cmd_init(), cmd_pull(), cmd_push(), cmd_status(), content_changes(), describe_namespaces(), get_remote(), git_status() (+15 more)

### Community 10 - "Git History Capture"
Cohesion: 0.18
Nodes (17): capture_github(), capture_local(), churn_report(), commit_is_interesting(), gh(), git(), main(), Write a captured markdown file if content is new or changed. (+9 more)

### Community 11 - "Task Context"
Cohesion: 0.16
Nodes (17): integrations_state(), is_stale(), load_corpus(), main(), parse_frontmatter(), review_after in the past → stale. Returns days overdue or 0., Deterministic selection: project > domain > global, each with a reason. Returns…, OKF v0.2 §5.3 trust tier from verified[]: human-reviewed > machine-confirmed >… (+9 more)

### Community 12 - "Stability Evals"
Cohesion: 0.19
Nodes (17): build_fabric(), claim_statements(), fuzzy_coverage(), gate_context_determinism(), gate_ingest_stability(), gate_model_sensitivity(), gate_rebuild_determinism(), jaccard() (+9 more)

### Community 13 - "Git Hooks"
Cohesion: 0.24
Nodes (16): _find_fabric_dir(), _git_root(), _hooks_dir(), install(), _install_hook(), _installed_version(), Path, Nearest .git dir, or None. (+8 more)

### Community 14 - "Query Engine"
Cohesion: 0.18
Nodes (17): concept_match(), expand_graph(), generate_answer(), load_pages(), load_relations(), main(), norm(), parse_frontmatter() (+9 more)

### Community 15 - "Domain Proposal"
Cohesion: 0.20
Nodes (16): build_signal_lookup(), compute_domain_scores(), load_ontology_domains(), main(), match_signal(), parse_frontmatter(), Scan claim tags for domain signals., Scan source records for domain signals. (+8 more)

### Community 16 - "Behavior Evals"
Cohesion: 0.26
Nodes (12): assemble_prompt(), compile_manifest(), llm_probe(), load_fixture(), main(), Manifest-level compliance checks (no LLM needed)., Copy the harness (scripts/schemas) into a fresh temp fabric, then write seed…, Agent prompt assembled from the manifest (same shape as demo.sh). (+4 more)

### Community 17 - "Local LLM Backends"
Cohesion: 0.22
Nodes (12): _apply_template(), backend_for(), generate(), _gguf_chat_or_complete(), _load(), GGUF: chat-tuned models (gemma etc.) return empty text from raw completion…, Run a single completion on the on-device backend. Serialized: one model in…, Return "mlx" | "gguf" for a model id/path, or None when unresolvable. (+4 more)

### Community 18 - "OKF Export"
Cohesion: 0.26
Nodes (12): convert_links(), repl(), export(), _fm_link(), main(), Inline-link resolver for YAML scalars: replace [[stem]] with the path., Stem -> list of bundle-relative paths (first wins on export)., [[stem]] -> [stem](/path.md); unknown stems stay as plain text. (+4 more)

### Community 19 - "PR Replay Evals"
Cohesion: 0.29
Nodes (11): compile_manifest(), fetch_pr(), gh(), ingest_pr_thread(), main(), --llm tier: LLM-extract claims from the PR thread. Returns number of claims…, Recall scoring: PR vocabulary vs manifest-selected artifacts., Fresh harness + docs captured from the repo clone + PR thread as raw. (+3 more)

### Community 20 - "Real-Repo Evals"
Cohesion: 0.26
Nodes (11): capture_docs(), entity_index_stats(), ingest_claim(), main(), manifest_stats(), LLM claim extraction for one doc. Returns parsed claims count., Graphify tier: run the AST entity index against the connected repo (by name,…, Copy the harness into a fresh fabric with integrations enabled. (+3 more)

### Community 21 - "Always-On Docs"
Cohesion: 0.53
Nodes (8): _block_text(), _has_marker(), install(), main(), Path, status(), _target(), uninstall()

## Knowledge Gaps
- **11 isolated node(s):** `Behavior Evaluations`, `wf context`, `wf lint`, `Common Frontmatter Fields`, `OKF Lifecycle Status (draft stable deprecated)` (+6 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 203 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_config()` connect `Config & Local Models` to `Golden Eval Harness`, `Entity Index`, `Actors & Eval Policy`, `Lint & Config Validation`, `Project Bootstrap`, `Ingest & Synthesis`, `Graphify Integration`, `Task Context`, `Git Hooks`, `Domain Proposal`?**
  _High betweenness centrality (0.242) - this node is a cross-community bridge._
- **Why does `get_llm_config()` connect `Behavior Evals` to `Config & Local Models`, `Golden Eval Harness`, `Actors & Eval Policy`, `Ingest & Synthesis`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `actor()` connect `Actors & Eval Policy` to `Config & Local Models`, `Golden Eval Harness`?**
  _High betweenness centrality (0.019) - this node is a cross-community bridge._
- **What connects `Behavior Evaluations`, `wf context`, `wf lint` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Config & Local Models` be split into smaller, more focused modules?**
  _Cohesion score 0.0647307924984876 - nodes in this community are weakly interconnected._
- **Should `Golden Eval Harness` be split into smaller, more focused modules?**
  _Cohesion score 0.0611764705882353 - nodes in this community are weakly interconnected._
- **Should `Entity Index` be split into smaller, more focused modules?**
  _Cohesion score 0.07053140096618357 - nodes in this community are weakly interconnected._