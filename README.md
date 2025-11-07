# 🤖 Advanced Customer Service AI

<div align="center">

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Node.js](https://img.shields.io/badge/node-18+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg)
![Next.js](https://img.shields.io/badge/Next.js-14.0-black.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**A sophisticated multi-agent AI system for intelligent customer service**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [API Reference](#-api-reference)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Overview

Advanced Customer Service AI is a production-ready, multi-agent system that intelligently routes customer queries to specialized AI agents. Built with LangChain, LangGraph, and modern web technologies.

**Key Highlights:**
- 🧠 Intelligent routing with AWS Bedrock-powered orchestrator
- 🔍 Hybrid retrieval strategies (RAG, CAG, Hybrid)
- 💬 Real-time streaming chat interface
- ⚡ Production-ready with caching, rate limiting, and comprehensive testing

---

## ✨ Features

### Core Capabilities
- **Multi-Agent Orchestration** - Hierarchical workflow with intelligent query routing
- **Advanced Retrieval Strategies** - RAG, CAG, and Hybrid approaches optimized per agent
- **Real-Time Chat Interface** - Modern, responsive UI with streaming responses
- **Session Management** - Conversation persistence and context awareness
- **Performance Optimized** - Caching, rate limiting, and efficient vector search

### Specialized Agents
- **Billing Agent** - Hybrid RAG/CAG for pricing and payment questions
- **Technical Agent** - Pure RAG for always-current technical support
- **Policy Agent** - Pure CAG for fast, consistent policy responses

### Production Features
- **Docker Support** - Containerized deployment with docker-compose
- **Comprehensive Testing** - Unit, integration, and E2E tests
- **API Documentation** - Auto-generated Swagger/OpenAPI docs
- **Security** - Input validation, sanitization, and rate limiting

---

## 🏗️ Architecture

```
Frontend (Next.js) → FastAPI Backend → Orchestrator Agent (AWS Bedrock)
                                              ↓
                    ┌─────────────────────────┼─────────────────────────┐
                    ↓                         ↓                         ↓
              Billing Agent          Technical Agent          Policy Agent
              (Hybrid RAG/CAG)       (Pure RAG)              (Pure CAG)
                    ↓                         ↓                         ↓
              ChromaDB Vector Store   ChromaDB Vector Store   CAG Cache
```

---

## 📦 Prerequisites

- **Python** 3.10+ ([Download](https://www.python.org/downloads/))
- **Node.js** 18+ ([Download](https://nodejs.org/))
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **AWS Account** with Bedrock access ([Setup guide](docs/setup/AWS_CREDENTIALS_GUIDE.md))
- **Docker** (optional, for containerized deployment)

---

## ⚡ Quick Start

### Option 1: Automated Script (Recommended)

```bash
# Make script executable
chmod +x scripts/quickstart.sh

# Run quickstart
./scripts/quickstart.sh
```

### Option 2: Manual Setup

**1. Clone and Install**

```bash
git clone https://github.com/yourusername/customer-service-ai.git
cd customer-service-ai

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

**2. Configure Environment**

```bash
# Backend
cd backend
cp .env.example .env
# Edit .env with your API keys

# Frontend
cd ../frontend
cp .env.example .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
```

**3. Ingest Data**

```bash
cd backend
source venv/bin/activate
python scripts/ingest_data.py
```

**4. Start Services**

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python -m app.main
# OR: uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm run dev
```

**5. Access Application**

- 🌐 Frontend: http://localhost:3000
- 📚 API Docs: http://localhost:8000/docs
- ❤️ Health: http://localhost:8000/health

### Option 3: Docker

```bash
docker-compose up --build
```

---

## ⚙️ Configuration

### Backend Environment Variables

Create `backend/.env`:

```env
# Required
OPENAI_API_KEY=sk-your-key-here
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-west-2

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_ENABLED=true
RATE_LIMIT_PER_MINUTE=60
```

See `backend/.env.example` for all options.

### Frontend Environment Variables

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 💻 Usage

### Web Interface

1. Open http://localhost:3000
2. Type your question
3. View the response with agent badge

### Example Queries

**Billing:** "What are your pricing plans?"  
**Technical:** "How do I enable 2FA?"  
**Policy:** "What is your privacy policy?"

### API Usage

```bash
# Standard chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are your pricing plans?", "session_id": "user-123"}'

# Streaming chat
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I enable 2FA?", "session_id": "user-123"}'
```

---

## 📚 API Reference

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Standard chat |
| `POST` | `/api/chat/stream` | Streaming chat |
| `GET` | `/health` | Health check |

### Request Format

```json
{
  "message": "Your question",
  "session_id": "optional-session-id",
  "conversation_history": []
}
```

### Response Format

```json
{
  "response": "AI response",
  "agent_used": "billing|technical|policy",
  "session_id": "session-id",
  "timestamp": "2024-11-06T12:00:00"
}
```

---

## 🧪 Testing

### Backend

```bash
cd backend
source venv/bin/activate
pytest
pytest --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend
npm test
npm run test:coverage
```

---

## 🐳 Deployment

### Docker

```bash
docker-compose up -d --build
docker-compose logs -f
docker-compose down
```

### Production

See [Deployment Guide](docs/DEPLOYMENT_GUIDE.md) for:
- AWS Elastic Beanstalk
- Heroku
- Railway
- Vercel (Frontend)
- Custom VPS

---

## 📁 Project Structure

```
customer-service-ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # AI agents
│   │   ├── api/             # FastAPI routes
│   │   ├── services/        # Business logic
│   │   ├── middleware/      # Rate limiting
│   │   └── models/          # Pydantic schemas
│   ├── data/raw/            # Source documents
│   ├── scripts/             # Data ingestion
│   ├── tests/               # Test suite
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app
│   │   ├── components/      # React components
│   │   └── lib/             # Utilities
│   ├── Dockerfile
│   └── package.json
├── docs/                     # Documentation
├── docker-compose.yml
└── README.md
```

---

## 🔧 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version: `python --version` (should be 3.10+)
- Verify virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

**Frontend build fails:**
- Clear and reinstall: `rm -rf node_modules && npm install`

**ChromaDB errors:**
- Re-run ingestion: `python scripts/ingest_data.py`

**CORS errors:**
- Ensure `CORS_ORIGINS` in backend `.env` includes frontend URL
- Check `NEXT_PUBLIC_API_URL` matches backend URL

### Getting Help

- 📖 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- 🐛 [Project Review](PROJECT_REVIEW.md)
- 💬 Open an issue on GitHub

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [LangChain](https://www.langchain.com/) - LLM framework
- [LangGraph](https://github.com/langchain-ai/langgraph) - Multi-agent orchestration
- [FastAPI](https://fastapi.tiangolo.com/) - Python web framework
- [Next.js](https://nextjs.org/) - React framework

---

<div align="center">

**Made with ❤️ using modern AI technologies**

⭐ Star this repo if you find it helpful!

</div>
