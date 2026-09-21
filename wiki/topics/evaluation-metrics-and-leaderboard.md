---
type: wiki-article
title: "Evaluation Metrics and Leaderboard"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Evaluation Metrics and Leaderboard

This article covers the evaluation metrics and leaderboard used for Godot's Last Exam (GLE). It describes the task tiers, the metrics collected during runs, the two-axis scoring model, the leaderboard ranking, and the saturation calibration checks. These components matter because they provide a repeatable way to compare models [3], measure operational cost [1], and determine whether the GLE set still contains tasks that strong models cannot fully solve [13].

## Task Tiers and Evaluation Runs

Tasks are categorized into two tiers: `smoke` and `bench`. The `smoke` tier is a fast, deterministic mock, while the `bench` tier uses the live Godot's Last Exam set [9]. The `smoke` tier provides a fast, deterministic mock gate used during Continuous Integration (CI) runs [5]. Running the evaluation with `--repeat N` allows the runner to aggregate metrics including mean ± std pass-rate and `tool_f1` [7].

## Core Metrics

During evaluation runs, the system tracks specific metrics including `pass_rate`, `avg_latency`, and `total_cost` [1]. The evaluation also reports `tool_precision`, `tool_recall`, `tool_f1`, and `tool_param_accuracy` [8]. Tool Precision, Recall, and F1 score measure the agreement between the recorded MCP call history and the expected tools at the tool-name level [12]. Prompt and Model Cost is an estimation of token pricing based on prompt and response tokens and their respective rates [11].

## Two-Axis Evaluation

Every GLE result is evaluated along two axes: Correctness (`partial_credit`) and Approach (`native_authoring_ratio`) [4]. A scatter plot allows comparing `partial_credit` (correctness) against `native_authoring_ratio` (approach) [2]. The Native Authoring Ratio is a continuous signal that distinguishes between code

---

_Citations link to claims in evidence/claims/. Generated on 2026-09-21._
