#!/bin/bash
# Create .gitignore
# Creates a comprehensive .gitignore file for common project types

if [ -f .gitignore ]; then
    read -p ".gitignore already exists. Overwrite? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
env/
ENV/
.venv

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
.npm
.yarn-integrity
.next/
out/
dist/
build/

# Environment variables
.env
.env.local
.env.*.local
.envrc

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/
.nox/
coverage.xml
*.cover
.hypothesis/

# Logs
*.log
logs/

# OS
Thumbs.db
.DS_Store
EOF

echo "✓ Created comprehensive .gitignore file"

