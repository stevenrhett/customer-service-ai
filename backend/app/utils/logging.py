"""
Centralized logging configuration for the application.
Compatible with uvicorn logging with PII filtering support.
"""
import logging
import sys
from typing import Optional

from app.config import get_settings

# Configure root logger
_logger_configured = False


def configure_logging(level: str = "INFO", enable_pii_masking: bool = None) -> None:
    """
    Configure application-wide logging with optional PII filtering.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_pii_masking: Enable PII masking in logs (default: from settings)
    """
    global _logger_configured

    if _logger_configured:
        return

    log_level = getattr(logging, level.upper(), logging.INFO)

    # Determine if PII masking should be enabled
    if enable_pii_masking is None:
        try:
            settings = get_settings()
            enable_pii_masking = getattr(settings, 'mask_pii_in_logs', True)
        except Exception:
            # Fallback to True if settings unavailable
            enable_pii_masking = True

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Add PII filter if enabled
    if enable_pii_masking:
        try:
            from app.utils.pii_filter import PIILoggingFilter
            pii_filter = PIILoggingFilter()
            handler.addFilter(pii_filter)
            # Also add to root logger
            logging.getLogger().addFilter(pii_filter)
        except ImportError:
            # PII filter not available, continue without it
            pass

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        handlers=[handler],
    )

    # Set levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    _logger_configured = True


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    if not _logger_configured:
        configure_logging()

    return logging.getLogger(name)
