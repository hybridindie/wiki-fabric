---
type: experience-event
title: "Redundant validation checks caused latency"
project: example-project
domain: [agent-systems]
observed_problem: "Three separate validation checks caused 150ms latency per request."
intervention: "Consolidated into one validator with circuit breaker."
conditions:
    task_class: refactoring
    runtime: python-3.12
outcomes:
    latency_ms: "150→23"
    error_rate: "unchanged"
evidence: []
confidence: medium
lineage: "example-project"
created: 2026-01-01
updated: 2026-01-01
---

# Example Experience Event

Shows the expected format: what problem was observed, what intervention was taken, and what the measurable outcomes were.