#!/bin/bash

# Customer Service AI - Quick Start Script
# Automated setup and launch script for the Customer Service AI application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Customer Service AI - Quick Start${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 is not installed${NC}"
    echo "  Please install Python 3.10 or higher: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
if (( $(echo "$PYTHON_VERSION < 3.10" | bc -l) )); then
    echo -e "${RED}✗ Python 3.10+ required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}✗ Node.js is not installed${NC}"
    echo "  Please install Node.js 18 or higher: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}✗ Node.js 18+ required. Found: $(node --version)${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2)${NC}"
echo -e "${GREEN}✓ Node.js $(node --version)${NC}"
echo ""

# Menu
echo "What would you like to do?"
echo "  1) First-time setup (install dependencies, configure, ingest data)"
echo "  2) Start backend server"
echo "  3) Start frontend server"
echo "  4) Start both servers (requires 2 terminals)"
echo "  5) Re-ingest data into vector database"
echo "  6) Run tests"
echo "  7) Docker setup (build and start)"
echo ""
read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}Starting first-time setup...${NC}"
        echo ""
        
        # Backend setup
        echo -e "${YELLOW}📦 Setting up backend...${NC}"
        cd "$PROJECT_ROOT/backend"
        
        if [ ! -d "venv" ]; then
            echo "Creating Python virtual environment..."
            python3 -m venv venv
        fi
        
        echo "Activating virtual environment..."
        source venv/bin/activate
        
        echo "Upgrading pip..."
        pip install --upgrade pip --quiet
        
        echo "Installing Python dependencies..."
        pip install -r requirements.txt --quiet
        
        echo -e "${GREEN}✓ Backend dependencies installed${NC}"
        
        # Check for .env file
        if [ ! -f ".env" ]; then
            echo ""
            echo -e "${YELLOW}⚠️  Creating .env file from template...${NC}"
            if [ -f ".env.example" ]; then
                cp .env.example .env
                echo -e "${YELLOW}⚠️  IMPORTANT: Please edit backend/.env with your API keys${NC}"
                echo "   Required: OPENAI_API_KEY, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
            else
                echo -e "${RED}✗ .env.example not found${NC}"
            fi
        else
            echo -e "${GREEN}✓ .env file exists${NC}"
        fi
        
        echo ""
        read -p "Press Enter once you've configured backend/.env (or Ctrl+C to cancel)..."
        
        echo ""
        echo "Ingesting data into vector database..."
        python scripts/ingest_data.py
        
        echo -e "${GREEN}✓ Data ingested successfully${NC}"
        cd "$PROJECT_ROOT"
        
        # Frontend setup
        echo ""
        echo -e "${YELLOW}📦 Setting up frontend...${NC}"
        cd "$PROJECT_ROOT/frontend"
        
        echo "Installing Node.js dependencies..."
        npm install --silent
        
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
        
        # Check for .env.local
        if [ ! -f ".env.local" ]; then
            echo ""
            echo -e "${YELLOW}⚠️  Creating .env.local from template...${NC}"
            if [ -f ".env.example" ]; then
                cp .env.example .env.local
                echo -e "${GREEN}✓ Frontend environment configured${NC}"
            fi
        fi
        
        cd "$PROJECT_ROOT"
        
        echo ""
        echo -e "${GREEN}✅ Setup complete!${NC}"
        echo ""
        echo "To start the application:"
        echo "  Option A: Run this script again and choose option 4"
        echo "  Option B: Manually start servers:"
        echo "    Backend:  cd backend && source venv/bin/activate && python -m app.main"
        echo "    Frontend: cd frontend && npm run dev"
        ;;
        
    2)
        echo ""
        echo -e "${BLUE}Starting backend server...${NC}"
        cd "$PROJECT_ROOT/backend"
        
        if [ ! -d "venv" ]; then
            echo -e "${RED}✗ Virtual environment not found. Run option 1 first.${NC}"
            exit 1
        fi
        
        source venv/bin/activate
        
        if [ ! -f ".env" ]; then
            echo -e "${RED}✗ .env file not found. Please configure it first.${NC}"
            exit 1
        fi
        
        echo "Backend starting on http://localhost:8000"
        echo "API docs available at http://localhost:8000/docs"
        echo ""
        python -m app.main
        ;;
        
    3)
        echo ""
        echo -e "${BLUE}Starting frontend development server...${NC}"
        cd "$PROJECT_ROOT/frontend"
        
        if [ ! -d "node_modules" ]; then
            echo -e "${RED}✗ Dependencies not installed. Run option 1 first.${NC}"
            exit 1
        fi
        
        echo "Frontend starting on http://localhost:3000"
        echo ""
        npm run dev
        ;;
        
    4)
        echo ""
        echo -e "${BLUE}Starting both servers...${NC}"
        echo ""
        echo -e "${YELLOW}This will open two terminal windows${NC}"
        echo ""
        
        # Detect OS and open terminals accordingly
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            osascript -e "tell app \"Terminal\" to do script \"cd '$PROJECT_ROOT/backend' && source venv/bin/activate && echo 'Backend starting on http://localhost:8000' && python -m app.main\"" &
            sleep 1
            osascript -e "tell app \"Terminal\" to do script \"cd '$PROJECT_ROOT/frontend' && echo 'Frontend starting on http://localhost:3000' && npm run dev\"" &
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            gnome-terminal -- bash -c "cd '$PROJECT_ROOT/backend' && source venv/bin/activate && echo 'Backend starting on http://localhost:8000' && python -m app.main; exec bash" &
            sleep 1
            gnome-terminal -- bash -c "cd '$PROJECT_ROOT/frontend' && echo 'Frontend starting on http://localhost:3000' && npm run dev; exec bash" &
        else
            echo -e "${YELLOW}Please start servers manually in separate terminals:${NC}"
            echo "  Terminal 1: cd backend && source venv/bin/activate && python -m app.main"
            echo "  Terminal 2: cd frontend && npm run dev"
            exit 1
        fi
        
        echo -e "${GREEN}✅ Both services starting in separate terminal windows${NC}"
        echo "   Backend:  http://localhost:8000"
        echo "   Frontend: http://localhost:3000"
        echo "   API Docs: http://localhost:8000/docs"
        ;;
        
    5)
        echo ""
        echo -e "${BLUE}Re-ingesting data...${NC}"
        cd "$PROJECT_ROOT/backend"
        
        if [ ! -d "venv" ]; then
            echo -e "${RED}✗ Virtual environment not found. Run option 1 first.${NC}"
            exit 1
        fi
        
        source venv/bin/activate
        python scripts/ingest_data.py
        echo ""
        echo -e "${GREEN}✅ Data re-ingested successfully${NC}"
        ;;
        
    6)
        echo ""
        echo -e "${BLUE}Running tests...${NC}"
        echo ""
        
        # Backend tests
        echo -e "${YELLOW}Running backend tests...${NC}"
        cd "$PROJECT_ROOT/backend"
        if [ -d "venv" ]; then
            source venv/bin/activate
            pytest --quiet
        else
            echo -e "${RED}✗ Virtual environment not found${NC}"
        fi
        
        echo ""
        
        # Frontend tests
        echo -e "${YELLOW}Running frontend tests...${NC}"
        cd "$PROJECT_ROOT/frontend"
        if [ -d "node_modules" ]; then
            npm test -- --silent
        else
            echo -e "${RED}✗ Dependencies not installed${NC}"
        fi
        
        echo ""
        echo -e "${GREEN}✅ Tests completed${NC}"
        ;;
        
    7)
        echo ""
        echo -e "${BLUE}Docker setup...${NC}"
        cd "$PROJECT_ROOT"
        
        if ! command_exists docker; then
            echo -e "${RED}✗ Docker is not installed${NC}"
            echo "  Please install Docker: https://www.docker.com/get-started"
            exit 1
        fi
        
        if ! command_exists docker-compose; then
            echo -e "${RED}✗ Docker Compose is not installed${NC}"
            exit 1
        fi
        
        echo "Building and starting containers..."
        docker-compose up --build -d
        
        echo ""
        echo -e "${GREEN}✅ Docker containers started${NC}"
        echo "   Frontend: http://localhost:3000"
        echo "   Backend:  http://localhost:8000"
        echo "   API Docs: http://localhost:8000/docs"
        echo ""
        echo "View logs: docker-compose logs -f"
        echo "Stop:      docker-compose down"
        ;;
        
    *)
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac
