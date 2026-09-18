---
type: experience-event
description: "<One-line summary for index and search>"
project: "<your-project-slug>"
domain: [agent-systems]
observed_problem: "<What problem did you observe? One paragraph.>"
intervention: "<What did you do? One paragraph.>"
conditions:
  task_class: "<task-class>"
  runtime: "<runtime/env>"
  tool: "<tool/framework>"
outcomes:
  metric_name:
    before: "<value>"
    after: "<value>"
evidence:
  - "[[src-<source-slug>]]"
confidence: high
tags: [<tag1>, <tag2>]
created: "{{date:YYYY-MM-DD}}"
updated: "{{date:YYYY-MM-DD}}"
---

# Experience Event: <brief-title>

## Observed Problem

<Detailed description of what went wrong or what was observed. Include metrics, errors, symptoms.>

## Intervention

<What you did to fix/improve it. Specific steps, code changes, config changes.>

## Conditions

| Field | Value |
|-------|-------|
| Task Class | `{{task_class}}` |
| Runtime | `{{runtime}}` |
| Tool/Framework | `{{tool}}` |

## Outcomes

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| <metric> | <before> | <after> | <delta> |

## Evidence

- Source: [[src-<source-slug>]]
- Related claims: [[claim-<claim-slug>]]

## Confidence

`high` — based on direct measurement / observation.

---

*Faithful record — no inference beyond observed data.*