"""FastAPI main application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.services.vector_store import VectorStoreService
from app.agents.orchestrator import AgentOrchestrator
from app.agents.general_agent import GeneralInquiryAgent
from app.agents.technical_agent import TechnicalSupportAgent
from app.agents.document_agent import DocumentRetrievalAgent
from app.api import routes

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Customer Service AI",
    description="Multi-agent AI customer service system with intelligent document retrieval",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
vector_store = VectorStoreService(
    persist_directory=settings.chroma_db_path,
    openai_api_key=settings.openai_api_key
)

# Initialize agents
retriever = vector_store.get_retriever(k=3)

document_agent = DocumentRetrievalAgent(
    openai_api_key=settings.openai_api_key,
    retriever=retriever
)

technical_agent = TechnicalSupportAgent(
    openai_api_key=settings.openai_api_key
)

general_agent = GeneralInquiryAgent(
    openai_api_key=settings.openai_api_key
)

# Create orchestrator with agent priority
# Order matters: Document > Technical > General
orchestrator = AgentOrchestrator([
    document_agent,
    technical_agent,
    general_agent
])

# Inject dependencies into routes
routes.orchestrator = orchestrator
routes.vector_store = vector_store

# Include routers
app.include_router(routes.router, prefix="/api/v1", tags=["api"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Customer Service AI API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
