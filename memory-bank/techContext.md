# Technical Context

## Last Updated
January 12, 2026

---

## Architecture Overview

### System Type
Event-driven, microservices-inspired architecture with:
- **Backend**: FastAPI REST API + WebSocket server
- **Frontend**: Vue.js SPA (Single Page Application)
- **Message Broker**: Apache Kafka
- **Database**: PostgreSQL with materialized views
- **External API**: Interactive Brokers TWS + Claude AI API

---

## Core Services

### 1. Market Data Collection
**Service**: `backend/services/tws_connector.py`
- Connects to Interactive Brokers Trader Workstation (TWS) using `ib_insync`
- Subscribes to real-time bar data (5-second bars)
- Handles connection management and reconnection logic

### 2. Kafka Producer
**Service**: `backend/services/kafka_producer.py`
- Receives market data from TWS connector
- Publishes to Kafka topic: `market-data`
- Ensures reliable message delivery

### 3. Kafka Consumer
**Service**: `backend/services/kafka_consumer.py`
- Consumes from `market-data` topic
- Dual-purpose consumer:
  - Writes data to PostgreSQL via `database_writer.py`
  - Broadcasts to WebSocket clients via `market_data_streamer.py`

### 4. Database Writer
**Service**: `backend/services/database_writer.py`
- Inserts real-time bars into `ohlcv_realtime_1min` table
- Handles duplicate detection
- Triggers materialized view refresh (every 5 minutes via APScheduler)

### 5. Market Data Streamer
**Service**: `backend/services/market_data_streamer.py`
- WebSocket server singleton
- Broadcasts real-time bars to connected frontend clients
- Manages WebSocket connections per symbol

### 6. Gap Detection & Backfill
**Services**:
- `backend/services/gap_detector.py` - SQL window functions to detect missing bars
- `backend/services/historical_backfill.py` - Fetches historical data from IB API
- **API Routes**: `backend/routes/data_management_routes.py`

### 7. Screenshot Service
**Service**: `backend/services/screenshot_service.py`
- Uses Selenium (headless Chrome) to capture chart screenshots
- Configurable: Selenium (default) or Playwright
- Screenshots sent to Vision Agent for analysis
- Currently points to: `http://localhost:5173`

---

## Database Architecture

### Connection Management
**Current State**: Mixed approach (needs consolidation)
- **Main API**: Uses psycopg2 connection pooling (`config/database.py`)
- **Agents**: Use psycopg2 with `get_cursor()` context manager
- **Configuration**: Database URL loaded from `.env` via `python-decouple`

### Tables
#### Real-Time Data
- `ohlcv_realtime_1min` - Live bars from Kafka stream

#### Historical Data
- `ohlcv_historical_1min` - Backfilled historical bars

#### Materialized Views (Auto-refresh every 5 min)
- `ohlcv_1min` - Union of realtime + historical
- `ohlcv_5min` - 5-minute aggregation
- `ohlcv_15min` - 15-minute aggregation
- `ohlcv_30min` - 30-minute aggregation
- `ohlcv_1h` - 1-hour aggregation
- `ohlcv_4h` - 4-hour aggregation
- `ohlcv_1d` - Daily aggregation

#### Agent System Tables
- `agent_analyses` - Individual analyst results
- `meta_decisions` - Meta-agent final decisions
- `trade_signals` - Signals with risk approval
- `executed_trades` - Actual trades with P&L
- `chart_screenshots` - Screenshot audit trail

### SQL Functions
- `refresh_all_timeframes()` - Refreshes all materialized views
- Called via APScheduler every 5 minutes

---

## Multi-Agent System

### Agent Types (Enum)
```python
class AgentType(Enum):
    SCANNER = "scanner"
    VISUAL_ANALYST = "visual_analyst"
    QUANT_ANALYST = "quant_analyst"
    SENTIMENT_ANALYST = "sentiment_analyst"
    PATTERN_RECOGNITION = "pattern_recognition"
    META_AGENT = "meta_agent"
    RISK_MANAGER = "risk_manager"
    EXECUTION = "execution"
```

