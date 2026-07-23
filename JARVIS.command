#!/bin/bash
# J.A.R.V.I.S. — One-click start
# Double-click this file to launch everything

DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill old server
lsof -ti:7777 | xargs kill 2>/dev/null
sleep 0.5

# Start server in background
cd "$DIR"
/usr/bin/python3 server.py &
SERVER_PID=$!

# Wait for server
sleep 2

# Check
if curl -s http://127.0.0.1:7777/api/ping > /dev/null 2>&1; then
    # Open browser
    open "$DIR/index.html"

    # Keep alive
    echo "JARVIS running (PID: $SERVER_PID)"
    wait $SERVER_PID
else
    echo "Server failed to start"
    exit 1
fi
