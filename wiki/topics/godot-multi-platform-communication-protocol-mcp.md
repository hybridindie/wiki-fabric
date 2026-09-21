---
type: wiki-article
title: "Godot Multi-Platform Communication Protocol (MCP)"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Godot Multi-Platform Communication Protocol (MCP)

2644 current claim(s) support this topic.

- Alpaca Agents is a multi-agent AI trading system for Alpaca Markets that operates in paper trading mode only." [1]
- The configuration source of truth is data/config/settings.yaml, which must always be loaded via load_config() from src.config.settings." [2]
- All agents must mutate fields on the shared TradingState object rather than reassigning the whole object, as reassignment is the most common [3]
- The module dependency direction is src/models/ → src/agents/ / src/tools/ / src/services/ → src/orchestration/ → src/workers/, with no rever [4]
- src/services/ must not import from agents or orchestration, a constraint enforced by tests/unit/architecture/test_import_boundaries.py." [5]
- The project's test coverage target is approximately 58–59% for the overall project and 70% or higher for new code." [6]
- src/api/ must not import src/orchestration/ directly, with the only allowlisted exception being bridge.py for the pre-existing workflow stre [7]
- Alpaca Agents is a multi-agent AI trading system for Alpaca Markets built on LangGraph." [8]
- The system's current status is Production-Ready for Paper Trading." [9]
- The agent pipeline flows from Research → Market Data → Technical and Sentiment into Risk → Portfolio → Execution." [10]
- All agents mutate a shared TradingState object defined in src/models/state.py rather than reassigning the whole object." [11]
- The deliberation system triggers a Bullish ↔ Bearish → Synthesizer debate at 60–95% confidence." [12]
- Expert Advisors consist of 14 investor personas used for deliberation consultation." [13]
- Docker services expose the Web UI on localhost:5173, the API on localhost:8000, and the database on localhost:5432." [14]
- The autonomous trader's minimum confidence threshold for execution is 80.0." [15]
- Live trading execution is disabled by default (TRADER_ENABLE_EXECUTION=false) and must be explicitly enabled." [16]
- The Agent Memory & Learning System provides persistent storage, similarity-based retrieval, and confidence calibration for trading agents." [17]
- The Memory Manager component is implemented in src/services/memory/manager.py." [18]
- Calibration adjustments are only applied when Wilson confidence is at least 80%." [19]
- The historical window for calibration is 30 days." [20]
- The Alpaca Agents trading system uses a LangGraph-based workflow with specialized agents that communicate through a shared state object." [21]
- The workflow adds edges from regime to technical and sentiment, and from both to a convergence node." [22]
- Parallel execution of technical and sentiment agents reduces workflow time by 30-40% (5-10 seconds saved)." [23]
- The backtest decision returns \"backtest\" when sentiment and technical signals conflict." [24]
- The deliberation subgraph is a modular subgraph for multi-agent debate." [25]
- The deliberation flow includes Bullish Researcher, Bearish Researcher, and Synthesizer, and produces an updated trade_recommendation." [26]
- The alpaca-agents system runs three LangGraph graphs (Research, Execution, Portfolio) that operate as a pipeline." [27]
- GLM-5.2 scores 62.1 on SWE-bench Pro, 81.0 on Terminal-Bench, and supports 1M context window." [28]
- The OrderExecutionAgent must use no LLM; Alpaca API calls must be mediated by deterministic rule-based Python only." [29]
- All three LangGraph graphs share a single PostgresSaver checkpointer instance for state persistence." [30]
- Version 2.1.0 of Alpaca Agents was released on 2026-07-11." [31]
- An `InvestmentCommitteeCoordinator` component enables multi-persona deliberation." [32]
- Multi-strategy orchestration comprises a strategy arbiter, capital allocator, and autonomy governor located in `src/orchestration/multi_stra [33]
- The MLflow Prompt Registry in `src/prompt_registry/` provides versioned prompts with A/B testing and agent fallback." [34]
- Version 2.0.0 of Alpaca Agents was released on 2025-10-14." [35]
- Bug #1 fixed a Risk Monitoring SQL column name mismatch by renaming `portfolio_beta` to `beta`." [36]
- Market Regime Detection (Feature 006) detects 6 market regimes: bull_trend, bear_trend, consolidation, high_volatility, low_volatility, and  [37]
- Market regime detection uses SPY as the market proxy with a 200-bar lookback." [38]
- The project's primary language is Python 3.10 or higher." [39]
- The database technology is PostgreSQL 14+ with TimescaleDB." [40]
- The LLM framework used is the OpenRouter API." [41]
- The trading API used is Alpaca Markets." [42]
- The news API used is Finnhub." [43]
- The web UI is built with React, FastAPI, and Plotly." [44]
- The Market Data Agent's purpose is technical analysis and chart pattern detection." [45]
- The Sentiment Agent's purpose is to analyze news sentiment and market impact." [46]
- The Backtest Agent's purpose is conditional backtesting for validation." [47]
- The Autonomous Trader's purpose is to orchestrate analysis and execute trades." [48]
- emit_deliberation_start accepts max_rounds and initial_confidence parameters." [49]
- emit_round_header accepts round_num and total_rounds parameters." [50]
- emit_bullish_argument accepts argument, confidence, and round_num parameters." [51]
- emit_bearish_argument accepts argument, confidence, and round_num parameters." [52]
- emit_disagreement_status accepts disagreement, round_num, and continuing parameters." [53]
- emit_consensus_reached accepts disagreement, round_num, and total_rounds parameters." [54]
- emit_synthesis accepts a synthesis string parameter." [55]
- DeliberationCoordinator accepts a chat_callback parameter." [56]
- LLMException handling calls callback.emit_error with error_message and round_num." [57]
- Deliberation triggers when initial confidence is between 60 and 95 inclusive." [58]
- The chat interface currently uses direct sequential agent calls with 5 agents, taking about 10-15 seconds and producing incomplete analysis. [59]
- The CLI currently uses the full LangGraph workflow with 11 agents, taking about 20-30 seconds and producing comprehensive analysis." [60]
- The chat interface bypasses the LangGraph workflow and is missing 6 critical agents." [61]
- The target state is for both paths to use the identical LangGraph workflow with optional UI streaming for chat." [62]
- The chat interface executes 5 agents: MarketDataAgent, TechnicalAgent, SentimentAgent, RiskAgent, and PortfolioAgent." [63]
- The CLI path executes 11 agents total." [64]
- Phase 2 created src/orchestration/workflow_streaming.py with a streaming wrapper." [65]
- Phase 3 made the chat execute all 11 agents: MarketData, Regime, Technical (parallel), Sentiment (parallel), Backtest (conditional), Risk, P [66]
- The chat interface supports token-by-token streaming responses that show agent thinking in real-time." [67]
- The /ask <agent> <question> command queries a specific agent." [68]
- The /debate <question> command triggers multi-agent deliberation." [69]
- The /ask command accepts agent names including market_data/data, technical/tech, sentiment/news, risk, portfolio/port, execution/exec, and r [70]
- Deliberation agents only appear in a response if confidence is between 60% and 95%." [71]
- The sentiment meter score gauge maps a -1 to +1 range onto 0-100." [72]
- The web UI is launched by running uvicorn on port 8000 and npm run dev for the web prefix." [73]
- Per-agent model selection lives in `llm_routing.assignments` in `data/config/settings.yaml`, mapping each agent to a provider and model." [74]
- Technical Agent's current model is `anthropic/claude-3-haiku`." [75]
- Cost-Optimized configuration costs ~$0.008-$0.012 per analysis (~1¢ per trade)." [76]
- Balanced configuration costs ~$0.015-$0.025 per analysis (~2¢ per trade)." [77]
- Premium configuration costs ~$0.04-$0.08 per analysis (~6¢ per trade)." [78]
- Phase 2 migration expects 20-30% speed improvement and 15% cost reduction." [79]
- Implementation requires setting shared sampling knobs under `models:` and per-agent provider/model under `llm_routing.assignments` in `data/ [80]
- For current stage (paper trading development), the recommendation is to use Balanced Configuration." [81]
- For live trading, the recommendation is to use Premium or Ultra-Premium Configuration." [82]
- The OutcomeScheduler is a background async scheduler that runs updates every N hours with a configurable interval." [83]
- Running the scheduler with `--interval 1` performs updates every hour." [84]
- The sentiment tools are located in src/tools/sentiment/." [85]
- There are 6 LangChain sentiment tools covering news sentiment, options flow, and aggregation." [86]
- All sentiment tools use the @tool decorator for LangChain integration." [87]
- All sentiment tools are async for non-blocking I/O." [88]
- fetch_news_articles fetches news articles from aggregated sources Alpaca and Finnhub." [89]
- fetch_news_articles has a default limit of 10 articles." [90]
- analyze_news_sentiment returns a sentiment score from -100 (bearish) to +100 (bullish)." [91]
- A call/put ratio greater than 1.5 is interpreted as bullish due to heavy call buying." [92]
- aggregate_sentiment_scores defaults to news weight 0.6, social weight 0.3, and flow weight 0.1." [93]
- detect_unusual_activity defaults to a magnitude threshold of 60.0 and an article count threshold of 15." [94]
- detect_unusual_activity assigns high severity when both magnitude and volume thresholds are exceeded." [95]
- The Alpaca Agents multi-agent trading system uses two distinct tool invocation patterns based on the nature of the analysis task." [96]
- ReAct pattern is used when the LLM should adaptively decide which tools to call and in what order based on data availability, asset type, an [97]
- Direct tool invocation is used when the workflow is deterministic and always follows the same steps, regardless of input data variations, as [98]
- The ReAct pattern's AgentExecutor is configured with max_iterations=15, handle_parsing_errors=True, max_execution_time=30.0, and early_stopp [99]
- TechnicalAgent uses the ReAct pattern for adaptive technical analysis." [100]
- SentimentAgent uses direct tool invocation for a deterministic sentiment workflow." [101]
- RiskAgent uses direct tool invocation for deterministic risk calculations." [102]
- PortfolioAgent uses direct tool invocation for deterministic signal aggregation." [103]
- The decision framework states that if the workflow adapts based on data availability, asset type, or market conditions, use ReAct Pattern; i [104]
- The ReAct pattern's typical execution time is 5-10 seconds." [105]
- Direct invocation's typical execution time is 1-3 seconds." [106]
- The Alpaca Agents system uses multiple agent patterns depending on the agent's responsibilities." [107]
- The document lists 14 total agents by pattern." [108]
- The BaseReActAgent pattern is used by two agents: TechnicalAgent and SentimentAgent." [109]
- The BaseToolAgent pattern is used by one agent: RiskAgent." [110]
- The Direct Tool Invocation pattern without a base class is used by three agents: MarketDataAgent, ExecutionAgent, and PortfolioAgent." [111]
- The Pure LLM Reasoning pattern without a base class is used by four agents: BullishResearcher, BearishResearcher, Synthesizer, and Backtesti [112]
- The Specialized pattern without a base class is used by four agents: RegimeAgent, OpportunityAgent, AnalysisRouterAgent, and ApprovalAgent." [113]
- RiskAgent migrated from BaseReActAgent to BaseToolAgent in Sprint 1." [114]
- The Hybrid pattern's base class is BaseToolAgent, which is new in Sprint 1." [115]
- The ReAct pattern uses 3-5 LLM calls per execution." [116]
- The main backtesting engine module is `src.backtest.engine.BacktestEngine`." [117]
- The backtesting engine recommends 1+ years of historical data validation." [118]
- The A/B Testing Framework compares two configurations statistically." [119]
- The A/B testing module is `src.backtest.ab_testing.ABTester`." [120]
- Walk-Forward Optimization optimizes parameters systematically without overfitting." [121]
- The walk-forward optimization module is `src.backtest.optimization.WalkForwardOptimizer`." [122]
- Monte Carlo Simulation assesses tail risk through bootstrap sampling." [123]
- The Monte Carlo simulation module is `src.backtest.monte_carlo.MonteCarloSimulator`." [124]
- Monte Carlo simulation supports bootstrap sampling with 1000+ scenarios." [125]
- The dashboard's default URL is http://localhost:5173." [126]
- The dashboard is built on a React frontend and FastAPI backend." [127]
- The dashboard provides real-time portfolio management, agent chat, risk monitoring, and comprehensive reporting capabilities." [128]
- The dashboard is launched with the command `uv run python main.py dashboard`." [129]
- Multi-agent mode uses sequential agent responses in the order Market Data, Technical, Sentiment, Risk, Portfolio." [130]
- The trade history limit is adjustable between 5 and 50 trades." [131]
- The auto-refresh interval slider ranges from 5 to 60 seconds." [132]
- The human-in-the-loop trade approval system requires checkpointing to be enabled." [133]
- Feature flags live in `data/config/settings.yaml`." [134]
- The four deliberation experiment flags default to false." [135]
- Each deliberation run records the enabled flags to `DeliberationData.active_experiments`." [136]
- The metrics endpoint is fetched via `curl \"http://localhost:8000/experiments/metrics?window_days=30\"`." [137]
- A flag can be toggled in `settings.yaml` via POST to `http://localhost:8000/experiments/flags` with JSON body `{\"experiment\":\"micro_swarm [138]
- The nightly report scheduler runs by default every 24 hours via `uv run python scripts/run_experiment_report_scheduler.py`." [139]
- Live trading is off by default and stays off until a human deliberately enables it." [140]
- Enabling live capital is a human decision requiring separate live credentials and explicit opt-in (`ALLOW_LIVE_TRADING=true`)." [141]
- Go-live requires 30+ paper trades completed with zero circuit-breaker trips." [142]
- Go-live requires shadow-eval agreement ≥ 85% across the last 30 replayed states." [143]
- Go-live requires all WP-6 eval scorer-gate thresholds passing on a ≥20-sample set." [144]
- Live mode requires `TRADING_MODE=live` in the k3s ConfigMap with a separate secret from paper keys, live keys are `AK`-prefixed and distinct [145]
- Live trading is disabled by reverting `ALPACA_PAPER_TRADE=true` or clearing `ALLOW_LIVE_TRADING`." [146]
- The kill switch in `src/risk_monitoring/circuit_breakers.py` cancels all open orders on a RED trip and requires an operator `reset()`." [147]
- Alpaca Agents uses MLflow for two distinct purposes: prompt registry and run tracking." [148]
- Both the prompt registry and run tracking live in the `Alpaca Agents` experiment on https://mlflow.johndstudios.net." [149]
- 31 prompts are registered on the MLflow server, covering every LLM-based agent in the system." [150]
- The ramp percentage can also be set via the MLFLOW_PROMPT_RAMP environment variable." [151]
- Agents without LLM prompts (RiskAgent, ExecutionAgent, MarketDataAgent, RegimeAgent, RebalancingAgent, PositionManagerAgent) are correctly e [152]
- The PromptResolver caches prompts for MLFLOW_PROMPT_CACHE_TTL seconds (default 300 = 5 minutes)." [153]
- The system includes comprehensive analytics and automatic optimization capabilities to continuously improve trading performance based on rea [154]
- The model optimizer is located at src/services/model_optimizer.py." [155]
- The model optimizer calculates optimal confidence thresholds." [156]
- The optimization CLI identifies models with win rates below 45%." [157]
- The optimization CLI identifies expensive models costing more than $0.10 per signal." [158]
- The optimization CLI identifies top performers with win rates above 60%." [159]
- The confidence optimization command calculates optimal minimum confidence for trade execution based on historical win rates." [160]
- The opportunity optimization command tunes the minimum opportunity score threshold based on prediction accuracy." [161]
- An optimal confidence threshold range requires a win rate of at least 55%." [162]
- An optimal confidence threshold range requires a minimum of 5 trades for significance." [163]
- Model analysis requires a minimum of 30 completed trades." [164]
- Both agents run automatically in every trading workflow execution." [165]
- The workflow order is Market Data → Technical/Sentiment → Risk → Portfolio → PositionManager → Rebalancing → Deliberation → Execution." [166]
- The default trailing stop activates after 5% profit and trails 3% below peak." [167]
- The default breakeven stop moves to breakeven at 2% profit." [168]
- The default profit protection locks in a 7% minimum at 10% profit." [169]
- The default maximum loss forces an exit at 10% loss." [170]
- The shadow eval gate requires the candidate to agree with @production on at least 90% of replayed states, with disagreement cases reviewed a [171]
- The runbook implements Spec §9.3 and ties together the WP-4 alias registry (src/prompt_registry/), the WP-6 eval scorer gate (src/eval/gate. [172]
- The overall code quality assessment is 8.5/10." [173]
- The estimated effort for refactoring #1 is 1 day." [174]
- The `analyze_security()` function is a 432-line function with 7 different responsibilities." [175]
- The estimated effort for refactoring #2 is 2 days." [176]
- The guide specifies creating a new test file at `tests/unit/agents/test_base_agent_llm_init.py`." [177]
- The guide specifies creating a new file `src/orchestration/workflow_executor.py` for the WorkflowExecutor service." [178]
- The guide specifies creating a new file `src/orchestration/reporting_service.py` for the ReportingService." [179]
- The Enhanced Risk Monitoring system scans the portfolio every 30 seconds by default, configurable." [180]
- The system provides real-time risk metrics including VaR, drawdown, volatility, beta, and Sharpe ratio." [181]
- Historical tracking uses TimescaleDB hypertables for performance analysis." [182]
- Migration 003 creates risk_metrics, alert_events, and other risk monitoring tables." [183]
- Python 3.11+ with dependencies installed via `uv sync --all-extras` is required." [184]
- The command to run all tests is `uv run pytest tests/ -v`." [185]
- The command to run a specific test file is `uv run pytest tests/unit/test_bullish_researcher.py -v`." [186]
- The command to run a single test is `uv run pytest tests/unit/test_bullish_researcher.py::test_bullish_case_generation -v`." [187]
- The command to run tests with coverage is `uv run pytest tests/ --cov=src --cov-report=html`." [188]
- The `mock_llm` fixture allows testing LLM-dependent code without API calls." [189]
- The `clean_database` fixture starts with a clean database and cleans it after the test." [190]
- The test suite is organized into unit, integration, contract, performance, property, and fixtures directories." [191]
- Async tests require the `@pytest.mark.asyncio` marker." [192]
- The overall coverage target is 85% or higher." [193]
- Deliberation agents require 95% or higher coverage." [194]
- Trading agents require 90% or higher coverage." [195]
- The default interval between analysis cycles is 300 seconds (5 minutes)." [196]
- The target average latency per analysis is under 40 seconds." [197]
- The target success rate for the Balanced configuration is at least 95%." [198]
- The target average confidence for the Balanced configuration is 60-80%." [199]
- The target cost per analysis for the Balanced configuration is approximately $0.015-$0.025 (~2¢)." [200]
- The Sentiment Agent makes calls to Claude 3.5 Sonnet." [201]
- The Execution Agent makes calls to Claude 3 Haiku." [202]
- The error rate should be less than 5% during execution reliability validation." [203]
- Execution latency should be less than 2 seconds." [204]
- The tech stack includes Python 3.12, FastAPI, PostgreSQL, SQLAlchemy async, React/TypeScript, and Slack webhooks." [205]
- The catalyst_weights table has a check constraint that current_weight must be between 0.8 and 1.2." [206]
- The opportunity_lifecycle table has a sentiment column constrained to 'bullish' or 'bearish'." [207]
- The notifications table has a type column constrained to 'opportunity', 'outcome', 'weight_change', or 'report'." [208]
- CatalystWeightsRepository defines a get_weight method that takes catalyst_type and returns an Optional[dict]." [209]
- Before refactoring, `get_options_chain()` was approximately 190 lines with complexity 26." [210]
- The target state for `get_options_chain()` is fewer than 80 lines." [211]
- Acceptance criteria state that `get_options_chain()` was reduced to fewer than 80 lines (now approximately 70 lines)." [212]
- All existing tests pass (73 tests)." [213]
- New unit tests for parsing helpers were added (16 tests)." [214]
- Current `_state_to_responses()` is approximately 270 lines and has high complexity." [215]
- Current `_detect_intent()` has hardcoded keyword lists inline." [216]
- Current `_extract_symbol()` has a 95-word `excluded_words` set inline." [217]
- Keyword lists are externalized to module-level constants." [218]
- The `SYMBOL_EXCLUSION_WORDS` constant externalizes the 95-word exclusion set from `_extract_symbol()`." [219]
- The `INTENT_KEYWORDS` constant externalizes keyword lists from `_detect_intent()`." [220]
- `_state_to_responses()` becomes a simple dispatcher." [221]
- Acceptance criteria: `_state_to_responses()` reduced from ~270 lines to ~50 lines." [222]
- Acceptance criteria: 7 focused response builder methods extracted." [223]
- Acceptance criteria: New unit tests for extracted helpers (22 tests)." [224]
- The current `_execute()` method is 275 lines with complexity 29." [225]
- The current `_submit_options_order()` method is 136 lines." [226]
- There are 5 duplicated Order constructions in exception handlers." [227]
- The target state for `_execute()` is approximately 120 lines." [228]
- The target state includes no duplicated Order construction code." [229]
- `_create_rejected_order()` eliminates duplicated Order construction in exception handlers." [230]
- `_apply_session_restrictions()` extracts a 63-line extended hours order type conversion block." [231]
- After refactoring, `_execute()` delegates session restrictions to `_apply_session_restrictions()`." [232]
- After refactoring, `_execute()` exception handling uses `_create_rejected_order()`." [233]
- The acceptance criteria require 100% coverage on new helper methods." [234]
- `_execute()` is approximately 230 lines with complexity 25." [235]
- `_synthesize_options_recommendation()` is approximately 225 lines with complexity 29." [236]
- Significant duplication exists in confidence calculation, calibration, and conflict detection." [237]
- Common synthesis logic is extracted to shared helpers." [238]
- Approximately 150 lines of duplication are eliminated." [239]
- `_build_confidence_list()` builds the confidence list based on asset type and available signals." [240]
- `_apply_confidence_adjustments()` applies all calibration, case, degradation, and signal adjustments." [241]
- `_identify_conflicting_signals()` identifies conflicting signals based on asset type." [242]
- `_execute()` is refactored to approximately 120 lines." [243]
- `_synthesize_options_recommendation()` is refactored to approximately 120 lines." [244]
- Current `_execute()` is approximately 350 lines with complexity 33." [245]
- Current `_assess_options_risk()` is approximately 280 lines with complexity 32." [246]
- Duplicated confidence calculation, calibration, and regime adjustment logic exists." [247]
- Target `_execute()` is less than 230 lines." [248]
- Target state includes 4 shared helper methods eliminating duplication." [249]
- `_apply_calibration_adjustments()` consolidates calibration logic (lines 187-198 and 532-544)." [250]
- `_apply_regime_adjustments()` consolidates regime adjustment logic (lines 259-266 and 564-571)." [251]
- `_apply_session_adjustments()` extracts a 60-line session adjustment block (lines 269-328)." [252]
- All tests in `tests/unit/agents/test_risk_agent.py` must pass." [253]
- The solution checks for recent analysis before running the workflow and returns cached results when fresh, with configurable TTL per asset t [254]
- Cache bypass is implemented via a ?force_fresh=true parameter, allowing power users to force fresh analysis while the default saves costs." [255]
- The TTL strategy is per-asset and configurable, with crypto more volatile (5 min) and stocks stable (15 min)." [256]
- The analysis_cache configuration enables the cache and sets TTL minutes to stock 15, crypto 5, option 10, and default 15." [257]
- The analyze_symbol endpoint has a force_fresh query parameter defaulting to False to bypass cache and run fresh analysis." [258]
- The analyze_symbol endpoint checks for cached analysis unless force_fresh is true and cache is enabled, using detect_asset_type and get_ttl  [259]
- The stream_cached_analysis function broadcasts agent_complete events for market_data, technical, sentiment, and risk with cached: True, then [260]
- The testing strategy includes unit tests verifying find_fresh_analysis returns analysis within TTL, returns None when older than TTL, exclud [261]
- The design aims to transform the existing single-strategy trading system into a multi-strategy orchestration platform." [262]
- The central arbiter detects conflicts when multiple strategies want to act on the same asset with opposing directions." [263]
- The central arbiter checks if disagreement is meaningful when both strategies are >70% confident." [264]
- Strategies are config-driven, defined in YAML and instantiated by the registry." [265]
- The existing deliberation system has 14 expert investor personas and integrates at the arbiter level." [266]
- The central arbiter triggers deliberation when both sides have >80% conviction." [267]
- Paper trading is always fully autonomous with no human approval needed." [268]
- The reward function uses log returns as the primary reward with penalties for transaction costs and drawdown, configurable per strategy." [269]
- Model inference is expected to take less than 1ms." [270]
- The finrl optional dependency group requires elegantrl>=0.3.0, gymnasium>=0.29.0, torch>=2.0.0, and numpy>=1.24.0." [271]
- The goal is to integrate the existing deliberation system with the multi-strategy arbiter for high-conviction conflicts." [272]
- When the Arbiter detects HIGH severity conflicts (both strategies >80% conviction), it routes to deliberation." [273]
- Deliberation uses strategy theses as context, enriches with expert consultation, and returns an adjusted recommendation." [274]
- IntentionConverter bridges the multi-strategy layer (intentions with 0-1 conviction) to the deliberation layer (recommendations with 0-100 c [275]
- IntentionConverter converts conviction (0-1) to confidence (0-100) by multiplying by 100 and casting to int." [276]
- DeliberationTrigger returns should_deliberate True with reason HIGH_CONVICTION_CONFLICT for HIGH severity conflict." [277]
- DeliberationTrigger returns should_deliberate False with reason CONFLICT_TOO_WEAK for LOW severity conflict." [278]
- DeliberationTrigger returns should_deliberate True with reason CONFIG_OVERRIDE for MEDIUM severity conflict when min_severity_for_deliberati [279]
- The Alpaca Agents system runs three distinct agentic loops: Analysis, Research, and Autonomous Trader." [280]
- The proposal keeps all indicators as custom NumPy implementations and does not adopt TA-Lib." [281]
- Proposal 014 catalogued five bugs and missing indicators in the custom NumPy technical analysis library." [282]
- TA-Lib has 160+ indicators, requires a C library install, and is actively maintained (2024+)." [283]
- pandas-ta has 130+ indicators, is pure Python, and is stale (last commit 2023)." [284]
- pandas-ta-classic has 203 indicators, is pure Python, and is an active fork." [285]
- The custom NumPy library has 10 indicators." [286]
- The recommendation is to adopt TA-Lib (the Python wrapper ta-lib-python, backed by the C library)." [287]
- Decision R1: Adopt TA-Lib; remove the vestigial TA-Lib>=0.4.28 from pyproject.toml and add the real dependency with the C library install in [288]
- Decision R3: Reject custom implementations for standard indicators; keep custom only for indicators TA-Lib doesn't cover." [289]
- The system uses a linear workflow where agents work independently." [290]
- The Bullish Researcher Agent's role is to advocate for the trade by finding supporting evidence." [291]
- The Bearish Researcher Agent's role is to play devil's advocate and identify risks." [292]
- The Synthesizer Agent's role is to moderate the debate and synthesize conclusions." [293]
- The deliberation configuration sets enabled to true and debate_rounds to 1." [294]
- The bullish and bearish researcher agents are configured to use anthropic/claude-3-5-sonnet while the synthesizer agent uses openai/o1-mini. [295]
- The estimated development time for the enhancement is 4-6 hours." [296]
- The estimated cost impact is +2 LLM calls per trade from the researchers and synthesizer." [297]
- The estimated latency impact is +5-10 seconds per trade." [298]
- The proposed persistent memory and learning system records all agent analyses and trade outcomes." [299]
- The proposed system tracks performance metrics per agent and pattern." [300]
- The proposed system calibrates agent confidence based on track record." [301]
- The memory system architecture uses a Vector DB for embeddings and PostgreSQL for structured data." [302]
- The OutcomeRecord data model tracks profit/loss, holding period, and correctness of technical signal, sentiment direction, and risk estimate [303]
- The estimated timeline is 8 weeks (2 sprints)." [304]
- The expected ROI is a 10-15% improvement in risk-adjusted returns." [305]
- The current deliberation system runs one round of debate." [306]
- The `debate_rounds` config exists but is not functional; all deliberation is single-round." [307]
- The DeliberationCoordinator checks for early consensus if disagreement is less than the consensus threshold." [308]
- The default consensus threshold is 0.20, meaning stop early if disagreement is less than 20%." [309]
- The disagreement calculation uses the absolute difference in confidence levels." [310]
- The configuration sets debate_rounds to 3 as the maximum rounds." [311]
- The configuration sets max_rounds to 5 as a hard limit." [312]
- The configuration sets min_rounds to 1." [313]
- Proposal 003 is largely complete with 76 tests passing and good coverage." [314]
- Current testing coverage is incomplete for the new deliberation system." [315]
- Unit tests are missing for the deliberation agents BullishResearcher, BearishResearcher, and Synthesizer." [316]
- Integration tests are missing for the full deliberation workflow." [317]
- Tests are missing for the deliberation toggle in enabled and disabled states." [318]
- Mock LLM responses for deterministic testing are missing." [319]
- Total test coverage is 62%." [320]
- The target is 85%+ coverage with focus on critical paths." [321]
- The proposed solution is to build a comprehensive, maintainable test suite covering unit tests, integration tests, contract tests, and prope [322]
- The reporting module is located at src/reporting/ with report_generator.py as the main report generation logic." [323]
- generate_portfolio_summary accepts a format parameter with markdown, json, and html options, defaulting to markdown." [324]
- The analyze_security workflow function has a generate_reports parameter defaulting to True." [325]
- The default reporting output formats are markdown and json, with html and pdf noted as future." [326]
- The proposal has an estimated effort of 4 weeks and no dependencies." [327]
- The proposal has status Proposed, priority High, effort Medium, and impact High." [328]
- Risk agent runs once per analysis and does not continuously monitor portfolio risk during market hours, real-time drawdown, correlation chan [329]
- The proposed solution is to implement a real-time risk monitoring system with alerts and circuit breakers." [330]
- The proposed architecture includes src/risk/ with monitor.py for continuous risk monitoring, alerts.py for alert system (email, Slack, SMS), [331]
- Real-time monitoring tracks portfolio Value at Risk (VaR), current drawdown vs max drawdown, correlation matrix updates, and concentration r [332]
- The alert system triggers on drawdown > 15% (warning) or > 18% (critical), VaR increases > 50% intraday, correlation between positions > 0.8 [333]
- The risk dashboard displays current drawdown (8.2% / 20% max), portfolio beta (1.15), 30-day Sharpe ratio (1.8), correlation heatmap, and Va [334]
- The implementation timeline is 6 weeks." [335]
- Proposal 006 has status Proposed, priority High, effort Medium, and impact High." [336]
- The solution is a comprehensive analytics system tracking agent performance across multiple dimensions." [337]
- TechnicalAgent is well calibrated, with 80% confidence corresponding to 78% actual." [338]
- Model comparison for Technical Agent shows claude-3-5-sonnet at 72% accuracy and $0.004/trade, claude-3-haiku at 68% accuracy and $0.001/tra [339]
- The recommendation is to use grok-4-fast for best value." [340]
- The implementation timeline is 5 weeks." [341]
- The dependencies include Proposal 001 (Memory System)." [342]
- The expected impact is 10-15% improvement via model optimization." [343]
- Proposal 007 was implemented on 2025-10-18 with medium priority, medium effort, and medium impact." [344]
- The proposed solution is a web-based UI for visualizing and interacting with deliberations." [345]
- The deliberation viewer is implemented at src/portfolio/deliberation_viewer.py." [346]
- Multi-round navigation is deferred because it requires an enhanced report format with per-round data." [347]
- Outcome correlation is deferred because it requires trade outcome tracking integration." [348]
- Argument highlighting is deferred because it requires structured argument extraction." [349]
- High volatility regime is characterized by VIX > 30." [350]
- High volatility strategy adjustment reduces position sizes by 50%." [351]
- The MarketRegimeAgent classifies regime as high_volatility if VIX > 30." [352]
- The MarketRegimeAgent classifies regime as bull_market if VIX < 20 and SPY price > 200 EMA and breadth > 0.7." [353]
- The MarketRegimeAgent classifies regime as bear_market if VIX > 25 and SPY price < 200 EMA." [354]
- The workflow adds an edge from market_data to regime_detection and from regime_detection to technical." [355]
- The proposal expects a 15-25% Sharpe improvement." [356]
- Current backtesting only runs conditionally, on conflicting signals." [357]
- Current backtesting backtests a single strategy." [358]
- Current backtesting has no A/B testing of deliberation vs non-deliberation." [359]
- Current backtesting has no walk-forward optimization." [360]
- Current backtesting has limited metrics (Sharpe, win rate, drawdown)." [361]
- The example full historical backtest reports 24.5% total return, 1.82 Sharpe, -12.3% max drawdown, 68% win rate, 147 trades, and 3.2-day ave [362]
- The example A/B test shows deliberation achieving Sharpe 1.82 and 68% win rate versus 1.65 and 64% without deliberation." [363]
- Walk-forward optimization uses a 180-day training window, 60-day test window, and 30-day step." [364]
- Walk-forward optimization achieved an out-of-sample Sharpe of 1.94 versus a 1.82 baseline." [365]
- Proposal 010 (Explainability & Interpretability) was implemented on 2025-10-18 with Medium priority, High effort, and High impact." [366]
- The explainability implementation is located in `src/explainability/`." [367]
- In the sample AAPL BUY feature-importance output, Technical Signal contributes 35%, Sentiment Score 28%, Risk/Reward Ratio 22%, Volume Confi [368]
- The sample SHAP analysis decomposes final confidence of 72% from a 50% neutral base, with Technical Signal +18%, Sentiment +12%, Risk/Reward [369]
- The confidence breakdown example computes a 72% final confidence from Technical 75% (weight 35% → +26.25%), Sentiment 80% (weight 25% → +20. [370]
- Sensitivity analysis shows final confidence is most sensitive to technical confidence (±1% tech → ±0.35% final) and least sensitive to risk  [371]
- Feature importance uses weighted importance scoring with Technical 35%, Sentiment 25%, Risk 20%, Fundamental 15%, and Deliberation 5%." [372]
- Phase 1 core functionality took 1 day of actual effort, while Phase 2 advanced features were deferred with an estimated 2-3 weeks of effort. [373]
- A single YAML flag enables personas, with individual persona configs." [374]
- Individual persona configurations can override the model per persona, as shown by the Warren Buffett persona using anthropic/claude-3.5-sonn [375]
- The Benjamin Graham synthesizer persona uses openai/o1-mini because synthesis requires reasoning." [376]
- The mitigation for LLM cost increase is to use the same models as existing, just different prompts." [377]
- Proposal 001 (Agent Memory & Learning System) has High priority, Medium-High effort, Transformative impact, and is Implemented." [378]
- Proposal 003 (Comprehensive Testing Suite) has Critical priority, Medium effort, High impact, and is Largely Done." [379]
- Proposal 013 (Agentic Dashboard: Multi-Loop Operations Console) has High priority, High effort, High impact, and is Approved." [380]
- Proposal 014 (Technical Indicators) is superseded by proposal 015." [381]
- The Comprehensive Testing Suite (Proposal 003) has 76 tests passing with good coverage." [382]
- The Market Regime Detection feature uses a 6 regime classification system." [383]
- The system performance target for Sharpe Ratio is 2.0+ (from current ~1.5)." [384]
- The system performance target for Win Rate is 70%+ (from current ~60%)." [385]
- The code quality target for Test Coverage is 85%+ (from 62%)." [386]
- The document reports a total of 12 proposals and a last-updated date of 2026-07-11." [387]
- Alpaca Agents is described as a production-ready multi-agent AI trading system." [388]
- The Developer Manual covers architecture and development guide." [389]
- The Database Setup document covers PostgreSQL/TimescaleDB configuration." [390]
- The Memory System architecture document describes pgvector semantic memory with sentence-transformer embeddings." [391]
- The Workflow Analysis architecture document covers LangGraph deliberation workflow analysis." [392]
- To set up the database, run ./scripts/db_start.sh from the alpaca-agents directory." [393]
- Install dependencies with uv sync --all-extras." [394]
- Run tests with uv run pytest tests/ -v." [395]
- Launch the dashboard with uv run python main.py dashboard." [396]
- The Multi-Agent Trading feature status is Production." [397]
- The system version is 2.1.0." [398]
- Phase 4 (Learning & Calibration) requires Phase 1's #200 signal outcome tracking to be complete." [399]
- Market data API calls were reduced by 10x (#212)." [400]
- The trading system uses PostgreSQL with TimescaleDB for portfolio tracking and trading history storage." [401]
- TimescaleDB provides time-series optimization with hypertables and continuous aggregates." [402]
- The script ./scripts/db_start.sh starts the TimescaleDB database." [403]
- The Docker command runs a TimescaleDB container named timescaledb, maps port 5432:5432, sets POSTGRES_PASSWORD and POSTGRES_DB=trading, and  [404]
- The .env file configures PostgreSQL connection with host localhost, port 5432, database trading, user trading_user, password your_secure_pas [405]
- The system automatically creates core tables positions, trades, orders, portfolio_snapshots, and performance_metrics." [406]
- When DB_USE_TIMESCALE=true, the tables trades, portfolio_snapshots, and performance_metrics are converted to hypertables partitioned by exit [407]
- TimescaleDB automatically creates and maintains the continuous aggregates daily_portfolio_performance and weekly_trading_stats." [408]
- TimescaleDB provides 10-100x faster queries on time-based data through time-series optimization." [409]
- TimescaleDB automatic compression provides 90%+ storage savings on historical data." [410]
- The database can be started with ./scripts/db_start.sh or docker-compose up -d timescaledb." [411]
- The database is available at localhost:5432 with database trading, user trading_user, and default password trading_secret." [412]
- Database status can be checked with ./scripts/db_status.sh." [413]
- The .env file should be updated with DB_TYPE=postgresql, DB_POSTGRES_HOST=localhost, DB_POSTGRES_PORT=5432, DB_POSTGRES_DATABASE=trading, DB [414]
- The connection can be tested by running uv run python main.py dashboard or python main.py dashboard." [415]
- pgAdmin can be started with docker-compose --profile admin up -d and is accessible at http://localhost:5050 with email admin@trading.local a [416]
- To connect pgAdmin to the database, register a server named 'Trading DB' with host timescaledb (Docker network), port 5432, database trading [417]
- This project uses pre-commit to ensure code quality, security, and consistency before committing changes." [418]
- Pre-commit hooks automatically run checks on code before each commit, catching issues early and maintaining high code standards." [419]
- Pre-commit checks include code formatting with Black and Ruff." [420]
- Pre-commit linting uses Ruff, which replaces flake8, isort, and pylint." [421]
- Pre-commit security checks use Bandit and detect-secrets." [422]
- Pre-commit type checking uses mypy." [423]
- Pre-commit testing runs a fast subset of unit tests." [424]
- Pre-commit file integrity checks include trailing whitespace, EOF fixers, and YAML/JSON validation." [425]
- Pre-commit documentation checks include Markdown formatting." [426]
- First-time setup installs all dev dependencies with uv sync --all-extras and installs pre-commit hooks with uv run pre-commit install." [427]
- The pytest-unit hook duration is about 5-10 seconds and runs unit tests only, not integration tests." [428]
- Integration tests run in CI, not pre-commit, because they are too slow." [429]
- This project uses uv-secure to scan dependencies for known security vulnerabilities." [430]
- uv-secure checks the uv.lock file against the PyPI JSON API for security issues." [431]
- uv-secure is configured as a manual pre-commit hook because it makes network calls to PyPI, which can be slow (~3+ minutes for 197 dependenc [432]
- The uv-secure pre-commit hook is configured with rev 0.14.0, args [--check-direct-dependency-vulnerabilities-only, uv.lock], files ^uv\\.loc [433]
- uv-secure should always be run before creating a release." [434]
- uv-secure should be run after `uv lock --upgrade`." [435]
- A successful uv-secure scan reports 'No vulnerabilities or maintenance issues detected!' and checks 197 dependencies." [436]
- To update all dependencies to latest compatible versions, run `uv lock --upgrade` and then re-run the scan with `pre-commit run --hook-stage [437]
- uv-secure is skipped in CI by default, as configured in `.pre-commit-config.yaml` with `ci: skip: [pytest-unit, mypy, uv-secure]`." [438]
- uv-secure scan time is approximately 3-5 minutes for 197 dependencies, requires network access for PyPI API calls, and pre-commit caches the [439]
- The document was last updated on 2025-10-10 and specifies uv-secure version 0.14.0." [440]
- Python 3.10 or higher is required." [441]
- PostgreSQL 14+ is required, TimescaleDB is recommended, and the repository ships a Docker setup." [442]
- The system requires accounts for Alpaca, OpenRouter, and Finnhub." [443]
- Dependencies are installed with `uv sync`, which creates the virtual environment automatically." [444]
- The database runs as a TimescaleDB container, and helper scripts under `scripts/` handle startup and schema creation." [445]
- The analysis workflow fetches recent news from Finnhub, analyzes sentiment with the configured LLM, fetches market data from Alpaca, perform [446]
- Whether trades execute automatically or wait for higher confidence is controlled by `auto_execute` and `min_confidence` in `data/config/sett [447]
- Before running autonomous trading, the safety checklist requires using a paper trading account (not live)." [448]
- Alpaca Agents is an autonomous AI-powered trading system that uses multiple specialized agents to analyze markets, discover opportunities, a [449]
- The News Monitor component monitors Finnhub for breaking news." [450]
- The default model for `market_data_agent` is `anthropic/claude-3.5-sonnet`." [451]
- The system uses 7 specialized agents orchestrated with LangGraph." [452]
- Each agent is assigned a specific LLM model: Research uses Claude Sonnet, Market Data uses Claude Haiku, Technical uses Claude Haiku, Sentim [453]
- Each analysis costs approximately $0.02 and takes 18–37 seconds." [454]
- The sentiment analysis agent uses the Alpaca News API with 50 articles per request." [455]
- The codebase contains approximately 114,671 lines of code excluding tests." [456]
- The web UI is built with React and FastAPI." [457]
- The system is restricted to paper trading and must never be used with live trading credentials." [458]
- Setup time is approximately 30 seconds when using the uv package manager." [459]
- The project has over 4000 tests passing." [460]
- Godot reported a parse error at res://godot/world_preview_3d.gd:102 stating it could not resolve external class member \"world_seed\"." [461]
- Godot failed to load the script res://godot/world_preview_3d.gd with a \"Parse error\"." [462]
- ChunkData.get_block has no bounds check." [463]
- Nothing in the runtime calls update_around." [464]
- The project is a Godot project containing project.godot and 46 .gd scripts." [465]
- Godot 4.7.2 is installed on the machine." [466]
- GDScript's LSP is not one of opencode's built-in language servers." [467]
- Godot's LSP is a TCP server on port 6005, requiring a stdio bridge." [468]
- Godot editor settings confirm the GDScript LSP listens on 127.0.0.1:6005 when the Godot editor is running." [469]
- The Godot editor was running with the GDScript LSP live on 127.0.0.1:6005." [470]
- The stdio↔TCP bridge works end-to-end." [471]
- An opencode.json was created with a custom gdscript LSP for .gd files and the context7 remote MCP." [472]
- A .opencode/godot-lsp-bridge.js stdio↔TCP bridge was created because Godot's LSP is TCP-only on 127.0.0.1:6005." [473]
- The GDScript LSP only runs while the Godot editor is open, so opencode's LSP connects and disconnects as the editor is opened or closed." [474]
- The block registry defines 8 hardcoded blocks registered via _register(id, name, solid, opaque, color)." [475]
- ChunkData.blocks is a PackedInt32Array always resized to 4096 and filled with AIR, indexed as x + y*16 + z*256, with no sparse storage, pale [476]
- The persistence format declares FORMAT_VERSION = 1 but never checks it on load." [477]
- block_registry has 8 blocks and no ore or material palette at all." [478]
- ChunkManager.update_around is documented \"Call every frame\", but nothing calls it at runtime." [479]
- The repository has 17 open issues." [480]
- Issue #11 is the only loose end from finished work and requires one exported-build benchmark to validate the use_threads=true default." [481]
- Issue #4 (Texture2DArray) fixes mip bleeding and is a hard prerequisite for #5 greedy meshing." [482]
- The workflow requires an existing issue, a failing test/harness, green, preflight, and PR." [483]
- No Godot export templates were installed, which the release-build part of issue #11 requires." [484]
- The vendored godot_mcp addon uses absolute preload paths res://addons/godot_mcp/... while the addon actually lives at godot/addons/godot_mcp [485]
- The open issues being reviewed belong to the GitHub repository hybridindie/godot-mcp." [486]
- The repository has 20 open issues at the time of the session." [487]
- Issue #422 is a high-priority silent failure in which deleting a .tscn file causes a stale tab to resurrect a mangled scene." [488]
- Issue #414 is a high-priority silent failure in which `set_node_property` with a res:// path no-ops while still reporting `set:true`." [489]
- Issue #413 is a high-priority silent failure in which `navigation_bake_mesh` returns `baked:true` on an empty navmesh." [490]
- Issue #411 is a high-priority silent failure in which the debugger traps the game invisibly." [491]
- The recommended next batch is the four priority:high silent-failure bugs #422, #414, #413, and #411." [492]
- A failing test for issue #414 reproduced the exact silent no-op from the issue, with `set:true` echoed and `null` returned." [493]
- A failing test for issue #413 reproduced `baked:true` being returned on an empty navmesh." [494]
- A failing test for issue #422 reproduced the deleted scene's stale tab remaining active." [495]
- The engine is built on Godot 4.7 using GDScript only with the 'mobile' renderer." [496]
- Chunks are 16³ blocks stored in a PackedInt32Array flat storage with no palette or RLE compression." [497]
- Meshing is naive per-face culled with no greedy meshing." [498]
- The engine has no ambient occlusion, no smooth lighting, and no per-face lighting." [499]
- Zylann measured that creating a mesh collider is 3–5× more expensive than meshing itself." [500]
- Greedy meshing reduces quads from 384 to 6 for an 8³ cube, 4770 to 2100 for a sphere, and 2198 to 1670 for noise terrain." [501]
- A healthy run spawns the player near (8, 10, 8), in the open, with visible terrain." [502]
- Headless probe on clean main places the player at (8.5, 8.9, 8.5) with eye at (8.5, 10.5, 8.5)." [503]
- Headless probe on clean main shows clear air at feet, eye, and 1-4m in front, with all ground cells non-solid." [504]
- test_spawn.gd and test_mesher.gd pass with 0 failed." [505]
- pos=8,8,8 means the player is at y≈8, inside the terrain, with ground=7 so feet are buried about 1 m." [506]
- A real defect on clean main is that in the windowed run the player at (8.5, 8.9, 8.5) is 0.1 m into the terrain, with block 7 solid." [507]
- Tier-1 is drained and the next work item is #5 (greedy meshing), the head of the tier-2 queue." [508]
- test_render_smoke.gd:49 calls look_at before add_child, logging \"Node not inside tree\" every run." [509]
- #5 greedy meshing is the only open story of epic #28." [510]
- ChunkData is a dense PackedInt32Array(4096) indexed as x + y*n + z*n²." [511]
- Chunk neighbor gating uses a [[1,0,0],…] list of 5 directions, assuming the XZ ring has exactly one chunk per side." [512]
- 0fps' culled meshing produces roughly 16× fewer quads than naive meshing on 16³ chunks, and greedy meshing is bounded at ≤ 8× optimal by the [513]
- 15 monohedral convex pentagon tiling families are known." [514]
- The Cairo pentagonal tiling belongs to the type 4 family of convex pentagon tilings." [515]
- The Cairo pentagonal tiling has 5 edge-neighbors per tile." [516]
- The prismatic pentagonal tiling is the dual of the elongated triangular tiling 3.3.3.4.4." [517]
- All 15 convex pentagon tiling types are periodic." [518]
- The truncated square tiling (4.8.8) is the only edge-to-edge regular-polygon tiling containing an octagon." [519]
- In the truncated square tiling (4.8.8), each octagon has 4 octagon neighbors and 4 square neighbors." [520]
- The truncated square tiling (4.8.8) is the truncation of the square tiling at every vertex." [521]
- The pinwheel tiling uses a right triangle 1-2-√5 and a 5-tile substitution at scale √5." [522]
- Triangles are always planar with per-vertex heights, whereas a square heightfield is not." [523]
- comfyui_mcp is a standalone MCP server for ComfyUI that is usable by any AI agent harness over stdio or Streamable HTTP." [524]
- The comfyui_mcp server is built on FastMCP 4 and enables AI assistants to generate images, run workflows, and manage jobs through ComfyUI wi [525]
- The MCP framework used is fastmcp[tasks] 4.0.0b1, a standalone FastMCP 4 beta built on MCP SDK v2." [526]
- The configuration file for comfyui_mcp is located at ~/.comfyui-mcp/config.yaml." [527]
- Tests use pytest-asyncio with asyncio_mode = auto and mock ComfyUI API responses with respx." [528]
- comfyui-mcp-secure version 2.2.0 was released on 2026-08-29." [529]
- The server migrated to FastMCP 4 beta (fastmcp[tasks]==4.0.0b1, built on MCP SDK v2), importing FastMCP from fastmcp instead of the mcp.serv [530]
- The Dockerfile Python base image was fixed from python:3.14-slim to python:3.12-slim to align with CI, .python-version, and the requires-pyt [531]
- comfyui-mcp-secure version 2.1.0 was released on 2026-05-12 as an additive minor release with no breaking changes since 2.0.0." [532]
- The project uses pre-commit to enforce code quality via a git hook that runs checks automatically on every git commit against staged files." [533]
- The pre-commit hook suite includes trailing whitespace fixer, YAML check, large file check, Ruff lint, Ruff format, and Mypy type annotation [534]
- All changes to the project must include tests, which use pytest with pytest-asyncio in auto mode and respx for mocking HTTP calls." [535]
- Tests must mock ComfyUI API responses with respx and must never make real HTTP calls." [536]
- Pydantic models are used for configuration and data structures in the project." [537]
- The project handles workflow execution against ComfyUI and must never expose dangerous endpoints including /userdata, /free, /users, and /hi [538]
- The default local ComfyUI URL for development is http://127.0.0.1:8188." [539]
- CI will run lint, type-check, and test jobs automatically on every pull request." [540]
- The Selective API Surface never proxies the dangerous ComfyUI endpoints /userdata, /free, and /users." [541]
- Version 2.1.0 (released 2026-05-12) is additive with no breaking changes since 2.0.0, adding comfyui_analyze_workflow, replacing the Ollama  [542]
- In version 2.0.0, the parameter `id` was renamed to `node_id` in comfyui_install_custom_node, comfyui_uninstall_custom_node, and comfyui_upd [543]
- comfyui-mcp-secure requires Python 3.12 or later and the uv package manager as prerequisites." [544]
- The `godot-agents` repository functions as the orchestrator/client, depending on the `godot-mcp` repository for the actual Godot editor brid [545]
- The `godot-agents` system is tightly coupled to the specific `godot-mcp` server implementation, requiring its exact surface structure." [546]
- For `godot-mcp` versions 2026.08.31b4 and later, toolset enablement is server-global and persists across client connections." [547]
- The default transport mechanism is stdio, requiring the `godot-mcp` CLI to be resolvable via environment variables or installation path." [548]
- Since version 2026.08.31b4, `godot-mcp` emits a structured payload, which the client prefers for normalization over text parsing." [549]
- The build/verify/fix loop is capped by a default of 3 retries and a recursion limit of 50." [550]
- The knowledge fabric is accessible by default at a specific local path, but this location can be overridden." [551]
- All configuration must be done via environment variables, as there is no configuration file." [552]
- The default transport mechanism for MCP is `stdio`." [553]
- The default port for HTTP transport is 9090." [554]
- Web search is disabled by default, requiring explicit opt-in to enable the retrieval band." [555]
- The experimental fluid executor is disabled by default, requiring explicit opt-in to activate the fluid loop." [556]
- Setting the MLflow tracking URI enables tracing and evaluation logging for the agent run." [557]
- The agent verifier can be instructed to run the project's existing GUT test suite after a code change." [558]
- Live mode execution, which provides the authoritative pass-rate, requires specific infrastructure components including a Godot editor, the ` [559]
- The execution flow involves the planner, executor, and verifier interacting with Godot via the MCP client." [560]
- The live calibration run requires a running Godot editor and the `godot_mcp` bridge and cannot be executed in CI." [561]
- Logging is controlled by setting the `MLFLOW_TRACKING_URI` environment variable, and without it, logging is a no-operation." [562]
- The Godot-native AI development platform is composed of three distinct layers: a Godot addon and bridge, an open-source FastMCP server, and  [563]
- The Godot addon and bridge holds direct authority over the live Godot editor state, scene trees, and runtime data." [564]
- The FastMCP server acts as the typed capability surface between the agent and Godot, managing safety, preconditions, and operation constrain [565]
- The agent system provides the policy and orchestration layer, managing planning, memory selection, and execution strategy." [566]
- The v1 implementation uses a LangGraph StateGraph architecture where nodes operate on typed shared state and return partial state updates." [567]
- The execution policy mandates that the MCP is the primary substrate for Godot work, requiring specific tool usage preferences." [568]
- Python 3.13 or newer is required for the setup." [569]
- The `godot-mcp` server is a standalone project, distinct from the agent's dependencies." [570]
- In service mode, a single `godot-mcp` HTTP service manages the editor bridge, preventing multiple clients from sharing the same live editor  [571]
- Godot version 4.4 or newer is required for live runs with the `godot_mcp` addon enabled." [572]
- Ollama defaults to listening on `http://127.0.0.1:11434`, unless overridden by `OLLAMA_HOST`." [573]
- MLflow tracing is optional; setting `MLFLOW_TRACKING_URI` enables logging, otherwise MLflow calls are no-ops." [574]
- The knowledge fabric lives at a default location, which can be overridden by an environment variable." [575]
- The agent is a self-improving, local-first LangGraph agent for AI-driven Godot development." [576]
- The agent uses a LangGraph StateGraph composed of 14 nodes to manage the build → verify → fix loop." [577]
- Tracing to MLflow is conditional on setting the `MLFLOW_TRACKING_URI` environment variable." [578]
- The system requires Python 3.13+ and includes an 80% coverage gate in its CI workflow." [579]
- The default WebSocket server binds to `127.0.0.1` on port `9070`." [580]
- PR #442 (Enforce local ollama-only graphify backend) failed CI on ruff." [581]
- PR #441 (Fix debugger silent no-op (break state)) failed CI on live editor e2e." [582]
- PR #440 (Close editor tabs for deleted open scenes) failed CI on live editor e2e." [583]
- Qodo reviews have landed on all 5 PRs." [584]
- Qodo found a real bug in #440: EditorInterface.close_scene() closes the active tab, not the one for the deleted path, so multi-tab deletes c [585]
- The EditorInterface Methods table in the file spans lines 43–110." [586]
- The complete set of EditorInterface methods whose names contain \"scene\" is 17 methods, with no others present in the Methods table." [587]
- EditorInterface has no method to make a different open scene tab the active one (no set_current_scene or activate_scene_tab equivalent)." [588]
- The signature of open_scene_from_path is `void open_scene_from_path(scene_filepath: String, set_inherited: bool = false)`." [589]
- The signature of reload_scene_from_path is `void reload_scene_from_path(scene_filepath: String)`." [590]
- get_open_scenes() and get_open_scene_roots() list all open scenes, but the active-tab cursor is only movable implicitly." [591]
- Graphify version 0.9.61 already lists opencode as an install platform." [592]
- The pre-existing .opencode/plugins/graphify.js only performs a once-per-session bash echo, much weaker than graphify's Claude hooks." [593]
- Because opencode cannot deny from tool.execute.before, Claude's permissionDecision: deny degrades to a strong once-per-session nudge." [594]
- The reporter tested the setup with Godot 4.7.0, godot-mcp version 2026.09.10, and Windows 10." [595]
- The MCP external tool server URL is entered as http://<IP or resolvable name of the MCP host>:<port>/mcp, with the MCP port defaulting to 90 [596]
- Editing tools stay hidden until the agent calls godot_enable_toolset(\"scene_edit\")." [597]
- After calling godot_enable_toolset for any gated toolset, the tools appear in godot_list_tools_by_safety_class but are not callable by the m [598]
- godot_enable_toolset() mutates the server-global enabled set in mcp_server/toolset_middleware.py:44-66 but never emits a notifications/tools [599]
- FastMCP 4.0.1 has no server-side send_tools_list_changed helper, but the MCP SDK's ServerRequestContext provides notify_tools_changed()." [600]
- All 162 addon cmd_* handlers exist and match mcp_server/command_map.py." [601]
- The proposed fix is to emit notifications/tools/list_changed after enable_toolset/disable_toolset using the MCP SDK context." [602]
- The root cause of the issue is an OpenCode client bug rather than a godot-mcp server issue." [603]
- Issue #485 was closed via PR #491 with the server-side fix implemented." [604]
- Issue #486 is in CLOSED state." [605]
- When .tscn or .gd files are edited externally, the Godot editor does not detect or apply the changes, requiring the user to manually close a [606]
- No cmd_scan, cmd_refresh, or cmd_reimport handler exists in the addon." [607]
- The addon only calls update_file() after its own writes." [608]
- cmd_reload_scene exists but is destructive (confirm=True) and requires the scene to already be open." [609]
- A proposed fix is to add a non-destructive cmd_rescan_filesystem handler that triggers EditorFileSystem.scan() to pick up external changes." [610]
- A proposed additional fix is to add a cmd_reload_scene variant that does not require the destructive confirm flag when the scene is already  [611]
- Issue #487 is in CLOSED state." [612]
- When the same PackedScene is instanced twice, property overrides on the second instance's children are silently ignored." [613]
- No tool can enable Editable Children." [614]
- The tree inspector emits no owner/editable-instance metadata, so agents cannot distinguish instanced children from local nodes." [615]
- _cmd_instance_scene calls packed.instantiate(GEN_EDIT_STATE_INSTANCE) but never calls set_editable_instance() on the instance." [616]
- scene_inspect.gd traverses with un-owner-filtered node.get_children() and emits no owner or editable marker." [617]
- Node.set_editable_instance(node, is_editable) is the API that would fix the issue, but no handler or MCP tool exposes it." [618]
- Proposed fix: add a cmd_set_editable_children handler plus a corresponding mutating, UndoRedo-wrapped MCP tool." [619]
- Proposed fix: include owner and is_editable_instance metadata in serialize_tree output so agents can identify instanced vs local nodes." [620]
- Proposed fix: consider auto-enabling editable children when an agent creates a second instance of the same PackedScene." [621]
- Every session requires calling three tools (godot_get_server_info, godot_list_toolsets, and godot_enable_toolset per needed category) before [622]
- A default toolset configuration option partially exists via the GODOT_MCP_DEFAULT_TOOLSETS environment variable." [623]
- A proposed option is to auto-enable the scene_edit and scripts toolsets by default for most workflows." [624]
- A proposed option is a single godot_bootstrap call that returns server info, tool list, and enables requested toolsets in one round trip." [625]
- The friction was amplified by issue #485, which is an OpenCode client bug rather than a godot-mcp issue." [626]
- Issue #488 is in the CLOSED state." [627]
- Issue #489 is in CLOSED state." [628]
- The root cause is described as a downstream symptom of Issue #3 (instanced scene overrides fail)." [629]
- When the instance doesn't load properly due to the editable-children gap, nodes beneath it don't exist in the tree, so path resolution silen [630]
- The fix was to fix Issue #3 by adding a `set_editable_children` tool plus owner metadata in tree inspection." [631]
- MuhamadBarzani closed the issue on 2026-09-16, stating it is a downstream symptom of #487 (instanced scene overrides fail)." [632]
- AnimationPlayer path resolution works correctly when the instance loads; the failure is that the instance doesn't load due to the missing ed [633]
- MCPBridge._pending_times is read and erased in _handle_text() but never populated anywhere." [634]
- Acceptance criteria: No dead state: _pending_times removed or populated." [635]
- Acceptance criteria: Contract/integration tests for the command_completed signal payload updated." [636]
- MCPPlugin._server_version is declared and read by _server_version_label() but never assigned." [637]
- The comment claims the server version is populated when the bridge connects via cmd_get_project_info, but nothing wires that." [638]
- The dock's version label can only ever show \"Godot x.y.z\", never the server package version." [639]
- A proposed fix is to add a cmd_get_addon_info handshake and have the server push its version to the addon on connect, or embed the server ve [640]
- A proposed fix is to assign _server_version from that handshake, so the dock label shows \"godot-mcp <calver> / Godot <x.y.z>\"." [641]
- A simplest alternative if a full handshake is deferred is to have cmd_get_project_info responses carry server_version and have the plugin in [642]
- An acceptance criterion is that _server_version is populated by a real value flowing from the server." [643]
- An acceptance criterion is that the dock displays both halves of the label once connected and a contract test pins the handshake envelope." [644]
- An acceptance criterion is that this issue pairs naturally with the cmd_get_addon_info issue and should be implemented together." [645]
- Issue #521 is in state CLOSED." [646]
- Issue #521 has labels bug and component:addon." [647]
- command_router.gd is 756 lines long." [648]
- The intended result is that the router contains only dispatch, envelope builders, and the two router-owned commands cmd_undo and cmd_run_com [649]
- An acceptance criterion is that no handler calls a private method on the router, with helpers coming from the new module." [650]
- An acceptance criterion is that existing contract tests pass unchanged, since envelope shapes are pinned and no behavior change is expected. [651]
- Issue #522 is in state CLOSED." [652]
- The 20-node UndoRedo threshold (#461) exists in exactly one of three batch-apply paths." [653]
- In batch.gd, batch_set_property declares a local const `undo_threshold := 20` but hardcodes the literal `> 20` on line 183 and in the hint t [654]
- composite.gd's batch_create_nodes (line 161) and apply_node_edits (line 229) have no threshold at all." [655]
- A 500-node batch create opens one giant UndoRedo action while an equivalent-sized batch_set_property silently skips undo, causing inconsiste [656]
- batch.gd cross-scene path (_cross_scene_one) mutates scenes on disk directly with no undo." [657]
- The fix requires batch_create_nodes and apply_node_edits to return the same `undoable` + `hint` honesty fields as batch_set_property." [658]
- Contract tests should pin the threshold boundary (19/20/21), the `undoable:false` + hint fields on all three tools, and the hint naming the  [659]
- Acceptance criterion: One shared const; no literal `20` outside it." [660]
- Acceptance criterion: All three batch tools return identical honesty-field shape (`undoable`, `hint`) — or a documented reason they differ." [661]
- Acceptance criterion: Tests updated in the same commit (rule testing)." [662]
- The addon's entire GDScript layer has zero automated tests." [663]
- Verification today is ~20 hand-run smoke scripts (godot/tests/*_smoke.gd, run manually / in the e2e.yml live-editor workflow)." [664]
- command_router.gd handles envelope validation, unknown-command handling, id stamping, the no-response catch-all, and cmd_run_commands batchi [665]
- type_coerce.gd handles all to_json/from_json shapes, string-form parsing, and error paths." [666]
- The fix proposes adding a headless GDScript test runner runnable from CI via a `godot --headless -s` script." [667]
- The fix proposes porting the pure-logic cases, starting with type_coerce round-trips and router envelope shapes." [668]
- The fix proposes wiring the harness into CI as a job that only runs when `godot/addons/**` changes, on the self-hosted runner alongside `e2e [669]
- Acceptance criteria require that type_coerce.gd and command_router.gd envelope logic have automated GDScript tests that run headless." [670]
- Acceptance criteria require CI to run the harness on addon changes." [671]
- Acceptance criteria require zero skips, with the enforcement suite health rule applying to the GDScript side." [672]
- Error codes returned by the addon are raw strings written by hand in approximately 30 handler files." [673]
- The authoritative set of error codes is the ErrorCode enum in mcp_server/models/envelope.py." [674]
- Nothing ties the addon error codes to the Python ErrorCode enum, so a typo'd or invented code would flow through to clients." [675]
- The proposed fix adds a const error-code registry on the GDScript side and uses it in _fail call sites." [676]
- The proposed fix adds a Python-side contract test that scans godot/addons/godot_mcp/**/*.gd for string literals passed as the first _fail(.. [677]
- The proposed contract test runs in the existing pytest suite and requires no editor." [678]
- The contract test direction alone pins the addon side without needing the GDScript test harness and fails CI when the surfaces drift." [679]
- An acceptance criterion is that a contract test fails CI when the addon emits an error code not in the Python enum." [680]
- An acceptance criterion is that all current call sites pass, with an audit for existing drift during implementation." [681]
- Issue #525 is in state CLOSED." [682]
- Issue #525 has labels Tests and component:addon." [683]
- The `_require_debug_session` guard is located at `command_router.gd:462-477` and checks for a play session, debugger, and valid session id." [684]
- The `_require_live_probe` guard is located at `command_router.gd:472-478` and checks for a play session, debugger, and probe connected." [685]
- `_cmd_get_game_scene_tree` at `runtime_session.gd:88-93` re-implements the live-probe guard inline with an enhanced hint (the #454 'max clie [686]
- `runtime_session._require_unpaused_live_probe()` (lines 20-29) chains `_require_live_probe` with a manual break-state check." [687]
- The proposed fix is to consolidate the guards into one guard module with composable guards (play-session, debugger-session, live-probe, unpa [688]
- The proposed fix is to move the rich probe-never-connected diagnostic from `runtime_session.gd:99-105` into the shared live-probe guard so e [689]
- An acceptance criterion is that there is one implementation of each guard and no handler re-implements precondition checks inline." [690]
- An acceptance criterion is that the #454 diagnostic ships from every probe-gated handler, pinned with a contract test." [691]
- An acceptance criterion is that existing handler behaviors remain unchanged otherwise." [692]
- Issue #527 is in CLOSED state." [693]
- Issue #527 has labels documentation and component:addon." [694]
- The `type_coerce.gd:9` class docstring says \"Read direction (Godot → JSON) only for now; from_json() lands with the mutation tools (#6).\"" [695]
- In `batch.gd`, the comment \"Edit one scene file on disk…\" is attached to `_node_summary` (line 98-100)." [696]
- In `batch.gd`, the comment \"Resolve batch targets…\" is attached to `_init` (line 109-110)." [697]
- In `batch.gd`, `_node_summary`'s own comment is on `_batch_targets`." [698]
- batch_set_property skips UndoRedo for operations above 20 nodes, returning undoable:false with a hint." [699]
- composite.gd's batch_create_nodes and apply_node_edits open a single UndoRedo action regardless of node count." [700]
- The hand-rolled add-child undo sequence is duplicated in three handlers: mutation._cmd_create_node, composite._cmd_compose_node, and composi [701]
- _commit_add_child already exists on the command router at command_router.gd:403 and is used by audio, particles, scene_3d, and navigation ha [702]
- The persistence-verdict stamping loop is copy-pasted between batch.gd:170-175 and composite.gd:220-225." [703]
- Proposed fix: add a composite variant that registers N children in one UndoRedo action." [704]
- Proposed fix: extract a _persistence_entries(nodes) helper for batch verdict stamping." [705]
- Proposed fix: add a shared threshold constant and honesty fields on composite tools, to land with the companion issue's fix." [706]
- Acceptance criterion: no handler hand-rolls the add-child undo sequence, and the composite N-child case uses one helper." [707]
- Acceptance criterion: verdict stamping has one implementation used by both batch and composite." [708]
- Acceptance criterion: envelope shapes pinned by existing tests pass unchanged." [709]
- Issue #529 is in OPEN state." [710]
- Undo parity is incomplete: `godot_undo` exists in core as `cmd_undo` (command_router.gd:251-275), but there is no `godot_redo`." [711]
- `godot_redo` is classified as `mutating` with dry_run, like `godot_undo`." [712]
- `godot_list_history` is classified as `read_only`." [713]
- Acceptance criterion: `godot_redo` mirrors `godot_undo`'s envelope and honesty shape, verified by a contract test." [714]
- Acceptance criterion: `godot_list_history` returns the documented fields, and empty history returns zero-values rather than errors." [715]
- The plugin declares `_server_version` at godot_mcp.gd:36 that nothing ever assigns." [716]
- When server/addon versions drift, the failure mode is opaque per-command `VALIDATION_ERROR: Unknown command 'cmd_x'` with no version context [717]
- The proposed addon command `cmd_get_addon_info` returns `{ addon_version, godot_version, commands: [all registered cmd_* names] }`." [718]
- The addon version source is `plugin.cfg` or a const set at release." [719]
- The server calls `cmd_get_addon_info` once on first successful `cmd_ping` (or lazily on first command) and caches it." [720]
- The server pushes `server_version` back to the addon, assigning the dock's `_server_version` and resolving #521." [721]
- The server exposes the addon info via `godot_get_server_info`, adding `addon_version`, `godot_version`, and `addon_commands` to the capabili [722]
- The server warns (structured, not stack trace) when the addon lacks handlers for tools the server exposes, enabling version-drift detection. [723]
- A contract test pins the handshake envelope." [724]
- The addon can instance a saved scene into the tree via the `scene_edit_instance_scene` tool." [725]
- The proposed tool is named `godot_scene_edit_extract_scene` with category `scene_edit` and safety `mutating`." [726]
- The proposed tool's parameters include `node_path`, `scene_path` (destination `res://`), `replace_with_instance: bool = false`, `save_curren [727]
- If `replace_with_instance` is true, the proposed tool performs one UndoRedo action that removes the original subtree and instances the new ` [728]
- The proposed tool refuses when the subtree contains nodes owned by an instanced child that isn't editable, providing a hint rather than sile [729]
- The proposed tool's `dry_run` reports the node list that would be extracted plus the destination path." [730]
- An acceptance criterion is that both sides plus contract tests for the envelope are provided." [731]
- An acceptance criterion is that the tool is undoable, `confirm`-free (additive, `mutating` class), but honors `dry_run`." [732]
- An acceptance criterion is that the tool refuses non-owned/instanced subtrees with an actionable hint, consistent with #477 rename refusals. [733]
- The proposed tool godot_project_move_file has toolset project, safety mutating, and dry_run." [734]
- Godot 4.4+ exposes the editor's rename machinery (EditorInterface/EditorFileSystem + ResourceUID)." [735]
- The proposed response format is { old_path, new_path, updated_refs: [{file, count}] } plus a dry_run preview listing which referencing files [736]
- Acceptance criteria include structured refusals for the three precondition cases." [737]
- Acceptance criteria include docs and a tool-contract entry with toolset project." [738]
- Issue #533 is in OPEN state and labeled enhancement, component:addon." [739]
- The proposed tool godot_core_describe_class belongs to toolset core, is read_only, and needs no bridge precondition beyond being connected." [740]
- The proposed tool takes parameters class_name, include_inherited (bool, default false), and include_private (bool, default false)." [741]
- The properties field is produced via ClassDB.class_get_property_default_value plus class_get_property_list, yielding name, Variant.Type name [742]
- The methods field is produced via class_get_method_list, yielding name, args (name and type), and return_type." [743]
- An acceptance criterion requires a GDScript handler plus FastMCP tool with typed Pydantic response and a contract test that pins the envelop [744]
- An acceptance criterion requires that an unknown class returns VALIDATION_ERROR with a did-you-mean suggestion over the ClassDB class list." [745]
- The proposed server tool godot_runtime_get_output is read_only, gated by _require_live_probe, returns { stdout, errors, warnings, truncated  [746]
- An acceptance criterion requires ring-buffer capture with a seq cursor and no unbounded growth across long sessions." [747]
- An acceptance criterion requires a godot_runtime_get_output contract test (poll-and-cache envelope) plus a live e2e smoke in e2e.yml style." [748]
- The output ring buffer lives in the addon while the MCP server stays stateless." [749]
- Issue #534 is in state OPEN." [750]
- An acceptance criterion requires both sides to be implemented with snapshots that are JSON-safe and depth-capped." [751]
- An acceptance criterion requires contract tests pinning both envelopes and a bounded store with no unbounded server memory." [752]
- Duplicates are not queued: consecutive identical values are collapsed (probe smoke test in `godot/tests/`)." [753]
- Contract test pins the new param through the envelope." [754]
- Issue #536 is OPEN." [755]
- Issue #536 has labels enhancement, component:addon." [756]
- The bridge accepts only one active peer connection at a time." [757]
- The proposed handshake has the addon send a hello containing project_path, godot_version, and addon_version on connect." [758]
- The proposed server behavior keeps the most recent peer while exposing the connected editor's project_path in godot_get_server_info." [759]
- The proposal logs a structured line naming both project paths when a second peer joins." [760]
- The proposal optionally includes previous_peer in the server info snapshot." [761]
- Acceptance criterion: the connected editor's project path is visible via godot_get_server_info or a resource." [762]
- Acceptance criterion: peer replacement produces a structured log entry with both project paths rather than silence." [763]
- The bridge is localhost-only with no authentication in v1." [764]
- Anything on localhost can currently inject command envelopes into the bridge." [765]
- The proposed opt-in token is a GODOT_MCP_BRIDGE_TOKEN env var read on both sides, mirroring existing GODOT_MCP_BRIDGE_URL handling in godot_ [766]
- The server listener refuses non-authenticated peers with a VALIDATION_ERROR-family envelope and drops them." [767]
- The token must never be logged and must be documented in docs/site/reference-env-vars.md and the security-model section." [768]
- An acceptance criterion requires the both-unset path to be byte-identical to today with contract tests unchanged." [769]
- Issue #539 is in the OPEN state." [770]
- Issue #539 has labels enhancement and component:addon." [771]
- The function godot_mcp._update_button_icon is located at godot_mcp.gd:169-183." [772]
- godot_mcp._update_button_icon regenerates a 16×16 ImageTexture pixel-by-pixel using 256 set_pixel calls plus Image.create_empty and ImageTex [773]
- An acceptance criterion is that there is one texture per status, built once." [774]
- An acceptance criterion is that behavior is visually unchanged and there is no allocation in the status-change path." [775]
- MCPCommandRouter._prop_cache maps get_instance_id() to a property-type dict and is pruned by size with a 256 cap and full clear." [776]
- A freed node's cache entry can be served for a new object with the same id, returning stale property types for properties that do not exist  [777]
- _invalidate_prop_cache is only called by batch/composite apply paths." [778]
- A node deleted via cmd_delete_node leaves a stale cache entry until cap prune or id reuse." [779]
- The proposed fix keys cache validity on ObjectID plus liveness, refreshing when the cached object id is a miss or when instance_from_id(obj_ [780]
- The proposed hardening calls _invalidate_prop_cache in cmd_delete_node, rename, and batch-apply completion paths." [781]
- An alternative proposed fix keys the cache by WeakRef/ObjectID and validates is_instance_valid on hit with a one-line guard in _property_typ [782]
- An acceptance criterion requires that a stale entry cannot survive a freed/reused instance id, unit-tested headlessly." [783]
- An acceptance criterion requires that the delete path invalidates the target's cache entry." [784]
- PR #497 was merged on 2026-09-17." [785]
- The addon adds a new read-only cmd_get_scan_state command returning {scanning: bool} from EditorFileSystem.is_scanning()." [786]
- Contract tests pin the poll ordering, the quiet path, and the stuck path." [787]
- Both new contract tests fail without the cmd_get_scan_state poll / rescan_pending field (red-first)." [788]
- is_scanning() was verified live on Godot 4.7.2 (true during the initial scan, false once quiet) and the addon loads clean." [789]
- Full preflight passed with 800 tests passed, ruff, mypy, zero-skip, and green integration smokes." [790]
- docs/tool-contracts.md was updated with the result schema and a determinism paragraph." [791]
- PR #498 was merged on 2026-09-17." [792]
- batch_set_property already skipped EditorUndoRedoManager above 20 nodes as a performance guard, but the response did not indicate this." [793]
- batch_set_property now reports undoable: false with a hint for >20-node batches and undoable: true explicitly for ≤20-node batches." [794]
- Contract tests pin both new reporting behaviors." [795]
- docs/tool-contracts.md was updated." [796]
- The PR closes issue #437." [797]
- Live e2e tests against Godot 4.7.2 verified a 25-node batch yields undoable:false with hint, an aborted run_commands yields aborted_at=0 and [798]
- Full preflight passed 803 tests with ruff, mypy, and zero-skip." [799]
- PR #499 was merged on 2026-09-17 and carries the documentation label." [800]
- Calling `create_scene(root_type=\"Collectible\")` on a registered custom `class_name` fails with `VALIDATION_ERROR: Unknown or non-instantia [801]
- The `root_type` limitation is stated in the `godot_scene_edit_create_scene` tool description." [802]
- The `root_type` limitation is stated in `docs/tool-contracts.md` along with the create-then-attach_script workaround." [803]
- The documented workaround is to create the scene with a base type and then call `attach_script`." [804]
- The change to `mcp_server/tools/mutation.py` added 4 lines and removed 0 lines." [805]
- The change to `docs/tool-contracts.md` added 6 lines and removed 0 lines." [806]
- The PR is docs-only and the ruff, mypy, and contract suites pass with zero skips." [807]
- Issue #429 is assessed as partially compliant, with the PR choosing the documentation option." [808]
- The PR reviewer guide assigns an estimated review effort of 1 and a score of 95." [809]
- PR #500 is a CalVer release bump from 2026.09.10 to 2026.09.17." [810]
- PR #500 was merged on 2026-09-17." [811]
- The release is additive-only since the last tag, so CONTRACT_VERSION stays at 1." [812]
- The version bump is applied in lockstep across pyproject.toml, mcp_server/__init__.py, godot/addons/godot_mcp/plugin.cfg, README, and skills [813]
- mcp_server/__init__.py was modified to bump the Python package version." [814]
- godot/addons/godot_mcp/plugin.cfg was modified to bump the Godot addon version." [815]
- pyproject.toml was modified to bump the Python project version." [816]
- Issue #490 is rated partially compliant because the PR is a version bump only with no code changes to debug_workflow.py." [817]
- PR #501 was merged on 2026-09-18." [818]
- Setting undoable: false on batches of more than 20 nodes means undo will not revert the change." [819]
- set_setting performs key validation and returns a did-you-mean hint." [820]
- Verification of the change showed tests/unit/test_skills_metadata.py green and the full suite at 803 passed with ruff/mypy/zero-skip clean." [821]
- AGENTS.md was changed by +5/-2 lines." [822]
- The PR reviewer guide rated the PR with a score of 92 and an estimated review effort of 2." [823]
- PR #502 updates the tool count to 181 in documentation." [824]
- PR #502 is merged as of 2026-09-18." [825]
- PR #502 has the documentation label." [826]
- The 180 count was stale in README (×3), AGENTS.md, skills/README, and godot-getting-started." [827]
- The PR type is Documentation." [828]
- AGENTS.md updated the tool count from 180 to 181 in the \"Current state\" section." [829]
- README.md updated the tool count from 180 to 181 in three locations." [830]
- skills/README.md updated the tool count from 180 to 181 in the skills documentation." [831]
- skills/godot-getting-started/SKILL.md updated the tool count from 180 to 181 in the getting started skill." [832]
- The estimated effort to review PR #502 is 1." [833]
- PR #503 is merged as of 2026-09-18." [834]
- PR #503 has labels enhancement, Review effort 3/5, and Bug fix." [835]
- `batch_set_property` and `apply_node_edits` now carry a `persistence[]` array with one `{node_path, persisted, reason?, hint?}` per applied/ [836]
- The addon compiles clean on Godot 4.7, and full preflight is green with 807 passed and ruff/mypy/zero-skip." [837]
- PR #504 was merged on 2026-09-18." [838]
- The godot_scene_edit_set_editable_children tool is mutating, UndoRedo-wrapped, and toggles Editable Children on an instanced scene." [839]
- The set_editable_children tool refuses local nodes, which would otherwise be a silent no-op." [840]
- Instanced nodes' children carry an `owner` field holding the source scene's res:// path and `editable_children: true` when the toggle is on. [841]
- Local nodes carry neither the `owner` nor the `editable_children` key in the serialized tree." [842]
- The PR updates docs/tool-contracts.md with a tool row and the SceneNode shape." [843]
- The preflight run passed with 811 tests and clean ruff/mypy/zero-skip checks." [844]
- Issue #487 is rated partially compliant, with auto-enabling editable children when an agent creates a second instance of the same PackedScen [845]
- PR #505 was merged on 2026-09-18." [846]
- PR #505 implements issue #459, generalizing #457's capture-path pattern." [847]
- A shared reason-token table was added to `docs/tool-contracts.md`." [848]
- The addition is additive, so `CONTRACT_VERSION` stays 1." [849]
- The addon compiles clean on Godot 4.7." [850]
- Full preflight passed with 813 tests, ruff, mypy, and zero-skip." [851]
- PR #506 was merged on 2026-09-18." [852]
- PR #506 carries the labels enhancement and Tests." [853]
- The addon's layout read now echoes each effect's exported property values using a PROPERTY_USAGE_EDITOR filter with values JSON-coerced via  [854]
- AudioBusEffectInfo gains a properties field of type dict[str, Any], an additive change that keeps contract_version at 1." [855]
- A red-first contract test named test_get_bus_layout_echoes_effect_properties was added, and the full preflight run reported 814 passed with  [856]
- The handler file godot/addons/godot_mcp/handlers/audio.gd was changed by +11/-0 lines." [857]
- PR #507 was merged on 2026-09-18." [858]
- The new godot_shader_validate tool is read_only, belongs to the shader toolset, and runs the shader through a real headless engine compile." [859]
- The throwaway runner and its .uid sidecar are deleted after the run." [860]
- Live on Godot 4.7.2, the issue's exact repro (uniform float edge_width : float) returned ok:false with the error \"Expected valid type hint  [861]
- The full preflight run passed 816 tests with ruff, mypy, and zero skips." [862]
- PR #508, titled \"Add AudioStreamWAV loop settings to import_asset\", was merged on 2026-09-19." [863]
- import_asset accepts loop configuration for .wav targets via options.import_settings with keys loop_mode, loop_begin, and loop_end." [864]
- The handler patches the .import sidecar's edit/loop_* params (ResourceImporterWAV's option keys) and queues a reimport." [865]
- The loop_applied field in the result reports whether the config was applied this call, and being additive the contract_version stays 1." [866]
- Live verification on Godot 4.7.2 showed importing a .wav with loop_mode: 1 yields loop_applied: true and the .import sidecar carries edit/lo [867]
- A red-first contract test named test_import_wav_loop_mode_applied was added, and the full preflight run passed 817 tests with ruff, mypy, an [868]
- The addon file import_asset.gd adds a _set_wav_loop function that patches the .import sidecar." [869]
- Issue 418 was assessed as partially compliant by the PR review." [870]
- PR #509 was merged on 2026-09-19." [871]
- The new tool `godot_scene_edit_rescan_filesystem` is registered with the `read_only` safety class in the scene_edit toolset." [872]
- The tool triggers `EditorFileSystem.scan()` so external edits to `.tscn`/`.gd` files are picked up by the editor without manual close/reopen [873]
- `reload_scene` discards unsaved changes and remains confirm-gated, unlike the new scan." [874]
- Live verification on Godot 4.7.2 via the bridge showed an externally written `.gd` file appearing in the editor's filesystem tree after `res [875]
- The full preflight run passed 819 tests with ruff, mypy, and zero skips." [876]
- `mcp_server/command_map.py` added a mapping from `scene_edit_rescan_filesystem` to `cmd_rescan_filesystem` (+1/-0)." [877]
- `mcp_server/models/scene_session.py` added a `RescanFilesystemResult` Pydantic model with `scanned` and `scanning` fields (+7/-0)." [878]
- The addon handler `cmd_rescan_filesystem` calls `EditorFileSystem.scan()` and returns status." [879]
- PR #510 was merged on 2026-09-19." [880]
- The release bumps the CalVer version from 2026.09.17 to 2026.09.19." [881]
- The change is additive-only since the last tag and CONTRACT_VERSION remains 1." [882]
- The tool surface grows from 181 to 184 tools, adding set_editable_children, validate_shader, and rescan_filesystem." [883]
- PR #510 carries the labels documentation, enhancement, and Review effort 1/5." [884]
- The PR syncs version strings across docs and config." [885]
- Ticket #458 was assessed as partially compliant with no compliant requirements." [886]
- The estimated effort to review PR #510 is 1 out of 5." [887]
- The PR review score is 95." [888]
- The review reports no relevant tests for the PR." [889]
- PR #511 adds a MkDocs documentation site and GitHub Pages deployment." [890]
- PR #511 was merged on 2026-09-19." [891]
- The documentation site uses MkDocs Material and is hosted at https://hybridindie.github.io/godot-mcp/." [892]
- The PR adds 17 new documentation pages." [893]
- The architecture deep-dive consists of 7 pages." [894]
- The getting started section consists of 5 pages." [895]
- The guides section consists of 3 pages." [896]
- Verification showed a clean `mkdocs build --strict`, rendering of mermaid diagrams and all 29 toolset tables, and a full repo preflight with [897]
- PR #512 titled \"Fix docs toolchain installation in CI\" was merged on 2026-09-19." [898]
- The PR is labeled as a Bug fix." [899]
- The PR modified the file .github/workflows/pages.yml." [900]
- The pages.yml change consists of 5 additions and 3 deletions." [901]
- The automated PR review estimated the effort to review as 1 out of 5." [902]
- The automated PR review assigned a score of 95." [903]
- PR #513 is titled \"Add LLM-friendly documentation endpoints and promote site\"." [904]
- PR #513 was merged on 2026-09-19." [905]
- PR #513 carries the labels documentation and enhancement." [906]
- `/llms.txt` (page index) and `/llms-full.txt` (whole site as one markdown document, ~1800 lines) are generated at build time via the `mkdocs [907]
- The PR promotes the documentation site across README, AGENTS.md, skills/README, CONTRIBUTING, and docs/reference/index.md." [908]
- `mkdocs-llmstxt>=0.2,<0.4` is pinned in `requirements-docs.txt` and added to the pages workflow's toolchain install." [909]
- `mkdocs build --strict` runs clean with the plugin and both `llms.txt` and `llms-full.txt` are produced with correct sections." [910]
- The full repo preflight reported 819 passed with ruff, mypy, and zero-skip." [911]
- The PR review scored the change 92." [912]
- The review found no relevant tests, no security concerns, and no TODO sections." [913]
- The `mkdocs-exclude` plugin is installed in the CI workflow and `requirements-docs.txt` but is not listed in the `plugins` section of `mkdoc [914]
- PR #514 ports the documentation site from MkDocs to the same VitePress tooling, layout, and page conventions as the wiki-fabric project." [915]
- PR #514 was merged on 2026-09-19." [916]
- docs/site/llms-gen.mjs runs as a post-build step and generates llms.txt and llms-full.txt into dist/." [917]
- The mkdocs pages.yml and mkdocs.yml/requirements-docs.txt files are removed by this PR." [918]
- All 27 content pages were migrated with cross-links verified by VitePress's dead-link checker with ignoreDeadLinks set to false." [919]
- npm run build exits zero with zero dead links and generates dist/llms.txt and dist/llms-full.txt with correct sections and URLs." [920]
- PR #514 carries the labels documentation and enhancement." [921]
- PR #515 was merged on 2026-09-19." [922]
- VitePress without `cleanUrls` renders `what-why.html`." [923]
- Every deep link in llms.txt was a 404." [924]
- The URL mapping was fixed to match what VitePress actually serves." [925]
- The llms-full.txt content was unaffected because it is raw markdown." [926]
- The PR modified docs/site/llms-gen.mjs." [927]
- The URL mapping was fixed to match VitePress default rendering behavior." [928]
- No relevant tests were found for the PR." [929]
- PR #516 was merged on 2026-09-19." [930]
- PR #516 carries the documentation label." [931]
- 27 per-page markdown variants are generated by llms-gen.mjs with frontmatter stripped." [932]
- Every rendered page's head carries a describedby link to llms.txt and an alternate link to that page's .html.md variant." [933]
- llms.txt follows the exact v2 file format: H1, blockquote, details, H2 file lists with ': notes', and an Optional section for secondary link [934]
- Local build verification produced dist/llms.txt, dist/llms-full.txt, and 27 *.html.md variants with link rel=describedby/alternate present i [935]
- Full repo preflight reported 819 passed with ruff, mypy, and zero-skip." [936]
- robots.txt was added with comments pointing agents to llms.txt, .html.md variants, and llms-full.txt." [937]
- The PR introduces significant new behavior (27 page.html.md variants, llms.txt v2 format, discovery links) but adds no tests." [938]
- PR #517 is in MERGED state, having been merged on 2026-09-19." [939]
- Sidebar, index pages, and llms-gen.mjs sections were updated so the new pages flow into llms.txt/llms-full.txt automatically." [940]
- Running `npm run build` produced zero dead links, with new pages and .html.md variants present in dist/ and the llms index carrying the new  [941]
- The PR-Agent review scored the PR 95." [942]
- PR #518 was merged on 2026-09-19." [943]
- VitePress only dead-link-checks markdown body links, allowing 13 config links to ship 404s silently." [944]
- All 16 stale config links were rewritten to the real flat page names, with architecture/* kept because those genuinely live in the subdirect [945]
- A new guard script docs/site/check-links.mjs is chained into npm run build." [946]
- npm run build exits zero and prints 'checked 32 nav/sidebar links: all resolve'." [947]
- The check-links.mjs file change was +31/-0 lines." [948]
- A reviewer noted the regex /link: '([^']+)'/g only matches single-quoted link values, so double-quoted nav/sidebar entries would be silently [949]
- PR #519 was merged on 2026-09-19." [950]
- PR #519 fixes dead nav/sidebar links in the VitePress config." [951]
- All 13 stale subdirectory links in .vitepress/config.mts were rewritten to flat page names." [952]
- After npm run build, dist/concepts.html contains 0 occurrences of the old getting-started/install path and 1 occurrence of the correct getti [953]
- The link guard passes with 32 nav/sidebar links resolving." [954]
- Architecture/* links were kept because those pages genuinely live in the subdirectory." [955]
- The guard check-links.mjs is not included in PR #519's diff because it was already merged in #518." [956]
- PR #519 rewrites 13 links to flat paths but does not include the corresponding .md source files in the diff." [957]
- PR #541 adds a contract test that source-scans GDScript addon files and asserts every error-code literal emitted at `_fail(...)` call sites  [958]
- The scan was verified to turn red on an injected `NOT_A_REAL_CODE` before committing." [959]
- Running `uv run pytest tests/contract/test_addon_error_codes.py` produced 2 passed." [960]
- The full test suite reported 821 passed with zero skips." [961]
- PR #541 was merged on 2026-09-20." [962]
- The test file `test_addon_error_codes.py` was added with a diff of +92/-0 lines." [963]
- The reviewer noted the `_FAIL_CALL` regex only matches `_fail(\"CODE\", ...)` where the code is a direct string literal, so variable or cons [964]
- All 338 audited call sites pass error codes as string literals, with no variable or const code references existing today." [965]
- PR #542 was merged on 2026-09-20." [966]
- The new file godot/tests/type_coerce_smoke.gd contains 34 headless checks pinning the full coercion shape table against the real Godot runti [967]
- godot/tests/run_commands_smoke.gd was extended to cover the #461 honest-abort contract including aborted_at/skipped_count/hint on halt, the  [968]
- tests/integration/test_addon_read_smokes.py registers type_coerce_smoke in the pytest parameter list so it runs headless in CI wherever a Go [969]
- The implementation chose the repo's existing headless SceneTree exerciser plus pytest runner pattern over adding GUT, because GUT is not ins [970]
- The tests have zero skips and run on any machine with Godot 4.4+." [971]
- Running godot --headless --path godot/ --script res://tests/type_coerce_smoke.gd produced TYPE_COERCE_TEST_OK." [972]
- Running uv run pytest tests/integration/test_addon_read_smokes.py resulted in 8 passed." [973]
- The full test suite reported 822 passed with zero skips, and ruff plus mypy were clean." [974]
- tests/contract/test_addon_error_codes.py adds a contract test ensuring addon error codes are a subset of the Python ErrorCode enum." [975]
- The PR review found that a CI job running when godot/addons/** changes was not added in this PR." [976]
- PR #543 implements the server↔addon handshake from issue #530, closing #521 as a side effect." [977]
- cmd_get_addon_info self-describes with addon_version (live from plugin.cfg, single source), godot_version, and the live registered-command l [978]
- cmd_server_hello {version} stores the server's pushed package version in router.server_version, which the plugin entry reflects on the next  [979]
- The first successful handshake fire-and-forgets cmd_server_hello {version: __version__}, best-effort ignoring an old addon's 'Unknown comman [980]
- BridgeDiagnostics gains addon_version/addon_commands and ServerDiagnostics gains addon_drift_warning." [981]
- A server↔addon version mismatch surfaces in godot_get_server_info as an addon_drift_warning string naming the count of unregistered commands [982]
- The headless handshake smoke test run via godot --headless --script res://tests/handshake_smoke.gd returns HANDSHAKE_TEST_OK." [983]
- tests/contract/test_addon_handshake.py reports 10 passed covering shape, caching, degrade, and drift." [984]
- The full test suite reports 832 passed with zero skips and ruff + mypy clean." [985]
- The addon_info method was not protected by a lock, so two concurrent first calls could both send cmd_get_addon_info and cmd_server_hello, vi [986]
- The race was fixed in commit c6d46e5 by taking _addon_info_lock only while the cache is empty (double-checked), so N concurrent first calls  [987]
- PR #544 was merged on 2026-09-20." [988]
- Three drifted guard flavors were consolidated into one module, godot/addons/godot_mcp/mcp_guards.gd (MCPGuards)." [989]
- The #454 \"max client limits reached\" recovery diagnostic now ships from every probe-gated handler, not just get_game_scene_tree." [990]
- get_game_scene_tree deliberately keeps its soft {playing, connected: false, probe_never_connected} result, consuming only the hint text from [991]
- The contract test tests/contract/test_addon_guards.py passed 5 tests." [992]
- Running godot --headless --path godot/ --script res://tests/guards_smoke.gd produced GUARDS_TEST_OK covering both branches via the oracle." [993]
- The contract and unit suites reported 781 passed with zero skips, and ruff plus mypy were clean." [994]
- The PR reviewer bot assessed ticket #527 as partially compliant." [995]
- PR #545 was merged on 2026-09-20." [996]
- command_router.gd defines a single shared constant MCP_UNDO_THRESHOLD := 20 plus the helper functions _undoable_for_count(count) and _undo_t [997]
- Before this PR, composite.gd's batch_create_nodes and apply_node_edits had no UndoRedo threshold, so a 500-node batch create opened one gian [998]
- In composite.gd both batch tools became threshold-aware: above the threshold they bypass UndoRedo via direct set and report the same undoabl [999]
- Running threshold_smoke.gd headless produced THRESHOLD_TEST_OK covering boundaries 19/20/21/500, hint wording, and the applies-noun variant. [1000]
- The full test suite at the time of the PR description reported 844 passed with zero skips and clean ruff and mypy." [1001]
- Review found that BatchCreateNodesResult previously had a dry_run: bool = False field that was removed in this PR while ApplyNodeEditsResult [1002]
- BatchCreateNodesResult regained the dry_run: bool = False field, and the server-side preview dict also carries the new undoable/hint default [1003]
- Both _cmd_batch_create_nodes and _cmd_apply_node_edits now check params.get(\"dry_run\") and return a preview-shaped result without touching [1004]
- After the fixes, the full suite reported 846 passed with zero skips and clean ruff and mypy, with threshold_smoke and run_commands smoke re- [1005]
- PR #546 was merged on 2026-09-20." [1006]
- The router was approximately 816 lines before the refactor." [1007]
- About two-thirds of the router was boilerplate and a helpers grab-bag." [1008]
- command_router.gd was reduced from 816 to 479 lines." [1009]
- Shared-logic call sites changed from `_router._X` to `_router._helpers.X`." [1010]
- tests/contract/test_router_refactor.py has 5 passing tests." [1011]
- The full test suite reported 852 passed with zero skips." [1012]
- The editor pulls game output on demand via godot_mcp:get_output → godot_mcp:game_output using a poll-and-cache pattern with no unsolicited p [1013]
- The server tool godot_runtime_get_game_output is read_only in the runtime toolset and returns a GameOutputResult with a monotonic seq cursor [1014]
- godot-mcp is a standalone MCP server providing generic Godot editor control over the Model Context Protocol, usable by any AI agent harness  [1015]
- The Godot editor dials the bridge connection and reconnects, while the server still initiates every command." [1016]
- The MCP server owns all safety/permission logic and Pydantic domain models and holds no Godot logic itself." [1017]
- The Godot addon is a GDScript EditorPlugin (Godot 4.4+) whose WebSocketPeer client connects out to the server's bridge listener and reconnec [1018]
- Every tool is tagged with a safety class (read_only, mutating, destructive, or runtime), where mutating/destructive tools take dry_run: bool [1019]
- Every MCP tool is exposed as godot_<toolset>_<action>, with the mapping applied centrally in mcp_server/transforms.py via FastMCP 4.0's Tool [1020]
- The toolchain requires Godot 4.4+ (validated on 4.7-stable), Python 3.11+, and FastMCP 4.0.1, managed with uv." [1021]
- godot-mcp is a standalone MCP server that drives a live Godot editor from AI agents." [1022]
- godot-mcp requires Python 3.11+ managed with uv." [1023]
- godot-mcp requires Godot 4.4+ and is validated on 4.7-stable." [1024]
- godot-mcp uses FastMCP 4.0.1, which is GA on MCP SDK v2 (the 2026-07-28 sessionless protocol)." [1025]
- The workflow is an issue-driven pipeline in which every merge traces to a GitHub issue." [1026]
- godot-mcp is composed of an AI client connected via stdio to a FastMCP Python server, which connects via WebSocket to a GDScript Godot addon [1027]
- The MCP server owns all safety/permission logic, Pydantic models, and tool schemas, and never touches Godot directly." [1028]
- The Godot addon is the only layer that touches the Godot Editor API and routes commands to cmd_* handlers." [1029]
- Every tool is tagged with one of four safety classes: read_only, mutating, destructive, or runtime." [1030]
- Releases are automated via .github/workflows/publish.yml and triggered on GitHub release publish." [1031]
- The Godot editor dials the WebSocket connection and the MCP server listens, but the server still drives every command, decoupling the two di [1032]
- The MCP server is a FastMCP server implemented in Python under mcp_server/." [1033]
- The Godot addon is written in GDScript with the @tool annotation and lives in addons/godot_mcp/." [1034]
- mcp_bridge.gd is the WebSocket client that connects to a URL and reconnects with backoff." [1035]
- The addon dials out to the server at ws://127.0.0.1:9080." [1036]
- The MCP server boots, binds port 9080, and waits for the addon to connect." [1037]
- The server owns all safety and preconditions while the addon owns all Godot calls, with neither crossing the seam." [1038]
- The AI client communicates with the MCP server over stdio using the MCP protocol." [1039]
- The bridge connection direction is inverted so that the server listens and the Godot editor connects out." [1040]
- The bridge URL defaults to ws://127.0.0.1:9080, is configurable on both sides via the GODOT_MCP_BRIDGE_URL env var, and is localhost-only wi [1041]
- Error codes must be stable and drawn only from the enumerated set, never ad-hoc strings." [1042]
- Godot types cross the bridge as JSON-safe forms coerced on the addon side in the dedicated type_coerce.gd helper (MCPTypeCoerce), never inli [1043]
- To inspect or drive a running game, the game must be launched from the editor so it connects back to the editor's remote debugger." [1044]
- The Godot editor-to-game debugger protocol supports step control, stack-frame inspection, and expression evaluation over the same EditorDebu [1045]
- A Tier 2 debugger toolset (step_*, continue, godot_debugger_get_stack_frames, godot_debugger_evaluate_expression) is implementable with no e [1046]
- The Godot editor is single-threaded: the addon drains queued command packets once per _process frame and executes them serially on the main  [1047]
- The server cannot parallelize past the single-threaded editor, so the only levers are fatter commands and fewer commands." [1048]
- godot_composite_run_commands executes a whole list of N commands in a single frame and returns one envelope per command, collapsing N round- [1049]
- Each sub-mutation in a composite batch wraps its own UndoRedo action and command order is preserved." [1050]
- godot_composite_run_commands cannot be nested." [1051]
- The MCP spec's 2026-07-28 revision removes sessions and the initialize handshake entirely." [1052]
- The 2026-07-28 revision defines a stateless protocol with no session lifecycle and no server-initiated requests riding a session back-channe [1053]
- In the 2026-07-28 revision, per-request `_meta` carries version/capabilities instead of handshake negotiation." [1054]
- Cross-call state in the 2026-07-28 revision moves to explicit handles: server-minted tokens passed as ordinary tool arguments." [1055]
- The 2026-07-28 revision replaces handshake capability probing with `server/discover`." [1056]
- godot-mcp is pinned to FastMCP 4.0.0b3 which speaks 2025-era session semantics, but FastMCP 4.0's Client negotiates sessionless by default,  [1057]
- Toolset enable/disable in ToolsetMiddleware has no session dependency and uses a single server-global enabled set (#364)." [1058]
- The destructive-tool approval guard in ApprovalMiddleware has no session dependency, using an InputRequiredResult plus request_state round-t [1059]
- The design decision rejects a session_handle/toolset_grant token because godot-mcp is a single-user, local server where a server-global enab [1060]
- Every @mcp.tool takes typed parameters and returns a typed Pydantic model, never a raw dict." [1061]
- Every @mcp.tool validates inputs and checks preconditions before any side effect." [1062]
- Every @mcp.tool is delegation only, with no domain branching in the handler body." [1063]
- Mutating tools must accept a dry_run boolean parameter defaulting to False." [1064]
- Destructive tools must accept dry_run and require a confirm boolean parameter defaulting to True." [1065]
- dry_run=True returns what would happen and performs nothing." [1066]
- All safety logic lives in mcp_server/safety.py and never in the addon." [1067]
- An optional webhook gates destructive tools behind a human decision and is opt-in: with no webhook configured the gate auto-approves." [1068]
- The approval gate runs at the tools/call boundary via ApprovalMiddleware (issue #330), with no per-tool wiring; any tool tagged destructive  [1069]
- godot-mcp requires Godot 4.4+, uv, and the godot-mcp addon enabled in the project." [1070]
- Every time the MCP client connects, the server sends initialization instructions that explain the gating system." [1071]
- The mandatory protocol is to call godot_get_server_info(), godot_list_toolsets(), and godot_enable_toolset(category) before calling tools in [1072]
- The server exposes workflow prompts that the LLM can discover and use." [1073]
- The LLM can discover prompts via list_prompts() and render them via get_prompt(name) or render_prompt(name)." [1074]
- If an MCP client does not surface server instructions or prompts, a system prompt template can be pasted into the first message to teach the [1075]
- If you get 'ToolError: unknown tool', the toolset is not enabled and you should call godot_enable_toolset first." [1076]
- The current release version is 2026.09.10, described as the first stable release." [1077]
- Godot 4.4 is the minimum supported version and 4.7 is the recommended validated target." [1078]
- Python 3.11 is the minimum supported version and 3.13 is recommended." [1079]
- The server listens on http://localhost:9090 for MCP HTTP and ws://localhost:9080 for the bridge." [1080]
- The Godot addon connects out to the MCP server's bridge listener at ws://127.0.0.1:9080 by default and reconnects automatically." [1081]
- The full pytest suite contains approximately 304 tests." [1082]
- The addon's command router handles 80+ cmd_* commands that call the Godot Editor API." [1083]
- The bridge to the editor is a single connection that only one server process can own at a time." [1084]
- Destructive-class tools require both dry_run and confirm: bool = True parameters." [1085]
- The repository generates AI assistant harnesses for `.claude/`, `.github/`, and `.opencode/` from a single set of shared constitutional arti [1086]
- The repository hosts the Epic Scoping Skills as its own installed harness." [1087]
- The Genesis harness renders `templates/_shared/` into target projects via `bootstrap.sh` and contains constitutional articles, agents, comma [1088]
- The Epic Scoping Skills system uses `.agents/` as its source directory with thin wrappers in `.claude/`, `.opencode/`, and `.github/`, conta [1089]
- The golden rule prohibits duplicating content into a wrapper; content must be edited in `.agents/` or `templates/_shared/`, and only frontma [1090]
- Shared rules referenced by multiple files live in a `doctrine/` layer and must be referenced rather than restated." [1091]
- On-demand reference sections in the repository are not auto-loaded and must be read explicitly when needed." [1092]
- The post-bootstrap flow proceeds as `bootstrap.sh` (render) → `/harness-eval` (trim + suggest) → `/customize-harness` (domain tailoring)." [1093]
- Each skill wrapper is a thin pointer; the model reads the `.agents/` body on-demand only when the skill is invoked." [1094]
- Doctrine files located at `.agents/doctrine/` are read on-demand when a skill references them." [1095]
- The shared, tool-agnostic project context (repo description, genesis bootstrap, source structure, Epic Scoping Skills) is defined in AGENTS. [1096]
- Only Claude-Code-specific notes belong in CLAUDE.md; all other shared context is delegated to AGENTS.md." [1097]
- Claude-specific harness assets (skills, hooks, scripts) are stored under the path templates/claude-code/.claude/." [1098]
- The Claude-specific harness assets are generated output mirrored from templates/_shared/, not authored independently." [1099]
- The Drift policy defined in AGENTS.md must be consulted before editing the mirrored Claude-specific harness assets." [1100]
- The primitive drift check is implemented as a Claude Code hook invoking the script templates/claude-code/.claude/hooks/check-primitive-drift [1101]
- The drift check script must be run from the repository root with a bootstrapped harness in scope." [1102]
- The CONTRIBUTING-HARNESS.md file is an editing contract for the repo that is not auto-loaded into sessions and must be opened on demand when [1103]
- Adding a new article requires placing a .md file in templates/_shared/articles/, adding an entry in mirror-pairs.json, and running bootstrap [1104]
- Adding a new agent requires placing a .md file in templates/_shared/agents/ and adding an agent_entries entry in mirror-pairs.json." [1105]
- Adding shared doctrine requires a .md in templates/_shared/doctrine/ and a doctrine_entries entry in mirror-pairs.json with source_file and  [1106]
- The drift-check script is located at templates/claude-code/.claude/hooks/check-primitive-drift.sh and must be run from the repo root with a  [1107]
- Each file versions independently, and the doctrine/ and skills/ files are versioned separately such that bumping a skill does not require bu [1108]
- templates/_shared/ is the single source of truth, and platform-specific files in templates/claude-code/.claude/agents/, templates/claude-cod [1109]
- Each harness ships a non-blocking pointer-edit guardrail that warns (never blocks) in three cases: editing a thin wrapper instead of canonic [1110]
- The pointer-edit guardrail configurations reside in .opencode/plugins/warn-pointer-edit.ts, .claude/hooks/warn-pointer-edit.sh, and .github/ [1111]
- Shared content for the epic-scoping skill system lives in the `.agents/` directory as plain markdown with no frontmatter and no harness-spec [1112]
- Each harness (Opencode, Claude Code, GitHub Copilot) has its own thin wrapper files containing only the frontmatter that harness recognizes, [1113]
- The `.agents/` directory is organized into four subdirectories: `skills/` (epic-* skills plus bootstrap-harness), `doctrine/` (shared rules) [1114]
- Three harnesses are supported via thin frontmatter-only pointer files: Opencode (`.opencode/skills/<name>/SKILL.md` plus `opencode.json` com [1115]
- Both the epic-scoping skills and the genesis meta-flow follow the shared-content-in-`.agents/` rule." [1116]
- `bootstrap-harness` is the single canonical body for installing or tailoring a harness, and the `install-harness` agent (Claude Code / Copil [1117]
- Genesis template output under `.github/instructions/` and `.github/copilot-instructions.md` is exempt from the `.agents/` deduplication rule [1118]
- The golden rule of the architecture is: edit content in `.agents/`, edit frontmatter in the harness wrappers, and never duplicate content in [1119]
- The `.agents/doctrine/` layer holds rules shared across multiple skills and rubrics, specifically: acceptance-criteria linting, parallelizat [1120]
- Skills reference doctrine rules via the directive `Applies .agents/doctrine/<name>.md` instead of restating the rules, and rubrics assess ag [1121]
- The bootstrap script `templates/scripts/bootstrap.sh` reads from `templates/_shared/` as its canonical source and renders three equivalent h [1122]
- The Claude Code harness uses `CLAUDE.md` as its entry point and stores rules in `.claude/rules/`, `.claude/agents/`, and `.claude/commands/` [1123]
- The GitHub Copilot harness uses `.github/copilot-instructions.md` as its entry point and stores rules in `.github/instructions/`, `.github/a [1124]
- The Opencode harness uses `CLAUDE.md` as its entry point and stores rules in `.opencode/`." [1125]
- The `--auto-detect` flag inspects the `--output-dir` to infer the project's stack, versions, and dependencies." [1126]
- The `--has-mlflow yes/no` flag controls inclusion of MLflow Prompt Registry rules in the generated harness." [1127]
- The `--has-langgraph yes/no` flag controls inclusion of LangGraph agent rules in the generated harness." [1128]
- The epic-composer skill transforms source material into a complete Epic." [1129]
- The story-decomposer skill decomposes a ready Epic into INVEST-compliant stories." [1130]
- The task-decomposer skill breaks down stories into AI-executable tasks with parallelization assessment." [1131]
- The acceptance-criteria-rules.md doctrine module contains the six AC linting rules plus examples and serves as the single source for those r [1132]
- The source-discipline.md doctrine module is referenced by six entities: epic-composer, epic-interview, epic-acceptance-linter, story-decompo [1133]
- Each skill wrapper is a one-line body referencing .agents/skills/<name>.md, and the Opencode and Claude Code wrappers additionally accept $A [1134]
- The epic-composer skill emits four progressive response states: SYNTHESIS_ONLY, INTERVIEW_REQUIRED, PARTIAL_EPIC, and FINAL_EPIC." [1135]
- The story-decomposer skill emits seven response states: EPIC_NOT_READY, DECOMPOSITION_PLANNED, STORIES_DRAFTED, TASKS_ADDED, READY_FOR_IMPLE [1136]
- The articles/ directory under _shared/ contains Constitutional rules that are rendered into all three harnesses." [1137]
- The agents/ directory under _shared/ contains shared agent definitions where Claude frontmatter is transformed into Copilot format." [1138]
- The commands/ directory under _shared/ contains shared commands and prompts whose body is identical across platforms." [1139]
- The doctrine/ directory contains shared rules referenced by multiple articles and agents, rendered to .claude/rules/doctrine/." [1140]
- The skills/ directory contains shared shippable skills rendered into target .claude/ and .opencode/ directories." [1141]
- mirror-pairs.json is the single source of truth for all mirror pairs, including entries, agent_entries, command_entries, and doctrine_entrie [1142]
- The claude-code/ directory holds Claude-specific harness assets including skills, hooks, and scripts." [1143]
- generate-copilot-mirrors.py transforms Claude frontmatter into Copilot frontmatter and skips the doctrine/ directory." [1144]
- The source material for Epic Creation includes transcripts, docs, notes, and existing codebase." [1145]
- Epic Creation Phase 0 is Context Discovery, which determines whether the project is greenfield or brownfield." [1146]
- Epic Creation Phase 3 is a Guided Interview that invokes the epic-interview tool in waves." [1147]
- Epic Creation Phase 4 produces an Epic Draft using epic-shell, a linter, and traceability." [1148]
- Epic Creation Phase 5 performs a Readiness Assessment by applying the epic-rubric." [1149]
- The output of the Epic Creation phase is a Ready Epic artifact accompanied by a traceability map and a readiness level." [1150]
- Story Decomposition Phase 3 performs Story Drafting using story-shell, BDD, INVEST, and a linter." [1151]
- Story Decomposition Phase 4 performs Dependency Mapping to produce an ordered backlog." [1152]
- Story Decomposition Phase 5 performs a Story Readiness Assessment using the story-rubric." [1153]
- The output of the Story Decomposition phase is a ready story backlog containing INVEST-compliant stories and BDD acceptance criteria." [1154]
- Harness evaluation is a post-bootstrap prompt that runs after `bootstrap.sh` has rendered the harness into a project." [1155]
- The harness targets three platforms: Claude Code, GitHub Copilot, and Opencode." [1156]
- The golden rule states that any rule shared across 2+ articles must reside in the `doctrine/` layer and be referenced, not inlined." [1157]
- When editing rule content, the agent must edit the `.claude/rules/` rendered copies in the target project and must not touch `templates/` or [1158]
- The AI harness supports three tools: Claude Code, Opencode, and GitHub Copilot." [1159]
- The instructions-and-rules repository is public and requires no authentication to use." [1160]
- All installation routes execute the same flow defined in `.agents/skills/bootstrap-harness.md`." [1161]
- Install options such as `--output-dir` and `--ref` are passed after `bash -s --` in the one-command install." [1162]
- The interactive single-prompt installation method works identically in both Claude Code and Opencode." [1163]
- The Copilot agent invocation uses the syntax `@install-harness /absolute/path/to/target`." [1164]
- The installation requires `git` and `python3` as system dependencies." [1165]
- The epic scoping skills system targets three AI coding harnesses: Opencode, Claude Code, and GitHub Copilot." [1166]
- Shared content in the repository lives in `.agents/` as plain markdown with no frontmatter and no harness-specific fields." [1167]
- The golden rule mandates that content is edited in `.agents/`, frontmatter is edited in harness wrappers, and content is never duplicated in [1168]
- Three skills hand off in sequence — epic-composer, story-decomposer, and task-decomposer — with each story fanning out into parallel-structu [1169]
- Each harness ships a non-blocking pointer-edit guardrail that warns but never blocks when a user attempts to edit a thin wrapper instead of  [1170]
- The Opencode pointer-edit hook is a TypeScript plugin that fires on `tool.execute.before` and logs a warning via `client.app.log`." [1171]
- The Claude Code pointer-edit hook is a shell script that fires on `PreToolUse` for Edit or Write events and returns an `additionalContext` r [1172]
- The GitHub Copilot pointer-edit hook uses a JSON config with bash and PowerShell scripts that fire on `preToolUse` and warn to stderr." [1173]
- The story readiness rubric evaluates stories against the INVEST criteria." [1174]
- The task-decomposer defines a shared contract (API, type, or interface) for a story's acceptance criteria, then fans out into parallel Track [1175]
- The project provides Constitutional AI instruction templates for Python (FastAPI, Flask, MCP) and TypeScript (React, Next.js) projects." [1176]
- The install-harness agent inspects the target project, shows an install plan, asks for confirmation, runs bootstrap and harness evaluation,  [1177]
- Both bootstrap approaches produce a set of output artifacts including .claude/rules/, .github/instructions/, .github/copilot-instructions.md [1178]
- The architecture follows a single-source thin-wrappers pattern where content is edited in .agents/ or templates/_shared/ and never duplicate [1179]
- The mirror system maintains body-identical mirrors between .claude/rules/*.md and .github/instructions/*.instructions.md, with generate-copi [1180]
- Claude Code employs a three-layer architecture: persistent Rules, on-demand Skills, and deterministic Hooks." [1181]
- The audit cataloged a total of 159 files across the instructions-and-rules, influencer-sync, and nomikailist repositories." [1182]
- Tech stack version placeholders such as {{PYTHON_VERSION}} and {{REACT_VERSION}} are duplicated across at least 10 template files including  [1183]
- The template system mandates a tiered TDD coverage hierarchy of Contract, Integration, E2E, and Unit tests with 90%, 85%, 70%, and 50% cover [1184]
- The NomikaiList backend is built with FastAPI and LangGraph 1.0 for recommendation agents." [1185]
- The NomikaiList frontend uses Next.js with shadcn UI components." [1186]
- The database is Supabase (PostgreSQL + RLS) and no direct DB access is permitted from the frontend; all queries must go through the API laye [1187]
- The Python package manager for NomikaiList is `uv`, not pip or poetry." [1188]
- Type hints are required on all Python function signatures and enforced by mypy." [1189]
- Backend test coverage must be at least 68%, enforced in CI via --cov-fail-under=68." [1190]
- LangGraph agent state in NomikaiList uses TypedDict (not dataclass), and tools return dicts for LangGraph to merge rather than mutating stat [1191]
- The team decided to use Supabase as the sole backend infrastructure provider for database, authentication, file storage, and real-time subsc [1192]
- SQLAlchemy ORM is explicitly excluded in favor of using the Supabase Python client directly." [1193]
- Redis is explicitly excluded, with Supabase used for caching patterns where needed." [1194]
- Celery is explicitly excluded in favor of async Python tasks or LangGraph for workflows." [1195]
- Supabase's built-in Row Level Security enforces data isolation at the database layer." [1196]
- The supabase-py async client integrates cleanly with FastAPI async patterns." [1197]
- SQLAlchemy bypasses Supabase RLS policies unless explicitly configured." [1198]
- The check-constitution.py script's Article II checks for forbidden dependencies in pyproject.toml." [1199]
- NomikaiList uses opencode as its AI coding assistant." [1200]
- AGENTS.md serves as a derived entry point that summarizes and links the rules but does not replace them." [1201]
- A machine-readable checker at backend/scripts/check-constitution.py validates articles against the running codebase on demand and in CI." [1202]
- The defined rule update order is .claude/rules/ → AGENTS.md." [1203]
- An instructions-drift checker at scripts/check-instructions-drift.sh validates that the opencode config and agent/command files exist and ar [1204]
- The constitution checker runs in CI and violations block merges." [1205]
- check-agent-drift.sh hooks warn when .claude/rules/ changes without corresponding downstream updates." [1206]
- CalVer version 2026.04.24 on enforcement.md tracks the rule publication date." [1207]
- check-agent-drift.sh runs on PreToolUse when editing rule files." [1208]
- NomikaiList has a 68% minimum aggregate coverage threshold enforced in CI." [1209]
- The Privacy/Auth tier (privacy_service.py, auth_service.py, api/routes/auth.py) requires ≥90% coverage." [1210]
- The Revenue/Data integrity tier (repositories/*, import_service.py, api/routes/media.py) requires ≥80% coverage." [1211]
- The AI Agents/ML tier (agents/*, ml/*, recommendation_scorer.py) requires ≥50% coverage." [1212]
- Tests must be authored in the order: contract tests, integration tests, E2E tests, then unit tests." [1213]
- The check-constitution.py script verifies that pytest.ini contains --cov-fail-under=68." [1214]
- The tiered coverage model is intended to supplement, not replace, the existing 68% CI aggregate threshold." [1215]
- The SIGNAL_FLOOR threshold for including a user weight in axis scoring is 0.1." [1216]
- The CAUTION_THRESHOLD is 0.2, representing the bottom quartile on the 0–1 normalised scale." [1217]
- The AI_FIT_SERVICE_ENABLED environment variable gates the route, with a default of True for dev/staging." [1218]
- All six routes on the review-queue API execute via the service-role Supabase client, which bypasses Row-Level Security by design." [1219]
- The MAL adapter was built on the public Jikan proxy at api.jikan.moe/v4." [1220]
- The public Jikan proxy is being retired upstream." [1221]
- The shared public Jikan rate limit is 60 requests per minute across all users, which is insufficient for batch ingestion." [1222]
- The adapter's base URL is sourced from settings.jikan_base_url with a default of http://localhost:8080/v4." [1223]
- Self-hosting Jikan requires zero adapter logic changes beyond swapping the base URL." [1224]
- Self-hosting raises the rate limit from 50 to 120 requests per minute, configurable via JIKAN_RATE_LIMIT_PER_MINUTE." [1225]
- NomikaiList provides a RESTful API for anime and manga discovery and recommendation." [1226]
- The NomikaiList development base URL is http://localhost:8000." [1227]
- NomikaiList API authentication uses Bearer tokens with JWT." [1228]
- The media search endpoint has a default page size of 20 results with a maximum of 100." [1229]
- The recommendations endpoint has a default of 10 results with a maximum of 50." [1230]
- The recommendations endpoint uses a content-based algorithm for generating suggestions." [1231]
- The authentication endpoints are rate-limited to 5 requests per minute." [1232]
- The search endpoint is rate-limited to 100 requests per minute." [1233]
- The recommendations endpoint is rate-limited to 30 requests per minute." [1234]
- MyAnimeList is a supported external platform for importing user data." [1235]
- The CI/CD pipeline workflow is triggered on every push to main and every pull request." [1236]
- Security code (RLS, auth) requires a minimum of 90% test coverage, enforced in CI via --cov-fail-under=90." [1237]
- General code requires a minimum of 80% test coverage, enforced via pytest.ini configuration." [1238]
- The security scanning workflow is triggered on pushes to main/develop, pull requests, and a weekly schedule." [1239]
- The security scanning workflow uses Bandit and Semgrep for static code analysis." [1240]
- The security scanning workflow uses Gitleaks to detect leaked secrets." [1241]
- The security scanning workflow uses Trivy to scan Docker images." [1242]
- GitHub does not expose repository secrets to pull requests from forks for security reasons." [1243]
- The Supabase service role key bypasses Row Level Security (RLS) policies." [1244]
- The deploy job in the CI/CD pipeline runs only on the main branch." [1245]
- The rls-security-tests job in the security scanning workflow verifies that RLS is enabled on all tables." [1246]
- Supabase serves as the managed database, authentication, and storage layer in production." [1247]
- Database migrations consist of 124 or more ordered SQL files in supabase/migrations/ and are applied via the Supabase CLI." [1248]
- The project requires Python 3.11 or later as a prerequisite." [1249]
- The project requires Node.js 18 or later as a prerequisite." [1250]
- The backend uses uv as its Python package manager." [1251]
- The backend uses Supabase as its database backend." [1252]
- The backend development server runs on port 8000 via uvicorn." [1253]
- The frontend development server runs on port 3000." [1254]
- The backend API layer is built with FastAPI." [1255]
- The frontend uses Next.js 16 with the App Router architecture." [1256]
- The frontend uses shadcn/ui for its React component library." [1257]
- The backend supports importing data from MyAnimeList, AniList, and Kitsu via external platform adapters." [1258]
- The backend uses Pydantic models for data validation." [1259]
- The default model kimi-k2.5:cloud has approximately 1 trillion parameters." [1260]
- The Ollama server client version is 0.21.2 and listens on http://localhost:11434." [1261]
- NomikaiList supports importing data from MyAnimeList, AniList, and Kitsu." [1262]
- MyAnimeList import in NomikaiList is performed via the Jikan API." [1263]
- AniList import in NomikaiList uses the GraphQL API." [1264]
- Kitsu import in NomikaiList uses the JSON:API format." [1265]
- Incremental catalog sync in NomikaiList uses each adapter's recently-updated endpoint when supported." [1266]
- When an adapter does not support recently-updated fetch, the NomikaiList service falls back to top-media fetch and logs a warning." [1267]
- Kitsu serves as a secondary source for enrichment and aliases in NomikaiList." [1268]
- MyAnimeList, AniList, and Kitsu each have unique libraries and communities, preventing users from easily migrating or syncing across platfor [1269]
- NomikaiList is a privacy-first anime and manga discovery platform that combines features of existing platforms with AI-powered recommendatio [1270]
- NomikaiList supports import and sync of ratings from AniList, MyAnimeList, and Kitsu." [1271]
- NomikaiList uses a graph-based recommendation engine that learns user taste preferences." [1272]
- NomikaiList is GDPR compliant with full data export and deletion capabilities." [1273]
- NomikaiList implements row-level security at the database level." [1274]
- The NomikaiList backend uses FastAPI, Python 3.11+, Supabase (PostgreSQL + Auth + Storage), and LangGraph for AI agents." [1275]
- The NomikaiList frontend uses Next.js 16 with App Router, TypeScript, and shadcn/ui components." [1276]
- The AI-driven graph recommendation engine with explainability is a completed feature of NomikaiList." [1277]
- NomiKaiList uses Supabase's Row Level Security to enforce data access controls at the database level, preventing unauthorized data exposure  [1278]
- The service role is a privileged Supabase role that bypasses all RLS policies." [1279]
- The ratings table uses a 3-point scale: 1 (dislike), 3 (curious), 5 (like)." [1280]
- The NomikaiList design system uses exactly three font families, each with a distinct role that must never be mixed." [1281]
- Dark mode is explicitly prohibited in the NomikaiList design system; the aesthetic is warm paper only." [1282]
- Glass and blur effects are deprecated by this design system, specifically the existing Tokyo Night .glass utilities." [1283]
- NomikaiList recommends using Local Supabase for all database-dependent tests to provide an environment identical to production." [1284]
- The NomikaiList backend has 37 test files in total." [1285]
- The NomikaiList backend has 21 contract test files located in backend/tests/contract/." [1286]
- The NomikaiList backend has 7 integration test files located in backend/tests/integration/." [1287]
- The NomikaiList backend has 5 unit test files located in backend/tests/unit/." [1288]
- The NomikaiList backend enforces a minimum 80% code coverage gate via pytest configuration." [1289]
- The NomikaiList frontend enforces a minimum 80% coverage threshold across branches, functions, lines, and statements." [1290]
- The NomikaiList backend requires recommendation generation to complete in under 2 seconds." [1291]
- The NomikaiList backend requires API response times to be under 100ms at the 95th percentile." [1292]
- The MockSupabaseClient is implemented in the file src/testing/mock_supabase.py." [1293]
- GitHub Actions CI runs unit tests as Stage 1 with an expected duration of approximately 10-30 seconds." [1294]
- NomikaiList requires usernames to be between 3 and 30 characters." [1295]
- NomikaiList requires a minimum password length of 8 characters." [1296]
- Account creation on NomikaiList requires accepting GDPR consent." [1297]
- NomikaiList onboarding requires users to rate 15 to 20 anime or manga titles." [1298]
- NomikaiList supports three rating types: Like, Dislike, and Curious." [1299]
- The NomikaiList dashboard displays a Taste Profile showing the user's preferred genres and themes." [1300]
- Upon connecting a supported platform, NomikaiList automatically imports the user's ratings and lists." [1301]
- NomikaiList supports data export and account deletion." [1302]
- NomikaiList is a personalized recommendation system with AI-powered curation and multi-platform import capabilities for anime and manga." [1303]
- The backend requires Python 3.11 or later." [1304]
- The frontend requires Node.js 18 or later." [1305]
- The import system supports three external platforms: AniList, MyAnimeList, and Kitsu." [1306]
- The backend uses FastAPI version 0.104.1 with SQLAlchemy 2.0 in async mode." [1307]
- The frontend uses Next.js 14 with App Router, TypeScript, shadcn/ui, Tailwind CSS, and React Query." [1308]
- Security vulnerabilities must not be reported as public issues on the repository." [1309]
- The security scope covers the NomikaiList backend API, frontend, and ingestion pipeline in the repository." [1310]
- Vulnerabilities in third-party platforms (Supabase, AniList, MyAnimeList, Kitsu) are out of scope and should be reported to the respective v [1311]
- Data-access controls in NomikaiList are enforced at the database layer via Supabase Row Level Security." [1312]
- Privacy and GDPR concerns involving personal data can be directed to privacy@nomikailist.com." [1313]

---

[1] claim-alpaca-agents-alpaca-agents-agents-md-000 — Alpaca Agents is a multi-agent AI trading system for Alpaca Markets that operate
[2] claim-alpaca-agents-alpaca-agents-agents-md-002 — The configuration source of truth is data/config/settings.yaml, which must alway
[3] claim-alpaca-agents-alpaca-agents-agents-md-003 — All agents must mutate fields on the shared TradingState object rather than reas
[4] claim-alpaca-agents-alpaca-agents-agents-md-004 — The module dependency direction is src/models/ → src/agents/ / src/tools/ / src/
[5] claim-alpaca-agents-alpaca-agents-agents-md-005 — src/services/ must not import from agents or orchestration, a constraint enforce
[6] claim-alpaca-agents-alpaca-agents-agents-md-006 — The project's test coverage target is approximately 58–59% for the overall proje
[7] claim-alpaca-agents-alpaca-agents-agents-md-010 — src/api/ must not import src/orchestration/ directly, with the only allowlisted
[8] claim-alpaca-agents-alpaca-agents-claude-md-000 — Alpaca Agents is a multi-agent AI trading system for Alpaca Markets built on Lan
[9] claim-alpaca-agents-alpaca-agents-claude-md-001 — The system's current status is Production-Ready for Paper Trading."
[10] claim-alpaca-agents-alpaca-agents-claude-md-002 — The agent pipeline flows from Research → Market Data → Technical and Sentiment i
[11] claim-alpaca-agents-alpaca-agents-claude-md-003 — All agents mutate a shared TradingState object defined in src/models/state.py ra
[12] claim-alpaca-agents-alpaca-agents-claude-md-005 — The deliberation system triggers a Bullish ↔ Bearish → Synthesizer debate at 60–
[13] claim-alpaca-agents-alpaca-agents-claude-md-008 — Expert Advisors consist of 14 investor personas used for deliberation consultati
[14] claim-alpaca-agents-alpaca-agents-claude-md-009 — Docker services expose the Web UI on localhost:5173, the API on localhost:8000,
[15] claim-alpaca-agents-alpaca-agents-claude-md-010 — The autonomous trader's minimum confidence threshold for execution is 80.0."
[16] claim-alpaca-agents-alpaca-agents-claude-md-011 — Live trading execution is disabled by default (TRADER_ENABLE_EXECUTION=false) an
[17] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-000 — The Agent Memory & Learning System provides persistent storage, similarity-based
[18] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-001 — The Memory Manager component is implemented in src/services/memory/manager.py."
[19] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-005 — Calibration adjustments are only applied when Wilson confidence is at least 80%.
[20] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-006 — The historical window for calibration is 30 days."
[21] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-000 — The Alpaca Agents trading system uses a LangGraph-based workflow with specialize
[22] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-001 — The workflow adds edges from regime to technical and sentiment, and from both to
[23] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-002 — Parallel execution of technical and sentiment agents reduces workflow time by 30
[24] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-005 — The backtest decision returns \"backtest\" when sentiment and technical signals
[25] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-007 — The deliberation subgraph is a modular subgraph for multi-agent debate."
[26] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-008 — The deliberation flow includes Bullish Researcher, Bearish Researcher, and Synth
[27] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-000 — The alpaca-agents system runs three LangGraph graphs (Research, Execution, Portf
[28] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-004 — GLM-5.2 scores 62.1 on SWE-bench Pro, 81.0 on Terminal-Bench, and supports 1M co
[29] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-005 — The OrderExecutionAgent must use no LLM; Alpaca API calls must be mediated by de
[30] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-006 — All three LangGraph graphs share a single PostgresSaver checkpointer instance fo
[31] claim-alpaca-agents-alpaca-agents-docs-changelog-md-000 — Version 2.1.0 of Alpaca Agents was released on 2026-07-11."
[32] claim-alpaca-agents-alpaca-agents-docs-changelog-md-002 — An `InvestmentCommitteeCoordinator` component enables multi-persona deliberation
[33] claim-alpaca-agents-alpaca-agents-docs-changelog-md-003 — Multi-strategy orchestration comprises a strategy arbiter, capital allocator, an
[34] claim-alpaca-agents-alpaca-agents-docs-changelog-md-004 — The MLflow Prompt Registry in `src/prompt_registry/` provides versioned prompts
[35] claim-alpaca-agents-alpaca-agents-docs-changelog-md-005 — Version 2.0.0 of Alpaca Agents was released on 2025-10-14."
[36] claim-alpaca-agents-alpaca-agents-docs-changelog-md-007 — Bug #1 fixed a Risk Monitoring SQL column name mismatch by renaming `portfolio_b
[37] claim-alpaca-agents-alpaca-agents-docs-changelog-md-008 — Market Regime Detection (Feature 006) detects 6 market regimes: bull_trend, bear
[38] claim-alpaca-agents-alpaca-agents-docs-changelog-md-009 — Market regime detection uses SPY as the market proxy with a 200-bar lookback."
[39] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-000 — The project's primary language is Python 3.10 or higher."
[40] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-001 — The database technology is PostgreSQL 14+ with TimescaleDB."
[41] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-002 — The LLM framework used is the OpenRouter API."
[42] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-003 — The trading API used is Alpaca Markets."
[43] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-004 — The news API used is Finnhub."
[44] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-005 — The web UI is built with React, FastAPI, and Plotly."
[45] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-008 — The Market Data Agent's purpose is technical analysis and chart pattern detectio
[46] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-009 — The Sentiment Agent's purpose is to analyze news sentiment and market impact."
[47] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-010 — The Backtest Agent's purpose is conditional backtesting for validation."
[48] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-011 — The Autonomous Trader's purpose is to orchestrate analysis and execute trades."
[49] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-002 — emit_deliberation_start accepts max_rounds and initial_confidence parameters."
[50] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-003 — emit_round_header accepts round_num and total_rounds parameters."
[51] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-004 — emit_bullish_argument accepts argument, confidence, and round_num parameters."
[52] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-005 — emit_bearish_argument accepts argument, confidence, and round_num parameters."
[53] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-006 — emit_disagreement_status accepts disagreement, round_num, and continuing paramet
[54] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-007 — emit_consensus_reached accepts disagreement, round_num, and total_rounds paramet
[55] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-008 — emit_synthesis accepts a synthesis string parameter."
[56] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-009 — DeliberationCoordinator accepts a chat_callback parameter."
[57] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-010 — LLMException handling calls callback.emit_error with error_message and round_num
[58] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-011 — Deliberation triggers when initial confidence is between 60 and 95 inclusive."
[59] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-000 — The chat interface currently uses direct sequential agent calls with 5 agents, t
[60] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-001 — The CLI currently uses the full LangGraph workflow with 11 agents, taking about
[61] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-003 — The chat interface bypasses the LangGraph workflow and is missing 6 critical age
[62] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-005 — The target state is for both paths to use the identical LangGraph workflow with
[63] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-006 — The chat interface executes 5 agents: MarketDataAgent, TechnicalAgent, Sentiment
[64] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-007 — The CLI path executes 11 agents total."
[65] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-009 — Phase 2 created src/orchestration/workflow_streaming.py with a streaming wrapper
[66] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-010 — Phase 3 made the chat execute all 11 agents: MarketData, Regime, Technical (para
[67] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-000 — The chat interface supports token-by-token streaming responses that show agent t
[68] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-004 — The /ask <agent> <question> command queries a specific agent."
[69] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-005 — The /debate <question> command triggers multi-agent deliberation."
[70] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-006 — The /ask command accepts agent names including market_data/data, technical/tech,
[71] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-007 — Deliberation agents only appear in a response if confidence is between 60% and 9
[72] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-009 — The sentiment meter score gauge maps a -1 to +1 range onto 0-100."
[73] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-010 — The web UI is launched by running uvicorn on port 8000 and npm run dev for the w
[74] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-000 — Per-agent model selection lives in `llm_routing.assignments` in `data/config/set
[75] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-003 — Technical Agent's current model is `anthropic/claude-3-haiku`."
[76] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-004 — Cost-Optimized configuration costs ~$0.008-$0.012 per analysis (~1¢ per trade)."
[77] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-005 — Balanced configuration costs ~$0.015-$0.025 per analysis (~2¢ per trade)."
[78] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-006 — Premium configuration costs ~$0.04-$0.08 per analysis (~6¢ per trade)."
[79] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-008 — Phase 2 migration expects 20-30% speed improvement and 15% cost reduction."
[80] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-009 — Implementation requires setting shared sampling knobs under `models:` and per-ag
[81] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-010 — For current stage (paper trading development), the recommendation is to use Bala
[82] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-011 — For live trading, the recommendation is to use Premium or Ultra-Premium Configur
[83] claim-alpaca-agents-alpaca-agents-docs-features-outcome-tracking-guide-md-006 — The OutcomeScheduler is a background async scheduler that runs updates every N h
[84] claim-alpaca-agents-alpaca-agents-docs-features-outcome-tracking-guide-md-008 — Running the scheduler with `--interval 1` performs updates every hour."
[85] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-000 — The sentiment tools are located in src/tools/sentiment/."
[86] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-001 — There are 6 LangChain sentiment tools covering news sentiment, options flow, and
[87] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-002 — All sentiment tools use the @tool decorator for LangChain integration."
[88] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-003 — All sentiment tools are async for non-blocking I/O."
[89] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-004 — fetch_news_articles fetches news articles from aggregated sources Alpaca and Fin
[90] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-005 — fetch_news_articles has a default limit of 10 articles."
[91] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-006 — analyze_news_sentiment returns a sentiment score from -100 (bearish) to +100 (bu
[92] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-008 — A call/put ratio greater than 1.5 is interpreted as bullish due to heavy call bu
[93] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-009 — aggregate_sentiment_scores defaults to news weight 0.6, social weight 0.3, and f
[94] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-010 — detect_unusual_activity defaults to a magnitude threshold of 60.0 and an article
[95] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-011 — detect_unusual_activity assigns high severity when both magnitude and volume thr
[96] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-000 — The Alpaca Agents multi-agent trading system uses two distinct tool invocation p
[97] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-001 — ReAct pattern is used when the LLM should adaptively decide which tools to call
[98] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-002 — Direct tool invocation is used when the workflow is deterministic and always fol
[99] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-003 — The ReAct pattern's AgentExecutor is configured with max_iterations=15, handle_p
[100] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-004 — TechnicalAgent uses the ReAct pattern for adaptive technical analysis."
[101] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-005 — SentimentAgent uses direct tool invocation for a deterministic sentiment workflo
[102] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-006 — RiskAgent uses direct tool invocation for deterministic risk calculations."
[103] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-007 — PortfolioAgent uses direct tool invocation for deterministic signal aggregation.
[104] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-008 — The decision framework states that if the workflow adapts based on data availabi
[105] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-009 — The ReAct pattern's typical execution time is 5-10 seconds."
[106] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-010 — Direct invocation's typical execution time is 1-3 seconds."
[107] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-000 — The Alpaca Agents system uses multiple agent patterns depending on the agent's r
[108] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-002 — The document lists 14 total agents by pattern."
[109] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-003 — The BaseReActAgent pattern is used by two agents: TechnicalAgent and SentimentAg
[110] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-004 — The BaseToolAgent pattern is used by one agent: RiskAgent."
[111] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-005 — The Direct Tool Invocation pattern without a base class is used by three agents:
[112] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-006 — The Pure LLM Reasoning pattern without a base class is used by four agents: Bull
[113] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-007 — The Specialized pattern without a base class is used by four agents: RegimeAgent
[114] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-008 — RiskAgent migrated from BaseReActAgent to BaseToolAgent in Sprint 1."
[115] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-010 — The Hybrid pattern's base class is BaseToolAgent, which is new in Sprint 1."
[116] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-011 — The ReAct pattern uses 3-5 LLM calls per execution."
[117] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-001 — The main backtesting engine module is `src.backtest.engine.BacktestEngine`."
[118] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-002 — The backtesting engine recommends 1+ years of historical data validation."
[119] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-004 — The A/B Testing Framework compares two configurations statistically."
[120] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-005 — The A/B testing module is `src.backtest.ab_testing.ABTester`."
[121] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-006 — Walk-Forward Optimization optimizes parameters systematically without overfittin
[122] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-007 — The walk-forward optimization module is `src.backtest.optimization.WalkForwardOp
[123] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-009 — Monte Carlo Simulation assesses tail risk through bootstrap sampling."
[124] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-010 — The Monte Carlo simulation module is `src.backtest.monte_carlo.MonteCarloSimulat
[125] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-011 — Monte Carlo simulation supports bootstrap sampling with 1000+ scenarios."
[126] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-000 — The dashboard's default URL is http://localhost:5173."
[127] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-001 — The dashboard is built on a React frontend and FastAPI backend."
[128] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-002 — The dashboard provides real-time portfolio management, agent chat, risk monitori
[129] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-003 — The dashboard is launched with the command `uv run python main.py dashboard`."
[130] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-004 — Multi-agent mode uses sequential agent responses in the order Market Data, Techn
[131] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-005 — The trade history limit is adjustable between 5 and 50 trades."
[132] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-007 — The auto-refresh interval slider ranges from 5 to 60 seconds."
[133] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-010 — The human-in-the-loop trade approval system requires checkpointing to be enabled
[134] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-001 — Feature flags live in `data/config/settings.yaml`."
[135] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-002 — The four deliberation experiment flags default to false."
[136] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-003 — Each deliberation run records the enabled flags to `DeliberationData.active_expe
[137] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-006 — The metrics endpoint is fetched via `curl \"http://localhost:8000/experiments/me
[138] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-008 — A flag can be toggled in `settings.yaml` via POST to `http://localhost:8000/expe
[139] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-010 — The nightly report scheduler runs by default every 24 hours via `uv run python s
[140] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-000 — Live trading is off by default and stays off until a human deliberately enables
[141] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-001 — Enabling live capital is a human decision requiring separate live credentials an
[142] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-003 — Go-live requires 30+ paper trades completed with zero circuit-breaker trips."
[143] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-004 — Go-live requires shadow-eval agreement ≥ 85% across the last 30 replayed states.
[144] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-005 — Go-live requires all WP-6 eval scorer-gate thresholds passing on a ≥20-sample se
[145] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-006 — Live mode requires `TRADING_MODE=live` in the k3s ConfigMap with a separate secr
[146] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-010 — Live trading is disabled by reverting `ALPACA_PAPER_TRADE=true` or clearing `ALL
[147] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-011 — The kill switch in `src/risk_monitoring/circuit_breakers.py` cancels all open or
[148] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-000 — Alpaca Agents uses MLflow for two distinct purposes: prompt registry and run tra
[149] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-001 — Both the prompt registry and run tracking live in the `Alpaca Agents` experiment
[150] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-002 — 31 prompts are registered on the MLflow server, covering every LLM-based agent i
[151] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-005 — The ramp percentage can also be set via the MLFLOW_PROMPT_RAMP environment varia
[152] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-007 — Agents without LLM prompts (RiskAgent, ExecutionAgent, MarketDataAgent, RegimeAg
[153] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-008 — The PromptResolver caches prompts for MLFLOW_PROMPT_CACHE_TTL seconds (default 3
[154] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-000 — The system includes comprehensive analytics and automatic optimization capabilit
[155] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-002 — The model optimizer is located at src/services/model_optimizer.py."
[156] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-003 — The model optimizer calculates optimal confidence thresholds."
[157] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-004 — The optimization CLI identifies models with win rates below 45%."
[158] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-005 — The optimization CLI identifies expensive models costing more than $0.10 per sig
[159] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-006 — The optimization CLI identifies top performers with win rates above 60%."
[160] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-007 — The confidence optimization command calculates optimal minimum confidence for tr
[161] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-008 — The opportunity optimization command tunes the minimum opportunity score thresho
[162] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-009 — An optimal confidence threshold range requires a win rate of at least 55%."
[163] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-010 — An optimal confidence threshold range requires a minimum of 5 trades for signifi
[164] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-011 — Model analysis requires a minimum of 30 completed trades."
[165] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-002 — Both agents run automatically in every trading workflow execution."
[166] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-003 — The workflow order is Market Data → Technical/Sentiment → Risk → Portfolio → Pos
[167] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-004 — The default trailing stop activates after 5% profit and trails 3% below peak."
[168] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-005 — The default breakeven stop moves to breakeven at 2% profit."
[169] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-006 — The default profit protection locks in a 7% minimum at 10% profit."
[170] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-009 — The default maximum loss forces an exit at 10% loss."
[171] claim-alpaca-agents-alpaca-agents-docs-guides-prompt-promotion-runbook-md-001 — The shadow eval gate requires the candidate to agree with @production on at leas
[172] claim-alpaca-agents-alpaca-agents-docs-guides-prompt-promotion-runbook-md-010 — The runbook implements Spec §9.3 and ties together the WP-4 alias registry (src/
[173] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-000 — The overall code quality assessment is 8.5/10."
[174] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-002 — The estimated effort for refactoring #1 is 1 day."
[175] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-003 — The `analyze_security()` function is a 432-line function with 7 different respon
[176] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-004 — The estimated effort for refactoring #2 is 2 days."
[177] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-008 — The guide specifies creating a new test file at `tests/unit/agents/test_base_age
[178] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-009 — The guide specifies creating a new file `src/orchestration/workflow_executor.py`
[179] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-010 — The guide specifies creating a new file `src/orchestration/reporting_service.py`
[180] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-000 — The Enhanced Risk Monitoring system scans the portfolio every 30 seconds by defa
[181] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-001 — The system provides real-time risk metrics including VaR, drawdown, volatility,
[182] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-005 — Historical tracking uses TimescaleDB hypertables for performance analysis."
[183] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-006 — Migration 003 creates risk_metrics, alert_events, and other risk monitoring tabl
[184] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-007 — Python 3.11+ with dependencies installed via `uv sync --all-extras` is required.
[185] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-000 — The command to run all tests is `uv run pytest tests/ -v`."
[186] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-001 — The command to run a specific test file is `uv run pytest tests/unit/test_bullis
[187] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-002 — The command to run a single test is `uv run pytest tests/unit/test_bullish_resea
[188] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-003 — The command to run tests with coverage is `uv run pytest tests/ --cov=src --cov-
[189] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-005 — The `mock_llm` fixture allows testing LLM-dependent code without API calls."
[190] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-006 — The `clean_database` fixture starts with a clean database and cleans it after th
[191] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-007 — The test suite is organized into unit, integration, contract, performance, prope
[192] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-008 — Async tests require the `@pytest.mark.asyncio` marker."
[193] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-009 — The overall coverage target is 85% or higher."
[194] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-010 — Deliberation agents require 95% or higher coverage."
[195] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-011 — Trading agents require 90% or higher coverage."
[196] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-002 — The default interval between analysis cycles is 300 seconds (5 minutes)."
[197] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-004 — The target average latency per analysis is under 40 seconds."
[198] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-005 — The target success rate for the Balanced configuration is at least 95%."
[199] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-006 — The target average confidence for the Balanced configuration is 60-80%."
[200] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-007 — The target cost per analysis for the Balanced configuration is approximately $0.
[201] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-008 — The Sentiment Agent makes calls to Claude 3.5 Sonnet."
[202] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-009 — The Execution Agent makes calls to Claude 3 Haiku."
[203] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-010 — The error rate should be less than 5% during execution reliability validation."
[204] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-011 — Execution latency should be less than 2 seconds."
[205] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-002 — The tech stack includes Python 3.12, FastAPI, PostgreSQL, SQLAlchemy async, Reac
[206] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-003 — The catalyst_weights table has a check constraint that current_weight must be be
[207] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-004 — The opportunity_lifecycle table has a sentiment column constrained to 'bullish'
[208] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-005 — The notifications table has a type column constrained to 'opportunity', 'outcome
[209] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-008 — CatalystWeightsRepository defines a get_weight method that takes catalyst_type a
[210] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-001 — Before refactoring, `get_options_chain()` was approximately 190 lines with compl
[211] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-002 — The target state for `get_options_chain()` is fewer than 80 lines."
[212] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-009 — Acceptance criteria state that `get_options_chain()` was reduced to fewer than 8
[213] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-010 — All existing tests pass (73 tests)."
[214] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-011 — New unit tests for parsing helpers were added (16 tests)."
[215] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-000 — Current `_state_to_responses()` is approximately 270 lines and has high complexi
[216] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-001 — Current `_detect_intent()` has hardcoded keyword lists inline."
[217] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-002 — Current `_extract_symbol()` has a 95-word `excluded_words` set inline."
[218] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-003 — Keyword lists are externalized to module-level constants."
[219] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-004 — The `SYMBOL_EXCLUSION_WORDS` constant externalizes the 95-word exclusion set fro
[220] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-005 — The `INTENT_KEYWORDS` constant externalizes keyword lists from `_detect_intent()
[221] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-006 — `_state_to_responses()` becomes a simple dispatcher."
[222] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-007 — Acceptance criteria: `_state_to_responses()` reduced from ~270 lines to ~50 line
[223] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-008 — Acceptance criteria: 7 focused response builder methods extracted."
[224] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-009 — Acceptance criteria: New unit tests for extracted helpers (22 tests)."
[225] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-000 — The current `_execute()` method is 275 lines with complexity 29."
[226] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-001 — The current `_submit_options_order()` method is 136 lines."
[227] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-002 — There are 5 duplicated Order constructions in exception handlers."
[228] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-003 — The target state for `_execute()` is approximately 120 lines."
[229] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-004 — The target state includes no duplicated Order construction code."
[230] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-005 — `_create_rejected_order()` eliminates duplicated Order construction in exception
[231] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-006 — `_apply_session_restrictions()` extracts a 63-line extended hours order type con
[232] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-009 — After refactoring, `_execute()` delegates session restrictions to `_apply_sessio
[233] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-010 — After refactoring, `_execute()` exception handling uses `_create_rejected_order(
[234] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-011 — The acceptance criteria require 100% coverage on new helper methods."
[235] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-000 — `_execute()` is approximately 230 lines with complexity 25."
[236] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-001 — `_synthesize_options_recommendation()` is approximately 225 lines with complexit
[237] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-002 — Significant duplication exists in confidence calculation, calibration, and confl
[238] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-003 — Common synthesis logic is extracted to shared helpers."
[239] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-004 — Approximately 150 lines of duplication are eliminated."
[240] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-005 — `_build_confidence_list()` builds the confidence list based on asset type and av
[241] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-006 — `_apply_confidence_adjustments()` applies all calibration, case, degradation, an
[242] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-008 — `_identify_conflicting_signals()` identifies conflicting signals based on asset
[243] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-010 — `_execute()` is refactored to approximately 120 lines."
[244] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-011 — `_synthesize_options_recommendation()` is refactored to approximately 120 lines.
[245] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-001 — Current `_execute()` is approximately 350 lines with complexity 33."
[246] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-002 — Current `_assess_options_risk()` is approximately 280 lines with complexity 32."
[247] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-003 — Duplicated confidence calculation, calibration, and regime adjustment logic exis
[248] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-004 — Target `_execute()` is less than 230 lines."
[249] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-005 — Target state includes 4 shared helper methods eliminating duplication."
[250] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-007 — `_apply_calibration_adjustments()` consolidates calibration logic (lines 187-198
[251] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-008 — `_apply_regime_adjustments()` consolidates regime adjustment logic (lines 259-26
[252] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-009 — `_apply_session_adjustments()` extracts a 60-line session adjustment block (line
[253] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-011 — All tests in `tests/unit/agents/test_risk_agent.py` must pass."
[254] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-001 — The solution checks for recent analysis before running the workflow and returns
[255] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-002 — Cache bypass is implemented via a ?force_fresh=true parameter, allowing power us
[256] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-003 — The TTL strategy is per-asset and configurable, with crypto more volatile (5 min
[257] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-006 — The analysis_cache configuration enables the cache and sets TTL minutes to stock
[258] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-008 — The analyze_symbol endpoint has a force_fresh query parameter defaulting to Fals
[259] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-009 — The analyze_symbol endpoint checks for cached analysis unless force_fresh is tru
[260] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-010 — The stream_cached_analysis function broadcasts agent_complete events for market_
[261] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-011 — The testing strategy includes unit tests verifying find_fresh_analysis returns a
[262] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-000 — The design aims to transform the existing single-strategy trading system into a
[263] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-002 — The central arbiter detects conflicts when multiple strategies want to act on th
[264] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-003 — The central arbiter checks if disagreement is meaningful when both strategies ar
[265] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-006 — Strategies are config-driven, defined in YAML and instantiated by the registry."
[266] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-009 — The existing deliberation system has 14 expert investor personas and integrates
[267] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-010 — The central arbiter triggers deliberation when both sides have >80% conviction."
[268] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-011 — Paper trading is always fully autonomous with no human approval needed."
[269] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-006 — The reward function uses log returns as the primary reward with penalties for tr
[270] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-007 — Model inference is expected to take less than 1ms."
[271] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-010 — The finrl optional dependency group requires elegantrl>=0.3.0, gymnasium>=0.29.0
[272] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-000 — The goal is to integrate the existing deliberation system with the multi-strateg
[273] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-001 — When the Arbiter detects HIGH severity conflicts (both strategies >80% convictio
[274] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-002 — Deliberation uses strategy theses as context, enriches with expert consultation,
[275] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-005 — IntentionConverter bridges the multi-strategy layer (intentions with 0-1 convict
[276] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-007 — IntentionConverter converts conviction (0-1) to confidence (0-100) by multiplyin
[277] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-008 — DeliberationTrigger returns should_deliberate True with reason HIGH_CONVICTION_C
[278] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-009 — DeliberationTrigger returns should_deliberate False with reason CONFLICT_TOO_WEA
[279] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-010 — DeliberationTrigger returns should_deliberate True with reason CONFIG_OVERRIDE f
[280] claim-alpaca-agents-alpaca-agents-docs-proposals-013-agentic-dashboard-md-000 — The Alpaca Agents system runs three distinct agentic loops: Analysis, Research,
[281] claim-alpaca-agents-alpaca-agents-docs-proposals-014-technical-indicators-md-011 — The proposal keeps all indicators as custom NumPy implementations and does not a
[282] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-000 — Proposal 014 catalogued five bugs and missing indicators in the custom NumPy tec
[283] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-003 — TA-Lib has 160+ indicators, requires a C library install, and is actively mainta
[284] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-004 — pandas-ta has 130+ indicators, is pure Python, and is stale (last commit 2023)."
[285] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-005 — pandas-ta-classic has 203 indicators, is pure Python, and is an active fork."
[286] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-006 — The custom NumPy library has 10 indicators."
[287] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-007 — The recommendation is to adopt TA-Lib (the Python wrapper ta-lib-python, backed
[288] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-008 — Decision R1: Adopt TA-Lib; remove the vestigial TA-Lib>=0.4.28 from pyproject.to
[289] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-010 — Decision R3: Reject custom implementations for standard indicators; keep custom
[290] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-000 — The system uses a linear workflow where agents work independently."
[291] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-003 — The Bullish Researcher Agent's role is to advocate for the trade by finding supp
[292] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-004 — The Bearish Researcher Agent's role is to play devil's advocate and identify ris
[293] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-005 — The Synthesizer Agent's role is to moderate the debate and synthesize conclusion
[294] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-006 — The deliberation configuration sets enabled to true and debate_rounds to 1."
[295] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-007 — The bullish and bearish researcher agents are configured to use anthropic/claude
[296] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-008 — The estimated development time for the enhancement is 4-6 hours."
[297] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-009 — The estimated cost impact is +2 LLM calls per trade from the researchers and syn
[298] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-010 — The estimated latency impact is +5-10 seconds per trade."
[299] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-001 — The proposed persistent memory and learning system records all agent analyses an
[300] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-002 — The proposed system tracks performance metrics per agent and pattern."
[301] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-003 — The proposed system calibrates agent confidence based on track record."
[302] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-004 — The memory system architecture uses a Vector DB for embeddings and PostgreSQL fo
[303] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-006 — The OutcomeRecord data model tracks profit/loss, holding period, and correctness
[304] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-007 — The estimated timeline is 8 weeks (2 sprints)."
[305] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-011 — The expected ROI is a 10-15% improvement in risk-adjusted returns."
[306] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-000 — The current deliberation system runs one round of debate."
[307] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-001 — The `debate_rounds` config exists but is not functional; all deliberation is sin
[308] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-005 — The DeliberationCoordinator checks for early consensus if disagreement is less t
[309] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-006 — The default consensus threshold is 0.20, meaning stop early if disagreement is l
[310] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-007 — The disagreement calculation uses the absolute difference in confidence levels."
[311] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-008 — The configuration sets debate_rounds to 3 as the maximum rounds."
[312] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-009 — The configuration sets max_rounds to 5 as a hard limit."
[313] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-010 — The configuration sets min_rounds to 1."
[314] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-000 — Proposal 003 is largely complete with 76 tests passing and good coverage."
[315] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-001 — Current testing coverage is incomplete for the new deliberation system."
[316] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-002 — Unit tests are missing for the deliberation agents BullishResearcher, BearishRes
[317] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-003 — Integration tests are missing for the full deliberation workflow."
[318] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-005 — Tests are missing for the deliberation toggle in enabled and disabled states."
[319] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-006 — Mock LLM responses for deterministic testing are missing."
[320] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-007 — Total test coverage is 62%."
[321] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-008 — The target is 85%+ coverage with focus on critical paths."
[322] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-009 — The proposed solution is to build a comprehensive, maintainable test suite cover
[323] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-002 — The reporting module is located at src/reporting/ with report_generator.py as th
[324] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-004 — generate_portfolio_summary accepts a format parameter with markdown, json, and h
[325] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-006 — The analyze_security workflow function has a generate_reports parameter defaulti
[326] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-007 — The default reporting output formats are markdown and json, with html and pdf no
[327] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-011 — The proposal has an estimated effort of 4 weeks and no dependencies."
[328] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-000 — The proposal has status Proposed, priority High, effort Medium, and impact High.
[329] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-001 — Risk agent runs once per analysis and does not continuously monitor portfolio ri
[330] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-002 — The proposed solution is to implement a real-time risk monitoring system with al
[331] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-003 — The proposed architecture includes src/risk/ with monitor.py for continuous risk
[332] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-004 — Real-time monitoring tracks portfolio Value at Risk (VaR), current drawdown vs m
[333] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-005 — The alert system triggers on drawdown > 15% (warning) or > 18% (critical), VaR i
[334] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-007 — The risk dashboard displays current drawdown (8.2% / 20% max), portfolio beta (1
[335] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-008 — The implementation timeline is 6 weeks."
[336] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-000 — Proposal 006 has status Proposed, priority High, effort Medium, and impact High.
[337] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-002 — The solution is a comprehensive analytics system tracking agent performance acro
[338] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-004 — TechnicalAgent is well calibrated, with 80% confidence corresponding to 78% actu
[339] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-007 — Model comparison for Technical Agent shows claude-3-5-sonnet at 72% accuracy and
[340] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-008 — The recommendation is to use grok-4-fast for best value."
[341] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-009 — The implementation timeline is 5 weeks."
[342] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-010 — The dependencies include Proposal 001 (Memory System)."
[343] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-011 — The expected impact is 10-15% improvement via model optimization."
[344] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-000 — Proposal 007 was implemented on 2025-10-18 with medium priority, medium effort,
[345] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-001 — The proposed solution is a web-based UI for visualizing and interacting with del
[346] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-002 — The deliberation viewer is implemented at src/portfolio/deliberation_viewer.py."
[347] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-009 — Multi-round navigation is deferred because it requires an enhanced report format
[348] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-010 — Outcome correlation is deferred because it requires trade outcome tracking integ
[349] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-011 — Argument highlighting is deferred because it requires structured argument extrac
[350] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-002 — High volatility regime is characterized by VIX > 30."
[351] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-003 — High volatility strategy adjustment reduces position sizes by 50%."
[352] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-004 — The MarketRegimeAgent classifies regime as high_volatility if VIX > 30."
[353] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-005 — The MarketRegimeAgent classifies regime as bull_market if VIX < 20 and SPY price
[354] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-006 — The MarketRegimeAgent classifies regime as bear_market if VIX > 25 and SPY price
[355] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-009 — The workflow adds an edge from market_data to regime_detection and from regime_d
[356] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-011 — The proposal expects a 15-25% Sharpe improvement."
[357] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-000 — Current backtesting only runs conditionally, on conflicting signals."
[358] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-001 — Current backtesting backtests a single strategy."
[359] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-002 — Current backtesting has no A/B testing of deliberation vs non-deliberation."
[360] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-003 — Current backtesting has no walk-forward optimization."
[361] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-004 — Current backtesting has limited metrics (Sharpe, win rate, drawdown)."
[362] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-005 — The example full historical backtest reports 24.5% total return, 1.82 Sharpe, -1
[363] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-006 — The example A/B test shows deliberation achieving Sharpe 1.82 and 68% win rate v
[364] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-008 — Walk-forward optimization uses a 180-day training window, 60-day test window, an
[365] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-010 — Walk-forward optimization achieved an out-of-sample Sharpe of 1.94 versus a 1.82
[366] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-000 — Proposal 010 (Explainability & Interpretability) was implemented on 2025-10-18 w
[367] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-002 — The explainability implementation is located in `src/explainability/`."
[368] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-004 — In the sample AAPL BUY feature-importance output, Technical Signal contributes 3
[369] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-006 — The sample SHAP analysis decomposes final confidence of 72% from a 50% neutral b
[370] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-007 — The confidence breakdown example computes a 72% final confidence from Technical
[371] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-008 — Sensitivity analysis shows final confidence is most sensitive to technical confi
[372] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-009 — Feature importance uses weighted importance scoring with Technical 35%, Sentimen
[373] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-011 — Phase 1 core functionality took 1 day of actual effort, while Phase 2 advanced f
[374] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-012-investor-persona-system-004 — A single YAML flag enables personas, with individual persona configs."
[375] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-012-investor-persona-system-006 — Individual persona configurations can override the model per persona, as shown b
[376] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-012-investor-persona-system-007 — The Benjamin Graham synthesizer persona uses openai/o1-mini because synthesis re
[377] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-012-investor-persona-system-011 — The mitigation for LLM cost increase is to use the same models as existing, just
[378] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-001 — Proposal 001 (Agent Memory & Learning System) has High priority, Medium-High eff
[379] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-002 — Proposal 003 (Comprehensive Testing Suite) has Critical priority, Medium effort,
[380] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-003 — Proposal 013 (Agentic Dashboard: Multi-Loop Operations Console) has High priorit
[381] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-004 — Proposal 014 (Technical Indicators) is superseded by proposal 015."
[382] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-006 — The Comprehensive Testing Suite (Proposal 003) has 76 tests passing with good co
[383] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-007 — The Market Regime Detection feature uses a 6 regime classification system."
[384] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-008 — The system performance target for Sharpe Ratio is 2.0+ (from current ~1.5)."
[385] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-009 — The system performance target for Win Rate is 70%+ (from current ~60%)."
[386] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-010 — The code quality target for Test Coverage is 85%+ (from 62%)."
[387] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-011 — The document reports a total of 12 proposals and a last-updated date of 2026-07-
[388] claim-alpaca-agents-alpaca-agents-docs-readme-md-000 — Alpaca Agents is described as a production-ready multi-agent AI trading system."
[389] claim-alpaca-agents-alpaca-agents-docs-readme-md-002 — The Developer Manual covers architecture and development guide."
[390] claim-alpaca-agents-alpaca-agents-docs-readme-md-003 — The Database Setup document covers PostgreSQL/TimescaleDB configuration."
[391] claim-alpaca-agents-alpaca-agents-docs-readme-md-004 — The Memory System architecture document describes pgvector semantic memory with
[392] claim-alpaca-agents-alpaca-agents-docs-readme-md-005 — The Workflow Analysis architecture document covers LangGraph deliberation workfl
[393] claim-alpaca-agents-alpaca-agents-docs-readme-md-006 — To set up the database, run ./scripts/db_start.sh from the alpaca-agents directo
[394] claim-alpaca-agents-alpaca-agents-docs-readme-md-007 — Install dependencies with uv sync --all-extras."
[395] claim-alpaca-agents-alpaca-agents-docs-readme-md-008 — Run tests with uv run pytest tests/ -v."
[396] claim-alpaca-agents-alpaca-agents-docs-readme-md-009 — Launch the dashboard with uv run python main.py dashboard."
[397] claim-alpaca-agents-alpaca-agents-docs-readme-md-010 — The Multi-Agent Trading feature status is Production."
[398] claim-alpaca-agents-alpaca-agents-docs-readme-md-011 — The system version is 2.1.0."
[399] claim-alpaca-agents-alpaca-agents-docs-roadmap-md-004 — Phase 4 (Learning & Calibration) requires Phase 1's #200 signal outcome tracking
[400] claim-alpaca-agents-alpaca-agents-docs-roadmap-md-005 — Market data API calls were reduced by 10x (#212)."
[401] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-000 — The trading system uses PostgreSQL with TimescaleDB for portfolio tracking and t
[402] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-001 — TimescaleDB provides time-series optimization with hypertables and continuous ag
[403] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-002 — The script ./scripts/db_start.sh starts the TimescaleDB database."
[404] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-005 — The Docker command runs a TimescaleDB container named timescaledb, maps port 543
[405] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-006 — The .env file configures PostgreSQL connection with host localhost, port 5432, d
[406] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-007 — The system automatically creates core tables positions, trades, orders, portfoli
[407] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-008 — When DB_USE_TIMESCALE=true, the tables trades, portfolio_snapshots, and performa
[408] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-009 — TimescaleDB automatically creates and maintains the continuous aggregates daily_
[409] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-010 — TimescaleDB provides 10-100x faster queries on time-based data through time-seri
[410] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-011 — TimescaleDB automatic compression provides 90%+ storage savings on historical da
[411] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-000 — The database can be started with ./scripts/db_start.sh or docker-compose up -d t
[412] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-001 — The database is available at localhost:5432 with database trading, user trading_
[413] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-002 — Database status can be checked with ./scripts/db_status.sh."
[414] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-003 — The .env file should be updated with DB_TYPE=postgresql, DB_POSTGRES_HOST=localh
[415] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-004 — The connection can be tested by running uv run python main.py dashboard or pytho
[416] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-006 — pgAdmin can be started with docker-compose --profile admin up -d and is accessib
[417] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-007 — To connect pgAdmin to the database, register a server named 'Trading DB' with ho
[418] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-000 — This project uses pre-commit to ensure code quality, security, and consistency b
[419] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-001 — Pre-commit hooks automatically run checks on code before each commit, catching i
[420] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-002 — Pre-commit checks include code formatting with Black and Ruff."
[421] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-003 — Pre-commit linting uses Ruff, which replaces flake8, isort, and pylint."
[422] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-004 — Pre-commit security checks use Bandit and detect-secrets."
[423] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-005 — Pre-commit type checking uses mypy."
[424] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-006 — Pre-commit testing runs a fast subset of unit tests."
[425] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-007 — Pre-commit file integrity checks include trailing whitespace, EOF fixers, and YA
[426] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-008 — Pre-commit documentation checks include Markdown formatting."
[427] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-009 — First-time setup installs all dev dependencies with uv sync --all-extras and ins
[428] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-010 — The pytest-unit hook duration is about 5-10 seconds and runs unit tests only, no
[429] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-011 — Integration tests run in CI, not pre-commit, because they are too slow."
[430] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-000 — This project uses uv-secure to scan dependencies for known security vulnerabilit
[431] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-001 — uv-secure checks the uv.lock file against the PyPI JSON API for security issues.
[432] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-002 — uv-secure is configured as a manual pre-commit hook because it makes network cal
[433] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-003 — The uv-secure pre-commit hook is configured with rev 0.14.0, args [--check-direc
[434] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-004 — uv-secure should always be run before creating a release."
[435] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-005 — uv-secure should be run after `uv lock --upgrade`."
[436] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-006 — A successful uv-secure scan reports 'No vulnerabilities or maintenance issues de
[437] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-008 — To update all dependencies to latest compatible versions, run `uv lock --upgrade
[438] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-009 — uv-secure is skipped in CI by default, as configured in `.pre-commit-config.yaml
[439] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-010 — uv-secure scan time is approximately 3-5 minutes for 197 dependencies, requires
[440] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-011 — The document was last updated on 2025-10-10 and specifies uv-secure version 0.14
[441] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-000 — Python 3.10 or higher is required."
[442] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-001 — PostgreSQL 14+ is required, TimescaleDB is recommended, and the repository ships
[443] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-002 — The system requires accounts for Alpaca, OpenRouter, and Finnhub."
[444] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-003 — Dependencies are installed with `uv sync`, which creates the virtual environment
[445] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-004 — The database runs as a TimescaleDB container, and helper scripts under `scripts/
[446] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-005 — The analysis workflow fetches recent news from Finnhub, analyzes sentiment with
[447] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-006 — Whether trades execute automatically or wait for higher confidence is controlled
[448] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-008 — Before running autonomous trading, the safety checklist requires using a paper t
[449] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-009 — Alpaca Agents is an autonomous AI-powered trading system that uses multiple spec
[450] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-010 — The News Monitor component monitors Finnhub for breaking news."
[451] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-011 — The default model for `market_data_agent` is `anthropic/claude-3.5-sonnet`."
[452] claim-alpaca-agents-alpaca-agents-readme-md-000 — The system uses 7 specialized agents orchestrated with LangGraph."
[453] claim-alpaca-agents-alpaca-agents-readme-md-001 — Each agent is assigned a specific LLM model: Research uses Claude Sonnet, Market
[454] claim-alpaca-agents-alpaca-agents-readme-md-002 — Each analysis costs approximately $0.02 and takes 18–37 seconds."
[455] claim-alpaca-agents-alpaca-agents-readme-md-003 — The sentiment analysis agent uses the Alpaca News API with 50 articles per reque
[456] claim-alpaca-agents-alpaca-agents-readme-md-005 — The codebase contains approximately 114,671 lines of code excluding tests."
[457] claim-alpaca-agents-alpaca-agents-readme-md-007 — The web UI is built with React and FastAPI."
[458] claim-alpaca-agents-alpaca-agents-readme-md-008 — The system is restricted to paper trading and must never be used with live tradi
[459] claim-alpaca-agents-alpaca-agents-readme-md-009 — Setup time is approximately 30 seconds when using the uv package manager."
[460] claim-alpaca-agents-alpaca-agents-readme-md-010 — The project has over 4000 tests passing."
[461] claim-aperiodic-chats-2026-09-06-chat-error-res-godot-world-preview-3d-gd-102-parse-er-000 — Godot reported a parse error at res://godot/world_preview_3d.gd:102 stating it c
[462] claim-aperiodic-chats-2026-09-06-chat-error-res-godot-world-preview-3d-gd-102-parse-er-002 — Godot failed to load the script res://godot/world_preview_3d.gd with a \"Parse e
[463] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-001 — ChunkData.get_block has no bounds check."
[464] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-007 — Nothing in the runtime calls update_around."
[465] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--000 — The project is a Godot project containing project.godot and 46 .gd scripts."
[466] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--001 — Godot 4.7.2 is installed on the machine."
[467] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--002 — GDScript's LSP is not one of opencode's built-in language servers."
[468] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--003 — Godot's LSP is a TCP server on port 6005, requiring a stdio bridge."
[469] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--005 — Godot editor settings confirm the GDScript LSP listens on 127.0.0.1:6005 when th
[470] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--006 — The Godot editor was running with the GDScript LSP live on 127.0.0.1:6005."
[471] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--008 — The stdio↔TCP bridge works end-to-end."
[472] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--009 — An opencode.json was created with a custom gdscript LSP for .gd files and the co
[473] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--010 — A .opencode/godot-lsp-bridge.js stdio↔TCP bridge was created because Godot's LSP
[474] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--011 — The GDScript LSP only runs while the Godot editor is open, so opencode's LSP con
[475] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--000 — The block registry defines 8 hardcoded blocks registered via _register(id, name,
[476] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--003 — ChunkData.blocks is a PackedInt32Array always resized to 4096 and filled with AI
[477] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--006 — The persistence format declares FORMAT_VERSION = 1 but never checks it on load."
[478] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-the-project-is-a-g-010 — block_registry has 8 blocks and no ore or material palette at all."
[479] claim-aperiodic-chats-2026-09-07-chat-the-chuncks-are-rendering-seperated-from-one-ano-006 — ChunkManager.update_around is documented \"Call every frame\", but nothing calls
[480] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-000 — The repository has 17 open issues."
[481] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-001 — Issue #11 is the only loose end from finished work and requires one exported-bui
[482] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-002 — Issue #4 (Texture2DArray) fixes mip bleeding and is a hard prerequisite for #5 g
[483] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-005 — The workflow requires an existing issue, a failing test/harness, green, prefligh
[484] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-006 — No Godot export templates were installed, which the release-build part of issue
[485] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-010 — The vendored godot_mcp addon uses absolute preload paths res://addons/godot_mcp/
[486] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-000 — The open issues being reviewed belong to the GitHub repository hybridindie/godot
[487] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-001 — The repository has 20 open issues at the time of the session."
[488] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-002 — Issue #422 is a high-priority silent failure in which deleting a .tscn file caus
[489] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-003 — Issue #414 is a high-priority silent failure in which `set_node_property` with a
[490] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-004 — Issue #413 is a high-priority silent failure in which `navigation_bake_mesh` ret
[491] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-005 — Issue #411 is a high-priority silent failure in which the debugger traps the gam
[492] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-007 — The recommended next batch is the four priority:high silent-failure bugs #422, #
[493] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-008 — A failing test for issue #414 reproduced the exact silent no-op from the issue,
[494] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-009 — A failing test for issue #413 reproduced `baked:true` being returned on an empty
[495] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-010 — A failing test for issue #422 reproduced the deleted scene's stale tab remaining
[496] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-000 — The engine is built on Godot 4.7 using GDScript only with the 'mobile' renderer.
[497] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-001 — Chunks are 16³ blocks stored in a PackedInt32Array flat storage with no palette
[498] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-003 — Meshing is naive per-face culled with no greedy meshing."
[499] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-004 — The engine has no ambient occlusion, no smooth lighting, and no per-face lightin
[500] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-007 — Zylann measured that creating a mesh collider is 3–5× more expensive than meshin
[501] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-008 — Greedy meshing reduces quads from 384 to 6 for an 8³ cube, 4770 to 2100 for a sp
[502] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-004 — A healthy run spawns the player near (8, 10, 8), in the open, with visible terra
[503] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-006 — Headless probe on clean main places the player at (8.5, 8.9, 8.5) with eye at (8
[504] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-007 — Headless probe on clean main shows clear air at feet, eye, and 1-4m in front, wi
[505] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-008 — test_spawn.gd and test_mesher.gd pass with 0 failed."
[506] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-009 — pos=8,8,8 means the player is at y≈8, inside the terrain, with ground=7 so feet
[507] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-010 — A real defect on clean main is that in the windowed run the player at (8.5, 8.9,
[508] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-000 — Tier-1 is drained and the next work item is #5 (greedy meshing), the head of the
[509] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-003 — test_render_smoke.gd:49 calls look_at before add_child, logging \"Node not insid
[510] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-004 — #5 greedy meshing is the only open story of epic #28."
[511] claim-aperiodic-chats-2026-09-12-chat-research-task-read-only-no-code-changes-in-users-001 — ChunkData is a dense PackedInt32Array(4096) indexed as x + y*n + z*n²."
[512] claim-aperiodic-chats-2026-09-12-chat-research-task-read-only-no-code-changes-in-users-011 — Chunk neighbor gating uses a [[1,0,0],…] list of 5 directions, assuming the XZ r
[513] claim-aperiodic-chats-2026-09-12-chat-research-task-web-research-no-code-changes-topic-003 — 0fps' culled meshing produces roughly 16× fewer quads than naive meshing on 16³
[514] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-000 — 15 monohedral convex pentagon tiling families are known."
[515] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-002 — The Cairo pentagonal tiling belongs to the type 4 family of convex pentagon tili
[516] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-003 — The Cairo pentagonal tiling has 5 edge-neighbors per tile."
[517] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-004 — The prismatic pentagonal tiling is the dual of the elongated triangular tiling 3
[518] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-005 — All 15 convex pentagon tiling types are periodic."
[519] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-006 — The truncated square tiling (4.8.8) is the only edge-to-edge regular-polygon til
[520] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-007 — In the truncated square tiling (4.8.8), each octagon has 4 octagon neighbors and
[521] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-008 — The truncated square tiling (4.8.8) is the truncation of the square tiling at ev
[522] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-010 — The pinwheel tiling uses a right triangle 1-2-√5 and a 5-tile substitution at sc
[523] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-research-only--010 — Triangles are always planar with per-vertex heights, whereas a square heightfiel
[524] claim-comfyui-mcp-comfyui-mcp-agents-md-000 — comfyui_mcp is a standalone MCP server for ComfyUI that is usable by any AI agen
[525] claim-comfyui-mcp-comfyui-mcp-agents-md-001 — The comfyui_mcp server is built on FastMCP 4 and enables AI assistants to genera
[526] claim-comfyui-mcp-comfyui-mcp-agents-md-002 — The MCP framework used is fastmcp[tasks] 4.0.0b1, a standalone FastMCP 4 beta bu
[527] claim-comfyui-mcp-comfyui-mcp-agents-md-005 — The configuration file for comfyui_mcp is located at ~/.comfyui-mcp/config.yaml.
[528] claim-comfyui-mcp-comfyui-mcp-agents-md-010 — Tests use pytest-asyncio with asyncio_mode = auto and mock ComfyUI API responses
[529] claim-comfyui-mcp-comfyui-mcp-changelog-md-000 — comfyui-mcp-secure version 2.2.0 was released on 2026-08-29."
[530] claim-comfyui-mcp-comfyui-mcp-changelog-md-003 — The server migrated to FastMCP 4 beta (fastmcp[tasks]==4.0.0b1, built on MCP SDK
[531] claim-comfyui-mcp-comfyui-mcp-changelog-md-006 — The Dockerfile Python base image was fixed from python:3.14-slim to python:3.12-
[532] claim-comfyui-mcp-comfyui-mcp-changelog-md-007 — comfyui-mcp-secure version 2.1.0 was released on 2026-05-12 as an additive minor
[533] claim-comfyui-mcp-comfyui-mcp-contributing-md-001 — The project uses pre-commit to enforce code quality via a git hook that runs che
[534] claim-comfyui-mcp-comfyui-mcp-contributing-md-002 — The pre-commit hook suite includes trailing whitespace fixer, YAML check, large
[535] claim-comfyui-mcp-comfyui-mcp-contributing-md-003 — All changes to the project must include tests, which use pytest with pytest-asyn
[536] claim-comfyui-mcp-comfyui-mcp-contributing-md-004 — Tests must mock ComfyUI API responses with respx and must never make real HTTP c
[537] claim-comfyui-mcp-comfyui-mcp-contributing-md-006 — Pydantic models are used for configuration and data structures in the project."
[538] claim-comfyui-mcp-comfyui-mcp-contributing-md-007 — The project handles workflow execution against ComfyUI and must never expose dan
[539] claim-comfyui-mcp-comfyui-mcp-contributing-md-008 — The default local ComfyUI URL for development is http://127.0.0.1:8188."
[540] claim-comfyui-mcp-comfyui-mcp-contributing-md-010 — CI will run lint, type-check, and test jobs automatically on every pull request.
[541] claim-comfyui-mcp-comfyui-mcp-readme-md-004 — The Selective API Surface never proxies the dangerous ComfyUI endpoints /userdat
[542] claim-comfyui-mcp-comfyui-mcp-readme-md-006 — Version 2.1.0 (released 2026-05-12) is additive with no breaking changes since 2
[543] claim-comfyui-mcp-comfyui-mcp-readme-md-007 — In version 2.0.0, the parameter `id` was renamed to `node_id` in comfyui_install
[544] claim-comfyui-mcp-comfyui-mcp-readme-md-010 — comfyui-mcp-secure requires Python 3.12 or later and the uv package manager as p
[545] claim-godot-agents-godot-agents-agents-md-000 — The `godot-agents` repository functions as the orchestrator/client, depending on
[546] claim-godot-agents-godot-agents-agents-md-001 — The `godot-agents` system is tightly coupled to the specific `godot-mcp` server
[547] claim-godot-agents-godot-agents-agents-md-003 — For `godot-mcp` versions 2026.08.31b4 and later, toolset enablement is server-gl
[548] claim-godot-agents-godot-agents-agents-md-004 — The default transport mechanism is stdio, requiring the `godot-mcp` CLI to be re
[549] claim-godot-agents-godot-agents-agents-md-005 — Since version 2026.08.31b4, `godot-mcp` emits a structured payload, which the cl
[550] claim-godot-agents-godot-agents-agents-md-006 — The build/verify/fix loop is capped by a default of 3 retries and a recursion li
[551] claim-godot-agents-godot-agents-claude-md-000 — The knowledge fabric is accessible by default at a specific local path, but this
[552] claim-godot-agents-godot-agents-docs-configuration-md-000 — All configuration must be done via environment variables, as there is no configu
[553] claim-godot-agents-godot-agents-docs-configuration-md-001 — The default transport mechanism for MCP is `stdio`."
[554] claim-godot-agents-godot-agents-docs-configuration-md-002 — The default port for HTTP transport is 9090."
[555] claim-godot-agents-godot-agents-docs-configuration-md-003 — Web search is disabled by default, requiring explicit opt-in to enable the retri
[556] claim-godot-agents-godot-agents-docs-configuration-md-004 — The experimental fluid executor is disabled by default, requiring explicit opt-i
[557] claim-godot-agents-godot-agents-docs-configuration-md-005 — Setting the MLflow tracking URI enables tracing and evaluation logging for the a
[558] claim-godot-agents-godot-agents-docs-configuration-md-007 — The agent verifier can be instructed to run the project's existing GUT test suit
[559] claim-godot-agents-godot-agents-docs-eval-fluid-ab-runbook-md-003 — Live mode execution, which provides the authoritative pass-rate, requires specif
[560] claim-godot-agents-godot-agents-docs-eval-live-md-001 — The execution flow involves the planner, executor, and verifier interacting with
[561] claim-godot-agents-godot-agents-docs-gle-calibration-md-001 — The live calibration run requires a running Godot editor and the `godot_mcp` bri
[562] claim-godot-agents-godot-agents-docs-observability-md-001 — Logging is controlled by setting the `MLFLOW_TRACKING_URI` environment variable,
[563] claim-godot-agents-godot-agents-docs-prd-md-000 — The Godot-native AI development platform is composed of three distinct layers: a
[564] claim-godot-agents-godot-agents-docs-prd-md-001 — The Godot addon and bridge holds direct authority over the live Godot editor sta
[565] claim-godot-agents-godot-agents-docs-prd-md-002 — The FastMCP server acts as the typed capability surface between the agent and Go
[566] claim-godot-agents-godot-agents-docs-prd-md-003 — The agent system provides the policy and orchestration layer, managing planning,
[567] claim-godot-agents-godot-agents-docs-prd-md-004 — The v1 implementation uses a LangGraph StateGraph architecture where nodes opera
[568] claim-godot-agents-godot-agents-docs-prd-md-005 — The execution policy mandates that the MCP is the primary substrate for Godot wo
[569] claim-godot-agents-godot-agents-docs-setup-md-000 — Python 3.13 or newer is required for the setup."
[570] claim-godot-agents-godot-agents-docs-setup-md-001 — The `godot-mcp` server is a standalone project, distinct from the agent's depend
[571] claim-godot-agents-godot-agents-docs-setup-md-002 — In service mode, a single `godot-mcp` HTTP service manages the editor bridge, pr
[572] claim-godot-agents-godot-agents-docs-setup-md-003 — Godot version 4.4 or newer is required for live runs with the `godot_mcp` addon
[573] claim-godot-agents-godot-agents-docs-setup-md-004 — Ollama defaults to listening on `http://127.0.0.1:11434`, unless overridden by `
[574] claim-godot-agents-godot-agents-docs-setup-md-005 — MLflow tracing is optional; setting `MLFLOW_TRACKING_URI` enables logging, other
[575] claim-godot-agents-godot-agents-pi-md-000 — The knowledge fabric lives at a default location, which can be overridden by an
[576] claim-godot-agents-godot-agents-readme-md-000 — The agent is a self-improving, local-first LangGraph agent for AI-driven Godot d
[577] claim-godot-agents-godot-agents-readme-md-001 — The agent uses a LangGraph StateGraph composed of 14 nodes to manage the build →
[578] claim-godot-agents-godot-agents-readme-md-004 — Tracing to MLflow is conditional on setting the `MLFLOW_TRACKING_URI` environmen
[579] claim-godot-agents-godot-agents-readme-md-005 — The system requires Python 3.13+ and includes an 80% coverage gate in its CI wor
[580] claim-godot-agents-godot-agents-readme-md-006 — The default WebSocket server binds to `127.0.0.1` on port `9070`."
[581] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-001 — PR #442 (Enforce local ollama-only graphify backend) failed CI on ruff."
[582] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-002 — PR #441 (Fix debugger silent no-op (break state)) failed CI on live editor e2e."
[583] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-003 — PR #440 (Close editor tabs for deleted open scenes) failed CI on live editor e2e
[584] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-008 — Qodo reviews have landed on all 5 PRs."
[585] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-011 — Qodo found a real bug in #440: EditorInterface.close_scene() closes the active t
[586] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-001 — The EditorInterface Methods table in the file spans lines 43–110."
[587] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-002 — The complete set of EditorInterface methods whose names contain \"scene\" is 17
[588] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-005 — EditorInterface has no method to make a different open scene tab the active one
[589] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-006 — The signature of open_scene_from_path is `void open_scene_from_path(scene_filepa
[590] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-007 — The signature of reload_scene_from_path is `void reload_scene_from_path(scene_fi
[591] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-008 — get_open_scenes() and get_open_scene_roots() list all open scenes, but the activ
[592] claim-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-000 — Graphify version 0.9.61 already lists opencode as an install platform."
[593] claim-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-001 — The pre-existing .opencode/plugins/graphify.js only performs a once-per-session
[594] claim-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-006 — Because opencode cannot deny from tool.execute.before, Claude's permissionDecisi
[595] claim-godot-mcp-git-issue-484-md-000 — The reporter tested the setup with Godot 4.7.0, godot-mcp version 2026.09.10, an
[596] claim-godot-mcp-git-issue-484-md-003 — The MCP external tool server URL is entered as http://<IP or resolvable name of
[597] claim-godot-mcp-git-issue-484-md-010 — Editing tools stay hidden until the agent calls godot_enable_toolset(\"scene_edi
[598] claim-godot-mcp-git-issue-485-md-000 — After calling godot_enable_toolset for any gated toolset, the tools appear in go
[599] claim-godot-mcp-git-issue-485-md-002 — godot_enable_toolset() mutates the server-global enabled set in mcp_server/tools
[600] claim-godot-mcp-git-issue-485-md-004 — FastMCP 4.0.1 has no server-side send_tools_list_changed helper, but the MCP SDK
[601] claim-godot-mcp-git-issue-485-md-005 — All 162 addon cmd_* handlers exist and match mcp_server/command_map.py."
[602] claim-godot-mcp-git-issue-485-md-008 — The proposed fix is to emit notifications/tools/list_changed after enable_toolse
[603] claim-godot-mcp-git-issue-485-md-009 — The root cause of the issue is an OpenCode client bug rather than a godot-mcp se
[604] claim-godot-mcp-git-issue-485-md-011 — Issue #485 was closed via PR #491 with the server-side fix implemented."
[605] claim-godot-mcp-git-issue-486-md-000 — Issue #486 is in CLOSED state."
[606] claim-godot-mcp-git-issue-486-md-001 — When .tscn or .gd files are edited externally, the Godot editor does not detect
[607] claim-godot-mcp-git-issue-486-md-002 — No cmd_scan, cmd_refresh, or cmd_reimport handler exists in the addon."
[608] claim-godot-mcp-git-issue-486-md-003 — The addon only calls update_file() after its own writes."
[609] claim-godot-mcp-git-issue-486-md-004 — cmd_reload_scene exists but is destructive (confirm=True) and requires the scene
[610] claim-godot-mcp-git-issue-486-md-006 — A proposed fix is to add a non-destructive cmd_rescan_filesystem handler that tr
[611] claim-godot-mcp-git-issue-486-md-007 — A proposed additional fix is to add a cmd_reload_scene variant that does not req
[612] claim-godot-mcp-git-issue-487-md-000 — Issue #487 is in CLOSED state."
[613] claim-godot-mcp-git-issue-487-md-001 — When the same PackedScene is instanced twice, property overrides on the second i
[614] claim-godot-mcp-git-issue-487-md-003 — No tool can enable Editable Children."
[615] claim-godot-mcp-git-issue-487-md-004 — The tree inspector emits no owner/editable-instance metadata, so agents cannot d
[616] claim-godot-mcp-git-issue-487-md-005 — _cmd_instance_scene calls packed.instantiate(GEN_EDIT_STATE_INSTANCE) but never
[617] claim-godot-mcp-git-issue-487-md-006 — scene_inspect.gd traverses with un-owner-filtered node.get_children() and emits
[618] claim-godot-mcp-git-issue-487-md-007 — Node.set_editable_instance(node, is_editable) is the API that would fix the issu
[619] claim-godot-mcp-git-issue-487-md-008 — Proposed fix: add a cmd_set_editable_children handler plus a corresponding mutat
[620] claim-godot-mcp-git-issue-487-md-009 — Proposed fix: include owner and is_editable_instance metadata in serialize_tree
[621] claim-godot-mcp-git-issue-487-md-010 — Proposed fix: consider auto-enabling editable children when an agent creates a s
[622] claim-godot-mcp-git-issue-488-md-000 — Every session requires calling three tools (godot_get_server_info, godot_list_to
[623] claim-godot-mcp-git-issue-488-md-003 — A default toolset configuration option partially exists via the GODOT_MCP_DEFAUL
[624] claim-godot-mcp-git-issue-488-md-004 — A proposed option is to auto-enable the scene_edit and scripts toolsets by defau
[625] claim-godot-mcp-git-issue-488-md-005 — A proposed option is a single godot_bootstrap call that returns server info, too
[626] claim-godot-mcp-git-issue-488-md-007 — The friction was amplified by issue #485, which is an OpenCode client bug rather
[627] claim-godot-mcp-git-issue-488-md-008 — Issue #488 is in the CLOSED state."
[628] claim-godot-mcp-git-issue-489-md-001 — Issue #489 is in CLOSED state."
[629] claim-godot-mcp-git-issue-489-md-004 — The root cause is described as a downstream symptom of Issue #3 (instanced scene
[630] claim-godot-mcp-git-issue-489-md-005 — When the instance doesn't load properly due to the editable-children gap, nodes
[631] claim-godot-mcp-git-issue-489-md-007 — The fix was to fix Issue #3 by adding a `set_editable_children` tool plus owner
[632] claim-godot-mcp-git-issue-489-md-008 — MuhamadBarzani closed the issue on 2026-09-16, stating it is a downstream sympto
[633] claim-godot-mcp-git-issue-489-md-009 — AnimationPlayer path resolution works correctly when the instance loads; the fai
[634] claim-godot-mcp-git-issue-520-md-000 — MCPBridge._pending_times is read and erased in _handle_text() but never populate
[635] claim-godot-mcp-git-issue-520-md-008 — Acceptance criteria: No dead state: _pending_times removed or populated."
[636] claim-godot-mcp-git-issue-520-md-010 — Acceptance criteria: Contract/integration tests for the command_completed signal
[637] claim-godot-mcp-git-issue-521-md-000 — MCPPlugin._server_version is declared and read by _server_version_label() but ne
[638] claim-godot-mcp-git-issue-521-md-001 — The comment claims the server version is populated when the bridge connects via
[639] claim-godot-mcp-git-issue-521-md-002 — The dock's version label can only ever show \"Godot x.y.z\", never the server pa
[640] claim-godot-mcp-git-issue-521-md-003 — A proposed fix is to add a cmd_get_addon_info handshake and have the server push
[641] claim-godot-mcp-git-issue-521-md-004 — A proposed fix is to assign _server_version from that handshake, so the dock lab
[642] claim-godot-mcp-git-issue-521-md-005 — A simplest alternative if a full handshake is deferred is to have cmd_get_projec
[643] claim-godot-mcp-git-issue-521-md-006 — An acceptance criterion is that _server_version is populated by a real value flo
[644] claim-godot-mcp-git-issue-521-md-007 — An acceptance criterion is that the dock displays both halves of the label once
[645] claim-godot-mcp-git-issue-521-md-008 — An acceptance criterion is that this issue pairs naturally with the cmd_get_addo
[646] claim-godot-mcp-git-issue-521-md-009 — Issue #521 is in state CLOSED."
[647] claim-godot-mcp-git-issue-521-md-010 — Issue #521 has labels bug and component:addon."
[648] claim-godot-mcp-git-issue-522-md-000 — command_router.gd is 756 lines long."
[649] claim-godot-mcp-git-issue-522-md-008 — The intended result is that the router contains only dispatch, envelope builders
[650] claim-godot-mcp-git-issue-522-md-009 — An acceptance criterion is that no handler calls a private method on the router,
[651] claim-godot-mcp-git-issue-522-md-010 — An acceptance criterion is that existing contract tests pass unchanged, since en
[652] claim-godot-mcp-git-issue-522-md-011 — Issue #522 is in state CLOSED."
[653] claim-godot-mcp-git-issue-523-md-000 — The 20-node UndoRedo threshold (#461) exists in exactly one of three batch-apply
[654] claim-godot-mcp-git-issue-523-md-001 — In batch.gd, batch_set_property declares a local const `undo_threshold := 20` bu
[655] claim-godot-mcp-git-issue-523-md-002 — composite.gd's batch_create_nodes (line 161) and apply_node_edits (line 229) hav
[656] claim-godot-mcp-git-issue-523-md-003 — A 500-node batch create opens one giant UndoRedo action while an equivalent-size
[657] claim-godot-mcp-git-issue-523-md-004 — batch.gd cross-scene path (_cross_scene_one) mutates scenes on disk directly wit
[658] claim-godot-mcp-git-issue-523-md-006 — The fix requires batch_create_nodes and apply_node_edits to return the same `und
[659] claim-godot-mcp-git-issue-523-md-007 — Contract tests should pin the threshold boundary (19/20/21), the `undoable:false
[660] claim-godot-mcp-git-issue-523-md-008 — Acceptance criterion: One shared const; no literal `20` outside it."
[661] claim-godot-mcp-git-issue-523-md-009 — Acceptance criterion: All three batch tools return identical honesty-field shape
[662] claim-godot-mcp-git-issue-523-md-010 — Acceptance criterion: Tests updated in the same commit (rule testing)."
[663] claim-godot-mcp-git-issue-524-md-000 — The addon's entire GDScript layer has zero automated tests."
[664] claim-godot-mcp-git-issue-524-md-001 — Verification today is ~20 hand-run smoke scripts (godot/tests/*_smoke.gd, run ma
[665] claim-godot-mcp-git-issue-524-md-003 — command_router.gd handles envelope validation, unknown-command handling, id stam
[666] claim-godot-mcp-git-issue-524-md-004 — type_coerce.gd handles all to_json/from_json shapes, string-form parsing, and er
[667] claim-godot-mcp-git-issue-524-md-006 — The fix proposes adding a headless GDScript test runner runnable from CI via a `
[668] claim-godot-mcp-git-issue-524-md-007 — The fix proposes porting the pure-logic cases, starting with type_coerce round-t
[669] claim-godot-mcp-git-issue-524-md-008 — The fix proposes wiring the harness into CI as a job that only runs when `godot/
[670] claim-godot-mcp-git-issue-524-md-009 — Acceptance criteria require that type_coerce.gd and command_router.gd envelope l
[671] claim-godot-mcp-git-issue-524-md-010 — Acceptance criteria require CI to run the harness on addon changes."
[672] claim-godot-mcp-git-issue-524-md-011 — Acceptance criteria require zero skips, with the enforcement suite health rule a
[673] claim-godot-mcp-git-issue-525-md-000 — Error codes returned by the addon are raw strings written by hand in approximate
[674] claim-godot-mcp-git-issue-525-md-001 — The authoritative set of error codes is the ErrorCode enum in mcp_server/models/
[675] claim-godot-mcp-git-issue-525-md-002 — Nothing ties the addon error codes to the Python ErrorCode enum, so a typo'd or
[676] claim-godot-mcp-git-issue-525-md-003 — The proposed fix adds a const error-code registry on the GDScript side and uses
[677] claim-godot-mcp-git-issue-525-md-004 — The proposed fix adds a Python-side contract test that scans godot/addons/godot_
[678] claim-godot-mcp-git-issue-525-md-005 — The proposed contract test runs in the existing pytest suite and requires no edi
[679] claim-godot-mcp-git-issue-525-md-006 — The contract test direction alone pins the addon side without needing the GDScri
[680] claim-godot-mcp-git-issue-525-md-007 — An acceptance criterion is that a contract test fails CI when the addon emits an
[681] claim-godot-mcp-git-issue-525-md-008 — An acceptance criterion is that all current call sites pass, with an audit for e
[682] claim-godot-mcp-git-issue-525-md-009 — Issue #525 is in state CLOSED."
[683] claim-godot-mcp-git-issue-525-md-010 — Issue #525 has labels Tests and component:addon."
[684] claim-godot-mcp-git-issue-526-md-001 — The `_require_debug_session` guard is located at `command_router.gd:462-477` and
[685] claim-godot-mcp-git-issue-526-md-002 — The `_require_live_probe` guard is located at `command_router.gd:472-478` and ch
[686] claim-godot-mcp-git-issue-526-md-003 — `_cmd_get_game_scene_tree` at `runtime_session.gd:88-93` re-implements the live-
[687] claim-godot-mcp-git-issue-526-md-004 — `runtime_session._require_unpaused_live_probe()` (lines 20-29) chains `_require_
[688] claim-godot-mcp-git-issue-526-md-005 — The proposed fix is to consolidate the guards into one guard module with composa
[689] claim-godot-mcp-git-issue-526-md-006 — The proposed fix is to move the rich probe-never-connected diagnostic from `runt
[690] claim-godot-mcp-git-issue-526-md-008 — An acceptance criterion is that there is one implementation of each guard and no
[691] claim-godot-mcp-git-issue-526-md-009 — An acceptance criterion is that the #454 diagnostic ships from every probe-gated
[692] claim-godot-mcp-git-issue-526-md-010 — An acceptance criterion is that existing handler behaviors remain unchanged othe
[693] claim-godot-mcp-git-issue-527-md-000 — Issue #527 is in CLOSED state."
[694] claim-godot-mcp-git-issue-527-md-001 — Issue #527 has labels documentation and component:addon."
[695] claim-godot-mcp-git-issue-527-md-005 — The `type_coerce.gd:9` class docstring says \"Read direction (Godot → JSON) only
[696] claim-godot-mcp-git-issue-527-md-007 — In `batch.gd`, the comment \"Edit one scene file on disk…\" is attached to `_nod
[697] claim-godot-mcp-git-issue-527-md-008 — In `batch.gd`, the comment \"Resolve batch targets…\" is attached to `_init` (li
[698] claim-godot-mcp-git-issue-527-md-009 — In `batch.gd`, `_node_summary`'s own comment is on `_batch_targets`."
[699] claim-godot-mcp-git-issue-528-md-000 — batch_set_property skips UndoRedo for operations above 20 nodes, returning undoa
[700] claim-godot-mcp-git-issue-528-md-001 — composite.gd's batch_create_nodes and apply_node_edits open a single UndoRedo ac
[701] claim-godot-mcp-git-issue-528-md-002 — The hand-rolled add-child undo sequence is duplicated in three handlers: mutatio
[702] claim-godot-mcp-git-issue-528-md-003 — _commit_add_child already exists on the command router at command_router.gd:403
[703] claim-godot-mcp-git-issue-528-md-004 — The persistence-verdict stamping loop is copy-pasted between batch.gd:170-175 an
[704] claim-godot-mcp-git-issue-528-md-006 — Proposed fix: add a composite variant that registers N children in one UndoRedo
[705] claim-godot-mcp-git-issue-528-md-007 — Proposed fix: extract a _persistence_entries(nodes) helper for batch verdict sta
[706] claim-godot-mcp-git-issue-528-md-008 — Proposed fix: add a shared threshold constant and honesty fields on composite to
[707] claim-godot-mcp-git-issue-528-md-009 — Acceptance criterion: no handler hand-rolls the add-child undo sequence, and the
[708] claim-godot-mcp-git-issue-528-md-010 — Acceptance criterion: verdict stamping has one implementation used by both batch
[709] claim-godot-mcp-git-issue-528-md-011 — Acceptance criterion: envelope shapes pinned by existing tests pass unchanged."
[710] claim-godot-mcp-git-issue-529-md-000 — Issue #529 is in OPEN state."
[711] claim-godot-mcp-git-issue-529-md-001 — Undo parity is incomplete: `godot_undo` exists in core as `cmd_undo` (command_ro
[712] claim-godot-mcp-git-issue-529-md-007 — `godot_redo` is classified as `mutating` with dry_run, like `godot_undo`."
[713] claim-godot-mcp-git-issue-529-md-008 — `godot_list_history` is classified as `read_only`."
[714] claim-godot-mcp-git-issue-529-md-009 — Acceptance criterion: `godot_redo` mirrors `godot_undo`'s envelope and honesty s
[715] claim-godot-mcp-git-issue-529-md-010 — Acceptance criterion: `godot_list_history` returns the documented fields, and em
[716] claim-godot-mcp-git-issue-530-md-000 — The plugin declares `_server_version` at godot_mcp.gd:36 that nothing ever assig
[717] claim-godot-mcp-git-issue-530-md-001 — When server/addon versions drift, the failure mode is opaque per-command `VALIDA
[718] claim-godot-mcp-git-issue-530-md-002 — The proposed addon command `cmd_get_addon_info` returns `{ addon_version, godot_
[719] claim-godot-mcp-git-issue-530-md-003 — The addon version source is `plugin.cfg` or a const set at release."
[720] claim-godot-mcp-git-issue-530-md-005 — The server calls `cmd_get_addon_info` once on first successful `cmd_ping` (or la
[721] claim-godot-mcp-git-issue-530-md-006 — The server pushes `server_version` back to the addon, assigning the dock's `_ser
[722] claim-godot-mcp-git-issue-530-md-007 — The server exposes the addon info via `godot_get_server_info`, adding `addon_ver
[723] claim-godot-mcp-git-issue-530-md-008 — The server warns (structured, not stack trace) when the addon lacks handlers for
[724] claim-godot-mcp-git-issue-530-md-009 — A contract test pins the handshake envelope."
[725] claim-godot-mcp-git-issue-531-md-000 — The addon can instance a saved scene into the tree via the `scene_edit_instance_
[726] claim-godot-mcp-git-issue-531-md-002 — The proposed tool is named `godot_scene_edit_extract_scene` with category `scene
[727] claim-godot-mcp-git-issue-531-md-003 — The proposed tool's parameters include `node_path`, `scene_path` (destination `r
[728] claim-godot-mcp-git-issue-531-md-005 — If `replace_with_instance` is true, the proposed tool performs one UndoRedo acti
[729] claim-godot-mcp-git-issue-531-md-006 — The proposed tool refuses when the subtree contains nodes owned by an instanced
[730] claim-godot-mcp-git-issue-531-md-007 — The proposed tool's `dry_run` reports the node list that would be extracted plus
[731] claim-godot-mcp-git-issue-531-md-009 — An acceptance criterion is that both sides plus contract tests for the envelope
[732] claim-godot-mcp-git-issue-531-md-010 — An acceptance criterion is that the tool is undoable, `confirm`-free (additive,
[733] claim-godot-mcp-git-issue-531-md-011 — An acceptance criterion is that the tool refuses non-owned/instanced subtrees wi
[734] claim-godot-mcp-git-issue-532-md-002 — The proposed tool godot_project_move_file has toolset project, safety mutating,
[735] claim-godot-mcp-git-issue-532-md-003 — Godot 4.4+ exposes the editor's rename machinery (EditorInterface/EditorFileSyst
[736] claim-godot-mcp-git-issue-532-md-005 — The proposed response format is { old_path, new_path, updated_refs: [{file, coun
[737] claim-godot-mcp-git-issue-532-md-009 — Acceptance criteria include structured refusals for the three precondition cases
[738] claim-godot-mcp-git-issue-532-md-010 — Acceptance criteria include docs and a tool-contract entry with toolset project.
[739] claim-godot-mcp-git-issue-533-md-000 — Issue #533 is in OPEN state and labeled enhancement, component:addon."
[740] claim-godot-mcp-git-issue-533-md-004 — The proposed tool godot_core_describe_class belongs to toolset core, is read_onl
[741] claim-godot-mcp-git-issue-533-md-005 — The proposed tool takes parameters class_name, include_inherited (bool, default
[742] claim-godot-mcp-git-issue-533-md-007 — The properties field is produced via ClassDB.class_get_property_default_value pl
[743] claim-godot-mcp-git-issue-533-md-008 — The methods field is produced via class_get_method_list, yielding name, args (na
[744] claim-godot-mcp-git-issue-533-md-010 — An acceptance criterion requires a GDScript handler plus FastMCP tool with typed
[745] claim-godot-mcp-git-issue-533-md-011 — An acceptance criterion requires that an unknown class returns VALIDATION_ERROR
[746] claim-godot-mcp-git-issue-534-md-003 — The proposed server tool godot_runtime_get_output is read_only, gated by _requir
[747] claim-godot-mcp-git-issue-534-md-005 — An acceptance criterion requires ring-buffer capture with a seq cursor and no un
[748] claim-godot-mcp-git-issue-534-md-006 — An acceptance criterion requires a godot_runtime_get_output contract test (poll-
[749] claim-godot-mcp-git-issue-534-md-008 — The output ring buffer lives in the addon while the MCP server stays stateless."
[750] claim-godot-mcp-git-issue-534-md-011 — Issue #534 is in state OPEN."
[751] claim-godot-mcp-git-issue-535-md-004 — An acceptance criterion requires both sides to be implemented with snapshots tha
[752] claim-godot-mcp-git-issue-535-md-006 — An acceptance criterion requires contract tests pinning both envelopes and a bou
[753] claim-godot-mcp-git-issue-536-md-006 — Duplicates are not queued: consecutive identical values are collapsed (probe smo
[754] claim-godot-mcp-git-issue-536-md-008 — Contract test pins the new param through the envelope."
[755] claim-godot-mcp-git-issue-536-md-010 — Issue #536 is OPEN."
[756] claim-godot-mcp-git-issue-536-md-011 — Issue #536 has labels enhancement, component:addon."
[757] claim-godot-mcp-git-issue-537-md-000 — The bridge accepts only one active peer connection at a time."
[758] claim-godot-mcp-git-issue-537-md-003 — The proposed handshake has the addon send a hello containing project_path, godot
[759] claim-godot-mcp-git-issue-537-md-004 — The proposed server behavior keeps the most recent peer while exposing the conne
[760] claim-godot-mcp-git-issue-537-md-005 — The proposal logs a structured line naming both project paths when a second peer
[761] claim-godot-mcp-git-issue-537-md-006 — The proposal optionally includes previous_peer in the server info snapshot."
[762] claim-godot-mcp-git-issue-537-md-009 — Acceptance criterion: the connected editor's project path is visible via godot_g
[763] claim-godot-mcp-git-issue-537-md-010 — Acceptance criterion: peer replacement produces a structured log entry with both
[764] claim-godot-mcp-git-issue-538-md-000 — The bridge is localhost-only with no authentication in v1."
[765] claim-godot-mcp-git-issue-538-md-001 — Anything on localhost can currently inject command envelopes into the bridge."
[766] claim-godot-mcp-git-issue-538-md-003 — The proposed opt-in token is a GODOT_MCP_BRIDGE_TOKEN env var read on both sides
[767] claim-godot-mcp-git-issue-538-md-005 — The server listener refuses non-authenticated peers with a VALIDATION_ERROR-fami
[768] claim-godot-mcp-git-issue-538-md-009 — The token must never be logged and must be documented in docs/site/reference-env
[769] claim-godot-mcp-git-issue-538-md-011 — An acceptance criterion requires the both-unset path to be byte-identical to tod
[770] claim-godot-mcp-git-issue-539-md-001 — Issue #539 is in the OPEN state."
[771] claim-godot-mcp-git-issue-539-md-002 — Issue #539 has labels enhancement and component:addon."
[772] claim-godot-mcp-git-issue-539-md-003 — The function godot_mcp._update_button_icon is located at godot_mcp.gd:169-183."
[773] claim-godot-mcp-git-issue-539-md-004 — godot_mcp._update_button_icon regenerates a 16×16 ImageTexture pixel-by-pixel us
[774] claim-godot-mcp-git-issue-539-md-009 — An acceptance criterion is that there is one texture per status, built once."
[775] claim-godot-mcp-git-issue-539-md-010 — An acceptance criterion is that behavior is visually unchanged and there is no a
[776] claim-godot-mcp-git-issue-540-md-000 — MCPCommandRouter._prop_cache maps get_instance_id() to a property-type dict and
[777] claim-godot-mcp-git-issue-540-md-002 — A freed node's cache entry can be served for a new object with the same id, retu
[778] claim-godot-mcp-git-issue-540-md-004 — _invalidate_prop_cache is only called by batch/composite apply paths."
[779] claim-godot-mcp-git-issue-540-md-005 — A node deleted via cmd_delete_node leaves a stale cache entry until cap prune or
[780] claim-godot-mcp-git-issue-540-md-006 — The proposed fix keys cache validity on ObjectID plus liveness, refreshing when
[781] claim-godot-mcp-git-issue-540-md-007 — The proposed hardening calls _invalidate_prop_cache in cmd_delete_node, rename,
[782] claim-godot-mcp-git-issue-540-md-008 — An alternative proposed fix keys the cache by WeakRef/ObjectID and validates is_
[783] claim-godot-mcp-git-issue-540-md-009 — An acceptance criterion requires that a stale entry cannot survive a freed/reuse
[784] claim-godot-mcp-git-issue-540-md-010 — An acceptance criterion requires that the delete path invalidates the target's c
[785] claim-godot-mcp-git-pr-497-md-000 — PR #497 was merged on 2026-09-17."
[786] claim-godot-mcp-git-pr-497-md-002 — The addon adds a new read-only cmd_get_scan_state command returning {scanning: b
[787] claim-godot-mcp-git-pr-497-md-006 — Contract tests pin the poll ordering, the quiet path, and the stuck path."
[788] claim-godot-mcp-git-pr-497-md-007 — Both new contract tests fail without the cmd_get_scan_state poll / rescan_pendin
[789] claim-godot-mcp-git-pr-497-md-008 — is_scanning() was verified live on Godot 4.7.2 (true during the initial scan, fa
[790] claim-godot-mcp-git-pr-497-md-009 — Full preflight passed with 800 tests passed, ruff, mypy, zero-skip, and green in
[791] claim-godot-mcp-git-pr-497-md-010 — docs/tool-contracts.md was updated with the result schema and a determinism para
[792] claim-godot-mcp-git-pr-498-md-000 — PR #498 was merged on 2026-09-17."
[793] claim-godot-mcp-git-pr-498-md-004 — batch_set_property already skipped EditorUndoRedoManager above 20 nodes as a per
[794] claim-godot-mcp-git-pr-498-md-005 — batch_set_property now reports undoable: false with a hint for >20-node batches
[795] claim-godot-mcp-git-pr-498-md-006 — Contract tests pin both new reporting behaviors."
[796] claim-godot-mcp-git-pr-498-md-007 — docs/tool-contracts.md was updated."
[797] claim-godot-mcp-git-pr-498-md-008 — The PR closes issue #437."
[798] claim-godot-mcp-git-pr-498-md-009 — Live e2e tests against Godot 4.7.2 verified a 25-node batch yields undoable:fals
[799] claim-godot-mcp-git-pr-498-md-010 — Full preflight passed 803 tests with ruff, mypy, and zero-skip."
[800] claim-godot-mcp-git-pr-499-md-000 — PR #499 was merged on 2026-09-17 and carries the documentation label."
[801] claim-godot-mcp-git-pr-499-md-001 — Calling `create_scene(root_type=\"Collectible\")` on a registered custom `class_
[802] claim-godot-mcp-git-pr-499-md-003 — The `root_type` limitation is stated in the `godot_scene_edit_create_scene` tool
[803] claim-godot-mcp-git-pr-499-md-004 — The `root_type` limitation is stated in `docs/tool-contracts.md` along with the
[804] claim-godot-mcp-git-pr-499-md-005 — The documented workaround is to create the scene with a base type and then call
[805] claim-godot-mcp-git-pr-499-md-006 — The change to `mcp_server/tools/mutation.py` added 4 lines and removed 0 lines."
[806] claim-godot-mcp-git-pr-499-md-007 — The change to `docs/tool-contracts.md` added 6 lines and removed 0 lines."
[807] claim-godot-mcp-git-pr-499-md-008 — The PR is docs-only and the ruff, mypy, and contract suites pass with zero skips
[808] claim-godot-mcp-git-pr-499-md-009 — Issue #429 is assessed as partially compliant, with the PR choosing the document
[809] claim-godot-mcp-git-pr-499-md-010 — The PR reviewer guide assigns an estimated review effort of 1 and a score of 95.
[810] claim-godot-mcp-git-pr-500-md-000 — PR #500 is a CalVer release bump from 2026.09.10 to 2026.09.17."
[811] claim-godot-mcp-git-pr-500-md-001 — PR #500 was merged on 2026-09-17."
[812] claim-godot-mcp-git-pr-500-md-002 — The release is additive-only since the last tag, so CONTRACT_VERSION stays at 1.
[813] claim-godot-mcp-git-pr-500-md-003 — The version bump is applied in lockstep across pyproject.toml, mcp_server/__init
[814] claim-godot-mcp-git-pr-500-md-005 — mcp_server/__init__.py was modified to bump the Python package version."
[815] claim-godot-mcp-git-pr-500-md-006 — godot/addons/godot_mcp/plugin.cfg was modified to bump the Godot addon version."
[816] claim-godot-mcp-git-pr-500-md-007 — pyproject.toml was modified to bump the Python project version."
[817] claim-godot-mcp-git-pr-500-md-009 — Issue #490 is rated partially compliant because the PR is a version bump only wi
[818] claim-godot-mcp-git-pr-501-md-000 — PR #501 was merged on 2026-09-18."
[819] claim-godot-mcp-git-pr-501-md-002 — Setting undoable: false on batches of more than 20 nodes means undo will not rev
[820] claim-godot-mcp-git-pr-501-md-007 — set_setting performs key validation and returns a did-you-mean hint."
[821] claim-godot-mcp-git-pr-501-md-009 — Verification of the change showed tests/unit/test_skills_metadata.py green and t
[822] claim-godot-mcp-git-pr-501-md-010 — AGENTS.md was changed by +5/-2 lines."
[823] claim-godot-mcp-git-pr-501-md-011 — The PR reviewer guide rated the PR with a score of 92 and an estimated review ef
[824] claim-godot-mcp-git-pr-502-md-000 — PR #502 updates the tool count to 181 in documentation."
[825] claim-godot-mcp-git-pr-502-md-001 — PR #502 is merged as of 2026-09-18."
[826] claim-godot-mcp-git-pr-502-md-002 — PR #502 has the documentation label."
[827] claim-godot-mcp-git-pr-502-md-004 — The 180 count was stale in README (×3), AGENTS.md, skills/README, and godot-gett
[828] claim-godot-mcp-git-pr-502-md-006 — The PR type is Documentation."
[829] claim-godot-mcp-git-pr-502-md-007 — AGENTS.md updated the tool count from 180 to 181 in the \"Current state\" sectio
[830] claim-godot-mcp-git-pr-502-md-008 — README.md updated the tool count from 180 to 181 in three locations."
[831] claim-godot-mcp-git-pr-502-md-009 — skills/README.md updated the tool count from 180 to 181 in the skills documentat
[832] claim-godot-mcp-git-pr-502-md-010 — skills/godot-getting-started/SKILL.md updated the tool count from 180 to 181 in
[833] claim-godot-mcp-git-pr-502-md-011 — The estimated effort to review PR #502 is 1."
[834] claim-godot-mcp-git-pr-503-md-000 — PR #503 is merged as of 2026-09-18."
[835] claim-godot-mcp-git-pr-503-md-001 — PR #503 has labels enhancement, Review effort 3/5, and Bug fix."
[836] claim-godot-mcp-git-pr-503-md-007 — `batch_set_property` and `apply_node_edits` now carry a `persistence[]` array wi
[837] claim-godot-mcp-git-pr-503-md-011 — The addon compiles clean on Godot 4.7, and full preflight is green with 807 pass
[838] claim-godot-mcp-git-pr-504-md-000 — PR #504 was merged on 2026-09-18."
[839] claim-godot-mcp-git-pr-504-md-001 — The godot_scene_edit_set_editable_children tool is mutating, UndoRedo-wrapped, a
[840] claim-godot-mcp-git-pr-504-md-002 — The set_editable_children tool refuses local nodes, which would otherwise be a s
[841] claim-godot-mcp-git-pr-504-md-004 — Instanced nodes' children carry an `owner` field holding the source scene's res:
[842] claim-godot-mcp-git-pr-504-md-005 — Local nodes carry neither the `owner` nor the `editable_children` key in the ser
[843] claim-godot-mcp-git-pr-504-md-006 — The PR updates docs/tool-contracts.md with a tool row and the SceneNode shape."
[844] claim-godot-mcp-git-pr-504-md-008 — The preflight run passed with 811 tests and clean ruff/mypy/zero-skip checks."
[845] claim-godot-mcp-git-pr-504-md-009 — Issue #487 is rated partially compliant, with auto-enabling editable children wh
[846] claim-godot-mcp-git-pr-505-md-001 — PR #505 was merged on 2026-09-18."
[847] claim-godot-mcp-git-pr-505-md-002 — PR #505 implements issue #459, generalizing #457's capture-path pattern."
[848] claim-godot-mcp-git-pr-505-md-007 — A shared reason-token table was added to `docs/tool-contracts.md`."
[849] claim-godot-mcp-git-pr-505-md-008 — The addition is additive, so `CONTRACT_VERSION` stays 1."
[850] claim-godot-mcp-git-pr-505-md-010 — The addon compiles clean on Godot 4.7."
[851] claim-godot-mcp-git-pr-505-md-011 — Full preflight passed with 813 tests, ruff, mypy, and zero-skip."
[852] claim-godot-mcp-git-pr-506-md-000 — PR #506 was merged on 2026-09-18."
[853] claim-godot-mcp-git-pr-506-md-001 — PR #506 carries the labels enhancement and Tests."
[854] claim-godot-mcp-git-pr-506-md-003 — The addon's layout read now echoes each effect's exported property values using
[855] claim-godot-mcp-git-pr-506-md-004 — AudioBusEffectInfo gains a properties field of type dict[str, Any], an additive
[856] claim-godot-mcp-git-pr-506-md-006 — A red-first contract test named test_get_bus_layout_echoes_effect_properties was
[857] claim-godot-mcp-git-pr-506-md-007 — The handler file godot/addons/godot_mcp/handlers/audio.gd was changed by +11/-0
[858] claim-godot-mcp-git-pr-507-md-000 — PR #507 was merged on 2026-09-18."
[859] claim-godot-mcp-git-pr-507-md-001 — The new godot_shader_validate tool is read_only, belongs to the shader toolset,
[860] claim-godot-mcp-git-pr-507-md-003 — The throwaway runner and its .uid sidecar are deleted after the run."
[861] claim-godot-mcp-git-pr-507-md-007 — Live on Godot 4.7.2, the issue's exact repro (uniform float edge_width : float)
[862] claim-godot-mcp-git-pr-507-md-009 — The full preflight run passed 816 tests with ruff, mypy, and zero skips."
[863] claim-godot-mcp-git-pr-508-md-000 — PR #508, titled \"Add AudioStreamWAV loop settings to import_asset\", was merged
[864] claim-godot-mcp-git-pr-508-md-001 — import_asset accepts loop configuration for .wav targets via options.import_sett
[865] claim-godot-mcp-git-pr-508-md-002 — The handler patches the .import sidecar's edit/loop_* params (ResourceImporterWA
[866] claim-godot-mcp-git-pr-508-md-004 — The loop_applied field in the result reports whether the config was applied this
[867] claim-godot-mcp-git-pr-508-md-005 — Live verification on Godot 4.7.2 showed importing a .wav with loop_mode: 1 yield
[868] claim-godot-mcp-git-pr-508-md-006 — A red-first contract test named test_import_wav_loop_mode_applied was added, and
[869] claim-godot-mcp-git-pr-508-md-008 — The addon file import_asset.gd adds a _set_wav_loop function that patches the .i
[870] claim-godot-mcp-git-pr-508-md-011 — Issue 418 was assessed as partially compliant by the PR review."
[871] claim-godot-mcp-git-pr-509-md-000 — PR #509 was merged on 2026-09-19."
[872] claim-godot-mcp-git-pr-509-md-001 — The new tool `godot_scene_edit_rescan_filesystem` is registered with the `read_o
[873] claim-godot-mcp-git-pr-509-md-002 — The tool triggers `EditorFileSystem.scan()` so external edits to `.tscn`/`.gd` f
[874] claim-godot-mcp-git-pr-509-md-004 — `reload_scene` discards unsaved changes and remains confirm-gated, unlike the ne
[875] claim-godot-mcp-git-pr-509-md-006 — Live verification on Godot 4.7.2 via the bridge showed an externally written `.g
[876] claim-godot-mcp-git-pr-509-md-007 — The full preflight run passed 819 tests with ruff, mypy, and zero skips."
[877] claim-godot-mcp-git-pr-509-md-008 — `mcp_server/command_map.py` added a mapping from `scene_edit_rescan_filesystem`
[878] claim-godot-mcp-git-pr-509-md-009 — `mcp_server/models/scene_session.py` added a `RescanFilesystemResult` Pydantic m
[879] claim-godot-mcp-git-pr-509-md-010 — The addon handler `cmd_rescan_filesystem` calls `EditorFileSystem.scan()` and re
[880] claim-godot-mcp-git-pr-510-md-000 — PR #510 was merged on 2026-09-19."
[881] claim-godot-mcp-git-pr-510-md-001 — The release bumps the CalVer version from 2026.09.17 to 2026.09.19."
[882] claim-godot-mcp-git-pr-510-md-002 — The change is additive-only since the last tag and CONTRACT_VERSION remains 1."
[883] claim-godot-mcp-git-pr-510-md-003 — The tool surface grows from 181 to 184 tools, adding set_editable_children, vali
[884] claim-godot-mcp-git-pr-510-md-005 — PR #510 carries the labels documentation, enhancement, and Review effort 1/5."
[885] claim-godot-mcp-git-pr-510-md-006 — The PR syncs version strings across docs and config."
[886] claim-godot-mcp-git-pr-510-md-007 — Ticket #458 was assessed as partially compliant with no compliant requirements."
[887] claim-godot-mcp-git-pr-510-md-009 — The estimated effort to review PR #510 is 1 out of 5."
[888] claim-godot-mcp-git-pr-510-md-010 — The PR review score is 95."
[889] claim-godot-mcp-git-pr-510-md-011 — The review reports no relevant tests for the PR."
[890] claim-godot-mcp-git-pr-511-md-000 — PR #511 adds a MkDocs documentation site and GitHub Pages deployment."
[891] claim-godot-mcp-git-pr-511-md-001 — PR #511 was merged on 2026-09-19."
[892] claim-godot-mcp-git-pr-511-md-002 — The documentation site uses MkDocs Material and is hosted at https://hybridindie
[893] claim-godot-mcp-git-pr-511-md-003 — The PR adds 17 new documentation pages."
[894] claim-godot-mcp-git-pr-511-md-004 — The architecture deep-dive consists of 7 pages."
[895] claim-godot-mcp-git-pr-511-md-005 — The getting started section consists of 5 pages."
[896] claim-godot-mcp-git-pr-511-md-007 — The guides section consists of 3 pages."
[897] claim-godot-mcp-git-pr-511-md-011 — Verification showed a clean `mkdocs build --strict`, rendering of mermaid diagra
[898] claim-godot-mcp-git-pr-512-md-000 — PR #512 titled \"Fix docs toolchain installation in CI\" was merged on 2026-09-1
[899] claim-godot-mcp-git-pr-512-md-004 — The PR is labeled as a Bug fix."
[900] claim-godot-mcp-git-pr-512-md-005 — The PR modified the file .github/workflows/pages.yml."
[901] claim-godot-mcp-git-pr-512-md-008 — The pages.yml change consists of 5 additions and 3 deletions."
[902] claim-godot-mcp-git-pr-512-md-009 — The automated PR review estimated the effort to review as 1 out of 5."
[903] claim-godot-mcp-git-pr-512-md-010 — The automated PR review assigned a score of 95."
[904] claim-godot-mcp-git-pr-513-md-000 — PR #513 is titled \"Add LLM-friendly documentation endpoints and promote site\".
[905] claim-godot-mcp-git-pr-513-md-001 — PR #513 was merged on 2026-09-19."
[906] claim-godot-mcp-git-pr-513-md-002 — PR #513 carries the labels documentation and enhancement."
[907] claim-godot-mcp-git-pr-513-md-003 — `/llms.txt` (page index) and `/llms-full.txt` (whole site as one markdown docume
[908] claim-godot-mcp-git-pr-513-md-004 — The PR promotes the documentation site across README, AGENTS.md, skills/README,
[909] claim-godot-mcp-git-pr-513-md-005 — `mkdocs-llmstxt>=0.2,<0.4` is pinned in `requirements-docs.txt` and added to the
[910] claim-godot-mcp-git-pr-513-md-006 — `mkdocs build --strict` runs clean with the plugin and both `llms.txt` and `llms
[911] claim-godot-mcp-git-pr-513-md-007 — The full repo preflight reported 819 passed with ruff, mypy, and zero-skip."
[912] claim-godot-mcp-git-pr-513-md-008 — The PR review scored the change 92."
[913] claim-godot-mcp-git-pr-513-md-009 — The review found no relevant tests, no security concerns, and no TODO sections."
[914] claim-godot-mcp-git-pr-513-md-010 — The `mkdocs-exclude` plugin is installed in the CI workflow and `requirements-do
[915] claim-godot-mcp-git-pr-514-md-000 — PR #514 ports the documentation site from MkDocs to the same VitePress tooling,
[916] claim-godot-mcp-git-pr-514-md-001 — PR #514 was merged on 2026-09-19."
[917] claim-godot-mcp-git-pr-514-md-003 — docs/site/llms-gen.mjs runs as a post-build step and generates llms.txt and llms
[918] claim-godot-mcp-git-pr-514-md-005 — The mkdocs pages.yml and mkdocs.yml/requirements-docs.txt files are removed by t
[919] claim-godot-mcp-git-pr-514-md-006 — All 27 content pages were migrated with cross-links verified by VitePress's dead
[920] claim-godot-mcp-git-pr-514-md-007 — npm run build exits zero with zero dead links and generates dist/llms.txt and di
[921] claim-godot-mcp-git-pr-514-md-010 — PR #514 carries the labels documentation and enhancement."
[922] claim-godot-mcp-git-pr-515-md-000 — PR #515 was merged on 2026-09-19."
[923] claim-godot-mcp-git-pr-515-md-002 — VitePress without `cleanUrls` renders `what-why.html`."
[924] claim-godot-mcp-git-pr-515-md-003 — Every deep link in llms.txt was a 404."
[925] claim-godot-mcp-git-pr-515-md-004 — The URL mapping was fixed to match what VitePress actually serves."
[926] claim-godot-mcp-git-pr-515-md-006 — The llms-full.txt content was unaffected because it is raw markdown."
[927] claim-godot-mcp-git-pr-515-md-007 — The PR modified docs/site/llms-gen.mjs."
[928] claim-godot-mcp-git-pr-515-md-010 — The URL mapping was fixed to match VitePress default rendering behavior."
[929] claim-godot-mcp-git-pr-515-md-011 — No relevant tests were found for the PR."
[930] claim-godot-mcp-git-pr-516-md-000 — PR #516 was merged on 2026-09-19."
[931] claim-godot-mcp-git-pr-516-md-001 — PR #516 carries the documentation label."
[932] claim-godot-mcp-git-pr-516-md-002 — 27 per-page markdown variants are generated by llms-gen.mjs with frontmatter str
[933] claim-godot-mcp-git-pr-516-md-003 — Every rendered page's head carries a describedby link to llms.txt and an alterna
[934] claim-godot-mcp-git-pr-516-md-005 — llms.txt follows the exact v2 file format: H1, blockquote, details, H2 file list
[935] claim-godot-mcp-git-pr-516-md-006 — Local build verification produced dist/llms.txt, dist/llms-full.txt, and 27 *.ht
[936] claim-godot-mcp-git-pr-516-md-007 — Full repo preflight reported 819 passed with ruff, mypy, and zero-skip."
[937] claim-godot-mcp-git-pr-516-md-009 — robots.txt was added with comments pointing agents to llms.txt, .html.md variant
[938] claim-godot-mcp-git-pr-516-md-010 — The PR introduces significant new behavior (27 page.html.md variants, llms.txt v
[939] claim-godot-mcp-git-pr-517-md-000 — PR #517 is in MERGED state, having been merged on 2026-09-19."
[940] claim-godot-mcp-git-pr-517-md-006 — Sidebar, index pages, and llms-gen.mjs sections were updated so the new pages fl
[941] claim-godot-mcp-git-pr-517-md-007 — Running `npm run build` produced zero dead links, with new pages and .html.md va
[942] claim-godot-mcp-git-pr-517-md-009 — The PR-Agent review scored the PR 95."
[943] claim-godot-mcp-git-pr-518-md-000 — PR #518 was merged on 2026-09-19."
[944] claim-godot-mcp-git-pr-518-md-002 — VitePress only dead-link-checks markdown body links, allowing 13 config links to
[945] claim-godot-mcp-git-pr-518-md-003 — All 16 stale config links were rewritten to the real flat page names, with archi
[946] claim-godot-mcp-git-pr-518-md-004 — A new guard script docs/site/check-links.mjs is chained into npm run build."
[947] claim-godot-mcp-git-pr-518-md-006 — npm run build exits zero and prints 'checked 32 nav/sidebar links: all resolve'.
[948] claim-godot-mcp-git-pr-518-md-008 — The check-links.mjs file change was +31/-0 lines."
[949] claim-godot-mcp-git-pr-518-md-009 — A reviewer noted the regex /link: '([^']+)'/g only matches single-quoted link va
[950] claim-godot-mcp-git-pr-519-md-000 — PR #519 was merged on 2026-09-19."
[951] claim-godot-mcp-git-pr-519-md-001 — PR #519 fixes dead nav/sidebar links in the VitePress config."
[952] claim-godot-mcp-git-pr-519-md-003 — All 13 stale subdirectory links in .vitepress/config.mts were rewritten to flat
[953] claim-godot-mcp-git-pr-519-md-004 — After npm run build, dist/concepts.html contains 0 occurrences of the old gettin
[954] claim-godot-mcp-git-pr-519-md-005 — The link guard passes with 32 nav/sidebar links resolving."
[955] claim-godot-mcp-git-pr-519-md-007 — Architecture/* links were kept because those pages genuinely live in the subdire
[956] claim-godot-mcp-git-pr-519-md-008 — The guard check-links.mjs is not included in PR #519's diff because it was alrea
[957] claim-godot-mcp-git-pr-519-md-009 — PR #519 rewrites 13 links to flat paths but does not include the corresponding .
[958] claim-godot-mcp-git-pr-541-md-000 — PR #541 adds a contract test that source-scans GDScript addon files and asserts
[959] claim-godot-mcp-git-pr-541-md-002 — The scan was verified to turn red on an injected `NOT_A_REAL_CODE` before commit
[960] claim-godot-mcp-git-pr-541-md-005 — Running `uv run pytest tests/contract/test_addon_error_codes.py` produced 2 pass
[961] claim-godot-mcp-git-pr-541-md-006 — The full test suite reported 821 passed with zero skips."
[962] claim-godot-mcp-git-pr-541-md-007 — PR #541 was merged on 2026-09-20."
[963] claim-godot-mcp-git-pr-541-md-008 — The test file `test_addon_error_codes.py` was added with a diff of +92/-0 lines.
[964] claim-godot-mcp-git-pr-541-md-009 — The reviewer noted the `_FAIL_CALL` regex only matches `_fail(\"CODE\", ...)` wh
[965] claim-godot-mcp-git-pr-541-md-011 — All 338 audited call sites pass error codes as string literals, with no variable
[966] claim-godot-mcp-git-pr-542-md-000 — PR #542 was merged on 2026-09-20."
[967] claim-godot-mcp-git-pr-542-md-001 — The new file godot/tests/type_coerce_smoke.gd contains 34 headless checks pinnin
[968] claim-godot-mcp-git-pr-542-md-002 — godot/tests/run_commands_smoke.gd was extended to cover the #461 honest-abort co
[969] claim-godot-mcp-git-pr-542-md-003 — tests/integration/test_addon_read_smokes.py registers type_coerce_smoke in the p
[970] claim-godot-mcp-git-pr-542-md-004 — The implementation chose the repo's existing headless SceneTree exerciser plus p
[971] claim-godot-mcp-git-pr-542-md-006 — The tests have zero skips and run on any machine with Godot 4.4+."
[972] claim-godot-mcp-git-pr-542-md-007 — Running godot --headless --path godot/ --script res://tests/type_coerce_smoke.gd
[973] claim-godot-mcp-git-pr-542-md-008 — Running uv run pytest tests/integration/test_addon_read_smokes.py resulted in 8
[974] claim-godot-mcp-git-pr-542-md-009 — The full test suite reported 822 passed with zero skips, and ruff plus mypy were
[975] claim-godot-mcp-git-pr-542-md-010 — tests/contract/test_addon_error_codes.py adds a contract test ensuring addon err
[976] claim-godot-mcp-git-pr-542-md-011 — The PR review found that a CI job running when godot/addons/** changes was not a
[977] claim-godot-mcp-git-pr-543-md-000 — PR #543 implements the server↔addon handshake from issue #530, closing #521 as a
[978] claim-godot-mcp-git-pr-543-md-001 — cmd_get_addon_info self-describes with addon_version (live from plugin.cfg, sing
[979] claim-godot-mcp-git-pr-543-md-002 — cmd_server_hello {version} stores the server's pushed package version in router.
[980] claim-godot-mcp-git-pr-543-md-004 — The first successful handshake fire-and-forgets cmd_server_hello {version: __ver
[981] claim-godot-mcp-git-pr-543-md-005 — BridgeDiagnostics gains addon_version/addon_commands and ServerDiagnostics gains
[982] claim-godot-mcp-git-pr-543-md-006 — A server↔addon version mismatch surfaces in godot_get_server_info as an addon_dr
[983] claim-godot-mcp-git-pr-543-md-007 — The headless handshake smoke test run via godot --headless --script res://tests/
[984] claim-godot-mcp-git-pr-543-md-008 — tests/contract/test_addon_handshake.py reports 10 passed covering shape, caching
[985] claim-godot-mcp-git-pr-543-md-009 — The full test suite reports 832 passed with zero skips and ruff + mypy clean."
[986] claim-godot-mcp-git-pr-543-md-010 — The addon_info method was not protected by a lock, so two concurrent first calls
[987] claim-godot-mcp-git-pr-543-md-011 — The race was fixed in commit c6d46e5 by taking _addon_info_lock only while the c
[988] claim-godot-mcp-git-pr-544-md-000 — PR #544 was merged on 2026-09-20."
[989] claim-godot-mcp-git-pr-544-md-001 — Three drifted guard flavors were consolidated into one module, godot/addons/godo
[990] claim-godot-mcp-git-pr-544-md-002 — The #454 \"max client limits reached\" recovery diagnostic now ships from every
[991] claim-godot-mcp-git-pr-544-md-003 — get_game_scene_tree deliberately keeps its soft {playing, connected: false, prob
[992] claim-godot-mcp-git-pr-544-md-006 — The contract test tests/contract/test_addon_guards.py passed 5 tests."
[993] claim-godot-mcp-git-pr-544-md-007 — Running godot --headless --path godot/ --script res://tests/guards_smoke.gd prod
[994] claim-godot-mcp-git-pr-544-md-008 — The contract and unit suites reported 781 passed with zero skips, and ruff plus
[995] claim-godot-mcp-git-pr-544-md-009 — The PR reviewer bot assessed ticket #527 as partially compliant."
[996] claim-godot-mcp-git-pr-545-md-000 — PR #545 was merged on 2026-09-20."
[997] claim-godot-mcp-git-pr-545-md-001 — command_router.gd defines a single shared constant MCP_UNDO_THRESHOLD := 20 plus
[998] claim-godot-mcp-git-pr-545-md-002 — Before this PR, composite.gd's batch_create_nodes and apply_node_edits had no Un
[999] claim-godot-mcp-git-pr-545-md-003 — In composite.gd both batch tools became threshold-aware: above the threshold the
[1000] claim-godot-mcp-git-pr-545-md-005 — Running threshold_smoke.gd headless produced THRESHOLD_TEST_OK covering boundari
[1001] claim-godot-mcp-git-pr-545-md-006 — The full test suite at the time of the PR description reported 844 passed with z
[1002] claim-godot-mcp-git-pr-545-md-007 — Review found that BatchCreateNodesResult previously had a dry_run: bool = False
[1003] claim-godot-mcp-git-pr-545-md-009 — BatchCreateNodesResult regained the dry_run: bool = False field, and the server-
[1004] claim-godot-mcp-git-pr-545-md-010 — Both _cmd_batch_create_nodes and _cmd_apply_node_edits now check params.get(\"dr
[1005] claim-godot-mcp-git-pr-545-md-011 — After the fixes, the full suite reported 846 passed with zero skips and clean ru
[1006] claim-godot-mcp-git-pr-546-md-000 — PR #546 was merged on 2026-09-20."
[1007] claim-godot-mcp-git-pr-546-md-001 — The router was approximately 816 lines before the refactor."
[1008] claim-godot-mcp-git-pr-546-md-002 — About two-thirds of the router was boilerplate and a helpers grab-bag."
[1009] claim-godot-mcp-git-pr-546-md-003 — command_router.gd was reduced from 816 to 479 lines."
[1010] claim-godot-mcp-git-pr-546-md-007 — Shared-logic call sites changed from `_router._X` to `_router._helpers.X`."
[1011] claim-godot-mcp-git-pr-546-md-009 — tests/contract/test_router_refactor.py has 5 passing tests."
[1012] claim-godot-mcp-git-pr-546-md-010 — The full test suite reported 852 passed with zero skips."
[1013] claim-godot-mcp-git-pr-547-md-004 — The editor pulls game output on demand via godot_mcp:get_output → godot_mcp:game
[1014] claim-godot-mcp-git-pr-547-md-007 — The server tool godot_runtime_get_game_output is read_only in the runtime toolse
[1015] claim-godot-mcp-godot-mcp-agents-md-000 — godot-mcp is a standalone MCP server providing generic Godot editor control over
[1016] claim-godot-mcp-godot-mcp-agents-md-005 — The Godot editor dials the bridge connection and reconnects, while the server st
[1017] claim-godot-mcp-godot-mcp-agents-md-006 — The MCP server owns all safety/permission logic and Pydantic domain models and h
[1018] claim-godot-mcp-godot-mcp-agents-md-007 — The Godot addon is a GDScript EditorPlugin (Godot 4.4+) whose WebSocketPeer clie
[1019] claim-godot-mcp-godot-mcp-agents-md-009 — Every tool is tagged with a safety class (read_only, mutating, destructive, or r
[1020] claim-godot-mcp-godot-mcp-agents-md-010 — Every MCP tool is exposed as godot_<toolset>_<action>, with the mapping applied
[1021] claim-godot-mcp-godot-mcp-agents-md-011 — The toolchain requires Godot 4.4+ (validated on 4.7-stable), Python 3.11+, and F
[1022] claim-godot-mcp-godot-mcp-contributing-md-000 — godot-mcp is a standalone MCP server that drives a live Godot editor from AI age
[1023] claim-godot-mcp-godot-mcp-contributing-md-001 — godot-mcp requires Python 3.11+ managed with uv."
[1024] claim-godot-mcp-godot-mcp-contributing-md-002 — godot-mcp requires Godot 4.4+ and is validated on 4.7-stable."
[1025] claim-godot-mcp-godot-mcp-contributing-md-003 — godot-mcp uses FastMCP 4.0.1, which is GA on MCP SDK v2 (the 2026-07-28 sessionl
[1026] claim-godot-mcp-godot-mcp-contributing-md-004 — The workflow is an issue-driven pipeline in which every merge traces to a GitHub
[1027] claim-godot-mcp-godot-mcp-contributing-md-005 — godot-mcp is composed of an AI client connected via stdio to a FastMCP Python se
[1028] claim-godot-mcp-godot-mcp-contributing-md-006 — The MCP server owns all safety/permission logic, Pydantic models, and tool schem
[1029] claim-godot-mcp-godot-mcp-contributing-md-007 — The Godot addon is the only layer that touches the Godot Editor API and routes c
[1030] claim-godot-mcp-godot-mcp-contributing-md-008 — Every tool is tagged with one of four safety classes: read_only, mutating, destr
[1031] claim-godot-mcp-godot-mcp-contributing-md-011 — Releases are automated via .github/workflows/publish.yml and triggered on GitHub
[1032] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-000 — The Godot editor dials the WebSocket connection and the MCP server listens, but
[1033] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-001 — The MCP server is a FastMCP server implemented in Python under mcp_server/."
[1034] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-003 — The Godot addon is written in GDScript with the @tool annotation and lives in ad
[1035] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-004 — mcp_bridge.gd is the WebSocket client that connects to a URL and reconnects with
[1036] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-005 — The addon dials out to the server at ws://127.0.0.1:9080."
[1037] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-006 — The MCP server boots, binds port 9080, and waits for the addon to connect."
[1038] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-008 — The server owns all safety and preconditions while the addon owns all Godot call
[1039] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-010 — The AI client communicates with the MCP server over stdio using the MCP protocol
[1040] claim-godot-mcp-godot-mcp-docs-architecture-md-000 — The bridge connection direction is inverted so that the server listens and the G
[1041] claim-godot-mcp-godot-mcp-docs-architecture-md-001 — The bridge URL defaults to ws://127.0.0.1:9080, is configurable on both sides vi
[1042] claim-godot-mcp-godot-mcp-docs-architecture-md-007 — Error codes must be stable and drawn only from the enumerated set, never ad-hoc
[1043] claim-godot-mcp-godot-mcp-docs-architecture-md-008 — Godot types cross the bridge as JSON-safe forms coerced on the addon side in the
[1044] claim-godot-mcp-godot-mcp-docs-architecture-md-010 — To inspect or drive a running game, the game must be launched from the editor so
[1045] claim-godot-mcp-godot-mcp-docs-debugger-feasibility-md-000 — The Godot editor-to-game debugger protocol supports step control, stack-frame in
[1046] claim-godot-mcp-godot-mcp-docs-debugger-feasibility-md-001 — A Tier 2 debugger toolset (step_*, continue, godot_debugger_get_stack_frames, go
[1047] claim-godot-mcp-godot-mcp-docs-harness-performance-md-000 — The Godot editor is single-threaded: the addon drains queued command packets onc
[1048] claim-godot-mcp-godot-mcp-docs-harness-performance-md-001 — The server cannot parallelize past the single-threaded editor, so the only lever
[1049] claim-godot-mcp-godot-mcp-docs-harness-performance-md-003 — godot_composite_run_commands executes a whole list of N commands in a single fra
[1050] claim-godot-mcp-godot-mcp-docs-harness-performance-md-004 — Each sub-mutation in a composite batch wraps its own UndoRedo action and command
[1051] claim-godot-mcp-godot-mcp-docs-harness-performance-md-005 — godot_composite_run_commands cannot be nested."
[1052] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-000 — The MCP spec's 2026-07-28 revision removes sessions and the initialize handshake
[1053] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-001 — The 2026-07-28 revision defines a stateless protocol with no session lifecycle a
[1054] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-002 — In the 2026-07-28 revision, per-request `_meta` carries version/capabilities ins
[1055] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-003 — Cross-call state in the 2026-07-28 revision moves to explicit handles: server-mi
[1056] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-004 — The 2026-07-28 revision replaces handshake capability probing with `server/disco
[1057] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-005 — godot-mcp is pinned to FastMCP 4.0.0b3 which speaks 2025-era session semantics,
[1058] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-007 — Toolset enable/disable in ToolsetMiddleware has no session dependency and uses a
[1059] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-008 — The destructive-tool approval guard in ApprovalMiddleware has no session depende
[1060] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-010 — The design decision rejects a session_handle/toolset_grant token because godot-m
[1061] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-000 — Every @mcp.tool takes typed parameters and returns a typed Pydantic model, never
[1062] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-001 — Every @mcp.tool validates inputs and checks preconditions before any side effect
[1063] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-002 — Every @mcp.tool is delegation only, with no domain branching in the handler body
[1064] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-003 — Mutating tools must accept a dry_run boolean parameter defaulting to False."
[1065] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-004 — Destructive tools must accept dry_run and require a confirm boolean parameter de
[1066] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-005 — dry_run=True returns what would happen and performs nothing."
[1067] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-006 — All safety logic lives in mcp_server/safety.py and never in the addon."
[1068] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-009 — An optional webhook gates destructive tools behind a human decision and is opt-i
[1069] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-010 — The approval gate runs at the tools/call boundary via ApprovalMiddleware (issue
[1070] claim-godot-mcp-godot-mcp-docs-tutorial-md-000 — godot-mcp requires Godot 4.4+, uv, and the godot-mcp addon enabled in the projec
[1071] claim-godot-mcp-godot-mcp-docs-tutorial-md-001 — Every time the MCP client connects, the server sends initialization instructions
[1072] claim-godot-mcp-godot-mcp-docs-tutorial-md-003 — The mandatory protocol is to call godot_get_server_info(), godot_list_toolsets()
[1073] claim-godot-mcp-godot-mcp-docs-tutorial-md-004 — The server exposes workflow prompts that the LLM can discover and use."
[1074] claim-godot-mcp-godot-mcp-docs-tutorial-md-005 — The LLM can discover prompts via list_prompts() and render them via get_prompt(n
[1075] claim-godot-mcp-godot-mcp-docs-tutorial-md-007 — If an MCP client does not surface server instructions or prompts, a system promp
[1076] claim-godot-mcp-godot-mcp-docs-tutorial-md-008 — If you get 'ToolError: unknown tool', the toolset is not enabled and you should
[1077] claim-godot-mcp-godot-mcp-readme-md-001 — The current release version is 2026.09.10, described as the first stable release
[1078] claim-godot-mcp-godot-mcp-readme-md-002 — Godot 4.4 is the minimum supported version and 4.7 is the recommended validated
[1079] claim-godot-mcp-godot-mcp-readme-md-003 — Python 3.11 is the minimum supported version and 3.13 is recommended."
[1080] claim-godot-mcp-godot-mcp-readme-md-004 — The server listens on http://localhost:9090 for MCP HTTP and ws://localhost:9080
[1081] claim-godot-mcp-godot-mcp-readme-md-005 — The Godot addon connects out to the MCP server's bridge listener at ws://127.0.0
[1082] claim-godot-mcp-godot-mcp-readme-md-006 — The full pytest suite contains approximately 304 tests."
[1083] claim-godot-mcp-godot-mcp-readme-md-007 — The addon's command router handles 80+ cmd_* commands that call the Godot Editor
[1084] claim-godot-mcp-godot-mcp-readme-md-008 — The bridge to the editor is a single connection that only one server process can
[1085] claim-godot-mcp-godot-mcp-readme-md-010 — Destructive-class tools require both dry_run and confirm: bool = True parameters
[1086] claim-instructions-and-rules-instructions-and-rules-agents-md-000 — The repository generates AI assistant harnesses for `.claude/`, `.github/`, and
[1087] claim-instructions-and-rules-instructions-and-rules-agents-md-001 — The repository hosts the Epic Scoping Skills as its own installed harness."
[1088] claim-instructions-and-rules-instructions-and-rules-agents-md-003 — The Genesis harness renders `templates/_shared/` into target projects via `boots
[1089] claim-instructions-and-rules-instructions-and-rules-agents-md-004 — The Epic Scoping Skills system uses `.agents/` as its source directory with thin
[1090] claim-instructions-and-rules-instructions-and-rules-agents-md-005 — The golden rule prohibits duplicating content into a wrapper; content must be ed
[1091] claim-instructions-and-rules-instructions-and-rules-agents-md-006 — Shared rules referenced by multiple files live in a `doctrine/` layer and must b
[1092] claim-instructions-and-rules-instructions-and-rules-agents-md-007 — On-demand reference sections in the repository are not auto-loaded and must be r
[1093] claim-instructions-and-rules-instructions-and-rules-agents-md-008 — The post-bootstrap flow proceeds as `bootstrap.sh` (render) → `/harness-eval` (t
[1094] claim-instructions-and-rules-instructions-and-rules-agents-md-009 — Each skill wrapper is a thin pointer; the model reads the `.agents/` body on-dem
[1095] claim-instructions-and-rules-instructions-and-rules-agents-md-010 — Doctrine files located at `.agents/doctrine/` are read on-demand when a skill re
[1096] claim-instructions-and-rules-instructions-and-rules-claude-md-000 — The shared, tool-agnostic project context (repo description, genesis bootstrap,
[1097] claim-instructions-and-rules-instructions-and-rules-claude-md-001 — Only Claude-Code-specific notes belong in CLAUDE.md; all other shared context is
[1098] claim-instructions-and-rules-instructions-and-rules-claude-md-002 — Claude-specific harness assets (skills, hooks, scripts) are stored under the pat
[1099] claim-instructions-and-rules-instructions-and-rules-claude-md-003 — The Claude-specific harness assets are generated output mirrored from templates/
[1100] claim-instructions-and-rules-instructions-and-rules-claude-md-004 — The Drift policy defined in AGENTS.md must be consulted before editing the mirro
[1101] claim-instructions-and-rules-instructions-and-rules-claude-md-005 — The primitive drift check is implemented as a Claude Code hook invoking the scri
[1102] claim-instructions-and-rules-instructions-and-rules-claude-md-006 — The drift check script must be run from the repository root with a bootstrapped
[1103] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-000 — The CONTRIBUTING-HARNESS.md file is an editing contract for the repo that is not
[1104] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-001 — Adding a new article requires placing a .md file in templates/_shared/articles/,
[1105] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-002 — Adding a new agent requires placing a .md file in templates/_shared/agents/ and
[1106] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-003 — Adding shared doctrine requires a .md in templates/_shared/doctrine/ and a doctr
[1107] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-004 — The drift-check script is located at templates/claude-code/.claude/hooks/check-p
[1108] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-006 — Each file versions independently, and the doctrine/ and skills/ files are versio
[1109] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-008 — templates/_shared/ is the single source of truth, and platform-specific files in
[1110] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-009 — Each harness ships a non-blocking pointer-edit guardrail that warns (never block
[1111] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-010 — The pointer-edit guardrail configurations reside in .opencode/plugins/warn-point
[1112] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--000 — Shared content for the epic-scoping skill system lives in the `.agents/` directo
[1113] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--001 — Each harness (Opencode, Claude Code, GitHub Copilot) has its own thin wrapper fi
[1114] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--002 — The `.agents/` directory is organized into four subdirectories: `skills/` (epic-
[1115] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--003 — Three harnesses are supported via thin frontmatter-only pointer files: Opencode
[1116] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--004 — Both the epic-scoping skills and the genesis meta-flow follow the shared-content
[1117] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--005 — `bootstrap-harness` is the single canonical body for installing or tailoring a h
[1118] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--006 — Genesis template output under `.github/instructions/` and `.github/copilot-instr
[1119] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--007 — The golden rule of the architecture is: edit content in `.agents/`, edit frontma
[1120] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--008 — The `.agents/doctrine/` layer holds rules shared across multiple skills and rubr
[1121] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--009 — Skills reference doctrine rules via the directive `Applies .agents/doctrine/<nam
[1122] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-000 — The bootstrap script `templates/scripts/bootstrap.sh` reads from `templates/_sha
[1123] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-001 — The Claude Code harness uses `CLAUDE.md` as its entry point and stores rules in
[1124] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-002 — The GitHub Copilot harness uses `.github/copilot-instructions.md` as its entry p
[1125] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-003 — The Opencode harness uses `CLAUDE.md` as its entry point and stores rules in `.o
[1126] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-004 — The `--auto-detect` flag inspects the `--output-dir` to infer the project's stac
[1127] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-007 — The `--has-mlflow yes/no` flag controls inclusion of MLflow Prompt Registry rule
[1128] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-008 — The `--has-langgraph yes/no` flag controls inclusion of LangGraph agent rules in
[1129] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-000 — The epic-composer skill transforms source material into a complete Epic."
[1130] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-001 — The story-decomposer skill decomposes a ready Epic into INVEST-compliant stories
[1131] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-002 — The task-decomposer skill breaks down stories into AI-executable tasks with para
[1132] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-004 — The acceptance-criteria-rules.md doctrine module contains the six AC linting rul
[1133] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-005 — The source-discipline.md doctrine module is referenced by six entities: epic-com
[1134] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-008 — Each skill wrapper is a one-line body referencing .agents/skills/<name>.md, and
[1135] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-009 — The epic-composer skill emits four progressive response states: SYNTHESIS_ONLY,
[1136] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-010 — The story-decomposer skill emits seven response states: EPIC_NOT_READY, DECOMPOS
[1137] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-000 — The articles/ directory under _shared/ contains Constitutional rules that are re
[1138] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-001 — The agents/ directory under _shared/ contains shared agent definitions where Cla
[1139] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-002 — The commands/ directory under _shared/ contains shared commands and prompts whos
[1140] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-003 — The doctrine/ directory contains shared rules referenced by multiple articles an
[1141] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-004 — The skills/ directory contains shared shippable skills rendered into target .cla
[1142] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-006 — mirror-pairs.json is the single source of truth for all mirror pairs, including
[1143] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-007 — The claude-code/ directory holds Claude-specific harness assets including skills
[1144] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-008 — generate-copilot-mirrors.py transforms Claude frontmatter into Copilot frontmatt
[1145] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-000 — The source material for Epic Creation includes transcripts, docs, notes, and exi
[1146] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-001 — Epic Creation Phase 0 is Context Discovery, which determines whether the project
[1147] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-002 — Epic Creation Phase 3 is a Guided Interview that invokes the epic-interview tool
[1148] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-003 — Epic Creation Phase 4 produces an Epic Draft using epic-shell, a linter, and tra
[1149] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-004 — Epic Creation Phase 5 performs a Readiness Assessment by applying the epic-rubri
[1150] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-005 — The output of the Epic Creation phase is a Ready Epic artifact accompanied by a
[1151] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-006 — Story Decomposition Phase 3 performs Story Drafting using story-shell, BDD, INVE
[1152] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-007 — Story Decomposition Phase 4 performs Dependency Mapping to produce an ordered ba
[1153] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-008 — Story Decomposition Phase 5 performs a Story Readiness Assessment using the stor
[1154] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-009 — The output of the Story Decomposition phase is a ready story backlog containing
[1155] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-000 — Harness evaluation is a post-bootstrap prompt that runs after `bootstrap.sh` has
[1156] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-006 — The harness targets three platforms: Claude Code, GitHub Copilot, and Opencode."
[1157] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-007 — The golden rule states that any rule shared across 2+ articles must reside in th
[1158] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-010 — When editing rule content, the agent must edit the `.claude/rules/` rendered cop
[1159] claim-instructions-and-rules-instructions-and-rules-install-md-000 — The AI harness supports three tools: Claude Code, Opencode, and GitHub Copilot."
[1160] claim-instructions-and-rules-instructions-and-rules-install-md-001 — The instructions-and-rules repository is public and requires no authentication t
[1161] claim-instructions-and-rules-instructions-and-rules-install-md-002 — All installation routes execute the same flow defined in `.agents/skills/bootstr
[1162] claim-instructions-and-rules-instructions-and-rules-install-md-004 — Install options such as `--output-dir` and `--ref` are passed after `bash -s --`
[1163] claim-instructions-and-rules-instructions-and-rules-install-md-005 — The interactive single-prompt installation method works identically in both Clau
[1164] claim-instructions-and-rules-instructions-and-rules-install-md-007 — The Copilot agent invocation uses the syntax `@install-harness /absolute/path/to
[1165] claim-instructions-and-rules-instructions-and-rules-install-md-008 — The installation requires `git` and `python3` as system dependencies."
[1166] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-000 — The epic scoping skills system targets three AI coding harnesses: Opencode, Clau
[1167] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-001 — Shared content in the repository lives in `.agents/` as plain markdown with no f
[1168] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-002 — The golden rule mandates that content is edited in `.agents/`, frontmatter is ed
[1169] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-003 — Three skills hand off in sequence — epic-composer, story-decomposer, and task-de
[1170] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-005 — Each harness ships a non-blocking pointer-edit guardrail that warns but never bl
[1171] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-006 — The Opencode pointer-edit hook is a TypeScript plugin that fires on `tool.execut
[1172] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-007 — The Claude Code pointer-edit hook is a shell script that fires on `PreToolUse` f
[1173] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-008 — The GitHub Copilot pointer-edit hook uses a JSON config with bash and PowerShell
[1174] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-010 — The story readiness rubric evaluates stories against the INVEST criteria."
[1175] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-011 — The task-decomposer defines a shared contract (API, type, or interface) for a st
[1176] claim-instructions-and-rules-instructions-and-rules-readme-md-000 — The project provides Constitutional AI instruction templates for Python (FastAPI
[1177] claim-instructions-and-rules-instructions-and-rules-readme-md-003 — The install-harness agent inspects the target project, shows an install plan, as
[1178] claim-instructions-and-rules-instructions-and-rules-readme-md-004 — Both bootstrap approaches produce a set of output artifacts including .claude/ru
[1179] claim-instructions-and-rules-instructions-and-rules-readme-md-005 — The architecture follows a single-source thin-wrappers pattern where content is
[1180] claim-instructions-and-rules-instructions-and-rules-readme-md-006 — The mirror system maintains body-identical mirrors between .claude/rules/*.md an
[1181] claim-instructions-and-rules-instructions-and-rules-research-md-003 — Claude Code employs a three-layer architecture: persistent Rules, on-demand Skil
[1182] claim-instructions-and-rules-instructions-and-rules-research-md-007 — The audit cataloged a total of 159 files across the instructions-and-rules, infl
[1183] claim-instructions-and-rules-instructions-and-rules-research-md-009 — Tech stack version placeholders such as {{PYTHON_VERSION}} and {{REACT_VERSION}}
[1184] claim-instructions-and-rules-instructions-and-rules-research-md-010 — The template system mandates a tiered TDD coverage hierarchy of Contract, Integr
[1185] claim-nomokailist-nomokailist-agents-md-000 — The NomikaiList backend is built with FastAPI and LangGraph 1.0 for recommendati
[1186] claim-nomokailist-nomokailist-agents-md-001 — The NomikaiList frontend uses Next.js with shadcn UI components."
[1187] claim-nomokailist-nomokailist-agents-md-002 — The database is Supabase (PostgreSQL + RLS) and no direct DB access is permitted
[1188] claim-nomokailist-nomokailist-agents-md-003 — The Python package manager for NomikaiList is `uv`, not pip or poetry."
[1189] claim-nomokailist-nomokailist-agents-md-004 — Type hints are required on all Python function signatures and enforced by mypy."
[1190] claim-nomokailist-nomokailist-agents-md-006 — Backend test coverage must be at least 68%, enforced in CI via --cov-fail-under=
[1191] claim-nomokailist-nomokailist-agents-md-011 — LangGraph agent state in NomikaiList uses TypedDict (not dataclass), and tools r
[1192] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-000 — The team decided to use Supabase as the sole backend infrastructure provider for
[1193] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-001 — SQLAlchemy ORM is explicitly excluded in favor of using the Supabase Python clie
[1194] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-002 — Redis is explicitly excluded, with Supabase used for caching patterns where need
[1195] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-003 — Celery is explicitly excluded in favor of async Python tasks or LangGraph for wo
[1196] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-004 — Supabase's built-in Row Level Security enforces data isolation at the database l
[1197] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-006 — The supabase-py async client integrates cleanly with FastAPI async patterns."
[1198] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-007 — SQLAlchemy bypasses Supabase RLS policies unless explicitly configured."
[1199] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-010 — The check-constitution.py script's Article II checks for forbidden dependencies
[1200] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-000 — NomikaiList uses opencode as its AI coding assistant."
[1201] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-002 — AGENTS.md serves as a derived entry point that summarizes and links the rules bu
[1202] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-004 — A machine-readable checker at backend/scripts/check-constitution.py validates ar
[1203] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-005 — The defined rule update order is .claude/rules/ → AGENTS.md."
[1204] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-006 — An instructions-drift checker at scripts/check-instructions-drift.sh validates t
[1205] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-007 — The constitution checker runs in CI and violations block merges."
[1206] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-008 — check-agent-drift.sh hooks warn when .claude/rules/ changes without correspondin
[1207] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-009 — CalVer version 2026.04.24 on enforcement.md tracks the rule publication date."
[1208] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-010 — check-agent-drift.sh runs on PreToolUse when editing rule files."
[1209] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-000 — NomikaiList has a 68% minimum aggregate coverage threshold enforced in CI."
[1210] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-001 — The Privacy/Auth tier (privacy_service.py, auth_service.py, api/routes/auth.py)
[1211] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-002 — The Revenue/Data integrity tier (repositories/*, import_service.py, api/routes/m
[1212] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-003 — The AI Agents/ML tier (agents/*, ml/*, recommendation_scorer.py) requires ≥50% c
[1213] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-005 — Tests must be authored in the order: contract tests, integration tests, E2E test
[1214] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-006 — The check-constitution.py script verifies that pytest.ini contains --cov-fail-un
[1215] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-008 — The tiered coverage model is intended to supplement, not replace, the existing 6
[1216] claim-nomokailist-nomokailist-docs-adr-0004-ai-fit-receipts-md-004 — The SIGNAL_FLOOR threshold for including a user weight in axis scoring is 0.1."
[1217] claim-nomokailist-nomokailist-docs-adr-0004-ai-fit-receipts-md-005 — The CAUTION_THRESHOLD is 0.2, representing the bottom quartile on the 0–1 normal
[1218] claim-nomokailist-nomokailist-docs-adr-0004-ai-fit-receipts-md-010 — The AI_FIT_SERVICE_ENABLED environment variable gates the route, with a default
[1219] claim-nomokailist-nomokailist-docs-adr-0005-review-queue-authz-model-md-001 — All six routes on the review-queue API execute via the service-role Supabase cli
[1220] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-000 — The MAL adapter was built on the public Jikan proxy at api.jikan.moe/v4."
[1221] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-001 — The public Jikan proxy is being retired upstream."
[1222] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-004 — The shared public Jikan rate limit is 60 requests per minute across all users, w
[1223] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-006 — The adapter's base URL is sourced from settings.jikan_base_url with a default of
[1224] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-007 — Self-hosting Jikan requires zero adapter logic changes beyond swapping the base
[1225] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-008 — Self-hosting raises the rate limit from 50 to 120 requests per minute, configura
[1226] claim-nomokailist-nomokailist-docs-api-md-000 — NomikaiList provides a RESTful API for anime and manga discovery and recommendat
[1227] claim-nomokailist-nomokailist-docs-api-md-001 — The NomikaiList development base URL is http://localhost:8000."
[1228] claim-nomokailist-nomokailist-docs-api-md-002 — NomikaiList API authentication uses Bearer tokens with JWT."
[1229] claim-nomokailist-nomokailist-docs-api-md-004 — The media search endpoint has a default page size of 20 results with a maximum o
[1230] claim-nomokailist-nomokailist-docs-api-md-005 — The recommendations endpoint has a default of 10 results with a maximum of 50."
[1231] claim-nomokailist-nomokailist-docs-api-md-006 — The recommendations endpoint uses a content-based algorithm for generating sugge
[1232] claim-nomokailist-nomokailist-docs-api-md-007 — The authentication endpoints are rate-limited to 5 requests per minute."
[1233] claim-nomokailist-nomokailist-docs-api-md-008 — The search endpoint is rate-limited to 100 requests per minute."
[1234] claim-nomokailist-nomokailist-docs-api-md-009 — The recommendations endpoint is rate-limited to 30 requests per minute."
[1235] claim-nomokailist-nomokailist-docs-api-md-011 — MyAnimeList is a supported external platform for importing user data."
[1236] claim-nomokailist-nomokailist-docs-ci-setup-md-000 — The CI/CD pipeline workflow is triggered on every push to main and every pull re
[1237] claim-nomokailist-nomokailist-docs-ci-setup-md-001 — Security code (RLS, auth) requires a minimum of 90% test coverage, enforced in C
[1238] claim-nomokailist-nomokailist-docs-ci-setup-md-002 — General code requires a minimum of 80% test coverage, enforced via pytest.ini co
[1239] claim-nomokailist-nomokailist-docs-ci-setup-md-003 — The security scanning workflow is triggered on pushes to main/develop, pull requ
[1240] claim-nomokailist-nomokailist-docs-ci-setup-md-004 — The security scanning workflow uses Bandit and Semgrep for static code analysis.
[1241] claim-nomokailist-nomokailist-docs-ci-setup-md-005 — The security scanning workflow uses Gitleaks to detect leaked secrets."
[1242] claim-nomokailist-nomokailist-docs-ci-setup-md-006 — The security scanning workflow uses Trivy to scan Docker images."
[1243] claim-nomokailist-nomokailist-docs-ci-setup-md-007 — GitHub does not expose repository secrets to pull requests from forks for securi
[1244] claim-nomokailist-nomokailist-docs-ci-setup-md-008 — The Supabase service role key bypasses Row Level Security (RLS) policies."
[1245] claim-nomokailist-nomokailist-docs-ci-setup-md-009 — The deploy job in the CI/CD pipeline runs only on the main branch."
[1246] claim-nomokailist-nomokailist-docs-ci-setup-md-010 — The rls-security-tests job in the security scanning workflow verifies that RLS i
[1247] claim-nomokailist-nomokailist-docs-deployment-md-001 — Supabase serves as the managed database, authentication, and storage layer in pr
[1248] claim-nomokailist-nomokailist-docs-deployment-md-008 — Database migrations consist of 124 or more ordered SQL files in supabase/migrati
[1249] claim-nomokailist-nomokailist-docs-developer-setup-md-000 — The project requires Python 3.11 or later as a prerequisite."
[1250] claim-nomokailist-nomokailist-docs-developer-setup-md-001 — The project requires Node.js 18 or later as a prerequisite."
[1251] claim-nomokailist-nomokailist-docs-developer-setup-md-002 — The backend uses uv as its Python package manager."
[1252] claim-nomokailist-nomokailist-docs-developer-setup-md-003 — The backend uses Supabase as its database backend."
[1253] claim-nomokailist-nomokailist-docs-developer-setup-md-004 — The backend development server runs on port 8000 via uvicorn."
[1254] claim-nomokailist-nomokailist-docs-developer-setup-md-005 — The frontend development server runs on port 3000."
[1255] claim-nomokailist-nomokailist-docs-developer-setup-md-006 — The backend API layer is built with FastAPI."
[1256] claim-nomokailist-nomokailist-docs-developer-setup-md-007 — The frontend uses Next.js 16 with the App Router architecture."
[1257] claim-nomokailist-nomokailist-docs-developer-setup-md-008 — The frontend uses shadcn/ui for its React component library."
[1258] claim-nomokailist-nomokailist-docs-developer-setup-md-010 — The backend supports importing data from MyAnimeList, AniList, and Kitsu via ext
[1259] claim-nomokailist-nomokailist-docs-developer-setup-md-011 — The backend uses Pydantic models for data validation."
[1260] claim-nomokailist-nomokailist-docs-graphify-setup-md-003 — The default model kimi-k2.5:cloud has approximately 1 trillion parameters."
[1261] claim-nomokailist-nomokailist-docs-graphify-setup-md-006 — The Ollama server client version is 0.21.2 and listens on http://localhost:11434
[1262] claim-nomokailist-nomokailist-docs-importing-data-md-000 — NomikaiList supports importing data from MyAnimeList, AniList, and Kitsu."
[1263] claim-nomokailist-nomokailist-docs-importing-data-md-003 — MyAnimeList import in NomikaiList is performed via the Jikan API."
[1264] claim-nomokailist-nomokailist-docs-importing-data-md-004 — AniList import in NomikaiList uses the GraphQL API."
[1265] claim-nomokailist-nomokailist-docs-importing-data-md-005 — Kitsu import in NomikaiList uses the JSON:API format."
[1266] claim-nomokailist-nomokailist-docs-importing-data-md-006 — Incremental catalog sync in NomikaiList uses each adapter's recently-updated end
[1267] claim-nomokailist-nomokailist-docs-importing-data-md-008 — When an adapter does not support recently-updated fetch, the NomikaiList service
[1268] claim-nomokailist-nomokailist-docs-importing-data-md-009 — Kitsu serves as a secondary source for enrichment and aliases in NomikaiList."
[1269] claim-nomokailist-nomokailist-docs-overview-md-000 — MyAnimeList, AniList, and Kitsu each have unique libraries and communities, prev
[1270] claim-nomokailist-nomokailist-docs-overview-md-001 — NomikaiList is a privacy-first anime and manga discovery platform that combines
[1271] claim-nomokailist-nomokailist-docs-overview-md-002 — NomikaiList supports import and sync of ratings from AniList, MyAnimeList, and K
[1272] claim-nomokailist-nomokailist-docs-overview-md-003 — NomikaiList uses a graph-based recommendation engine that learns user taste pref
[1273] claim-nomokailist-nomokailist-docs-overview-md-005 — NomikaiList is GDPR compliant with full data export and deletion capabilities."
[1274] claim-nomokailist-nomokailist-docs-overview-md-006 — NomikaiList implements row-level security at the database level."
[1275] claim-nomokailist-nomokailist-docs-overview-md-007 — The NomikaiList backend uses FastAPI, Python 3.11+, Supabase (PostgreSQL + Auth
[1276] claim-nomokailist-nomokailist-docs-overview-md-008 — The NomikaiList frontend uses Next.js 16 with App Router, TypeScript, and shadcn
[1277] claim-nomokailist-nomokailist-docs-overview-md-009 — The AI-driven graph recommendation engine with explainability is a completed fea
[1278] claim-nomokailist-nomokailist-docs-security-rls-md-000 — NomiKaiList uses Supabase's Row Level Security to enforce data access controls a
[1279] claim-nomokailist-nomokailist-docs-security-rls-md-002 — The service role is a privileged Supabase role that bypasses all RLS policies."
[1280] claim-nomokailist-nomokailist-docs-security-rls-md-005 — The ratings table uses a 3-point scale: 1 (dislike), 3 (curious), 5 (like)."
[1281] claim-nomokailist-nomokailist-docs-style-md-000 — The NomikaiList design system uses exactly three font families, each with a dist
[1282] claim-nomokailist-nomokailist-docs-style-md-010 — Dark mode is explicitly prohibited in the NomikaiList design system; the aesthet
[1283] claim-nomokailist-nomokailist-docs-style-md-011 — Glass and blur effects are deprecated by this design system, specifically the ex
[1284] claim-nomokailist-nomokailist-docs-testing-md-000 — NomikaiList recommends using Local Supabase for all database-dependent tests to
[1285] claim-nomokailist-nomokailist-docs-testing-md-001 — The NomikaiList backend has 37 test files in total."
[1286] claim-nomokailist-nomokailist-docs-testing-md-002 — The NomikaiList backend has 21 contract test files located in backend/tests/cont
[1287] claim-nomokailist-nomokailist-docs-testing-md-003 — The NomikaiList backend has 7 integration test files located in backend/tests/in
[1288] claim-nomokailist-nomokailist-docs-testing-md-004 — The NomikaiList backend has 5 unit test files located in backend/tests/unit/."
[1289] claim-nomokailist-nomokailist-docs-testing-md-005 — The NomikaiList backend enforces a minimum 80% code coverage gate via pytest con
[1290] claim-nomokailist-nomokailist-docs-testing-md-006 — The NomikaiList frontend enforces a minimum 80% coverage threshold across branch
[1291] claim-nomokailist-nomokailist-docs-testing-md-007 — The NomikaiList backend requires recommendation generation to complete in under
[1292] claim-nomokailist-nomokailist-docs-testing-md-008 — The NomikaiList backend requires API response times to be under 100ms at the 95t
[1293] claim-nomokailist-nomokailist-docs-testing-md-010 — The MockSupabaseClient is implemented in the file src/testing/mock_supabase.py."
[1294] claim-nomokailist-nomokailist-docs-testing-md-011 — GitHub Actions CI runs unit tests as Stage 1 with an expected duration of approx
[1295] claim-nomokailist-nomokailist-docs-user-guide-md-000 — NomikaiList requires usernames to be between 3 and 30 characters."
[1296] claim-nomokailist-nomokailist-docs-user-guide-md-001 — NomikaiList requires a minimum password length of 8 characters."
[1297] claim-nomokailist-nomokailist-docs-user-guide-md-002 — Account creation on NomikaiList requires accepting GDPR consent."
[1298] claim-nomokailist-nomokailist-docs-user-guide-md-003 — NomikaiList onboarding requires users to rate 15 to 20 anime or manga titles."
[1299] claim-nomokailist-nomokailist-docs-user-guide-md-004 — NomikaiList supports three rating types: Like, Dislike, and Curious."
[1300] claim-nomokailist-nomokailist-docs-user-guide-md-005 — The NomikaiList dashboard displays a Taste Profile showing the user's preferred
[1301] claim-nomokailist-nomokailist-docs-user-guide-md-007 — Upon connecting a supported platform, NomikaiList automatically imports the user
[1302] claim-nomokailist-nomokailist-docs-user-guide-md-009 — NomikaiList supports data export and account deletion."
[1303] claim-nomokailist-nomokailist-readme-md-000 — NomikaiList is a personalized recommendation system with AI-powered curation and
[1304] claim-nomokailist-nomokailist-readme-md-001 — The backend requires Python 3.11 or later."
[1305] claim-nomokailist-nomokailist-readme-md-002 — The frontend requires Node.js 18 or later."
[1306] claim-nomokailist-nomokailist-readme-md-003 — The import system supports three external platforms: AniList, MyAnimeList, and K
[1307] claim-nomokailist-nomokailist-readme-md-009 — The backend uses FastAPI version 0.104.1 with SQLAlchemy 2.0 in async mode."
[1308] claim-nomokailist-nomokailist-readme-md-011 — The frontend uses Next.js 14 with App Router, TypeScript, shadcn/ui, Tailwind CS
[1309] claim-nomokailist-nomokailist-security-md-001 — Security vulnerabilities must not be reported as public issues on the repository
[1310] claim-nomokailist-nomokailist-security-md-006 — The security scope covers the NomikaiList backend API, frontend, and ingestion p
[1311] claim-nomokailist-nomokailist-security-md-007 — Vulnerabilities in third-party platforms (Supabase, AniList, MyAnimeList, Kitsu)
[1312] claim-nomokailist-nomokailist-security-md-008 — Data-access controls in NomikaiList are enforced at the database layer via Supab
[1313] claim-nomokailist-nomokailist-security-md-009 — Privacy and GDPR concerns involving personal data can be directed to privacy@nom

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
