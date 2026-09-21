---
type: index
title: "alpaca-agents: What We Learned"
review_after: 2027-03-20
---

# Alpaca Agents: Retrospective

Alpaca Agents is a multi-agent AI trading system built for Alpaca Markets paper trading [1]. Its role in the knowledge fabric is as a reference implementation of a LangGraph-based workflow in which specialized agents communicate through a shared state object [28] — a shape that recurs across agentic systems, but rarely with this much operational scaffolding around it. It matters because the interesting problems here are not "can an LLM pick a stock" but the harder ones: keeping agents from looking into the future, keeping module boundaries from rotting, and keeping memory retrieval off the critical path of a live trading loop.

## What was built

The core is a LangGraph workflow [28] with four supported agent patterns: ReAct, Direct, Hybrid, and Pure LLM [12]. The Regime Agent feeds the Technical and Sentiment Agents, which run in parallel [29] — a change that cut workflow time by 30–40%, saving 5–10 seconds per run [30]. A Synthesizer debate is triggered when confidence lands in the 60–95% band [13], and 14 investor personas are available for deliberation consultation [19].

Around the workflow sits a memory and analytics layer: PostgreSQL with the pgvector extension stores and queries high-dimensional analysis embeddings [20]. Embeddings come from all-MiniLM-L6-v2 at 384 dimensions per analysis [23]. Retrieval defaults to the top 5 similar cases at a cosine similarity threshold of 0.75 [21]. The system tracks agent performance metrics — analysis, outcomes, and agent metadata — in the database [26], which is what makes [[outcome-tracking]] and [[price-prediction-outcome-tracking]] possible at all.

Operationally, the autonomous trader scans every 15 minutes [17] against a 60-second quote interval [16]. Services are exposed locally on Web 5173, API 8000, and DB 5432 [18]. Scheduled maintenance covers retention cleanup and pgvector index optimization [27], the mechanics of which live in [[data-retention-and-archival-policy]].

## Constraints discovered

Several hard limits shaped the design. Configuration requires three specific API keys [2]. Token spend is capped at 50,000 per workflow, with a warning at 40,000 [15] — a two-tier threshold that fits the general shape described in [[gate-thresholds-and-error-handling]].

The sharpest constraint is temporal. Inside `src/agents/` and `src/orchestration/`, analysis time must be read from `state.as_of_date` or an injected `as_of` value, never from `datetime.now()` [8]. This is a look-ahead bias guard, and it is absolute: any agent that reaches for wall-clock time silently invalidates its own backtest.

Module boundaries are equally strict. Dependencies flow unidirectionally from `src/models/` to `src/workers/`, and `src/services/` may not import `agents` or `orchestration` [4]. The `src/api/` module may not import `src/orchestration/` at all, with `bridge.py` as the single allowed exception [9]. That lone exception is exactly the kind of carve-out that later becomes a [[dry-principle-violation]] if it is not watched.

Version floors are pinned to spec: `langgraph` at 0.4.8 or higher and `langgraph-checkpoint-postgres` at 2.1.2 or higher, per Spec §11.3 [7].

## Patterns that emerged

Two patterns did most of the load-bearing work. First, all agents mutate a shared `TradingState` object by mutating its fields rather than reassigning the whole object [3][11]. This keeps concurrent branches — like the parallel Technical and Sentiment Agents [29] — from clobbering each other's writes.

Second, memory operations are non-blocking by design, so retrieval and embedding work never interferes with core trading logic [24]. Combined with asynchronous SQLAlchemy and tuned pooling parameters [25], this keeps the trading loop responsive while the memory layer does its slower work.

These are the kinds of rules that get promoted rather than rediscovered: [[pattern-cluster_1c9cac89]], [[pattern-cluster_6cb87c7c]], [[pattern-cluster_a0bba1b7]], and [[pattern-cluster_cf12208f]] all draw on this project's evidence.

## Decisions made

The parallelization of Technical and Sentiment Agents [29] was a deliberate latency trade: more concurrent state mutation in exchange for 5–10 seconds saved per workflow [30]. The shared-state mutation rule [3][11] is what made that trade safe.

Calibration adjustments are gated on a Wilson score confidence interval reaching 80% or higher [22] — a conservative choice that prefers under-adjusting to over-adjusting on thin evidence. The 60–95% Synthesizer debate band [13] is the same instinct applied to deliberation: don't spend tokens arguing when the answer is already clear, and don't pretend a coin flip is a consensus.

The `bridge.py` exception [9] was accepted rather than engineered away, which is a decision worth revisiting.

## Current state

The architecture is documented and the constraints are enforced: module direction [4], the API/orchestration boundary [9], the `as_of` rule [8], and the version floors [7]. CI runs unit tests via `uv run pytest tests/unit/` with flags excluding slow, integration, and performance tests [5]. Coverage sits at roughly 58–59%, with new code required to hit 70% or higher [6]. Merging a pull request requires a review from the pr-agent, which acts as a hard gate [10].

What remains open: the evidence base does not record a claims count or a graph status for this project, so neither is asserted here. The `bridge.py` exception [9] and the coverage gap between the 58–59% baseline and the 70% new-code bar [6] are the two items most likely to need attention.

---

_Generated from the evidence fabric on 2026-09-21. 467 current claim(s) from 467 analyzed sources._
