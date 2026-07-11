# Multi-Agent Trading System

A sophisticated autonomous trading system using 7 specialized agents that work together to analyze markets, make trading decisions, and execute trades.

## System Architecture

### Layer 1: Core Trading Agents (Operational)

```
┌─────────────────────────────────────────────────────────────────┐
│                     AGENT ORCHESTRATOR                           │
│              (Message Broker & Scheduler)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┴──────────────┐
                │                             │
        ┌───────▼────────┐            ┌──────▼───────┐
        │   SCANNER      │            │  EXECUTION   │
        │    AGENT       │            │    AGENT     │
        │                │            │              │
        │ - Takes        │            │ - Places     │
        │   screenshots  │            │   orders     │
        │ - Monitors     │            │ - Manages    │
        │   market       │            │   positions  │
        │ - Detects      │            │              │
        │   opportunities│            │              │
        └────────┬───────┘            └──────▲───────┘
                 │                           │
                 │ ANALYSIS_REQUEST          │ EXECUTION_REQUEST
                 │                           │
    ┌────────────┴────────────┐     ┌───────┴─────────┐
    │                          │     │                  │
┌───▼──────┐  ┌────▼──────┐  ┌▼────▼──┐         ┌────▼────────┐
│ VISUAL   │  │TECHNICAL  │  │SENTIMENT│         │    RISK     │
│ ANALYST  │  │ ANALYST   │  │ ANALYST │         │   MANAGER   │
│          │  │           │  │         │         │             │
│ - Claude │  │ - RSI     │  │ - News  │         │ - Position  │
│   Vision │  │ - MACD    │  │ - Claude│         │   sizing    │
│ - Pattern│  │ - BB      │  │   Text  │         │ - Stop Loss │
│   recog  │  │ - MA      │  │ - Macro │         │ - Take      │
│          │  │           │  │   factors│         │   Profit    │
└────┬─────┘  └────┬──────┘  └────┬────┘         └─────▲───────┘
     │             │              │                     │
     │ ANALYSIS_RESULT            │                     │
     └─────────────┴──────────────┴──────┐              │
                                          │              │
                                   ┌──────▼──────────────┴─────┐
                                   │     META-AGENT             │
                                   │   (Judge/Coordinator)      │
                                   │                            │
                                   │ - Weighs opinions          │
                                   │ - Resolves conflicts       │
                                   │ - Makes final decision     │
                                   │                            │
                                   └────────────────────────────┘
```

## Agent Descriptions

### 1. Scanner Agent
**Role**: Market Monitoring

**Frequency**: Every 15 minutes (scheduled)

**Responsibilities**:
- Takes chart screenshots using headless Chrome
- Monitors market for opportunities (price breakouts, volume spikes, MA crossovers)
- Fetches current market data from database
- Broadcasts `ANALYSIS_REQUEST` to all analysts when opportunity detected

**Key Files**:
- `backend/agents/scanner_agent.py`

---

### 2. Visual Analyst Agent
**Role**: Chart Pattern Recognition

**Uses**: Claude Sonnet 4 Vision API

**Responsibilities**:
- Analyzes chart screenshots using AI vision
- Identifies patterns (head & shoulders, triangles, flags, double tops/bottoms)
- Detects support/resistance levels
- Assesses trend direction and strength
- Returns: BUY/SELL/NEUTRAL with confidence 0-100%

**Prompt**: Expert gold trader with 20 years experience analyzing XAUUSD charts

**Key Files**:
- `backend/agents/visual_analyst_agent.py`

---

### 3. Technical Analyst Agent
**Role**: Indicator-Based Analysis

**Responsibilities**:
- Calculates technical indicators:
  - RSI (Relative Strength Index)
  - MACD (Moving Average Convergence Divergence)
  - Bollinger Bands
  - SMA (Simple Moving Average) - 20 & 50 period
  - EMA (Exponential Moving Average)
  - Volume analysis
- Generates signals based on indicator thresholds
- Aggregates multiple signals into final recommendation
- Returns: BUY/SELL/NEUTRAL with confidence

**Key Files**:
- `backend/agents/technical_analyst_agent.py`

---

### 4. Sentiment Analyst Agent
**Role**: Market Sentiment Analysis

**Uses**: Claude Sonnet 4 Text API

**Responsibilities**:
- Analyzes market sentiment from:
  - Current market conditions
  - Macro factors (USD strength, Fed policy, inflation)
  - Geopolitical events
  - Market psychology (fear vs greed)
- Considers gold-specific factors (safe-haven demand)
- Returns: BULLISH/BEARISH/NEUTRAL with confidence

**Prompt**: Expert gold market sentiment analyst with macroeconomic understanding

**Key Files**:
- `backend/agents/sentiment_analyst_agent.py`

