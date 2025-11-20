#!/bin/bash
# MANUAL PROJECT SETUP SCRIPT
# Run this on your local machine to create the entire project structure

echo "Creating Customer Service AI Project Structure..."

# Create main directory
mkdir -p customer-service-ai
cd customer-service-ai

# Create backend structure
mkdir -p backend/{app/{agents,api,chains,models,utils},data/mock_documents/{billing,technical,policy},scripts}

echo "✓ Created backend directories"

# Create frontend structure  
mkdir -p frontend/src/{app,components/ui,lib}

echo "✓ Created frontend directories"

echo ""
echo "Project structure created!"
echo "Next: I'll provide you with the actual file contents to copy-paste"
echo ""
echo "Directory structure:"
tree -L 3 -I 'node_modules|venv|__pycache__' . || find . -type d -maxdepth 3

