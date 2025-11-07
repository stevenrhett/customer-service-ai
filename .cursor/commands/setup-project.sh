# Setup Project
# Installs dependencies for both backend and frontend

echo "Installing backend dependencies..."
cd backend && pip install -r requirements.txt

echo "Installing frontend dependencies..."
cd ../frontend && npm install

echo "Setup complete! Don't forget to:"
echo "1. Create .env file in backend with API keys"
echo "2. Create .env.local in frontend with NEXT_PUBLIC_API_URL"
echo "3. Run data ingestion: ingest-data"

