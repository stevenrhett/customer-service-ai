#!/bin/bash
# Check Port Usage
# Shows what's running on common development ports

echo "=== Port Usage ==="
echo ""

PORTS=(3000 3001 8000 8001 8080 5000 5001 5173 4000 4001)

for port in "${PORTS[@]}"; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :$port -sTCP:LISTEN -t)
        PROCESS=$(ps -p $PID -o comm= 2>/dev/null)
        echo "Port $port: ✓ In use (PID: $PID, Process: $PROCESS)"
    else
        echo "Port $port: ✓ Available"
    fi
done

