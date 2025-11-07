#!/bin/bash
# Kill Process on Port
# Kills the process using a specific port

if [ -z "$1" ]; then
    echo "Usage: kill-port.sh <port-number>"
    exit 1
fi

PID=$(lsof -ti:$1)
if [ -z "$PID" ]; then
    echo "No process found on port $1"
else
    echo "Killing process $PID on port $1"
    kill -9 $PID
    echo "✓ Process killed"
fi

