---
type: index
title: "alpaca-agents: What We Learned"
review_after: 2027-03-20
---

# Alpaca Agents: A Retrospective

Alpaca Agents is a multi-agent AI trading system built for Alpaca Markets paper trading. It runs a LangGraph-based workflow in which specialized agents communicate through a shared state object, and it exists to answer a narrow but hard question: can a committee of LLM agents produce defensible trading analysis under real market constraints — look-ahead bias, token budgets, confidence gating — without risking capital? Because it targets paper trading only, the project can be aggressive about agent topology and memory design while staying honest about what has and hasn't been proven.

## What was built

The core is a LangGraph workflow over a shared `TradingState`. Agents mutate fields on that object rather than reassigning it, which keeps concurrent writers from clobbering each other's work. Four agent patterns are supported: ReAct, Direct, Hybrid, and Pure LLM.

The topology is a fan-out. A Regime Agent classifies conditions, then Technical and Sentiment Agents run in parallel. That parallelism is the single largest latency win in the system — a 30–40% reduction in workflow time, saving 5–10 seconds per run. A Synthesizer debate is triggered only when confidence lands in the 60–95% band, so deliberation is spent where uncertainty is real. Fourteen investor personas are available for consultation during that deliberation.

Memory is backed by PostgreSQL with the pgvector extension. Analyses are embedded with `all-MiniLM-L6-v2` into 384-dimensional vectors; retrieval defaults to the top 5 similar cases at a cosine similarity threshold of 0.75. Memory operations are non-blocking so they never sit on the critical path of trading logic. The database connection uses asynchronous SQLAlchemy with tuned pooling. Agent performance metrics — analysis, outcomes, and agent metadata — are tracked in the same store, and scheduled maintenance handles retention cleanup and pgvector index optimization.

Operationally: market data quotes at a 60-second interval, the autonomous trader scans every 15 minutes, and services are exposed locally on Web 5173, API 8000, and DB 5432. Each workflow carries a 50,000-token budget with a warning at 40,000.

## Constraints discovered

Several constraints turned out to be structural rather than incidental.

Dependency direction is enforced: modules flow unidirectionally from `src/models/` to `src/workers/`, and `src/services/` is barred from importing `agents` or `orchestration`. The API layer is similarly restricted — `src/api/` may not import `src/orchestration/`, with `bridge.py` as the sole exception.

Time handling is a correctness constraint, not a style preference. Inside `src/agents/` and `src/orchestration/`, analysis time must be read from `state.as_of_date` or an injected `as_of` value, never from `datetime.now()`. Wall-clock reads would introduce look-ahead bias and silently invalidate backtests.

Version floors are pinned to Spec §11.3: `langgraph` at 0.4.8 or higher and `langgraph-checkpoint-postgres` at 2.1.2 or higher. Coverage sits around 58–59% overall, with new code required to clear 70%. CI runs `uv run pytest tests/unit/` with flags excluding slow, integration, and performance tests. Merging a PR requires a review from the pr-agent — a hard gate, not advisory. Calibration adjustments apply only when the Wilson score confidence interval reaches 80% or higher.

## Patterns that emerged

The recurring solution shape is *constrain the seam, not the agent*. Shared mutable state gives agents a coordination primitive without coupling them to each other. Unidirectional imports keep services from reaching into orchestration. Injected `as_of` values keep time honest. Non-blocking memory keeps retrieval off the hot path. Confidence-gated debate keeps token spend proportional to uncertainty.

Gate thresholds show up repeatedly — pr-agent review, coverage floors, the Wilson CI bar — and are collected under [[gate-thresholds-and-error-handling]]. Retention and index maintenance follow a scheduled-work pattern documented in [[data-retention-and-archival-policy]]. Outcome measurement is split across [[outcome-tracking]] and [[price-prediction-outcome-tracking]]. Tension between shared state and duplicated logic is captured in [[dry-principle-violation]], and regime-conditioned sizing in [[market-regime-driven-position-sizing]].

Four promoted patterns carry load-bearing rules out of this project: [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]].

## Decisions made

Paper trading only — no live capital, which keeps the risk envelope closed while agent behavior is still being characterized. LangGraph as the orchestration substrate, with version floors pinned rather than floating. Postgres plus pgvector instead of a separate vector store, so state, metrics, and embeddings live in one database. `all-MiniLM-L6-v2` for embeddings — local, 384 dimensions, no external embedding dependency. Field mutation over reassignment. Injected time over wall clock. `bridge.py` as the single sanctioned API-to-orchestration seam. pr-agent as a hard merge gate. A token budget with an early warning at 40,000 rather than a silent ceiling at 50,000.

## Current state

The evidence set for this retrospective does not record a claims count or a graph status, so those numbers aren't asserted here. What remains open is a set of standing obligations rather than unresolved defects: holding the coverage floor while new code clears 70%, keeping the pr-agent gate meaningful, maintaining the Wilson CI threshold for calibration, running retention cleanup and pgvector index optimization on schedule, and watching token usage against the 40,000 warning line. The system is scoped to paper trading; nothing in the evidence indicates live deployment.

---

_Generated from the evidence fabric on 2026-09-21. 467 current claim(s) from 467 analyzed sources._
