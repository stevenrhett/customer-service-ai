# 🧪 Local Testing Checklist

Complete guide for setting up and testing the Customer Service AI application locally.

---

## ✅ Prerequisites

### Required Software
- [ ] **Python 3.10+** - Check: `python3 --version`
- [ ] **Node.js 18+** - Check: `node --version`
- [ ] **npm** (comes with Node.js) - Check: `npm --version`
- [ ] **Git** - Check: `git --version`

### Required API Keys & Credentials
- [ ] **OpenAI API Key** - Get from: https://platform.openai.com/api-keys
- [ ] **AWS Account** with Bedrock access
- [ ] **AWS Access Key ID** - Get from AWS Console
- [ ] **AWS Secret Access Key** - Get from AWS Console
- [ ] **AWS Region** (default: `us-west-2`)

### Optional (for Docker)
- [ ] **Docker Desktop** - For containerized deployment
- [ ] **Docker Compose** - Usually included with Docker Desktop

---

## 📋 Setup Steps

### 1. Clone/Download Project
```bash
# If using Git
git clone <repository-url>
cd customer-service-ai

# Or extract downloaded zip file
cd customer-service-ai
```

### 2. Backend Setup

#### 2.1 Create Virtual Environment
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2.2 Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2.3 Configure Environment Variables
```bash
# Copy example file
cp .env.example .env

# Edit .env with your actual values
# Required variables:
# - OPENAI_API_KEY=sk-your-key-here
# - AWS_ACCESS_KEY_ID=your-access-key
# - AWS_SECRET_ACCESS_KEY=your-secret-key
# - AWS_REGION=us-west-2
```

**Minimum `.env` file:**
```env
OPENAI_API_KEY=sk-your-openai-key-here
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-west-2
```

#### 2.4 Test Credentials (Optional but Recommended)
```bash
python scripts/test_credentials.py
# Should show: OpenAI: PASS, AWS Bedrock: PASS, ChromaDB: Needs data (expected)
```

#### 2.5 Ingest Data into Vector Store
```bash
python scripts/ingest_data.py
# This creates ChromaDB collections for billing, technical, and policy documents
# Expected output: "Data ingestion completed successfully"
```

### 3. Frontend Setup

#### 3.1 Install Dependencies
```bash
cd ../frontend
npm install
```

#### 3.2 Configure Environment Variables
```bash
# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Or manually create .env.local with:
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Running the Application

### Option 1: Manual Start (Recommended for Development)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python -m app.main
# OR: uvicorn app.main:app --reload --port 8000
# Should see: "Uvicorn running on http://0.0.0.0:8000"
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
# Should see: "Ready on http://localhost:3000"
```

### Option 2: Quick Start Script
```bash
# From project root
chmod +x scripts/quickstart.sh
./scripts/quickstart.sh
```

### Option 3: Docker Compose
```bash
# From project root
docker-compose up --build
```

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

**Expected:** All 41 tests should pass ✅

### Frontend Tests
```bash
cd frontend

# Run all tests
npm test

# Run with watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

**Expected:** All 14 tests should pass ✅

### Integration Testing
```bash
# 1. Start backend (Terminal 1)
cd backend && source venv/bin/activate && python -m app.main

# 2. Start frontend (Terminal 2)
cd frontend && npm run dev

