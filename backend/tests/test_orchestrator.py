"""
Integration tests for the orchestrator agent.
"""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.orchestrator import OrchestratorAgent


@pytest.mark.asyncio
async def test_orchestrator_routes_to_billing_agent(mock_openai_chat, mock_bedrock_chat, mock_vector_store):
    """Test that orchestrator routes billing queries correctly."""
    with patch('app.services.vector_store.vector_store_service') as mock_service:
        mock_service.get_billing_store.return_value = mock_vector_store
        mock_service.get_technical_store.return_value = mock_vector_store
        
        # Mock routing LLM to return "billing"
        with patch('app.agents.orchestrator.ChatBedrock') as mock_bedrock:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=AIMessage(content="billing"))
            mock_bedrock.return_value = mock_instance
            
            orchestrator = OrchestratorAgent()
            
            # Mock billing agent
            orchestrator.billing_agent.process_query = AsyncMock(return_value="Billing response")
            
            result = await orchestrator.process_query(
                "What are your pricing plans?",
                "test-session",
                []
            )
            
            assert result["agent_used"] == "billing"
            assert "response" in result


@pytest.mark.asyncio
async def test_orchestrator_routes_to_technical_agent(mock_openai_chat, mock_bedrock_chat, mock_vector_store):
    """Test that orchestrator routes technical queries correctly."""
    with patch('app.services.vector_store.vector_store_service') as mock_service:
        mock_service.get_billing_store.return_value = mock_vector_store
        mock_service.get_technical_store.return_value = mock_vector_store
        
        # Mock routing LLM to return "technical"
        with patch('app.agents.orchestrator.ChatBedrock') as mock_bedrock:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=AIMessage(content="technical"))
            mock_bedrock.return_value = mock_instance
            
            orchestrator = OrchestratorAgent()
            
            # Mock technical agent
            orchestrator.technical_agent.process_query = AsyncMock(return_value="Technical response")
            
            result = await orchestrator.process_query(
                "How do I fix a bug?",
                "test-session",
                []
            )
            
            assert result["agent_used"] == "technical"
            assert "response" in result


@pytest.mark.asyncio
async def test_orchestrator_routes_to_policy_agent(mock_openai_chat, mock_bedrock_chat, mock_vector_store):
    """Test that orchestrator routes policy queries correctly."""
    with patch('app.services.vector_store.vector_store_service') as mock_service:
        mock_service.get_billing_store.return_value = mock_vector_store
        mock_service.get_technical_store.return_value = mock_vector_store
        
        # Mock routing LLM to return "policy"
        with patch('app.agents.orchestrator.ChatBedrock') as mock_bedrock:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=AIMessage(content="policy"))
            mock_bedrock.return_value = mock_instance
            
            orchestrator = OrchestratorAgent()
            
            # Mock policy agent
            orchestrator.policy_agent.process_query = AsyncMock(return_value="Policy response")
            
            result = await orchestrator.process_query(
                "What is your privacy policy?",
                "test-session",
                []
            )
            
            assert result["agent_used"] == "policy"
            assert "response" in result


@pytest.mark.asyncio
async def test_orchestrator_streaming(mock_openai_chat, mock_bedrock_chat, mock_vector_store):
    """Test orchestrator streaming functionality."""
    with patch('app.services.vector_store.vector_store_service') as mock_service:
        mock_service.get_billing_store.return_value = mock_vector_store
        mock_service.get_technical_store.return_value = mock_vector_store
        
        # Mock routing LLM to return "billing"
        with patch('app.agents.orchestrator.ChatBedrock') as mock_bedrock:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=AIMessage(content="billing"))
            mock_bedrock.return_value = mock_instance
            
            orchestrator = OrchestratorAgent()
            
            # Mock streaming from billing agent
            async def mock_stream(query, session_id, history):
                chunks = ["Billing ", "response ", "content."]
                for chunk in chunks:
                    yield chunk
            
            orchestrator.billing_agent.stream_query = mock_stream
            
            chunks = []
            async for chunk_data in orchestrator.stream_query(
                "What are your pricing plans?",
                "test-session",
                []
            ):
                chunks.append(chunk_data)
            
            assert len(chunks) > 0
            assert chunks[0]["agent_used"] == "billing"
            assert chunks[-1]["is_final"] == True


@pytest.mark.asyncio
async def test_orchestrator_with_history(mock_openai_chat, mock_bedrock_chat, mock_vector_store, sample_messages):
    """Test orchestrator with conversation history."""
    with patch('app.services.vector_store.vector_store_service') as mock_service:
        mock_service.get_billing_store.return_value = mock_vector_store
        mock_service.get_technical_store.return_value = mock_vector_store
        
        with patch('app.agents.orchestrator.ChatBedrock') as mock_bedrock:
            mock_instance = MagicMock()
            mock_instance.ainvoke = AsyncMock(return_value=AIMessage(content="billing"))
            mock_bedrock.return_value = mock_instance
            
            orchestrator = OrchestratorAgent()
            orchestrator.billing_agent.process_query = AsyncMock(return_value="Response with history")
            
            result = await orchestrator.process_query(
                "Tell me more",
                "test-session",
                sample_messages
            )
            
            # Verify history was passed to agent
            call_args = orchestrator.billing_agent.process_query.call_args
            history_passed = call_args[0][2]  # history parameter
            
            # Compare content, not object identity (orchestrator creates a slice)
            assert len(history_passed) == len(sample_messages)
            for passed_msg, expected_msg in zip(history_passed, sample_messages):
                assert passed_msg.content == expected_msg.content
                assert type(passed_msg) == type(expected_msg)