### Message Types
```python
class MessageType(Enum):
    MARKET_SCAN = "market_scan"
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESULT = "analysis_result"
    TRADE_SIGNAL = "trade_signal"
    RISK_ASSESSMENT = "risk_assessment"
    EXECUTION_REQUEST = "execution_request"
    EXECUTION_RESULT = "execution_result"
    STATUS_UPDATE = "status_update"
```

### Agent Communication Flow
1. **Scanner Agent** runs every 15 minutes (APScheduler)
2. Captures screenshot + market data
3. Broadcasts `ANALYSIS_REQUEST` to all analysts
4. Analysts (Visual/Technical/Sentiment) respond with `ANALYSIS_RESULT`
5. **Meta Agent** aggregates results and sends `TRADE_SIGNAL`
6. **Risk Manager** validates and sends `EXECUTION_REQUEST`
7. **Execution Agent** places order and returns `EXECUTION_RESULT`

### Agent Orchestrator
**Service**: `backend/services/agent_orchestrator_service.py`
- Message broker for agent communication
- Manages agent lifecycle (activate/deactivate)
- Routes messages between agents
- Maintains message history (last 1000 messages)

---

## API Endpoints

### Chart Data
- `GET /api/chart-data/{symbol}/{timeframe}` - Fetch OHLCV bars
- `GET /api/symbols` - List available symbols
- `GET /api/latest/{symbol}` - Get latest bar
- `GET /api/stats` - Database statistics

### WebSocket
- `WS /ws/live-data/{symbol}` - Real-time bar streaming

### Streaming Control
- `POST /api/streaming/start` - Start market data service
- `POST /api/streaming/stop` - Stop streaming
- `POST /api/streaming/subscribe/{symbol}` - Subscribe to symbol
- `POST /api/streaming/unsubscribe/{symbol}` - Unsubscribe
- `GET /api/streaming/status` - Get streaming status

### Agent System
- `POST /api/agents/initialize` - Initialize all agents
- `POST /api/agents/start` - Start agent system
- `POST /api/agents/stop` - Stop agent system
- `GET /api/agents/status` - Get agent status
- `POST /api/agents/scan` - Manual market scan

### Data Management
- `GET /api/data/gaps/scan` - Scan for data gaps
- `GET /api/data/coverage/{symbol}` - Coverage statistics
- `POST /api/data/backfill` - Backfill historical data
- `GET /api/data/stats` - Database statistics

### Live Trading
- `POST /api/live/connect` - Connect to broker
- `POST /api/live/order` - Place order
- `GET /api/live/positions` - Get positions
- `POST /api/live/close/{id}` - Close position
- `GET /api/live/account` - Account info

---

## Frontend Architecture

### Technology
- **Framework**: Vue 3 (Composition API)
- **Build Tool**: Vite
- **State Management**: Pinia stores
- **Routing**: Vue Router
- **Charting**: TradingView Lightweight Charts

### Key Components
- `ChartArea.vue` - Main chart component with TradingView integration
- `TopBar/` - Symbol selector, timeframe switcher, indicators
- `MainNavigation.vue` - App navigation menu

### Views
- `ChartView.vue` - Main trading chart (default route)
- `LiveTradingView.vue` - Live trading interface
- `BacktestView.vue` - Backtesting interface

### State Management (Pinia)
- `candlesticksStore.js` - Chart data, WebSocket connection, timeframe switching

