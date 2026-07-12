# OPARLI

A multi-agent, LLM-assisted algorithmic trading system for spot gold (XAUUSD),
built around a single codebase that runs identically in live and backtest modes.

The system streams market data from Interactive Brokers into PostgreSQL, runs a
pipeline of specialised agents (technical, visual, sentiment, meta, risk,
execution, and position management) over that data, and exposes a FastAPI backend
and a Vue 3 frontend for monitoring, control, and research. A separate research
stack covers Smart Money Concepts (SMC) strategy validation and a jump-model
market-regime classifier.

This is a solo research project under active development. It is not a
production-ready or turnkey trading bot, and it is not investment advice. See
[Project Status](#project-status) and [Disclaimer](#disclaimer) before running
anything against a funded account.

---

## Table of Contents

- [Design Goals](#design-goals)
- [Architecture](#architecture)
  - [Agent Pipeline](#agent-pipeline)
  - [Message Bus](#message-bus)
  - [Backtestable Services](#backtestable-services)
  - [Scanner: Two-Stage Filtering](#scanner-two-stage-filtering)
- [Repository Layout](#repository-layout)
- [Data](#data)
- [Research Stack](#research-stack)
- [Technology](#technology)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [API Surface](#api-surface)
- [Deployment](#deployment)
- [Project Status](#project-status)
- [Disclaimer](#disclaimer)

---

## Design Goals

1. **One codebase, two execution modes.** The same agent logic that trades live
   must be replayable bar-for-bar in a backtest, with no parallel
   re-implementation to drift out of sync. This is achieved by injecting the data
   source and the clock rather than reading `datetime.now()` and the live
   database directly (see [Backtestable Services](#backtestable-services)).

2. **Separation of decision from analysis.** Each analyst produces an opinion; a
   meta-agent aggregates weighted opinions into a decision; a risk manager
   validates it; an execution agent places it; a trade/position manager owns its
   lifecycle. No single agent both analyses and executes.

3. **Cost-aware LLM usage.** Vision and language-model calls are expensive.
   A cheap, rule-based filter gates the expensive multi-agent analysis so that
   full LLM passes only run when a candidate opportunity clears a quality bar.

4. **Run on constrained hardware.** The target deployment is an Oracle Cloud Free
   Tier instance (1 GB RAM). Inter-agent messaging is therefore an in-process,
   thread-safe bus rather than an external broker.

---

## Architecture

### Agent Pipeline

Agents are defined in [backend/agents/](backend/agents/) and share a common
[base_agent.py](backend/agents/base_agent.py) that declares the agent taxonomy
and the message envelope.

| Agent | Role | Notes |
|-------|------|-------|
| Scanner | Monitors the market, captures chart screenshots, detects candidate opportunities, and fans out analysis requests | Two-stage filter, see below |
| Technical Analyst | Rule-based indicator analysis (RSI, MACD, Bollinger Bands, moving averages), confluence, key levels | Backed by a pure service, no LLM |
| Visual Analyst | Chart-pattern recognition over a rendered chart image using a vision LLM | Support/resistance, trend, signal + reasoning |
| Sentiment Analyst | News and macro-context reasoning via a text LLM | No live news source wired yet |
| Meta Agent | Aggregates weighted analyst opinions, resolves conflicts, applies consensus/confidence thresholds, and emits a trade signal | Governance and weight bounds enforced pre-trade |
| Risk Manager | Position sizing, stop-loss and take-profit validation, hard limits | Pure `risk_service` delegate |
| Execution | Places and tracks orders | Injected clock and data provider |
| Trade Manager | Owns the in-flight trade lifecycle and mid-trade actions | Replayable |
| Position Manager | Manages open positions after fill | |

The taxonomy also reserves a Quant Analyst slot for future use.

Flow, at a high level:

```
Scanner ──ANALYSIS_REQUEST──▶ Technical / Visual / Sentiment
                                    │
                                    ▼  ANALYSIS_RESULT (signal, confidence, reasoning)
                                 Meta Agent
                                    │  weighted vote + governance
                                    ▼  TRADE_SIGNAL
                                 Risk Manager
                                    │  approve / reject, sizing, SL/TP
                                    ▼  EXECUTION_REQUEST
                                 Execution ──▶ Trade Manager / Position Manager
```

### Message Bus

Inter-agent communication uses an in-process
[message_bus.py](backend/core/message_bus.py): a thread-safe set of per-agent
priority mailboxes with broadcast and direct-addressing, plus message-history
tracking. An [agent_orchestrator.py](backend/core/agent_orchestrator.py) wires
agents to the bus, and a [scheduler.py](backend/core/scheduler.py) drives
periodic work.

A Kafka + Zookeeper stack is defined in the Docker Compose file under
[design_files/](design_files/) and was part of the original design, but the
backend does **not** depend on it. The in-process bus was chosen deliberately to
fit the 1 GB memory budget.

### Backtestable Services

The core architectural bet is that agents should not talk to wall-clock time or
the live database directly. Instead, the decision logic lives in pure services
under [backend/services/](backend/services/) that take their data source and
clock as arguments:

- **Market data** — `MarketDataProvider` (abstract) with a `LiveDataProvider`
  (PostgreSQL) and a `HistoricalDataProvider` (CSV/Parquet). The historical
  provider is bounded by an `as_of` timestamp and slices its frame with a binary
  search, which both prevents lookahead and keeps replays fast.
- **Clock** — `Clock` (abstract) with a `LiveClock` and a `SimulatedClock`, so
  agents that need "now" receive an injected time.
- **Analysis** — `technical_service.run_technical_analysis(provider, symbol,
  as_of)` is the single source of truth used by both the live Technical Analyst
  and the backtests. Meta and visual decision logic are likewise factored into
  pure modules.
- **Risk & governance** — `risk_service.run_risk_validation(...)` is a pure
  function the Risk Manager delegates to; `governance.py` holds circuit breakers,
  iterative weight-bound enforcement, and position-size clamping wired into the
  meta pre-trade path.

Because the strategy *is* the agent pipeline, the backtest harness
([scripts/backtest_agents.py](scripts/backtest_agents.py)) is strategy-agnostic:
it swaps in the historical provider and simulated clock and replays the same
agents that run live.

### Scanner: Two-Stage Filtering

The Scanner ([SCANNER_AGENT_ARCHITECTURE.md](backend/agents/SCANNER_AGENT_ARCHITECTURE.md))
balances opportunity detection against LLM cost:

- **Stage 1 — technical filter.** Pure Python, no LLM, sub-100 ms. Rejects
  anything below a confidence/confluence floor or not at a key level / volume
  event. Event-driven triggers include candle close (weighted by timeframe),
  significant price moves, volume spikes, and a periodic heartbeat, with
  throttling to cap scan frequency.
- **Stage 2 — full multi-agent analysis.** Only runs when Stage 1 passes.
  Engages the visual, sentiment, and meta agents at real LLM cost.

The intent is to keep the expensive analysis path rare while still reacting to
genuine structure.

---

## Repository Layout

```
algo_project/
├── backend/                 FastAPI backend, agents, services, routes
│   ├── agents/              The nine agent classes + base agent and docs
│   ├── core/                Message bus, orchestrator, scheduler
│   ├── services/            Pure services: data providers, clock, technical,
│   │                        risk, governance, sizing, indicators, streaming
│   ├── routes/              REST + WebSocket endpoints
│   ├── middleware/          API key, rate limiting, security headers
│   ├── config/              DB config, LLM provider abstraction, news events
│   ├── database/            Agent / risk / meta / evolution SQL schemas
│   └── main.py              API entry point
├── frontend/                Vue 3 + Vite dashboard (charts, agent pipeline,
│                            backtest and validation views)
├── backtester/              Standalone event-driven backtesting module
│                            (indicators, signals, portfolio, handlers)
├── regime_classifier/       Jump-model market-regime classifier
├── scripts/                 Backtests, SMC validation, walk-forward, backfill,
│                            data import/export, deploy, cloud setup
├── database/                SQL schema + historical OHLCV and news CSV/Parquet
├── notebooks/               Research notebooks + SMC strategy knowledge base
├── memory-bank/             Project brief, system patterns, technical context
├── design_files/            Docker Compose (Kafka), deployment notes, env example
└── scraper_fxfac/           Forex Factory economic-calendar scraper
```

## Data

- **Price** — roughly five years of 1-minute XAUUSD bars (~990k bars, ~688
  trading days, 2021–2026) plus GC futures, stored as CSV and Parquet under
  [database/ohlcv_data/](database/ohlcv_data/). A canonical `ohlcv_1min` view in
  Postgres unions historical and realtime tables for live reads.
- **News** — Forex Factory economic-calendar exports per year (2010–2026) under
  [database/historical_news/](database/historical_news/), normalised to a
  UTC Parquet file, produced by [scraper_fxfac/](scraper_fxfac/).

## Research Stack

Independent of the live pipeline, the repository carries a substantial research
effort used to decide *what* the agents should look for. Most of it lives in the
notebooks under [notebooks/](notebooks/), backed by scripts and a standalone
engine.

- **Research notebooks.** [notebooks/](notebooks/) is where hypotheses are
  formed and tested before anything reaches the agents:
  - [backtest.ipynb](notebooks/backtest.ipynb) — the main research notebook. It
    covers session definitions (UTC, DST-split), a key-level engine and touch-
    outcome study built to be free of look-ahead by construction (levels carry
    an `active_from`, outcomes measured in $ and ATR units over 15m/1h/4h), a
    mandatory matched-random baseline control, pre-registered conditions with
    multiple-comparison correction, unit tests, and a time-series-momentum
    (TSMOM) study with train / sealed-window splits and block-bootstrap
    significance testing. It exports touch-event and signal datasets that feed
    the live scanner.
  - [smc_validation_backtest.ipynb](notebooks/smc_validation_backtest.ipynb) —
    full Smart Money Concepts validation: order blocks, fair value gaps, break
    of structure / change of character, and liquidity sweeps, each with proper
    filters (displacement, mitigation, higher-timeframe trend gating).
  - [multi_agent_simulation.ipynb](notebooks/multi_agent_simulation.ipynb) —
    replays the multi-agent pipeline over historical CSV data using the same
    shared services as production, so agent behaviour can be studied offline.
- **SMC findings.** Validated conclusions are written up in
  [notebooks/SMC_STRATEGY_GUIDE.md](notebooks/SMC_STRATEGY_GUIDE.md) —
  displacement and mitigation filters, higher-timeframe trend gating, and
  session/hour win-rate tables.
- **Validation scripts.** [scripts/](scripts/) holds runnable counterparts to
  the notebook studies (SMC sweeps, order-block/FVG/BOS-CHoCH validation,
  opening-range breakout / fade, train/test splits, walk-forward analysis).
  Strategies that failed validation are kept under
  [scripts/no_go_strategies/](scripts/no_go_strategies/) as a record.
- **Regime classifier.** [regime_classifier/](regime_classifier/) implements a
  three-state (trending / ranging / volatile) statistical jump model with a jump
  penalty tuned to downstream strategy Sharpe rather than log-likelihood, sparse
  feature selection, and a random-forest layer for next-regime prediction. It
  follows the Nystrup et al. and Pomorski & Gorse regime-modelling literature
  (references are cited in the source).
- **Standalone backtester.** [backtester/](backtester/) is a separate
  event-driven engine (data handlers, indicators, signals, portfolio) used for
  faster single-strategy experiments.

## Technology

**Backend** — Python 3.12+, FastAPI, Uvicorn, psycopg2, `ib_insync`
(Interactive Brokers), APScheduler, pandas / numpy / pandas-ta, mplfinance,
`anthropic`, and a pluggable LLM provider abstraction.

**LLM providers** — [llm_provider.py](backend/config/llm_provider.py) abstracts
text and vision calls behind a single interface; the project uses Gemini in
development and Claude in production, selected by environment.

**Frontend** — Vue 3, Vite, Pinia, Vue Router, and TradingView Lightweight
Charts, with custom chart primitives for session boxes and regime overlays.

**Storage** — PostgreSQL for time-series and agent state, with materialised /
unioned views for multi-timeframe reads.

**Infrastructure** — Docker Compose (optional Kafka stack), deployment to Oracle
Cloud Free Tier over SSH.

## Getting Started

Prerequisites: Python 3.12+, Node.js 18+, PostgreSQL, and — for live data —
Interactive Brokers TWS or IB Gateway.

```bash
# 1. Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Database — apply the schemas
#    database/schema.sql plus the schemas under backend/database/
psql "$DATABASE_URL" -f ../database/schema.sql

# 3. Frontend
cd ../frontend
npm install
```

## Configuration

Backend configuration is read from `backend/.env`. An example lives at
[design_files/.env.example](design_files/.env.example):

```
DATABASE_URL=postgresql://user:password@localhost:5432/oparli_database
API_KEY=your-generated-api-key
GOOGLE_API_KEY=your-gemini-api-key       # development
ANTHROPIC_API_KEY=your-anthropic-api-key # production
ENV=development                          # development = Gemini, production = Claude
IB_HOST=127.0.0.1
IB_PORT=4002
IB_CLIENT_ID=1
```

The frontend reads its own `frontend/.env` (`VITE_API_BASE_URL`, `VITE_WS_URL`,
`VITE_API_KEY`).


## Running the System

```bash
# API server (routes, WebSocket streaming, dashboard)
cd backend && source venv/bin/activate
uvicorn main:app --reload

# Agent runtime (orchestrator + supporting services)
python run_system.py

# Frontend dev server
cd frontend && npm run dev
```

Backtests and research are driven from [scripts/](scripts/), for example:

```bash
python scripts/backtest_agents.py        # replay the agent pipeline on history
python scripts/run_walk_forward.py       # walk-forward analysis
python scripts/smc_validation_train_test.py
```

Convenience launchers (`scripts/start-all.sh`, `scripts/3-start-backend.sh`,
`scripts/4-start-frontend.sh`) wrap the above.

## API Surface

The FastAPI app in [backend/main.py](backend/main.py) mounts routers for:

- **Live trading** — market state, order and position control
- **Data management** — historical backfill, gap detection, import/export
- **Backtest** — run and inspect agent-pipeline and strategy backtests
- **Regime** — regime-classifier output
- **Validation** — SMC / strategy validation results
- **Dashboard** — aggregated monitoring data
- **Auth** — JWT-based authentication

Requests pass through API-key, rate-limiting, and security-header middleware
([backend/middleware/security.py](backend/middleware/security.py)), with input
validators for symbol, timeframe, and limit parameters.

## Deployment

The target is a single small cloud instance. [scripts/deploy.sh](scripts/deploy.sh)
builds the frontend and rsyncs the frontend build and backend source to the
server over SSH (the server has no git credentials), then restarts the API.
[scripts/setup-oracle-cloud.sh](scripts/setup-oracle-cloud.sh) provisions the
host. The Kafka Docker Compose stack under [design_files/](design_files/) is
optional and not required by the running system.

## Project Status

Active development by a single author. Substantial parts are implemented — all
agent classes, the core message bus / orchestrator / scheduler, the FastAPI
backend and Vue frontend, the TWS-to-PostgreSQL streaming pipeline, the
two-stage scanner, and a validated liquidity-sweep backtest — but the system is
**not** yet running end-to-end live. Known gaps at the time of writing:

- The agent orchestrator is not yet started from the API entry point, and the
  agent routes are not fully enabled, so the pipeline does not trade
  automatically out of the box.
- The Sentiment Analyst has no live news source; backtests treat it as neutral.
- The meta-agent evolution mode uses placeholder performance data.
- There is schema-versus-code drift on the `executed_trades` table that needs
  reconciliation before relying on trade persistence.

Treat this repository as a research and engineering artifact, not a deployable
trading product.

## Disclaimer

This software is provided for research and educational purposes only. It is not
financial advice, and nothing here is a recommendation to buy or sell any
instrument. Trading leveraged instruments such as spot gold carries substantial
risk of loss. Use it against a live, funded account entirely at your own risk.
The authors accept no liability for any losses incurred.
