#!/bin/bash
# Create Python Virtual Environment
# Creates a Python virtual environment in current directory

if [ -d "venv" ] || [ -d ".venv" ]; then
    echo "Virtual environment already exists"
    exit 1
fi

echo "Creating Python virtual environment..."
python3 -m venv venv
echo "✓ Virtual environment created"
echo ""
echo "To activate:"
echo "  source venv/bin/activate"

