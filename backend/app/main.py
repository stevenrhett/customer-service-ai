"""
Main FastAPI application for the Customer Service AI system.
Handles incoming chat requests and routes them through the multi-agent system.
"""
from contextlib import asynccontextmanager

from app.api.v1 import chat
from app.config import get_settings
from app.middleware.rate_limiter import (RateLimitExceeded, limiter,
                                         rate_limit_handler)
from app.services.dependencies import get_orchestrator_chain
from app.utils.exceptions import CustomerServiceException
from app.utils.logging import configure_logging, get_logger
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize settings
settings = get_settings()

# Configure logging
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event("startup") pattern.
    """
    # Startup
    try:
        orchestrator = get_orchestrator_chain()
        chat.set_orchestrator(orchestrator)
        logger.info("Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
        raise
    
    yield
    
    # Shutdown (if needed in the future)
    logger.info("Application shutting down")


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Customer Service AI",
    description="Advanced multi-agent customer service system with specialized agents",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative
    lifespan=lifespan,
)

# Configure CORS
cors_origins = (
    settings.get_cors_origins_list()
    if settings.cors_origins
    else ["http://localhost:3000"]
)
cors_methods = settings.get_cors_methods_list()
cors_headers = settings.get_cors_headers_list()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=cors_methods if cors_methods else ["*"],
    allow_headers=cors_headers if cors_headers else ["*"],
)


# Error handling middleware
@app.exception_handler(CustomerServiceException)
async def customer_service_exception_handler(
    request: Request, exc: CustomerServiceException
):
    """Handle custom customer service exceptions."""
    logger.error(
        f"CustomerServiceException: {exc.message}",
        extra={"status_code": exc.status_code, "details": exc.details},
        exc_info=True,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "status_code": exc.status_code,
            "details": exc.details,
            "type": exc.__class__.__name__,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
            "type": "RequestValidationError",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
            if settings.environment == "production"
            else str(exc),
            "type": exc.__class__.__name__,
        },
    )


# Include routers
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

# Add rate limiting exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_handler)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "message": "Customer Service AI API is running",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    from app.services.cache_service import cache_service

    return {
        "status": "healthy",
        "environment": settings.environment,
        "services": {
            "api": "operational",
            "vector_db": "operational",
            "cache": "operational",
        },
        "cache_stats": cache_service.get_stats(),
    }


if __name__ == "__main__":
    import uvicorn

    # Run from backend/ directory: python -m app.main
    # Or: uvicorn app.main:app --reload
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True if settings.environment == "development" else False,
    )
