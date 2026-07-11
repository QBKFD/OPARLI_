# Project Brief

## Project Name
**algo_project** - Multi-Agent Algorithmic Trading System

## Last Updated
January 12, 2026

## Project Overview
A sophisticated algorithmic trading platform that combines:
- Real-time market data streaming from Interactive Brokers (TWS)
- Multi-agent AI system using Claude API (Vision + Text models) for trading decisions
- Event-driven architecture using Kafka for inter-service communication
- Vue.js frontend with TradingView Lightweight Charts for visualization
- PostgreSQL database with optimized materialized views for multiple timeframes

## Core Purpose
Build an autonomous trading system where multiple AI agents analyze markets from different perspectives (visual chart patterns, technical indicators, sentiment analysis) and collaboratively make informed trading decisions with proper risk management.

## Key Features
1. **Multi-Agent Decision Making**: 7 specialized agents work together
2. **Real-Time Data Streaming**: Live market data via Interactive Brokers
3. **AI-Powered Analysis**: Claude Vision API for chart pattern recognition
4. **Automated Gap Filling**: Detects and backfills missing historical data
5. **Risk Management**: Position sizing, stop-loss, take-profit validation
6. **Live Trading Interface**: Web-based UI for monitoring and control

## Technology Stack
### Backend
- Python 3.13
- FastAPI (REST API + WebSockets)
- psycopg2 (Database connection pooling)
- ib_insync (Interactive Brokers API)
- kafka-python (Message queue)
- anthropic (Claude AI API)
- pandas-ta (Technical indicators)
- APScheduler (Task scheduling)

### Frontend
- Vue 3 + Vite
- TradingView Lightweight Charts
- Pinia (State management)
- Vue Router

### Infrastructure
- PostgreSQL (Time-series data storage)
- Apache Kafka + Zookeeper (Docker containers)
- Selenium/Playwright (Chart screenshots)

### Development Environment
- macOS (Darwin 21.6.0)
- Python venv
- Node.js/npm

## Project Goals
### Phase 1 (Current)
- Establish reliable real-time data streaming
- Implement multi-agent decision system
- Test agents with paper trading
- Build monitoring dashboard

### Phase 2 (Future)
- Deploy to production (cloud hosting)
- Implement self-evolving system (agents that improve themselves)
- Add backtesting integration
- Performance analytics dashboard

## Critical Design Decisions
1. **Event-Driven Architecture**: Kafka ensures reliable message passing between services
2. **Agent-Based AI**: Multiple specialized agents prevent single-point-of-failure
3. **Database Optimization**: Materialized views for fast chart data retrieval
4. **API-First Design**: FastAPI enables easy integration and testing

## Known Challenges
1. Interactive Brokers API rate limits (pacing violations during backfill)
2. Screenshot service requires running frontend for chart capture
3. Database configuration split (psycopg2 vs SQLAlchemy - consolidation needed)
4. Agent system needs end-to-end testing before live trading

## Repository Location
`/Users/x/Desktop/algo_project`

## Main Entry Points
- Backend API: `backend/main.py` (port 8001)
- Frontend: `frontend/src/main.js` (port 5173)
- Agent System: `backend/routes/agent_routes.py`
- Live Trading: `backend/live_trading.py`
