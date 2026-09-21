---
type: wiki-article
title: "RLConfig"
domain: [agent-systems]
review_after: 2027-01-19
---

# RLConfig

12 current claim(s) support this topic.

- Momentum uses PPO with a continuous action space of [-1, 1] scaled by max position size, where -1 is full short, 0 is flat, and +1 is full l [1]
- Mean Reversion uses DQN with a discrete action space of 5 actions: 0=hold, 1=buy_small, 2=buy_large, 3=sell_small, 4=sell_large." [2]
- The momentum training config specifies algorithm ppo, training_steps 100000, learning_rate 0.0003, batch_size 64, and validation_sharpe_thre [3]
- RLConfig defaults are algorithm ppo, action_space continuous, training_steps 100_000, learning_rate 0.0003, batch_size 64, gamma 0.99, and v [4]
- Ingestion exit codes for k3s Job.backoffLimit are: 0=success, 2=populate, 3=extract, 4=commit, 5=validate, 6=graph_validate (agent construct [5]
- The pipeline uses exit codes 0=success, 2=populate, 3=extract, 4=commit, 5=validate, and 64=usage error, mapped to k3s Job.backoffLimit." [6]

---

[1] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-003 — Momentum uses PPO with a continuous action space of [-1, 1] scaled by max positi
[2] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-004 — Mean Reversion uses DQN with a discrete action space of 5 actions: 0=hold, 1=buy
[3] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-008 — The momentum training config specifies algorithm ppo, training_steps 100000, lea
[4] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-009 — RLConfig defaults are algorithm ppo, action_space continuous, training_steps 100
[5] claim-nomokailist-nomokailist-agents-md-009 — Ingestion exit codes for k3s Job.backoffLimit are: 0=success, 2=populate, 3=extr
[6] claim-nomokailist-nomokailist-readme-md-007 — The pipeline uses exit codes 0=success, 2=populate, 3=extract, 4=commit, 5=valid

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
