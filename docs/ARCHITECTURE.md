# Architecture Documentation

## System Overview

The Customer Service AI system is a multi-agent architecture designed to provide intelligent customer support through natural language interaction and document-based knowledge retrieval.

## Components

### 1. Frontend (Next.js)

**Purpose**: Provides the user interface for interacting with the AI customer service system.

**Key Files**:
- `app/page.tsx`: Main page component with chat and document upload
- `components/ChatInterface.tsx`: Real-time chat interface
- `components/DocumentUpload.tsx`: Document upload functionality
- `lib/api.ts`: API client for backend communication

**Features**:
- Real-time chat interface
- Document upload with progress feedback
- Agent identification in responses
- Responsive design with Tailwind CSS

### 2. Backend (FastAPI)

**Purpose**: Orchestrates multiple AI agents and manages the vector database.

**Key Files**:
- `app/main.py`: FastAPI application initialization
- `app/api/routes.py`: API endpoint definitions
- `app/config.py`: Configuration management
- `app/models/schemas.py`: Pydantic models for request/response

**Features**:
- RESTful API with automatic documentation
- CORS support for cross-origin requests
- Health check endpoints
- File upload handling

### 3. Multi-Agent System (LangChain)

**Purpose**: Intelligent routing and processing of customer queries.

#### Agent Types

##### a. Document Retrieval Agent
- **Priority**: Highest
- **Triggers**: Questions containing keywords like "how to", "documentation", "guide", "instructions"
- **Function**: Retrieves relevant information from uploaded documents using RAG (Retrieval Augmented Generation)
- **LLM Settings**: Temperature 0.3 (more deterministic for factual answers)

##### b. Technical Support Agent
- **Priority**: Medium
- **Triggers**: Questions containing keywords like "error", "not working", "broken", "issue", "problem"
- **Function**: Provides step-by-step troubleshooting guidance
- **LLM Settings**: Temperature 0.5 (balanced creativity and accuracy)

##### c. General Inquiry Agent
- **Priority**: Lowest (fallback)
- **Triggers**: All other queries
- **Function**: Handles general customer service questions
- **LLM Settings**: Temperature 0.7 (more conversational)

#### Orchestrator

The `AgentOrchestrator` class manages:
- Agent selection based on query analysis
- Conversation history tracking
- Context management across turns
- Fallback handling

**Selection Logic**:
```python
for agent in [document_agent, technical_agent, general_agent]:
    if agent.can_handle(query):
        return agent.process(query, context)
```

### 4. Vector Database (ChromaDB)

**Purpose**: Stores and retrieves document embeddings for semantic search.

**Key Features**:
- Persistent storage on disk
- OpenAI embeddings (text-embedding-ada-002)
- Similarity search with scoring
- Metadata storage for source tracking

**Document Processing Pipeline**:
1. Document upload (PDF/TXT)
2. Text extraction
3. Chunking (1000 chars with 200 char overlap)
4. Embedding generation
5. Storage in ChromaDB
6. Metadata indexing

## Data Flow

### Chat Request Flow

```
User Input
    ↓
Frontend (ChatInterface)
    ↓
API Client (axios)
    ↓
Backend API (/api/v1/chat)
    ↓
AgentOrchestrator
    ↓
Agent Selection (can_handle())
    ↓
Selected Agent Process
    ↓ (if Document Agent)
ChromaDB Retrieval
    ↓
LangChain QA Chain
    ↓
OpenAI GPT-3.5
    ↓
Response with Sources
    ↓
Frontend Display
```

### Document Upload Flow

```
User Selects File
    ↓
Frontend (DocumentUpload)
    ↓
API Client (multipart/form-data)
    ↓
Backend API (/api/v1/documents/upload)
    ↓
File Type Detection
    ↓
Text Extraction (PyPDF/UTF-8)
    ↓
VectorStoreService
    ↓
Text Splitter (RecursiveCharacterTextSplitter)
    ↓
OpenAI Embeddings
    ↓
ChromaDB Storage
    ↓
Success Response
```

## Technology Choices

### Why FastAPI?
- Modern async support
- Automatic API documentation (OpenAPI/Swagger)
- Type validation with Pydantic
- High performance
- Easy integration with Python AI libraries

### Why Next.js?
- Server-side rendering capabilities
- Built-in routing
- Optimized production builds
- Great developer experience
- TypeScript support

### Why LangChain?
- Abstracts LLM interactions
- Built-in support for agents and chains
- Retrieval augmentation patterns
- Conversation memory management
- Vector store integrations

### Why ChromaDB?
- Easy to use and deploy
- No separate server required
- Good performance for small to medium datasets
- Native Python integration
- Persistent storage

## Security Considerations

1. **API Key Management**: OpenAI API key stored in environment variables
2. **CORS**: Configurable origin restrictions
3. **File Upload**: Type validation and size limits
4. **Input Validation**: Pydantic models validate all inputs
5. **Error Handling**: Graceful error responses without exposing internals

## Scalability Considerations

### Current Limitations
- Single-instance ChromaDB (not distributed)
- In-memory conversation history
- Single OpenAI API key

### Future Improvements
- Redis for conversation state
- Distributed vector database (Weaviate, Pinecone)
- Load balancing for multiple backend instances
- Caching layer for frequent queries
- Rate limiting

## Deployment

### Docker Compose
- Isolated containers for backend and frontend
- Persistent volume for ChromaDB data
- Environment variable configuration
- Easy local development

### Production Considerations
- Use environment-specific configuration
- Set up proper logging
- Configure monitoring (Prometheus, Grafana)
- Implement rate limiting
- Use managed vector database
- Set up CI/CD pipeline

## Monitoring and Observability

Recommended additions:
- Request/response logging
- Agent selection metrics
- Response time tracking
- Error rate monitoring
- Vector search performance metrics
- OpenAI API usage tracking

## Testing Strategy

1. **Unit Tests**: Individual agent logic
2. **Integration Tests**: API endpoints
3. **E2E Tests**: Full user flows
4. **Load Tests**: Performance under load
5. **Vector Search Tests**: Retrieval accuracy
