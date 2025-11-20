"""
Security headers middleware for FastAPI.

Implements OWASP recommended security headers to protect against common attacks:
- XSS (Cross-Site Scripting)
- Clickjacking
- MIME sniffing
- Information disclosure
- Man-in-the-middle attacks
"""
import logging
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses.

    Implements OWASP security best practices:
    https://owasp.org/www-project-secure-headers/
    """

    def __init__(self, app: ASGIApp):
        """Initialize security headers middleware."""
        super().__init__(app)
        self.is_production = settings.environment.lower() == "production"
        self.enforce_https = getattr(settings, 'enforce_https', False)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        # Call the next middleware/route
        response = await call_next(request)

        # Add security headers
        self._add_security_headers(response, request)

        return response

    def _add_security_headers(self, response: Response, request: Request) -> None:
        """
        Add comprehensive security headers to the response.

        Args:
            response: The FastAPI response object
            request: The FastAPI request object
        """
        # 1. Content Security Policy (CSP)
        # Prevents XSS attacks by controlling what resources can be loaded
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Relaxed for development
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self' data:",
            "connect-src 'self' https:",
            "frame-ancestors 'none'",  # Prevent embedding
            "base-uri 'self'",
            "form-action 'self'"
        ]

        if self.is_production:
            # Stricter CSP for production
            csp_directives = [
                "default-src 'self'",
                "script-src 'self'",
                "style-src 'self'",
                "img-src 'self' data: https:",
                "font-src 'self'",
                "connect-src 'self'",
                "frame-ancestors 'none'",
                "base-uri 'self'",
                "form-action 'self'",
                "upgrade-insecure-requests"  # Force HTTPS
            ]

        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # 2. Strict-Transport-Security (HSTS)
        # Forces HTTPS connections for enhanced security
        if self.enforce_https or self.is_production:
            # max-age: 31536000 seconds = 1 year
            # includeSubDomains: Apply to all subdomains
            # preload: Allow inclusion in browser HSTS preload lists
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 3. X-Content-Type-Options
        # Prevents MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # 4. X-Frame-Options
        # Prevents clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"

        # 5. X-XSS-Protection
        # Legacy XSS protection (still used by older browsers)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 6. Referrer-Policy
        # Controls referrer information sent with requests
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # 7. Permissions-Policy (formerly Feature-Policy)
        # Controls which browser features can be used
        permissions_directives = [
            "geolocation=()",
            "microphone=()",
            "camera=()",
            "payment=()",
            "usb=()",
            "magnetometer=()",
            "gyroscope=()",
            "accelerometer=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_directives)

        # 8. X-Permitted-Cross-Domain-Policies
        # Restricts cross-domain access (Flash, PDF, etc.)
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"

        # 9. Cache-Control for sensitive endpoints
        # Prevent caching of sensitive data
        if self._is_sensitive_endpoint(request.url.path):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        # 10. Server header removal/obfuscation
        # Don't reveal server implementation details
        response.headers["Server"] = "SecureServer"

        # 11. X-Robots-Tag (for non-public APIs)
        # Prevent search engine indexing
        if self.is_production:
            response.headers["X-Robots-Tag"] = "noindex, nofollow"

    def _is_sensitive_endpoint(self, path: str) -> bool:
        """
        Check if the endpoint handles sensitive data.

        Args:
            path: Request URL path

        Returns:
            True if endpoint is sensitive, False otherwise
        """
        sensitive_patterns = [
            "/api/v1/chat",  # Chat endpoints may contain user data
            "/auth",  # Authentication endpoints
            "/login",
            "/token",
            "/user",
            "/admin"
        ]

        return any(pattern in path for pattern in sensitive_patterns)


class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to redirect HTTP requests to HTTPS.

    Only active in production when enforce_https is enabled.
    """

    def __init__(self, app: ASGIApp):
        """Initialize HTTPS redirect middleware."""
        super().__init__(app)
        self.enforce_https = getattr(settings, 'enforce_https', False)
        self.is_production = settings.environment.lower() == "production"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Redirect HTTP to HTTPS if configured."""
        # Only enforce in production
        if not (self.enforce_https and self.is_production):
            return await call_next(request)

        # Check if request is HTTP
        if request.url.scheme == "http":
            # Redirect to HTTPS
            https_url = request.url.replace(scheme="https")
            logger.info(f"Redirecting HTTP to HTTPS: {request.url} -> {https_url}")

            return Response(
                status_code=301,  # Permanent redirect
                headers={"Location": str(https_url)}
            )

        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size.

    Prevents DoS attacks via large request payloads.
    """

    def __init__(self, app: ASGIApp, max_size: int = None):
        """
        Initialize request size limit middleware.

        Args:
            app: ASGI application
            max_size: Maximum request size in bytes (default from settings)
        """
        super().__init__(app)
        self.max_size = max_size or getattr(settings, 'max_request_size', 10485760)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check request size before processing."""
        # Get content length from headers
        content_length = request.headers.get("content-length")

        if content_length:
            content_length = int(content_length)
            if content_length > self.max_size:
                logger.warning(
                    f"Request size {content_length} exceeds limit {self.max_size} "
                    f"from {request.client.host}"
                )
                return Response(
                    status_code=413,  # Payload Too Large
                    content={
                        "error": "Request too large",
                        "message": f"Request size exceeds maximum allowed size of {self.max_size} bytes"
                    }
                )

        return await call_next(request)


__all__ = [
    "SecurityHeadersMiddleware",
    "HTTPSRedirectMiddleware",
    "RequestSizeLimitMiddleware"
]
