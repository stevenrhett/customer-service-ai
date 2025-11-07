#!/bin/bash
# List Large Files
# Lists the largest files in current directory

if [ -z "$1" ]; then
    LIMIT=10
else
    LIMIT=$1
fi

echo "=== Top $LIMIT Largest Files ==="
find . -type f -not -path "./*/node_modules/*" -not -path "./.git/*" -exec du -h {} \; | sort -rh | head -$LIMIT

