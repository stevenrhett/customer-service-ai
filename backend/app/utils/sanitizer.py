"""
Input sanitization utilities for security.
"""
import re
from typing import Optional

# Try to import html_sanitizer, fallback to basic sanitization if not available
try:
    from html_sanitizer import Sanitizer

    HAS_SANITIZER = True
    # Configure HTML sanitizer (strict mode for user input)
    sanitizer = Sanitizer(
        {
            "tags": set(),  # Remove all HTML tags
            "attributes": {},
            "empty": True,
            "separate": True,
            "strip_whitespace": True,
        }
    )
except ImportError:
    HAS_SANITIZER = False
    sanitizer = None

# Maximum lengths
MAX_MESSAGE_LENGTH = 10000  # 10KB
MAX_SESSION_ID_LENGTH = 128
MAX_MESSAGES_IN_HISTORY = 100


def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input text.

    Args:
        text: Input text to sanitize
        max_length: Maximum length (will truncate if exceeded)

    Returns:
        Sanitized text
    """
    if not isinstance(text, str):
        return ""

    # Remove HTML tags and scripts
    if HAS_SANITIZER and sanitizer:
        sanitized = sanitizer.sanitize(text)
    else:
        # Fallback: basic HTML tag removal using regex
        sanitized = re.sub(r"<[^>]+>", "", text)

    # Remove control characters except newlines and tabs
    sanitized = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", sanitized)

    # Normalize whitespace (but preserve newlines)
    sanitized = re.sub(
        r"[ \t]+", " ", sanitized
    )  # Multiple spaces/tabs to single space
    sanitized = re.sub(r"[ \t]*\n[ \t]*", "\n", sanitized)  # Normalize newlines

    # Strip leading/trailing whitespace
    sanitized = sanitized.strip()

    # Apply length limit if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        # Truncate at word boundary if possible
        last_space = sanitized.rfind(" ")
        if last_space > max_length * 0.9:  # If space is near the end
            sanitized = sanitized[:last_space] + "..."

    return sanitized


def sanitize_session_id(session_id: str) -> str:
    """
    Sanitize session ID.

    Args:
        session_id: Session ID to sanitize

    Returns:
        Sanitized session ID
    """
    if not isinstance(session_id, str):
        return ""

    # Only allow alphanumeric, hyphens, and underscores
    sanitized = re.sub(r"[^a-zA-Z0-9\-_]", "", session_id)

    # Limit length
    if len(sanitized) > MAX_SESSION_ID_LENGTH:
        sanitized = sanitized[:MAX_SESSION_ID_LENGTH]

    return sanitized


def validate_message_length(text: str) -> bool:
    """
    Validate that message length is within limits.

    Args:
        text: Message text to validate

    Returns:
        True if valid, False otherwise
    """
    return len(text) <= MAX_MESSAGE_LENGTH and len(text) > 0


def validate_message_history(messages: list) -> bool:
    """
    Validate message history size.

    Args:
        messages: List of messages

    Returns:
        True if valid, False otherwise
    """
    return len(messages) <= MAX_MESSAGES_IN_HISTORY
