"""
Secure file operations with 2025 security standards.

Features:
- Path traversal prevention
- Atomic writes
- Secure file permissions (0o600)
- Rate limiting on file operations
- Command injection protection
- Audit logging
"""
import os
import tempfile
import shutil
import hashlib
import logging
from pathlib import Path
from typing import Optional, Union
from datetime import datetime, timedelta
from threading import Lock

from app.utils.audit_logger import audit_logger, AuditSeverity

logger = logging.getLogger(__name__)


class FileOperationRateLimiter:
    """Rate limiter for file operations to prevent abuse."""

    def __init__(self, max_ops_per_minute: int = 100):
        """
        Initialize rate limiter.

        Args:
            max_ops_per_minute: Maximum file operations per minute
        """
        self.max_ops = max_ops_per_minute
        self.operations = []
        self.lock = Lock()

    def check_rate_limit(self) -> bool:
        """
        Check if operation is within rate limit.

        Returns:
            True if allowed, False if rate limit exceeded
        """
        with self.lock:
            now = datetime.now()
            # Remove operations older than 1 minute
            self.operations = [
                op_time for op_time in self.operations
                if now - op_time < timedelta(minutes=1)
            ]

            if len(self.operations) >= self.max_ops:
                logger.warning(f"File operation rate limit exceeded: {len(self.operations)}/{self.max_ops}")
                return False

            self.operations.append(now)
            return True


