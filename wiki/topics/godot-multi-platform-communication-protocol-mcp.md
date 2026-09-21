---
type: wiki-article
title: "Godot Multi-Platform Communication Protocol (MCP)"
domain: [agent-systems, godot-systems]
review_after: 2027-01-19
---

# Godot Multi-Platform Communication Protocol (MCP)

2248 current claim(s) support this topic.

- The system is a multi-agent AI trading system designed for Alpaca Markets paper trading." [1]
- All agents must operate on a shared `TradingState` object by mutating its fields rather than reassigning the entire object." [2]
- The module dependencies must flow unidirectionally from `src/models/` to `src/workers/`, with `src/services/` being restricted from importin [3]
- CI runs unit tests using the command `uv run pytest tests/unit/` with specific flags to exclude slow, integration, and performance tests." [4]
- The project requires approximately 58–59% coverage, with new code requiring 70%+ coverage." [5]
- To ensure compliance with Spec §11.3, `langgraph` and `langgraph-checkpoint-postgres` must be at least versions 0.4.8 and 2.1.2, respectivel [6]
- All agents mutate a shared TradingState object, requiring field mutation rather than full object reassignment." [7]
- The system supports four agent patterns: ReAct, Direct, Hybrid, and Pure LLM." [8]
- The Synthesizer debate is triggered when the system reaches 60–95% confidence." [9]
- The maximum token budget per workflow is 50,000." [10]
- The quote interval for market data is 60 seconds." [11]
- The system includes 14 investor personas available for deliberation consultation." [12]
- The system uses PostgreSQL with the pgvector extension to store and query high-dimensional analysis embeddings." [13]
- The memory retrieval mechanism defaults to searching for the top 5 similar cases using a cosine similarity threshold of 0.75." [14]
- The database connection utilizes asynchronous SQLAlchemy with specific pooling parameters for performance." [15]
- The system tracks agent performance metrics, including analysis, outcomes, and agent metadata, within the database." [16]
- The Alpaca Agents trading system utilizes a LangGraph-based workflow where specialized agents communicate through a shared state object." [17]
- Technical and Sentiment Agents run in parallel after receiving input from the Regime Agent." [18]
- Parallel execution of the Technical and Sentiment Agents achieves a 30-40% reduction in workflow time, saving 5-10 seconds." [19]
- The final execution decision is controlled by a Conditional Router, requiring human approval unless the trade is auto-approved." [20]
- The system employs a Shared State Accumulation Pattern where agents progressively enrich the TradingState rather than replacing it entirely. [21]
- The system operates as a pipeline using three distinct LangGraph instances." [22]
- The Execution Graph includes agents like `TechnicalAnalysisAgent`, `SentimentAgent`, `RegimeDetectionAgent`, `RiskGateAgent`, `DeliberationA [23]
- Structured-output and reasoning nodes are assigned `qwen3:30b` via Ollama, offering high performance benchmarks." [24]
- FinBERT is inaccurate 83% of the time when applied to positive financial headlines, necessitating a Gemma4 override." [25]
- The system includes a market regime detection feature that identifies six distinct market states." [26]
- The backtesting framework supports historical testing over a period exceeding one year of data." [27]
- The system incorporates Monte Carlo simulation for the assessment of tail risk." [28]
- The system provides a template rendering performance constraint of less than 1 millisecond (P95)." [29]
- The system supports the generation of multiple report types upon workflow execution." [30]
- The system migrated its database backend from SQLite to PostgreSQL with TimescaleDB extension." [31]
- The database schema was expanded to include dedicated tables for risk metrics, alert events, and circuit breaker states." [32]
- The chat interface supports streaming responses, allowing for token-by-token display." [33]
- The system requires Python 3.10 or newer for its implementation." [34]
- The system utilizes PostgreSQL 14 or newer as its database backend, with optional integration of TimescaleDB." [35]
- The Market Data Agent provides a detailed output structure including a recommendation, confidence score, and technical indicators." [36]
- The Sentiment Agent requires a symbol and a list of news items to perform sentiment analysis." [37]
- The Backtest Agent provides quantitative performance metrics upon completion, including win rate, average return, and maximum drawdown." [38]
- A core design principle of the system is Modularity, ensuring that each agent is independent and replaceable." [39]
- The disagreement status in Round 1 was 77.5%." [40]
- The deliberation reached consensus in Round 2 with a disagreement score of 18.0%." [41]
- Agent argument messages include confidence, round number, agent type, and analysis ID." [42]
- Deliberation messages can be retrieved from the chat_messages table using session_id, analysis_id, and filtering for is_deliberation_message [43]
- A complete deliberation episode can be exported by querying chat_messages filtered by analysis_id and is_deliberation_message = TRUE." [44]
- The initial Chat interface path executes 5 agents sequentially and takes approximately 10-15 seconds to provide an incomplete analysis." [45]
- The initial CLI path executes 11 agents using a full LangGraph workflow and takes approximately 20-30 seconds to provide a comprehensive ana [46]
- The CLI path executes 11 agents, including specialized components like MarketRegimeAgent, BacktestingAgent, and PositionManagerAgent." [47]
- The streaming wrapper introduced in Phase 2 includes a chat mode optimization that disables backtesting and limits deliberation to ensure fa [48]
- The refactored system allows Technical and Sentiment agents to run concurrently, which contributes to a potential 30-40% speed increase." [49]
- The system fetches real-time portfolio context from Alpaca, including the portfolio value, available cash, and current positions." [50]
- The Agent Chat Interface includes specialized agents for various trading functions, including market data, technical analysis, sentiment, ri [51]
- The system provides a command-line interface for quick actions, including commands for full trading analysis, viewing portfolio status, and  [52]
- The system utilizes a defined data flow pipeline where user input is processed through a Command Parser, Message Router, and Response Format [53]
- The per-agent model selection is managed in `llm_routing.assignments` within `data/config/settings.yaml` and serves as the single source of  [54]
- The Sentiment Agent should be upgraded to `anthropic/claude-3-5-sonnet` for superior sentiment understanding and nuanced analysis of financi [55]
- For live trading, the Portfolio Agent should be upgraded to `claude-3-opus` or `o1-preview` to achieve the best synthesis and reasoning capa [56]
- The Cost-Optimized configuration averages a cost of $0.008 to $0.012 per analysis, making it suitable for development and testing." [57]
- The Live Trading configuration averages a cost of $0.04 to $0.08 per analysis." [58]
- The system tracks the lowest and highest prices observed during the first 24 hours of an opportunity." [59]
- The `fetch_news_articles` function fetches news articles based on specified stock symbols and a maximum limit." [60]
- The sentiment score generated by `analyze_news_sentiment` ranges from -100 to +100, where -100 is bearish and +100 is bullish." [61]
- The aggregation function allows weighting inputs from different sentiment sources, such as news and options flow." [62]
- Unusual activity detection accepts configurable thresholds for sentiment magnitude and article count." [63]
- The `analyze_options_flow_sentiment` function requires the underlying symbol, total call volume, and total put volume for analysis." [64]
- A combined sentiment score greater than 20 indicates an \"improving\" trend." [65]
- A sentiment score between +50 and +20 indicates a \"Bullish\" sentiment." [66]
- The AgentExecutor used in the ReAct pattern has a maximum of 15 iterations and a timeout protection of 30.0 seconds." [67]
- The ReAct pattern typically executes in 5 to 10 seconds, with tool calls taking 0.5 to 1 second per tool." [68]
- The ReAct pattern requires a high token usage, including approximately 500 tokens for the system prompt." [69]
- The Direct Tool Invocation pattern typically executes in 1 to 3 seconds and uses low token usage." [70]
- Direct Invocation is preferred when the workflow is deterministic and follows the same steps regardless of input data variations, asset type [71]
- The ReAct pattern is appropriate when the workflow must adaptively decide which tools to call and in what order based on data availability,  [72]
- A specific constraint of the ReAct pattern is the ability to skip indicators if the available data is insufficient, such as needing 200 bars [73]
- Direct Invocation is used for fixed workflows, such as sentiment analysis or risk management, where the sequence of steps is always the same [74]
- The ReAct pattern requires the LLM to dynamically select tools and involves an iterative reasoning loop until a decision is reached." [75]
- The Hybrid pattern utilizes BaseToolAgent for deterministic calculations and employs the LLM solely for generating natural language reasonin [76]
- ReAct agents are slower than Direct Invocation agents because ReAct requires more LLM calls for orchestration and reasoning." [77]
- Pure LLM Reasoning is used when the task is analysis, debate, or text generation and no external tools are required." [78]
- The 14 total agents are distributed across five categories: BaseReActAgent (2), BaseToolAgent (1), Direct Tool Invocation (3), Pure LLM Reas [79]
- For robust validation, the backtesting framework recommends using at least one year of historical data." [80]
- A specific backtest run starting with $10,000 resulted in a 24.50% total return." [81]
- In a specific A/B test, Configuration A achieved a higher Total Return (24.50%) compared to Configuration B (21.20%)." [82]
- The Walk-Forward Optimization module allows users to define rolling window sizes, such as an 180-day training window and a 60-day testing wi [83]
- The optimization process can identify consensus parameters, such as `stop_loss_pct: 0.06`, which appeared in all six tested windows." [84]
- The Monte Carlo Simulator is designed to run simulations using 1000 or more scenarios and calculate metrics like Value at Risk (VaR)." [85]
- The Trading Portfolio Dashboard is a custom web UI built on React and FastAPI, providing real-time portfolio management, agent chat, risk mo [86]
- The dashboard can be launched by executing the command `uv run python main.py dashboard` after ensuring the database is started." [87]
- The system supports two modes of agent interaction: Sequential Mode, where agents respond step-by-step (Market Data → Technical → Sentiment  [88]
- The Positions view displays detailed metrics including Symbol, Type, Quantity, Average Entry Price, Current Market Price, Total Market Value [89]
- The Risk Monitoring section tracks specific metrics such as Sharpe Ratio, Maximum Drawdown (in currency and percentage), and Portfolio Beta  [90]
- The system includes a Circuit Breaker feature that can be in an 'Inactive' state, indicating that trading is operational." [91]
- The dashboard allows users to set the data refresh interval via a slider ranging from 5 to 60 seconds." [92]
- The `challenge_round_enabled` flag is initially set to false." [93]
- The `dissenter_sampling_enabled` flag is initially set to false." [94]
- The `calibrated_weights_enabled` flag is initially set to false." [95]
- The maximum allowed increase in p95 wall time is 30.0 percent." [96]
- Each deliberation run records the enabled flags to `DeliberationData.active_experiments`." [97]
- Live trading is disabled by default and requires deliberate human action to transition to live capital." [98]
- Enabling live capital requires a human decision, separate live credentials, and explicit configuration setting `ALLOW_LIVE_TRADING=true`." [99]
- A second readiness criterion is achieving an agreement rate of 85% or higher in Shadow-eval across the last 30 replayed states." [100]
- A third readiness criterion is passing all WP-6 eval scorer-gate thresholds using a dataset of 20 or more samples." [101]
- Live mode requires setting `TRADING_MODE=live` in the k3s ConfigMap and using distinct, AK-prefixed secret keys, alongside setting `ALLOW_LI [102]
- Live trading can be disabled by reverting configuration settings or by using a kill switch that cancels open orders upon a RED trip and requ [103]
- All agent prompts and run metrics are consolidated in a single experiment on the MLflow tracking server." [104]
- The system registers a total of 31 prompts across various categories, including system, deliberation, task, and persona prompts." [105]
- The prompt resolution process involves the agent returning a sentinel string, which is then passed to the PromptResolver for rendering." [106]
- The PromptResolver caches prompts for a configurable Time-To-Live (TTL), which defaults to 300 seconds." [107]
- The Model Optimizer automatically identifies underperforming models, recommends replacements, calculates optimal confidence thresholds, tune [108]
- An underperformer is defined by a win rate below 45%, low ROI, or cost exceeding $0.10 per signal." [109]
- An overperformer is characterized by a win rate above 60%, high ROI, and consistency across time periods." [110]
- Aggressive trading strategies utilize a confidence threshold range of 65-70% to maximize trade volume." [111]
- Aggressive opportunity scoring uses a prediction accuracy range of 60-65%." [112]
- A minimum of 30 completed trades is required for reliable model analysis." [113]
- The CLI tool identifies models based on win rates below 45% or above 60%, and flags expensive models costing over $0.10 per signal." [114]
- The Position Manager runs before the Rebalancing Agent within the trading workflow." [115]
- The Position Manager Agent allows setting a maximum loss percentage to force an exit." [116]
- Profit protection can be configured to lock in a minimum percentage of gains." [117]
- The Rebalancing Agent supports triggering based on allocation drift, calendar intervals, or tax-loss harvesting." [118]
- The Rebalancing Agent allows setting a maximum portfolio turnover percentage for a rebalancing action." [119]
- Promotion to staging requires two conditions: 5+ market days of paper trading on staging, and passing the WP-6 eval scorer gate on a ≥20-sam [120]
- The `_init_llm()` method was identically duplicated across two classes, spanning 104 lines." [121]
- The `WorkflowExecutor` initializes with configuration, an optional auto-execution flag, and a checkpointer for persistence." [122]
- The `_create_initial_state` method defaults the portfolio value and available cash to 10000 if the configuration values are missing." [123]
- The reporting service is designed to generate reports asynchronously and handle generation failures without halting the main analysis proces [124]
- The Enhanced Risk Monitoring system scans the portfolio at a configurable interval, defaulting to every 30 seconds." [125]
- The system provides real-time risk metrics including VaR, drawdown, volatility, beta, and Sharpe ratio." [126]
- A prerequisite for the system is a running TimescaleDB instance, which must have Migration 003 applied to create necessary risk monitoring t [127]
- Email alerts require specific SMTP configuration details, such as using port 587 and providing an app-specific password for Gmail." [128]
- The overall code coverage target for the system is 85% or higher." [129]
- Deliberation agents require a minimum of 95% code coverage." [130]
- Trading agents require a minimum of 90% code coverage." [131]
- The `tests/unit/` directory is designated for fast, isolated tests." [132]
- A successful integration test run must produce a trade recommendation." [133]
- When testing code that utilizes `AlpacaClient`, the mock must be configured to return a specific quote price." [134]
- The default symbols analyzed during a run are BTC/USD, ETH/USD, AAPL, GOOGL." [135]
- The Balanced configuration targets an average latency of 20 to 40 seconds per analysis." [136]
- The Balanced configuration targets a cost per analysis between $0.015 and $0.025." [137]
- A 1-hour validation run can be executed by setting the duration parameter to 3600." [138]
- The execution reliability validation suggests monitoring the error rate to be less than 5%." [139]
- The example output indicates that 48 calls were made to the Market Data agent during the run." [140]
- A high-frequency analysis run can be performed using 1-minute intervals and a 3600-second duration." [141]
- The `earnings_beat` catalyst type is assigned a specific evaluation window of 4 hours." [142]
- A bullish success is defined by the price movement percentage being greater than or equal to +1.5%." [143]
- The PriceMonitor background worker executes price snapshots for tracked opportunities every 15 minutes." [144]
- A high-priority notification is triggered if the adjusted score of an opportunity reaches 80 or higher." [145]
- The target size for `get_options_chain()` was less than 80 lines." [146]
- The refactored `get_options_chain()` is approximately 70 lines." [147]
- The original `_state_to_responses()` method was approximately 270 lines long and had high complexity." [148]
- The `_extract_symbol()` method previously contained a 95-word `excluded_words` set inline." [149]
- The refactored `_state_to_responses()` method is now approximately 50 lines long and functions as a simple dispatcher." [150]
- The refactoring introduced 7 focused response builder methods." [151]
- The intent detection mechanism (`_detect_intent()`) was updated to use an externalized `INTENT_KEYWORDS` constant." [152]
- The symbol extraction mechanism (`_extract_symbol()`) now uses an externalized `SYMBOL_EXCLUSION_WORDS` constant." [153]
- The project added 22 new unit tests specifically for the extracted helper methods." [154]
- The original `_execute()` method contained 275 lines of code and a complexity of 29." [155]
- The exception handlers contained 5 instances of duplicated Order construction code." [156]
- The refactored `_execute()` method is targeted to be approximately 120 lines." [157]
- The `_apply_session_restrictions()` method extracts the extended hours order type conversion logic, which was previously a 63-line block." [158]
- The `_create_rejected_order()` method eliminates the duplicated Order construction found in exception handlers." [159]
- The `_build_order_params()` method extracts the logic for building order parameters from a trade recommendation." [160]
- A key acceptance criterion is that the `_execute()` method must be reduced to less than 130 lines." [161]
- The original `_execute()` function was approximately 230 lines long and had a complexity of 25." [162]
- The original `_synthesize_options_recommendation()` function was approximately 225 lines long and had a complexity of 29." [163]
- The refactoring successfully eliminated approximately 150 lines of duplication." [164]
- After refactoring, the `_execute()` function is approximately 120 lines." [165]
- After refactoring, the `_synthesize_options_recommendation()` function is approximately 120 lines." [166]
- Options trade direction determination was simplified using a signal lookup mechanism." [167]
- The project includes 13 existing tests and 21 new unit tests for the extracted helpers." [168]
- The original `_assess_options_risk()` method was approximately 280 lines long and had a complexity of 32." [169]
- The refactored `_execute()` method is targeted to be less than 230 lines." [170]
- The refactoring introduced 4 shared helper methods to eliminate duplication." [171]
- The `_calculate_average_confidence()` method consolidates duplicated confidence averaging logic from specific lines in the original code." [172]
- The `_apply_calibration_adjustments()` method consolidates calibration logic from specific lines in the original code." [173]
- The `_apply_session_adjustments()` method extracts a 60-line session adjustment block." [174]
- The refactored `_execute()` method utilizes specific helper methods for its sequence of operations." [175]
- The new system checks for recent analysis before running a full workflow and returns cached results based on a configurable Time-To-Live (TT [176]
- The default TTL for stock analysis is 15 minutes." [177]
- The default TTL for crypto analysis is 5 minutes." [178]
- When a cached analysis is successfully retrieved and served, the API response status is set to \"cached\"." [179]
- A TradeIntention must include fields for strategy ID, symbol, direction, conviction, and requested amount." [180]
- Graduation of a strategy requires meeting specific performance thresholds: a minimum Sharpe ratio of 1.0, a maximum drawdown of 0.15, a mini [181]
- The lifecycle stage of a strategy determines its capital allocation: Paper uses 0% real capital, Probation uses 10%, and Active uses 100%." [182]
- The SharedAnalysisState mechanism allows for the detection of stale data by checking if the analysis has exceeded a defined maximum age." [183]
- The `ObservationBuilder` converts `SharedAnalysisState` into normalized numpy arrays for RL models, and feature groups are independently tog [184]
- The system defines four possible market regime categories: bullish, bearish, sideways, and high_volatility." [185]
- Routing to deliberation occurs when the Arbiter detects HIGH severity conflicts, provided both strategies exceed 80% conviction." [186]
- Phase 4 implements three key features: wiring deliberation into the arbiter, per-strategy deliberation configuration, and enriching delibera [187]
- The system converts a strategy's intention conviction (0-1 scale) into a recommendation confidence (0-100 scale)." [188]
- Deliberation is skipped if the conflict severity is LOW or NONE, provided the Arbiter decision is received." [189]
- The Alpaca Agents system comprises three distinct operational components: Analysis, Research, and Autonomous Trader loops." [190]
- The migration to TA-Lib is structured into sequential and parallel stories, with S0 being the initial decision and setup story." [191]
- The technical indicators are configurable via `settings.yaml`, allowing per-asset-type overrides for parameters like RSI period and Bollinge [192]
- The installation of TA-Lib requires installing the C library and the Python wrapper." [193]
- The current system uses a linear workflow where agents work independently without challenging assumptions or debating conclusions." [194]
- The Bearish Researcher Agent plays devil's advocate by identifying risks, highlighting conflicting signals, and challenging assumptions in t [195]
- The Synthesizer Agent moderates the debate and produces a final balanced recommendation by synthesizing inputs from both researchers." [196]
- The new workflow routes analysis from the Risk Agent to both Bullish and Bearish Researcher Agents, whose outputs then feed into the Synthes [197]
- The implementation of the deliberation phase adds 5-10 seconds of latency per trade and requires 4-6 hours of development time." [198]
- The hypothesis is that the deliberation phase improves the expected win rate by 3-8%." [199]
- The memory system architecture consists of a Vector Database storing embeddings and a PostgreSQL database storing structured data." [200]
- An Analysis Record must capture the technical signal, sentiment score, risk assessment, and trade recommendation generated by the agent." [201]
- The Outcome Record tracks various execution and outcome metrics, including exit price, profit/loss percentage, and holding period in hours." [202]
- The system configuration allows setting the number of similar past cases retrieved during analysis to 5." [203]
- The `double_bottom` technical pattern demonstrated a 72% win rate and 2.1 average Risk/Reward ratio." [204]
- Trades incorporating deliberation showed a 71% win rate, compared to 64% for trades without deliberation." [205]
- The current deliberation system operates on a single-round approach." [206]
- The system allows setting a maximum number of debate rounds for the deliberation process." [207]
- Using early termination is a mitigation strategy against high computational cost." [208]
- The total current test coverage across all agents and workflows is 62%." [209]
- The BullishResearcher agent has 0% test coverage." [210]
- The target coverage goal for the testing suite is 85% or higher." [211]
- The RiskAgent module has 85% test coverage." [212]
- A standard initial trading workflow state includes a portfolio value and available cash of 10000." [213]
- The proposed solution is to implement automated report generation for individual agent analyses, portfolio summaries, and deliberation trans [214]
- The system configuration allows setting an output directory for reports and defines a 90-day retention period for archived data." [215]
- The example trade involved setting a stop-loss at $175.20 (4.8% downside) and a take-profit target at $189.00 (5.3% upside)." [216]
- A warning alert is triggered if the drawdown exceeds 15%, and a critical alert is triggered if it exceeds 18%." [217]
- An alert is triggered if the Value at Risk (VaR) increases by more than 50% within a single day." [218]
- An alert is triggered if the correlation between positions exceeds 0.8." [219]
- An alert is triggered if a single position accounts for more than 35% of the total portfolio value." [220]
- Trading is automatically halted if the drawdown reaches the predefined maximum drawdown threshold." [221]
- Trading is automatically halted if there are three consecutive losing trades, each exceeding a loss of -$500." [222]
- The implementation timeline for the enhanced risk monitoring system is six weeks." [223]
- The monitoring infrastructure requires a monthly cost of $50." [224]
- The TechnicalAgent's buy signals have a 68% profitability rate." [225]
- The average contribution of the TechnicalAgent to profit is +$42 per trade." [226]
- Claude-3-5-sonnet provides 72% accuracy at a cost of $0.004 per trade." [227]
- The implementation timeline for the analytics system is estimated at 5 weeks." [228]
- The Interactive Deliberation Viewer was completed on October 18, 2025." [229]
- The system features a two-column layout displaying the Bullish and Bearish cases, followed by a Synthesis section." [230]
- The viewer is integrated into the dashboard navigation and utilizes a custom web UI with a backend API." [231]
- High volatility (crisis) is defined by VIX above 30, daily moves exceeding 2%, and correlation approaching 1.0." [232]
- In a bull market, the proposed strategy is to increase position sizes by 20% and favor momentum signals." [233]
- In a bear market, the proposed strategy is to reduce position sizes by 30% and favor short signals or inverse ETFs." [234]
- During high volatility, the proposed strategy is to reduce position sizes by 50% and avoid taking new positions." [235]
- The implementation of the regime detection system is estimated to take 6 weeks and depends on market data for SPY and VIX." [236]
- The initial backtest run achieved a Total Return of 24.5%, a Sharpe Ratio of 1.82, and a Max Drawdown of -12.3%." [237]
- The strategy incorporating deliberation achieved a higher Sharpe Ratio (1.82) and Win Rate (68%) compared to the non-deliberation configurat [238]
- The walk-forward optimization process identified new parameters (e.g., min_confidence: 92%, max_position: 12%, stop_loss: 6%) and resulted i [239]
- A Monte Carlo simulation of 1000 possible futures indicated a median 1-year return of 22% and a 95% confidence interval between 8% and 48%." [240]
- The backtesting framework allows for realistic simulation of transaction costs, including a 0.05% slippage fee, a $0.50 commission per trade [241]
- The backtesting framework is structured into dedicated modules for the main engine, parameter optimization, Monte Carlo simulation, performa [242]
- The BUY decision for AAPL was primarily driven by Technical Signal (35%), Sentiment Score (28%), and Risk/Reward Ratio (22%)." [243]
- The final confidence of 72% was achieved through contributions including Technical Signal (+18%), Sentiment Score (+12%), and Risk/Reward (+ [244]
- The final confidence of 72% is calculated as a weighted average of components, including Technical (75%), Sentiment (80%), and Risk (65%)." [245]
- The initial implementation includes five specific personas: Buffett, Munger, Dalio, Lynch, and Graham." [246]
- The `WarrenBuffettPersona` class inherits functionality from `BaseBullishPersona`." [247]
- The system has two proposals currently under consideration or in progress." [248]
- The target Sharpe Ratio for the system is 2.0 or higher, up from a current average of approximately 1.5." [249]
- The target Win Rate for the system is 70% or higher, up from a current average of approximately 60%." [250]
- The maximum acceptable drawdown constraint is less than 15%." [251]
- The CI/CD pipeline requires a build time of less than 5 minutes." [252]
- Proposal 003 (Comprehensive Testing Suite) involved establishing a testing infrastructure using unit, integration, and contract tests." [253]
- Proposal 005 (Enhanced Risk Monitoring) includes a 24/7 monitoring service, email alerts, and circuit breakers." [254]
- Proposal 006 (Agent Performance Analytics) provides a learning analytics dashboard and a model optimizer with recommendations." [255]
- The Alpaca Agents system is a production-ready multi-agent AI trading system." [256]
- The Memory System utilizes pgvector semantic memory combined with sentence-transformer embeddings." [257]
- The system incorporates LangGraph for deliberation workflow analysis." [258]
- Multi-Agent Trading is a production feature." [259]
- Risk Monitoring is a production feature." [260]
- Backtesting is a production feature." [261]
- Database setup requires PostgreSQL/TimescaleDB configuration." [262]
- Docker setup provides an alternative installation method." [263]
- Multi-timeframe confirmation functionality has been enabled." [264]
- The system successfully incorporated breaking news into sentiment analysis." [265]
- The trading system utilizes PostgreSQL with TimescaleDB for managing portfolio tracking and trading history." [266]
- The core tables—trades, portfolio_snapshots, and performance_metrics—are converted to hypertables when TimescaleDB is enabled." [267]
- The specific partitioning keys for the time-series tables are defined as follows: trades by exit_date, and portfolio_snapshots and performan [268]
- Automatic compression provides a storage efficiency benefit of over 90% on historical data." [269]
- For high-concurrency production deployments, Pgbouncer is configured with a default pool size of 20 and a maximum client connection count of [270]
- The database is accessible via localhost on port 5432, using the 'trading' database, 'trading_user', and 'trading_secret' password." [271]
- The application requires specific environment variables to connect to the PostgreSQL database, including the host, port, database name, user [272]
- To connect to the database using pgAdmin, the host is 'timescaledb' (within the Docker network), port 5432, and the credentials are 'trading [273]
- The database can be started using the script `./scripts/db_start.sh`." [274]
- The database can be stopped using the script `./scripts/db_stop.sh`." [275]
- Ruff serves as a unified linter, replacing flake8, isort, and pylint." [276]
- Bandit is a security scanner that identifies common vulnerabilities, including hardcoded passwords and SQL injection risks." [277]
- detect-secrets prevents the accidental commitment of sensitive information such as API keys, AWS credentials, and passwords." [278]
- The `pytest-unit` hook runs fast unit tests in approximately 5 to 10 seconds." [279]
- Black is a code formatter that enforces consistent Python code formatting and can be configured via `pyproject.toml`." [280]
- The file integrity checks include removing trailing whitespace, ensuring files end with a newline, and validating YAML/JSON syntax." [281]
- mypy performs static type checking for Python code." [282]
- Running all hooks on all files can take approximately 30 seconds." [283]
- uv-secure scans dependencies for known security vulnerabilities by checking the uv.lock file against the PyPI JSON API." [284]
- When used as a pre-commit hook, uv-secure requires manual execution because it involves network calls to PyPI, which can be slow." [285]
- The scan can be restricted to only checking direct dependencies." [286]
- A full scan of 197 dependencies can take between 3 and 5 minutes." [287]
- When vulnerabilities are found, the report includes the package name, vulnerability ID, severity level, and description." [288]
- uv-secure is skipped by default in CI environments." [289]
- The system requires Python 3.10 or higher and PostgreSQL 14+ for installation." [290]
- Operation requires accounts for Alpaca, OpenRouter, and Finnhub." [291]
- The database utilizes a TimescaleDB container for operation." [292]
- The default base URL for Alpaca paper trading is specified." [293]
- The default stop loss percentage is configurable at 5.0%." [294]
- The default take profit percentage is configurable at 10.0%." [295]
- The system checks for news using a configurable interval of 300 seconds." [296]
- Backtesting can be triggered by low confidence, conflicting signals, or high volatility." [297]
- Autonomous trading execution is controlled by the `auto_execute` setting, which defaults to requiring approval." [298]
- The system is a multi-agent AI trading system designed for Alpaca Markets, incorporating technical analysis, sentiment analysis, and risk ma [299]
- The system includes 7 specialized AI agents, each with a specific defined purpose." [300]
- The system provides comprehensive testing, including over 4000 passing tests and 100% paper trading validation." [301]
- The system's analysis of a security typically takes between 18 and 37 seconds and costs approximately $0.02 per analysis." [302]
- The system integrates real-time market data from Alpaca and IEX feeds, covering stocks and cryptocurrency." [303]
- Local setup of the system can be achieved in approximately 30 seconds using the uv package manager." [304]
- Godot reported a parse error at res://godot/world_preview_3d.gd:102: Could not resolve external class member \"world_seed\"." [305]
- Godot reported an invalid call at res://addons/world_forge/inspector_plugin.gd:14: nonexistent function 'new_inspector_preview' in base 'GDS [306]
- The root cause was core/world_seed.gd missing two members, causing a cascade of parse failures through WorldSeed, WorldState, WorldForgeWorl [307]
- ChunkKey.from_world() computes chunk coordinates using floori(float(w)/CHUNK_SIZE), which handles negative coordinates correctly." [308]
- ChunkView sets scale to Vector3.ONE * voxel_size and position to Vector3(origin) * voxel_size, so adjacent chunks land exactly 16*vs apart w [309]
- The project is a Godot project containing project.godot and 46 .gd scripts." [310]
- Godot 4.7.2 is installed on the machine." [311]
- GDScript's LSP is not one of opencode's built-ins, so it requires a custom LSP entry." [312]
- Godot's LSP is a TCP server listening on port 6005." [313]
- The running Godot editor has the GDScript LSP live on 127.0.0.1:6005." [314]
- The bridge test failed because piping closes stdin instantly, causing the bridge to exit before the reply arrives." [315]
- A .opencode/godot-lsp-bridge.js stdio↔TCP bridge was created because Godot's LSP is TCP-only on 127.0.0.1:6005." [316]
- The GDScript LSP only runs while the Godot editor is open, so opencode's LSP connects and disconnects as the editor is opened or closed." [317]
- Context7 works keyless at default rate limits, and higher limits require an API key added via an Authorization Bearer header in the config." [318]
- opencode does not hot-reload its config, so it must be quit and restarted for the config to load." [319]
- The mesher reads interior cells from raw ChunkData (baseline only) while edits live only in EditOverlay, creating a data-flow gap." [320]
- EditOverlay stores edits in a sparse Dictionary keyed by Vector3i world cell to block id, where a missing key means baseline." [321]
- Chunk manager spawn budget is 2 per frame, scaled down by maxi(1, roundi(2/vs²)) at higher resolution." [322]
- The aperiodic terrain generator disabled ruins rather than retheming them." [323]
- Measured: 182/2787 tree cells mismatch." [324]
- The aperiodic project had 17 open GitHub issues, with Tier 1 issues #1, #2, and #3 already completed." [325]
- Issue #11 is a tier-1 release-build threading benchmark that validates the use_threads=true default via one exported-build benchmark." [326]
- Issue #4 (Texture2DArray) fixes mip bleeding visual artifacts and is a hard prerequisite for #5 greedy meshing because shader-side UV tiling [327]
- No Godot export templates were installed on the machine, which the release-build portion of issue #11 requires." [328]
- The generated_count counter is only incremented on the threaded spawn path (chunk_manager.gd:218), so sync mode reports chunks=0." [329]
- Symlinking the addon directory caused Godot to see the addon twice, producing duplicate class_name registrations." [330]
- The hybridindie/godot-mcp repository had 20 open issues at the time of the session." [331]
- Issue #422 is a high-priority silent failure in which deleting a .tscn file leaves a stale tab that resurrects a mangled scene." [332]
- Issue #414 is a high-priority silent failure in which set_node_property with a res:// path no-ops while still reporting set:true." [333]
- Issue #413 is a high-priority silent failure in which navigation_bake_mesh returns baked:true on an empty navmesh." [334]
- Issue #411 is a high-priority silent failure in which the debugger traps the game invisibly." [335]
- Issue #416 is a medium bug where frame-dependent commands hang and timeout_ms is ignored in the bridge." [336]
- The previously merged batch #433–436 fixed issues #409, #410, #412, #420, and #421." [337]
- The recommended next batch consists of the four priority:high silent-failure bugs #422, #414, #413, and #411." [338]
- The navigation e2e test bakes an empty navmesh and asserts baked:true, which is the false success being fixed." [339]
- A red test for issue #414 reproduced the exact silent no-op, returning set:true while echoing null." [340]
- The engine is built on Godot 4.7, uses GDScript only (no GDExtension/C++), and targets the 'mobile' renderer." [341]
- Chunks are 16³ blocks stored in a PackedInt32Array flat storage with no palette or RLE compression." [342]
- Meshing is naive per-face culled with no greedy meshing, uses per-face UVs into a runtime-built texture atlas (64px cells from block registr [343]
- Collision uses one ConcavePolygonShape3D trimesh per chunk, rebuilt wholesale on every edit." [344]
- The engine has no LOD, no frustum culling beyond Godot default, no occlusion culling, and only a fixed 16-block chunk size." [345]
- Zylann's GodotVoxel module is built around a worker pool for meshing/saving, with only the irreducibly-main-thread parts (mesh upload, colli [346]
- Seed 12345 is a land world with ground at the spawn column y=7 and sea=-2." [347]
- Headless screenshots are not usable because the dummy renderer hands back null textures; visual verification must use the live editor via go [348]
- On clean main, a headless probe places the player at (8.5, 8.9, 8.5), eye at (8.5, 10.5, 8.5), with clear air at feet/eye/1-4m in front and  [349]
- test_spawn.gd and test_mesher.gd pass with 0 failed." [350]
- Clean main also has the _apply_mesh on freed-object error in test_threading.gd, a pre-existing teardown race (issue #20) unrelated to the sc [351]
- On clean main, in the windowed run the player at (8.5, 8.9, 8.5) is 0.1 m into the terrain (block 7 solid)." [352]
- The next work item is #5 (greedy meshing), the head of the tier-2 queue." [353]
- test_render_smoke.gd:49 calls look_at before add_child, logging \"Node not inside tree\" every run." [354]
- #5 greedy meshing is the only open story of epic #28 and is unblocked because the epic's stated purpose is \"before greedy/GDExtension\"." [355]
- ChunkData stores blocks in a dense PackedInt32Array(4096) indexed as x + y*n + z*n²." [356]
- FluidSim's _NEIGHBORS and _SIDE_NEIGHBORS are constant lists, gravity is a distinct −Y step, and the lateral lowest-open-neighbor tie-break  [357]
- In 0fps' culled meshing, culled meshing produces roughly 16× fewer quads than naive meshing on 16³ chunks, and greedy meshing is bounded at  [358]
- 15 monohedral convex pentagon tiling families are known, with attribution spanning Reinhardt 1918 through Mann/McLoud/Von Derau 2015." [359]
- The Cairo pentagonal tiling is the type 4 family, defined by two non-adjacent 90° angles each between equal-length sides, with b=c, d=e, B=D [360]
- The snub-square-dual Cairo form has angles 120°, 120°, 90°, 120°, 90° and side ratio 1 : (√3−1), with 4 long edges and 1 short edge." [361]
- The Cairo pentagonal tiling has 5 edge-neighbors per tile and is edge-to-edge and face-transitive." [362]
- In the truncated square tiling (4.8.8), each octagon has 4 octagon neighbors on alternating sides plus 4 square neighbors, totaling 8 neighb [363]
- The truncated square tiling is the truncation of the square tiling at every vertex, and the chamfered square tiling is the limit of alternat [364]
- The 11 convex uniform (Archimedean) tilings comprise 3 regular and 8 semiregular tilings, have 32 uniform colorings, and all are Wythoffian  [365]
- In the truncated triangular tiling (3.12.12), each dodecagon has 6 dodecagon neighbors and 6 triangle neighbors, each triangle has 3 dodecag [366]
- Cairo is the dual of the snub square tiling, whose wallpaper group is p4g, a 4-fold square-lattice symmetry; the basketweave is the degenera [367]
- BorisTheBrave 'Triangle Grids': triangles are always planar with per-vertex heights — a square heightfield is not." [368]
- The `godot-agents` repository functions as the orchestrator/client, depending on the `godot-mcp` repository for the actual Godot editor brid [369]
- The `godot-agents` system is tightly coupled to the specific `godot-mcp` server implementation, requiring its exact surface structure." [370]
- For `godot-mcp` versions 2026.08.31b4 and later, toolset enablement is server-global and persists across client connections." [371]
- The default transport mechanism is stdio, requiring the `godot-mcp` CLI to be resolvable via environment variables or installation path." [372]
- Since version 2026.08.31b4, `godot-mcp` emits a structured payload, which the client prefers for normalization over text parsing." [373]
- The build/verify/fix loop is capped by a default of 3 retries and a recursion limit of 50." [374]
- All configuration must be done via environment variables, as there is no configuration file." [375]
- The default transport mechanism for MCP is `stdio`." [376]
- The default port for HTTP transport is 9090." [377]
- Web search is disabled by default, requiring explicit opt-in to enable the retrieval band." [378]
- The experimental fluid executor is disabled by default, requiring explicit opt-in to activate the fluid loop." [379]
- Setting the MLflow tracking URI enables tracing and evaluation logging for the agent run." [380]
- The agent verifier can be instructed to run the project's existing GUT test suite after a code change." [381]
- Live mode execution, which provides the authoritative pass-rate, requires specific infrastructure components including a Godot editor, the ` [382]
- The execution flow involves the planner, executor, and verifier interacting with Godot via the MCP client." [383]
- The live calibration run requires a running Godot editor and the `godot_mcp` bridge and cannot be executed in CI." [384]
- Logging is controlled by setting the `MLFLOW_TRACKING_URI` environment variable, and without it, logging is a no-operation." [385]
- The Godot-native AI development platform is composed of three distinct layers: a Godot addon and bridge, an open-source FastMCP server, and  [386]
- The Godot addon and bridge holds direct authority over the live Godot editor state, scene trees, and runtime data." [387]
- The FastMCP server acts as the typed capability surface between the agent and Godot, managing safety, preconditions, and operation constrain [388]
- The agent system provides the policy and orchestration layer, managing planning, memory selection, and execution strategy." [389]
- The v1 implementation uses a LangGraph StateGraph architecture where nodes operate on typed shared state and return partial state updates." [390]
- The execution policy mandates that the MCP is the primary substrate for Godot work, requiring specific tool usage preferences." [391]
- Python 3.13 or newer is required for the setup." [392]
- The `godot-mcp` server is a standalone project, distinct from the agent's dependencies." [393]
- In service mode, a single `godot-mcp` HTTP service manages the editor bridge, preventing multiple clients from sharing the same live editor  [394]
- Godot version 4.4 or newer is required for live runs with the `godot_mcp` addon enabled." [395]
- Ollama defaults to listening on `http://127.0.0.1:11434`, unless overridden by `OLLAMA_HOST`." [396]
- MLflow tracing is optional; setting `MLFLOW_TRACKING_URI` enables logging, otherwise MLflow calls are no-ops." [397]
- The agent is a self-improving, local-first LangGraph agent for AI-driven Godot development." [398]
- The agent uses a LangGraph StateGraph composed of 14 nodes to manage the build → verify → fix loop." [399]
- Tracing to MLflow is conditional on setting the `MLFLOW_TRACKING_URI` environment variable." [400]
- The system requires Python 3.13+ and includes an 80% coverage gate in its CI workflow." [401]
- The default WebSocket server binds to `127.0.0.1` on port `9070`." [402]
- PR #439 (Refuse zero-polygon navigation bakes) has all green CI and no review yet." [403]
- PR #442 (Enforce local ollama-only graphify backend) has a CI failure in ruff." [404]
- PR #438 (Fix Object property coercion + null-write) has CI failures in e2e and mypy." [405]
- PR #442 has a real lint error: E501 line too long at scripts/graphify_gdscript_support.py:158." [406]
- Qodo found a real bug in PR #440 where EditorInterface.close_scene() closes the active tab, not the one for the deleted path, so multi-tab d [407]
- EditorInterface in Godot 4.7 exposes exactly 17 methods whose names contain \"scene\", spanning close_scene() through stop_playing_scene()." [408]
- The only scene-closing method is Error close_scene(), which takes zero parameters, closes the currently active scene discarding pending chan [409]
- open_scene_from_path opens the scene at the given path and creates a new inherited scene when set_inherited is true, but does not document a [410]
- reload_scene_from_path fails if the scene is not open." [411]
- get_open_scenes() and get_open_scene_roots() list all open scenes, but the active-tab cursor can only be moved implicitly." [412]
- The Godot 4.7 EditorInterface page has no Signals section, containing only Description, Properties, Methods, Property Descriptions, Method D [413]
- The `.opencode/plugins/graphify.js` plugin was rewritten to port graphify's full Claude Code `PreToolUse` guard pair from `graphify/cli.py:_ [414]
- The search guard fires on executed tokens with heredoc bodies and quoted spans stripped and wrappers skipped, so a command like `git commit  [415]
- The plugin fails open everywhere: any error results in no nudge and never a blocked call." [416]
- The reporter tested the setup with Godot 4.7.0, Godot MCP version 2026.09.10, on Windows 10." [417]
- The MCP server URL is entered as http://<IP or resolvable name>:<port>/mcp with a default MCP port of 9090." [418]
- The tool-name prefix is OpenWebUI's integration-ID namespacing rather than a server-side defect, mitigated by keeping the integration ID sho [419]
- After calling godot_enable_toolset for any gated toolset, the tools appear in godot_list_tools_by_safety_class but are not callable by the m [420]
- godot_enable_toolset() mutates the server-global enabled set in mcp_server/toolset_middleware.py but never emits a notifications/tools/list_ [421]
- FastMCP 4.0.1 has no server-side send_tools_list_changed helper, but the MCP SDK's ServerRequestContext provides notify_tools_changed()." [422]
- All 162 addon cmd_* handlers exist and match mcp_server/command_map.py." [423]
- The server-side fix emitting notifications/tools/list_changed after enable_toolset/disable_toolset is implemented and tested." [424]
- The root cause of the issue is claimed to be an OpenCode client bug rather than a godot-mcp server issue." [425]
- The issue was closed via PR #491 with the server-side fix implemented." [426]
- Issue #486 is in CLOSED state." [427]
- When .tscn or .gd files are edited externally, the Godot editor does not detect or apply the changes." [428]
- The user must manually close and reopen scenes, or restart the editor entirely, to apply external changes." [429]
- No cmd_scan, cmd_refresh, or cmd_reimport handler exists in the addon." [430]
- The addon only calls update_file() after its own writes." [431]
- Nothing reimports externally-edited .gd files or refreshes the filesystem on demand." [432]
- The proposed fix is to add a non-destructive cmd_rescan_filesystem handler that triggers EditorFileSystem.scan() to pick up external changes [433]
- Issue #487 is in CLOSED state." [434]
- When the same PackedScene is instanced twice, property overrides on the second instance's children are silently ignored." [435]
- No tool can enable Editable Children." [436]
- The tree inspector emits no owner/editable-instance metadata, so agents cannot distinguish instanced children from local nodes." [437]
- _cmd_instance_scene calls packed.instantiate(GEN_EDIT_STATE_INSTANCE) but never calls set_editable_instance() on the instance." [438]
- scene_inspect.gd traverses with un-owner-filtered node.get_children() and emits no owner or editable marker." [439]
- Node.set_editable_instance(node, is_editable) is the API that would fix the issue, but no handler or MCP tool exposes it." [440]
- Proposed fix: add a cmd_set_editable_children handler plus a corresponding mutating, UndoRedo-wrapped MCP tool." [441]
- Proposed fix: include owner and is_editable_instance metadata in serialize_tree output so agents can identify instanced vs local nodes." [442]
- Proposed fix: consider auto-enabling editable children when an agent creates a second instance of the same PackedScene." [443]
- Every session requires calling three tools before any work can begin." [444]
- Because of the missing notification, an agent that enables a toolset and tries to use its tools gets rejected, making the discovery protocol [445]
- One proposed option is to fix issue #1 first by emitting the notification so enabling toolsets works mid-session." [446]
- A GODOT_MCP_DEFAULT_TOOLSETS mechanism partially exists to let users pre-enable toolsets via env var or config." [447]
- A proposed option is a single godot_bootstrap(toolsets=[...]) call that returns server info, tool list, and enables requested toolsets in on [448]
- The issue was closed on the grounds that the mandatory 3-tool discovery protocol is by design per issue #26." [449]
- Referencing `$\"Soldier/AnimationPlayer\"` from a script resolves the path successfully." [450]
- The reported failure is a downstream symptom of Issue #3 (instanced scene overrides fail)." [451]
- When an instance fails to load due to the editable-children gap, nodes beneath it do not exist in the tree, so path resolution silently retu [452]
- The issue was fixed by fixing Issue #3, adding a `set_editable_children` tool plus owner metadata in tree inspection." [453]
- The closing comment by MuhamadBarzani attributes the issue to #487 (instanced scene overrides fail) rather than #3." [454]
- Per the closing comment, AnimationPlayer path resolution works correctly when the instance loads, and the failure is that the instance does  [455]
- MCPBridge._pending_times (mcp_bridge.gd:39) is read and erased in _handle_text() (lines 151-153) but is never populated anywhere." [456]
- An acceptance criterion is that latency_ms reported be either real round-trip with a documented origin timestamp or removed in favor of exec [457]
- Issue #520 is in state OPEN." [458]
- `MCPPlugin._server_version` is declared at godot_mcp.gd:36 and read by `_server_version_label()` at lines 205-214 but is never assigned." [459]
- A code comment claims the server version is populated when the bridge connects via cmd_get_project_info, but nothing wires that assignment." [460]
- The dock's version label can only ever show \"Godot x.y.z\" and never the server package version." [461]
- Issue #521 is in state CLOSED." [462]
- Issue #521 carries the labels bug and component:addon." [463]
- The proposed fix is to add a `cmd_get_addon_info` handshake and have the server push its version to the addon on connect, or embed the serve [464]
- `_server_version` should be assigned from the handshake so the dock label shows \"godot-mcp <calver> / Godot <x.y.z>\"." [465]
- A simpler alternative is to have `cmd_get_project_info` responses carry `server_version` and have the plugin intercept its own project-info  [466]
- An acceptance criterion is that `_server_version` is populated by a real value flowing from the server." [467]
- An acceptance criterion is that the dock displays both halves of the label once connected and a contract test pins the handshake envelope." [468]
- The fix pairs naturally with the `cmd_get_addon_info` issue and should be implemented together with it." [469]
- command_router.gd is 756 lines long." [470]
- An acceptance criterion is that no handler calls a private method on the router, with helpers coming from the new module." [471]
- An acceptance criterion is that existing contract tests pass unchanged, since envelope shapes are pinned and no behavior change is intended. [472]
- An acceptance criterion is that `graphify.sh update .` shows no new god-node and router complexity drops." [473]
- Issue #522 is in state CLOSED and carries the label component:addon." [474]
- The 20-node UndoRedo threshold (#461) exists in exactly one of three batch-apply paths." [475]
- In batch.gd, batch_set_property declares `var undo_threshold := 20` but hardcodes the literal `> 20` on line 183 and again in the hint text  [476]
- composite.gd's batch_create_nodes (line 161) and apply_node_edits (line 229) have no threshold at all." [477]
- A 500-node batch create opens one giant UndoRedo action (potential editor stall/perf cliff) while an equivalent-sized batch_set_property sil [478]
- batch.gd cross-scene path (_cross_scene_one) mutates scenes on disk directly with no undo anywhere." [479]
- Proposed fix: batch_create_nodes and apply_node_edits must return the same undoable + hint honesty fields batch_set_property does." [480]
- Proposed contract tests should pin threshold boundary (19/20/21), the undoable:false + hint fields on all three tools, and the hint naming t [481]
- Acceptance criterion: One shared const; no literal `20` outside it." [482]
- Acceptance criterion: All three batch tools return identical honesty-field shape (undoable, hint) — or a documented reason they differ." [483]
- Acceptance criterion: Tests updated in the same commit (rule testing)." [484]
- The addon's entire GDScript layer has zero automated tests." [485]
- Verification today is ~20 hand-run smoke scripts plus indirect pinning from Python contract tests using fake addons." [486]
- command_router.gd covers envelope validation, unknown-command handling, id stamping, the no-response catch-all, and cmd_run_commands batchin [487]
- type_coerce.gd covers all to_json/from_json shapes, string-form parsing, and error paths." [488]
- The fix proposes porting the pure-logic cases, starting small with type_coerce round-trips and router envelope shapes." [489]
- The fix proposes wiring the harness into CI as a job that only runs when `godot/addons/**` changes, on the self-hosted runner alongside `e2e [490]
- Acceptance criteria require that type_coerce.gd and command_router.gd envelope logic have automated GDScript tests that run headless." [491]
- Acceptance criteria require CI to run the harness on addon changes." [492]
- Acceptance criteria require zero skips, applying the enforcement suite health rule to the GDScript side." [493]
- Python-side contract tests pinning envelopes are located at tests/contract/test_bridge_envelope.py." [494]
- Error codes returned by the addon are raw strings written by hand in approximately 30 handler files." [495]
- The authoritative set of error codes is the ErrorCode enum in mcp_server/models/envelope.py." [496]
- Nothing ties the addon's hand-written error-code strings to the Python ErrorCode enum, so a typo'd or invented code would flow through to cl [497]
- The proposed fix adds a const error-code registry on the GDScript side and uses it in _fail call sites." [498]
- The proposed Python-side contract test scans godot/addons/godot_mcp/**/*.gd for string literals passed as the first _fail(...) argument and  [499]
- The proposed contract test runs in the existing pytest suite and requires no editor." [500]
- The Python-side contract test alone pins the addon side without needing the GDScript test harness and fails CI when the two surfaces drift." [501]
- An acceptance criterion requires a contract test that fails CI when the addon emits an error code not in the Python enum." [502]
- An acceptance criterion requires all current call sites to pass, with an audit for existing drift during implementation." [503]
- Issue #525 is in state CLOSED." [504]
- `_require_debug_session` in command_router.gd (lines 462-477) checks play session, debugger, and valid session id." [505]
- `_require_live_probe` in command_router.gd (lines 472-478) checks play session, debugger, and probe connected." [506]
- `_cmd_get_game_scene_tree` in runtime_session.gd (lines 88-93) re-implements the live-probe guard inline with an enhanced hint." [507]
- The enhanced hint includes the #454 \"max client limits reached\" diagnostic plus a `probe_never_connected: true` field that the shared help [508]
- `runtime_session._require_unpaused_live_probe()` (lines 20-29) chains `_require_live_probe` with a manual break-state check." [509]
- The proposed fix consolidates the guards into one guard module with composable play-session, debugger-session, live-probe, and unpaused guar [510]
- An acceptance criterion requires one implementation of each guard with no handler re-implementing precondition checks inline." [511]
- An acceptance criterion requires the #454 diagnostic to ship from every probe-gated handler, pinned with a contract test." [512]
- Issue #526 is in state OPEN and carries the label component:addon." [513]
- Issue #527 is in state CLOSED and is labeled documentation and component:addon." [514]
- The cleanup batch comes from the 2026-09-20 addon review and is entirely doc/comment level with no behavior change." [515]
- `from_json` shipped long ago, so the type_coerce.gd docstring should be updated to describe both directions." [516]
- The report proposes moving `_init`/`register` to the conventional top-of-file position used by every other handler module." [517]
- The `# -- batch/export/screenshot/project/resource helpers --` section headers at command_router.gd:504-512 are empty leftovers from past ex [518]
- The acceptance criteria require all four fixes in one small PR that is doc-only and skips the graphify refresh per workflow." [519]
- batch_set_property skips UndoRedo for operations above 20 nodes and reports undoable:false with a hint." [520]
- composite.gd's batch_create_nodes and apply_node_edits open a single giant UndoRedo action regardless of node count." [521]
- The add-child undo sequence block is duplicated in mutation._cmd_create_node, composite._cmd_compose_node, and composite._cmd_batch_create_n [522]
- _commit_add_child already exists on the command router and is used by audio, particles, scene_3d, and navigation handlers." [523]
- The persistence-verdict stamping loop is copy-pasted between batch.gd and composite.gd." [524]
- The proposed fix adds a composite variant that registers N children in one action." [525]
- The proposed fix extracts a _persistence_entries(nodes) helper for batch verdict stamping." [526]
- The proposed fix adds a shared threshold constant and honesty fields on composite tools." [527]
- Acceptance criterion: no handler hand-rolls the add-child undo sequence, and the composite N-child case is one helper." [528]
- Acceptance criterion: verdict stamping has one implementation used by both batch and composite." [529]
- Acceptance criterion: envelope shapes pinned by existing tests pass unchanged." [530]
- `godot_undo` is a core command implemented as `cmd_undo` in command_router.gd lines 251-275." [531]
- There is no `godot_redo` command." [532]
- `godot_redo` is proposed as mutating (dry_run, like `godot_undo`); `godot_list_history` is proposed as read_only." [533]
- The fix requires updating `docs/tool-contracts.md`, skills metadata pinned by `test_skills_metadata.py`, and the `testing`/safety-class matr [534]
- An acceptance criterion is that `godot_redo` mirrors `godot_undo`'s envelope and honesty shape, verified by a contract test." [535]
- An acceptance criterion is that `godot_list_history` returns the documented fields, and empty history returns zero-values rather than errors [536]
- Server and addon have no handshake." [537]
- The plugin declares `_server_version` (godot_mcp.gd:36) that nothing ever assigns (#521)." [538]
- When server/addon versions drift, the failure mode is opaque per-command `VALIDATION_ERROR: Unknown command 'cmd_x'` with no version context [539]
- Addon `cmd_get_addon_info` returns `{ addon_version, godot_version, commands: [all registered cmd_* names] }`." [540]
- Server pushes `server_version` back to the addon, assigning the dock's `_server_version` and resolving #521." [541]
- Server exposes the handshake via `godot_get_server_info`, whose capability snapshot gains `addon_version`, `godot_version`, and `addon_comma [542]
- Server warns (structured, not stack trace) when the addon lacks handlers for tools the server exposes, enabling version-drift detection." [543]
- `godot_get_server_info` reports addon version, Godot version, and registered-command count/list." [544]
- The dock shows the server version once connected, closing #521's missing half." [545]
- The addon can instance a saved scene into the tree via the scene_edit_instance_scene tool." [546]
- The proposed tool is named godot_scene_edit_extract_scene, in category scene_edit, with safety mutating." [547]
- The proposed tool takes params node_path, scene_path (destination res://), replace_with_instance bool default false, save_current bool defau [548]
- If replace_with_instance is true, one UndoRedo action removes the original subtree and instances the new .tscn in its place, preserving tran [549]
- The tool refuses when the subtree contains nodes owned by an instanced child that isn't editable, with a hint rather than silent partial ext [550]
- dry_run reports the node list that would be extracted plus the destination path." [551]
- The tool must be undoable, confirm-free (additive, mutating class), but honor dry_run." [552]
- The tool refuses non-owned/instanced subtrees with an actionable hint consistent with #477 rename refusals." [553]
- The issue proposes a tool named godot_project_move_file in the project toolset with safety mutating and a dry_run option." [554]
- The proposed tool moves or renames files within res:// while updating referencing files." [555]
- The Godot editor's own move dialog remaps scene-embedded and script class_name references." [556]
- An acceptance criterion requires move with reference remap across .tscn, .gd, and .tres files, verified by contract and live e2e smoke tests [557]
- An acceptance criterion requires docs and a tool-contract entry for the project toolset." [558]
- Issue #533 is a feature request for cmd_describe_class, which would expose ClassDB metadata (properties/methods/signals) for agent discovery [559]
- The proposed tool takes parameters class_name, include_inherited (bool, default false), and include_private (bool, default false)." [560]
- The addon response is built entirely from ClassDB and requires no live node." [561]
- Methods are returned as name/args/return_type entries obtained via class_get_method_list." [562]
- The response also includes signals, constants, enums, the inherits chain, and can_instantiate." [563]
- Acceptance criteria require a GDScript handler plus a FastMCP tool with a typed Pydantic response and a contract test that pins the envelope [564]
- Acceptance criteria require the tool to be read_only with category core." [565]
- The proposed server tool godot_runtime_get_output is read_only, gated by _require_live_probe, returns { stdout, errors, warnings, truncated  [566]
- An acceptance criterion is ring-buffer capture with a seq cursor and no unbounded growth across long sessions." [567]
- An acceptance criterion is a godot_runtime_get_output contract test (poll-and-cache envelope) plus a live e2e smoke in e2e.yml style." [568]
- The output ring buffer lives in the addon, consistent with #535's amendment that the addon holds state for live editor/runtime data while th [569]
- Issue #534 is in CLOSED state with labels enhancement and component:addon." [570]
- An acceptance criterion requires both sides ([Both]) to be implemented with snapshots that are JSON-safe and depth-capped." [571]
- A design amendment dated 2026-09-20 moved the snapshot store into the addon rather than the server, to keep the MCP layer stateless per the  [572]
- An optional on_change_only: bool = true param on godot_runtime_monitor_property defaults to true for the new behavior and false preserves ol [573]
- Acceptance criterion: float epsilon behavior is documented and a contract test pins the new param through the envelope." [574]
- The bridge accepts one active peer, and a second Godot editor instance silently replaces the first, causing the first agent to receive BRIDG [575]
- The server keeps the most recent peer but exposes the connection identity in godot_get_server_info as the project_path of the connected edit [576]
- A second peer joining logs a structured line naming both project paths." [577]
- The snapshot optionally includes previous_peer." [578]
- True multi-peer with per-peer command routing is a stretch goal, where the server routes by project path param or a connection handle." [579]
- Acceptance criterion: peer replacement produces a structured log entry with both project paths, not silence." [580]
- Acceptance criterion: the server is backward compatible by accepting peers without the hello (older addon) and marking identity unknown." [581]
- The Godot MCP bridge is localhost-only with no authentication in v1." [582]
- Anything on localhost can currently inject command envelopes into the bridge." [583]
- When the token is set, the addon's first message after connect is a handshake of the form { auth: <token> }." [584]
- A token mismatch manifests as a reconnect loop with a structured reason in the dock log." [585]
- An acceptance criterion requires token mismatch to yield a structured refusal at handshake, not per-command errors or a silent drop." [586]
- There are three possible connection statuses mapping to three immutable textures, and all of them are regenerated on each status change." [587]
- The proposed fix is to build the three status textures once lazily on first use into a Dictionary keyed by MCPBridge.Status, store them for  [588]
- The proposed fix frees the textures in _exit_tree, where plain dereference suffices because textures are Resources, but the dictionary is dr [589]
- An acceptance criterion requires one texture per status, built once." [590]
- MCPCommandRouter._prop_cache maps get_instance_id() to a property-type dict and is pruned by size with a 256 cap and full clear." [591]
- A freed node's cache entry can be served for a new object with the same id, returning stale property types for properties that don't exist o [592]
- _invalidate_prop_cache is only called by batch/composite apply paths." [593]
- A node deleted via cmd_delete_node leaves a stale entry until cap prune or id reuse." [594]
- The proposed fix is to key validity on ObjectID + liveness, storing a valid_at counter/frames, or in _property_type refresh when the cached  [595]
- A proposed hardening is to call _invalidate_prop_cache in cmd_delete_node / rename / batch-apply completion paths, since delete currently mi [596]
- An alternative proposed fix is to key the cache by WeakRef/ObjectID and validate is_instance_valid on hit with a one-line guard in _property [597]
- Acceptance criterion: stale entry cannot survive a freed/reused instance id, with unit-testing of the guard logic headlessly." [598]
- Acceptance criterion: delete path invalidates the target's cache entry." [599]
- PR #497 was merged on 2026-09-17." [600]
- The addon adds a new read-only cmd_get_scan_state command returning {scanning: bool} from EditorFileSystem.is_scanning()." [601]
- Contract tests pin the poll ordering, the quiet path, and the stuck path." [602]
- Both new contract tests fail without the cmd_get_scan_state poll or the rescan_pending field." [603]
- is_scanning() was verified on Godot 4.7.2, returning true during the initial scan and false once quiet." [604]
- The full preflight run reported 800 passed with ruff, mypy, and zero-skip, and integration smokes green." [605]
- docs/tool-contracts.md was updated with the result schema and a determinism paragraph." [606]
- PR #498 was merged on 2026-09-17." [607]
- batch_set_property already skipped EditorUndoRedoManager above 20 nodes as a performance guard." [608]
- batch_set_property now reports undoable: false plus a hint naming the threshold, while batches of 20 nodes or fewer explicitly report undoab [609]
- Contract tests pin both new behaviors, docs/tool-contracts.md was updated, and the change closes issue #437." [610]
- Live end-to-end checks against Godot 4.7.2 produced undoable:false plus hint for a 25-node batch, aborted_at=0 with skipped_count=1 and an u [611]
- The full preflight run reported 803 passed with ruff, mypy, and zero-skip clean." [612]
- The test test_batch_undoable_flag_addon_source_pins_gate_order reads the addon source file and asserts on the exact strings \"to_apply.size( [613]
- The PR review assigned a score of 92." [614]
- PR #499 was merged on 2026-09-17." [615]
- `create_scene(root_type=\"Collectible\")` on a registered custom `class_name` fails with `VALIDATION_ERROR: Unknown or non-instantiable root [616]
- The limitation is stated in the `godot_scene_edit_create_scene` tool description." [617]
- The limitation is stated in `docs/tool-contracts.md` with the create-then-attach_script workaround." [618]
- The PR is docs-only and the ruff/mypy/contract suite is green with zero-skip clean." [619]
- The PR type is Documentation." [620]
- The PR documents the `root_type` built-in ClassDB restriction." [621]
- The PR adds a workaround for custom `class_name` scripts." [622]
- The PR updates the tool description and contracts." [623]
- In `mcp_server/tools/mutation.py`, documentation was added to the `create_scene` tool description." [624]
- PR #500 is a CalVer release bump from 2026.09.10 to 2026.09.17." [625]
- The release is additive-only since the last tag and CONTRACT_VERSION stays 1." [626]
- The version bump is applied in lockstep across pyproject.toml, mcp_server/__init__.py, godot/addons/godot_mcp/plugin.cfg, README, and skills [627]
- PR #500 was merged on 2026-09-17." [628]
- The PR bumps the Python package version in __init__.py." [629]
- The PR updates version badges and text in README.md." [630]
- The PR review score is 95." [631]
- Issue #490 is partially compliant because the PR is a version bump only with no code changes to debug_workflow.py." [632]
- PR #501 was merged on 2026-09-18." [633]
- The PR changes line counts in skills and AGENTS.md from 55 to 65, 81 to 84, and 557 to 568." [634]
- The PR adds a \"Round-trip economy\" section in getting-started with guidelines: enable-as-needed, batch N commands into one `run_commands`, [635]
- PR #502 updated the tool count to 181 in documentation." [636]
- PR #502 was merged on 2026-09-18." [637]
- The registered tool surface is 181 tools, verified via local_provider.list_tools()." [638]
- The change was a count-only correction with no surface change." [639]
- README.md updated the tool count from 180 to 181 in three locations." [640]
- README.md corrected the stale count in the status badge, toolsets section, and all toolsets section." [641]
- skills/README.md updated the tool count from 180 to 181 in the skills documentation." [642]
- skills/godot-getting-started/SKILL.md updated the tool count from 180 to 181 in the getting started skill." [643]
- The PR review gave a score of 98." [644]
- PR #503 is merged on 2026-09-18." [645]
- PR #503 closes the last silent-failure class from the #458 family: structural edits." [646]
- _batch_targets descends into instanced children, so one aggregate ok never hides a lost target." [647]
- Addon compiles clean on Godot 4.7; full preflight green (807 passed, ruff/mypy/zero-skip)." [648]
- PR #504 adds a set_editable_children tool and instance metadata in the scene tree." [649]
- PR #504 was merged on 2026-09-18." [650]
- The godot_scene_edit_set_editable_children tool is mutating and UndoRedo-wrapped, and toggles Editable Children on an instanced scene." [651]
- The persisted verdict for editable children keys on the parent node because the flag is packed with the parent's entry." [652]
- Instanced nodes' children carry an owner field (the source scene's res:// path) and editable_children: true when the toggle is on." [653]
- Local nodes carry neither the owner nor editable_children key in the serialized tree." [654]
- The preflight check passed with 811 tests passed and ruff/mypy/zero-skip clean." [655]
- Issue #487 is assessed as partially compliant by the PR review." [656]
- Every poll-based handler now self-reports why it is pending with a stable `reason` token." [657]
- `poll_ready` relays the last `reason` in its expiry `ToolError`." [658]
- `cmd_get_import_status` maps to `rescan_in_flight` plus a `scanning: bool` flag." [659]
- A shared reason-token table was added to `docs/tool-contracts.md`, and the change is additive so `CONTRACT_VERSION` stays 1." [660]
- `poll_ready` relays `reason` in its expiry error, and a contract test pins that behavior red-first." [661]
- The addon compiles clean on Godot 4.7, and integration tests pass 56/56 locally." [662]
- PR #506, titled \"Echo audio bus effect properties in layout read\", was merged on 2026-09-18." [663]
- A read/write asymmetry existed because godot_audio_add_bus_effect accepts properties while godot_audio_get_bus_layout listed effects only as [664]
- AudioBusEffectInfo gains a properties field of type dict[str, Any], added additively so contract_version stays 1." [665]
- On Godot 4.7.2, adding an AudioEffectReverb with room_size 0.85 and wet 0.4 on bus \"Ambience\" resulted in the layout read echoing both val [666]
- The handler file godot/addons/godot_mcp/handlers/audio.gd was changed to extract exported properties from effects, JSON-coerce property valu [667]
- The contract test file tests/contract/test_audio.py gained a test for effect property echo that verifies read/write parity." [668]
- PR #507 adds a `godot_shader_validate` tool for headless shader compile checks." [669]
- PR #507 was merged on 2026-09-18." [670]
- A throwaway runner script sets the code on a scratch `Shader` to trigger the engine's compile, and `SHADER ERROR` / `Shader compilation fail [671]
- Live verification on Godot 4.7.2 showed the issue's exact repro (`uniform float edge_width : float`) returns `ok:false` with `\"Expected val [672]
- Contract tests were written red-first, integration tests passed 56/56 on-device, and full preflight passed 816 with ruff, mypy, and zero-ski [673]
- PR #508, which adds AudioStreamWAV loop settings to import_asset, was merged on 2026-09-19." [674]
- import_asset accepts loop config for .wav targets via options.import_settings with keys loop_mode, loop_begin, and loop_end." [675]
- The import_asset handler patches the .import sidecar's edit/loop_* params (ResourceImporterWAV option keys) and queues a reimport so the imp [676]
- The loop_applied field in the result reports whether the loop config was applied during that call, and because the change is additive contra [677]
- Live testing on Godot 4.7.2 showed importing a .wav with loop_mode: 1 produced loop_applied: true and the .import sidecar carried edit/loop_ [678]
- A red-first contract test named test_import_wav_loop_mode_applied was added, and the full preflight run passed 817 tests with ruff, mypy, an [679]
- The seeded-sidecar path writes remap/importer, remap/type, and deps/md5 into a fresh .import file, and whether Godot's import pipeline accep [680]
- docs/tool-contracts.md was updated to include loop_applied in the ImportAssetResult return fields and to document AudioStreamWAV loop settin [681]
- PR #509 adds the `godot_scene_edit_rescan_filesystem` tool (read_only, scene_edit toolset) that triggers `EditorFileSystem.scan()` so extern [682]
- The rescan is non-destructive by design: the scan reads the disk and refreshes the editor's view, discarding no editor state, in contrast to [683]
- The rescan response carries `scanned` and `scanning` keys derived from the same `is_scanning()` state, so the agent knows when the async sca [684]
- Live verification on Godot 4.7.2 via the bridge showed that writing a `.gd` file externally while the editor is open, then calling `rescan_f [685]
- PR #509 was merged on 2026-09-19." [686]
- `mcp_server/command_map.py` gained a mapping from `scene_edit_rescan_filesystem` to `cmd_rescan_filesystem`." [687]
- `mcp_server/models/scene_session.py` gained a `RescanFilesystemResult` Pydantic model with `scanned` and `scanning` fields." [688]
- The `_cmd_rescan_filesystem` handler does not register an UndoRedo action, so the filesystem scan cannot be undone via Ctrl+Z." [689]
- The optional `cmd_reload_scene` variant without confirm was not implemented, being explicitly noted as out of scope in the PR description." [690]
- PR #510, titled Release 2026.09.19, was merged on 2026-09-19." [691]
- The release bumps CalVer from 2026.09.17 to 2026.09.19." [692]
- The release is additive-only since the last tag, with CONTRACT_VERSION remaining 1." [693]
- The tool surface grows from 181 to 184 tools, adding set_editable_children, validate_shader, and rescan_filesystem." [694]
- The PR type is Documentation and Enhancement." [695]
- The configuration changes affect 3 files." [696]
- The documentation changes affect 5 files." [697]
- The reviewer guide estimates review effort as 1 and gives a score of 95." [698]
- The reviewer guide reports no relevant tests." [699]
- PR-Agent could not safely update the persistent review, so the standalone result will not replace the canonical review." [700]
- PR #511 adds a MkDocs documentation site and GitHub Pages deployment." [701]
- PR #511 was merged on 2026-09-19." [702]
- The documentation site is built with MkDocs Material and hosted at https://hybridindie.github.io/godot-mcp/." [703]
- The documentation site contains 17 new pages." [704]
- The architecture deep-dive section comprises 7 pages." [705]
- toolsets.md is generated from the live registry and covers 184 tools across 29 toolsets with safety classes." [706]
- mkdocs.yml configures the Material theme, dark/light mode, mermaid via superfences, tabs, and strict builds." [707]
- PR #512 is titled \"Fix docs toolchain installation in CI\"." [708]
- The fix was verified locally with the exact workflow command `uv tool install --with mkdocs-material --with mkdocs-exclude mkdocs` → `mkdocs [709]
- In .github/workflows/pages.yml, `uv tool install` was changed to use `mkdocs` as the primary tool instead of `mkdocs-material`." [710]
- The PR pins `mkdocs-material` version." [711]
- PR #513 was merged on 2026-09-19." [712]
- PR #513 carries the labels documentation and enhancement." [713]
- `/llms.txt` (page index) and `/llms-full.txt` (whole site as one markdown document, ~1800 lines) are generated at build time by the `mkdocs- [714]
- `mkdocs-llmstxt>=0.2,<0.4` is pinned in `requirements-docs.txt` and added to the pages workflow's toolchain install." [715]
- `mkdocs build --strict` runs clean with the plugin and produces both `llms.txt` and `llms-full.txt` with correct sections." [716]
- The full repo preflight reported 819 passed with ruff, mypy, and zero-skip." [717]
- README.md was updated with a docs badge and a Documentation callout naming the site and the two LLM entry points." [718]
- AGENTS.md was updated with the site URL, build pipeline, and the llms URLs to point agents away from crawling." [719]
- CONTRIBUTING was updated with local `mkdocs serve`/`build --strict` instructions and the llms files." [720]
- mkdocs.yml was modified to configure the `mkdocs-llmstxt` plugin." [721]
- The `mkdocs-exclude` plugin is installed in the CI workflow and `requirements-docs.txt` but is not listed in the `plugins` section of `mkdoc [722]
- PR #514 was merged on 2026-09-19." [723]
- The PR ports the documentation site from MkDocs to VitePress using the same tooling, layout, and page conventions as the wiki-fabric project [724]
- .vitepress/config.mts mirrors wiki-fabric's shape including base, mermaid plugin, local search, socialLinks, editLink, and footer." [725]
- docs/site/llms-gen.mjs runs as a post-build step generating llms.txt and llms-full.txt (~2200 lines) into dist/." [726]
- .github/workflows/deploy-docs.yml mirrors wiki-fabric's workflow using setup-node 20 with npm cache, npm run build, upload-pages-artifact, a [727]
- The mkdocs pages.yml and mkdocs.yml/requirements-docs.txt files are removed." [728]
- All 27 content pages were migrated with cross-links verified by VitePress's dead-link checker with ignoreDeadLinks set to false." [729]
- The full repo preflight reports 819 passed with ruff, mypy, and zero-skip." [730]
- PR #515 was merged on 2026-09-19 and labeled as a bug fix." [731]
- All 27 index links in llms.txt were verified to return HTTP 200 against the live site after the fix." [732]
- The llms-full.txt content was unaffected by the fix because it is raw markdown." [733]
- The fix updated the htmlPath function in docs/site/llms-gen.mjs to generate .html URLs for non-index pages." [734]
- The change to llms-gen.mjs was +6/-4 lines." [735]
- The PR reviewer guide scored the PR 95 with an estimated review effort of 1." [736]
- PR #516 was merged on 2026-09-19 and labeled documentation." [737]
- The llmstxt.org v2 spec added two capabilities beyond v1 that the site lacked: per-page markdown variants and discovery link relations." [738]
- Every rendered page serves clean markdown at its own URL with .md appended, so an agent can fetch the markdown variant directly without craw [739]
- 27 page.html.md variants are generated by llms-gen.mjs with frontmatter stripped." [740]
- The two discovery link relations are injected via VitePress's transformHead hook." [741]
- llms.txt follows the exact v2 file format: H1, blockquote, details, H2 file lists with ': notes', and an Optional section for secondary link [742]
- A local build produced dist/llms.txt, dist/llms-full.txt, and 27 *.html.md variants, with describedby/alternate link tags present in rendere [743]
- config.mts gained a transformHead hook to inject describedby and alternate link tags, a +16/-0 change." [744]
- llms-gen.mjs was rewritten to follow the llmstxt.org v2 spec and to generate <page>.html.md variants for all pages, a +168/-78 change." [745]
- PR #517 was merged on 2026-09-19." [746]
- Sidebar, index pages, and llms-gen.mjs sections were updated so the new pages flow into llms.txt/llms-full.txt automatically." [747]
- npm run build produced zero dead links, with new pages and .html.md variants in dist/ and the llms index carrying the new entries." [748]
- The PR's file walkthrough lists 7 documentation files changed." [749]
- PR #518 was merged on 2026-09-19." [750]
- VitePress only dead-link-checks markdown body links, so 13 config links shipped 404s silently." [751]
- All 16 stale config links were rewritten to the real flat page names, with architecture/* kept because those genuinely live in the subdirect [752]
- A new guard script docs/site/check-links.mjs is chained into npm run build, parses every link: '…' entry in config.mts, verifies it resolves [753]
- The new check-links.mjs file was added with 31 insertions and 0 deletions." [754]
- A reviewer flagged that the regex /link: '([^']+)'/g only matches single-quoted link values, so any double-quoted link entry in config.mts i [755]
- PR #519 was merged on 2026-09-19." [756]
- Issue #518 diagnosed the dead links correctly but shipped only the guard, leaving the config fix itself unstaged in that commit." [757]
- After `npm run build`, `dist/concepts.html` contains 0 occurrences of the old `getting-started/install` path and 1 occurrence of the correct [758]
- The link guard passes with 32 nav/sidebar links resolving." [759]
- The change to `docs/site/.vitepress/config.mts` is +15/-15 lines." [760]
- The guard `check-links.mjs` is not included in this PR's diff because it was already merged in #518." [761]
- The PR rewrites 13 links to flat paths but does not include the corresponding `.md` source files in the diff, so a reviewer cannot confirm t [762]
- PR #519 carries the labels enhancement, Bug fix, and Review effort 1/5." [763]
- PR #541 was merged on 2026-09-20." [764]
- A reverse-drift check requires every ErrorCode member to be either emitted by the addon or explicitly accounted for as server-only (BRIDGE_D [765]
- Running `uv run pytest tests/contract/test_addon_error_codes.py` produced 2 passed tests." [766]
- The full test suite run reported 821 passed with zero skips." [767]
- The `_FAIL_CALL` regex only matches `_fail(\"CODE\", ...)` where the code is a direct string literal, so variable or constant code reference [768]
- The reverse-drift test hardcodes a `server_only` set of three codes, so every enum addition requires a manual update to the test." [769]
- After the fix, the regex uses DOTALL across `_fail(` plus whitespace, catching the wrapped multi-line layout at 21 call sites, and collected [770]
- The ticket's suggested const error-code registry on the GDScript side was not implemented in this PR." [771]
- PR #542 was merged on 2026-09-20." [772]
- The new file godot/tests/type_coerce_smoke.gd adds 34 headless checks pinning the full coercion shape table against the real Godot runtime." [773]
- godot/tests/run_commands_smoke.gd was extended to cover the #461 honest-abort contract, including aborted_at/skipped_count/hint on halt, the [774]
- tests/integration/test_addon_read_smokes.py registers type_coerce_smoke in the pytest parameter list so it runs headless in CI wherever a Go [775]
- The tests are deterministic by design: no sockets, no editor, no wall-clock, no RNG, with exit code plus OK/FAIL markers as the assertion su [776]
- The full test suite run reported 822 passed with zero skips, and ruff plus mypy clean." [777]
- tests/contract/test_addon_error_codes.py adds a contract test ensuring addon error codes are a subset of the Python ErrorCode enum by scanni [778]
- The reviewer flagged that the _check function's `same` variable is dead code, since the function relies solely on _json_equal." [779]
- The redundant `same` local was fixed in commit da69c09 by removing the unused expression, leaving _json_equal as the single equality path, w [780]
- No new CI job was added for godot/addons/** changes; the new smoke tests ride the existing editor-dependent integration glob tests/integrati [781]
- Ticket #461's batch_set_property undoable flag and docs/tool-contracts.md update are out of scope for this PR and tracked separately as #523 [782]
- PR #543 implements the server↔addon handshake from issue #530, closing #521 as a side effect." [783]
- cmd_get_addon_info self-describes with addon_version (live from plugin.cfg), godot_version, and the live registered-command list from _handl [784]
- cmd_server_hello {version} stores the server's pushed package version (router.server_version), which the plugin entry reflects on the next 2 [785]
- The first successful handshake fire-and-forgets cmd_server_hello with the server's __version__." [786]
- BridgeDiagnostics gains addon_version/addon_commands fields and ServerDiagnostics gains addon_drift_warning." [787]
- A server↔addon version mismatch surfaces in godot_get_server_info as an addon_drift_warning naming the count of unregistered commands." [788]
- The contract test tests/contract/test_addon_handshake.py reports 10 passed covering shape, caching, degrade, and drift." [789]
- The full test suite reports 832 passed with zero skips and clean ruff + mypy." [790]
- The addon_info method was not protected by a lock, so two concurrent first calls could both send cmd_get_addon_info and cmd_server_hello." [791]
- The race condition was fixed in commit c6d46e5 by taking _addon_info_lock only while the cache is empty (double-checked), so N concurrent fi [792]
- PR #543 was merged on 2026-09-20." [793]
- PR #544, which unifies runtime probe and debug session guards into mcp_guards.gd, was merged on 2026-09-20." [794]
- Three drifted guard flavors were consolidated into a single module, MCPGuards, at godot/addons/godot_mcp/mcp_guards.gd." [795]
- command_router.gd's _require_debug_session and _require_live_probe implementations were replaced with delegating two-line wrappers, leaving  [796]
- runtime_session.gd's private _require_unpaused_live_probe re-wrapper now routes through _router._guards.require_unpaused_live_probe()." [797]
- get_game_scene_tree deliberately keeps its soft {playing, connected: false, probe_never_connected} result, consuming only the hint text from [798]
- The guards take an injectable play-session oracle (set_play_session_oracle) because the EditorInterface singleton in headless -s mode exists [799]
- is_game_paused() (the #411 tell) moved into the guard module, and is_breaked() logic is no longer duplicated." [800]
- tests/contract/test_addon_guards.py passed 5 tests, source-scanning for module existence, delegation-only wrappers, inline-copy removal, #45 [801]
- PR #545 was merged on 2026-09-20." [802]
- command_router.gd defines a single shared const MCP_UNDO_THRESHOLD := 20 plus the helper functions _undoable_for_count(count) and _undo_thre [803]
- Before this PR, composite.gd's batch_create_nodes and apply_node_edits had no undo threshold, so a 500-node batch create opened one giant Un [804]
- In composite.gd both batch tools became threshold-aware: above the threshold they bypass UndoRedo via direct set and report the same undoabl [805]
- The contract test file tests/contract/test_undo_threshold.py passed 5 tests covering shared const/decision site, delegation, hint single-sou [806]
- Running the headless threshold_smoke.gd script produced THRESHOLD_TEST_OK covering boundaries 19/20/21/500, hint wording, and the applies-no [807]
- The full test suite at the time of the PR description reported 844 passed with zero skips and clean ruff and mypy." [808]
- BatchCreateNodesResult regained the dry_run: bool = False field, which had been removed accidentally in the threshold commit." [809]
- Both _cmd_batch_create_nodes and _cmd_apply_node_edits now check params.get(\"dry_run\") and return a preview-shaped result without touching [810]
- After the review fixes, the full suite reported 846 passed with zero skips, clean ruff and mypy, and re-verified threshold_smoke and run_com [811]
- PR #546 was merged on 2026-09-20." [812]
- The router was approximately 816 lines, about two-thirds of which was boilerplate and a helpers grab-bag." [813]
- mcp_helpers.gd is a new module named MCPHelpers." [814]
- mcp_helpers.gd contains the #523 threshold single-source, including the UNDO_THRESHOLD const, undoable_for_count, and undo_threshold_hint." [815]
- Adding a domain now costs one table entry instead of four edits." [816]
- Shared-logic call sites were changed from _router._X to _router._helpers.X." [817]
- The RefCounted cycle is gone because handlers no longer keep per-domain members on the router." [818]
- `cmd_get_game_output` deliberately has no break-state gate so output remains readable while the game is frozen at a debugger break." [819]
- The full test suite reported 861 passed with zero skips, plus clean ruff and mypy runs." [820]
- godot-mcp is a standalone MCP server providing generic Godot editor control over the Model Context Protocol, usable by any AI agent harness  [821]
- The MCP server owns all safety/permission logic and Pydantic domain models and holds no Godot logic itself, forwarding to the addon over the [822]
- The Godot addon is a GDScript EditorPlugin (Godot 4.4+) whose WebSocketPeer client connects out to the server and is the only layer that tou [823]
- JSON envelopes are versioned from day one, with command {id, command, params} and response {id, ok, result, error} correlated by id." [824]
- All create/rename/delete/set operations in the addon must register with EditorUndoRedoManager." [825]
- The toolchain requires Godot 4.4+ (validated on 4.7-stable), Python 3.11+, and FastMCP 4.0.1, managed with uv." [826]
- The addon connects to the server's bridge listener at default ws://127.0.0.1:9080 (configurable via GODOT_MCP_BRIDGE_URL) and reconnects aut [827]
- godot-mcp requires Python 3.11 or newer, managed with uv." [828]
- godot-mcp requires Godot 4.4 or newer and has been validated on 4.7-stable." [829]
- The project pins FastMCP 4.0.1, which is GA on MCP SDK v2 (the 2026-07-28 sessionless protocol)." [830]
- The system is two halves joined by a WebSocket bridge: AI client over stdio to a Python FastMCP server, then WebSocket to a GDScript Godot a [831]
- The MCP server owns all safety/permission logic, Pydantic models, and tool schemas, and never touches Godot directly." [832]
- The Godot addon is the only layer that touches the Godot Editor API and routes commands to cmd_* handlers." [833]
- Tools tagged destructive may be irreversible and require both dry_run and confirm: bool = True." [834]
- Zero skipped tests are a blocking gate: no @pytest.mark.skip, no xfail, and no bare pytest.skip() are allowed." [835]
- Versioning uses CalVer YYYY.MM.DD[-N], and the version must stay in lockstep across pyproject.toml, mcp_server/__init__.py, godot/addons/god [836]
- The Qodo PR bot automatically runs /describe and /review on pull requests, and findings must be fixed or replied to before merge." [837]
- The editor dials and the server listens, but the server still drives every command, with those two directions decoupled." [838]
- The FastMCP server is implemented in Python under mcp_server/." [839]
- The Godot addon is GDScript with the @tool annotation, located in addons/godot_mcp/." [840]
- mcp_bridge.gd is a WebSocket client that connects to a URL and reconnects with backoff." [841]
- The addon dials out to ws://127.0.0.1:9080." [842]
- The server boots, binds port 9080, and waits." [843]
- The server owns all safety/preconditions while the addon owns all Godot calls, and neither crosses the seam." [844]
- The AI client communicates with the server over stdio using the MCP protocol." [845]
- The bridge connection direction is inverted: the server listens and the editor connects out." [846]
- The server initiates every command and the addon responds; the addon never pushes unsolicited commands." [847]
- Error codes must be stable and drawn from the enumerated set, never ad-hoc strings." [848]
- Godot types cross the bridge as JSON-safe forms coerced on the addon side in the dedicated type_coerce.gd helper (MCPTypeCoerce), never inli [849]
- Because the WebSocket bridge is synchronous (one request to one response), the round-trip to the running game is poll-and-cache: a command s [850]
- The Godot editor→game debugger protocol supports step control, stack-frame inspection, and expression evaluation over the same EditorDebugge [851]
- A Tier 2 debugger toolset (step_*, continue, godot_debugger_get_stack_frames, godot_debugger_evaluate_expression) is implementable with no e [852]
- The Godot editor is single-threaded: the addon drains queued command packets once per _process frame and executes them serially on the main  [853]
- Change #166 dropped a redundant preflight round-trip per mutation." [854]
- godot_composite_run_commands executes a whole command list in a single frame and returns one envelope per command, collapsing N round-trips  [855]
- Each sub-mutation in a composite batch wraps its own UndoRedo action and command order is preserved." [856]
- godot_composite_run_commands cannot be nested." [857]
- The MCP spec's 2026-07-28 revision removes sessions and the initialize handshake entirely." [858]
- In the 2026-07-28 revision, per-request `_meta` carries version/capabilities instead of handshake negotiation." [859]
- Cross-call state moves to explicit handles: server-minted tokens passed as ordinary tool arguments, the pattern `request_state` already uses [860]
- godot-mcp is pinned to FastMCP 4.0.0b3, which speaks 2025-era session semantics." [861]
- FastMCP 4.0's `Client` already negotiates sessionless by default, so real client traffic godot-mcp sees is the sessionless 2026-07-28 protoc [862]
- The issue's premise that ToolsetMiddleware keys enable/disable on `context.session_id` was fixed in #370/#364 (merged 2026-08-27), which rem [863]
- The destructive-tool approval guard has no session dependency; it uses an `InputRequiredResult` plus `request_state` round-trip that is dura [864]
- A source-shape guard (`tests/contract/test_sessionless_invariants.py`) AST-scans `mcp_server/**` so no module may read `.session_id`/`.sessi [865]
- Unlike a spec-default server that scopes a grant to the caller, godot-mcp's grants are visible to every client of the process." [866]
- Every @mcp.tool takes typed parameters and returns a typed Pydantic model, never a raw dict." [867]
- Every @mcp.tool validates inputs and checks preconditions before any side effect." [868]
- Every tool is tagged with exactly one safety class." [869]
- dry_run=True returns what would happen and performs nothing." [870]
- All safety logic lives in mcp_server/safety.py, never in the addon." [871]
- Every JSON-result tool declares a standard outputSchema and returns structuredContent alongside text content, with FastMCP 4.0 deriving both [872]
- godot_editor_capture_screenshot returns ImageContent (non-JSON), so it declares no schema and no structuredContent." [873]
- GODOT_MCP_APPROVAL_TIMEOUT defaults to 30.0 seconds per request." [874]
- godot_enable_toolset checks the connected Godot version lazily once per session via cmd_get_project_info against TOOLSET_MIN_GODOT in mcp_se [875]
- The tutorial requires Godot 4.4+ installed, uv (Python package manager), and the godot-mcp addon enabled in the project." [876]
- Every time the MCP client connects, the server sends initialization instructions that explain the gating system." [877]
- Only after enabling a toolset can you call the tools in that category." [878]
- The LLM can discover workflow prompts via list_prompts() and render them via get_prompt(name) or render_prompt(name)." [879]
- Every tool's description explicitly states which toolset it belongs to." [880]
- The Coin Collector mini-game has a player (CharacterBody2D) that moves with arrow keys." [881]
- The Coin Collector mini-game has three gold coins (Area2D) scattered on the map." [882]
- godot-mcp has 180 tools across 29 categories." [883]
- Only the inspection toolset is enabled by default among the 28 toggleable toolsets." [884]
- The PyPI package is named godot-editor-mcp." [885]
- The Docker image is ghcr.io/hybridindie/godot-mcp." [886]
- Version 2026.09.10 is the first stable release." [887]
- godot-mcp bridges an AI agent and a live Godot editor, allowing the agent to drive the editor directly instead of editing files on disk." [888]
- The server is game-agnostic and knows Godot, not the user's game." [889]
- Godot minimum version is 4.4 and the recommended validated target is 4.7." [890]
- The addon checks the editor version on enable and warns if it is older than Godot 4.4." [891]
- The server listens on http://localhost:9090 for MCP HTTP and ws://localhost:9080 for the bridge." [892]
- This repository is the genesis repository that generates AI assistant harnesses for .claude/, .github/, and .opencode/ from a single set of  [893]
- The repository also hosts the Epic Scoping Skills as its own installed harness." [894]
- The genesis harness uses templates/_shared/ rendered into target projects by bootstrap.sh." [895]
- Epic Scoping Skills use .agents/ as the source rendered into thin wrappers in .claude/, .opencode/, and .github/." [896]
- The golden rule is to edit content in .agents/ for epic skills or templates/_shared/ for genesis." [897]
- Content must never be duplicated into a wrapper." [898]
- Shared rules referenced by multiple files live in a doctrine/ layer and should be referenced rather than restated." [899]
- The on-demand reference sections are not auto-loaded." [900]
- The post-bootstrap flow is bootstrap.sh (render) → /harness-eval (trim + suggest) → /customize-harness (domain tailoring)." [901]
- Each skill wrapper is a thin pointer, and the model reads the .agents/ body on-demand when the skill is invoked." [902]
- The shared, tool-agnostic project context — covering what this repo is, how the genesis bootstrap works, the source structure, and the Epic  [903]
- Only Claude-Code-specific notes belong in this file." [904]
- Claude-specific harness assets (skills, hooks, scripts) live under `templates/claude-code/.claude/`." [905]
- These assets are generated output where mirrored from `templates/_shared/`." [906]
- The Drift policy is in AGENTS.md." [907]
- The drift check is a Claude Code hook invoked as `bash templates/claude-code/.claude/hooks/check-primitive-drift.sh`." [908]
- The drift check should be run from repo root with a bootstrapped harness in scope." [909]
- Adding a new article requires adding a .md file to templates/_shared/articles/, adding an entry in mirror-pairs.json, and running bootstrap  [910]
- Adding a new agent requires adding a .md file to templates/_shared/agents/ and an agent_entries entry in mirror-pairs.json." [911]
- Adding a new command requires adding a .md file to templates/_shared/commands/ and a command_entries entry in mirror-pairs.json." [912]
- Shared doctrine requires a doctrine_entries entry in mirror-pairs.json with source_file and render_dir set to .claude/rules/doctrine, and do [913]
- Drift is checked by running bash templates/claude-code/.claude/hooks/check-primitive-drift.sh from the repo root with a bootstrapped harness [914]
- A patch version bump (x.y.z to x.y.(z+1)) covers typo, wording, or formatting fixes that do not change behavior." [915]
- A major version bump (x.y.z to (x+1).0.0) covers a workflow restructure that breaks existing handoffs or response-state contracts." [916]
- Each file versions independently, with doctrine/ and skills/ files versioned separately so bumping a skill does not require bumping the doct [917]
- templates/_shared/ is the single source, and the platform-specific files under templates/claude-code/.claude/agents/, templates/claude-code/ [918]
- Shared content lives in `.agents/` as plain markdown with no frontmatter and no harness-specific fields." [919]
- Each harness has its own thin wrapper files containing only the frontmatter that harness recognizes." [920]
- The harness wrapper files reference the shared content by path." [921]
- Harness wrappers are located at `.opencode/skills/<name>/SKILL.md` plus opencode.json commands for Opencode, `.claude/skills/<name>/SKILL.md [922]
- Both the epic-scoping skills and the genesis meta-flow follow the shared-content/wrapper rule." [923]
- `bootstrap-harness` is the single canonical body for installing and tailoring a harness." [924]
- The `install-harness` agent (Claude Code / Copilot) is a thin entry point pointing at the same bootstrap-harness file." [925]
- Genesis template output under `.github/instructions/`, `.github/copilot-instructions.md`, etc. is exempt from the `.agents/` rule and is ded [926]
- The golden rule is to edit content in `.agents/`, edit frontmatter in the harness wrappers, and never duplicate content into a wrapper." [927]
- `.agents/doctrine/` holds rules shared across multiple skills and rubrics, covering acceptance-criteria linting, parallelization, AI-readabl [928]
- The bootstrap script reads templates/_shared/ as the canonical source and renders three equivalent harnesses into a target project." [929]
- For Claude Code, the entry point is CLAUDE.md and rules live in .claude/rules/, .claude/agents/, and .claude/commands/." [930]
- For GitHub Copilot, the entry point is .github/copilot-instructions.md and rules live in .github/instructions/, .github/agents/, and .github [931]
- For Opencode, the entry point is CLAUDE.md and rules live in .opencode/." [932]
- The recommended auto-detect install command is `bash templates/scripts/bootstrap.sh --auto-detect --output-dir /path/to/target/project`." [933]
- The `--auto-detect` flag inspects `--output-dir` for stack, versions, and dependencies." [934]
- The `--mode backend-only` flag skips all frontend rules and placeholders." [935]
- The epic-composer skill transforms source material into a complete Epic." [936]
- The story-decomposer skill decomposes a ready Epic into INVEST-compliant stories." [937]
- The task-decomposer skill breaks down stories into AI-executable tasks with parallelization assessment." [938]
- The acceptance-criteria-rules.md doctrine module is referenced by epic-acceptance-linter, epic-composer, story-decomposer, epic-rubric dim 8 [939]
- When a rule is shared by two or more skills or rubrics, it belongs in doctrine/." [940]
- Each skill wrapper is a one-line body referencing .agents/skills/<name>.md." [941]
- The Opencode and Claude Code wrappers take $ARGUMENTS for user-provided input." [942]
- The epic-composer skill labels its output with the progression SYNTHESIS_ONLY → INTERVIEW_REQUIRED → PARTIAL_EPIC → FINAL_EPIC." [943]
- The templates/_shared/articles/ directory contains constitutional rules that are rendered into all three harnesses." [944]
- The templates/_shared/agents/ directory contains shared agent definitions where Claude frontmatter is transformed into Copilot frontmatter." [945]
- The templates/_shared/commands/ directory contains shared commands/prompts whose body is identical across platforms." [946]
- The templates/_shared/doctrine/ directory contains shared rules referenced by multiple articles/agents and is rendered to .claude/rules/doct [947]
- The templates/_shared/skills/ directory contains shared shippable skills that are rendered into target .claude/ and .opencode/." [948]
- The mirror-pairs.json file is the single source of truth for all mirror pairs, including entries, agent_entries, command_entries, and doctri [949]
- The bootstrap.sh script is the main installer." [950]
- The generate-copilot-mirrors.py script transforms Claude frontmatter into Copilot frontmatter and skips the doctrine/ directory." [951]
- epic-composer includes a Phase 0: Context Discovery that distinguishes greenfield from brownfield." [952]
- epic-composer includes a Phase 1: Source Synthesis." [953]
- epic-composer includes a Phase 2: Contradiction & Completeness Review." [954]
- epic-composer includes a Phase 3: Guided Interview that invokes epic-interview in waves." [955]
- epic-composer includes a Phase 4: Epic Draft that uses epic-shell, linter, and traceability." [956]
- epic-composer includes a Phase 5: Readiness Assessment that applies epic-rubric." [957]
- epic-composer includes a Phase 6: Stakeholder Review Checkpoint." [958]
- The epic-composer pipeline produces a Ready Epic artifact with a traceability map and a readiness level." [959]
- story-decomposer includes a Phase 1: Epic Validation." [960]
- story-decomposer includes a Phase 2: Decomposition Planning that uses a coverage matrix." [961]
- Harness evaluation is run after bootstrap.sh has rendered the harness into a project." [962]
- Phase 4 does not create files yet; it only lists suggestions for the user to pick." [963]
- The rules state to propose, not execute — never delete or edit files without confirmation." [964]
- If a rule is shared across 2+ articles, it belongs in doctrine/ and should be referenced, not inlined." [965]
- The repo is public, so nothing here needs authentication." [966]
- All routes run the same flow defined in `.agents/skills/bootstrap-harness.md`." [967]
- The one-command install clones the genesis repo into `~/.cache/instructions-and-rules`." [968]
- The one-command install requires no interview and no authentication." [969]
- The install script accepts options after `bash -s --`, including `--output-dir` and `--ref`." [970]
- The interactive prompt works identically in Claude Code and Opencode." [971]
- From a clone, Claude Code / Opencode can run `/bootstrap-harness` with an output dir argument or from the target project." [972]
- Each harness has its own thin, frontmatter-only wrapper files that reference the shared content by path." [973]
- Rules shared across multiple skills and rubrics live in `.agents/doctrine/` and are referenced rather than restated, which keeps the skills  [974]
- Each skill labels its output with one of a defined set of response states." [975]
- Every skill can be invoked two ways: directly via its slash command, or automatically when the harness loads the matching skill based on the [976]
- Opencode skills are model-invoked only, so the commands in `opencode.json` are the slash path." [977]
- Claude Code skills double as slash commands and accept `$ARGUMENTS`." [978]
- Each harness ships a non-blocking pointer-edit guardrail that warns but never blocks when a thin wrapper or a load-bearing `.agents/doctrine [979]
- Claude Code additionally runs an `InstructionsLoaded` hook that logs which instruction files load to `.claude/hooks/instructions-loaded.log` [980]
- The repository generates equivalent instruction harnesses for GitHub Copilot, Claude Code, and Opencode with a single command." [981]
- The .claude/rules/ directory contains the Constitutional Articles I–X plus doctrine and is the source of truth." [982]
- The golden rule requires editing content in .agents/ or templates/_shared/, editing frontmatter in the harness wrappers, and never duplicati [983]
- The flask profile has 5 overlays (architecture, api-design, testing, async-patterns, error-handling) that change to Flask blueprints, sync-f [984]
- Claude rules and Copilot instructions are body-identical mirrors, with generate-copilot-mirrors.py creating Copilot mirrors and check-primit [985]
- Anthropic explicitly warns that bloated CLAUDE.md files cause Claude to ignore actual instructions." [986]
- AGENTS.md is the lowest-common-denominator portable file across all 4+ platforms." [987]
- Articles I, II, IV, V, VI, and IX have zero automated enforcement." [988]
- Tech stack versions are duplicated across 10+ files." [989]
- Backend lint and typecheck are run with `cd backend && uv run ruff check src/ && uv run mypy src/`." [990]
- Frontend verification runs `cd frontend && npm run lint && npm run type-check`." [991]
- The backend uses FastAPI + LangGraph 1.0 for recommendation agents." [992]
- The frontend uses Next.js with shadcn UI components." [993]
- There is no direct DB access from the frontend; all queries go through the API layer." [994]
- Type hints are required on all function signatures and enforced by mypy." [995]
- Tier-based cache TTL in `by_request_hash_tiered` is finished=90d / airing=3d / upcoming=14d / NULL=7d." [996]
- Supabase is used as the sole backend infrastructure provider for database, authentication, file storage, and real-time subscriptions." [997]
- SQLAlchemy ORM is explicitly excluded; the Supabase Python client is used directly instead." [998]
- Redis is explicitly excluded; Supabase is used for caching patterns where needed." [999]
- Celery is explicitly excluded; async Python tasks or LangGraph are used for workflows." [1000]
- Built-in Row Level Security (RLS) enforces data isolation at the database layer." [1001]
- SQLAlchemy bypasses Supabase RLS policies unless explicitly configured." [1002]
- Vendor lock-in to Supabase means migrating away requires rewriting repositories." [1003]
- Auth tokens are validated via supabase.auth.get_user(token) with no static secret decoding." [1004]
- NomikaiList's AI coding assistant configuration lives in AGENTS.md, .opencode/, and .claude/rules/, loaded via opencode.json instructions." [1005]
- AGENTS.md is the derived entry point that summarizes and links the rules but does not replace them." [1006]
- A machine-readable checker at backend/scripts/check-constitution.py validates articles against the running codebase on demand and in CI." [1007]
- A rule update order is defined as .claude/rules/ → AGENTS.md." [1008]
- An instructions-drift checker at scripts/check-instructions-drift.sh validates that the opencode config and agent/command files exist and ar [1009]
- The constitution checker runs in CI and violations block merges." [1010]
- check-agent-drift.sh hooks warn when .claude/rules/ changes without downstream updates." [1011]
- CalVer (2026.04.24) on enforcement.md tracks the rule publication date." [1012]
- check-constitution.py Article IX checks that enforcement.md exists." [1013]
- NomikaiList enforces a 68% minimum aggregate test coverage threshold in CI." [1014]
- The project adopts a tiered coverage model that sets expectations by module risk level while supplementing rather than replacing the 68% CI  [1015]
- Privacy/Auth modules (services/privacy_service.py, services/auth_service.py, api/routes/auth.py) have a coverage target of at least 90%." [1016]
- Revenue/Data integrity modules (repositories/*, services/import_service.py, api/routes/media.py) have a coverage target of at least 80%." [1017]
- AI Agents/ML modules (agents/*, ml/*, services/recommendation_scorer.py) have a coverage target of at least 50%." [1018]
- Utilities/Config modules (config.py, adapters/*, CLI helpers) have a coverage target of at least 50%." [1019]
- Tests are authored in the order: contract tests, integration tests, E2E tests, then unit tests." [1020]
- Per-axis weights at or above SIGNAL_FLOOR (0.1) are summed and normalised against the count of media attributes on that axis, not the count  [1021]
- Cross-axis composition uses a simple unweighted mean over non-zero axes." [1022]
- The service is deterministic: the same (user, media) pair returns the same payload until profile data changes, and it landed with 8 unit tes [1023]
- All six review-queue routes execute via the service-role Supabase client (get_supabase_admin_client), which bypasses Row-Level Security by d [1024]
- The MAL adapter was built on the public Jikan proxy at api.jikan.moe/v4." [1025]
- The public Jikan proxy is being retired upstream." [1026]
- The decision is to self-host Jikan v4 via the official jikanme/jikan-rest Docker image backed by MongoDB, TypeSense, and a private Redis." [1027]
- Self-hosting requires zero adapter logic changes, only swapping base_url, while retaining full feature parity including themes, episodes, an [1028]
- The rate limit is raised from 50 to 120 req/min, configurable via JIKAN_RATE_LIMIT_PER_MINUTE." [1029]
- The Compose stack grows by 4 containers (jikan-rest, MongoDB, TypeSense, backing Redis) and adds ~1.5 GB of memory in dev." [1030]
- NomikaiList provides a RESTful API for anime and manga discovery and recommendation." [1031]
- The development base URL for the NomikaiList API is http://localhost:8000." [1032]
- The NomikaiList API version is v1." [1033]
- POST /auth/signup creates a new user account." [1034]
- POST /auth/login returns an access_token, token_type bearer, and expires_in 3600." [1035]
- GET /media/search supports query parameters q (required), media_type (optional), limit (default 20, max 100), and offset (default 0)." [1036]
- POST /ratings requires an Authorization Bearer token and accepts media_id, rating_type (like/dislike/curious), notes, and status (watching/c [1037]
- GET /recommendations returns personalized recommendations with fields id, media_id, score, reason, algorithm, and media." [1038]
- Rate limits are applied per endpoint: Authentication 5 requests/minute, Search 100 requests/minute, Recommendations 30 requests/minute, and  [1039]
- All error responses follow a format containing detail, error_code, request_id, timestamp, and path." [1040]
- The CI setup requires four Supabase test environment secrets: SUPABASE_TEST_URL, SUPABASE_TEST_ANON_KEY, SUPABASE_TEST_SERVICE_KEY, and DATA [1041]
- AWS deployment secrets (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) are optional." [1042]
- A new Supabase project for testing should be created separately from production." [1043]
- Database migrations are applied by iterating over all .sql files in backend/migrations and executing them with psql." [1044]
- The CI/CD Pipeline workflow runs on every push to main and every pull request." [1045]
- The test-backend job enforces 90% coverage for security code." [1046]
- The Security Scanning workflow runs on pushes to main/develop, pull requests, and a weekly schedule." [1047]
- The rls-security-tests job runs all RLS tests with a 90% coverage requirement and verifies RLS is enabled on all tables." [1048]
- Coverage requirements are 90% for security code (enforced by --cov-fail-under=90 in CI) and 80% for general code (enforced by pytest.ini con [1049]
- RLS tests are skipped for pull requests from forks because GitHub does not expose secrets to forks." [1050]
- Best practice is to use a dedicated Supabase project for testing, not production." [1051]
- Supabase remains the managed database, auth, and storage, and no Vercel, Fly.io, Railway, Render, or AWS is in the production path." [1052]
- NEXT_PUBLIC_* values are inlined into the client bundle at build time by Next.js, and because frontend/Dockerfile.prod does not accept them  [1053]
- Prerequisites include Python 3.11+, Node.js 18+, `uv` package manager, Git, and a Supabase account." [1054]
- Backend setup uses `uv sync` to create a virtual environment and install dependencies." [1055]
- Frontend setup uses `npm install`." [1056]
- Create `.env` file in project root by copying `.env.example`." [1057]
- Required environment variables include Supabase configuration (SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY, DATABASE_URL) and external  [1058]
- Development servers are run with backend command `uv run uvicorn src.main:app --reload --port 8000` and frontend command `npm run dev`." [1059]
- Access URLs are frontend at http://localhost:3000, backend API at http://localhost:8000, and API docs at http://localhost:8000/docs." [1060]
- Database schema is managed through Supabase." [1061]
- Alembic/SQLAlchemy migrations have been removed." [1062]
- New Supabase tables should be created with Row Level Security (RLS) policies." [1063]
- Contributing workflow uses TDD approach (RED → GREEN → REFACTOR)." [1064]
- The OLLAMA_BASE_URL default is http://localhost:11434/v1." [1065]
- graphifyy 0.8.6+ handles Ollama extraction natively." [1066]
- NomikaiList supports importing from MyAnimeList (via Jikan), AniList (GraphQL), and Kitsu (JSON:API)." [1067]
- Bulk catalog import uses `backend/scripts/comprehensive_import.py` for catalog seeding and incremental sync." [1068]
- A full import from all supported platforms can be run with `uv run python scripts/comprehensive_import.py --all --limit 500`." [1069]
- An incremental update can be run with `uv run python scripts/comprehensive_import.py --all --incremental`." [1070]
- Incremental catalog sync uses each adapter's recently-updated endpoint when supported." [1071]
- If an adapter does not support recently-updated fetch, the service falls back to top-media fetch and logs a warning so operators can detect  [1072]
- For recurring imports, script execution can be scheduled using cron, GitHub Actions scheduled workflow, or hosting provider scheduled jobs." [1073]
- NomikaiList is a privacy-first anime and manga discovery platform that combines the best features of existing platforms with modern AI-power [1074]
- Import and sync ratings from AniList, MyAnimeList, and Kitsu." [1075]
- Every recommendation includes a human-readable explanation of why you're getting it." [1076]
- Multiple algorithms are used: collaborative filtering, content-based, hidden gems discovery, and controversy filtering." [1077]
- Row-level security is implemented at the database level." [1078]
- The media catalog is a normalized database from multiple platforms." [1079]
- Cross-platform deduplication ensures you see one entry per title." [1080]
- NomikaiList uses an AI-driven graph recommendation engine that builds a dynamic taste profile from your ratings and viewing patterns." [1081]
- The graph recommendation system considers your direct ratings and viewing history, similar users' tastes, content attributes, hidden gems, a [1082]
- NomiKaiList uses Supabase's Row Level Security (RLS) to enforce data access controls at the database level." [1083]
- The service role is a privileged Supabase role that bypasses all RLS policies." [1084]
- Public Read pattern allows anyone to read data, but only service role can modify." [1085]
- Typography uses three font families, each with a clear role, and roles must never be mixed." [1086]
- The AI drawer pattern is a 560px slide-in panel from the right." [1087]
- The design system prohibits dark mode." [1088]
- The recommended testing approach is to use Local Supabase for all database-dependent tests." [1089]
- Integration tests always use Local Supabase and never use the Mock Client." [1090]
- Contract tests always use Local Supabase and never use the Mock Client." [1091]
- Unit tests with a database prefer Local Supabase, with the Mock Client as fallback only." [1092]
- The backend test suite contains 37 test files." [1093]
- The backend contract test suite contains 21 files." [1094]
- The backend integration test suite contains 7 files." [1095]
- The backend unit test suite contains 5 files." [1096]
- Recommendation generation has a performance requirement of under 2 seconds." [1097]
- The backend pytest configuration sets the coverage failure threshold at 80%." [1098]
- The frontend Jest configuration requires global coverage thresholds of 80 for branches, functions, lines, and statements." [1099]
- Usernames must be between 3 and 30 characters." [1100]
- Passwords must be at least 8 characters long." [1101]
- Onboarding requires rating 15 to 20 anime or manga titles." [1102]
- The dashboard displays recent activity, taste profile, recommendations, and statistics." [1103]
- Search allows filtering by type (anime or manga)." [1104]
- Import supports MyAnimeList, AniList, and Kitsu." [1105]
- The import process involves going to the Import page, selecting a platform, entering your username, clicking Connect, and starting the impor [1106]
- Ratings and lists are imported automatically." [1107]
- Profile visibility can be controlled." [1108]
- NomikaiList is an Anime & Manga Discovery Platform with AI-powered curation and multi-platform import capabilities." [1109]
- Backend prerequisites include Python 3.11+, uv, Node.js 18+, and a Supabase account." [1110]
- Backend dependencies are declared in pyproject.toml and pinned in uv.lock, with no requirements.txt shipped." [1111]
- The unified ingestion pipeline runs as one command `nomikai ingest run --mode batch|stream|refresh` orchestrating Phases A–D: populate → ext [1112]
- The backend framework is FastAPI 0.104.1." [1113]
- The database is PostgreSQL (Supabase)." [1114]
- Security vulnerabilities must be reported privately through GitHub's private vulnerability reporting rather than via a public issue." [1115]
- The project aims to remediate high/critical issues within 30 days and agrees a disclosure timeline with the reporter." [1116]
- Reporters who wish to be credited will be named." [1117]
- The NomikaiList backend API, frontend, and ingestion pipeline in this repository are in scope for vulnerability reports." [1118]
- Vulnerabilities in the third-party platforms Supabase, AniList, MyAnimeList, and Kitsu are out of scope and should be reported to the respec [1119]

---

[1] claim-alpaca-agents-alpaca-agents-agents-md-000 — The system is a multi-agent AI trading system designed for Alpaca Markets paper
[2] claim-alpaca-agents-alpaca-agents-agents-md-002 — All agents must operate on a shared `TradingState` object by mutating its fields
[3] claim-alpaca-agents-alpaca-agents-agents-md-003 — The module dependencies must flow unidirectionally from `src/models/` to `src/wo
[4] claim-alpaca-agents-alpaca-agents-agents-md-004 — CI runs unit tests using the command `uv run pytest tests/unit/` with specific f
[5] claim-alpaca-agents-alpaca-agents-agents-md-005 — The project requires approximately 58–59% coverage, with new code requiring 70%+
[6] claim-alpaca-agents-alpaca-agents-agents-md-006 — To ensure compliance with Spec §11.3, `langgraph` and `langgraph-checkpoint-post
[7] claim-alpaca-agents-alpaca-agents-claude-md-000 — All agents mutate a shared TradingState object, requiring field mutation rather
[8] claim-alpaca-agents-alpaca-agents-claude-md-001 — The system supports four agent patterns: ReAct, Direct, Hybrid, and Pure LLM."
[9] claim-alpaca-agents-alpaca-agents-claude-md-002 — The Synthesizer debate is triggered when the system reaches 60–95% confidence."
[10] claim-alpaca-agents-alpaca-agents-claude-md-003 — The maximum token budget per workflow is 50,000."
[11] claim-alpaca-agents-alpaca-agents-claude-md-005 — The quote interval for market data is 60 seconds."
[12] claim-alpaca-agents-alpaca-agents-claude-md-008 — The system includes 14 investor personas available for deliberation consultation
[13] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-000 — The system uses PostgreSQL with the pgvector extension to store and query high-d
[14] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-001 — The memory retrieval mechanism defaults to searching for the top 5 similar cases
[15] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-005 — The database connection utilizes asynchronous SQLAlchemy with specific pooling p
[16] claim-alpaca-agents-alpaca-agents-docs-architecture-memory-system-md-006 — The system tracks agent performance metrics, including analysis, outcomes, and a
[17] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-000 — The Alpaca Agents trading system utilizes a LangGraph-based workflow where speci
[18] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-001 — Technical and Sentiment Agents run in parallel after receiving input from the Re
[19] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-002 — Parallel execution of the Technical and Sentiment Agents achieves a 30-40% reduc
[20] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-005 — The final execution decision is controlled by a Conditional Router, requiring hu
[21] claim-alpaca-agents-alpaca-agents-docs-architecture-workflow-analysis-md-007 — The system employs a Shared State Accumulation Pattern where agents progressivel
[22] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-000 — The system operates as a pipeline using three distinct LangGraph instances."
[23] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-004 — The Execution Graph includes agents like `TechnicalAnalysisAgent`, `SentimentAge
[24] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-005 — Structured-output and reasoning nodes are assigned `qwen3:30b` via Ollama, offer
[25] claim-alpaca-agents-alpaca-agents-docs-autonomous-trading-system-coding-agent-specific-006 — FinBERT is inaccurate 83% of the time when applied to positive financial headlin
[26] claim-alpaca-agents-alpaca-agents-docs-changelog-md-000 — The system includes a market regime detection feature that identifies six distin
[27] claim-alpaca-agents-alpaca-agents-docs-changelog-md-002 — The backtesting framework supports historical testing over a period exceeding on
[28] claim-alpaca-agents-alpaca-agents-docs-changelog-md-003 — The system incorporates Monte Carlo simulation for the assessment of tail risk."
[29] claim-alpaca-agents-alpaca-agents-docs-changelog-md-004 — The system provides a template rendering performance constraint of less than 1 m
[30] claim-alpaca-agents-alpaca-agents-docs-changelog-md-005 — The system supports the generation of multiple report types upon workflow execut
[31] claim-alpaca-agents-alpaca-agents-docs-changelog-md-007 — The system migrated its database backend from SQLite to PostgreSQL with Timescal
[32] claim-alpaca-agents-alpaca-agents-docs-changelog-md-008 — The database schema was expanded to include dedicated tables for risk metrics, a
[33] claim-alpaca-agents-alpaca-agents-docs-changelog-md-009 — The chat interface supports streaming responses, allowing for token-by-token dis
[34] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-000 — The system requires Python 3.10 or newer for its implementation."
[35] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-001 — The system utilizes PostgreSQL 14 or newer as its database backend, with optiona
[36] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-002 — The Market Data Agent provides a detailed output structure including a recommend
[37] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-003 — The Sentiment Agent requires a symbol and a list of news items to perform sentim
[38] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-004 — The Backtest Agent provides quantitative performance metrics upon completion, in
[39] claim-alpaca-agents-alpaca-agents-docs-developer-manual-md-005 — A core design principle of the system is Modularity, ensuring that each agent is
[40] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-002 — The disagreement status in Round 1 was 77.5%."
[41] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-003 — The deliberation reached consensus in Round 2 with a disagreement score of 18.0%
[42] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-004 — Agent argument messages include confidence, round number, agent type, and analys
[43] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-005 — Deliberation messages can be retrieved from the chat_messages table using sessio
[44] claim-alpaca-agents-alpaca-agents-docs-examples-deliberation-streaming-md-006 — A complete deliberation episode can be exported by querying chat_messages filter
[45] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-000 — The initial Chat interface path executes 5 agents sequentially and takes approxi
[46] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-001 — The initial CLI path executes 11 agents using a full LangGraph workflow and take
[47] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-003 — The CLI path executes 11 agents, including specialized components like MarketReg
[48] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-005 — The streaming wrapper introduced in Phase 2 includes a chat mode optimization th
[49] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-006 — The refactored system allows Technical and Sentiment agents to run concurrently,
[50] claim-alpaca-agents-alpaca-agents-docs-features-chat-cli-parity-md-007 — The system fetches real-time portfolio context from Alpaca, including the portfo
[51] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-000 — The Agent Chat Interface includes specialized agents for various trading functio
[52] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-004 — The system provides a command-line interface for quick actions, including comman
[53] claim-alpaca-agents-alpaca-agents-docs-features-chat-interface-md-005 — The system utilizes a defined data flow pipeline where user input is processed t
[54] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-000 — The per-agent model selection is managed in `llm_routing.assignments` within `da
[55] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-003 — The Sentiment Agent should be upgraded to `anthropic/claude-3-5-sonnet` for supe
[56] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-004 — For live trading, the Portfolio Agent should be upgraded to `claude-3-opus` or `
[57] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-005 — The Cost-Optimized configuration averages a cost of $0.008 to $0.012 per analysi
[58] claim-alpaca-agents-alpaca-agents-docs-features-model-selection-guide-md-006 — The Live Trading configuration averages a cost of $0.04 to $0.08 per analysis."
[59] claim-alpaca-agents-alpaca-agents-docs-features-outcome-tracking-guide-md-006 — The system tracks the lowest and highest prices observed during the first 24 hou
[60] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-000 — The `fetch_news_articles` function fetches news articles based on specified stoc
[61] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-001 — The sentiment score generated by `analyze_news_sentiment` ranges from -100 to +1
[62] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-002 — The aggregation function allows weighting inputs from different sentiment source
[63] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-003 — Unusual activity detection accepts configurable thresholds for sentiment magnitu
[64] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-004 — The `analyze_options_flow_sentiment` function requires the underlying symbol, to
[65] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-005 — A combined sentiment score greater than 20 indicates an \"improving\" trend."
[66] claim-alpaca-agents-alpaca-agents-docs-features-sentiment-tools-guide-md-006 — A sentiment score between +50 and +20 indicates a \"Bullish\" sentiment."
[67] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-000 — The AgentExecutor used in the ReAct pattern has a maximum of 15 iterations and a
[68] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-001 — The ReAct pattern typically executes in 5 to 10 seconds, with tool calls taking
[69] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-002 — The ReAct pattern requires a high token usage, including approximately 500 token
[70] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-003 — The Direct Tool Invocation pattern typically executes in 1 to 3 seconds and uses
[71] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-004 — Direct Invocation is preferred when the workflow is deterministic and follows th
[72] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-005 — The ReAct pattern is appropriate when the workflow must adaptively decide which
[73] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-006 — A specific constraint of the ReAct pattern is the ability to skip indicators if
[74] claim-alpaca-agents-alpaca-agents-docs-features-tool-invocation-patterns-md-007 — Direct Invocation is used for fixed workflows, such as sentiment analysis or ris
[75] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-000 — The ReAct pattern requires the LLM to dynamically select tools and involves an i
[76] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-002 — The Hybrid pattern utilizes BaseToolAgent for deterministic calculations and emp
[77] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-003 — ReAct agents are slower than Direct Invocation agents because ReAct requires mor
[78] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-004 — Pure LLM Reasoning is used when the task is analysis, debate, or text generation
[79] claim-alpaca-agents-alpaca-agents-docs-guides-agent-patterns-md-005 — The 14 total agents are distributed across five categories: BaseReActAgent (2),
[80] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-001 — For robust validation, the backtesting framework recommends using at least one y
[81] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-002 — A specific backtest run starting with $10,000 resulted in a 24.50% total return.
[82] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-004 — In a specific A/B test, Configuration A achieved a higher Total Return (24.50%)
[83] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-005 — The Walk-Forward Optimization module allows users to define rolling window sizes
[84] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-006 — The optimization process can identify consensus parameters, such as `stop_loss_p
[85] claim-alpaca-agents-alpaca-agents-docs-guides-backtesting-guide-md-007 — The Monte Carlo Simulator is designed to run simulations using 1000 or more scen
[86] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-000 — The Trading Portfolio Dashboard is a custom web UI built on React and FastAPI, p
[87] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-001 — The dashboard can be launched by executing the command `uv run python main.py da
[88] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-002 — The system supports two modes of agent interaction: Sequential Mode, where agent
[89] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-003 — The Positions view displays detailed metrics including Symbol, Type, Quantity, A
[90] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-004 — The Risk Monitoring section tracks specific metrics such as Sharpe Ratio, Maximu
[91] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-005 — The system includes a Circuit Breaker feature that can be in an 'Inactive' state
[92] claim-alpaca-agents-alpaca-agents-docs-guides-dashboard-guide-md-007 — The dashboard allows users to set the data refresh interval via a slider ranging
[93] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-001 — The `challenge_round_enabled` flag is initially set to false."
[94] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-002 — The `dissenter_sampling_enabled` flag is initially set to false."
[95] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-003 — The `calibrated_weights_enabled` flag is initially set to false."
[96] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-006 — The maximum allowed increase in p95 wall time is 30.0 percent."
[97] claim-alpaca-agents-alpaca-agents-docs-guides-deliberation-experiments-workflow-md-008 — Each deliberation run records the enabled flags to `DeliberationData.active_expe
[98] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-000 — Live trading is disabled by default and requires deliberate human action to tran
[99] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-001 — Enabling live capital requires a human decision, separate live credentials, and
[100] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-003 — A second readiness criterion is achieving an agreement rate of 85% or higher in
[101] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-004 — A third readiness criterion is passing all WP-6 eval scorer-gate thresholds usin
[102] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-005 — Live mode requires setting `TRADING_MODE=live` in the k3s ConfigMap and using di
[103] claim-alpaca-agents-alpaca-agents-docs-guides-go-live-checklist-md-006 — Live trading can be disabled by reverting configuration settings or by using a k
[104] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-000 — All agent prompts and run metrics are consolidated in a single experiment on the
[105] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-001 — The system registers a total of 31 prompts across various categories, including
[106] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-002 — The prompt resolution process involves the agent returning a sentinel string, wh
[107] claim-alpaca-agents-alpaca-agents-docs-guides-mlflow-prompt-versioning-md-005 — The PromptResolver caches prompts for a configurable Time-To-Live (TTL), which d
[108] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-000 — The Model Optimizer automatically identifies underperforming models, recommends
[109] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-002 — An underperformer is defined by a win rate below 45%, low ROI, or cost exceeding
[110] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-003 — An overperformer is characterized by a win rate above 60%, high ROI, and consist
[111] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-004 — Aggressive trading strategies utilize a confidence threshold range of 65-70% to
[112] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-005 — Aggressive opportunity scoring uses a prediction accuracy range of 60-65%."
[113] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-006 — A minimum of 30 completed trades is required for reliable model analysis."
[114] claim-alpaca-agents-alpaca-agents-docs-guides-optimization-guide-md-007 — The CLI tool identifies models based on win rates below 45% or above 60%, and fl
[115] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-002 — The Position Manager runs before the Rebalancing Agent within the trading workfl
[116] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-003 — The Position Manager Agent allows setting a maximum loss percentage to force an
[117] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-004 — Profit protection can be configured to lock in a minimum percentage of gains."
[118] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-005 — The Rebalancing Agent supports triggering based on allocation drift, calendar in
[119] claim-alpaca-agents-alpaca-agents-docs-guides-position-management-md-006 — The Rebalancing Agent allows setting a maximum portfolio turnover percentage for
[120] claim-alpaca-agents-alpaca-agents-docs-guides-prompt-promotion-runbook-md-001 — Promotion to staging requires two conditions: 5+ market days of paper trading on
[121] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-000 — The `_init_llm()` method was identically duplicated across two classes, spanning
[122] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-002 — The `WorkflowExecutor` initializes with configuration, an optional auto-executio
[123] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-003 — The `_create_initial_state` method defaults the portfolio value and available ca
[124] claim-alpaca-agents-alpaca-agents-docs-guides-refactoring-guide-md-004 — The reporting service is designed to generate reports asynchronously and handle
[125] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-000 — The Enhanced Risk Monitoring system scans the portfolio at a configurable interv
[126] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-001 — The system provides real-time risk metrics including VaR, drawdown, volatility,
[127] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-005 — A prerequisite for the system is a running TimescaleDB instance, which must have
[128] claim-alpaca-agents-alpaca-agents-docs-guides-risk-monitoring-setup-md-006 — Email alerts require specific SMTP configuration details, such as using port 587
[129] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-000 — The overall code coverage target for the system is 85% or higher."
[130] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-001 — Deliberation agents require a minimum of 95% code coverage."
[131] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-002 — Trading agents require a minimum of 90% code coverage."
[132] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-003 — The `tests/unit/` directory is designated for fast, isolated tests."
[133] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-005 — A successful integration test run must produce a trade recommendation."
[134] claim-alpaca-agents-alpaca-agents-docs-guides-testing-quickstart-md-006 — When testing code that utilizes `AlpacaClient`, the mock must be configured to r
[135] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-002 — The default symbols analyzed during a run are BTC/USD, ETH/USD, AAPL, GOOGL."
[136] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-004 — The Balanced configuration targets an average latency of 20 to 40 seconds per an
[137] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-005 — The Balanced configuration targets a cost per analysis between $0.015 and $0.025
[138] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-006 — A 1-hour validation run can be executed by setting the duration parameter to 360
[139] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-007 — The execution reliability validation suggests monitoring the error rate to be le
[140] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-008 — The example output indicates that 48 calls were made to the Market Data agent du
[141] claim-alpaca-agents-alpaca-agents-docs-guides-validation-guide-md-009 — A high-frequency analysis run can be performed using 1-minute intervals and a 36
[142] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-002 — The `earnings_beat` catalyst type is assigned a specific evaluation window of 4
[143] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-003 — A bullish success is defined by the price movement percentage being greater than
[144] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-004 — The PriceMonitor background worker executes price snapshots for tracked opportun
[145] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-17-opportunity-lifecycl-005 — A high-priority notification is triggered if the adjusted score of an opportunit
[146] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-001 — The target size for `get_options_chain()` was less than 80 lines."
[147] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-alpaca-mcp-client-si-002 — The refactored `get_options_chain()` is approximately 70 lines."
[148] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-000 — The original `_state_to_responses()` method was approximately 270 lines long and
[149] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-001 — The `_extract_symbol()` method previously contained a 95-word `excluded_words` s
[150] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-002 — The refactored `_state_to_responses()` method is now approximately 50 lines long
[151] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-003 — The refactoring introduced 7 focused response builder methods."
[152] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-004 — The intent detection mechanism (`_detect_intent()`) was updated to use an extern
[153] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-005 — The symbol extraction mechanism (`_extract_symbol()`) now uses an externalized `
[154] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-chat-manager-simplif-006 — The project added 22 new unit tests specifically for the extracted helper method
[155] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-000 — The original `_execute()` method contained 275 lines of code and a complexity of
[156] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-001 — The exception handlers contained 5 instances of duplicated Order construction co
[157] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-002 — The refactored `_execute()` method is targeted to be approximately 120 lines."
[158] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-003 — The `_apply_session_restrictions()` method extracts the extended hours order typ
[159] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-004 — The `_create_rejected_order()` method eliminates the duplicated Order constructi
[160] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-005 — The `_build_order_params()` method extracts the logic for building order paramet
[161] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-execution-agent-simp-006 — A key acceptance criterion is that the `_execute()` method must be reduced to le
[162] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-000 — The original `_execute()` function was approximately 230 lines long and had a co
[163] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-001 — The original `_synthesize_options_recommendation()` function was approximately 2
[164] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-002 — The refactoring successfully eliminated approximately 150 lines of duplication."
[165] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-003 — After refactoring, the `_execute()` function is approximately 120 lines."
[166] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-004 — After refactoring, the `_synthesize_options_recommendation()` function is approx
[167] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-005 — Options trade direction determination was simplified using a signal lookup mecha
[168] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-portfolio-agent-simp-006 — The project includes 13 existing tests and 21 new unit tests for the extracted h
[169] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-001 — The original `_assess_options_risk()` method was approximately 280 lines long an
[170] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-002 — The refactored `_execute()` method is targeted to be less than 230 lines."
[171] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-003 — The refactoring introduced 4 shared helper methods to eliminate duplication."
[172] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-004 — The `_calculate_average_confidence()` method consolidates duplicated confidence
[173] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-005 — The `_apply_calibration_adjustments()` method consolidates calibration logic fro
[174] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-007 — The `_apply_session_adjustments()` method extracts a 60-line session adjustment
[175] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-18-risk-agent-simplific-008 — The refactored `_execute()` method utilizes specific helper methods for its sequ
[176] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-001 — The new system checks for recent analysis before running a full workflow and ret
[177] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-002 — The default TTL for stock analysis is 15 minutes."
[178] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-003 — The default TTL for crypto analysis is 5 minutes."
[179] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-19-analysis-cache-desig-006 — When a cached analysis is successfully retrieved and served, the API response st
[180] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-000 — A TradeIntention must include fields for strategy ID, symbol, direction, convict
[181] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-002 — Graduation of a strategy requires meeting specific performance thresholds: a min
[182] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-003 — The lifecycle stage of a strategy determines its capital allocation: Paper uses
[183] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-orche-006 — The SharedAnalysisState mechanism allows for the detection of stale data by chec
[184] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-006 — The `ObservationBuilder` converts `SharedAnalysisState` into normalized numpy ar
[185] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-20-multi-strategy-phase-007 — The system defines four possible market regime categories: bullish, bearish, sid
[186] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-000 — Routing to deliberation occurs when the Arbiter detects HIGH severity conflicts,
[187] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-001 — Phase 4 implements three key features: wiring deliberation into the arbiter, per
[188] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-002 — The system converts a strategy's intention conviction (0-1 scale) into a recomme
[189] claim-alpaca-agents-alpaca-agents-docs-plans-completed-2026-01-21-multi-strategy-phase-005 — Deliberation is skipped if the conflict severity is LOW or NONE, provided the Ar
[190] claim-alpaca-agents-alpaca-agents-docs-proposals-013-agentic-dashboard-md-000 — The Alpaca Agents system comprises three distinct operational components: Analys
[191] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-000 — The migration to TA-Lib is structured into sequential and parallel stories, with
[192] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-003 — The technical indicators are configurable via `settings.yaml`, allowing per-asse
[193] claim-alpaca-agents-alpaca-agents-docs-proposals-015-indicator-library-evaluation-md-004 — The installation of TA-Lib requires installing the C library and the Python wrap
[194] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-000 — The current system uses a linear workflow where agents work independently withou
[195] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-003 — The Bearish Researcher Agent plays devil's advocate by identifying risks, highli
[196] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-004 — The Synthesizer Agent moderates the debate and produces a final balanced recomme
[197] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-005 — The new workflow routes analysis from the Risk Agent to both Bullish and Bearish
[198] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-006 — The implementation of the deliberation phase adds 5-10 seconds of latency per tr
[199] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-deliberation-enha-007 — The hypothesis is that the deliberation phase improves the expected win rate by
[200] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-001 — The memory system architecture consists of a Vector Database storing embeddings
[201] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-002 — An Analysis Record must capture the technical signal, sentiment score, risk asse
[202] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-003 — The Outcome Record tracks various execution and outcome metrics, including exit
[203] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-004 — The system configuration allows setting the number of similar past cases retriev
[204] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-006 — The `double_bottom` technical pattern demonstrated a 72% win rate and 2.1 averag
[205] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-001-agent-memory-learning-s-007 — Trades incorporating deliberation showed a 71% win rate, compared to 64% for tra
[206] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-000 — The current deliberation system operates on a single-round approach."
[207] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-001 — The system allows setting a maximum number of debate rounds for the deliberation
[208] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-002-multi-round-deliberatio-005 — Using early termination is a mitigation strategy against high computational cost
[209] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-000 — The total current test coverage across all agents and workflows is 62%."
[210] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-001 — The BullishResearcher agent has 0% test coverage."
[211] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-002 — The target coverage goal for the testing suite is 85% or higher."
[212] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-003 — The RiskAgent module has 85% test coverage."
[213] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-003-comprehensive-testing-s-005 — A standard initial trading workflow state includes a portfolio value and availab
[214] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-002 — The proposed solution is to implement automated report generation for individual
[215] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-004 — The system configuration allows setting an output directory for reports and defi
[216] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-004-agent-report-generation-006 — The example trade involved setting a stop-loss at $175.20 (4.8% downside) and a
[217] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-000 — A warning alert is triggered if the drawdown exceeds 15%, and a critical alert i
[218] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-001 — An alert is triggered if the Value at Risk (VaR) increases by more than 50% with
[219] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-002 — An alert is triggered if the correlation between positions exceeds 0.8."
[220] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-003 — An alert is triggered if a single position accounts for more than 35% of the tot
[221] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-004 — Trading is automatically halted if the drawdown reaches the predefined maximum d
[222] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-005 — Trading is automatically halted if there are three consecutive losing trades, ea
[223] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-007 — The implementation timeline for the enhanced risk monitoring system is six weeks
[224] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-005-enhanced-risk-monitorin-008 — The monitoring infrastructure requires a monthly cost of $50."
[225] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-000 — The TechnicalAgent's buy signals have a 68% profitability rate."
[226] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-002 — The average contribution of the TechnicalAgent to profit is +$42 per trade."
[227] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-004 — Claude-3-5-sonnet provides 72% accuracy at a cost of $0.004 per trade."
[228] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-006-agent-performance-analy-007 — The implementation timeline for the analytics system is estimated at 5 weeks."
[229] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-000 — The Interactive Deliberation Viewer was completed on October 18, 2025."
[230] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-001 — The system features a two-column layout displaying the Bullish and Bearish cases
[231] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-007-interactive-deliberatio-002 — The viewer is integrated into the dashboard navigation and utilizes a custom web
[232] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-002 — High volatility (crisis) is defined by VIX above 30, daily moves exceeding 2%, a
[233] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-003 — In a bull market, the proposed strategy is to increase position sizes by 20% and
[234] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-004 — In a bear market, the proposed strategy is to reduce position sizes by 30% and f
[235] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-005 — During high volatility, the proposed strategy is to reduce position sizes by 50%
[236] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-008-market-regime-detection-006 — The implementation of the regime detection system is estimated to take 6 weeks a
[237] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-000 — The initial backtest run achieved a Total Return of 24.5%, a Sharpe Ratio of 1.8
[238] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-001 — The strategy incorporating deliberation achieved a higher Sharpe Ratio (1.82) an
[239] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-002 — The walk-forward optimization process identified new parameters (e.g., min_confi
[240] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-003 — A Monte Carlo simulation of 1000 possible futures indicated a median 1-year retu
[241] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-004 — The backtesting framework allows for realistic simulation of transaction costs,
[242] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-009-backtesting-framework-e-005 — The backtesting framework is structured into dedicated modules for the main engi
[243] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-000 — The BUY decision for AAPL was primarily driven by Technical Signal (35%), Sentim
[244] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-002 — The final confidence of 72% was achieved through contributions including Technic
[245] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-010-explainability-interpre-004 — The final confidence of 72% is calculated as a weighted average of components, i
[246] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-012-investor-persona-system-004 — The initial implementation includes five specific personas: Buffett, Munger, Dal
[247] claim-alpaca-agents-alpaca-agents-docs-proposals-completed-012-investor-persona-system-006 — The `WarrenBuffettPersona` class inherits functionality from `BaseBullishPersona
[248] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-001 — The system has two proposals currently under consideration or in progress."
[249] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-002 — The target Sharpe Ratio for the system is 2.0 or higher, up from a current avera
[250] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-003 — The target Win Rate for the system is 70% or higher, up from a current average o
[251] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-004 — The maximum acceptable drawdown constraint is less than 15%."
[252] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-006 — The CI/CD pipeline requires a build time of less than 5 minutes."
[253] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-007 — Proposal 003 (Comprehensive Testing Suite) involved establishing a testing infra
[254] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-008 — Proposal 005 (Enhanced Risk Monitoring) includes a 24/7 monitoring service, emai
[255] claim-alpaca-agents-alpaca-agents-docs-proposals-readme-md-009 — Proposal 006 (Agent Performance Analytics) provides a learning analytics dashboa
[256] claim-alpaca-agents-alpaca-agents-docs-readme-md-000 — The Alpaca Agents system is a production-ready multi-agent AI trading system."
[257] claim-alpaca-agents-alpaca-agents-docs-readme-md-002 — The Memory System utilizes pgvector semantic memory combined with sentence-trans
[258] claim-alpaca-agents-alpaca-agents-docs-readme-md-003 — The system incorporates LangGraph for deliberation workflow analysis."
[259] claim-alpaca-agents-alpaca-agents-docs-readme-md-004 — Multi-Agent Trading is a production feature."
[260] claim-alpaca-agents-alpaca-agents-docs-readme-md-005 — Risk Monitoring is a production feature."
[261] claim-alpaca-agents-alpaca-agents-docs-readme-md-006 — Backtesting is a production feature."
[262] claim-alpaca-agents-alpaca-agents-docs-readme-md-007 — Database setup requires PostgreSQL/TimescaleDB configuration."
[263] claim-alpaca-agents-alpaca-agents-docs-readme-md-008 — Docker setup provides an alternative installation method."
[264] claim-alpaca-agents-alpaca-agents-docs-roadmap-md-004 — Multi-timeframe confirmation functionality has been enabled."
[265] claim-alpaca-agents-alpaca-agents-docs-roadmap-md-005 — The system successfully incorporated breaking news into sentiment analysis."
[266] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-000 — The trading system utilizes PostgreSQL with TimescaleDB for managing portfolio t
[267] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-001 — The core tables—trades, portfolio_snapshots, and performance_metrics—are convert
[268] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-002 — The specific partitioning keys for the time-series tables are defined as follows
[269] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-005 — Automatic compression provides a storage efficiency benefit of over 90% on histo
[270] claim-alpaca-agents-alpaca-agents-docs-setup-database-setup-md-006 — For high-concurrency production deployments, Pgbouncer is configured with a defa
[271] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-000 — The database is accessible via localhost on port 5432, using the 'trading' datab
[272] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-001 — The application requires specific environment variables to connect to the Postgr
[273] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-002 — To connect to the database using pgAdmin, the host is 'timescaledb' (within the
[274] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-003 — The database can be started using the script `./scripts/db_start.sh`."
[275] claim-alpaca-agents-alpaca-agents-docs-setup-docker-setup-md-004 — The database can be stopped using the script `./scripts/db_stop.sh`."
[276] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-000 — Ruff serves as a unified linter, replacing flake8, isort, and pylint."
[277] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-001 — Bandit is a security scanner that identifies common vulnerabilities, including h
[278] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-002 — detect-secrets prevents the accidental commitment of sensitive information such
[279] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-003 — The `pytest-unit` hook runs fast unit tests in approximately 5 to 10 seconds."
[280] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-004 — Black is a code formatter that enforces consistent Python code formatting and ca
[281] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-005 — The file integrity checks include removing trailing whitespace, ensuring files e
[282] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-006 — mypy performs static type checking for Python code."
[283] claim-alpaca-agents-alpaca-agents-docs-setup-pre-commit-hooks-md-007 — Running all hooks on all files can take approximately 30 seconds."
[284] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-000 — uv-secure scans dependencies for known security vulnerabilities by checking the
[285] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-001 — When used as a pre-commit hook, uv-secure requires manual execution because it i
[286] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-002 — The scan can be restricted to only checking direct dependencies."
[287] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-003 — A full scan of 197 dependencies can take between 3 and 5 minutes."
[288] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-004 — When vulnerabilities are found, the report includes the package name, vulnerabil
[289] claim-alpaca-agents-alpaca-agents-docs-setup-uv-secure-md-005 — uv-secure is skipped by default in CI environments."
[290] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-000 — The system requires Python 3.10 or higher and PostgreSQL 14+ for installation."
[291] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-001 — Operation requires accounts for Alpaca, OpenRouter, and Finnhub."
[292] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-002 — The database utilizes a TimescaleDB container for operation."
[293] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-003 — The default base URL for Alpaca paper trading is specified."
[294] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-004 — The default stop loss percentage is configurable at 5.0%."
[295] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-005 — The default take profit percentage is configurable at 10.0%."
[296] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-006 — The system checks for news using a configurable interval of 300 seconds."
[297] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-008 — Backtesting can be triggered by low confidence, conflicting signals, or high vol
[298] claim-alpaca-agents-alpaca-agents-docs-user-manual-md-009 — Autonomous trading execution is controlled by the `auto_execute` setting, which
[299] claim-alpaca-agents-alpaca-agents-readme-md-000 — The system is a multi-agent AI trading system designed for Alpaca Markets, incor
[300] claim-alpaca-agents-alpaca-agents-readme-md-001 — The system includes 7 specialized AI agents, each with a specific defined purpos
[301] claim-alpaca-agents-alpaca-agents-readme-md-002 — The system provides comprehensive testing, including over 4000 passing tests and
[302] claim-alpaca-agents-alpaca-agents-readme-md-003 — The system's analysis of a security typically takes between 18 and 37 seconds an
[303] claim-alpaca-agents-alpaca-agents-readme-md-005 — The system integrates real-time market data from Alpaca and IEX feeds, covering
[304] claim-alpaca-agents-alpaca-agents-readme-md-007 — Local setup of the system can be achieved in approximately 30 seconds using the
[305] claim-aperiodic-chats-2026-09-06-chat-error-res-godot-world-preview-3d-gd-102-parse-er-000 — Godot reported a parse error at res://godot/world_preview_3d.gd:102: Could not r
[306] claim-aperiodic-chats-2026-09-06-chat-error-res-godot-world-preview-3d-gd-102-parse-er-001 — Godot reported an invalid call at res://addons/world_forge/inspector_plugin.gd:1
[307] claim-aperiodic-chats-2026-09-06-chat-error-res-godot-world-preview-3d-gd-102-parse-er-002 — The root cause was core/world_seed.gd missing two members, causing a cascade of
[308] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-001 — ChunkKey.from_world() computes chunk coordinates using floori(float(w)/CHUNK_SIZ
[309] claim-aperiodic-chats-2026-09-07-chat-explore-the-godot-project-at-users-johnd-develop-007 — ChunkView sets scale to Vector3.ONE * voxel_size and position to Vector3(origin)
[310] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--000 — The project is a Godot project containing project.godot and 46 .gd scripts."
[311] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--001 — Godot 4.7.2 is installed on the machine."
[312] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--002 — GDScript's LSP is not one of opencode's built-ins, so it requires a custom LSP e
[313] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--003 — Godot's LSP is a TCP server listening on port 6005."
[314] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--005 — The running Godot editor has the GDScript LSP live on 127.0.0.1:6005."
[315] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--006 — The bridge test failed because piping closes stdin instantly, causing the bridge
[316] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--008 — A .opencode/godot-lsp-bridge.js stdio↔TCP bridge was created because Godot's LSP
[317] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--009 — The GDScript LSP only runs while the Godot editor is open, so opencode's LSP con
[318] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--010 — Context7 works keyless at default rate limits, and higher limits require an API
[319] claim-aperiodic-chats-2026-09-07-chat-help-me-configure-lsps-for-this-project-and-add--011 — opencode does not hot-reload its config, so it must be quit and restarted for th
[320] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--000 — The mesher reads interior cells from raw ChunkData (baseline only) while edits l
[321] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--003 — EditOverlay stores edits in a sparse Dictionary keyed by Vector3i world cell to
[322] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-project-godot-4-7--006 — Chunk manager spawn budget is 2 per frame, scaled down by maxi(1, roundi(2/vs²))
[323] claim-aperiodic-chats-2026-09-07-chat-research-task-no-code-changes-the-project-is-a-g-010 — The aperiodic terrain generator disabled ruins rather than retheming them."
[324] claim-aperiodic-chats-2026-09-07-chat-the-chuncks-are-rendering-seperated-from-one-ano-006 — Measured: 182/2787 tree cells mismatch."
[325] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-000 — The aperiodic project had 17 open GitHub issues, with Tier 1 issues #1, #2, and
[326] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-001 — Issue #11 is a tier-1 release-build threading benchmark that validates the use_t
[327] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-002 — Issue #4 (Texture2DArray) fixes mip bleeding visual artifacts and is a hard prer
[328] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-005 — No Godot export templates were installed on the machine, which the release-build
[329] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-006 — The generated_count counter is only incremented on the threaded spawn path (chun
[330] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-the-github-issues-and-prioritize-w-010 — Symlinking the addon directory caused Godot to see the addon twice, producing du
[331] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-000 — The hybridindie/godot-mcp repository had 20 open issues at the time of the sessi
[332] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-001 — Issue #422 is a high-priority silent failure in which deleting a .tscn file leav
[333] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-002 — Issue #414 is a high-priority silent failure in which set_node_property with a r
[334] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-003 — Issue #413 is a high-priority silent failure in which navigation_bake_mesh retur
[335] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-004 — Issue #411 is a high-priority silent failure in which the debugger traps the gam
[336] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-005 — Issue #416 is a medium bug where frame-dependent commands hang and timeout_ms is
[337] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-007 — The previously merged batch #433–436 fixed issues #409, #410, #412, #420, and #4
[338] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-008 — The recommended next batch consists of the four priority:high silent-failure bug
[339] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-009 — The navigation e2e test bakes an empty navmesh and asserts baked:true, which is
[340] claim-aperiodic-chats-2026-09-08-chat-let-s-look-at-what-the-next-group-of-issues-shou-010 — A red test for issue #414 reproduced the exact silent no-op, returning set:true
[341] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-000 — The engine is built on Godot 4.7, uses GDScript only (no GDExtension/C++), and t
[342] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-001 — Chunks are 16³ blocks stored in a PackedInt32Array flat storage with no palette
[343] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-003 — Meshing is naive per-face culled with no greedy meshing, uses per-face UVs into
[344] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-004 — Collision uses one ConcavePolygonShape3D trimesh per chunk, rebuilt wholesale on
[345] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-007 — The engine has no LOD, no frustum culling beyond Godot default, no occlusion cul
[346] claim-aperiodic-chats-2026-09-08-chat-research-task-web-based-no-code-changes-i-m-audi-008 — Zylann's GodotVoxel module is built around a worker pool for meshing/saving, wit
[347] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-004 — Seed 12345 is a land world with ground at the spawn column y=7 and sea=-2."
[348] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-006 — Headless screenshots are not usable because the dummy renderer hands back null t
[349] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-007 — On clean main, a headless probe places the player at (8.5, 8.9, 8.5), eye at (8.
[350] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-008 — test_spawn.gd and test_mesher.gd pass with 0 failed."
[351] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-009 — Clean main also has the _apply_mesh on freed-object error in test_threading.gd,
[352] claim-aperiodic-chats-2026-09-10-chat-we-are-addressing-the-issues-with-spawning-insid-010 — On clean main, in the windowed run the player at (8.5, 8.9, 8.5) is 0.1 m into t
[353] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-000 — The next work item is #5 (greedy meshing), the head of the tier-2 queue."
[354] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-003 — test_render_smoke.gd:49 calls look_at before add_child, logging \"Node not insid
[355] claim-aperiodic-chats-2026-09-10-chat-what-is-the-next-item-we-should-work-on-md-004 — #5 greedy meshing is the only open story of epic #28 and is unblocked because th
[356] claim-aperiodic-chats-2026-09-12-chat-research-task-read-only-no-code-changes-in-users-001 — ChunkData stores blocks in a dense PackedInt32Array(4096) indexed as x + y*n + z
[357] claim-aperiodic-chats-2026-09-12-chat-research-task-read-only-no-code-changes-in-users-011 — FluidSim's _NEIGHBORS and _SIDE_NEIGHBORS are constant lists, gravity is a disti
[358] claim-aperiodic-chats-2026-09-12-chat-research-task-web-research-no-code-changes-topic-003 — In 0fps' culled meshing, culled meshing produces roughly 16× fewer quads than na
[359] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-000 — 15 monohedral convex pentagon tiling families are known, with attribution spanni
[360] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-002 — The Cairo pentagonal tiling is the type 4 family, defined by two non-adjacent 90
[361] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-003 — The snub-square-dual Cairo form has angles 120°, 120°, 90°, 120°, 90° and side r
[362] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-004 — The Cairo pentagonal tiling has 5 edge-neighbors per tile and is edge-to-edge an
[363] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-005 — In the truncated square tiling (4.8.8), each octagon has 4 octagon neighbors on
[364] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-006 — The truncated square tiling is the truncation of the square tiling at every vert
[365] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-007 — The 11 convex uniform (Archimedean) tilings comprise 3 regular and 8 semiregular
[366] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-008 — In the truncated triangular tiling (3.12.12), each dodecagon has 6 dodecagon nei
[367] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-context-a-godo-010 — Cairo is the dual of the snub square tiling, whose wallpaper group is p4g, a 4-f
[368] claim-aperiodic-chats-2026-09-12-chat-web-research-task-no-code-changes-research-only--010 — BorisTheBrave 'Triangle Grids': triangles are always planar with per-vertex heig
[369] claim-godot-agents-godot-agents-agents-md-000 — The `godot-agents` repository functions as the orchestrator/client, depending on
[370] claim-godot-agents-godot-agents-agents-md-001 — The `godot-agents` system is tightly coupled to the specific `godot-mcp` server
[371] claim-godot-agents-godot-agents-agents-md-003 — For `godot-mcp` versions 2026.08.31b4 and later, toolset enablement is server-gl
[372] claim-godot-agents-godot-agents-agents-md-004 — The default transport mechanism is stdio, requiring the `godot-mcp` CLI to be re
[373] claim-godot-agents-godot-agents-agents-md-005 — Since version 2026.08.31b4, `godot-mcp` emits a structured payload, which the cl
[374] claim-godot-agents-godot-agents-agents-md-006 — The build/verify/fix loop is capped by a default of 3 retries and a recursion li
[375] claim-godot-agents-godot-agents-docs-configuration-md-000 — All configuration must be done via environment variables, as there is no configu
[376] claim-godot-agents-godot-agents-docs-configuration-md-001 — The default transport mechanism for MCP is `stdio`."
[377] claim-godot-agents-godot-agents-docs-configuration-md-002 — The default port for HTTP transport is 9090."
[378] claim-godot-agents-godot-agents-docs-configuration-md-003 — Web search is disabled by default, requiring explicit opt-in to enable the retri
[379] claim-godot-agents-godot-agents-docs-configuration-md-004 — The experimental fluid executor is disabled by default, requiring explicit opt-i
[380] claim-godot-agents-godot-agents-docs-configuration-md-005 — Setting the MLflow tracking URI enables tracing and evaluation logging for the a
[381] claim-godot-agents-godot-agents-docs-configuration-md-007 — The agent verifier can be instructed to run the project's existing GUT test suit
[382] claim-godot-agents-godot-agents-docs-eval-fluid-ab-runbook-md-003 — Live mode execution, which provides the authoritative pass-rate, requires specif
[383] claim-godot-agents-godot-agents-docs-eval-live-md-001 — The execution flow involves the planner, executor, and verifier interacting with
[384] claim-godot-agents-godot-agents-docs-gle-calibration-md-001 — The live calibration run requires a running Godot editor and the `godot_mcp` bri
[385] claim-godot-agents-godot-agents-docs-observability-md-001 — Logging is controlled by setting the `MLFLOW_TRACKING_URI` environment variable,
[386] claim-godot-agents-godot-agents-docs-prd-md-000 — The Godot-native AI development platform is composed of three distinct layers: a
[387] claim-godot-agents-godot-agents-docs-prd-md-001 — The Godot addon and bridge holds direct authority over the live Godot editor sta
[388] claim-godot-agents-godot-agents-docs-prd-md-002 — The FastMCP server acts as the typed capability surface between the agent and Go
[389] claim-godot-agents-godot-agents-docs-prd-md-003 — The agent system provides the policy and orchestration layer, managing planning,
[390] claim-godot-agents-godot-agents-docs-prd-md-004 — The v1 implementation uses a LangGraph StateGraph architecture where nodes opera
[391] claim-godot-agents-godot-agents-docs-prd-md-005 — The execution policy mandates that the MCP is the primary substrate for Godot wo
[392] claim-godot-agents-godot-agents-docs-setup-md-000 — Python 3.13 or newer is required for the setup."
[393] claim-godot-agents-godot-agents-docs-setup-md-001 — The `godot-mcp` server is a standalone project, distinct from the agent's depend
[394] claim-godot-agents-godot-agents-docs-setup-md-002 — In service mode, a single `godot-mcp` HTTP service manages the editor bridge, pr
[395] claim-godot-agents-godot-agents-docs-setup-md-003 — Godot version 4.4 or newer is required for live runs with the `godot_mcp` addon
[396] claim-godot-agents-godot-agents-docs-setup-md-004 — Ollama defaults to listening on `http://127.0.0.1:11434`, unless overridden by `
[397] claim-godot-agents-godot-agents-docs-setup-md-005 — MLflow tracing is optional; setting `MLFLOW_TRACKING_URI` enables logging, other
[398] claim-godot-agents-godot-agents-readme-md-000 — The agent is a self-improving, local-first LangGraph agent for AI-driven Godot d
[399] claim-godot-agents-godot-agents-readme-md-001 — The agent uses a LangGraph StateGraph composed of 14 nodes to manage the build →
[400] claim-godot-agents-godot-agents-readme-md-004 — Tracing to MLflow is conditional on setting the `MLFLOW_TRACKING_URI` environmen
[401] claim-godot-agents-godot-agents-readme-md-005 — The system requires Python 3.13+ and includes an 80% coverage gate in its CI wor
[402] claim-godot-agents-godot-agents-readme-md-006 — The default WebSocket server binds to `127.0.0.1` on port `9070`."
[403] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-001 — PR #439 (Refuse zero-polygon navigation bakes) has all green CI and no review ye
[404] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-002 — PR #442 (Enforce local ollama-only graphify backend) has a CI failure in ruff."
[405] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-003 — PR #438 (Fix Object property coercion + null-write) has CI failures in e2e and m
[406] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-008 — PR #442 has a real lint error: E501 line too long at scripts/graphify_gdscript_s
[407] claim-godot-mcp-chats-2026-09-08-chat-let-s-address-the-open-prs-on-this-repo-there-is-011 — Qodo found a real bug in PR #440 where EditorInterface.close_scene() closes the
[408] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-001 — EditorInterface in Godot 4.7 exposes exactly 17 methods whose names contain \"sc
[409] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-002 — The only scene-closing method is Error close_scene(), which takes zero parameter
[410] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-005 — open_scene_from_path opens the scene at the given path and creates a new inherit
[411] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-006 — reload_scene_from_path fails if the scene is not open."
[412] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-007 — get_open_scenes() and get_open_scene_roots() list all open scenes, but the activ
[413] claim-godot-mcp-chats-2026-09-08-chat-read-the-file-users-johnd-local-share-opencode-t-008 — The Godot 4.7 EditorInterface page has no Signals section, containing only Descr
[414] claim-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-000 — The `.opencode/plugins/graphify.js` plugin was rewritten to port graphify's full
[415] claim-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-001 — The search guard fires on executed tokens with heredoc bodies and quoted spans s
[416] claim-godot-mcp-chats-2026-09-16-chat-graphify-has-hooks-for-harnesses-like-claude-let-006 — The plugin fails open everywhere: any error results in no nudge and never a bloc
[417] claim-godot-mcp-git-issue-484-md-000 — The reporter tested the setup with Godot 4.7.0, Godot MCP version 2026.09.10, on
[418] claim-godot-mcp-git-issue-484-md-003 — The MCP server URL is entered as http://<IP or resolvable name>:<port>/mcp with
[419] claim-godot-mcp-git-issue-484-md-010 — The tool-name prefix is OpenWebUI's integration-ID namespacing rather than a ser
[420] claim-godot-mcp-git-issue-485-md-000 — After calling godot_enable_toolset for any gated toolset, the tools appear in go
[421] claim-godot-mcp-git-issue-485-md-002 — godot_enable_toolset() mutates the server-global enabled set in mcp_server/tools
[422] claim-godot-mcp-git-issue-485-md-004 — FastMCP 4.0.1 has no server-side send_tools_list_changed helper, but the MCP SDK
[423] claim-godot-mcp-git-issue-485-md-005 — All 162 addon cmd_* handlers exist and match mcp_server/command_map.py."
[424] claim-godot-mcp-git-issue-485-md-008 — The server-side fix emitting notifications/tools/list_changed after enable_tools
[425] claim-godot-mcp-git-issue-485-md-009 — The root cause of the issue is claimed to be an OpenCode client bug rather than
[426] claim-godot-mcp-git-issue-485-md-011 — The issue was closed via PR #491 with the server-side fix implemented."
[427] claim-godot-mcp-git-issue-486-md-000 — Issue #486 is in CLOSED state."
[428] claim-godot-mcp-git-issue-486-md-001 — When .tscn or .gd files are edited externally, the Godot editor does not detect
[429] claim-godot-mcp-git-issue-486-md-002 — The user must manually close and reopen scenes, or restart the editor entirely,
[430] claim-godot-mcp-git-issue-486-md-003 — No cmd_scan, cmd_refresh, or cmd_reimport handler exists in the addon."
[431] claim-godot-mcp-git-issue-486-md-004 — The addon only calls update_file() after its own writes."
[432] claim-godot-mcp-git-issue-486-md-006 — Nothing reimports externally-edited .gd files or refreshes the filesystem on dem
[433] claim-godot-mcp-git-issue-486-md-007 — The proposed fix is to add a non-destructive cmd_rescan_filesystem handler that
[434] claim-godot-mcp-git-issue-487-md-000 — Issue #487 is in CLOSED state."
[435] claim-godot-mcp-git-issue-487-md-001 — When the same PackedScene is instanced twice, property overrides on the second i
[436] claim-godot-mcp-git-issue-487-md-003 — No tool can enable Editable Children."
[437] claim-godot-mcp-git-issue-487-md-004 — The tree inspector emits no owner/editable-instance metadata, so agents cannot d
[438] claim-godot-mcp-git-issue-487-md-005 — _cmd_instance_scene calls packed.instantiate(GEN_EDIT_STATE_INSTANCE) but never
[439] claim-godot-mcp-git-issue-487-md-006 — scene_inspect.gd traverses with un-owner-filtered node.get_children() and emits
[440] claim-godot-mcp-git-issue-487-md-007 — Node.set_editable_instance(node, is_editable) is the API that would fix the issu
[441] claim-godot-mcp-git-issue-487-md-008 — Proposed fix: add a cmd_set_editable_children handler plus a corresponding mutat
[442] claim-godot-mcp-git-issue-487-md-009 — Proposed fix: include owner and is_editable_instance metadata in serialize_tree
[443] claim-godot-mcp-git-issue-487-md-010 — Proposed fix: consider auto-enabling editable children when an agent creates a s
[444] claim-godot-mcp-git-issue-488-md-000 — Every session requires calling three tools before any work can begin."
[445] claim-godot-mcp-git-issue-488-md-003 — Because of the missing notification, an agent that enables a toolset and tries t
[446] claim-godot-mcp-git-issue-488-md-004 — One proposed option is to fix issue #1 first by emitting the notification so ena
[447] claim-godot-mcp-git-issue-488-md-005 — A GODOT_MCP_DEFAULT_TOOLSETS mechanism partially exists to let users pre-enable
[448] claim-godot-mcp-git-issue-488-md-007 — A proposed option is a single godot_bootstrap(toolsets=[...]) call that returns
[449] claim-godot-mcp-git-issue-488-md-008 — The issue was closed on the grounds that the mandatory 3-tool discovery protocol
[450] claim-godot-mcp-git-issue-489-md-001 — Referencing `$\"Soldier/AnimationPlayer\"` from a script resolves the path succe
[451] claim-godot-mcp-git-issue-489-md-004 — The reported failure is a downstream symptom of Issue #3 (instanced scene overri
[452] claim-godot-mcp-git-issue-489-md-005 — When an instance fails to load due to the editable-children gap, nodes beneath i
[453] claim-godot-mcp-git-issue-489-md-007 — The issue was fixed by fixing Issue #3, adding a `set_editable_children` tool pl
[454] claim-godot-mcp-git-issue-489-md-008 — The closing comment by MuhamadBarzani attributes the issue to #487 (instanced sc
[455] claim-godot-mcp-git-issue-489-md-009 — Per the closing comment, AnimationPlayer path resolution works correctly when th
[456] claim-godot-mcp-git-issue-520-md-000 — MCPBridge._pending_times (mcp_bridge.gd:39) is read and erased in _handle_text()
[457] claim-godot-mcp-git-issue-520-md-008 — An acceptance criterion is that latency_ms reported be either real round-trip wi
[458] claim-godot-mcp-git-issue-520-md-010 — Issue #520 is in state OPEN."
[459] claim-godot-mcp-git-issue-521-md-000 — `MCPPlugin._server_version` is declared at godot_mcp.gd:36 and read by `_server_
[460] claim-godot-mcp-git-issue-521-md-001 — A code comment claims the server version is populated when the bridge connects v
[461] claim-godot-mcp-git-issue-521-md-002 — The dock's version label can only ever show \"Godot x.y.z\" and never the server
[462] claim-godot-mcp-git-issue-521-md-003 — Issue #521 is in state CLOSED."
[463] claim-godot-mcp-git-issue-521-md-004 — Issue #521 carries the labels bug and component:addon."
[464] claim-godot-mcp-git-issue-521-md-005 — The proposed fix is to add a `cmd_get_addon_info` handshake and have the server
[465] claim-godot-mcp-git-issue-521-md-006 — `_server_version` should be assigned from the handshake so the dock label shows
[466] claim-godot-mcp-git-issue-521-md-007 — A simpler alternative is to have `cmd_get_project_info` responses carry `server_
[467] claim-godot-mcp-git-issue-521-md-008 — An acceptance criterion is that `_server_version` is populated by a real value f
[468] claim-godot-mcp-git-issue-521-md-009 — An acceptance criterion is that the dock displays both halves of the label once
[469] claim-godot-mcp-git-issue-521-md-010 — The fix pairs naturally with the `cmd_get_addon_info` issue and should be implem
[470] claim-godot-mcp-git-issue-522-md-000 — command_router.gd is 756 lines long."
[471] claim-godot-mcp-git-issue-522-md-008 — An acceptance criterion is that no handler calls a private method on the router,
[472] claim-godot-mcp-git-issue-522-md-009 — An acceptance criterion is that existing contract tests pass unchanged, since en
[473] claim-godot-mcp-git-issue-522-md-010 — An acceptance criterion is that `graphify.sh update .` shows no new god-node and
[474] claim-godot-mcp-git-issue-522-md-011 — Issue #522 is in state CLOSED and carries the label component:addon."
[475] claim-godot-mcp-git-issue-523-md-000 — The 20-node UndoRedo threshold (#461) exists in exactly one of three batch-apply
[476] claim-godot-mcp-git-issue-523-md-001 — In batch.gd, batch_set_property declares `var undo_threshold := 20` but hardcode
[477] claim-godot-mcp-git-issue-523-md-002 — composite.gd's batch_create_nodes (line 161) and apply_node_edits (line 229) hav
[478] claim-godot-mcp-git-issue-523-md-003 — A 500-node batch create opens one giant UndoRedo action (potential editor stall/
[479] claim-godot-mcp-git-issue-523-md-004 — batch.gd cross-scene path (_cross_scene_one) mutates scenes on disk directly wit
[480] claim-godot-mcp-git-issue-523-md-006 — Proposed fix: batch_create_nodes and apply_node_edits must return the same undoa
[481] claim-godot-mcp-git-issue-523-md-007 — Proposed contract tests should pin threshold boundary (19/20/21), the undoable:f
[482] claim-godot-mcp-git-issue-523-md-008 — Acceptance criterion: One shared const; no literal `20` outside it."
[483] claim-godot-mcp-git-issue-523-md-009 — Acceptance criterion: All three batch tools return identical honesty-field shape
[484] claim-godot-mcp-git-issue-523-md-010 — Acceptance criterion: Tests updated in the same commit (rule testing)."
[485] claim-godot-mcp-git-issue-524-md-000 — The addon's entire GDScript layer has zero automated tests."
[486] claim-godot-mcp-git-issue-524-md-001 — Verification today is ~20 hand-run smoke scripts plus indirect pinning from Pyth
[487] claim-godot-mcp-git-issue-524-md-003 — command_router.gd covers envelope validation, unknown-command handling, id stamp
[488] claim-godot-mcp-git-issue-524-md-004 — type_coerce.gd covers all to_json/from_json shapes, string-form parsing, and err
[489] claim-godot-mcp-git-issue-524-md-006 — The fix proposes porting the pure-logic cases, starting small with type_coerce r
[490] claim-godot-mcp-git-issue-524-md-007 — The fix proposes wiring the harness into CI as a job that only runs when `godot/
[491] claim-godot-mcp-git-issue-524-md-008 — Acceptance criteria require that type_coerce.gd and command_router.gd envelope l
[492] claim-godot-mcp-git-issue-524-md-009 — Acceptance criteria require CI to run the harness on addon changes."
[493] claim-godot-mcp-git-issue-524-md-010 — Acceptance criteria require zero skips, applying the enforcement suite health ru
[494] claim-godot-mcp-git-issue-524-md-011 — Python-side contract tests pinning envelopes are located at tests/contract/test_
[495] claim-godot-mcp-git-issue-525-md-000 — Error codes returned by the addon are raw strings written by hand in approximate
[496] claim-godot-mcp-git-issue-525-md-001 — The authoritative set of error codes is the ErrorCode enum in mcp_server/models/
[497] claim-godot-mcp-git-issue-525-md-002 — Nothing ties the addon's hand-written error-code strings to the Python ErrorCode
[498] claim-godot-mcp-git-issue-525-md-003 — The proposed fix adds a const error-code registry on the GDScript side and uses
[499] claim-godot-mcp-git-issue-525-md-004 — The proposed Python-side contract test scans godot/addons/godot_mcp/**/*.gd for
[500] claim-godot-mcp-git-issue-525-md-005 — The proposed contract test runs in the existing pytest suite and requires no edi
[501] claim-godot-mcp-git-issue-525-md-006 — The Python-side contract test alone pins the addon side without needing the GDSc
[502] claim-godot-mcp-git-issue-525-md-007 — An acceptance criterion requires a contract test that fails CI when the addon em
[503] claim-godot-mcp-git-issue-525-md-008 — An acceptance criterion requires all current call sites to pass, with an audit f
[504] claim-godot-mcp-git-issue-525-md-009 — Issue #525 is in state CLOSED."
[505] claim-godot-mcp-git-issue-526-md-001 — `_require_debug_session` in command_router.gd (lines 462-477) checks play sessio
[506] claim-godot-mcp-git-issue-526-md-002 — `_require_live_probe` in command_router.gd (lines 472-478) checks play session,
[507] claim-godot-mcp-git-issue-526-md-003 — `_cmd_get_game_scene_tree` in runtime_session.gd (lines 88-93) re-implements the
[508] claim-godot-mcp-git-issue-526-md-004 — The enhanced hint includes the #454 \"max client limits reached\" diagnostic plu
[509] claim-godot-mcp-git-issue-526-md-005 — `runtime_session._require_unpaused_live_probe()` (lines 20-29) chains `_require_
[510] claim-godot-mcp-git-issue-526-md-006 — The proposed fix consolidates the guards into one guard module with composable p
[511] claim-godot-mcp-git-issue-526-md-008 — An acceptance criterion requires one implementation of each guard with no handle
[512] claim-godot-mcp-git-issue-526-md-009 — An acceptance criterion requires the #454 diagnostic to ship from every probe-ga
[513] claim-godot-mcp-git-issue-526-md-010 — Issue #526 is in state OPEN and carries the label component:addon."
[514] claim-godot-mcp-git-issue-527-md-000 — Issue #527 is in state CLOSED and is labeled documentation and component:addon."
[515] claim-godot-mcp-git-issue-527-md-001 — The cleanup batch comes from the 2026-09-20 addon review and is entirely doc/com
[516] claim-godot-mcp-git-issue-527-md-005 — `from_json` shipped long ago, so the type_coerce.gd docstring should be updated
[517] claim-godot-mcp-git-issue-527-md-007 — The report proposes moving `_init`/`register` to the conventional top-of-file po
[518] claim-godot-mcp-git-issue-527-md-008 — The `# -- batch/export/screenshot/project/resource helpers --` section headers a
[519] claim-godot-mcp-git-issue-527-md-009 — The acceptance criteria require all four fixes in one small PR that is doc-only
[520] claim-godot-mcp-git-issue-528-md-000 — batch_set_property skips UndoRedo for operations above 20 nodes and reports undo
[521] claim-godot-mcp-git-issue-528-md-001 — composite.gd's batch_create_nodes and apply_node_edits open a single giant UndoR
[522] claim-godot-mcp-git-issue-528-md-002 — The add-child undo sequence block is duplicated in mutation._cmd_create_node, co
[523] claim-godot-mcp-git-issue-528-md-003 — _commit_add_child already exists on the command router and is used by audio, par
[524] claim-godot-mcp-git-issue-528-md-004 — The persistence-verdict stamping loop is copy-pasted between batch.gd and compos
[525] claim-godot-mcp-git-issue-528-md-006 — The proposed fix adds a composite variant that registers N children in one actio
[526] claim-godot-mcp-git-issue-528-md-007 — The proposed fix extracts a _persistence_entries(nodes) helper for batch verdict
[527] claim-godot-mcp-git-issue-528-md-008 — The proposed fix adds a shared threshold constant and honesty fields on composit
[528] claim-godot-mcp-git-issue-528-md-009 — Acceptance criterion: no handler hand-rolls the add-child undo sequence, and the
[529] claim-godot-mcp-git-issue-528-md-010 — Acceptance criterion: verdict stamping has one implementation used by both batch
[530] claim-godot-mcp-git-issue-528-md-011 — Acceptance criterion: envelope shapes pinned by existing tests pass unchanged."
[531] claim-godot-mcp-git-issue-529-md-000 — `godot_undo` is a core command implemented as `cmd_undo` in command_router.gd li
[532] claim-godot-mcp-git-issue-529-md-001 — There is no `godot_redo` command."
[533] claim-godot-mcp-git-issue-529-md-007 — `godot_redo` is proposed as mutating (dry_run, like `godot_undo`); `godot_list_h
[534] claim-godot-mcp-git-issue-529-md-008 — The fix requires updating `docs/tool-contracts.md`, skills metadata pinned by `t
[535] claim-godot-mcp-git-issue-529-md-009 — An acceptance criterion is that `godot_redo` mirrors `godot_undo`'s envelope and
[536] claim-godot-mcp-git-issue-529-md-010 — An acceptance criterion is that `godot_list_history` returns the documented fiel
[537] claim-godot-mcp-git-issue-530-md-000 — Server and addon have no handshake."
[538] claim-godot-mcp-git-issue-530-md-001 — The plugin declares `_server_version` (godot_mcp.gd:36) that nothing ever assign
[539] claim-godot-mcp-git-issue-530-md-002 — When server/addon versions drift, the failure mode is opaque per-command `VALIDA
[540] claim-godot-mcp-git-issue-530-md-003 — Addon `cmd_get_addon_info` returns `{ addon_version, godot_version, commands: [a
[541] claim-godot-mcp-git-issue-530-md-005 — Server pushes `server_version` back to the addon, assigning the dock's `_server_
[542] claim-godot-mcp-git-issue-530-md-006 — Server exposes the handshake via `godot_get_server_info`, whose capability snaps
[543] claim-godot-mcp-git-issue-530-md-007 — Server warns (structured, not stack trace) when the addon lacks handlers for too
[544] claim-godot-mcp-git-issue-530-md-008 — `godot_get_server_info` reports addon version, Godot version, and registered-com
[545] claim-godot-mcp-git-issue-530-md-009 — The dock shows the server version once connected, closing #521's missing half."
[546] claim-godot-mcp-git-issue-531-md-000 — The addon can instance a saved scene into the tree via the scene_edit_instance_s
[547] claim-godot-mcp-git-issue-531-md-002 — The proposed tool is named godot_scene_edit_extract_scene, in category scene_edi
[548] claim-godot-mcp-git-issue-531-md-003 — The proposed tool takes params node_path, scene_path (destination res://), repla
[549] claim-godot-mcp-git-issue-531-md-005 — If replace_with_instance is true, one UndoRedo action removes the original subtr
[550] claim-godot-mcp-git-issue-531-md-006 — The tool refuses when the subtree contains nodes owned by an instanced child tha
[551] claim-godot-mcp-git-issue-531-md-007 — dry_run reports the node list that would be extracted plus the destination path.
[552] claim-godot-mcp-git-issue-531-md-009 — The tool must be undoable, confirm-free (additive, mutating class), but honor dr
[553] claim-godot-mcp-git-issue-531-md-010 — The tool refuses non-owned/instanced subtrees with an actionable hint consistent
[554] claim-godot-mcp-git-issue-532-md-002 — The issue proposes a tool named godot_project_move_file in the project toolset w
[555] claim-godot-mcp-git-issue-532-md-003 — The proposed tool moves or renames files within res:// while updating referencin
[556] claim-godot-mcp-git-issue-532-md-005 — The Godot editor's own move dialog remaps scene-embedded and script class_name r
[557] claim-godot-mcp-git-issue-532-md-009 — An acceptance criterion requires move with reference remap across .tscn, .gd, an
[558] claim-godot-mcp-git-issue-532-md-010 — An acceptance criterion requires docs and a tool-contract entry for the project
[559] claim-godot-mcp-git-issue-533-md-000 — Issue #533 is a feature request for cmd_describe_class, which would expose Class
[560] claim-godot-mcp-git-issue-533-md-004 — The proposed tool takes parameters class_name, include_inherited (bool, default
[561] claim-godot-mcp-git-issue-533-md-005 — The addon response is built entirely from ClassDB and requires no live node."
[562] claim-godot-mcp-git-issue-533-md-007 — Methods are returned as name/args/return_type entries obtained via class_get_met
[563] claim-godot-mcp-git-issue-533-md-008 — The response also includes signals, constants, enums, the inherits chain, and ca
[564] claim-godot-mcp-git-issue-533-md-010 — Acceptance criteria require a GDScript handler plus a FastMCP tool with a typed
[565] claim-godot-mcp-git-issue-533-md-011 — Acceptance criteria require the tool to be read_only with category core."
[566] claim-godot-mcp-git-issue-534-md-003 — The proposed server tool godot_runtime_get_output is read_only, gated by _requir
[567] claim-godot-mcp-git-issue-534-md-005 — An acceptance criterion is ring-buffer capture with a seq cursor and no unbounde
[568] claim-godot-mcp-git-issue-534-md-006 — An acceptance criterion is a godot_runtime_get_output contract test (poll-and-ca
[569] claim-godot-mcp-git-issue-534-md-008 — The output ring buffer lives in the addon, consistent with #535's amendment that
[570] claim-godot-mcp-git-issue-534-md-011 — Issue #534 is in CLOSED state with labels enhancement and component:addon."
[571] claim-godot-mcp-git-issue-535-md-004 — An acceptance criterion requires both sides ([Both]) to be implemented with snap
[572] claim-godot-mcp-git-issue-535-md-006 — A design amendment dated 2026-09-20 moved the snapshot store into the addon rath
[573] claim-godot-mcp-git-issue-536-md-006 — An optional on_change_only: bool = true param on godot_runtime_monitor_property
[574] claim-godot-mcp-git-issue-536-md-008 — Acceptance criterion: float epsilon behavior is documented and a contract test p
[575] claim-godot-mcp-git-issue-537-md-000 — The bridge accepts one active peer, and a second Godot editor instance silently
[576] claim-godot-mcp-git-issue-537-md-003 — The server keeps the most recent peer but exposes the connection identity in god
[577] claim-godot-mcp-git-issue-537-md-004 — A second peer joining logs a structured line naming both project paths."
[578] claim-godot-mcp-git-issue-537-md-005 — The snapshot optionally includes previous_peer."
[579] claim-godot-mcp-git-issue-537-md-006 — True multi-peer with per-peer command routing is a stretch goal, where the serve
[580] claim-godot-mcp-git-issue-537-md-009 — Acceptance criterion: peer replacement produces a structured log entry with both
[581] claim-godot-mcp-git-issue-537-md-010 — Acceptance criterion: the server is backward compatible by accepting peers witho
[582] claim-godot-mcp-git-issue-538-md-000 — The Godot MCP bridge is localhost-only with no authentication in v1."
[583] claim-godot-mcp-git-issue-538-md-001 — Anything on localhost can currently inject command envelopes into the bridge."
[584] claim-godot-mcp-git-issue-538-md-003 — When the token is set, the addon's first message after connect is a handshake of
[585] claim-godot-mcp-git-issue-538-md-005 — A token mismatch manifests as a reconnect loop with a structured reason in the d
[586] claim-godot-mcp-git-issue-538-md-009 — An acceptance criterion requires token mismatch to yield a structured refusal at
[587] claim-godot-mcp-git-issue-539-md-001 — There are three possible connection statuses mapping to three immutable textures
[588] claim-godot-mcp-git-issue-539-md-002 — The proposed fix is to build the three status textures once lazily on first use
[589] claim-godot-mcp-git-issue-539-md-003 — The proposed fix frees the textures in _exit_tree, where plain dereference suffi
[590] claim-godot-mcp-git-issue-539-md-004 — An acceptance criterion requires one texture per status, built once."
[591] claim-godot-mcp-git-issue-540-md-000 — MCPCommandRouter._prop_cache maps get_instance_id() to a property-type dict and
[592] claim-godot-mcp-git-issue-540-md-002 — A freed node's cache entry can be served for a new object with the same id, retu
[593] claim-godot-mcp-git-issue-540-md-004 — _invalidate_prop_cache is only called by batch/composite apply paths."
[594] claim-godot-mcp-git-issue-540-md-005 — A node deleted via cmd_delete_node leaves a stale entry until cap prune or id re
[595] claim-godot-mcp-git-issue-540-md-006 — The proposed fix is to key validity on ObjectID + liveness, storing a valid_at c
[596] claim-godot-mcp-git-issue-540-md-007 — A proposed hardening is to call _invalidate_prop_cache in cmd_delete_node / rena
[597] claim-godot-mcp-git-issue-540-md-008 — An alternative proposed fix is to key the cache by WeakRef/ObjectID and validate
[598] claim-godot-mcp-git-issue-540-md-009 — Acceptance criterion: stale entry cannot survive a freed/reused instance id, wit
[599] claim-godot-mcp-git-issue-540-md-010 — Acceptance criterion: delete path invalidates the target's cache entry."
[600] claim-godot-mcp-git-pr-497-md-000 — PR #497 was merged on 2026-09-17."
[601] claim-godot-mcp-git-pr-497-md-002 — The addon adds a new read-only cmd_get_scan_state command returning {scanning: b
[602] claim-godot-mcp-git-pr-497-md-006 — Contract tests pin the poll ordering, the quiet path, and the stuck path."
[603] claim-godot-mcp-git-pr-497-md-007 — Both new contract tests fail without the cmd_get_scan_state poll or the rescan_p
[604] claim-godot-mcp-git-pr-497-md-008 — is_scanning() was verified on Godot 4.7.2, returning true during the initial sca
[605] claim-godot-mcp-git-pr-497-md-009 — The full preflight run reported 800 passed with ruff, mypy, and zero-skip, and i
[606] claim-godot-mcp-git-pr-497-md-010 — docs/tool-contracts.md was updated with the result schema and a determinism para
[607] claim-godot-mcp-git-pr-498-md-000 — PR #498 was merged on 2026-09-17."
[608] claim-godot-mcp-git-pr-498-md-004 — batch_set_property already skipped EditorUndoRedoManager above 20 nodes as a per
[609] claim-godot-mcp-git-pr-498-md-005 — batch_set_property now reports undoable: false plus a hint naming the threshold,
[610] claim-godot-mcp-git-pr-498-md-006 — Contract tests pin both new behaviors, docs/tool-contracts.md was updated, and t
[611] claim-godot-mcp-git-pr-498-md-007 — Live end-to-end checks against Godot 4.7.2 produced undoable:false plus hint for
[612] claim-godot-mcp-git-pr-498-md-008 — The full preflight run reported 803 passed with ruff, mypy, and zero-skip clean.
[613] claim-godot-mcp-git-pr-498-md-009 — The test test_batch_undoable_flag_addon_source_pins_gate_order reads the addon s
[614] claim-godot-mcp-git-pr-498-md-010 — The PR review assigned a score of 92."
[615] claim-godot-mcp-git-pr-499-md-000 — PR #499 was merged on 2026-09-17."
[616] claim-godot-mcp-git-pr-499-md-001 — `create_scene(root_type=\"Collectible\")` on a registered custom `class_name` fa
[617] claim-godot-mcp-git-pr-499-md-003 — The limitation is stated in the `godot_scene_edit_create_scene` tool description
[618] claim-godot-mcp-git-pr-499-md-004 — The limitation is stated in `docs/tool-contracts.md` with the create-then-attach
[619] claim-godot-mcp-git-pr-499-md-005 — The PR is docs-only and the ruff/mypy/contract suite is green with zero-skip cle
[620] claim-godot-mcp-git-pr-499-md-006 — The PR type is Documentation."
[621] claim-godot-mcp-git-pr-499-md-007 — The PR documents the `root_type` built-in ClassDB restriction."
[622] claim-godot-mcp-git-pr-499-md-008 — The PR adds a workaround for custom `class_name` scripts."
[623] claim-godot-mcp-git-pr-499-md-009 — The PR updates the tool description and contracts."
[624] claim-godot-mcp-git-pr-499-md-010 — In `mcp_server/tools/mutation.py`, documentation was added to the `create_scene`
[625] claim-godot-mcp-git-pr-500-md-000 — PR #500 is a CalVer release bump from 2026.09.10 to 2026.09.17."
[626] claim-godot-mcp-git-pr-500-md-001 — The release is additive-only since the last tag and CONTRACT_VERSION stays 1."
[627] claim-godot-mcp-git-pr-500-md-002 — The version bump is applied in lockstep across pyproject.toml, mcp_server/__init
[628] claim-godot-mcp-git-pr-500-md-003 — PR #500 was merged on 2026-09-17."
[629] claim-godot-mcp-git-pr-500-md-005 — The PR bumps the Python package version in __init__.py."
[630] claim-godot-mcp-git-pr-500-md-006 — The PR updates version badges and text in README.md."
[631] claim-godot-mcp-git-pr-500-md-007 — The PR review score is 95."
[632] claim-godot-mcp-git-pr-500-md-009 — Issue #490 is partially compliant because the PR is a version bump only with no
[633] claim-godot-mcp-git-pr-501-md-000 — PR #501 was merged on 2026-09-18."
[634] claim-godot-mcp-git-pr-501-md-002 — The PR changes line counts in skills and AGENTS.md from 55 to 65, 81 to 84, and
[635] claim-godot-mcp-git-pr-501-md-007 — The PR adds a \"Round-trip economy\" section in getting-started with guidelines:
[636] claim-godot-mcp-git-pr-502-md-000 — PR #502 updated the tool count to 181 in documentation."
[637] claim-godot-mcp-git-pr-502-md-001 — PR #502 was merged on 2026-09-18."
[638] claim-godot-mcp-git-pr-502-md-002 — The registered tool surface is 181 tools, verified via local_provider.list_tools
[639] claim-godot-mcp-git-pr-502-md-004 — The change was a count-only correction with no surface change."
[640] claim-godot-mcp-git-pr-502-md-006 — README.md updated the tool count from 180 to 181 in three locations."
[641] claim-godot-mcp-git-pr-502-md-007 — README.md corrected the stale count in the status badge, toolsets section, and a
[642] claim-godot-mcp-git-pr-502-md-008 — skills/README.md updated the tool count from 180 to 181 in the skills documentat
[643] claim-godot-mcp-git-pr-502-md-009 — skills/godot-getting-started/SKILL.md updated the tool count from 180 to 181 in
[644] claim-godot-mcp-git-pr-502-md-010 — The PR review gave a score of 98."
[645] claim-godot-mcp-git-pr-503-md-000 — PR #503 is merged on 2026-09-18."
[646] claim-godot-mcp-git-pr-503-md-001 — PR #503 closes the last silent-failure class from the #458 family: structural ed
[647] claim-godot-mcp-git-pr-503-md-007 — _batch_targets descends into instanced children, so one aggregate ok never hides
[648] claim-godot-mcp-git-pr-503-md-011 — Addon compiles clean on Godot 4.7; full preflight green (807 passed, ruff/mypy/z
[649] claim-godot-mcp-git-pr-504-md-000 — PR #504 adds a set_editable_children tool and instance metadata in the scene tre
[650] claim-godot-mcp-git-pr-504-md-001 — PR #504 was merged on 2026-09-18."
[651] claim-godot-mcp-git-pr-504-md-002 — The godot_scene_edit_set_editable_children tool is mutating and UndoRedo-wrapped
[652] claim-godot-mcp-git-pr-504-md-004 — The persisted verdict for editable children keys on the parent node because the
[653] claim-godot-mcp-git-pr-504-md-005 — Instanced nodes' children carry an owner field (the source scene's res:// path)
[654] claim-godot-mcp-git-pr-504-md-006 — Local nodes carry neither the owner nor editable_children key in the serialized
[655] claim-godot-mcp-git-pr-504-md-008 — The preflight check passed with 811 tests passed and ruff/mypy/zero-skip clean."
[656] claim-godot-mcp-git-pr-504-md-009 — Issue #487 is assessed as partially compliant by the PR review."
[657] claim-godot-mcp-git-pr-505-md-001 — Every poll-based handler now self-reports why it is pending with a stable `reaso
[658] claim-godot-mcp-git-pr-505-md-002 — `poll_ready` relays the last `reason` in its expiry `ToolError`."
[659] claim-godot-mcp-git-pr-505-md-007 — `cmd_get_import_status` maps to `rescan_in_flight` plus a `scanning: bool` flag.
[660] claim-godot-mcp-git-pr-505-md-008 — A shared reason-token table was added to `docs/tool-contracts.md`, and the chang
[661] claim-godot-mcp-git-pr-505-md-010 — `poll_ready` relays `reason` in its expiry error, and a contract test pins that
[662] claim-godot-mcp-git-pr-505-md-011 — The addon compiles clean on Godot 4.7, and integration tests pass 56/56 locally.
[663] claim-godot-mcp-git-pr-506-md-000 — PR #506, titled \"Echo audio bus effect properties in layout read\", was merged
[664] claim-godot-mcp-git-pr-506-md-001 — A read/write asymmetry existed because godot_audio_add_bus_effect accepts proper
[665] claim-godot-mcp-git-pr-506-md-003 — AudioBusEffectInfo gains a properties field of type dict[str, Any], added additi
[666] claim-godot-mcp-git-pr-506-md-004 — On Godot 4.7.2, adding an AudioEffectReverb with room_size 0.85 and wet 0.4 on b
[667] claim-godot-mcp-git-pr-506-md-006 — The handler file godot/addons/godot_mcp/handlers/audio.gd was changed to extract
[668] claim-godot-mcp-git-pr-506-md-007 — The contract test file tests/contract/test_audio.py gained a test for effect pro
[669] claim-godot-mcp-git-pr-507-md-000 — PR #507 adds a `godot_shader_validate` tool for headless shader compile checks."
[670] claim-godot-mcp-git-pr-507-md-001 — PR #507 was merged on 2026-09-18."
[671] claim-godot-mcp-git-pr-507-md-003 — A throwaway runner script sets the code on a scratch `Shader` to trigger the eng
[672] claim-godot-mcp-git-pr-507-md-007 — Live verification on Godot 4.7.2 showed the issue's exact repro (`uniform float
[673] claim-godot-mcp-git-pr-507-md-009 — Contract tests were written red-first, integration tests passed 56/56 on-device,
[674] claim-godot-mcp-git-pr-508-md-000 — PR #508, which adds AudioStreamWAV loop settings to import_asset, was merged on
[675] claim-godot-mcp-git-pr-508-md-001 — import_asset accepts loop config for .wav targets via options.import_settings wi
[676] claim-godot-mcp-git-pr-508-md-002 — The import_asset handler patches the .import sidecar's edit/loop_* params (Resou
[677] claim-godot-mcp-git-pr-508-md-004 — The loop_applied field in the result reports whether the loop config was applied
[678] claim-godot-mcp-git-pr-508-md-005 — Live testing on Godot 4.7.2 showed importing a .wav with loop_mode: 1 produced l
[679] claim-godot-mcp-git-pr-508-md-006 — A red-first contract test named test_import_wav_loop_mode_applied was added, and
[680] claim-godot-mcp-git-pr-508-md-008 — The seeded-sidecar path writes remap/importer, remap/type, and deps/md5 into a f
[681] claim-godot-mcp-git-pr-508-md-011 — docs/tool-contracts.md was updated to include loop_applied in the ImportAssetRes
[682] claim-godot-mcp-git-pr-509-md-000 — PR #509 adds the `godot_scene_edit_rescan_filesystem` tool (read_only, scene_edi
[683] claim-godot-mcp-git-pr-509-md-001 — The rescan is non-destructive by design: the scan reads the disk and refreshes t
[684] claim-godot-mcp-git-pr-509-md-002 — The rescan response carries `scanned` and `scanning` keys derived from the same
[685] claim-godot-mcp-git-pr-509-md-004 — Live verification on Godot 4.7.2 via the bridge showed that writing a `.gd` file
[686] claim-godot-mcp-git-pr-509-md-006 — PR #509 was merged on 2026-09-19."
[687] claim-godot-mcp-git-pr-509-md-007 — `mcp_server/command_map.py` gained a mapping from `scene_edit_rescan_filesystem`
[688] claim-godot-mcp-git-pr-509-md-008 — `mcp_server/models/scene_session.py` gained a `RescanFilesystemResult` Pydantic
[689] claim-godot-mcp-git-pr-509-md-009 — The `_cmd_rescan_filesystem` handler does not register an UndoRedo action, so th
[690] claim-godot-mcp-git-pr-509-md-010 — The optional `cmd_reload_scene` variant without confirm was not implemented, bei
[691] claim-godot-mcp-git-pr-510-md-000 — PR #510, titled Release 2026.09.19, was merged on 2026-09-19."
[692] claim-godot-mcp-git-pr-510-md-001 — The release bumps CalVer from 2026.09.17 to 2026.09.19."
[693] claim-godot-mcp-git-pr-510-md-002 — The release is additive-only since the last tag, with CONTRACT_VERSION remaining
[694] claim-godot-mcp-git-pr-510-md-003 — The tool surface grows from 181 to 184 tools, adding set_editable_children, vali
[695] claim-godot-mcp-git-pr-510-md-005 — The PR type is Documentation and Enhancement."
[696] claim-godot-mcp-git-pr-510-md-006 — The configuration changes affect 3 files."
[697] claim-godot-mcp-git-pr-510-md-007 — The documentation changes affect 5 files."
[698] claim-godot-mcp-git-pr-510-md-009 — The reviewer guide estimates review effort as 1 and gives a score of 95."
[699] claim-godot-mcp-git-pr-510-md-010 — The reviewer guide reports no relevant tests."
[700] claim-godot-mcp-git-pr-510-md-011 — PR-Agent could not safely update the persistent review, so the standalone result
[701] claim-godot-mcp-git-pr-511-md-000 — PR #511 adds a MkDocs documentation site and GitHub Pages deployment."
[702] claim-godot-mcp-git-pr-511-md-001 — PR #511 was merged on 2026-09-19."
[703] claim-godot-mcp-git-pr-511-md-002 — The documentation site is built with MkDocs Material and hosted at https://hybri
[704] claim-godot-mcp-git-pr-511-md-003 — The documentation site contains 17 new pages."
[705] claim-godot-mcp-git-pr-511-md-004 — The architecture deep-dive section comprises 7 pages."
[706] claim-godot-mcp-git-pr-511-md-005 — toolsets.md is generated from the live registry and covers 184 tools across 29 t
[707] claim-godot-mcp-git-pr-511-md-007 — mkdocs.yml configures the Material theme, dark/light mode, mermaid via superfenc
[708] claim-godot-mcp-git-pr-512-md-000 — PR #512 is titled \"Fix docs toolchain installation in CI\"."
[709] claim-godot-mcp-git-pr-512-md-004 — The fix was verified locally with the exact workflow command `uv tool install --
[710] claim-godot-mcp-git-pr-512-md-005 — In .github/workflows/pages.yml, `uv tool install` was changed to use `mkdocs` as
[711] claim-godot-mcp-git-pr-512-md-008 — The PR pins `mkdocs-material` version."
[712] claim-godot-mcp-git-pr-513-md-000 — PR #513 was merged on 2026-09-19."
[713] claim-godot-mcp-git-pr-513-md-001 — PR #513 carries the labels documentation and enhancement."
[714] claim-godot-mcp-git-pr-513-md-002 — `/llms.txt` (page index) and `/llms-full.txt` (whole site as one markdown docume
[715] claim-godot-mcp-git-pr-513-md-003 — `mkdocs-llmstxt>=0.2,<0.4` is pinned in `requirements-docs.txt` and added to the
[716] claim-godot-mcp-git-pr-513-md-004 — `mkdocs build --strict` runs clean with the plugin and produces both `llms.txt`
[717] claim-godot-mcp-git-pr-513-md-005 — The full repo preflight reported 819 passed with ruff, mypy, and zero-skip."
[718] claim-godot-mcp-git-pr-513-md-006 — README.md was updated with a docs badge and a Documentation callout naming the s
[719] claim-godot-mcp-git-pr-513-md-007 — AGENTS.md was updated with the site URL, build pipeline, and the llms URLs to po
[720] claim-godot-mcp-git-pr-513-md-008 — CONTRIBUTING was updated with local `mkdocs serve`/`build --strict` instructions
[721] claim-godot-mcp-git-pr-513-md-009 — mkdocs.yml was modified to configure the `mkdocs-llmstxt` plugin."
[722] claim-godot-mcp-git-pr-513-md-010 — The `mkdocs-exclude` plugin is installed in the CI workflow and `requirements-do
[723] claim-godot-mcp-git-pr-514-md-000 — PR #514 was merged on 2026-09-19."
[724] claim-godot-mcp-git-pr-514-md-001 — The PR ports the documentation site from MkDocs to VitePress using the same tool
[725] claim-godot-mcp-git-pr-514-md-003 — .vitepress/config.mts mirrors wiki-fabric's shape including base, mermaid plugin
[726] claim-godot-mcp-git-pr-514-md-005 — docs/site/llms-gen.mjs runs as a post-build step generating llms.txt and llms-fu
[727] claim-godot-mcp-git-pr-514-md-006 — .github/workflows/deploy-docs.yml mirrors wiki-fabric's workflow using setup-nod
[728] claim-godot-mcp-git-pr-514-md-007 — The mkdocs pages.yml and mkdocs.yml/requirements-docs.txt files are removed."
[729] claim-godot-mcp-git-pr-514-md-008 — All 27 content pages were migrated with cross-links verified by VitePress's dead
[730] claim-godot-mcp-git-pr-514-md-010 — The full repo preflight reports 819 passed with ruff, mypy, and zero-skip."
[731] claim-godot-mcp-git-pr-515-md-000 — PR #515 was merged on 2026-09-19 and labeled as a bug fix."
[732] claim-godot-mcp-git-pr-515-md-002 — All 27 index links in llms.txt were verified to return HTTP 200 against the live
[733] claim-godot-mcp-git-pr-515-md-003 — The llms-full.txt content was unaffected by the fix because it is raw markdown."
[734] claim-godot-mcp-git-pr-515-md-004 — The fix updated the htmlPath function in docs/site/llms-gen.mjs to generate .htm
[735] claim-godot-mcp-git-pr-515-md-006 — The change to llms-gen.mjs was +6/-4 lines."
[736] claim-godot-mcp-git-pr-515-md-007 — The PR reviewer guide scored the PR 95 with an estimated review effort of 1."
[737] claim-godot-mcp-git-pr-516-md-000 — PR #516 was merged on 2026-09-19 and labeled documentation."
[738] claim-godot-mcp-git-pr-516-md-001 — The llmstxt.org v2 spec added two capabilities beyond v1 that the site lacked: p
[739] claim-godot-mcp-git-pr-516-md-002 — Every rendered page serves clean markdown at its own URL with .md appended, so a
[740] claim-godot-mcp-git-pr-516-md-003 — 27 page.html.md variants are generated by llms-gen.mjs with frontmatter stripped
[741] claim-godot-mcp-git-pr-516-md-005 — The two discovery link relations are injected via VitePress's transformHead hook
[742] claim-godot-mcp-git-pr-516-md-006 — llms.txt follows the exact v2 file format: H1, blockquote, details, H2 file list
[743] claim-godot-mcp-git-pr-516-md-007 — A local build produced dist/llms.txt, dist/llms-full.txt, and 27 *.html.md varia
[744] claim-godot-mcp-git-pr-516-md-009 — config.mts gained a transformHead hook to inject describedby and alternate link
[745] claim-godot-mcp-git-pr-516-md-010 — llms-gen.mjs was rewritten to follow the llmstxt.org v2 spec and to generate <pa
[746] claim-godot-mcp-git-pr-517-md-000 — PR #517 was merged on 2026-09-19."
[747] claim-godot-mcp-git-pr-517-md-006 — Sidebar, index pages, and llms-gen.mjs sections were updated so the new pages fl
[748] claim-godot-mcp-git-pr-517-md-007 — npm run build produced zero dead links, with new pages and .html.md variants in
[749] claim-godot-mcp-git-pr-517-md-009 — The PR's file walkthrough lists 7 documentation files changed."
[750] claim-godot-mcp-git-pr-518-md-000 — PR #518 was merged on 2026-09-19."
[751] claim-godot-mcp-git-pr-518-md-002 — VitePress only dead-link-checks markdown body links, so 13 config links shipped
[752] claim-godot-mcp-git-pr-518-md-003 — All 16 stale config links were rewritten to the real flat page names, with archi
[753] claim-godot-mcp-git-pr-518-md-004 — A new guard script docs/site/check-links.mjs is chained into npm run build, pars
[754] claim-godot-mcp-git-pr-518-md-007 — The new check-links.mjs file was added with 31 insertions and 0 deletions."
[755] claim-godot-mcp-git-pr-518-md-008 — A reviewer flagged that the regex /link: '([^']+)'/g only matches single-quoted
[756] claim-godot-mcp-git-pr-519-md-000 — PR #519 was merged on 2026-09-19."
[757] claim-godot-mcp-git-pr-519-md-001 — Issue #518 diagnosed the dead links correctly but shipped only the guard, leavin
[758] claim-godot-mcp-git-pr-519-md-003 — After `npm run build`, `dist/concepts.html` contains 0 occurrences of the old `g
[759] claim-godot-mcp-git-pr-519-md-004 — The link guard passes with 32 nav/sidebar links resolving."
[760] claim-godot-mcp-git-pr-519-md-005 — The change to `docs/site/.vitepress/config.mts` is +15/-15 lines."
[761] claim-godot-mcp-git-pr-519-md-007 — The guard `check-links.mjs` is not included in this PR's diff because it was alr
[762] claim-godot-mcp-git-pr-519-md-008 — The PR rewrites 13 links to flat paths but does not include the corresponding `.
[763] claim-godot-mcp-git-pr-519-md-009 — PR #519 carries the labels enhancement, Bug fix, and Review effort 1/5."
[764] claim-godot-mcp-git-pr-541-md-000 — PR #541 was merged on 2026-09-20."
[765] claim-godot-mcp-git-pr-541-md-002 — A reverse-drift check requires every ErrorCode member to be either emitted by th
[766] claim-godot-mcp-git-pr-541-md-005 — Running `uv run pytest tests/contract/test_addon_error_codes.py` produced 2 pass
[767] claim-godot-mcp-git-pr-541-md-006 — The full test suite run reported 821 passed with zero skips."
[768] claim-godot-mcp-git-pr-541-md-007 — The `_FAIL_CALL` regex only matches `_fail(\"CODE\", ...)` where the code is a d
[769] claim-godot-mcp-git-pr-541-md-008 — The reverse-drift test hardcodes a `server_only` set of three codes, so every en
[770] claim-godot-mcp-git-pr-541-md-009 — After the fix, the regex uses DOTALL across `_fail(` plus whitespace, catching t
[771] claim-godot-mcp-git-pr-541-md-011 — The ticket's suggested const error-code registry on the GDScript side was not im
[772] claim-godot-mcp-git-pr-542-md-000 — PR #542 was merged on 2026-09-20."
[773] claim-godot-mcp-git-pr-542-md-001 — The new file godot/tests/type_coerce_smoke.gd adds 34 headless checks pinning th
[774] claim-godot-mcp-git-pr-542-md-002 — godot/tests/run_commands_smoke.gd was extended to cover the #461 honest-abort co
[775] claim-godot-mcp-git-pr-542-md-003 — tests/integration/test_addon_read_smokes.py registers type_coerce_smoke in the p
[776] claim-godot-mcp-git-pr-542-md-004 — The tests are deterministic by design: no sockets, no editor, no wall-clock, no
[777] claim-godot-mcp-git-pr-542-md-006 — The full test suite run reported 822 passed with zero skips, and ruff plus mypy
[778] claim-godot-mcp-git-pr-542-md-007 — tests/contract/test_addon_error_codes.py adds a contract test ensuring addon err
[779] claim-godot-mcp-git-pr-542-md-008 — The reviewer flagged that the _check function's `same` variable is dead code, si
[780] claim-godot-mcp-git-pr-542-md-009 — The redundant `same` local was fixed in commit da69c09 by removing the unused ex
[781] claim-godot-mcp-git-pr-542-md-010 — No new CI job was added for godot/addons/** changes; the new smoke tests ride th
[782] claim-godot-mcp-git-pr-542-md-011 — Ticket #461's batch_set_property undoable flag and docs/tool-contracts.md update
[783] claim-godot-mcp-git-pr-543-md-000 — PR #543 implements the server↔addon handshake from issue #530, closing #521 as a
[784] claim-godot-mcp-git-pr-543-md-001 — cmd_get_addon_info self-describes with addon_version (live from plugin.cfg), god
[785] claim-godot-mcp-git-pr-543-md-002 — cmd_server_hello {version} stores the server's pushed package version (router.se
[786] claim-godot-mcp-git-pr-543-md-004 — The first successful handshake fire-and-forgets cmd_server_hello with the server
[787] claim-godot-mcp-git-pr-543-md-005 — BridgeDiagnostics gains addon_version/addon_commands fields and ServerDiagnostic
[788] claim-godot-mcp-git-pr-543-md-006 — A server↔addon version mismatch surfaces in godot_get_server_info as an addon_dr
[789] claim-godot-mcp-git-pr-543-md-007 — The contract test tests/contract/test_addon_handshake.py reports 10 passed cover
[790] claim-godot-mcp-git-pr-543-md-008 — The full test suite reports 832 passed with zero skips and clean ruff + mypy."
[791] claim-godot-mcp-git-pr-543-md-009 — The addon_info method was not protected by a lock, so two concurrent first calls
[792] claim-godot-mcp-git-pr-543-md-010 — The race condition was fixed in commit c6d46e5 by taking _addon_info_lock only w
[793] claim-godot-mcp-git-pr-543-md-011 — PR #543 was merged on 2026-09-20."
[794] claim-godot-mcp-git-pr-544-md-000 — PR #544, which unifies runtime probe and debug session guards into mcp_guards.gd
[795] claim-godot-mcp-git-pr-544-md-001 — Three drifted guard flavors were consolidated into a single module, MCPGuards, a
[796] claim-godot-mcp-git-pr-544-md-002 — command_router.gd's _require_debug_session and _require_live_probe implementatio
[797] claim-godot-mcp-git-pr-544-md-003 — runtime_session.gd's private _require_unpaused_live_probe re-wrapper now routes
[798] claim-godot-mcp-git-pr-544-md-006 — get_game_scene_tree deliberately keeps its soft {playing, connected: false, prob
[799] claim-godot-mcp-git-pr-544-md-007 — The guards take an injectable play-session oracle (set_play_session_oracle) beca
[800] claim-godot-mcp-git-pr-544-md-008 — is_game_paused() (the #411 tell) moved into the guard module, and is_breaked() l
[801] claim-godot-mcp-git-pr-544-md-009 — tests/contract/test_addon_guards.py passed 5 tests, source-scanning for module e
[802] claim-godot-mcp-git-pr-545-md-000 — PR #545 was merged on 2026-09-20."
[803] claim-godot-mcp-git-pr-545-md-001 — command_router.gd defines a single shared const MCP_UNDO_THRESHOLD := 20 plus th
[804] claim-godot-mcp-git-pr-545-md-002 — Before this PR, composite.gd's batch_create_nodes and apply_node_edits had no un
[805] claim-godot-mcp-git-pr-545-md-003 — In composite.gd both batch tools became threshold-aware: above the threshold the
[806] claim-godot-mcp-git-pr-545-md-005 — The contract test file tests/contract/test_undo_threshold.py passed 5 tests cove
[807] claim-godot-mcp-git-pr-545-md-006 — Running the headless threshold_smoke.gd script produced THRESHOLD_TEST_OK coveri
[808] claim-godot-mcp-git-pr-545-md-007 — The full test suite at the time of the PR description reported 844 passed with z
[809] claim-godot-mcp-git-pr-545-md-009 — BatchCreateNodesResult regained the dry_run: bool = False field, which had been
[810] claim-godot-mcp-git-pr-545-md-010 — Both _cmd_batch_create_nodes and _cmd_apply_node_edits now check params.get(\"dr
[811] claim-godot-mcp-git-pr-545-md-011 — After the review fixes, the full suite reported 846 passed with zero skips, clea
[812] claim-godot-mcp-git-pr-546-md-000 — PR #546 was merged on 2026-09-20."
[813] claim-godot-mcp-git-pr-546-md-001 — The router was approximately 816 lines, about two-thirds of which was boilerplat
[814] claim-godot-mcp-git-pr-546-md-002 — mcp_helpers.gd is a new module named MCPHelpers."
[815] claim-godot-mcp-git-pr-546-md-003 — mcp_helpers.gd contains the #523 threshold single-source, including the UNDO_THR
[816] claim-godot-mcp-git-pr-546-md-007 — Adding a domain now costs one table entry instead of four edits."
[817] claim-godot-mcp-git-pr-546-md-009 — Shared-logic call sites were changed from _router._X to _router._helpers.X."
[818] claim-godot-mcp-git-pr-546-md-010 — The RefCounted cycle is gone because handlers no longer keep per-domain members
[819] claim-godot-mcp-git-pr-547-md-004 — `cmd_get_game_output` deliberately has no break-state gate so output remains rea
[820] claim-godot-mcp-git-pr-547-md-007 — The full test suite reported 861 passed with zero skips, plus clean ruff and myp
[821] claim-godot-mcp-godot-mcp-agents-md-000 — godot-mcp is a standalone MCP server providing generic Godot editor control over
[822] claim-godot-mcp-godot-mcp-agents-md-005 — The MCP server owns all safety/permission logic and Pydantic domain models and h
[823] claim-godot-mcp-godot-mcp-agents-md-006 — The Godot addon is a GDScript EditorPlugin (Godot 4.4+) whose WebSocketPeer clie
[824] claim-godot-mcp-godot-mcp-agents-md-007 — JSON envelopes are versioned from day one, with command {id, command, params} an
[825] claim-godot-mcp-godot-mcp-agents-md-009 — All create/rename/delete/set operations in the addon must register with EditorUn
[826] claim-godot-mcp-godot-mcp-agents-md-010 — The toolchain requires Godot 4.4+ (validated on 4.7-stable), Python 3.11+, and F
[827] claim-godot-mcp-godot-mcp-agents-md-011 — The addon connects to the server's bridge listener at default ws://127.0.0.1:908
[828] claim-godot-mcp-godot-mcp-contributing-md-000 — godot-mcp requires Python 3.11 or newer, managed with uv."
[829] claim-godot-mcp-godot-mcp-contributing-md-001 — godot-mcp requires Godot 4.4 or newer and has been validated on 4.7-stable."
[830] claim-godot-mcp-godot-mcp-contributing-md-002 — The project pins FastMCP 4.0.1, which is GA on MCP SDK v2 (the 2026-07-28 sessio
[831] claim-godot-mcp-godot-mcp-contributing-md-003 — The system is two halves joined by a WebSocket bridge: AI client over stdio to a
[832] claim-godot-mcp-godot-mcp-contributing-md-004 — The MCP server owns all safety/permission logic, Pydantic models, and tool schem
[833] claim-godot-mcp-godot-mcp-contributing-md-005 — The Godot addon is the only layer that touches the Godot Editor API and routes c
[834] claim-godot-mcp-godot-mcp-contributing-md-006 — Tools tagged destructive may be irreversible and require both dry_run and confir
[835] claim-godot-mcp-godot-mcp-contributing-md-007 — Zero skipped tests are a blocking gate: no @pytest.mark.skip, no xfail, and no b
[836] claim-godot-mcp-godot-mcp-contributing-md-008 — Versioning uses CalVer YYYY.MM.DD[-N], and the version must stay in lockstep acr
[837] claim-godot-mcp-godot-mcp-contributing-md-011 — The Qodo PR bot automatically runs /describe and /review on pull requests, and f
[838] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-000 — The editor dials and the server listens, but the server still drives every comma
[839] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-001 — The FastMCP server is implemented in Python under mcp_server/."
[840] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-003 — The Godot addon is GDScript with the @tool annotation, located in addons/godot_m
[841] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-004 — mcp_bridge.gd is a WebSocket client that connects to a URL and reconnects with b
[842] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-005 — The addon dials out to ws://127.0.0.1:9080."
[843] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-006 — The server boots, binds port 9080, and waits."
[844] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-008 — The server owns all safety/preconditions while the addon owns all Godot calls, a
[845] claim-godot-mcp-godot-mcp-docs-architecture-diagram-md-010 — The AI client communicates with the server over stdio using the MCP protocol."
[846] claim-godot-mcp-godot-mcp-docs-architecture-md-000 — The bridge connection direction is inverted: the server listens and the editor c
[847] claim-godot-mcp-godot-mcp-docs-architecture-md-001 — The server initiates every command and the addon responds; the addon never pushe
[848] claim-godot-mcp-godot-mcp-docs-architecture-md-007 — Error codes must be stable and drawn from the enumerated set, never ad-hoc strin
[849] claim-godot-mcp-godot-mcp-docs-architecture-md-008 — Godot types cross the bridge as JSON-safe forms coerced on the addon side in the
[850] claim-godot-mcp-godot-mcp-docs-architecture-md-010 — Because the WebSocket bridge is synchronous (one request to one response), the r
[851] claim-godot-mcp-godot-mcp-docs-debugger-feasibility-md-000 — The Godot editor→game debugger protocol supports step control, stack-frame inspe
[852] claim-godot-mcp-godot-mcp-docs-debugger-feasibility-md-001 — A Tier 2 debugger toolset (step_*, continue, godot_debugger_get_stack_frames, go
[853] claim-godot-mcp-godot-mcp-docs-harness-performance-md-000 — The Godot editor is single-threaded: the addon drains queued command packets onc
[854] claim-godot-mcp-godot-mcp-docs-harness-performance-md-001 — Change #166 dropped a redundant preflight round-trip per mutation."
[855] claim-godot-mcp-godot-mcp-docs-harness-performance-md-003 — godot_composite_run_commands executes a whole command list in a single frame and
[856] claim-godot-mcp-godot-mcp-docs-harness-performance-md-004 — Each sub-mutation in a composite batch wraps its own UndoRedo action and command
[857] claim-godot-mcp-godot-mcp-docs-harness-performance-md-005 — godot_composite_run_commands cannot be nested."
[858] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-000 — The MCP spec's 2026-07-28 revision removes sessions and the initialize handshake
[859] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-001 — In the 2026-07-28 revision, per-request `_meta` carries version/capabilities ins
[860] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-002 — Cross-call state moves to explicit handles: server-minted tokens passed as ordin
[861] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-003 — godot-mcp is pinned to FastMCP 4.0.0b3, which speaks 2025-era session semantics.
[862] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-004 — FastMCP 4.0's `Client` already negotiates sessionless by default, so real client
[863] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-005 — The issue's premise that ToolsetMiddleware keys enable/disable on `context.sessi
[864] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-007 — The destructive-tool approval guard has no session dependency; it uses an `Input
[865] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-008 — A source-shape guard (`tests/contract/test_sessionless_invariants.py`) AST-scans
[866] claim-godot-mcp-godot-mcp-docs-mcp-2026-07-28-migration-md-010 — Unlike a spec-default server that scopes a grant to the caller, godot-mcp's gran
[867] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-000 — Every @mcp.tool takes typed parameters and returns a typed Pydantic model, never
[868] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-001 — Every @mcp.tool validates inputs and checks preconditions before any side effect
[869] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-002 — Every tool is tagged with exactly one safety class."
[870] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-003 — dry_run=True returns what would happen and performs nothing."
[871] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-004 — All safety logic lives in mcp_server/safety.py, never in the addon."
[872] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-005 — Every JSON-result tool declares a standard outputSchema and returns structuredCo
[873] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-006 — godot_editor_capture_screenshot returns ImageContent (non-JSON), so it declares
[874] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-009 — GODOT_MCP_APPROVAL_TIMEOUT defaults to 30.0 seconds per request."
[875] claim-godot-mcp-godot-mcp-docs-tool-contracts-md-010 — godot_enable_toolset checks the connected Godot version lazily once per session
[876] claim-godot-mcp-godot-mcp-docs-tutorial-md-000 — The tutorial requires Godot 4.4+ installed, uv (Python package manager), and the
[877] claim-godot-mcp-godot-mcp-docs-tutorial-md-001 — Every time the MCP client connects, the server sends initialization instructions
[878] claim-godot-mcp-godot-mcp-docs-tutorial-md-003 — Only after enabling a toolset can you call the tools in that category."
[879] claim-godot-mcp-godot-mcp-docs-tutorial-md-004 — The LLM can discover workflow prompts via list_prompts() and render them via get
[880] claim-godot-mcp-godot-mcp-docs-tutorial-md-005 — Every tool's description explicitly states which toolset it belongs to."
[881] claim-godot-mcp-godot-mcp-docs-tutorial-md-007 — The Coin Collector mini-game has a player (CharacterBody2D) that moves with arro
[882] claim-godot-mcp-godot-mcp-docs-tutorial-md-008 — The Coin Collector mini-game has three gold coins (Area2D) scattered on the map.
[883] claim-godot-mcp-godot-mcp-readme-md-001 — godot-mcp has 180 tools across 29 categories."
[884] claim-godot-mcp-godot-mcp-readme-md-002 — Only the inspection toolset is enabled by default among the 28 toggleable toolse
[885] claim-godot-mcp-godot-mcp-readme-md-003 — The PyPI package is named godot-editor-mcp."
[886] claim-godot-mcp-godot-mcp-readme-md-004 — The Docker image is ghcr.io/hybridindie/godot-mcp."
[887] claim-godot-mcp-godot-mcp-readme-md-005 — Version 2026.09.10 is the first stable release."
[888] claim-godot-mcp-godot-mcp-readme-md-006 — godot-mcp bridges an AI agent and a live Godot editor, allowing the agent to dri
[889] claim-godot-mcp-godot-mcp-readme-md-007 — The server is game-agnostic and knows Godot, not the user's game."
[890] claim-godot-mcp-godot-mcp-readme-md-008 — Godot minimum version is 4.4 and the recommended validated target is 4.7."
[891] claim-godot-mcp-godot-mcp-readme-md-010 — The addon checks the editor version on enable and warns if it is older than Godo
[892] claim-godot-mcp-godot-mcp-readme-md-011 — The server listens on http://localhost:9090 for MCP HTTP and ws://localhost:9080
[893] claim-instructions-and-rules-instructions-and-rules-agents-md-000 — This repository is the genesis repository that generates AI assistant harnesses
[894] claim-instructions-and-rules-instructions-and-rules-agents-md-001 — The repository also hosts the Epic Scoping Skills as its own installed harness."
[895] claim-instructions-and-rules-instructions-and-rules-agents-md-003 — The genesis harness uses templates/_shared/ rendered into target projects by boo
[896] claim-instructions-and-rules-instructions-and-rules-agents-md-004 — Epic Scoping Skills use .agents/ as the source rendered into thin wrappers in .c
[897] claim-instructions-and-rules-instructions-and-rules-agents-md-005 — The golden rule is to edit content in .agents/ for epic skills or templates/_sha
[898] claim-instructions-and-rules-instructions-and-rules-agents-md-006 — Content must never be duplicated into a wrapper."
[899] claim-instructions-and-rules-instructions-and-rules-agents-md-007 — Shared rules referenced by multiple files live in a doctrine/ layer and should b
[900] claim-instructions-and-rules-instructions-and-rules-agents-md-008 — The on-demand reference sections are not auto-loaded."
[901] claim-instructions-and-rules-instructions-and-rules-agents-md-009 — The post-bootstrap flow is bootstrap.sh (render) → /harness-eval (trim + suggest
[902] claim-instructions-and-rules-instructions-and-rules-agents-md-010 — Each skill wrapper is a thin pointer, and the model reads the .agents/ body on-d
[903] claim-instructions-and-rules-instructions-and-rules-claude-md-000 — The shared, tool-agnostic project context — covering what this repo is, how the
[904] claim-instructions-and-rules-instructions-and-rules-claude-md-001 — Only Claude-Code-specific notes belong in this file."
[905] claim-instructions-and-rules-instructions-and-rules-claude-md-002 — Claude-specific harness assets (skills, hooks, scripts) live under `templates/cl
[906] claim-instructions-and-rules-instructions-and-rules-claude-md-003 — These assets are generated output where mirrored from `templates/_shared/`."
[907] claim-instructions-and-rules-instructions-and-rules-claude-md-004 — The Drift policy is in AGENTS.md."
[908] claim-instructions-and-rules-instructions-and-rules-claude-md-005 — The drift check is a Claude Code hook invoked as `bash templates/claude-code/.cl
[909] claim-instructions-and-rules-instructions-and-rules-claude-md-006 — The drift check should be run from repo root with a bootstrapped harness in scop
[910] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-000 — Adding a new article requires adding a .md file to templates/_shared/articles/,
[911] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-001 — Adding a new agent requires adding a .md file to templates/_shared/agents/ and a
[912] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-002 — Adding a new command requires adding a .md file to templates/_shared/commands/ a
[913] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-003 — Shared doctrine requires a doctrine_entries entry in mirror-pairs.json with sour
[914] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-004 — Drift is checked by running bash templates/claude-code/.claude/hooks/check-primi
[915] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-006 — A patch version bump (x.y.z to x.y.(z+1)) covers typo, wording, or formatting fi
[916] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-008 — A major version bump (x.y.z to (x+1).0.0) covers a workflow restructure that bre
[917] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-009 — Each file versions independently, with doctrine/ and skills/ files versioned sep
[918] claim-instructions-and-rules-instructions-and-rules-contributing-harness-md-010 — templates/_shared/ is the single source, and the platform-specific files under t
[919] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--000 — Shared content lives in `.agents/` as plain markdown with no frontmatter and no
[920] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--001 — Each harness has its own thin wrapper files containing only the frontmatter that
[921] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--002 — The harness wrapper files reference the shared content by path."
[922] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--003 — Harness wrappers are located at `.opencode/skills/<name>/SKILL.md` plus opencode
[923] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--004 — Both the epic-scoping skills and the genesis meta-flow follow the shared-content
[924] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--005 — `bootstrap-harness` is the single canonical body for installing and tailoring a
[925] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--006 — The `install-harness` agent (Claude Code / Copilot) is a thin entry point pointi
[926] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--007 — Genesis template output under `.github/instructions/`, `.github/copilot-instruct
[927] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--008 — The golden rule is to edit content in `.agents/`, edit frontmatter in the harnes
[928] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-architecture--009 — `.agents/doctrine/` holds rules shared across multiple skills and rubrics, cover
[929] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-000 — The bootstrap script reads templates/_shared/ as the canonical source and render
[930] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-001 — For Claude Code, the entry point is CLAUDE.md and rules live in .claude/rules/,
[931] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-002 — For GitHub Copilot, the entry point is .github/copilot-instructions.md and rules
[932] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-003 — For Opencode, the entry point is CLAUDE.md and rules live in .opencode/."
[933] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-004 — The recommended auto-detect install command is `bash templates/scripts/bootstrap
[934] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-007 — The `--auto-detect` flag inspects `--output-dir` for stack, versions, and depend
[935] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-genesis-overv-008 — The `--mode backend-only` flag skips all frontend rules and placeholders."
[936] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-000 — The epic-composer skill transforms source material into a complete Epic."
[937] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-001 — The story-decomposer skill decomposes a ready Epic into INVEST-compliant stories
[938] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-002 — The task-decomposer skill breaks down stories into AI-executable tasks with para
[939] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-004 — The acceptance-criteria-rules.md doctrine module is referenced by epic-acceptanc
[940] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-005 — When a rule is shared by two or more skills or rubrics, it belongs in doctrine/.
[941] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-008 — Each skill wrapper is a one-line body referencing .agents/skills/<name>.md."
[942] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-009 — The Opencode and Claude Code wrappers take $ARGUMENTS for user-provided input."
[943] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-skills-and-re-010 — The epic-composer skill labels its output with the progression SYNTHESIS_ONLY →
[944] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-000 — The templates/_shared/articles/ directory contains constitutional rules that are
[945] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-001 — The templates/_shared/agents/ directory contains shared agent definitions where
[946] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-002 — The templates/_shared/commands/ directory contains shared commands/prompts whose
[947] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-003 — The templates/_shared/doctrine/ directory contains shared rules referenced by mu
[948] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-004 — The templates/_shared/skills/ directory contains shared shippable skills that ar
[949] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-006 — The mirror-pairs.json file is the single source of truth for all mirror pairs, i
[950] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-007 — The bootstrap.sh script is the main installer."
[951] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-source-struct-008 — The generate-copilot-mirrors.py script transforms Claude frontmatter into Copilo
[952] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-000 — epic-composer includes a Phase 0: Context Discovery that distinguishes greenfiel
[953] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-001 — epic-composer includes a Phase 1: Source Synthesis."
[954] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-002 — epic-composer includes a Phase 2: Contradiction & Completeness Review."
[955] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-003 — epic-composer includes a Phase 3: Guided Interview that invokes epic-interview i
[956] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-004 — epic-composer includes a Phase 4: Epic Draft that uses epic-shell, linter, and t
[957] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-005 — epic-composer includes a Phase 5: Readiness Assessment that applies epic-rubric.
[958] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-006 — epic-composer includes a Phase 6: Stakeholder Review Checkpoint."
[959] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-007 — The epic-composer pipeline produces a Ready Epic artifact with a traceability ma
[960] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-008 — story-decomposer includes a Phase 1: Epic Validation."
[961] claim-instructions-and-rules-instructions-and-rules-docs-agents-sections-workflow-md-009 — story-decomposer includes a Phase 2: Decomposition Planning that uses a coverage
[962] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-000 — Harness evaluation is run after bootstrap.sh has rendered the harness into a pro
[963] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-006 — Phase 4 does not create files yet; it only lists suggestions for the user to pic
[964] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-007 — The rules state to propose, not execute — never delete or edit files without con
[965] claim-instructions-and-rules-instructions-and-rules-docs-harness-eval-md-010 — If a rule is shared across 2+ articles, it belongs in doctrine/ and should be re
[966] claim-instructions-and-rules-instructions-and-rules-install-md-000 — The repo is public, so nothing here needs authentication."
[967] claim-instructions-and-rules-instructions-and-rules-install-md-001 — All routes run the same flow defined in `.agents/skills/bootstrap-harness.md`."
[968] claim-instructions-and-rules-instructions-and-rules-install-md-002 — The one-command install clones the genesis repo into `~/.cache/instructions-and-
[969] claim-instructions-and-rules-instructions-and-rules-install-md-004 — The one-command install requires no interview and no authentication."
[970] claim-instructions-and-rules-instructions-and-rules-install-md-005 — The install script accepts options after `bash -s --`, including `--output-dir`
[971] claim-instructions-and-rules-instructions-and-rules-install-md-007 — The interactive prompt works identically in Claude Code and Opencode."
[972] claim-instructions-and-rules-instructions-and-rules-install-md-008 — From a clone, Claude Code / Opencode can run `/bootstrap-harness` with an output
[973] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-001 — Each harness has its own thin, frontmatter-only wrapper files that reference the
[974] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-002 — Rules shared across multiple skills and rubrics live in `.agents/doctrine/` and
[975] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-005 — Each skill labels its output with one of a defined set of response states."
[976] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-006 — Every skill can be invoked two ways: directly via its slash command, or automati
[977] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-007 — Opencode skills are model-invoked only, so the commands in `opencode.json` are t
[978] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-008 — Claude Code skills double as slash commands and accept `$ARGUMENTS`."
[979] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-010 — Each harness ships a non-blocking pointer-edit guardrail that warns but never bl
[980] claim-instructions-and-rules-instructions-and-rules-prompts-skills-md-011 — Claude Code additionally runs an `InstructionsLoaded` hook that logs which instr
[981] claim-instructions-and-rules-instructions-and-rules-readme-md-000 — The repository generates equivalent instruction harnesses for GitHub Copilot, Cl
[982] claim-instructions-and-rules-instructions-and-rules-readme-md-003 — The .claude/rules/ directory contains the Constitutional Articles I–X plus doctr
[983] claim-instructions-and-rules-instructions-and-rules-readme-md-004 — The golden rule requires editing content in .agents/ or templates/_shared/, edit
[984] claim-instructions-and-rules-instructions-and-rules-readme-md-005 — The flask profile has 5 overlays (architecture, api-design, testing, async-patte
[985] claim-instructions-and-rules-instructions-and-rules-readme-md-006 — Claude rules and Copilot instructions are body-identical mirrors, with generate-
[986] claim-instructions-and-rules-instructions-and-rules-research-md-003 — Anthropic explicitly warns that bloated CLAUDE.md files cause Claude to ignore a
[987] claim-instructions-and-rules-instructions-and-rules-research-md-007 — AGENTS.md is the lowest-common-denominator portable file across all 4+ platforms
[988] claim-instructions-and-rules-instructions-and-rules-research-md-009 — Articles I, II, IV, V, VI, and IX have zero automated enforcement."
[989] claim-instructions-and-rules-instructions-and-rules-research-md-010 — Tech stack versions are duplicated across 10+ files."
[990] claim-nomokailist-nomokailist-agents-md-000 — Backend lint and typecheck are run with `cd backend && uv run ruff check src/ &&
[991] claim-nomokailist-nomokailist-agents-md-001 — Frontend verification runs `cd frontend && npm run lint && npm run type-check`."
[992] claim-nomokailist-nomokailist-agents-md-002 — The backend uses FastAPI + LangGraph 1.0 for recommendation agents."
[993] claim-nomokailist-nomokailist-agents-md-003 — The frontend uses Next.js with shadcn UI components."
[994] claim-nomokailist-nomokailist-agents-md-004 — There is no direct DB access from the frontend; all queries go through the API l
[995] claim-nomokailist-nomokailist-agents-md-006 — Type hints are required on all function signatures and enforced by mypy."
[996] claim-nomokailist-nomokailist-agents-md-011 — Tier-based cache TTL in `by_request_hash_tiered` is finished=90d / airing=3d / u
[997] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-000 — Supabase is used as the sole backend infrastructure provider for database, authe
[998] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-001 — SQLAlchemy ORM is explicitly excluded; the Supabase Python client is used direct
[999] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-002 — Redis is explicitly excluded; Supabase is used for caching patterns where needed
[1000] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-003 — Celery is explicitly excluded; async Python tasks or LangGraph are used for work
[1001] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-004 — Built-in Row Level Security (RLS) enforces data isolation at the database layer.
[1002] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-006 — SQLAlchemy bypasses Supabase RLS policies unless explicitly configured."
[1003] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-007 — Vendor lock-in to Supabase means migrating away requires rewriting repositories.
[1004] claim-nomokailist-nomokailist-docs-adr-0001-supabase-only-backend-md-010 — Auth tokens are validated via supabase.auth.get_user(token) with no static secre
[1005] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-000 — NomikaiList's AI coding assistant configuration lives in AGENTS.md, .opencode/,
[1006] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-002 — AGENTS.md is the derived entry point that summarizes and links the rules but doe
[1007] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-004 — A machine-readable checker at backend/scripts/check-constitution.py validates ar
[1008] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-005 — A rule update order is defined as .claude/rules/ → AGENTS.md."
[1009] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-006 — An instructions-drift checker at scripts/check-instructions-drift.sh validates t
[1010] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-007 — The constitution checker runs in CI and violations block merges."
[1011] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-008 — check-agent-drift.sh hooks warn when .claude/rules/ changes without downstream u
[1012] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-009 — CalVer (2026.04.24) on enforcement.md tracks the rule publication date."
[1013] claim-nomokailist-nomokailist-docs-adr-0002-constitution-as-code-md-010 — check-constitution.py Article IX checks that enforcement.md exists."
[1014] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-000 — NomikaiList enforces a 68% minimum aggregate test coverage threshold in CI."
[1015] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-001 — The project adopts a tiered coverage model that sets expectations by module risk
[1016] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-002 — Privacy/Auth modules (services/privacy_service.py, services/auth_service.py, api
[1017] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-003 — Revenue/Data integrity modules (repositories/*, services/import_service.py, api/
[1018] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-005 — AI Agents/ML modules (agents/*, ml/*, services/recommendation_scorer.py) have a
[1019] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-006 — Utilities/Config modules (config.py, adapters/*, CLI helpers) have a coverage ta
[1020] claim-nomokailist-nomokailist-docs-adr-0003-tiered-test-coverage-md-008 — Tests are authored in the order: contract tests, integration tests, E2E tests, t
[1021] claim-nomokailist-nomokailist-docs-adr-0004-ai-fit-receipts-md-004 — Per-axis weights at or above SIGNAL_FLOOR (0.1) are summed and normalised agains
[1022] claim-nomokailist-nomokailist-docs-adr-0004-ai-fit-receipts-md-005 — Cross-axis composition uses a simple unweighted mean over non-zero axes."
[1023] claim-nomokailist-nomokailist-docs-adr-0004-ai-fit-receipts-md-010 — The service is deterministic: the same (user, media) pair returns the same paylo
[1024] claim-nomokailist-nomokailist-docs-adr-0005-review-queue-authz-model-md-001 — All six review-queue routes execute via the service-role Supabase client (get_su
[1025] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-000 — The MAL adapter was built on the public Jikan proxy at api.jikan.moe/v4."
[1026] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-001 — The public Jikan proxy is being retired upstream."
[1027] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-004 — The decision is to self-host Jikan v4 via the official jikanme/jikan-rest Docker
[1028] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-006 — Self-hosting requires zero adapter logic changes, only swapping base_url, while
[1029] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-007 — The rate limit is raised from 50 to 120 req/min, configurable via JIKAN_RATE_LIM
[1030] claim-nomokailist-nomokailist-docs-adr-0006-self-host-jikan-md-008 — The Compose stack grows by 4 containers (jikan-rest, MongoDB, TypeSense, backing
[1031] claim-nomokailist-nomokailist-docs-api-md-000 — NomikaiList provides a RESTful API for anime and manga discovery and recommendat
[1032] claim-nomokailist-nomokailist-docs-api-md-001 — The development base URL for the NomikaiList API is http://localhost:8000."
[1033] claim-nomokailist-nomokailist-docs-api-md-002 — The NomikaiList API version is v1."
[1034] claim-nomokailist-nomokailist-docs-api-md-004 — POST /auth/signup creates a new user account."
[1035] claim-nomokailist-nomokailist-docs-api-md-005 — POST /auth/login returns an access_token, token_type bearer, and expires_in 3600
[1036] claim-nomokailist-nomokailist-docs-api-md-006 — GET /media/search supports query parameters q (required), media_type (optional),
[1037] claim-nomokailist-nomokailist-docs-api-md-007 — POST /ratings requires an Authorization Bearer token and accepts media_id, ratin
[1038] claim-nomokailist-nomokailist-docs-api-md-008 — GET /recommendations returns personalized recommendations with fields id, media_
[1039] claim-nomokailist-nomokailist-docs-api-md-009 — Rate limits are applied per endpoint: Authentication 5 requests/minute, Search 1
[1040] claim-nomokailist-nomokailist-docs-api-md-011 — All error responses follow a format containing detail, error_code, request_id, t
[1041] claim-nomokailist-nomokailist-docs-ci-setup-md-000 — The CI setup requires four Supabase test environment secrets: SUPABASE_TEST_URL,
[1042] claim-nomokailist-nomokailist-docs-ci-setup-md-001 — AWS deployment secrets (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY) are optiona
[1043] claim-nomokailist-nomokailist-docs-ci-setup-md-002 — A new Supabase project for testing should be created separately from production.
[1044] claim-nomokailist-nomokailist-docs-ci-setup-md-003 — Database migrations are applied by iterating over all .sql files in backend/migr
[1045] claim-nomokailist-nomokailist-docs-ci-setup-md-004 — The CI/CD Pipeline workflow runs on every push to main and every pull request."
[1046] claim-nomokailist-nomokailist-docs-ci-setup-md-005 — The test-backend job enforces 90% coverage for security code."
[1047] claim-nomokailist-nomokailist-docs-ci-setup-md-006 — The Security Scanning workflow runs on pushes to main/develop, pull requests, an
[1048] claim-nomokailist-nomokailist-docs-ci-setup-md-007 — The rls-security-tests job runs all RLS tests with a 90% coverage requirement an
[1049] claim-nomokailist-nomokailist-docs-ci-setup-md-008 — Coverage requirements are 90% for security code (enforced by --cov-fail-under=90
[1050] claim-nomokailist-nomokailist-docs-ci-setup-md-009 — RLS tests are skipped for pull requests from forks because GitHub does not expos
[1051] claim-nomokailist-nomokailist-docs-ci-setup-md-010 — Best practice is to use a dedicated Supabase project for testing, not production
[1052] claim-nomokailist-nomokailist-docs-deployment-md-001 — Supabase remains the managed database, auth, and storage, and no Vercel, Fly.io,
[1053] claim-nomokailist-nomokailist-docs-deployment-md-008 — NEXT_PUBLIC_* values are inlined into the client bundle at build time by Next.js
[1054] claim-nomokailist-nomokailist-docs-developer-setup-md-000 — Prerequisites include Python 3.11+, Node.js 18+, `uv` package manager, Git, and
[1055] claim-nomokailist-nomokailist-docs-developer-setup-md-001 — Backend setup uses `uv sync` to create a virtual environment and install depende
[1056] claim-nomokailist-nomokailist-docs-developer-setup-md-002 — Frontend setup uses `npm install`."
[1057] claim-nomokailist-nomokailist-docs-developer-setup-md-003 — Create `.env` file in project root by copying `.env.example`."
[1058] claim-nomokailist-nomokailist-docs-developer-setup-md-004 — Required environment variables include Supabase configuration (SUPABASE_URL, SUP
[1059] claim-nomokailist-nomokailist-docs-developer-setup-md-005 — Development servers are run with backend command `uv run uvicorn src.main:app --
[1060] claim-nomokailist-nomokailist-docs-developer-setup-md-006 — Access URLs are frontend at http://localhost:3000, backend API at http://localho
[1061] claim-nomokailist-nomokailist-docs-developer-setup-md-007 — Database schema is managed through Supabase."
[1062] claim-nomokailist-nomokailist-docs-developer-setup-md-008 — Alembic/SQLAlchemy migrations have been removed."
[1063] claim-nomokailist-nomokailist-docs-developer-setup-md-010 — New Supabase tables should be created with Row Level Security (RLS) policies."
[1064] claim-nomokailist-nomokailist-docs-developer-setup-md-011 — Contributing workflow uses TDD approach (RED → GREEN → REFACTOR)."
[1065] claim-nomokailist-nomokailist-docs-graphify-setup-md-003 — The OLLAMA_BASE_URL default is http://localhost:11434/v1."
[1066] claim-nomokailist-nomokailist-docs-graphify-setup-md-006 — graphifyy 0.8.6+ handles Ollama extraction natively."
[1067] claim-nomokailist-nomokailist-docs-importing-data-md-000 — NomikaiList supports importing from MyAnimeList (via Jikan), AniList (GraphQL),
[1068] claim-nomokailist-nomokailist-docs-importing-data-md-003 — Bulk catalog import uses `backend/scripts/comprehensive_import.py` for catalog s
[1069] claim-nomokailist-nomokailist-docs-importing-data-md-004 — A full import from all supported platforms can be run with `uv run python script
[1070] claim-nomokailist-nomokailist-docs-importing-data-md-005 — An incremental update can be run with `uv run python scripts/comprehensive_impor
[1071] claim-nomokailist-nomokailist-docs-importing-data-md-006 — Incremental catalog sync uses each adapter's recently-updated endpoint when supp
[1072] claim-nomokailist-nomokailist-docs-importing-data-md-008 — If an adapter does not support recently-updated fetch, the service falls back to
[1073] claim-nomokailist-nomokailist-docs-importing-data-md-009 — For recurring imports, script execution can be scheduled using cron, GitHub Acti
[1074] claim-nomokailist-nomokailist-docs-overview-md-000 — NomikaiList is a privacy-first anime and manga discovery platform that combines
[1075] claim-nomokailist-nomokailist-docs-overview-md-001 — Import and sync ratings from AniList, MyAnimeList, and Kitsu."
[1076] claim-nomokailist-nomokailist-docs-overview-md-002 — Every recommendation includes a human-readable explanation of why you're getting
[1077] claim-nomokailist-nomokailist-docs-overview-md-003 — Multiple algorithms are used: collaborative filtering, content-based, hidden gem
[1078] claim-nomokailist-nomokailist-docs-overview-md-005 — Row-level security is implemented at the database level."
[1079] claim-nomokailist-nomokailist-docs-overview-md-006 — The media catalog is a normalized database from multiple platforms."
[1080] claim-nomokailist-nomokailist-docs-overview-md-007 — Cross-platform deduplication ensures you see one entry per title."
[1081] claim-nomokailist-nomokailist-docs-overview-md-008 — NomikaiList uses an AI-driven graph recommendation engine that builds a dynamic
[1082] claim-nomokailist-nomokailist-docs-overview-md-009 — The graph recommendation system considers your direct ratings and viewing histor
[1083] claim-nomokailist-nomokailist-docs-security-rls-md-000 — NomiKaiList uses Supabase's Row Level Security (RLS) to enforce data access cont
[1084] claim-nomokailist-nomokailist-docs-security-rls-md-002 — The service role is a privileged Supabase role that bypasses all RLS policies."
[1085] claim-nomokailist-nomokailist-docs-security-rls-md-005 — Public Read pattern allows anyone to read data, but only service role can modify
[1086] claim-nomokailist-nomokailist-docs-style-md-000 — Typography uses three font families, each with a clear role, and roles must neve
[1087] claim-nomokailist-nomokailist-docs-style-md-010 — The AI drawer pattern is a 560px slide-in panel from the right."
[1088] claim-nomokailist-nomokailist-docs-style-md-011 — The design system prohibits dark mode."
[1089] claim-nomokailist-nomokailist-docs-testing-md-000 — The recommended testing approach is to use Local Supabase for all database-depen
[1090] claim-nomokailist-nomokailist-docs-testing-md-001 — Integration tests always use Local Supabase and never use the Mock Client."
[1091] claim-nomokailist-nomokailist-docs-testing-md-002 — Contract tests always use Local Supabase and never use the Mock Client."
[1092] claim-nomokailist-nomokailist-docs-testing-md-003 — Unit tests with a database prefer Local Supabase, with the Mock Client as fallba
[1093] claim-nomokailist-nomokailist-docs-testing-md-004 — The backend test suite contains 37 test files."
[1094] claim-nomokailist-nomokailist-docs-testing-md-005 — The backend contract test suite contains 21 files."
[1095] claim-nomokailist-nomokailist-docs-testing-md-006 — The backend integration test suite contains 7 files."
[1096] claim-nomokailist-nomokailist-docs-testing-md-007 — The backend unit test suite contains 5 files."
[1097] claim-nomokailist-nomokailist-docs-testing-md-008 — Recommendation generation has a performance requirement of under 2 seconds."
[1098] claim-nomokailist-nomokailist-docs-testing-md-010 — The backend pytest configuration sets the coverage failure threshold at 80%."
[1099] claim-nomokailist-nomokailist-docs-testing-md-011 — The frontend Jest configuration requires global coverage thresholds of 80 for br
[1100] claim-nomokailist-nomokailist-docs-user-guide-md-000 — Usernames must be between 3 and 30 characters."
[1101] claim-nomokailist-nomokailist-docs-user-guide-md-001 — Passwords must be at least 8 characters long."
[1102] claim-nomokailist-nomokailist-docs-user-guide-md-002 — Onboarding requires rating 15 to 20 anime or manga titles."
[1103] claim-nomokailist-nomokailist-docs-user-guide-md-003 — The dashboard displays recent activity, taste profile, recommendations, and stat
[1104] claim-nomokailist-nomokailist-docs-user-guide-md-004 — Search allows filtering by type (anime or manga)."
[1105] claim-nomokailist-nomokailist-docs-user-guide-md-005 — Import supports MyAnimeList, AniList, and Kitsu."
[1106] claim-nomokailist-nomokailist-docs-user-guide-md-006 — The import process involves going to the Import page, selecting a platform, ente
[1107] claim-nomokailist-nomokailist-docs-user-guide-md-007 — Ratings and lists are imported automatically."
[1108] claim-nomokailist-nomokailist-docs-user-guide-md-009 — Profile visibility can be controlled."
[1109] claim-nomokailist-nomokailist-readme-md-000 — NomikaiList is an Anime & Manga Discovery Platform with AI-powered curation and
[1110] claim-nomokailist-nomokailist-readme-md-001 — Backend prerequisites include Python 3.11+, uv, Node.js 18+, and a Supabase acco
[1111] claim-nomokailist-nomokailist-readme-md-002 — Backend dependencies are declared in pyproject.toml and pinned in uv.lock, with
[1112] claim-nomokailist-nomokailist-readme-md-003 — The unified ingestion pipeline runs as one command `nomikai ingest run --mode ba
[1113] claim-nomokailist-nomokailist-readme-md-009 — The backend framework is FastAPI 0.104.1."
[1114] claim-nomokailist-nomokailist-readme-md-011 — The database is PostgreSQL (Supabase)."
[1115] claim-nomokailist-nomokailist-security-md-001 — Security vulnerabilities must be reported privately through GitHub's private vul
[1116] claim-nomokailist-nomokailist-security-md-006 — The project aims to remediate high/critical issues within 30 days and agrees a d
[1117] claim-nomokailist-nomokailist-security-md-007 — Reporters who wish to be credited will be named."
[1118] claim-nomokailist-nomokailist-security-md-008 — The NomikaiList backend API, frontend, and ingestion pipeline in this repository
[1119] claim-nomokailist-nomokailist-security-md-009 — Vulnerabilities in the third-party platforms Supabase, AniList, MyAnimeList, and

_Generated from the evidence fabric on 2026-09-21. Citations link to claims in evidence/claims/._
