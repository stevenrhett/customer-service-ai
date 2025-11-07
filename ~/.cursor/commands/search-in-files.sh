#!/bin/bash
# Search in Files
# Search for text pattern in files

if [ -z "$1" ]; then
    echo "Usage: search-in-files.sh <pattern>"
    exit 1
fi

echo "Searching for: $1"
grep -r --color=always -n "$1" . --exclude-dir=node_modules --exclude-dir=.git --exclude-dir=__pycache__ 2>/dev/null | head -30

