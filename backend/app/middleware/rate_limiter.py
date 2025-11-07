"""
Rate limiting middleware for FastAPI.
"""
import logging
from typing import Callable

from app.config import get_settings
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
settings = get_settings()

# Try to import slowapi, create no-op fallback if not available
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address

    HAS_SLOWAPI = True

    # Initialize rate limiter
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[
            f"{settings.rate_limit_per_minute}/minute",
            f"{settings.rate_limit_per_hour}/hour",
        ]
        if settings.rate_limit_enabled
        else [],
        storage_uri="memory://",
    )
except ImportError:
    HAS_SLOWAPI = False
    logger.warning(
        "slowapi not installed. Rate limiting disabled. Install with: pip install slowapi"
    )

    # Create a no-op limiter for when slowapi is not available
    class NoOpLimiter:
        """No-op rate limiter when slowapi is not available."""

        def limit(self, *args, **kwargs):
            """No-op decorator that does nothing."""

            def decorator(func: Callable) -> Callable:
                return func

            return decorator

    limiter = NoOpLimiter()

    # Create a dummy RateLimitExceeded exception
    class RateLimitExceeded(Exception):
        def __init__(self, detail: str = "Rate limit exceeded"):
            self.detail = detail
            super().__init__(detail)


def get_rate_limiter():
    """Get the rate limiter instance."""
    return limiter


# Export RateLimitExceeded so it can be imported from this module
__all__ = ["limiter", "rate_limit_handler", "RateLimitExceeded", "get_rate_limiter"]


def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors."""
    if HAS_SLOWAPI:
        from slowapi.util import get_remote_address

        logger.warning(f"Rate limit exceeded for {get_remote_address(request)}")
    else:
        logger.warning("Rate limit exceeded (slowapi not available)")

    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": f"Too many requests. Limit: {exc.detail}",
            "retry_after": exc.retry_after if hasattr(exc, "retry_after") else None,
        },
    )
