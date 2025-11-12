"""
Configuration management for the Customer Service AI application.
Loads environment variables and provides application settings.
"""
import re
from functools import lru_cache
from typing import Optional

from pydantic import ValidationError, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # OpenAI Configuration
    openai_api_key: Optional[str] = None  # Optional - can use Bedrock instead
    openai_model: str = "gpt-4o"  # Default to gpt-4o (fallback to gpt-5 if available)
    use_bedrock_for_services: bool = False  # Use Bedrock instead of OpenAI for services

    # AWS Bedrock Configuration
    aws_access_key_id: Optional[str] = None  # Optional if using bearer token
    aws_secret_access_key: Optional[str] = None  # Optional if using bearer token
    aws_session_token: Optional[str] = None  # Required for temporary SSO credentials
    aws_bearer_token_bedrock: Optional[str] = None  # Bearer token for Bedrock API key authentication
    aws_region: str = "us-west-2"
    bedrock_model_id: str = (
        "anthropic.claude-3-haiku-20240307-v1:0"  # Claude Haiku for routing
    )
    bedrock_service_model_id: str = (
        "anthropic.claude-3-sonnet-20240229-v1:0"  # Claude Sonnet for services (better quality)
    )

    # Application Configuration
    environment: str = "development"
    log_level: str = "INFO"

    # Vector Database
    chroma_persist_directory: str = "./chroma_db"

    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS Configuration
    cors_origins: str = "http://localhost:3000"  # Comma-separated list of origins
    cors_allow_methods: str = "*"  # Comma-separated list of allowed HTTP methods
    cors_allow_headers: str = "*"  # Comma-separated list of allowed headers

    # Rate Limiting Configuration
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60  # Requests per minute per IP
    rate_limit_per_hour: int = 1000  # Requests per hour per IP

    # Frontend Configuration
    frontend_url: str = "http://localhost:3000"

    # Security Configuration
    enable_secrets_manager: bool = False  # Use AWS Secrets Manager (optional)
    secrets_manager_region: Optional[str] = None  # AWS region for Secrets Manager
    secrets_manager_secret_name: Optional[
        str
    ] = None  # Name of secret in Secrets Manager

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate OpenAI API key format if provided."""
        if v is None:
            return None  # OpenAI is optional if using Bedrock
        v = v.strip()
        if not v or not v.startswith("sk-"):
            raise ValueError(
                "OpenAI API key appears to be invalid. "
                "OpenAI keys typically start with 'sk-'. "
                "Please check your OPENAI_API_KEY environment variable."
            )
        return v

    @field_validator("aws_access_key_id")
    @classmethod
    def validate_aws_access_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate AWS access key ID format if provided."""
        if v is None:
            return None  # Optional if using bearer token
        v = v.strip()
        if not v:
            return None
        # AWS Access Key IDs are typically 20 characters, alphanumeric
        if len(v) < 16 or len(v) > 128:
            raise ValueError(
                "AWS Access Key ID appears to be invalid. "
                "Access Key IDs are typically 20 characters long. "
                "Please check your AWS_ACCESS_KEY_ID environment variable."
            )
        return v

    @field_validator("aws_secret_access_key")
    @classmethod
    def validate_aws_secret_key(cls, v: Optional[str]) -> Optional[str]:
        """Validate AWS secret access key format if provided."""
        if v is None:
            return None  # Optional if using bearer token
        v = v.strip()
        if not v:
            return None
        # AWS Secret Access Keys are typically 40 characters
        if len(v) < 20:
            raise ValueError(
                "AWS Secret Access Key appears to be invalid. "
                "Secret Access Keys are typically 40 characters long. "
                "Please check your AWS_SECRET_ACCESS_KEY environment variable."
            )
        return v
    
    @field_validator("aws_bearer_token_bedrock")
    @classmethod
    def validate_bearer_token(cls, v: Optional[str]) -> Optional[str]:
        """Validate AWS Bedrock bearer token format if provided."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        # Basic validation - bearer tokens should have some length
        if len(v) < 10:
            raise ValueError(
                "AWS Bedrock bearer token appears to be invalid. "
                "Please check your AWS_BEARER_TOKEN_BEDROCK environment variable."
            )
        return v

    @field_validator("aws_region")
    @classmethod
    def validate_aws_region(cls, v: str) -> str:
        """Validate AWS region format."""
        if not v or not v.strip():
            return "us-west-2"  # Default region

        v = v.strip()
        # Basic AWS region format validation (e.g., us-east-1, eu-west-1)
        region_pattern = re.compile(r"^[a-z]{2}-[a-z]+-[0-9]+$")
        if not region_pattern.match(v):
            raise ValueError(
                f"AWS region '{v}' appears to be invalid. "
                "AWS regions follow the format 'us-east-1', 'eu-west-1', etc. "
                "Please check your AWS_REGION environment variable."
            )
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(
                f"Invalid log level '{v}'. Must be one of: {', '.join(valid_levels)}"
            )
        return v_upper

    @field_validator("rate_limit_per_minute", "rate_limit_per_hour")
    @classmethod
    def validate_rate_limit(cls, v: int) -> int:
        """Validate rate limit values."""
        if v < 1:
            raise ValueError("Rate limit must be at least 1 request")
        if v > 100000:
            raise ValueError("Rate limit cannot exceed 100,000 requests")
        return v

    def get_cors_origins_list(self) -> list:
        """Parse CORS origins string into a list."""
        if not self.cors_origins:
            return []
        return [
            origin.strip() for origin in self.cors_origins.split(",") if origin.strip()
        ]

    def get_cors_methods_list(self) -> list:
        """Parse CORS methods string into a list."""
        if self.cors_allow_methods == "*":
            return ["*"]
        return [
            method.strip()
            for method in self.cors_allow_methods.split(",")
            if method.strip()
        ]

    def get_cors_headers_list(self) -> list:
        """Parse CORS headers string into a list."""
        if self.cors_allow_headers == "*":
            return ["*"]
        return [
            header.strip()
            for header in self.cors_allow_headers.split(",")
            if header.strip()
        ]

    def model_post_init(self, __context) -> None:
        """Validate that at least one AWS authentication method is provided."""
        has_bearer_token = bool(self.aws_bearer_token_bedrock)
        has_access_keys = bool(self.aws_access_key_id and self.aws_secret_access_key)
        
        if not has_bearer_token and not has_access_keys:
            # Check if using default credential chain (no explicit credentials)
            # This is OK if running on EC2, Lambda, or with AWS profile configured
            import os
            if not os.getenv("AWS_PROFILE") and not os.getenv("AWS_ROLE_ARN"):
                raise ValueError(
                    "AWS authentication required. Provide either:\n"
                    "  - AWS_BEARER_TOKEN_BEDROCK (for Bedrock API key), OR\n"
                    "  - AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY (for traditional credentials)\n"
                    "  - Or configure AWS_PROFILE/AWS_ROLE_ARN for default credential chain"
                )

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.

    Raises:
        ValidationError: If required environment variables are missing or invalid.
    """
    try:
        return Settings()
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_messages.append(f"{field}: {message}")

        raise ValueError(
            "Configuration validation failed:\n"
            + "\n".join(error_messages)
            + "\n\nPlease check your environment variables or .env file."
        ) from e
