#!/bin/bash
# Find Files by Name
# Quickly find files by name pattern

if [ -z "$1" ]; then
    echo "Usage: find-file.sh <filename-pattern>"
    exit 1
fi

echo "Searching for: $1"
find . -type f -iname "*$1*" 2>/dev/null | head -20

