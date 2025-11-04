"""
Chat API endpoints for handling user messages and streaming responses.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from typing import AsyncGenerator
import json
import uuid
from datetime import datetime

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle incoming chat messages and route them through the agent system.
    
    This endpoint will:
    1. Receive the user's message
    2. Pass it to the orchestrator agent
    3. Route to the appropriate specialized agent
    4. Return the agent's response
    """
    try:
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # TODO: Integrate with LangGraph orchestrator
        # For now, return a placeholder response
        
        response = ChatResponse(
            response=f"Received your message: {request.message}. Agent system integration pending.",
            agent_used="orchestrator",
            session_id=session_id,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Handle incoming chat messages with streaming responses.
    
    This endpoint streams the AI response token by token for a better UX.
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        try:
            # Generate or use existing session ID
            session_id = request.session_id or str(uuid.uuid4())
            
            # TODO: Integrate with LangGraph orchestrator for streaming
            # For now, send a placeholder streaming response
            
            chunks = [
                "This ", "is ", "a ", "placeholder ", "streaming ", 
                "response. ", "Agent ", "integration ", "pending."
            ]
            
            for chunk in chunks:
                data = {
                    "content": chunk,
                    "is_final": False,
                    "agent_used": "orchestrator"
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Send final chunk
            final_data = {
                "content": "",
                "is_final": True,
                "agent_used": "orchestrator",
                "session_id": session_id
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except Exception as e:
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