### WebSocket Integration
```javascript
// Connects to backend WebSocket
ws = new WebSocket(`ws://localhost:8001/ws/live-data/${symbol}`)
// Receives real-time bars and updates chart
```

---

## Configuration Files

### Backend
**File**: `backend/.env`
```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/trading_db
ANTHROPIC_API_KEY=sk-ant-api03-xxx
```

### Frontend
**File**: `frontend/.env`
```bash
VITE_API_URL=http://localhost:8001
```

### Docker Compose
**File**: `docker-compose.yml`
- Zookeeper (port 2181)
- Kafka (port 9092)
- Kafka UI (port 8080)

---

## Development Workflow

### Starting Services
1. Start Kafka: `docker-compose up -d`
2. Start Backend: `cd backend && source venv/bin/activate && python main.py`
3. Start Frontend: `cd frontend && npm run dev`
4. (Optional) Start TWS: Open Interactive Brokers Trader Workstation

### Useful Scripts
- `scripts/1-start-zookeeper.sh`
- `scripts/2-start-kafka.sh`
- `scripts/3-start-backend.sh`
- `scripts/4-start-frontend.sh`
- `scripts/start-all.sh` - Start everything

---

## Security Considerations

### API Keys
- Anthropic API key stored in `.env` (not committed to git)
- `.gitignore` excludes `.env` files

### Database
- Connection pooling prevents connection exhaustion
- Parameterized queries prevent SQL injection

### WebSocket
- CORS configured for allowed origins only
- No authentication yet (TODO for production)

---

## Performance Optimizations

### Database
- Materialized views cache aggregated timeframes
- Indexes on `(symbol, timestamp)` for fast queries
- Automatic refresh every 5 minutes balances freshness vs load

### Frontend
- TradingView Lightweight Charts handles 10,000+ bars efficiently
- WebSocket streaming updates only changed bars
- Pinia reactive state management

### Kafka
- Asynchronous message passing decouples services
- Buffer prevents data loss during service restarts

---

## Known Technical Debt

1. **Database Config Split**: Consolidate psycopg2 vs SQLAlchemy
2. **Screenshot Service**: Requires frontend running (deploy frontend first)
3. **Error Handling**: Need circuit breakers for external API failures
4. **Testing**: Need comprehensive test suite for agents
5. **Monitoring**: No Prometheus/Grafana integration yet

---

## Dependencies

### Python Requirements
See: `backend/requirements.txt`
- fastapi, uvicorn (web framework)
- psycopg2-binary (PostgreSQL)
- anthropic (Claude AI)
- ib_insync (Interactive Brokers)
- kafka-python (Kafka client)
- pandas, numpy, pandas-ta (data processing)
- apscheduler (task scheduling)

### Node Packages
See: `frontend/package.json`
- vue, vue-router, pinia
- lightweight-charts (TradingView)
- vite (build tool)

---

## Deployment Considerations

### Current State
- Local development environment
- Services run on localhost
- Screenshot service expects `http://localhost:5173`

### Production Requirements
1. Deploy frontend to hosting (Vercel/Netlify/cloud)
2. Update screenshot service URL to hosted frontend
3. Deploy backend to cloud (AWS/GCP/Azure)
4. Migrate PostgreSQL to managed database
5. Use managed Kafka (Confluent Cloud) or deploy Kafka cluster
6. Add authentication/authorization
7. SSL/TLS for all connections
8. Environment-specific configuration

---

## Logging & Debugging

### Backend Logs
- Console output from `python main.py`
- Log level: INFO (configurable via `logging.basicConfig`)

### Kafka Logs
```bash
docker logs kafka
docker logs zookeeper
```

### Database Queries
- Use `psql` to connect and inspect tables
- Check materialized view refresh times

### Frontend DevTools
- Vue DevTools browser extension
- Network tab for WebSocket messages
- Console logs from Pinia store actions

---

## Future Enhancements

### Short Term
- Add comprehensive error handling
- Implement agent performance metrics
- Add unit tests for all agents
- Consolidate database configuration

### Medium Term
- Integrate backtester with agent system
- Add agent self-improvement (Layer 2)
- Build performance analytics dashboard
- Implement alerting system

### Long Term
- Deploy to production
- Add multiple asset class support
- Implement portfolio management
- Machine learning model integration
