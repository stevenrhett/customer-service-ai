#!/bin/bash
# Clean Common Build Artifacts
# Removes common build artifacts and caches

echo "Cleaning build artifacts..."

# Python
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null

# Node.js
find . -type d -name "node_modules/.cache" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".next" -exec rm -rf {} + 2>/dev/null
find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null
find . -type d -name "build" -exec rm -rf {} + 2>/dev/null

# IDE
find . -type d -name ".vscode" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".idea" -exec rm -rf {} + 2>/dev/null

# OS
find . -type f -name ".DS_Store" -delete 2>/dev/null
find . -type f -name "Thumbs.db" -delete 2>/dev/null

echo "✓ Clean complete"

