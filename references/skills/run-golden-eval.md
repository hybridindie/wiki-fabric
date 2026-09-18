---
type: skill
name: run-golden-eval
description: "Run the golden-corpus claim-recall eval and emit a machine-checkable receipt."
tags: [eval, executor]
---

# Run: golden corpus eval

1. `set -a; source .env.wiki-fabric 2>/dev/null; set +a`
2. `WIKI_LLM_MODEL=<compiler-model> python3 scripts/eval.py`
3. Receipt = the `## [date] / **eval | ...**` registry/log.md block + stdout metrics:
   `{model, recall, locator_rate, quote_rate, verdict: PASS|FAIL}`

The receipt is a runtime artifact — never stored in the bundle (OKF §10).
