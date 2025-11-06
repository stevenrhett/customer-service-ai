"""
Chat API endpoints for handling user messages and streaming responses.
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest, ChatResponse
from app.agents.orchestrator import OrchestratorAgent
from app.services.session_manager import session_manager
from app.utils.exceptions import CustomerServiceException, AgentError, SessionError
from app.middleware.rate_limiter import limiter
from langchain_core.messages import HumanMessage, AIMessage
from typing import AsyncGenerator
import json
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize orchestrator (singleton pattern)
_orchestrator = None

def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
async def chat(request: Request, chat_request: ChatRequest):
    """
    Handle incoming chat messages and route them through the agent system.
    
    This endpoint will:
    1. Receive the user's message
    2. Pass it to the orchestrator agent
    3. Route to the appropriate specialized agent
    4. Return the agent's response
    """
    try:
        # Get or create session
        session_id = session_manager.get_or_create_session(chat_request.session_id)
        
        # Get conversation history from session
        history = session_manager.get_session_history(session_id)
        
        # If request has conversation history, use it (for frontend compatibility)
        # Otherwise use session history
        if chat_request.conversation_history:
            # Convert request messages to LangChain messages
            history = []
            for msg in chat_request.conversation_history:
                if msg.role == "user":
                    history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    history.append(AIMessage(content=msg.content))
        
        # Get orchestrator and process query
        orchestrator = get_orchestrator()
        result = await orchestrator.process_query(
            chat_request.message,
            session_id,
            history
        )
        
        # Extract response
        response_content = result.get("response", "")
        agent_used = result.get("agent_used", "unknown")
        
        # Save messages to session
        session_manager.add_message(session_id, "user", chat_request.message)
        session_manager.add_message(session_id, "assistant", response_content)
        
        # Create response
        response = ChatResponse(
            response=response_content,
            agent_used=agent_used,
            session_id=session_id,
            timestamp=datetime.now()
        )
        
        return response
        
    except CustomerServiceException as e:
        logger.error(f"Customer service error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


@router.post("/chat/stream")
@limiter.limit("60/minute")
async def chat_stream(request: Request, chat_request: ChatRequest):
    """
    Handle incoming chat messages with streaming responses.
    
    This endpoint streams the AI response token by token for a better UX.
    """
    
    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate streaming response."""
        try:
            # Get or create session
            session_id = session_manager.get_or_create_session(chat_request.session_id)
            
            # Get conversation history
            history = session_manager.get_session_history(session_id)
            if chat_request.conversation_history:
                history = []
                for msg in chat_request.conversation_history:
                    if msg.role == "user":
                        history.append(HumanMessage(content=msg.content))
                    elif msg.role == "assistant":
                        history.append(AIMessage(content=msg.content))
            
            # Get orchestrator
            orchestrator = get_orchestrator()
            
            # Save user message
            session_manager.add_message(session_id, "user", chat_request.message)
            
            # Stream response token-by-token from agents
            full_response = ""
            agent_used = "unknown"
            
            async for chunk_data in orchestrator.stream_query(
                chat_request.message,
                session_id,
                history
            ):
                agent_used = chunk_data.get("agent_used", agent_used)
                content = chunk_data.get("content", "")
                is_final = chunk_data.get("is_final", False)
                
                if content:
                    full_response += content
                
                # Stream each chunk
                data = {
                    "content": content,
                    "is_final": is_final,
                    "agent_used": agent_used
                }
                yield f"data: {json.dumps(data)}\n\n"
            
            # Save assistant message after streaming completes
            if full_response:
                session_manager.add_message(session_id, "assistant", full_response)
            
            # Send final chunk with session_id
            final_data = {
                "content": "",
                "is_final": True,
                "agent_used": agent_used,
                "session_id": session_id
            }
            yield f"data: {json.dumps(final_data)}\n\n"
            
        except CustomerServiceException as e:
            logger.error(f"Customer service error: {e.message}", exc_info=True)
            error_data = {"error": e.message, "status_code": e.status_code}
            yield f"data: {json.dumps(error_data)}\n\n"
        except Exception as e:
            logger.error(f"Error in streaming: {str(e)}", exc_info=True)
            error_data = {"error": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
