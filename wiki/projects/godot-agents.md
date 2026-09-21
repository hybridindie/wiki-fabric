---
type: index
title: "godot-agents: What We Learned"
review_after: 2027-03-20
---

# godot-agents: Project Retrospective

`godot-agents` is the orchestrator and client half of a two-repository system for agent-driven Godot development. It does not talk to the Godot editor directly — it depends on `godot-mcp` for the editor bridge and the underlying logic [1]. That split is the defining fact of the project. `godot-agents` owns the loop, the evaluation harness, and the promotion gates; `godot-mcp` owns the tool surface. The client is where agent behavior is actually shaped: retries, verification, scoring, and the decision to promote one configuration over another all live here.

## What was built

The client mirrors the server's tool names and parameter keys exactly, so the two repositories are bound by an explicit contract rather than a shared library [3]. Transport defaults to `stdio`, which requires the `godot-mcp` CLI to be resolvable through environment variables or an installation path [5][12]; HTTP transport defaults to port 9090 [13].

The core loop is build/verify/fix, capped by a default of 3 retries and a recursion limit of 50 [7]. The verifier can be instructed to run the project's existing GUT test suite after a code change [18]. On first contact the system performs a deterministic structural scan to populate the `project_map`; subsequent runs skip that scan [10].

Evaluation is a separate pipeline: data flows from the dataset through the runner to the MLflow dashboard [19], tracking `pass_rate`, `avg_latency`, and `total_cost` [20]. Results can be grouped by `genres` or `domains` and measured with `verification_passed` or `partial_credit` [21], and a scatter plot compares `partial_credit` against `native_authoring_ratio` [22]. A CLI comparison script diffs current against baseline runs and exits with code 1 when regressions are detected [23]. The leaderboard ranks models on `gle_score`, `pass_rate`, `native_authoring_ratio`, and a derived `capability_per_cost` score [24].

## Constraints discovered

The tightest constraint is coupling: the system requires the exact surface structure of a specific `godot-mcp` server implementation [2]. For `godot-mcp` 2026.08.31b4 and later, toolset enablement is server-global and persists across client connections [4] — the client cannot scope toolsets per session.

Configuration is environment-variable-only; there is no configuration file [11]. Several capabilities are off by default and require explicit opt-in: web search for the retrieval band [14], and the experimental fluid executor [15]. Tracing and evaluation logging activate only when the MLflow tracking URI is set [16]. S3 artifact storage requires `boto3` and AWS credentials [17].

Evaluation has its own hard edges. Leaderboard comparisons are only valid when all result files share the same frozen benchmark version [25]. The promotion gate requires a judge model alignment score of 0.7 or higher to be considered authoritative [27]. Mock mode records detailed metrics but explicitly excludes the final verdict on whether the feature successfully built in Godot [28]; the authoritative pass-rate comes only from live mode, which requires a Godot editor, the `godot_mcp` addon, and a running `godot-mcp` server [29].

## Patterns that emerged

Three patterns carried most of the weight. First, contract mirroring: by copying tool names and parameter keys exactly, the client and server stay in sync without a shared schema artifact [3]. Second, one-shot deterministic scanning: the `project_map` is built once and reused, keeping repeated runs cheap and stable [10]. Third, separating failure classes: transport failures get exponential backoff and a circuit breaker, while tool-level errors are treated as deterministic and non-retriable [9]. Retrying a deterministic tool error would only burn budget.

A fourth pattern is the mock/live split. Mock mode gives cheap iteration with detailed metrics but no build verdict [28]; live mode gives the authoritative signal at the cost of real infrastructure [29]. Promotion then depends on comparison gates: a fluid arm is promotable over the champion baseline only if it is non-regressive and improves [30].

## Decisions made

`stdio` was chosen as the default transport, with HTTP on 9090 as the alternative [5][12][13]. Run durability defaults to a non-persistent in-process `MemorySaver`, with `sqlite` or `postgres` available for runs that must survive restarts [8]. Configuration was pushed entirely into environment variables rather than a file [11]. Web search and the fluid executor were both left disabled by default, requiring explicit opt-in [14][15]. Since 2026.08.31b4, the client prefers the structured payload `godot-mcp` emits for normalization over parsing text [6]. Retry behavior was capped at 3 retries with a recursion limit of 50 to bound runaway loops [7].

## Current state

The evidence set for this retrospective does not record a claim count or a graph status, so neither is asserted here. What is clearly still open: the fluid executor remains experimental and disabled by default [15], web search remains opt-in [14], and default run durability is still non-persistent [8]. Mock mode still cannot answer whether a feature actually built in Godot [28], so any authoritative pass-rate claim depends on live infrastructure [29]. Arm D — fluid execution, challenger prompt, and test-gate enabled — exists as a configuration [26], but promotion still runs through the non-regression and improvement gates [30] and the 0.7 judge alignment threshold [27].

This project contributed four promoted patterns: [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]]. No related topic articles were recorded in the evidence set, so mechanics references here are limited to those promoted patterns.

---

_Generated from the evidence fabric on 2026-09-21. 96 current claim(s) from 96 analyzed sources._
