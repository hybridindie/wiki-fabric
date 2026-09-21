---
type: index
title: "godot-agents: What We Learned"
review_after: 2027-03-20
---

# godot-agents: Project Retrospective

`godot-agents` is the orchestrator and client half of a two-repository system for driving the Godot editor with an agent loop. It does not talk to Godot directly. The actual editor bridge and the tool logic live in `godot-mcp`; `godot-agents` depends on that repository and drives it. The split is deliberate but not loose: the client mirrors the server's tool names and parameter keys exactly, so the two repositories are bound by a contract rather than by a shared library. Any change to the server's surface is a breaking change for the client.

## Constraints discovered

The coupling to `godot-mcp` is the dominant constraint. The client requires the server's exact surface structure — tool names, parameter keys, payload shape — and there is no compatibility shim. Transport is stdio by default, which means the `godot-mcp` CLI must be resolvable through environment variables or an install path before anything runs; HTTP is available and defaults to port 9090. See [[mcp-transport]].

Configuration is entirely environment-driven. There is no config file, so every knob — transport, persistence backend, tracing, retrieval, fluid execution — is set at process start. That is simple to reason about but makes local experimentation awkward.

Several capabilities are off by default and require explicit opt-in: web search (the retrieval band), the experimental fluid executor, and MLflow tracing via the tracking URI. S3 artifact storage adds a hard dependency on `boto3` and AWS credentials. See [[toolset-enablement]] and [[run-durability]].

## Patterns that emerged

Retry semantics split cleanly in two. Transport failures are transient and get exponential backoff plus a circuit breaker. Tool-level errors are deterministic and are not retried — retrying them just burns budget. See [[retry-semantics]].

The build/verify/fix loop is bounded: 3 retries by default, recursion limit 50. Bounded loops made failures reproducible instead of open-ended.

State handling is asymmetric. Run durability defaults to an in-process `MemorySaver`, so restarts lose everything unless `sqlite` or `postgres` is configured. The project map behaves the opposite way: a deterministic structural scan runs on first contact and is skipped on subsequent runs, so the map is a cache that must be invalidated deliberately. See [[project-map]].

Payload handling improved once `godot-mcp` began emitting structured output (2026.08.31b4 and later). The client prefers the structured payload and normalizes from it rather than parsing text. Toolset enablement also became server-global in that version, persisting across client connections — a stateful behavior that clients must not assume they own.

## Decisions made

Evaluation was treated as a first-class pipeline rather than an afterthought. Data flows from dataset through runner to the MLflow dashboard, tracking `pass_rate`, `avg_latency`, and `total_cost`. Success is sliced by `genres` or `domains` against `verification_passed` and `partial_credit`, and a scatter plot compares `partial_credit` against `native_authoring_ratio` to separate correctness from approach. See [[evaluation-metrics]].

Comparison is gated. The CLI comparison script diffs current against baseline and exits 1 on regression. The leaderboard ranks on `gle_score`, `pass_rate`, `native_authoring_ratio`, and a derived `capability_per_cost` — but only across result files sharing the same frozen benchmark version. Promotion of a fluid arm over the champion requires non-regression plus improvement, and the judge model alignment score must be at least 0.7 to be authoritative. See [[promotion-gates]].

Mock mode was kept deliberately incomplete: it records metrics but withholds the final verdict on whether the feature built in Godot. Only live mode, which needs a Godot editor, the `godot_mcp` addon, and a running server, produces the authoritative pass rate. That keeps the cheap path from being mistaken for the real one.

## Current state

30 claims recorded, all linked into the fabric graph; the graph is connected with no orphaned claims. The verifier can be pointed at the project's existing GUT suite after a code change, which closes the loop between agent edits and the project's own tests.

---

_Generated from the evidence fabric on 2026-09-21. 96 current claim(s) from 96 analyzed sources._
