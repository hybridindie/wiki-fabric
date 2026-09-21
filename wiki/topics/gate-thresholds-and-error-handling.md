---
type: wiki-article
title: "Gate Thresholds and Error Handling"
domain: [agent-systems]
review_after: 2027-01-19
---

# Gate Thresholds and Error Handling

8 current claim(s) support this topic.

- The paper default for `cb_min_risk_gate_pass_rate` is 0.30, and the suggested live value is higher." [1]
- promote_prompt_to_production raises PromotionGateError and leaves @production untouched (fail closed) if structure mean < 0.95, risk consist [2]
- promote_prompt_to_staging raises ShadowGateError and leaves @staging untouched if agreement_rate is below the eval_gate default of 0.90." [3]
- Gate thresholds live in settings.yaml under eval_gate (structure_min_mean, risk_gate_consistency_min, min_samples), while the shadow floor l [4]

---

[1] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-009 — The paper default for `cb_min_risk_gate_pass_rate` is 0.30, and the suggested li
[2] claim-alpaca-agents-alpaca-agents-docs-guides-prompt-promotion-runbook-md-003 — promote_prompt_to_production raises PromotionGateError and leaves @production un
[3] claim-alpaca-agents-alpaca-agents-docs-guides-prompt-promotion-runbook-md-004 — promote_prompt_to_staging raises ShadowGateError and leaves @staging untouched i
[4] claim-alpaca-agents-alpaca-agents-docs-guides-prompt-promotion-runbook-md-007 — Gate thresholds live in settings.yaml under eval_gate (structure_min_mean, risk_

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