class SecureFileHandler:
    """
    Secure file handler with comprehensive security controls.

    Prevents:
    - Path traversal attacks
    - Command injection
    - Race conditions
    - Unauthorized access
    """

    # Allowed base directories (whitelist)
    ALLOWED_BASE_DIRS = [
        "/var/lib/customer-service-ai",
        "/tmp/customer-service-ai",
        "./chroma_db",
        "./data",
    ]

    # Blocked path components (blacklist)
    BLOCKED_COMPONENTS = [
        "..",
        "~",
        "${",  # Environment variable expansion
        "$(",  # Command substitution
        "`",   # Command substitution
        "|",   # Pipe
        ";",   # Command separator
        "&",   # Background execution
        ">",   # Redirection
        "<",   # Redirection
        "\n",  # Newline injection
        "\r",  # Carriage return injection
    ]

    def __init__(self, base_directory: Optional[str] = None):
        """
        Initialize secure file handler.

        Args:
            base_directory: Base directory for file operations
        """
        self.base_directory = Path(base_directory) if base_directory else Path.cwd()
        self.rate_limiter = FileOperationRateLimiter()

        # Validate base directory
        if not self._is_safe_base_directory(str(self.base_directory)):
            raise ValueError(f"Base directory not in allowed list: {self.base_directory}")

    def _is_safe_base_directory(self, path: str) -> bool:
        """
        Check if base directory is in allowed list.

        Args:
            path: Directory path to check

        Returns:
            True if safe, False otherwise
        """
        abs_path = os.path.abspath(path)
        for allowed_dir in self.ALLOWED_BASE_DIRS:
            allowed_abs = os.path.abspath(allowed_dir)
            if abs_path.startswith(allowed_abs):
                return True
        return False

    def _validate_path(self, file_path: str) -> Path:
        """
        Validate and sanitize file path to prevent path traversal.

        Args:
            file_path: File path to validate

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is unsafe
        """
        # Check for blocked components
        for blocked in self.BLOCKED_COMPONENTS:
            if blocked in file_path:
                audit_logger.log_security_event(
                    event_type="violation",
                    severity=AuditSeverity.HIGH,
                    description=f"Path traversal attempt detected: {file_path}",
                    details={"blocked_component": blocked}
                )
                raise ValueError(f"Path contains blocked component: {blocked}")

        # Resolve path and check it's within base directory
        try:
            full_path = (self.base_directory / file_path).resolve()
            base_resolved = self.base_directory.resolve()

            # Check if resolved path is within base directory
            if not str(full_path).startswith(str(base_resolved)):
                audit_logger.log_security_event(
                    event_type="violation",
                    severity=AuditSeverity.CRITICAL,
                    description="Path traversal attempt outside base directory",
                    details={
                        "requested_path": file_path,
                        "resolved_path": str(full_path),
                        "base_directory": str(base_resolved)
                    }
                )
                raise ValueError("Path traversal attempt detected")

            return full_path

        except Exception as e:
            logger.error(f"Path validation failed: {e}")
            raise ValueError(f"Invalid path: {file_path}")

    def _check_rate_limit(self) -> None:
        """
        Check rate limit for file operations.

        Raises:
            RuntimeError: If rate limit exceeded
        """
        if not self.rate_limiter.check_rate_limit():
            audit_logger.log_security_event(
                event_type="rate_limit",
                severity=AuditSeverity.MEDIUM,
                description="File operation rate limit exceeded"
            )
            raise RuntimeError("File operation rate limit exceeded")

    def _set_secure_permissions(self, file_path: Path) -> None:
        """
        Set secure file permissions (0o600 - owner read/write only).

        Args:
            file_path: Path to file
        """
        try:
            os.chmod(file_path, 0o600)
            logger.debug(f"Set secure permissions (0o600) on {file_path}")
        except Exception as e:
            logger.warning(f"Failed to set secure permissions on {file_path}: {e}")

    def read_file(self, file_path: str) -> bytes:
        """
        Securely read file contents.

        Args:
            file_path: Path to file (relative to base directory)

        Returns:
            File contents as bytes

        Raises:
            ValueError: If path is unsafe
            RuntimeError: If rate limit exceeded
            FileNotFoundError: If file doesn't exist
        """
        self._check_rate_limit()
        validated_path = self._validate_path(file_path)

        try:
            with open(validated_path, 'rb') as f:
                content = f.read()

            audit_logger.log_data_access(
                operation="read",
                resource=str(validated_path),
                success=True
            )

            return content

        except Exception as e:
            audit_logger.log_data_access(
                operation="read",
                resource=str(validated_path),
                success=False,
                error=str(e)
            )
            raise

    def write_file(self, file_path: str, content: Union[str, bytes], atomic: bool = True) -> None:
        """
        Securely write file with atomic operation.

        Args:
            file_path: Path to file (relative to base directory)
            content: Content to write
            atomic: Use atomic write (default: True)

        Raises:
            ValueError: If path is unsafe
            RuntimeError: If rate limit exceeded
        """
        self._check_rate_limit()
        validated_path = self._validate_path(file_path)

        # Ensure parent directory exists
        validated_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            if atomic:
                # Atomic write using temporary file and rename
                with tempfile.NamedTemporaryFile(
                    mode='wb' if isinstance(content, bytes) else 'w',
                    dir=validated_path.parent,
                    delete=False,
                    prefix='.tmp_',
                    suffix=validated_path.suffix
                ) as tmp_file:
                    tmp_path = Path(tmp_file.name)

                    # Write content
                    if isinstance(content, bytes):
                        tmp_file.write(content)
                    else:
                        tmp_file.write(content.encode('utf-8'))

                # Set secure permissions before rename
                self._set_secure_permissions(tmp_path)

                # Atomic rename
                tmp_path.replace(validated_path)

            else:
                # Direct write (non-atomic)
                mode = 'wb' if isinstance(content, bytes) else 'w'
                with open(validated_path, mode) as f:
                    if isinstance(content, bytes):
                        f.write(content)
                    else:
                        f.write(content)

                self._set_secure_permissions(validated_path)

            audit_logger.log_data_access(
                operation="write",
                resource=str(validated_path),
                success=True,
                record_count=1
            )

            logger.info(f"Successfully wrote file: {validated_path}")

        except Exception as e:
            audit_logger.log_data_access(
                operation="write",
                resource=str(validated_path),
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to write file {validated_path}: {e}")
            raise

    def delete_file(self, file_path: str, secure_delete: bool = True) -> None:
        """
        Securely delete file.

        Args:
            file_path: Path to file (relative to base directory)
            secure_delete: Overwrite before deletion (default: True)

        Raises:
            ValueError: If path is unsafe
            RuntimeError: If rate limit exceeded
        """
        self._check_rate_limit()
        validated_path = self._validate_path(file_path)

        try:
            if secure_delete and validated_path.exists():
                # Overwrite with random data before deletion
                file_size = validated_path.stat().st_size
                with open(validated_path, 'wb') as f:
                    f.write(os.urandom(file_size))

            # Delete file
            validated_path.unlink(missing_ok=True)

            audit_logger.log_data_access(
                operation="delete",
                resource=str(validated_path),
                success=True
            )

            logger.info(f"Successfully deleted file: {validated_path}")

        except Exception as e:
            audit_logger.log_data_access(
                operation="delete",
                resource=str(validated_path),
                success=False,
                error=str(e)
            )
            logger.error(f"Failed to delete file {validated_path}: {e}")
            raise

    def verify_file_integrity(self, file_path: str, expected_hash: str, algorithm: str = "sha256") -> bool:
        """
        Verify file integrity using hash.

        Args:
            file_path: Path to file
            expected_hash: Expected hash value
            algorithm: Hash algorithm (sha256, sha512)

        Returns:
            True if hash matches, False otherwise
        """
        validated_path = self._validate_path(file_path)

        try:
            content = validated_path.read_bytes()
            hasher = hashlib.new(algorithm)
            hasher.update(content)
            actual_hash = hasher.hexdigest()

            match = actual_hash == expected_hash

            audit_logger.log_data_access(
                operation="verify",
                resource=str(validated_path),
                success=match,
                details={"algorithm": algorithm}
            )

            return match

        except Exception as e:
            logger.error(f"File integrity check failed: {e}")
            return False


# Global secure file handler instance
secure_file_handler = SecureFileHandler()


__all__ = ["SecureFileHandler", "FileOperationRateLimiter", "secure_file_handler"]
