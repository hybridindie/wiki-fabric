---
type: wiki-article
title: "DRY Principle Violation"
domain: [agent-systems]
review_after: 2027-01-19
---

# DRY Principle Violation

8 current claim(s) support this topic.

- The `_init_llm()` method is duplicated identically (104 lines) in both `BaseReActAgent` and `BaseToolAgent`, violating the DRY principle." [1]
- The guide instructs adding `_init_llm()` to the `BaseAgent` class after the `__init__` method." [2]
- The guide instructs removing the entire `_init_llm()` method (lines 81-115) from `BaseReActAgent`." [3]
- The guide instructs removing the entire `_init_llm()` method (lines 72-106) from `BaseToolAgent`." [4]

---

[1] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-001 — The `_init_llm()` method is duplicated identically (104 lines) in both `BaseReAc
[2] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-005 — The guide instructs adding `_init_llm()` to the `BaseAgent` class after the `__i
[3] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-006 — The guide instructs removing the entire `_init_llm()` method (lines 81-115) from
[4] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-007 — The guide instructs removing the entire `_init_llm()` method (lines 72-106) from

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
