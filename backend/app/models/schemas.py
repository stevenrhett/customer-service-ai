"""Pydantic models for API requests and responses."""
from pydantic import BaseModel
from typing import List, Optional


class ChatMessage(BaseModel):
    """Chat message model."""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    conversation_id: str
    agent_used: str


class DocumentUploadResponse(BaseModel):
    """Document upload response model."""
    success: bool
    message: str
    document_id: Optional[str] = None


class DocumentInfo(BaseModel):
    """Document information model."""
    id: str
    filename: str
    chunks: int
