---
type: index
title: "alpaca-agents: What We Learned"
review_after: 2027-03-20
---

# alpaca-agents: What We Learned

## Current state

467 verified claim(s) from 467 analyzed sources.

## Key findings

- The system is a multi-agent AI trading system designed for Alpaca Markets paper trading." [1]
- Three specific API keys are required to configure the environment." [2]
- All agents must operate on a shared `TradingState` object by mutating its fields rather than reassigning the entire object." [3]
- The module dependencies must flow unidirectionally from `src/models/` to `src/workers/`, with `src/services/` being restricted from importin [4]
- CI runs unit tests using the command `uv run pytest tests/unit/` with specific flags to exclude slow, integration, and performance tests." [5]
- The project requires approximately 58–59% coverage, with new code requiring 70%+ coverage." [6]
- To ensure compliance with Spec §11.3, `langgraph` and `langgraph-checkpoint-postgres` must be at least versions 0.4.8 and 2.1.2, respectivel [7]
- Inside `src/agents/` and `src/orchestration/`, analysis time must be read from `state.as_of_date` or an injected `as_of` value, never from ` [8]
- The `src/api/` module must not directly import `src/orchestration/`, with `bridge.py` being the only allowed exception." [9]
- Merging a Pull Request requires a review from the pr-agent, which serves as a hard gate." [10]
- All agents mutate a shared TradingState object, requiring field mutation rather than full object reassignment." [11]
- The system supports four agent patterns: ReAct, Direct, Hybrid, and Pure LLM." [12]
- The Synthesizer debate is triggered when the system reaches 60–95% confidence." [13]
- The maximum token budget per workflow is 50,000." [14]
- The system issues a warning when the token usage reaches 40,000." [15]

