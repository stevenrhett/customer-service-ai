#!/bin/bash
# Show Directory Tree
# Shows directory structure in a tree format

DEPTH=${1:-2}

if command -v tree &> /dev/null; then
    tree -L $DEPTH -I 'node_modules|__pycache__|.git|.next|dist|build'
else
    echo "Install 'tree' command for better output: brew install tree"
    echo ""
    find . -maxdepth $DEPTH -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/__pycache__/*' | head -50
fi

