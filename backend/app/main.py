"""
Main FastAPI application for the Customer Service AI system.
Handles incoming chat requests and routes them through the multi-agent system.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import chat

# Initialize settings
settings = get_settings()

# Create FastAPI app
app = FastAPI(
    title="Customer Service AI",
    description="Advanced multi-agent customer service system with specialized agents",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api", tags=["chat"])


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "Customer Service AI API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "services": {
            "api": "operational",
            "vector_db": "operational"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.environment == "development" else False
    )
