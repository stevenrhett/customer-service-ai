"""
Main FastAPI application for the Customer Service AI system.
Handles incoming chat requests and routes them through the multi-agent system.

Production-ready with comprehensive security features:
- Authentication & Authorization
- Security headers
- PII filtering
- Audit logging
- Rate limiting
- HTTPS enforcement
- Production validation
"""
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

from app.api.v1 import chat
from app.config import get_settings
from app.middleware.rate_limiter import (RateLimitExceeded, limiter,
                                         rate_limit_handler)
from app.middleware.security_headers import (
    SecurityHeadersMiddleware,
    HTTPSRedirectMiddleware,
    RequestSizeLimitMiddleware
)
from app.services.dependencies import get_orchestrator_chain
from app.utils.exceptions import CustomerServiceException
from app.utils.logging import configure_logging, get_logger
from app.utils.production_validator import validate_production_environment, ValidationError
from app.utils.audit_logger import audit_logger, AuditEventType, AuditSeverity
from app.utils.data_retention import data_retention_policy
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize settings
settings = get_settings()

# Configure logging with PII masking
configure_logging(settings.log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event("startup") pattern.
    """
    # Startup
    logger.info(f"Starting Customer Service AI v1.0.0 in {settings.environment} mode")
    audit_logger.log_event(
        event_type=AuditEventType.SYSTEM_START,
        severity=AuditSeverity.LOW,
        action="startup",
        details={"environment": settings.environment}
    )

    # Validate production environment
    if settings.environment.lower() == "production":
        try:
            logger.info("Validating production environment configuration...")
            validate_production_environment(strict=True)
            logger.info("✓ Production validation passed")
        except ValidationError as e:
            logger.critical(f"Production validation failed: {e}")
            audit_logger.log_event(
                event_type=AuditEventType.SYSTEM_ERROR,
                severity=AuditSeverity.CRITICAL,
                action="startup_validation",
                result="failure",
                details={"error": str(e)}
            )
            raise

    # Initialize orchestrator
    try:
        orchestrator = get_orchestrator_chain()
        chat.set_orchestrator(orchestrator)
        logger.info("✓ Orchestrator initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}", exc_info=True)
        audit_logger.log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            severity=AuditSeverity.CRITICAL,
            action="orchestrator_init",
            result="failure",
            details={"error": str(e)}
        )
        raise

    # Start background cleanup task
    cleanup_task = asyncio.create_task(periodic_cleanup())

    logger.info("✓ Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutting down...")
    audit_logger.log_event(
        event_type=AuditEventType.SYSTEM_STOP,
        severity=AuditSeverity.LOW,
        action="shutdown"
    )

    # Cancel cleanup task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    logger.info("✓ Graceful shutdown complete")


async def periodic_cleanup():
    """Background task for periodic data cleanup."""
    while True:
        try:
            # Wait 1 hour between cleanups
            await asyncio.sleep(3600)

            logger.info("Running periodic data cleanup...")

            # Cleanup sessions
            from app.services.session_manager import session_manager
            session_count = data_retention_policy.cleanup_sessions(session_manager)

            # Cleanup cache
            from app.services.cache_service import cache_service
            data_retention_policy.cleanup_cache(cache_service)

            logger.info(f"✓ Periodic cleanup complete (cleaned {session_count} sessions)")

        except asyncio.CancelledError:
            logger.info("Cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}", exc_info=True)


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Customer Service AI",
    description="Advanced multi-agent customer service system with specialized agents",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative
    lifespan=lifespan,
)

# Add security middleware (order matters!)

# 1. HTTPS redirect (must be first)
app.add_middleware(HTTPSRedirectMiddleware)

# 2. Security headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. Request size limiting
app.add_middleware(
    RequestSizeLimitMiddleware,
    max_size=getattr(settings, 'max_request_size', 10485760)
)

# 4. CORS (after security headers)
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
    """
    Comprehensive health check endpoint.

    Returns detailed health status of all system components.
    """
    from app.services.cache_service import cache_service
    from app.services.session_manager import session_manager
    import os

    # Check vector database
    vector_db_status = "operational"
    try:
        chroma_dir = settings.chroma_persist_directory
        if not os.path.exists(chroma_dir):
            vector_db_status = "warning: directory not found"
    except Exception as e:
        vector_db_status = f"error: {str(e)}"

    # Check cache
    cache_stats = cache_service.get_stats()
    cache_status = "operational" if cache_stats['size'] >= 0 else "error"

    # Check sessions
    session_count = len(session_manager._sessions)
    session_status = "operational"

    # Overall health
    overall_status = "healthy"
    if "error" in vector_db_status or cache_status == "error":
        overall_status = "degraded"

    # Get data retention info
    retention_info = data_retention_policy.get_retention_info()

    return {
        "status": overall_status,
        "timestamp": datetime.now().isoformat(),
        "environment": settings.environment,
        "version": "1.0.0",
        "services": {
            "api": "operational",
            "vector_db": vector_db_status,
            "cache": cache_status,
            "session_manager": session_status,
        },
        "metrics": {
            "cache_stats": cache_stats,
            "active_sessions": session_count,
        },
        "security": {
            "authentication_required": getattr(settings, 'require_authentication', False),
            "https_enforced": getattr(settings, 'enforce_https', False),
            "rate_limiting_enabled": settings.rate_limit_enabled,
            "pii_masking_enabled": getattr(settings, 'mask_pii_in_logs', True),
        },
        "data_retention": retention_info,
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
