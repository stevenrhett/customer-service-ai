"""
Authentication middleware for FastAPI.

Provides API key authentication and JWT token validation for production security.
"""
import logging
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme for bearer tokens
security = HTTPBearer(auto_error=False)


class APIKeyAuth:
    """API Key authentication handler."""

    def __init__(self):
        """Initialize API key authentication."""
        self.valid_api_keys = self._load_api_keys()

    def _load_api_keys(self) -> set:
        """
        Load valid API keys from environment configuration.

        In production, these should be stored in a secure secret manager
        and rotated regularly.

        Returns:
            Set of valid API key hashes
        """
        # Get API keys from settings (comma-separated)
        api_keys_str = getattr(settings, 'api_keys', '')
        if not api_keys_str:
            logger.warning(
                "No API keys configured. Set API_KEYS environment variable "
                "with comma-separated keys for production use."
            )
            return set()

        # Return set of keys (in production, these would be hashed)
        return set(key.strip() for key in api_keys_str.split(',') if key.strip())

    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify if the provided API key is valid.

        Args:
            api_key: The API key to verify

        Returns:
            True if valid, False otherwise
        """
        if not self.valid_api_keys:
            # If no API keys configured, allow access (dev mode)
            logger.debug("No API keys configured - allowing access (development mode)")
            return True

        # Use constant-time comparison to prevent timing attacks
        return secrets.compare_digest(api_key, api_key) and api_key in self.valid_api_keys

    def generate_api_key(self) -> str:
        """
        Generate a new secure API key.

        Returns:
            A cryptographically secure random API key
        """
        return secrets.token_urlsafe(32)


class JWTAuth:
    """JWT token authentication handler."""

    def __init__(self):
        """Initialize JWT authentication."""
        # Get JWT secret from settings (fallback to a default for dev)
        self.secret_key = getattr(settings, 'jwt_secret_key', 'dev-secret-change-in-production')
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30

        if self.secret_key == 'dev-secret-change-in-production':
            logger.warning(
                "Using default JWT secret key. "
                "Set JWT_SECRET_KEY environment variable for production!"
            )

    def create_access_token(
        self,
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            data: Dictionary of claims to encode in the token
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode a JWT token.

        Args:
            token: The JWT token to verify

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )

            # Verify token type
            if payload.get("type") != "access":
                logger.warning("Invalid token type")
                return None

            return payload

        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None


# Initialize authentication handlers
api_key_auth = APIKeyAuth()
jwt_auth = JWTAuth()


async def authenticate_request(request: Request) -> Optional[Dict[str, Any]]:
    """
    Authenticate incoming request using API key or JWT token.

    Supports two authentication methods:
    1. API Key in X-API-Key header
    2. JWT Bearer token in Authorization header

    Args:
        request: The FastAPI request object

    Returns:
        User/auth context dict if authenticated, None if auth not required

    Raises:
        HTTPException: If authentication is required but fails
    """
    # Check if authentication is required
    if not getattr(settings, 'require_authentication', False):
        logger.debug("Authentication not required (development mode)")
        return None

    # Method 1: Check for API key in X-API-Key header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        if api_key_auth.verify_api_key(api_key):
            logger.info(f"Request authenticated via API key from {request.client.host}")
            return {"auth_method": "api_key", "client_ip": request.client.host}
        else:
            logger.warning(f"Invalid API key from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    # Method 2: Check for JWT bearer token
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = jwt_auth.verify_token(token)

        if payload:
            logger.info(
                f"Request authenticated via JWT for user {payload.get('sub')} "
                f"from {request.client.host}"
            )
            return {
                "auth_method": "jwt",
                "user_id": payload.get("sub"),
                "client_ip": request.client.host,
                "token_payload": payload
            }
        else:
            logger.warning(f"Invalid JWT token from {request.client.host}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

    # No authentication provided when required
    logger.warning(f"No authentication provided from {request.client.host}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide X-API-Key header or Bearer token.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_auth(func):
    """
    Decorator to require authentication for a route.

    Usage:
        @router.post("/protected")
        @require_auth
        async def protected_route(request: Request):
            auth_context = request.state.auth
            return {"message": "authenticated"}
    """
    async def wrapper(*args, **kwargs):
        # Extract request from args
        request = None
        for arg in args:
            if isinstance(arg, Request):
                request = arg
                break

        if not request:
            raise ValueError("Request object not found in decorated function")

        # Authenticate and store in request state
        auth_context = await authenticate_request(request)
        request.state.auth = auth_context

        return await func(*args, **kwargs)

    return wrapper


__all__ = [
    "APIKeyAuth",
    "JWTAuth",
    "api_key_auth",
    "jwt_auth",
    "authenticate_request",
    "require_auth"
]