# 3. Test in browser
# Open http://localhost:3000
# Try these queries:
# - "What are your pricing plans?" (should route to billing agent)
# - "How do I enable 2FA?" (should route to technical agent)
# - "What is your privacy policy?" (should route to policy agent)
```

---

## 🔍 Verification Checklist

### Backend Health Check
- [ ] Backend running: http://localhost:8000/health
  - Expected: `{"status": "healthy"}`
- [ ] API docs accessible: http://localhost:8000/docs
  - Should show Swagger UI with all endpoints
- [ ] Test chat endpoint:
  ```bash
  curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "Hello", "session_id": "test-123"}'
  ```

### Frontend Health Check
- [ ] Frontend accessible: http://localhost:3000
- [ ] Chat interface loads without errors
- [ ] Can type and send messages
- [ ] Agent badges appear (billing/technical/policy)

### Agent Routing Test
- [ ] **Billing Agent**: "What are your pricing plans?"
  - Should show "billing" badge
  - Should return pricing information
- [ ] **Technical Agent**: "How do I enable 2FA?"
  - Should show "technical" badge
  - Should return technical instructions
- [ ] **Policy Agent**: "What is your privacy policy?"
  - Should show "policy" badge
  - Should return policy information

### Vector Store Verification
```bash
cd backend
source venv/bin/activate
python -c "
from app.services.vector_store import vector_store_service
billing_store = vector_store_service.get_billing_store()
technical_store = vector_store_service.get_technical_store()
print(f'Billing collection: {billing_store._collection.count() if hasattr(billing_store, \"_collection\") else \"OK\"}')
print(f'Technical collection: {technical_store._collection.count() if hasattr(technical_store, \"_collection\") else \"OK\"}')
"
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. "ModuleNotFoundError" or Import Errors
```bash
# Solution: Reinstall dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

#### 2. "OPENAI_API_KEY not found" or Pydantic Validation Error
```bash
# Solution: Check .env file exists and has correct variable names
cd backend
cat .env  # Should show OPENAI_API_KEY=sk-...
# Make sure no quotes around values
```

#### 3. "ChromaDB collection not found"
```bash
# Solution: Re-run data ingestion
cd backend
source venv/bin/activate
python scripts/ingest_data.py
```

#### 4. "AWS Bedrock Access Denied"
- Verify AWS credentials are correct
- Check AWS region matches (default: us-west-2)
- Ensure Bedrock is enabled in your AWS account
- Check IAM permissions for Bedrock access

#### 5. Frontend can't connect to backend
- Verify backend is running on port 8000
- Check `.env.local` has: `NEXT_PUBLIC_API_URL=http://localhost:8000`
- Check CORS settings in `backend/app/config.py`

#### 6. Tests failing
```bash
# Run tests with verbose output to see errors
pytest -v

# Check if environment variables are set for tests
# Tests use mock values, but some may need actual config
```

---

## 📊 Expected Test Results

### Backend Tests (41 total)
```
tests/test_agents.py ................... [PASS]
tests/test_api_chat.py ................. [PASS]
tests/test_error_handling.py ............ [PASS]
tests/test_orchestrator.py .............. [PASS]
tests/test_rate_limiting.py ............. [PASS]
tests/test_session_manager.py ........... [PASS]

Total: 41 passed
```

### Frontend Tests (14 total)
```
ChatInterface.test.tsx .................. [PASS]
ChatMessage.test.tsx .................... [PASS]

Total: 14 passed
```

---

## 🎯 Quick Test Commands

### One-Liner Setup (if prerequisites met)
```bash
# Backend
cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && cp .env.example .env && python scripts/ingest_data.py

# Frontend
cd frontend && npm install && echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### One-Liner Start
```bash
# Terminal 1
cd backend && source venv/bin/activate && python -m app.main

# Terminal 2
cd frontend && npm run dev
```

### One-Liner Test
```bash
# Backend tests
cd backend && source venv/bin/activate && pytest

# Frontend tests
cd frontend && npm test
```

---

## 📝 Notes

- **First-time setup**: ~15-20 minutes
- **Subsequent starts**: ~30 seconds
- **Data ingestion**: Only needed once (or when documents change)
- **Environment variables**: Never commit `.env` files to Git
- **Docker**: Alternative to manual setup, good for production-like testing

---

## ✅ Completion Checklist

Before considering setup complete, verify:
- [ ] All prerequisites installed
- [ ] All API keys configured
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] Data ingested into vector store
- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Health endpoint returns 200
- [ ] API docs accessible
- [ ] Chat interface loads
- [ ] All three agents respond correctly
- [ ] All backend tests pass (41/41)
- [ ] All frontend tests pass (14/14)

---

**🎉 Once all items are checked, you're ready to develop and test locally!**

