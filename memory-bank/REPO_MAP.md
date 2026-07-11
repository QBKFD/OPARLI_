# Repository Map

This document outlines the major components and directories within the `algo_project` repository.

## Top-Level Components

- `backend/`: Contains the core backend services, agents, and API routes for live trading and data management.
- `backtester/`: Houses the backtesting framework, including data handlers, indicators, portfolio management, and signal generation.
- `data/`: Stores historical and raw market data.
- `database/`: Contains database schemas and related files.
- `frontend/`: The user interface for the trading application, built with Vue.js.
- `kafka/`: Kafka installation directory, including binaries, configuration, and libraries for message queuing.
- `md/`: Markdown documentation for various aspects of the project, such as daily startup, deployment, and system architecture.
- `scripts/`: Utility scripts for starting services, importing data, and cloud setup.
- `trade_bot/`: (Currently empty) Placeholder for automated trading bot logic.
- `memory-bank/`: Documentation repository for project brief, system patterns, technical context, and active context.

## Root-Level Files

- `.gitignore`: Specifies intentionally untracked files to ignore.
- `docker-compose.yml`: Defines and runs multi-container Docker applications.
- `kafka_2.13-3.6.1.tgz`: The compressed archive of the Kafka installation.
