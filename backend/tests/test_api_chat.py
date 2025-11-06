"""Tests for chat API endpoints."""
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.services.session_manager import session_manager


@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data


@pytest.mark.asyncio
async def test_root_endpoint():
    """Test the root endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "version" in data


@pytest.mark.asyncio
async def test_chat_endpoint_basic(mock_env_vars):
    """Test the chat endpoint with a simple message."""
    with patch('app.api.chat.get_orchestrator') as mock_get_orch:
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value={
            "response": "Test response",
            "agent_used": "billing",
            "session_id": "test-session-123"
        })
        mock_get_orch.return_value = mock_orchestrator
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/chat",
                json={
                    "message": "What are your pricing plans?",
                    "session_id": "test-session-123"
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "agent_used" in data
        assert "session_id" in data
        assert data["session_id"] == "test-session-123"


@pytest.mark.asyncio
async def test_chat_endpoint_with_history(mock_env_vars):
    """Test chat endpoint with conversation history."""
    with patch('app.api.chat.get_orchestrator') as mock_get_orch:
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value={
            "response": "Follow-up response",
            "agent_used": "billing",
            "session_id": "test-session-123"
        })
        mock_get_orch.return_value = mock_orchestrator
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/chat",
                json={
                    "message": "Tell me more",
                    "session_id": "test-session-123",
                    "conversation_history": [
                        {"role": "user", "content": "Hello"},
                        {"role": "assistant", "content": "Hi!"}
                    ]
                }
            )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data


@pytest.mark.asyncio
async def test_chat_endpoint_validation(mock_env_vars):
    """Test chat endpoint input validation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Empty message
        response = await client.post(
            "/api/chat",
            json={"message": ""}
        )
        assert response.status_code == 422
        
        # Missing message
        response = await client.post(
            "/api/chat",
            json={}
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_stream_endpoint(mock_env_vars):
    """Test streaming chat endpoint."""
    with patch('app.api.chat.get_orchestrator') as mock_get_orch:
        mock_orchestrator = AsyncMock()
        
        async def mock_stream(query, session_id, history):
            yield {"agent_used": "billing", "content": "Streaming ", "is_final": False}
            yield {"agent_used": "billing", "content": "response.", "is_final": False}
            yield {"agent_used": "billing", "content": "", "is_final": True}
        
        mock_orchestrator.stream_query = mock_stream
        mock_get_orch.return_value = mock_orchestrator
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/chat/stream",
                json={
                    "message": "What are your pricing plans?",
                    "session_id": "test-session-123"
                }
            )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"


@pytest.mark.asyncio
async def test_session_persistence(mock_env_vars):
    """Test that sessions persist across requests."""
    with patch('app.api.chat.get_orchestrator') as mock_get_orch:
        mock_orchestrator = AsyncMock()
        mock_orchestrator.process_query = AsyncMock(return_value={
            "response": "Response",
            "agent_used": "billing",
            "session_id": "test-session-456"
        })
        mock_get_orch.return_value = mock_orchestrator
        
        session_id = "test-session-456"
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # First request
            response1 = await client.post(
                "/api/chat",
                json={"message": "Hello", "session_id": session_id}
            )
            
            # Second request with same session
            response2 = await client.post(
                "/api/chat",
                json={"message": "Follow-up", "session_id": session_id}
            )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json()["session_id"] == session_id
        assert response2.json()["session_id"] == session_id
