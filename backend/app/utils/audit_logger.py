"""
Audit logging system for tracking security-sensitive operations.

Provides comprehensive audit trail for:
- Authentication attempts
- Authorization decisions
- Data access
- Configuration changes
- System events
"""
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Types of audit events."""

    # Authentication events
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTH_LOGOUT = "auth.logout"

    # Authorization events
    AUTHZ_ALLOWED = "authz.allowed"
    AUTHZ_DENIED = "authz.denied"

    # Data access events
    DATA_READ = "data.read"
    DATA_WRITE = "data.write"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"

    # Configuration events
    CONFIG_CHANGE = "config.change"
    SETTINGS_UPDATE = "settings.update"

    # System events
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"

    # Security events
    SECURITY_VIOLATION = "security.violation"
    RATE_LIMIT_EXCEEDED = "security.rate_limit"
    SUSPICIOUS_ACTIVITY = "security.suspicious"

    # API events
    API_CALL = "api.call"
    API_ERROR = "api.error"


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLogger:
    """
    Audit logger for security-sensitive operations.

    Creates structured audit logs for compliance and security monitoring.
    """

    def __init__(self, service_name: str = "customer-service-ai"):
        """
        Initialize audit logger.

        Args:
            service_name: Name of the service for audit logs
        """
        self.service_name = service_name
        self.logger = logging.getLogger(f"audit.{service_name}")

    def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """
        Log an audit event.

        Args:
            event_type: Type of audit event
            severity: Severity level
            user_id: User identifier (if applicable)
            ip_address: Source IP address
            resource: Resource being accessed/modified
            action: Action being performed
            result: Result of the action (success/failure)
            details: Additional details as dictionary
            **kwargs: Additional fields to include in audit log
        """
        # Build audit log entry
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "service": self.service_name,
            "event_type": event_type.value,
            "severity": severity.value,
            "result": result,
        }

        # Add optional fields
        if user_id:
            audit_entry["user_id"] = user_id
        if ip_address:
            audit_entry["ip_address"] = ip_address
        if resource:
            audit_entry["resource"] = resource
        if action:
            audit_entry["action"] = action
        if details:
            audit_entry["details"] = details

        # Add any additional kwargs
        audit_entry.update(kwargs)

        # Convert to JSON for structured logging
        log_message = json.dumps(audit_entry, default=str)

        # Log at appropriate level based on severity
        if severity == AuditSeverity.CRITICAL:
            self.logger.critical(log_message)
        elif severity == AuditSeverity.HIGH:
            self.logger.error(log_message)
        elif severity == AuditSeverity.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

    def log_authentication(
        self,
        success: bool,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        auth_method: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Log authentication event.

        Args:
            success: Whether authentication succeeded
            user_id: User identifier
            ip_address: Source IP address
            auth_method: Authentication method used (api_key, jwt, etc.)
            reason: Reason for failure (if applicable)
        """
        event_type = AuditEventType.AUTH_SUCCESS if success else AuditEventType.AUTH_FAILURE
        severity = AuditSeverity.LOW if success else AuditSeverity.HIGH

        details = {}
        if auth_method:
            details["auth_method"] = auth_method
        if reason:
            details["reason"] = reason

        self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            action="authenticate",
            result="success" if success else "failure",
            details=details
        )

    def log_authorization(
        self,
        allowed: bool,
        user_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        ip_address: Optional[str] = None,
        reason: Optional[str] = None
    ) -> None:
        """
        Log authorization decision.

        Args:
            allowed: Whether access was allowed
            user_id: User identifier
            resource: Resource being accessed
            action: Action being performed
            ip_address: Source IP address
            reason: Reason for denial (if applicable)
        """
        event_type = AuditEventType.AUTHZ_ALLOWED if allowed else AuditEventType.AUTHZ_DENIED
        severity = AuditSeverity.LOW if allowed else AuditSeverity.MEDIUM

        details = {}
        if reason:
            details["reason"] = reason

        self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=action,
            result="allowed" if allowed else "denied",
            details=details
        )

    def log_data_access(
        self,
        operation: str,
        resource: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        record_count: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Log data access operation.

        Args:
            operation: Type of operation (read, write, delete, export)
            resource: Resource being accessed
            user_id: User identifier
            ip_address: Source IP address
            record_count: Number of records affected
            success: Whether operation succeeded
            error: Error message (if failed)
        """
        event_type_map = {
            "read": AuditEventType.DATA_READ,
            "write": AuditEventType.DATA_WRITE,
            "delete": AuditEventType.DATA_DELETE,
            "export": AuditEventType.DATA_EXPORT,
        }

        event_type = event_type_map.get(operation.lower(), AuditEventType.DATA_READ)
        severity = AuditSeverity.LOW if operation == "read" else AuditSeverity.MEDIUM

        details = {}
        if record_count is not None:
            details["record_count"] = record_count
        if error:
            details["error"] = error
            severity = AuditSeverity.HIGH

        self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            resource=resource,
            action=operation,
            result="success" if success else "failure",
            details=details
        )

    def log_security_event(
        self,
        event_type: str,
        severity: AuditSeverity,
        description: str,
        ip_address: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log security-related event.

        Args:
            event_type: Type of security event
            severity: Severity level
            description: Description of the event
            ip_address: Source IP address
            user_id: User identifier (if known)
            details: Additional details
        """
        event_type_map = {
            "violation": AuditEventType.SECURITY_VIOLATION,
            "rate_limit": AuditEventType.RATE_LIMIT_EXCEEDED,
            "suspicious": AuditEventType.SUSPICIOUS_ACTIVITY,
        }

        event = event_type_map.get(event_type.lower(), AuditEventType.SECURITY_VIOLATION)

        log_details = {"description": description}
        if details:
            log_details.update(details)

        self.log_event(
            event_type=event,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            action="security_event",
            result="detected",
            details=log_details
        )

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        response_time_ms: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """
        Log API call.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            status_code: HTTP status code
            user_id: User identifier
            ip_address: Source IP address
            response_time_ms: Response time in milliseconds
            error: Error message (if failed)
        """
        success = 200 <= status_code < 400
        event_type = AuditEventType.API_CALL if success else AuditEventType.API_ERROR

        # Determine severity based on status code
        if status_code >= 500:
            severity = AuditSeverity.HIGH
        elif status_code >= 400:
            severity = AuditSeverity.MEDIUM
        else:
            severity = AuditSeverity.LOW

        details = {
            "method": method,
            "status_code": status_code,
        }

        if response_time_ms is not None:
            details["response_time_ms"] = response_time_ms
        if error:
            details["error"] = error

        self.log_event(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            ip_address=ip_address,
            resource=endpoint,
            action=method,
            result="success" if success else "error",
            details=details
        )


# Global audit logger instance
audit_logger = AuditLogger()


__all__ = [
    "AuditLogger",
    "AuditEventType",
    "AuditSeverity",
    "audit_logger"
]
