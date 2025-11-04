"""
Pydantic models for API request/response validation.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class Message(BaseModel):
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    """Request model for the chat endpoint."""
    message: str = Field(..., min_length=1, description="User's message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation continuity")
    conversation_history: Optional[List[Message]] = Field(default_factory=list, description="Previous messages in the conversation")


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
