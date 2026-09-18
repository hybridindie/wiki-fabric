---
type: experiment
description: "<One-line summary for index and search>"
tags: []
id: "exp-<slug>"
title: "<Experiment Title>"
status: planned
hypothesis: "<One-sentence hypothesis>"
question: "<Research question>"
repo: "<github:org/repo>"
commit: "<sha>"
environment:
  model: "<model>"
  inference_server: "<server>"
  gpu: "<gpu>"
  temperature: 0
metrics:
  - <metric1>
  - <metric2>
related_claims:
  - "[[claim-<claim-slug-1>]]"
  - "[[claim-<claim-slug-2>]]"
raw_artifacts:
  - "[[src-<source-slug>]]"
results: []
created: "{{date:YYYY-MM-DD}}"
updated: "{{date:YYYY-MM-DD}}"
---

# Experiment: <Experiment Title>

## Hypothesis

<One-sentence hypothesis: what we expect to observe.>

## Baseline Pairing Verifier Protocol

### Baseline (Reference Implementation)
- **Implementation**: <sync path / reference impl / contract test>
- **Determinism**: <how determinism is ensured>
- **Scope**: <what state is compared>

### Mutation (Agent's Implementation)
- **Implementation**: <async path / agent's mutation / optimized path>
- **Scope**: <what mutations are applied>

### Parity Check
- **Comparison**: <exact diff / structural equivalence / semantic equivalence>
- **Tolerance**: <exact match / within tolerance / semantic equivalence>
- **Scope**: <what state is compared>

### Stress Test
- **Concurrency**: <number of concurrent operations>
- **Duration**: <duration or iterations>
- **Load Profile**: <steady / burst / ramp>
- **Failure Modes Observed**: <mismatches, crashes, timeouts>

## Metrics

| Metric | Baseline | Mutation | Delta | Pass/Fail |
|--------|----------|----------|-------|-----------|
| <metric1> | <val> | <val> | <delta> | <pass/fail> |
| <metric2> | <val> | <val> | <delta> | <pass/fail> |

## Results

| Run | Baseline State | Mutated State | Parity | Notes |
|-----|----------------|---------------|--------|-------|
| 1 | <state> | <state> | pass/fail | <notes> |
| 2 | <state> | <state> | pass/fail | <notes> |
| ... | ... | ... | ... | ... |

## Stress Test Results

| Concurrency | Duration | Baseline State | Mutated State | Parity | Mismatches | Errors |
|-------------|----------|----------------|---------------|--------|------------|--------|
| <N> | <t> | <state> | <state> | pass/fail | <N> | <errors> |

## Analysis

### Parity Result
- **At rest**: pass / fail
- **Under stress**: pass / fail

### Mismatch Analysis
- **Count**: <N> mismatches
- **Type**: <type of mismatch>
- **Root Cause**: <root cause if known>

### Stress Test Verdict
- **Verifier holds under stress**: yes / no
- **If no**: <what failed, what needs fixing>

## Conclusion

- **Hypothesis**: supported / refuted / inconclusive
- **Verifier holds under stress**: yes / no
- **Next Steps**: <what to do next>

## Artifacts

- Baseline snapshot: [[src-<slug>]]
- Mutated snapshot: [[src-<slug>]]
- Diff: [[src-<slug>]]
- Stress test logs: [[src-<slug>]]

## Related

- [[pattern-<pattern-slug>]]
- [[skill-<skill-slug>]]
- [[claim-<claim-slug>]]