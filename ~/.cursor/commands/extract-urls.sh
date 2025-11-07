#!/bin/bash
# Extract URLs from Text
# Extracts URLs from clipboard or stdin

if [ -p /dev/stdin ]; then
    INPUT=$(cat)
else
    INPUT=$(pbpaste 2>/dev/null || echo "")
fi

if [ -z "$INPUT" ]; then
    echo "No input found. Paste text with URLs or pipe text to this command."
    exit 1
fi

echo "=== Extracted URLs ==="
echo "$INPUT" | grep -oE 'https?://[^[:space:]]+' | sort -u

