"""Tests for chat API endpoints."""
from unittest.mock import AsyncMock

import pytest
from app.api.v1.chat import set_orchestrator
from app.main import app
from httpx import AsyncClient


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
    mock_orchestrator = AsyncMock()
    mock_orchestrator.process_query = AsyncMock(
        return_value={
            "response": "Test response",
            "agent_used": "billing",
            "session_id": "test-session-123",
        }
    )
    set_orchestrator(mock_orchestrator)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "What are your pricing plans?",
                "session_id": "test-session-123",
            },
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
    mock_orchestrator = AsyncMock()
    mock_orchestrator.process_query = AsyncMock(
        return_value={
            "response": "Follow-up response",
            "agent_used": "billing",
            "session_id": "test-session-123",
        }
    )
    set_orchestrator(mock_orchestrator)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "Tell me more",
                "session_id": "test-session-123",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi!"},
                ],
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data


@pytest.mark.asyncio
async def test_chat_endpoint_validation(mock_env_vars):
    """Test chat endpoint input validation."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Empty message
        response = await client.post("/api/v1/chat", json={"message": ""})
        assert response.status_code == 422

        # Missing message
        response = await client.post("/api/v1/chat", json={})
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_stream_endpoint(mock_env_vars):
    """Test streaming chat endpoint."""
    mock_orchestrator = AsyncMock()

    async def mock_stream(query, session_id, history):
        yield {"agent_used": "billing", "content": "Streaming ", "is_final": False}
        yield {"agent_used": "billing", "content": "response.", "is_final": False}
        yield {"agent_used": "billing", "content": "", "is_final": True}

    mock_orchestrator.stream_query = mock_stream
    set_orchestrator(mock_orchestrator)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat?stream=true",
            json={
                "message": "What are your pricing plans?",
                "session_id": "test-session-123",
            },
        )

    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
