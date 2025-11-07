"""
Integration tests for the orchestrator chain.
"""
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.chains.orchestrator import OrchestratorChain
from app.services.billing_service import BillingService
from app.services.policy_service import PolicyService
from app.services.router_service import RouterService
from app.services.technical_service import TechnicalService


@pytest.mark.asyncio
async def test_orchestrator_routes_to_billing_service(
    mock_openai_chat, mock_bedrock_chat, mock_vector_store
):
    """Test that orchestrator routes billing queries correctly."""
    # Mock router service
    mock_router = MagicMock(spec=RouterService)
    mock_router.classify_intent = AsyncMock(return_value="billing")

    # Mock billing service
    mock_billing = MagicMock(spec=BillingService)
    mock_billing.process_query = AsyncMock(return_value="Billing response")

    # Mock other services
    mock_technical = MagicMock(spec=TechnicalService)
    mock_policy = MagicMock(spec=PolicyService)

    orchestrator = OrchestratorChain(
        router_service=mock_router,
        billing_service=mock_billing,
        technical_service=mock_technical,
        policy_service=mock_policy,
    )

    result = await orchestrator.process_query(
        "What are your pricing plans?", "test-session", []
    )

    assert result["agent_used"] == "billing"
    assert "response" in result
    assert result["response"] == "Billing response"
    mock_router.classify_intent.assert_called_once()
    mock_billing.process_query.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_routes_to_technical_service(
    mock_openai_chat, mock_bedrock_chat, mock_vector_store
):
    """Test that orchestrator routes technical queries correctly."""
    # Mock router service
    mock_router = MagicMock(spec=RouterService)
    mock_router.classify_intent = AsyncMock(return_value="technical")

    # Mock technical service
    mock_technical = MagicMock(spec=TechnicalService)
    mock_technical.process_query = AsyncMock(return_value="Technical response")

    # Mock other services
    mock_billing = MagicMock(spec=BillingService)
    mock_policy = MagicMock(spec=PolicyService)

    orchestrator = OrchestratorChain(
        router_service=mock_router,
        billing_service=mock_billing,
        technical_service=mock_technical,
        policy_service=mock_policy,
    )

    result = await orchestrator.process_query("How do I fix a bug?", "test-session", [])

    assert result["agent_used"] == "technical"
    assert "response" in result
    assert result["response"] == "Technical response"
    mock_router.classify_intent.assert_called_once()
    mock_technical.process_query.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_routes_to_policy_service(
    mock_openai_chat, mock_bedrock_chat, mock_vector_store
):
    """Test that orchestrator routes policy queries correctly."""
    # Mock router service
    mock_router = MagicMock(spec=RouterService)
    mock_router.classify_intent = AsyncMock(return_value="policy")

    # Mock policy service
    mock_policy = MagicMock(spec=PolicyService)
    mock_policy.process_query = AsyncMock(return_value="Policy response")

    # Mock other services
    mock_billing = MagicMock(spec=BillingService)
    mock_technical = MagicMock(spec=TechnicalService)

    orchestrator = OrchestratorChain(
        router_service=mock_router,
        billing_service=mock_billing,
        technical_service=mock_technical,
        policy_service=mock_policy,
    )

    result = await orchestrator.process_query(
        "What is your privacy policy?", "test-session", []
    )

    assert result["agent_used"] == "policy"
    assert "response" in result
    assert result["response"] == "Policy response"
    mock_router.classify_intent.assert_called_once()
    mock_policy.process_query.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_streaming(
    mock_openai_chat, mock_bedrock_chat, mock_vector_store
):
    """Test orchestrator streaming functionality."""
    # Mock router service
    mock_router = MagicMock(spec=RouterService)
    mock_router.classify_intent = AsyncMock(return_value="billing")

    # Mock billing service streaming
    async def mock_stream(query, session_id, history):
        chunks = ["Billing ", "response ", "content."]
        for chunk in chunks:
            yield chunk

    mock_billing = MagicMock(spec=BillingService)
    mock_billing.stream_query = mock_stream

    # Mock other services
    mock_technical = MagicMock(spec=TechnicalService)
    mock_policy = MagicMock(spec=PolicyService)

    orchestrator = OrchestratorChain(
        router_service=mock_router,
        billing_service=mock_billing,
        technical_service=mock_technical,
        policy_service=mock_policy,
    )

    chunks = []
    async for chunk_data in orchestrator.stream_query(
        "What are your pricing plans?", "test-session", []
    ):
        chunks.append(chunk_data)

    assert len(chunks) > 0
    assert chunks[0]["agent_used"] == "billing"
    assert chunks[-1]["is_final"]
    mock_router.classify_intent.assert_called_once()


@pytest.mark.asyncio
async def test_orchestrator_with_history(
    mock_openai_chat, mock_bedrock_chat, mock_vector_store, sample_messages
):
    """Test orchestrator with conversation history."""
    # Mock router service
    mock_router = MagicMock(spec=RouterService)
    mock_router.classify_intent = AsyncMock(return_value="billing")

    # Mock billing service
    mock_billing = MagicMock(spec=BillingService)
    mock_billing.process_query = AsyncMock(return_value="Response with history")

    # Mock other services
    mock_technical = MagicMock(spec=TechnicalService)
    mock_policy = MagicMock(spec=PolicyService)

    orchestrator = OrchestratorChain(
        router_service=mock_router,
        billing_service=mock_billing,
        technical_service=mock_technical,
        policy_service=mock_policy,
    )

    await orchestrator.process_query("Tell me more", "test-session", sample_messages)

    # Verify history was passed to service
    call_args = mock_billing.process_query.call_args
    history_passed = call_args[0][2]  # history parameter

    # Compare content, not object identity (orchestrator creates a slice)
    assert len(history_passed) == len(sample_messages)
    for passed_msg, expected_msg in zip(history_passed, sample_messages):
        assert passed_msg.content == expected_msg.content
        assert isinstance(passed_msg, type(expected_msg))
