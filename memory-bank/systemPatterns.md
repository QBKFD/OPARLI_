# System Patterns

## Agent Data Flow: Vision Agent, Raw Data Agent, and Meta Trader Agent

This section details the data flow between key agents in the `algo_project` system: the Raw Data Agent (ScannerAgent), Vision Agent (VisualAnalystAgent), and Meta Trader Agent (MetaAgent).

### 1. Raw Data Agent (ScannerAgent)

**Role**: The ScannerAgent is responsible for continuously monitoring market conditions, gathering raw market data, and capturing visual chart information. It acts as the initial data provider for the analytical agents.

**Data Flow**: 
- The `ScannerAgent` periodically executes its `run` method (e.g., every 15 minutes).
- It fetches current `market_data` (price, volume, indicators) from the database using its internal `_get_current_market_data` method.
- It then captures a chart `screenshot` (base64 encoded) using a `screenshot_service` via its `_take_screenshot` method.
- A preliminary analysis is performed to detect simple trading `opportunity` using `_detect_opportunity`.
- If an opportunity is detected, the `ScannerAgent` broadcasts an `ANALYSIS_REQUEST` message to all analyzer agents.

**Outgoing Message (`ScannerAgent` -> All Analyzer Agents)**:
- **Type**: `MessageType.ANALYSIS_REQUEST`
- **Recipient**: `None` (broadcast)
- **Data Payload**: 
    - `symbol` (e.g., 'USGOLD')
    - `screenshot` (base64 encoded image of the chart)
    - `market_data` (current price, volume, SMA, etc.)
    - `opportunity_type` (e.g., 'price_breakout', 'volume_spike')
    - `confidence` (of the detected opportunity)
    - `scan_time`

### 2. Vision Agent (VisualAnalystAgent)

**Role**: The VisualAnalystAgent specializes in interpreting visual chart patterns and providing trading recommendations based on graphical analysis. It consumes raw visual data and provides a specialized analysis.

**Data Flow**: 
- The `VisualAnalystAgent` receives `ANALYSIS_REQUEST` messages from the `ScannerAgent` (or other agents requesting visual analysis).
- It extracts the `symbol`, `screenshot`, and `market_data` from the incoming message.
- It utilizes the Claude Vision API (`_analyze_chart`) to analyze the provided `screenshot` in conjunction with the `market_data`.
- The API returns a structured visual `analysis` including identified patterns, support/resistance levels, trend, and a trading `signal` with `confidence` and `reasoning`.
- The `VisualAnalystAgent` then sends an `ANALYSIS_RESULT` message containing its findings.

**Outgoing Message (`VisualAnalystAgent` -> Meta Trader Agent)**:
- **Type**: `MessageType.ANALYSIS_RESULT`
- **Recipient**: `AgentType.META_AGENT`
- **Data Payload**: 
    - `symbol`
    - `analyst`: 'visual'
    - `signal`: ('BUY', 'SELL', or 'NEUTRAL')
    - `confidence`: (0-100%)
    - `analysis`: (full structured analysis from Claude Vision API)

### 3. Meta Trader Agent (MetaAgent)

**Role**: The MetaAgent acts as the central decision-maker, aggregating and synthesizing analyses from multiple specialized agents (Visual, Technical, Sentiment). It weighs conflicting signals and makes a final, comprehensive trading decision.

**Data Flow**: 
- The `MetaAgent` receives `ANALYSIS_RESULT` messages from all analyzer agents, including the `VisualAnalystAgent` (as well as `TechnicalAnalystAgent` and `SentimentAnalystAgent`).
- It stores these individual analyses in its `pending_analyses` for the respective `symbol`.
- Once analyses from all configured analysts are received (`_all_analyses_received`), the `MetaAgent` invokes its `_make_decision` method.
- The `_make_decision` method processes the collected analyses by:
    - Counting `BUY`, `SELL`, and `NEUTRAL` votes.
    - Calculating weighted confidence scores based on predefined `weights` for each analyst's input.
    - Applying `min_confidence` and `min_consensus` thresholds to ensure robust decision-making.
    - Constructing a human-readable `reasoning` for the final decision.
- Finally, the `MetaAgent` sends a `TRADE_SIGNAL` message to the `RiskManagerAgent` with its conclusive trading decision.

**Outgoing Message (`MetaAgent` -> Risk Manager Agent)**:
- **Type**: `MessageType.TRADE_SIGNAL`
- **Recipient**: `AgentType.RISK_MANAGER`
- **Data Payload**: 
    - `symbol`
    - `signal`: ('BUY', 'SELL', or 'NEUTRAL')
    - `confidence`: (final calculated confidence)
    - `reasoning`: (explanation for the decision)
    - `decision`: (full decision dict, including analyst opinions, votes, and weighted scores)
    - `timestamp`
