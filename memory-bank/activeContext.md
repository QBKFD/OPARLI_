# Active Context

## Last Updated
January 12, 2026

---

## Current Development Phase
**Phase 1**: Building Core Infrastructure & Testing Agent System

---

## Recent Work (Last Session)

### Completed
1. ✅ Cleaned up deprecated code (moved to `_archive/`)
2. ✅ Set up memory-bank documentation system
3. ✅ Documented system architecture in `md/SYSTEM_ARCHITECTURE.md`
4. ✅ Established agent communication patterns
5. ✅ Implemented screenshot service with Selenium
6. ✅ Created data gap detection and backfill system
7. ✅ Built real-time data streaming pipeline (TWS → Kafka → PostgreSQL → WebSocket)

### In Progress
1. 🔄 Testing agent system end-to-end
2. 🔄 Validating screenshot service with Vision Agent
3. 🔄 Consolidating database configuration (psycopg2 vs SQLAlchemy)

---

## Current Priority Tasks

### High Priority (This Week)
1. **Test Multi-Agent System**
   - Initialize all 7 agents
   - Run manual scan to trigger agent workflow
   - Verify Vision Agent receives screenshots correctly
   - Validate Meta Agent decision-making logic
   - Test Risk Manager position sizing calculations

2. **Screenshot Service Validation**
   - Ensure frontend chart renders correctly at `http://localhost:5173`
   - Test Selenium captures chart properly
   - Verify base64 encoding/decoding
   - Test with different timeframes (1min, 5min, 15min, etc.)

3. **Database Consolidation**
   - Decide: Keep psycopg2 or migrate to SQLAlchemy
   - Update all services to use chosen approach
   - Test connection pooling under load

### Medium Priority (Next 2 Weeks)
4. **Agent Performance Metrics**
   - Track individual analyst accuracy
   - Measure Meta Agent decision quality
   - Log response times per agent

5. **Error Handling & Resilience**
   - Add retry logic for Anthropic API calls
   - Implement circuit breakers for TWS connection
   - Handle Kafka consumer failures gracefully

6. **Frontend Agent Integration**
   - Add agent status display to LiveTradingView
   - Show recent agent decisions on chart
   - Display Meta Agent reasoning in UI

### Low Priority (Future)
7. **Backtester Integration**
   - Connect backtester indicators to Technical Analyst
   - Add historical strategy testing
   - Compare backtest vs live performance

8. **Production Deployment**
   - Deploy frontend (Vercel/Netlify)
   - Update screenshot service URL
   - Set up cloud PostgreSQL
   - Configure managed Kafka

---

## Known Issues & Blockers

### Critical Issues
1. **Screenshot Service Dependency**
   - **Issue**: Vision Agent requires frontend to be running for screenshots
   - **Impact**: Agent system can't run independently
   - **Solution**: Deploy frontend to stable URL or create lightweight chart server
   - **Status**: Workaround in place (localhost), needs production fix

2. **Interactive Brokers Rate Limits**
   - **Issue**: Historical backfill hits pacing violations (max 60 requests/10min)
   - **Impact**: Slow gap filling, can take hours for large gaps
   - **Solution**: Implemented delay logic, but still constrained
   - **Status**: Acceptable for now, consider alternative data sources

### Minor Issues
3. **Database Configuration Split**
   - **Issue**: Some code uses psycopg2, some uses SQLAlchemy
   - **Impact**: Maintenance complexity, potential connection leaks
   - **Solution**: Consolidate to single approach
   - **Status**: Documented, scheduled for cleanup

4. **No Authentication**
   - **Issue**: API endpoints have no authentication
   - **Impact**: Security risk in production
   - **Solution**: Add JWT auth before deployment
   - **Status**: Acceptable for local dev, blocker for production

5. **Limited Error Handling**
   - **Issue**: Many services lack comprehensive error handling
   - **Impact**: Services crash on unexpected errors
   - **Solution**: Add try-catch blocks, logging, retries
   - **Status**: Ongoing improvement

---

## Git Status Summary
```
Modified:
- backend/main.py (added new routes)
- frontend/src/App.vue (updated navigation)
- frontend/src/components/Chart/ChartArea.vue (chart updates)

Deleted (archived):
- source/ folder → _archive/
- data_script.py → _archive/
- README.md (old version)

New (untracked):
- backend/agents/ (all agent files)
- backend/services/ (new services)
- memory-bank/ (this documentation)
- docker-compose.yml
- scripts/ (startup scripts)
```

---

## Environment Status

### Services Currently Running (Typical Dev Session)
- ❓ PostgreSQL: Check with `psql -U user -d trading_db`
- ❓ Kafka + Zookeeper: Check with `docker ps`
- ❓ Backend API: Check `http://localhost:8001/`
- ❓ Frontend: Check `http://localhost:5173/`
- ❓ TWS (Interactive Brokers): Check GUI application

### Services Not Yet Started
- Agent System: Need to call `POST /api/agents/initialize` then `/api/agents/start`
- Market Data Streaming: Need to call `POST /api/streaming/start`

---

## Data Status

### Available Symbols (Example)
- XAUUSD (Gold)
- ES (E-mini S&P 500)
- NQ (E-mini NASDAQ)
- [Check with `GET /api/symbols`]

### Data Coverage
- Real-time data: Only when streaming service is active
- Historical data: Depends on backfill operations
- Check coverage: `GET /api/data/coverage/{symbol}`

