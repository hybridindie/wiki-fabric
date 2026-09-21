---
type: index
title: "alpaca-agents: What We Learned"
review_after: 2027-03-20
---

# alpaca-agents: What We Learned

## Current state

711 verified claim(s) from 711 analyzed sources.

## Key findings

- Alpaca Agents is a multi-agent AI trading system for Alpaca Markets that operates in paper trading mode only." [1]
- The required environment variables for the project are OPENROUTER_API_KEY, ALPACA_API_KEY, and ALPACA_SECRET_KEY." [2]
- The configuration source of truth is data/config/settings.yaml, which must always be loaded via load_config() from src.config.settings." [3]
- All agents must mutate fields on the shared TradingState object rather than reassigning the whole object, as reassignment is the most common [4]
- The module dependency direction is src/models/ → src/agents/ / src/tools/ / src/services/ → src/orchestration/ → src/workers/, with no rever [5]
- src/services/ must not import from agents or orchestration, a constraint enforced by tests/unit/architecture/test_import_boundaries.py." [6]
- The project's test coverage target is approximately 58–59% for the overall project and 70% or higher for new code." [7]
- The Black formatter line length is set to 100 characters, not the default 88." [8]
- The minimum patched versions to prevent LangGraph Checkpoint RCE are langgraph>=0.4.8 and langgraph-checkpoint-postgres>=2.1.2, and these fl [9]
- No pull request is merged without a pr-agent review, which is enforced as a hard gate requiring the review to be received, CI to be green, p [10]
- src/api/ must not import src/orchestration/ directly, with the only allowlisted exception being bridge.py for the pre-existing workflow stre [11]
- Alpaca Agents is a multi-agent AI trading system for Alpaca Markets built on LangGraph." [12]
- The system's current status is Production-Ready for Paper Trading." [13]
- The agent pipeline flows from Research → Market Data → Technical and Sentiment into Risk → Portfolio → Execution." [14]
- All agents mutate a shared TradingState object defined in src/models/state.py rather than reassigning the whole object." [15]

