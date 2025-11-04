# Customer Service AI

A multi-agent AI customer service system with FastAPI backend, Next.js frontend, LangChain orchestration, and ChromaDB vector database for intelligent document retrieval.

## Features

- **Multi-Agent System**: Three specialized agents work together to handle different types of queries:
  - **Document Retrieval Agent**: Answers questions based on uploaded documentation
  - **Technical Support Agent**: Handles technical issues and troubleshooting
  - **General Inquiry Agent**: Manages general customer questions

- **Intelligent Routing**: Automatic query routing to the most appropriate agent
- **Document Management**: Upload and process PDF/TXT documents for knowledge base
- **Vector Search**: ChromaDB-powered semantic search for relevant information retrieval
- **Real-time Chat**: Interactive chat interface with conversation history
- **Modern UI**: Responsive Next.js frontend with Tailwind CSS

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│   Next.js       │         │   FastAPI        │
│   Frontend      │◄────────┤   Backend        │
└─────────────────┘  REST   └──────────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
              ┌─────▼──────┐   ┌─────▼──────┐   ┌─────▼──────┐
              │ Document   │   │ Technical  │   │  General   │
              │ Agent      │   │ Agent      │   │  Agent     │
              └────────────┘   └────────────┘   └────────────┘
                    │
              ┌─────▼──────┐
              │ ChromaDB   │
              │ Vector DB  │
              └────────────┘
```

## Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key
- Docker & Docker Compose (optional)

## Installation

### Option 1: Docker Compose (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/stevenrhett/customer-service-ai.git
cd customer-service-ai
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
```

3. Edit `backend/.env` and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

4. Start the services:
```bash
docker-compose up -d
```

5. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Option 2: Manual Setup

#### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file:
```bash
cp .env.example .env
```

5. Edit `.env` and add your OpenAI API key

6. Run the backend:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create `.env.local` file:
```bash
cp .env.local.example .env.local
```

4. Run the development server:
```bash
npm run dev
```

5. Open http://localhost:3000 in your browser

## Usage

### Uploading Documents

1. Click on the file input in the sidebar
2. Select a PDF or TXT file
3. Click "Upload Document"
4. The document will be processed and added to the knowledge base

### Chatting with the AI

1. Type your question in the input box
2. Press Enter or click Send
3. The system will automatically route your query to the appropriate agent
4. View the response along with which agent handled your query

### Example Queries

- **Document-related**: "How to install the software?" (routes to Document Retrieval Agent)
- **Technical issues**: "The application is not working" (routes to Technical Support Agent)
- **General questions**: "What are your business hours?" (routes to General Inquiry Agent)

## API Endpoints

### Chat
- **POST** `/api/v1/chat`
  - Send a message and receive a response
  - Request body: `{ "message": "string", "conversation_id": "string?" }`
  - Response: `{ "response": "string", "conversation_id": "string", "agent_used": "string" }`

### Document Upload
- **POST** `/api/v1/documents/upload`
  - Upload a document to the knowledge base
  - Content-Type: `multipart/form-data`
  - Response: `{ "success": boolean, "message": "string", "document_id": "string?" }`

### Health Check
- **GET** `/api/v1/health`
  - Check API health status
  - Response: `{ "status": "healthy", "service": "customer-service-ai" }`

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain**: Framework for developing applications powered by language models
- **ChromaDB**: Open-source embedding database for vector storage
- **OpenAI**: GPT-3.5 for natural language understanding and generation
- **Pydantic**: Data validation using Python type annotations

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **Axios**: HTTP client for API requests

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Formatting

```bash
# Backend
black app/
ruff app/

# Frontend
npm run lint
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.