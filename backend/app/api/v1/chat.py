"""
Chat API endpoints for handling user messages and streaming responses.
"""
import json
from datetime import datetime
from typing import AsyncGenerator

from app.chains.orchestrator import OrchestratorChain
from app.middleware.rate_limiter import limiter
from app.models.chat import ChatRequest, ChatResponse
from app.services.session_manager import session_manager
from app.utils.exceptions import CustomerServiceException
from app.utils.logging import get_logger
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage

logger = get_logger(__name__)

router = APIRouter()

# Orchestrator instance (will be injected via dependency)
_orchestrator: OrchestratorChain | None = None


def get_orchestrator() -> OrchestratorChain:
    """
    Get orchestrator instance.
    This should be set via dependency injection in main.py.
    """
    global _orchestrator
    if _orchestrator is None:
        raise RuntimeError(
            "Orchestrator not initialized. Call set_orchestrator() first."
        )
    return _orchestrator


def set_orchestrator(orchestrator: OrchestratorChain) -> None:
    """Set orchestrator instance for dependency injection."""
    global _orchestrator
    _orchestrator = orchestrator


@router.post("/chat", response_model=ChatResponse)
@limiter.limit("60/minute")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    stream: bool = Query(default=False, description="Enable streaming response"),
):
    """
    Handle incoming chat messages and route them through the agent system.

    Supports both streaming and non-streaming modes:
    - stream=false (default): Returns JSON response
    - stream=true: Returns text/event-stream

    Args:
        request: FastAPI request object
        chat_request: Chat request with message and optional history
        stream: Whether to stream the response

    Returns:
        ChatResponse (JSON) or StreamingResponse (text/event-stream)
    """
    try:
        # Get or create session
        session_id = session_manager.get_or_create_session(chat_request.session_id)

        # Get conversation history from session
        history = session_manager.get_session_history(session_id)

        # If request has conversation history, use it (for frontend compatibility)
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

        # Handle streaming vs non-streaming
        if stream:
            return StreamingResponse(
                _generate_stream(
                    orchestrator, chat_request.message, session_id, history
                ),
                media_type="text/event-stream",
            )
        else:
            # Non-streaming: process query
            result = await orchestrator.process_query(
                chat_request.message, session_id, history
            )

            # Extract response
            response_content = result.get("response", "")
            agent_used = result.get("agent_used", "unknown")

            # Save assistant message
            session_manager.add_message(session_id, "assistant", response_content)

            # Create response
            response = ChatResponse(
                response=response_content,
                agent_used=agent_used,
                session_id=session_id,
                timestamp=datetime.now(),
            )

            return response

    except CustomerServiceException as e:
        logger.error(f"Customer service error: {e.message}", exc_info=True)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


async def _generate_stream(
    orchestrator: OrchestratorChain, message: str, session_id: str, history: list
) -> AsyncGenerator[str, None]:
    """Generate streaming response."""
    try:
        full_response = ""
        agent_used = "unknown"

        async for chunk_data in orchestrator.stream_query(message, session_id, history):
            agent_used = chunk_data.get("agent_used", agent_used)
            content = chunk_data.get("content", "")
            is_final = chunk_data.get("is_final", False)

            if content:
                full_response += content

            # Stream each chunk
            data = {"content": content, "is_final": is_final, "agent_used": agent_used}
            yield f"data: {json.dumps(data)}\n\n"

        # Save assistant message after streaming completes
        if full_response:
            session_manager.add_message(session_id, "assistant", full_response)

        # Send final chunk with session_id
        final_data = {
            "content": "",
            "is_final": True,
            "agent_used": agent_used,
            "session_id": session_id,
        }
        yield f"data: {json.dumps(final_data)}\n\n"

    except CustomerServiceException as e:
        logger.error(f"Customer service error in stream: {e.message}", exc_info=True)
        error_data = {"error": e.message, "status_code": e.status_code}
        yield f"data: {json.dumps(error_data)}\n\n"
    except Exception as e:
        logger.error(f"Error in streaming: {str(e)}", exc_info=True)
        error_data = {"error": "An internal error occurred."}
        yield f"data: {json.dumps(error_data)}\n\n"
