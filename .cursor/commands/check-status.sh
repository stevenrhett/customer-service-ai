# Check Project Status
# Checks if backend and frontend are running and verifies setup

echo "=== Checking Project Status ==="
echo ""

# Check backend
echo "Backend:"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Backend is running on http://localhost:8000"
else
    echo "✗ Backend is not running"
fi

echo ""

# Check frontend
echo "Frontend:"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "✓ Frontend is running on http://localhost:3000"
else
    echo "✗ Frontend is not running"
fi

echo ""

# Check vector database
echo "Vector Database:"
if [ -d "backend/chroma_db" ]; then
    echo "✓ ChromaDB directory exists"
    COLLECTIONS=$(ls backend/chroma_db 2>/dev/null | wc -l)
    echo "  Collections found: $COLLECTIONS"
else
    echo "✗ ChromaDB directory not found - run ingest-data"
fi

echo ""

# Check environment files
echo "Environment Files:"
if [ -f "backend/.env" ]; then
    echo "✓ Backend .env exists"
else
    echo "✗ Backend .env missing - create it with API keys"
fi

if [ -f "frontend/.env.local" ]; then
    echo "✓ Frontend .env.local exists"
else
    echo "✗ Frontend .env.local missing - create it with NEXT_PUBLIC_API_URL"
fi

echo ""
echo "=== Status Check Complete ==="

