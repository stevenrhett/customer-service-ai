#!/bin/bash
# Show Environment Info
# Shows useful environment information

echo "=== Environment Information ==="
echo ""
echo "OS: $(uname -s)"
echo "Architecture: $(uname -m)"
echo "Shell: $SHELL"
echo ""

# Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "Python: $PYTHON_VERSION"
else
    echo "Python: Not found"
fi

# Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    echo "Node.js: $NODE_VERSION"
    echo "npm: $NPM_VERSION"
else
    echo "Node.js: Not found"
fi

# Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version)
    echo "Git: $GIT_VERSION"
else
    echo "Git: Not found"
fi

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "Docker: $DOCKER_VERSION"
else
    echo "Docker: Not found"
fi

echo ""
echo "Current Directory: $(pwd)"

