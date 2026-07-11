#!/bin/bash
# Master Startup Script - Launches all services in separate terminals
# This uses AppleScript to open Terminal windows on macOS

PROJECT_DIR="/Users/x/Desktop/algo_project"
SCRIPTS_DIR="$PROJECT_DIR/scripts"

echo "🚀 Starting Algo Trading System..."
echo ""
echo "This will open 4 terminal windows:"
echo "  1. Zookeeper"
echo "  2. Kafka"
echo "  3. Backend API"
echo "  4. Frontend"
echo ""
echo "⚠️  Make sure TWS/Gateway is running and logged in!"
echo ""
read -p "Press Enter to continue..."

# Terminal 1 - Zookeeper
osascript <<END
tell application "Terminal"
    do script "cd '$SCRIPTS_DIR' && ./1-start-zookeeper.sh"
    set custom title of front window to "ZOOKEEPER"
end tell
END

echo "✅ Zookeeper starting..."
sleep 5

# Terminal 2 - Kafka
osascript <<END
tell application "Terminal"
    do script "cd '$SCRIPTS_DIR' && ./2-start-kafka.sh"
    set custom title of front window to "KAFKA"
end tell
END

echo "✅ Kafka starting..."
sleep 10

# Terminal 3 - Backend
osascript <<END
tell application "Terminal"
    do script "cd '$SCRIPTS_DIR' && ./3-start-backend.sh"
    set custom title of front window to "BACKEND"
end tell
END

echo "✅ Backend starting..."
sleep 5

# Terminal 4 - Frontend
osascript <<END
tell application "Terminal"
    do script "cd '$SCRIPTS_DIR' && ./4-start-frontend.sh"
    set custom title of front window to "FRONTEND"
end tell
END

echo ""
echo "✅ All services starting in separate terminals!"
echo ""
echo "📊 Wait 30 seconds, then open: http://localhost:5173"
echo ""
echo "To stop: Press Ctrl+C in each terminal window"
