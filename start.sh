#!/bin/bash
# J.A.R.V.I.S. — Auto-start
DIR="$(cd "$(dirname "$0")" && pwd)"

# Kill old server
lsof -ti:7777 | xargs kill 2>/dev/null
sleep 0.5

# Start server
cd "$DIR"
python3 server.py &
SERVER_PID=$!

sleep 2

# Check
if curl -s http://127.0.0.1:7777/api/ping > /dev/null 2>&1; then
    echo "✅ J.A.R.V.I.S. online (PID: $SERVER_PID)"
else
    echo "❌ Server failed"
    exit 1
fi

# Open browser
open "$DIR/index.html"

echo "🤖 Good evening, Sir."
wait $SERVER_PID
