"""
Production environment validation.

Validates that all required security settings are configured correctly
before starting the application in production mode.
"""
import logging
import secrets
from typing import List, Tuple
from app.config import get_settings

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when production validation fails."""

    pass


class ProductionValidator:
    """
    Validates production environment configuration.

    Ensures all security requirements are met before deployment.
    """

    def __init__(self):
        """Initialize production validator."""
        self.settings = get_settings()
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_all(self, strict: bool = True) -> Tuple[bool, List[str], List[str]]:
        """
        Run all production validation checks.

        Args:
            strict: If True, warnings are treated as errors

        Returns:
            Tuple of (is_valid, errors, warnings)

        Raises:
            ValidationError: If validation fails in strict mode
        """
        self.errors = []
        self.warnings = []

        # Only validate if in production
        if self.settings.environment.lower() != "production":
            logger.info("Skipping production validation (not in production environment)")
            return True, [], []

        logger.info("Running production environment validation...")

        # Run all validation checks
        self._validate_authentication()
        self._validate_secrets()
        self._validate_https()
        self._validate_cors()
        self._validate_rate_limiting()
        self._validate_logging()
        self._validate_encryption()
        self._validate_aws_config()

        # Check results
        if self.errors:
            error_msg = "\n".join([f"  - {error}" for error in self.errors])
            logger.error(f"Production validation FAILED:\n{error_msg}")

            if strict:
                raise ValidationError(
                    f"Production environment validation failed:\n{error_msg}\n\n"
                    f"Fix these issues before deploying to production."
                )

        if self.warnings:
            warning_msg = "\n".join([f"  - {warning}" for warning in self.warnings])
            logger.warning(f"Production validation warnings:\n{warning_msg}")

            if strict:
                raise ValidationError(
                    f"Production environment has warnings:\n{warning_msg}\n\n"
                    f"Address these warnings or run with strict=False to ignore."
                )

        if not self.errors and not self.warnings:
            logger.info("✓ Production environment validation PASSED")

        return len(self.errors) == 0, self.errors, self.warnings

    def _validate_authentication(self) -> None:
        """Validate authentication configuration."""
        if not getattr(self.settings, 'require_authentication', False):
            self.errors.append(
                "Authentication is disabled. Set REQUIRE_AUTHENTICATION=true for production"
            )

        # Check for API keys
        api_keys = getattr(self.settings, 'api_keys', None)
        if not api_keys or api_keys.strip() == "":
            self.errors.append(
                "No API keys configured. Set API_KEYS environment variable"
            )

        # Check JWT secret
        jwt_secret = getattr(self.settings, 'jwt_secret_key', None)
        if not jwt_secret:
            self.warnings.append(
                "No JWT secret key configured. Set JWT_SECRET_KEY for token support"
            )
        elif jwt_secret == 'dev-secret-change-in-production':
            self.errors.append(
                "Using default JWT secret key. Set a secure JWT_SECRET_KEY"
            )
        elif len(jwt_secret) < 32:
            self.warnings.append(
                "JWT secret key is short. Use at least 32 characters for security"
            )

    def _validate_secrets(self) -> None:
        """Validate secrets management."""
        # Check if using default secrets
        if self.settings.openai_api_key:
            if self.settings.openai_api_key.startswith("sk-"):
                # Valid format, but warn if using env vars
                if not getattr(self.settings, 'enable_secrets_manager', False):
                    self.warnings.append(
                        "API keys stored in environment variables. "
                        "Consider using AWS Secrets Manager (ENABLE_SECRETS_MANAGER=true)"
                    )

        # Check encryption key for data at rest
        if getattr(self.settings, 'enable_encryption_at_rest', False):
            encryption_key = getattr(self.settings, 'encryption_key', None)
            if not encryption_key:
                self.errors.append(
                    "Encryption at rest enabled but no encryption key provided. "
                    "Set ENCRYPTION_KEY environment variable"
                )
            elif len(encryption_key) < 32:
                self.errors.append(
                    "Encryption key too short. Use at least 32 bytes"
                )

    def _validate_https(self) -> None:
        """Validate HTTPS configuration."""
        enforce_https = getattr(self.settings, 'enforce_https', False)

        if not enforce_https:
            self.errors.append(
                "HTTPS not enforced. Set ENFORCE_HTTPS=true for production"
            )

        # Check CORS origins for HTTPS
        cors_origins = self.settings.get_cors_origins_list()
        for origin in cors_origins:
            if origin.startswith('http://') and 'localhost' not in origin:
                self.errors.append(
                    f"Insecure HTTP origin in CORS: {origin}. Use HTTPS in production"
                )

    def _validate_cors(self) -> None:
        """Validate CORS configuration."""
        cors_origins = self.settings.get_cors_origins_list()

        if '*' in cors_origins or not cors_origins:
            self.errors.append(
                "CORS allows all origins (*). Specify explicit origins in CORS_ORIGINS"
            )

        if 'localhost' in str(cors_origins):
            self.warnings.append(
                "CORS includes localhost. Remove localhost origins from production"
            )

    def _validate_rate_limiting(self) -> None:
        """Validate rate limiting configuration."""
        if not self.settings.rate_limit_enabled:
            self.errors.append(
                "Rate limiting is disabled. Enable with RATE_LIMIT_ENABLED=true"
            )

        # Check rate limits are reasonable
        if self.settings.rate_limit_per_minute > 1000:
            self.warnings.append(
                f"High rate limit: {self.settings.rate_limit_per_minute}/min. "
                "Consider lowering for production"
            )

    def _validate_logging(self) -> None:
        """Validate logging configuration."""
        log_level = self.settings.log_level.upper()

        if log_level == "DEBUG":
            self.warnings.append(
                "Logging level is DEBUG. Use INFO or WARNING for production"
            )

        # Check PII masking
        mask_pii = getattr(self.settings, 'mask_pii_in_logs', True)
        if not mask_pii:
            self.errors.append(
                "PII masking in logs is disabled. Set MASK_PII_IN_LOGS=true"
            )

    def _validate_encryption(self) -> None:
        """Validate encryption settings."""
        # Recommend encryption at rest
        enable_encryption = getattr(self.settings, 'enable_encryption_at_rest', False)
        if not enable_encryption:
            self.warnings.append(
                "Encryption at rest is disabled. Consider enabling for sensitive data"
            )

    def _validate_aws_config(self) -> None:
        """Validate AWS configuration."""
        # Check for hardcoded credentials (not recommended)
        if self.settings.aws_access_key_id and self.settings.aws_secret_access_key:
            self.warnings.append(
                "Using hardcoded AWS credentials. "
                "Consider using IAM roles or temporary credentials"
            )

        # Validate region
        if not self.settings.aws_region:
            self.errors.append("AWS_REGION not configured")


def validate_production_environment(strict: bool = True) -> None:
    """
    Validate production environment on startup.

    Args:
        strict: If True, warnings are treated as errors

    Raises:
        ValidationError: If validation fails
    """
    validator = ProductionValidator()
    validator.validate_all(strict=strict)


__all__ = ["ProductionValidator", "ValidationError", "validate_production_environment"]
