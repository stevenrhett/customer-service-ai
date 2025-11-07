#!/bin/bash
# Quick Git Status
# Shows git status in a concise format

if [ -d .git ]; then
    echo "=== Git Status ==="
    git status -sb
    echo ""
    echo "=== Recent Commits ==="
    git log --oneline -5
else
    echo "Not a git repository"
fi

