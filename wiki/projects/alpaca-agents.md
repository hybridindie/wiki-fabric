---
type: index
title: "alpaca-agents: What We Learned"
review_after: 2027-03-20
---

# Project Retrospective: alpaca-agents

alpaca-agents is a multi-agent AI trading system for Alpaca Markets paper trading. It uses a LangGraph-based workflow where specialized agents communicate through a shared state object. The system's role in the ecosystem is to provide a controlled environment for deliberation, market analysis, and outcome tracking before real capital is involved. It contributes mechanics to topics such as market regime sizing, outcome tracking, and data retention.

## Constraints Discovered

The project surfaced several hard constraints. Configuration requires three specific API keys. All agents must operate on a shared `TradingState` object by mutating fields rather than reassigning the entire object. Module dependencies must flow unidirectionally from `src/models/` to `src/workers/`, and `src/services/` is restricted from importing `agents` or `orchestration`. The `src/api/` module must not directly import `src/orchestration/`, with `bridge.py` as the only allowed exception. These boundaries prevent circular dependencies and keep the service layer independent.

Time discipline is strict: inside `src/agents/` and `src/orchestration/`, analysis time must be read from `state.as_of_date` or an injected `as_of` value, never from `datetime.now()`. This prevents look-ahead bias. Spec §11.3 requires `langgraph` and `langgraph-checkpoint-postgres` at minimum versions 0.4.8 and 2.1.2. Coverage targets are approximately 58–59% overall, with new code requiring 70%+ coverage. CI runs unit tests with `uv run pytest tests/unit/` and flags to exclude slow, integration, and performance tests. Merging a pull request requires a review from the pr-agent, which acts as a hard gate.

Operational limits include a maximum token budget of 50,000 per workflow, with a warning at 40,000. Market data quote interval is 60 seconds, and the autonomous trader scans every 15 minutes. Services are locally exposed on Web 5173, API 8000, and DB 5432. Memory retrieval defaults to top 5 similar cases with a cosine similarity threshold of 0.75. Calibration adjustments apply only if the Wilson score confidence interval reaches 80% or higher. Embeddings use `all-MiniLM-L6-v2`, producing 384-dimensional vectors.

## Patterns That Emerged

The dominant pattern is a LangGraph workflow with a shared state object. The Regime Agent feeds Technical and Sentiment Agents, which run in parallel. That parallelism reduces workflow time by 30–40%, saving 5–10 seconds. The system supports four agent patterns: ReAct, Direct, Hybrid, and Pure LLM. The Synthesizer debate triggers when confidence reaches 60–95%, balancing cost against rigor. Fourteen investor personas are available for deliberation consultation.

Memory operations use a non-blocking architecture so they do not interfere with core trading logic. PostgreSQL with the pgvector extension stores and queries high-dimensional analysis embeddings. The system tracks agent performance metrics—analysis, outcomes, and agent metadata—inside the database. Scheduled maintenance includes retention cleanup and pgvector index optimization. These mechanics connect to [[data-retention-and-archival-policy]], [[outcome-tracking]], and [[price-prediction-outcome-tracking]].

## Decisions Made

We chose field mutation over object reassignment to keep the shared state stable across agents. We enforced unidirectional dependencies to avoid service-layer coupling, which also reduces duplication and relates to [[dry-principle-violation]]. We injected `as_of` time rather than reading the clock, making backtests and live analysis consistent. We used async SQLAlchemy with tuned pooling for database performance. We set the memory retrieval threshold at 0.75 and top-5 retrieval to keep context relevant without flooding the prompt. We gated calibration at 80% Wilson confidence to avoid overfitting. We set token budgets and warning thresholds to control cost. We made pr-agent review a hard gate for merges. We triggered the Synthesizer debate only in the 60–95% confidence band. We scheduled retention and index maintenance to keep the vector store healthy. These decisions tie into [[gate-thresholds-and-error-handling]] and [[market-regime-driven-position-sizing]].

## Current State

The project has produced 30 claims in the knowledge fabric. The graph status is connected: claims link to six topic articles, including [[data-retention-and-archival-policy]], [[dry-principle-violation]], [[gate-thresholds-and-error-handling]], [[market-regime-driven-position-sizing]], [[outcome-tracking]], and [[price-prediction-outcome-tracking]]. The system is stable for paper trading, with clear boundaries, time discipline, and memory mechanics documented for future work.

---

_Generated from the evidence fabric on 2026-09-21. 467 current claim(s) from 467 analyzed sources._
