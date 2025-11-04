#!/bin/bash

# Quick Start Script for Customer Service AI
# This script helps you set up and run the application quickly

set -e

echo "====================================="
echo "Customer Service AI - Quick Start"
echo "====================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.10 or higher."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

echo "✓ Python and Node.js found"
echo ""

# Ask user what they want to do
echo "What would you like to do?"
echo "1) First-time setup (install dependencies and ingest data)"
echo "2) Start backend only"
echo "3) Start frontend only"
echo "4) Start both backend and frontend"
echo "5) Re-ingest data"
echo ""
read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Starting first-time setup..."
        echo ""
        
        # Backend setup
        echo "📦 Setting up backend..."
        cd backend
        
        if [ ! -d "venv" ]; then
            echo "Creating virtual environment..."
            python3 -m venv venv
        fi
        
        echo "Activating virtual environment..."
        source venv/bin/activate
        
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
        
        echo ""
        echo "⚠️  IMPORTANT: Please configure your .env file with API keys"
        echo "   Location: backend/.env"
        echo ""
        read -p "Press Enter once you've configured backend/.env..."
        
        echo ""
        echo "Ingesting data into vector database..."
        python scripts/ingest_data.py
        
        cd ..
        
        # Frontend setup
        echo ""
        echo "📦 Setting up frontend..."
        cd frontend
        
        echo "Installing Node.js dependencies..."
        npm install
        
        cd ..
        
        echo ""
        echo "✅ Setup complete!"
        echo ""
        echo "To start the application:"
        echo "  Backend:  cd backend && source venv/bin/activate && python -m app.main"
        echo "  Frontend: cd frontend && npm run dev"
        echo ""
        echo "Or run this script again and choose option 4"
        ;;
        
    2)
        echo ""
        echo "Starting backend server..."
        cd backend
        source venv/bin/activate
        python -m app.main
        ;;
        
    3)
        echo ""
        echo "Starting frontend development server..."
        cd frontend
        npm run dev
        ;;
        
    4)
        echo ""
        echo "Starting both backend and frontend..."
        echo ""
        echo "Opening backend in a new terminal..."
        
        # This will work on macOS, adjust for other systems if needed
        osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'/backend\" && source venv/bin/activate && python -m app.main"' &
        
        sleep 2
        
        echo "Opening frontend in a new terminal..."
        osascript -e 'tell app "Terminal" to do script "cd \"'$(pwd)'/frontend\" && npm run dev"' &
        
        echo ""
        echo "✅ Both services starting in separate terminal windows"
        echo "   Backend: http://localhost:8000"
        echo "   Frontend: http://localhost:3000"
        ;;
        
    5)
        echo ""
        echo "Re-ingesting data..."
        cd backend
        source venv/bin/activate
        python scripts/ingest_data.py
        echo ""
        echo "✅ Data re-ingested successfully"
        ;;
        
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
