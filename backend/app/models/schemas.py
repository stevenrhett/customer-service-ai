"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal
from datetime import datetime
from app.utils.sanitizer import sanitize_text, sanitize_session_id, validate_message_length, MAX_MESSAGE_LENGTH, MAX_MESSAGES_IN_HISTORY


class Message(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None
    
    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Sanitize and validate message content."""
        if not isinstance(v, str):
            raise ValueError("Content must be a string")
        
        # Sanitize the content
        sanitized = sanitize_text(v, max_length=MAX_MESSAGE_LENGTH)
        
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Message content cannot be empty")
        
        if not validate_message_length(sanitized):
            raise ValueError(f"Message content exceeds maximum length of {MAX_MESSAGE_LENGTH} characters")
        
        return sanitized


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    message: str = Field(..., min_length=1, description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    conversation_history: Optional[List[Message]] = Field(default_factory=list, description="Previous messages in the conversation")
    
    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Sanitize and validate the main message."""
        if not isinstance(v, str):
            raise ValueError("Message must be a string")
        
        # Sanitize the message
        sanitized = sanitize_text(v, max_length=MAX_MESSAGE_LENGTH)
        
        if not sanitized or len(sanitized.strip()) == 0:
            raise ValueError("Message cannot be empty")
        
        if not validate_message_length(sanitized):
            raise ValueError(f"Message exceeds maximum length of {MAX_MESSAGE_LENGTH} characters")
        
        return sanitized
    
    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize session ID."""
        if v is None:
            return None
        
        if not isinstance(v, str):
            raise ValueError("Session ID must be a string")
        
        return sanitize_session_id(v)
    
    @field_validator("conversation_history")
    @classmethod
    def validate_history(cls, v: Optional[List[Message]]) -> Optional[List[Message]]:
        """Validate conversation history size."""
        if v is None:
            return []
        
        if len(v) > MAX_MESSAGES_IN_HISTORY:
            raise ValueError(f"Conversation history cannot exceed {MAX_MESSAGES_IN_HISTORY} messages")
        
        return v


class ChatResponse(BaseModel):
    """Response model for the chat endpoint."""
    response: str = Field(..., description="AI assistant's response")
    agent_used: str = Field(..., description="Which specialized agent handled the query")
    session_id: str = Field(..., description="Session ID for this conversation")
    timestamp: datetime = Field(default_factory=datetime.now)


class StreamChunk(BaseModel):
    """Model for streaming response chunks."""
    content: str
    is_final: bool = False
    agent_used: Optional[str] = None
