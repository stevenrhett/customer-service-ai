"""
Rate limiting middleware for FastAPI.
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request
from fastapi.responses import JSONResponse
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute", f"{settings.rate_limit_per_hour}/hour"] if settings.rate_limit_enabled else [],
    storage_uri="memory://",
)

def get_rate_limiter() -> Limiter:
    """Get the rate limiter instance."""
    return limiter

def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
        }
    )