---

## Next Steps for New AI Agent

When a new AI agent starts a session, they should:

1. **Understand Current State**
   - Read all memory-bank files (you're doing this now!)
   - Check git status: `git status`
   - Review recent git commits: `git log --oneline -10`

2. **Verify Environment**
   - Check if services are running: `docker ps`, `curl http://localhost:8001/`
   - Verify database connection: Query `/api/stats`
   - Check Kafka: `curl http://localhost:8080` (Kafka UI)

3. **Ask User for Context**
   - What were they working on last?
   - What do they want to work on now?
   - Are there any immediate issues?

4. **Update This File**
   - Move completed tasks from "In Progress" to "Completed"
   - Add new tasks based on user input
   - Update "Recent Work" section
   - Update date at top

---

## Important Notes for Future Agents

### Code Style Preferences
- Python: Use type hints, docstrings for all functions
- Vue: Composition API (not Options API)
- SQL: Parameterized queries always
- Error handling: Log errors with context, don't silently fail

### Testing Philosophy
- Test agents with manual API calls first
- Use `curl` or Postman for endpoint testing
- Check database after agent runs to verify data written
- Monitor logs for errors

### Communication Patterns
- Agent messages are broadcast or targeted (see systemPatterns.md)
- All communication goes through Agent Orchestrator
- Messages stored in database for audit trail

### Deployment Strategy
- Local dev first (current stage)
- Paper trading testing (next stage)
- Live trading with small positions (final stage)
- Never skip testing phases

---

## Quick Reference Commands

### Start Everything
```bash
# From project root
docker-compose up -d  # Kafka + Zookeeper
cd backend && source venv/bin/activate && python main.py  # Backend
cd frontend && npm run dev  # Frontend (new terminal)
```

### Initialize Agents
```bash
curl -X POST http://localhost:8001/api/agents/initialize
curl -X POST http://localhost:8001/api/agents/start
curl http://localhost:8001/api/agents/status
```

### Start Data Streaming
```bash
curl -X POST http://localhost:8001/api/streaming/start
curl -X POST "http://localhost:8001/api/streaming/subscribe/XAUUSD?bar_size=5&sec_type=CMDTY&exchange=SMART&currency=USD"
```

### Check System Status
```bash
curl http://localhost:8001/api/stats  # Database stats
curl http://localhost:8001/api/agents/status  # Agent status
curl http://localhost:8001/api/streaming/status  # Streaming status
docker ps  # Check Kafka containers
```

### Database Access
```bash
psql -U <user> -d trading_db
# Then run queries:
SELECT symbol, COUNT(*) FROM ohlcv_1min GROUP BY symbol;
SELECT * FROM agent_analyses ORDER BY timestamp DESC LIMIT 10;
```

---

## Context for Specific Questions

### "How do I test the Vision Agent?"
1. Start frontend: `cd frontend && npm run dev`
2. Initialize agents: `curl -X POST http://localhost:8001/api/agents/initialize`
3. Start agents: `curl -X POST http://localhost:8001/api/agents/start`
4. Trigger scan: `curl -X POST http://localhost:8001/api/agents/scan`
5. Check database: `SELECT * FROM chart_screenshots ORDER BY captured_at DESC LIMIT 1;`
6. Check agent analyses: `SELECT * FROM agent_analyses WHERE analyst = 'visual' ORDER BY timestamp DESC LIMIT 1;`

### "How do I add a new symbol?"
1. Ensure TWS is running and connected
2. Start streaming: `curl -X POST http://localhost:8001/api/streaming/start`
3. Subscribe to symbol with correct parameters:
   ```bash
   # For stocks:
   curl -X POST "http://localhost:8001/api/streaming/subscribe/AAPL?bar_size=5&sec_type=STK"

   # For commodities (like gold):
   curl -X POST "http://localhost:8001/api/streaming/subscribe/XAUUSD?bar_size=5&sec_type=CMDTY"

   # For futures:
   curl -X POST "http://localhost:8001/api/streaming/subscribe/ES?bar_size=5&sec_type=FUT"
   ```
4. Verify data flowing: `curl http://localhost:8001/api/latest/AAPL`

### "How do I backfill historical data?"
1. Check gaps: `curl http://localhost:8001/api/data/gaps/scan`
2. Backfill: `curl -X POST "http://localhost:8001/api/data/backfill?symbol=XAUUSD&start_date=2025-01-01&end_date=2025-01-10"`
3. Monitor progress in backend logs
4. Note: IB API limits to ~60 requests per 10 minutes

---

## Conversation Context

### Memory Bank Purpose
This memory-bank system allows continuity across AI agent sessions. Each new agent can read these files to understand:
- What the project is (projectbrief.md)
- How it's built (techContext.md)
- What's happening now (activeContext.md - this file)
- How components interact (systemPatterns.md)

### User's Intent
The user wants to:
1. Build a fully autonomous trading system
2. Use AI agents that collaborate like a trading team
3. Have the system learn and improve over time (Layer 2 - future)
4. Eventually run this 24/7 in production
5. Maintain context across multiple AI coding sessions

### Communication Style
- User prefers technical, detailed explanations
- Appreciates documentation and organization
- Values understanding "how it works" not just "it works"
- Comfortable with command-line tools and APIs
- Wants to learn and understand the architecture

---

## End of Active Context

**Remember**: Always update this file when completing tasks or starting new work!