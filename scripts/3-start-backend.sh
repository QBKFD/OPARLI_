#!/bin/bash
# Start Backend API (Terminal 3)

echo "🚀 Starting Backend API..."
cd "$(dirname "$0")/backend"
python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
