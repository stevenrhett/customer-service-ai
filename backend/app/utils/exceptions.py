"""
Custom exceptions for the Customer Service AI application.
"""
from typing import Optional


class CustomerServiceException(Exception):
    """Base exception for customer service errors."""
    def __init__(self, message: str, status_code: int = 500, details: Optional[dict] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AgentError(CustomerServiceException):
    """Exception raised when an agent encounters an error."""
    def __init__(self, message: str, agent_name: str, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)
        self.agent_name = agent_name


class VectorStoreError(CustomerServiceException):
    """Exception raised when vector store operations fail."""
    def __init__(self, message: str, collection_name: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)
        self.collection_name = collection_name


class SessionError(CustomerServiceException):
    """Exception raised when session operations fail."""
    def __init__(self, message: str, session_id: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message, status_code=400, details=details)
        self.session_id = session_id


class LLMError(CustomerServiceException):
    """Exception raised when LLM operations fail."""
    def __init__(self, message: str, provider: Optional[str] = None, details: Optional[dict] = None):
        super().__init__(message, status_code=500, details=details)
        self.provider = provider