---

### 5. Meta-Agent
**Role**: Judge/Coordinator

**Responsibilities**:
- Receives analysis from all 3 analysts
- Counts votes (BUY/SELL/NEUTRAL)
- Calculates weighted scores using configurable weights:
  - Visual: 35%
  - Technical: 40%
  - Sentiment: 25%
- Requires minimum consensus (2/3 analysts agree)
- Makes final trading decision
- Sends `TRADE_SIGNAL` to Risk Manager

**Decision Logic**:
```python
if consensus >= 2 and confidence >= 60%:
    approve_signal()
else:
    return NEUTRAL
```

**Key Files**:
- `backend/agents/meta_agent.py`

---

### 6. Risk Manager Agent
**Role**: Position Sizing & Risk Validation

**Responsibilities**:
- Validates trade signals:
  - Confidence threshold (default: 60%)
  - Daily loss limit (default: 5%)
  - Position limits
  - Portfolio exposure
- Calculates position sizing:
  - Risk per trade: 2% of account
  - Position size = Risk Amount / Stop Loss Distance
- Sets stop loss (1.5% default) and take profit (3% default)
- Risk/Reward ratio: 2:1
- Rejects trades that violate rules
- Sends `EXECUTION_REQUEST` to Execution Agent

**Key Files**:
- `backend/agents/risk_manager_agent.py`

---

### 7. Execution Agent
**Role**: Order Placement & Management

**Uses**: Interactive Brokers TWS API (ib_insync)

**Responsibilities**:
- Connects to TWS/IB Gateway
- Places market or limit orders
- Attaches stop loss and take profit orders
- Monitors open positions
- Reports execution results
- Sends `EXECUTION_RESULT` back to Risk Manager

**Key Files**:
- `backend/agents/execution_agent.py`

---

## Message Flow

```
SCANNER (every 15 min)
  └─> ANALYSIS_REQUEST (broadcast to all analysts)
        │
        ├─> VISUAL ANALYST
        │     └─> ANALYSIS_RESULT → META-AGENT
        │
        ├─> TECHNICAL ANALYST
        │     └─> ANALYSIS_RESULT → META-AGENT
        │
        └─> SENTIMENT ANALYST
              └─> ANALYSIS_RESULT → META-AGENT
                    │
                    └─> Meta-Agent waits for all 3 analysts
                          │
                          └─> TRADE_SIGNAL → RISK MANAGER
                                │
                                ├─> If APPROVED: EXECUTION_REQUEST → EXECUTION AGENT
                                │                   └─> EXECUTION_RESULT → RISK MANAGER
                                │
                                └─> If REJECTED: Log rejection reason
```

## Database Schema

### Core Tables

1. **agent_analyses**: Individual analyst results
2. **meta_decisions**: Meta-Agent final decisions with votes
3. **trade_signals**: Trade signals with risk approval
4. **executed_trades**: Actual trades with P&L
5. **chart_screenshots**: Screenshots for audit trail
6. **agent_performance**: Agent accuracy tracking
7. **daily_statistics**: Daily performance metrics
8. **system_logs**: System events and errors

### Key Views

- `v_recent_decisions`: Recent decisions with full context
- `v_open_positions`: Current open positions
- `v_trade_history`: Trade history with performance

**Schema File**: `backend/database/agent_schema.sql`

---

## API Endpoints

### Agent Control

```bash
POST /api/agents/initialize
  - Initialize all agents with configuration

POST /api/agents/start
  - Start agent system (activates scheduler)

POST /api/agents/stop
  - Stop agent system

GET /api/agents/status
  - Get comprehensive system status

POST /api/agents/scan
  - Manually trigger a market scan

GET /api/agents/risk
  - Get risk management status

GET /api/agents/positions
  - Get current open positions
```

---

## Configuration

### Agent Weights (Meta-Agent)
```python
{
    'visual': 0.35,      # 35% weight
    'technical': 0.40,   # 40% weight
    'sentiment': 0.25    # 25% weight
}
```

### Risk Parameters
```python
{
    'account_balance': 10000.0,
    'risk_per_trade': 0.02,          # 2% per trade
    'max_position_size': 0.30,       # 30% of account
    'max_daily_loss': 0.05,          # 5% daily loss limit
    'min_confidence': 60,            # Minimum 60% confidence
    'default_stop_loss_pct': 0.015,  # 1.5% stop loss
    'default_take_profit_pct': 0.03  # 3% take profit (2:1 R/R)
}
```

### TWS Connection
```python
{
    'tws_host': '127.0.0.1',
    'tws_port': 7497,  # 7497 = TWS live, 7496 = paper
    'client_id': 3
}
```

---

## Getting Started

### 1. Environment Variables

