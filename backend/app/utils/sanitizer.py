"""
Input sanitization utilities for security with 2025 standards.

Features:
- Character whitelisting
- Command injection protection
- Path traversal prevention
- XSS protection
- SQL injection prevention
"""
import re
from typing import Optional, Set

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

# Character whitelists for different input types
ALPHANUMERIC_CHARSET: Set[str] = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
SESSION_ID_CHARSET: Set[str] = ALPHANUMERIC_CHARSET | set("-_")
SAFE_TEXT_CHARSET: Set[str] = ALPHANUMERIC_CHARSET | set(" .,!?;:'-\"()[]{}@#$%&*+=\n\t")

# Command injection patterns (blacklist)
COMMAND_INJECTION_PATTERNS = [
    r";\s*\w+",  # Command chaining with semicolon
    r"\|\s*\w+",  # Pipe to command
    r"&&\s*\w+",  # AND command
    r"\|\|\s*\w+",  # OR command
    r"`[^`]*`",  # Backtick command substitution
    r"\$\([^\)]*\)",  # $() command substitution
    r">\s*[\w/]",  # Output redirection
    r"<\s*[\w/]",  # Input redirection
    r"\r\n|\n|\r",  # Newline injection (in certain contexts)
]

# SQL injection patterns (blacklist)
SQL_INJECTION_PATTERNS = [
    r"('\s*(or|and)\s+'|'\s*or\s*'1'\s*=\s*'1)",  # SQL OR injection
    r"--",  # SQL comment
    r"/\*.*\*/",  # SQL block comment
    r";\s*(drop|delete|update|insert)",  # SQL commands
    r"(union|select|from|where)\s+",  # SQL keywords
]


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


def whitelist_characters(text: str, allowed_chars: Set[str]) -> str:
    """
    Filter text to only allowed characters (whitelist approach).

    Args:
        text: Input text
        allowed_chars: Set of allowed characters

    Returns:
        Filtered text with only allowed characters
    """
    return ''.join(char for char in text if char in allowed_chars)


def detect_command_injection(text: str) -> bool:
    """
    Detect potential command injection attempts.

    Args:
        text: Text to check

    Returns:
        True if potential command injection detected, False otherwise
    """
    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_sql_injection(text: str) -> bool:
    """
    Detect potential SQL injection attempts.

    Args:
        text: Text to check

    Returns:
        True if potential SQL injection detected, False otherwise
    """
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_path_traversal(text: str) -> bool:
    """
    Detect potential path traversal attempts.

    Args:
        text: Text to check

    Returns:
        True if potential path traversal detected, False otherwise
    """
    path_traversal_patterns = [
        r"\.\./",  # ../
        r"\.\./",  # ..\
        r"%2e%2e/",  # URL encoded ../
        r"%2e%2e\\",  # URL encoded ..\
        r"~",  # Home directory
        r"/etc/",  # System files
        r"/proc/",  # System files
        r"C:\\",  # Windows paths
    ]

    for pattern in path_traversal_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def sanitize_strict(text: str, max_length: Optional[int] = None) -> str:
    """
    Strict sanitization with character whitelisting (2025 security standard).

    Args:
        text: Input text to sanitize
        max_length: Maximum length

    Returns:
        Sanitized text with only safe characters

    Raises:
        ValueError: If injection attempts detected
    """
    if not isinstance(text, str):
        return ""

    # Check for injection attempts
    if detect_command_injection(text):
        raise ValueError("Potential command injection detected")

    if detect_sql_injection(text):
        raise ValueError("Potential SQL injection detected")

    if detect_path_traversal(text):
        raise ValueError("Potential path traversal detected")

    # Whitelist safe characters
    sanitized = whitelist_characters(text, SAFE_TEXT_CHARSET)

    # Apply additional sanitization
    sanitized = sanitize_text(sanitized, max_length)

    return sanitized


def sanitize_alphanumeric(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize to alphanumeric characters only.

    Args:
        text: Input text
        max_length: Maximum length

    Returns:
        Alphanumeric-only text
    """
    sanitized = whitelist_characters(text, ALPHANUMERIC_CHARSET)

    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized
