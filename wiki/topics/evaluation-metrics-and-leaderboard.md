---
type: wiki-article
title: "Evaluation Metrics and Leaderboard"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Evaluation Metrics and Leaderboard

32 current claim(s) support this topic.

- The system tracks specific metrics including `pass_rate`, `avg_latency`, and `total_cost` during evaluation runs." [1]
- A scatter plot allows comparing `partial_credit` (correctness) against `native_authoring_ratio` (approach)." [2]
- The leaderboard ranks models using metrics including `gle_score`, `pass_rate`, `native_authoring_ratio`, and a derived `capability_per_cost` [3]
- Every GLE result is evaluated along two axes: Correctness (partial_credit) and Approach (native_authoring_ratio)." [4]
- The 'smoke' tier provides a fast, deterministic mock gate used during Continuous Integration (CI) runs." [5]
- The leaderboard ranks models based on a capability-per-cost metric, defined as the GLE score per 1k tokens." [6]
- Running the evaluation with `--repeat N` allows the runner to aggregate metrics including mean ± std pass-rate and `tool_f1`." [7]
- The evaluation reports specific metrics including `tool_precision`, `tool_recall`, `tool_f1`, and `tool_param_accuracy`." [8]
- Tasks are categorized into two tiers: `smoke` and `bench`. The `smoke` tier is a fast, deterministic mock, while the `bench` tier uses the l [9]
- The Native Authoring Ratio is a continuous signal that distinguishes between code-first and tool-first agent behavior." [10]
- The Prompt and Model Cost is an estimation of token pricing based on prompt and response tokens and their respective rates." [11]
- Tool Precision, Recall, and F1 score measure the agreement between the recorded MCP call history and the expected tools at the tool-name lev [12]
- The calibration run demonstrates that the Godot's Last Exam set is not saturated by a strong model, meaning the model either fails or only p [13]
- The GLE set is considered NOT saturated if the strong model's overall GLE score is less than 100% and the pass rate is less than 100%." [14]
- For the GLE set to be considered NOT saturated, no task should show a `⚠️ retire?` flag when calibrated across two or more models." [15]
- If a strong model aces all tasks, this signals the need to author harder tasks or retire easy ones into the next version of the GLE." [16]

---

[1] claim-godot-agents-godot-agents-docs-eval-dashboard-md-001 — The system tracks specific metrics including `pass_rate`, `avg_latency`, and `to
[2] claim-godot-agents-godot-agents-docs-eval-dashboard-md-003 — A scatter plot allows comparing `partial_credit` (correctness) against `native_a
[3] claim-godot-agents-godot-agents-docs-eval-dashboard-md-005 — The leaderboard ranks models using metrics including `gle_score`, `pass_rate`, `
[4] claim-godot-agents-godot-agents-docs-eval-gle-md-003 — Every GLE result is evaluated along two axes: Correctness (partial_credit) and A
[5] claim-godot-agents-godot-agents-docs-eval-gle-md-006 — The 'smoke' tier provides a fast, deterministic mock gate used during Continuous
[6] claim-godot-agents-godot-agents-docs-eval-gle-md-009 — The leaderboard ranks models based on a capability-per-cost metric, defined as t
[7] claim-godot-agents-godot-agents-docs-eval-live-md-003 — Running the evaluation with `--repeat N` allows the runner to aggregate metrics
[8] claim-godot-agents-godot-agents-docs-eval-live-md-005 — The evaluation reports specific metrics including `tool_precision`, `tool_recall
[9] claim-godot-agents-godot-agents-docs-eval-live-md-007 — Tasks are categorized into two tiers: `smoke` and `bench`. The `smoke` tier is a
[10] claim-godot-agents-godot-agents-docs-eval-metrics-md-006 — The Native Authoring Ratio is a continuous signal that distinguishes between cod
[11] claim-godot-agents-godot-agents-docs-eval-metrics-md-007 — The Prompt and Model Cost is an estimation of token pricing based on prompt and
[12] claim-godot-agents-godot-agents-docs-eval-metrics-md-008 — Tool Precision, Recall, and F1 score measure the agreement between the recorded
[13] claim-godot-agents-godot-agents-docs-gle-calibration-md-000 — The calibration run demonstrates that the Godot's Last Exam set is not saturated
[14] claim-godot-agents-godot-agents-docs-gle-calibration-md-003 — The GLE set is considered NOT saturated if the strong model's overall GLE score
[15] claim-godot-agents-godot-agents-docs-gle-calibration-md-004 — For the GLE set to be considered NOT saturated, no task should show a `⚠️ retire
[16] claim-godot-agents-godot-agents-docs-gle-calibration-md-005 — If a strong model aces all tasks, this signals the need to author harder tasks o

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