Create `.env` file:
```bash
ANTHROPIC_API_KEY=your_api_key_here
DATABASE_URL=postgresql://user:pass@localhost:5432/database
```

### 2. Initialize Database Schema

```bash
psql $DATABASE_URL -f backend/database/agent_schema.sql
```

### 3. Start the System

```python
from services.agent_orchestrator_service import get_orchestrator_service

# Initialize agents
service = get_orchestrator_service()
service.initialize_agents({
    'scanner': {'symbols': ['XAUUSD']},
    'risk_manager': {'account_balance': 10000.0}
})

# Start system (activates scheduler)
service.start()
```

### 4. Via API

```bash
# Initialize
curl -X POST http://localhost:8001/api/agents/initialize

# Start
curl -X POST http://localhost:8001/api/agents/start

# Check status
curl http://localhost:8001/api/agents/status

# Manual scan
curl -X POST http://localhost:8001/api/agents/scan
```

---

## How It Works

### Complete Trading Cycle (15 minutes)

1. **Scanner runs** (scheduled every 15 min)
   - Takes screenshot of XAUUSD chart
   - Checks for opportunities (breakouts, volume spikes)

2. **If opportunity detected**:
   - Scanner broadcasts `ANALYSIS_REQUEST` to all 3 analysts

3. **Analysts analyze in parallel**:
   - Visual Analyst: Analyzes chart patterns via Claude Vision
   - Technical Analyst: Calculates indicators (RSI, MACD, etc.)
   - Sentiment Analyst: Assesses market sentiment via Claude Text

4. **Meta-Agent receives all 3 opinions**:
   - Counts votes
   - Calculates weighted scores
   - Makes final decision
   - Sends `TRADE_SIGNAL` to Risk Manager

5. **Risk Manager validates**:
   - Checks confidence threshold
   - Checks daily loss limit
   - Calculates position size
   - Sets stop loss & take profit
   - Approves or rejects trade

6. **If approved, Execution Agent**:
   - Places order via TWS
   - Attaches SL/TP orders
   - Monitors position
   - Reports results

---

## Monitoring & Logging

### System Status
```python
service = get_orchestrator_service()
status = service.get_system_status()

print(status['is_running'])
print(status['agents'])
print(status['risk_manager'])
print(status['execution'])
```

### Risk Status
```python
risk_status = service.risk_manager.get_risk_status()

print(f"Daily P&L: ${risk_status['daily_pnl']}")
print(f"Trades Today: {risk_status['trades_today']}")
print(f"Rejected Trades: {risk_status['rejected_trades']}")
print(f"Open Positions: {risk_status['open_positions']}")
```

### Logs
```bash
tail -f logs/agent_system.log
```

---

## Testing

### Manual Scan
```bash
curl -X POST http://localhost:8001/api/agents/scan
```

### Check Analyst Responses
```sql
SELECT * FROM agent_analyses
WHERE timestamp > NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

### Check Meta-Agent Decisions
```sql
SELECT * FROM v_recent_decisions
ORDER BY timestamp DESC
LIMIT 10;
```

---

## Future Enhancements (Layer 2)

### Self-Evolving System
- Red vs Blue team debates
- Performance tracking & adaptation
- Agent weight adjustment based on accuracy
- Game theory agent
- Wyckoff analysis agent
- Order flow agent

**Note**: Layer 2 is not implemented yet. Focus is on Layer 1 operational system.

---

## Files Structure

```
backend/
├── agents/
│   ├── base_agent.py              # Base classes & message system
│   ├── scanner_agent.py           # Market monitoring
│   ├── visual_analyst_agent.py    # Chart pattern recognition
│   ├── technical_analyst_agent.py # Indicator analysis
│   ├── sentiment_analyst_agent.py # Market sentiment
│   ├── meta_agent.py              # Decision coordinator
│   ├── risk_manager_agent.py      # Risk management
│   ├── execution_agent.py         # Order execution
│   └── README.md                  # This file
├── services/
│   └── agent_orchestrator_service.py  # Main orchestrator
├── routes/
│   └── agent_routes.py            # API endpoints
└── database/
    └── agent_schema.sql           # Database schema
```

---

## Dependencies

```txt
anthropic>=0.45.0     # Claude API
ib_insync>=0.9.86    # Interactive Brokers
numpy>=1.24.0        # Technical calculations
psycopg2>=2.9.0      # PostgreSQL
apscheduler>=3.10.0  # Job scheduling
selenium>=4.0.0      # Screenshots
fastapi>=0.100.0     # API
```

---

## Support

For issues or questions:
- Check logs: `logs/agent_system.log`
- Check database: Query `system_logs` table
- Check agent status: `/api/agents/status`

---

## License

Proprietary - Internal Use Only
