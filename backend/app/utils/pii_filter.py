"""
PII (Personally Identifiable Information) filtering and masking utilities.

Detects and masks sensitive information in logs and user inputs to comply
with privacy regulations (GDPR, CCPA, etc.).
"""
import re
import logging
from typing import Dict, Pattern, List, Tuple

logger = logging.getLogger(__name__)


class PIIFilter:
    """
    Filter and mask Personally Identifiable Information (PII) in text.

    Detects and masks:
    - Email addresses
    - Phone numbers (US and international formats)
    - Credit card numbers
    - Social Security Numbers (SSN)
    - IP addresses
    - API keys and tokens
    - Passwords
    - URLs with sensitive data
    """

    def __init__(self, mask_char: str = "*"):
        """
        Initialize PII filter.

        Args:
            mask_char: Character to use for masking (default: *)
        """
        self.mask_char = mask_char
        self._patterns = self._compile_patterns()

    def _compile_patterns(self) -> Dict[str, Pattern]:
        """
        Compile regex patterns for PII detection.

        Returns:
            Dictionary of compiled regex patterns
        """
        return {
            # Email addresses
            "email": re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                re.IGNORECASE
            ),

            # Phone numbers (US: (123) 456-7890, 123-456-7890, 1234567890)
            "phone_us": re.compile(
                r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
            ),

            # International phone numbers
            "phone_intl": re.compile(
                r'\+\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}'
            ),

            # Credit card numbers (with optional spaces/dashes)
            "credit_card": re.compile(
                r'\b(?:\d{4}[-\s]?){3}\d{4}\b'
            ),

            # Social Security Numbers (US)
            "ssn": re.compile(
                r'\b\d{3}-\d{2}-\d{4}\b'
            ),

            # IPv4 addresses
            "ipv4": re.compile(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            ),

            # IPv6 addresses
            "ipv6": re.compile(
                r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b'
            ),

            # API keys (common formats)
            "api_key": re.compile(
                r'\b(?:api[_-]?key|apikey|api[_-]?secret)[\s:=]+["\']?([A-Za-z0-9_\-]{20,})["\']?\b',
                re.IGNORECASE
            ),

            # AWS Access Keys
            "aws_key": re.compile(
                r'\b(AKIA[0-9A-Z]{16})\b'
            ),

            # Bearer tokens
            "bearer_token": re.compile(
                r'\bBearer\s+([A-Za-z0-9_\-\.]+)\b',
                re.IGNORECASE
            ),

            # Passwords in common formats
            "password": re.compile(
                r'\b(?:password|passwd|pwd)[\s:=]+["\']?([^\s"\']{8,})["\']?\b',
                re.IGNORECASE
            ),

            # JWT tokens
            "jwt": re.compile(
                r'\beyJ[A-Za-z0-9_-]*\.eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]*\b'
            ),

            # URLs with sensitive query parameters
            "sensitive_url": re.compile(
                r'https?://[^\s]*[?&](?:token|key|secret|password|api_key)=[^&\s]*',
                re.IGNORECASE
            ),
        }

    def mask_text(self, text: str, keep_domain: bool = False) -> str:
        """
        Mask PII in the given text.

        Args:
            text: Text to mask
            keep_domain: For emails, keep the domain visible (e.g., ***@example.com)

        Returns:
            Text with PII masked
        """
        if not text:
            return text

        masked_text = text

        # Mask each type of PII
        for pii_type, pattern in self._patterns.items():
            if pii_type == "email" and keep_domain:
                # Mask email but keep domain
                masked_text = self._mask_email_keep_domain(masked_text, pattern)
            elif pii_type in ["api_key", "password", "bearer_token"]:
                # For key-value patterns, mask only the value
                masked_text = self._mask_key_value(masked_text, pattern)
            else:
                # Completely mask the match
                masked_text = pattern.sub(self._mask_string, masked_text)

        return masked_text

    def _mask_string(self, match: re.Match) -> str:
        """
        Mask a regex match with asterisks.

        Args:
            match: Regex match object

        Returns:
            Masked string
        """
        matched_text = match.group(0)
        # Keep first and last character visible for debugging
        if len(matched_text) <= 4:
            return self.mask_char * len(matched_text)

        return (
            matched_text[0] +
            self.mask_char * (len(matched_text) - 2) +
            matched_text[-1]
        )

    def _mask_email_keep_domain(self, text: str, pattern: Pattern) -> str:
        """
        Mask email addresses but keep domain visible.

        Args:
            text: Text containing emails
            pattern: Compiled email regex pattern

        Returns:
            Text with emails partially masked
        """
        def mask_email(match: re.Match) -> str:
            email = match.group(0)
            if '@' not in email:
                return self.mask_char * len(email)

            local, domain = email.rsplit('@', 1)
            # Mask local part, keep domain
            masked_local = self.mask_char * len(local)
            return f"{masked_local}@{domain}"

        return pattern.sub(mask_email, text)

    def _mask_key_value(self, text: str, pattern: Pattern) -> str:
        """
        Mask only the value in key-value pairs.

        Args:
            text: Text containing key-value pairs
            pattern: Compiled regex pattern

        Returns:
            Text with values masked
        """
        def mask_value(match: re.Match) -> str:
            full_match = match.group(0)
            # If there's a captured group, mask only that
            if match.groups():
                value = match.group(1)
                masked_value = self.mask_char * len(value)
                return full_match.replace(value, masked_value)
            # Otherwise mask entire match
            return self.mask_char * len(full_match)

        return pattern.sub(mask_value, text)

    def detect_pii(self, text: str) -> List[Tuple[str, str]]:
        """
        Detect PII in text without masking.

        Args:
            text: Text to analyze

        Returns:
            List of (pii_type, matched_text) tuples
        """
        detections = []

        for pii_type, pattern in self._patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                detections.append((pii_type, match.group(0)))

        return detections

    def has_pii(self, text: str) -> bool:
        """
        Check if text contains any PII.

        Args:
            text: Text to check

        Returns:
            True if PII detected, False otherwise
        """
        if not text:
            return False

        for pattern in self._patterns.values():
            if pattern.search(text):
                return True

        return False


class PIILoggingFilter(logging.Filter):
    """
    Logging filter to automatically mask PII in log messages.

    Usage:
        logger = logging.getLogger(__name__)
        logger.addFilter(PIILoggingFilter())
    """

    def __init__(self, name: str = "", mask_char: str = "*"):
        """
        Initialize PII logging filter.

        Args:
            name: Filter name
            mask_char: Character to use for masking
        """
        super().__init__(name)
        self.pii_filter = PIIFilter(mask_char=mask_char)

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter and mask PII in log records.

        Args:
            record: Log record to filter

        Returns:
            True to allow the record to be logged
        """
        # Mask PII in the message
        if hasattr(record, 'msg') and record.msg:
            if isinstance(record.msg, str):
                record.msg = self.pii_filter.mask_text(record.msg, keep_domain=True)

        # Mask PII in arguments
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self.pii_filter.mask_text(str(v), keep_domain=True) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, (list, tuple)):
                record.args = tuple(
                    self.pii_filter.mask_text(str(arg), keep_domain=True) if isinstance(arg, str) else arg
                    for arg in record.args
                )

        return True


# Global PII filter instance
pii_filter = PIIFilter()


__all__ = ["PIIFilter", "PIILoggingFilter", "pii_filter"]
