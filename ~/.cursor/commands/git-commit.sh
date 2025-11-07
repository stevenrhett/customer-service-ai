#!/bin/bash
# Quick Git Commit
# Stages all changes and commits with a message

if [ -z "$1" ]; then
    echo "Usage: git-commit.sh <commit-message>"
    exit 1
fi

git add -A
git commit -m "$1"
echo "✓ Committed: $1"

