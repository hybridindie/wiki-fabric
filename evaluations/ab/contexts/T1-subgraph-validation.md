# Context Manifest

- **Task:** workflow validation walk nested subgraph node maps: prompts, dangerous nodes, output node inside subgraph
- **Project:** comfyui-mcp
- **Compiled:** deterministic selection (0 tokens) — every item carries a reason

## Code navigation (graphify)

Symbols matching the task, ranked by file — open these first:

### comfyui-mcp (480 symbol matches)

- `tests/test_tools_generation.py` — 42 matching symbols
- `tests/test_workflow_templates.py` — 32 matching symbols
- `tests/test_workflow_operations.py` — 28 matching symbols
- `tests/test_tools_workflow.py` — 28 matching symbols
- `tests/test_tools_nodes.py` — 28 matching symbols

### nomokailist (1096 symbol matches)

- `backend/tests/unit/test_data_validation_service.py` — 89 matching symbols
- `backend/tests/contract/test_data_validation.py` — 41 matching symbols
- `backend/tests/unit/test_recommendation_agent.py` — 40 matching symbols
- `backend/tests/unit/agents/test_unified_fetch_node.py` — 35 matching symbols
- `backend/tests/unit/test_validators.py` — 30 matching symbols

### alpaca-agents (690 symbol matches)

- `tests/unit/agents/prompts/test_technical_prompt_builder.py` — 43 matching symbols
- `tests/unit/test_trading_workflow.py` — 36 matching symbols
- `tests/unit/test_approval_workflow.py` — 27 matching symbols
- `tests/unit/test_config_validation.py` — 25 matching symbols
- `_archived/test_react_structured_output.py` — 18 matching symbols

### godot-agents (612 symbol matches)

- `src/godot_agent/nodes/verifier/native_readback.py` — 95 matching symbols
- `src/godot_agent/nodes/planner.py` — 39 matching symbols
- `tests/nodes/test_knowledge_query.py` — 37 matching symbols
- `tests/test_fluid_executor_node.py` — 32 matching symbols
- `src/godot_agent/nodes/fluid_executor.py` — 26 matching symbols

### godot-mcp (144 symbol matches)

- `mcp_server/prompts/prompts.py` — 21 matching symbols
- `mcp_server/prompts/completion.py` — 8 matching symbols
- `godot/addons/godot_mcp/handlers/node_parity.gd` — 7 matching symbols
- `mcp_server/tools/node_ops.py` — 7 matching symbols
- `mcp_server/models/inspection.py` — 6 matching symbols

## Selected

### Project (highest precedence)

- [[claim-comfyui-mcp-comfyui-mcp-agents-md-004]] — *task evidence (claim): dangerou, dangerous, nodes, workflow* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-agents-md-007]] — *task evidence (claim): nodes* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-changelog-md-001]] — *task evidence (claim): valida, validation, workflow* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-changelog-md-003]] — *task evidence (claim): nodes, prompt, prompts* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-changelog-md-004]] — *task evidence (claim): neste, nested, nodes, subgraph* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-changelog-md-005]] — *task evidence (claim): subgraph* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-contributing-md-007]] — *task evidence (claim): dangerou, dangerous* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-readme-md-002]] — *task evidence (claim): dangerou, dangerous, workflow* `trust: machine-confirmed`
- [[claim-comfyui-mcp-comfyui-mcp-readme-md-003]] — *task evidence (claim): nodes* `trust: machine-confirmed`
- [[claim-comfyui-mcp-git-issue-109-md-001]] — *task evidence (claim): nodes* `trust: machine-confirmed`
  *decided in: [[src-comfyui-mcp-git-issue-109-md]]*
- [[claim-comfyui-mcp-git-issue-109-md-002]] — *task evidence (claim): nodes* `trust: machine-confirmed`
  *decided in: [[src-comfyui-mcp-git-issue-109-md]]*
### Domain

- [[concept-0-28-suites-test]] — *domain match: walk*
- [[concept-agent]] — *domain match: output, workflow*
- [[concept-answers-architecture-backed-before]] — *domain match: workflow*
### Global

- [[concept-0-40s-95-analysis]] — *global match (concept): valida, validation*

## Excluded

- `domains/ontology.md` — not a context artifact (type: ontology)
- `evidence/insights/2026-09-08-insight-let-s-address-the-open-prs-on-this-repo-there-is-ci-failures.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-08-insight-read-the-file-users-johnd-local-share-opencode-tool-output-t.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-11-insight-research-only-task-no-code-writing-i-need-a-survey-of-how-hi.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-let-s-look-at-the-open-issues-and-prioritize-them-to-figure-.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-let-s-start-looking-at-other-voxel-shapes-to-support-just-re.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-research-only-task-no-code-writing-no-file-changes-just-repo.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-research-task-read-only-no-code-changes-in-users-johnd-devel.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-research-task-web-research-no-code-changes-topic-supporting-.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-web-research-task-no-code-changes-context-a-godot-voxel-engi.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-12-insight-web-research-task-no-code-changes-research-only-you-must-ret.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-16-insight-graphify-has-hooks-for-harnesses-like-claude-let-s-recreate-.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-23-insight-fix-mlflow-mcp-and-make-sure-that-graphify-and-context7-are-.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-23-insight-run-graphify-locally-with-the-bansai-model-i-have-locally.md` — not a context artifact (type: synthesis)
- `evidence/insights/2026-09-24-insight-in-the-repo-users-johnd-development-alpaca-agents-analyze-al.md` — not a context artifact (type: synthesis)
- ... and 4898 more

## Precedence

When artifacts conflict: project decisions override domain patterns,
domain patterns override global policies. Cite the artifact you followed.

