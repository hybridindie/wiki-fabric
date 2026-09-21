---
type: index
title: "godot-agents: What We Learned"
review_after: 2027-03-20
---

# godot-agents — Project Retrospective

## Overview

`godot-agents` is the orchestrator and client half of a two-repository system. It does not talk to the Godot editor directly; it depends on `godot-mcp` for the actual editor bridge and the logic behind each tool call [1]. That division is the whole point of the project: the agent loop, the evaluation harness, and the promotion machinery live here, while the editor-facing surface lives there. It matters because it is the piece that turns a model into something that can build, verify, and fix a Godot feature under measurable conditions — and because the seam between the two repositories is narrow enough to be described exactly.

## What was built

The client mirrors the server's tool names and parameter keys exactly, so the client implementation functions as a contract between the two repositories [3]. Transport defaults to `stdio`, which means the `godot-mcp` CLI has to be resolvable through environment variables or an installation path [5][12]; HTTP transport is available with a default port of 9090 [13]. Since `godot-mcp` 2026.08.31b4, the server emits a structured payload, and the client prefers that payload for normalization rather than parsing text [6].

The agent loop is a build/verify/fix cycle capped by a default of 3 retries and a recursion limit of 50 [7]. On first contact the system performs a deterministic structural scan to populate the `project_map`; later runs skip the scan [10]. The verifier can be instructed to run the project's existing GUT test suite after a code change [18].

Around the loop sits an evaluation stack: data flows from the dataset through the runner to the MLflow dashboard [19], tracking `pass_rate`, `avg_latency`, and `total_cost` [20]. Success rates can be grouped by `genres` or `domains` and measured with `verification_passed` or `partial_credit` [21], and a scatter plot compares `partial_credit` against `native_authoring_ratio` [22]. A CLI comparison script diffs current against baseline runs and exits with code 1 when regressions are detected [23]. The leaderboard ranks models on `gle_score`, `pass_rate`, `native_authoring_ratio`, and a derived `capability_per_cost` score [24].

## Constraints discovered

The coupling is the first hard limit: the system requires the exact surface structure of a specific `godot-mcp` server implementation [2]. Toolset enablement is server-global and persists across client connections for 2026.08.31b4 and later [4], so enablement is not a per-client decision.

Configuration is environment-variable-only; there is no configuration file [11]. Several capabilities are off until explicitly turned on: web search, which gates the retrieval band [14], and the experimental fluid executor, which gates the fluid loop [15]. MLflow tracing and evaluation logging activate only when the tracking URI is set [16]. S3 artifact storage requires `boto3` and AWS credentials [17].

Evaluation has its own constraints. Leaderboard comparisons are only valid when all result files share the same frozen benchmark version [25]. The promotion gate requires a judge model alignment score of 0.7 or higher before a result is considered authoritative [27], and a fluid arm can only be promoted over the champion baseline if it is non-regressive and improves under predefined comparison gates [30]. Mock mode records detailed metrics but explicitly excludes the final verdict on whether the feature actually built in Godot [28]; the authoritative pass rate comes only from live mode, which needs a Godot editor, the `godot_mcp` addon, and a running godot-mcp server [29].

## Patterns that emerged

Three patterns recur. First, contract mirroring: rather than abstracting the server surface, the client reproduces it exactly, which makes drift detectable but makes the two repositories move together [3]. Second, a deterministic one-time scan that caches into `project_map`, trading freshness for repeatability across runs [10]. Third, an explicit error taxonomy — transport failures are retried with exponential backoff behind a circuit breaker, while tool-level errors are treated as deterministic and non-retriable [9]. That split keeps the retry budget from being spent on failures that will not change.

The evaluation side settled into a pipeline shape: frozen benchmark, runner, dashboard, comparison gate, leaderboard [19][23][24][25]. Promotion is deliberately conservative — non-regression plus improvement, with a judge alignment threshold [27][30]. Arm D is the concrete configuration that exercises this: fluid execution, challenger prompt, and test-gate enabled [26].

These are the load-bearing rules this project contributed to: [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]].

## Decisions made

Defaulting to `stdio` keeps the common path free of network setup, at the cost of requiring the CLI to be discoverable [5][12]. Defaulting run durability to a non-persistent in-process `MemorySaver`, with `sqlite` or `postgres` as opt-in backends, keeps short runs cheap while leaving restart survival available [8]. Env-var-only configuration was chosen over a config file [11], which makes deployment uniform but pushes complexity into the environment. Web search and the fluid executor were both left off by default so the baseline stays deterministic and cheap [14][15]. The mock/live split was accepted knowingly: mock gives fast, detailed metrics without the final build verdict, and live is reserved for authoritative numbers [28][29].

## Current state

The evidence set does not record a claim count or a graph snapshot for this project, so the honest summary is about posture rather than totals. The default configuration is stdio transport, in-process memory durability, no web search, no fluid executor, no MLflow tracing, and mock-mode evaluation. Everything authoritative — the live pass rate, the promotion gate, the leaderboard — sits behind explicit opt-in and specific infrastructure [16][25][27][29]. The open edges are the ones the constraints imply: the exact-surface coupling to `godot-mcp` [2], server-global toolset enablement that a client cannot scope [4], and the requirement that comparisons share a frozen benchmark version before any ranking is meaningful [25].

---

_Generated from the evidence fabric on 2026-09-21. 96 current claim(s) from 96 analyzed sources._
