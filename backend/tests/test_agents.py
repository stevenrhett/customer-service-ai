"""
Integration tests for specialized agents.
"""
from unittest.mock import MagicMock, patch

import pytest
from app.agents.billing_agent import BillingAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.technical_agent import TechnicalAgent


@pytest.mark.asyncio
async def test_billing_agent_with_retriever(mock_openai_chat, mock_documents):
    """Test billing agent with vector store retriever."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = mock_documents
    mock_vector_store.as_retriever.return_value = mock_retriever

    with patch("app.agents.billing_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = BillingAgent(vector_store=mock_vector_store)

        response = await agent.process_query(
            "What are your pricing plans?", "test-session", []
        )

        assert "Mock" in response or "Billing" in response
        mock_retriever.get_relevant_documents.assert_called_once()


@pytest.mark.asyncio
async def test_billing_agent_streaming(mock_openai_chat, mock_documents):
    """Test billing agent streaming."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = mock_documents
    mock_vector_store.as_retriever.return_value = mock_retriever

    with patch("app.agents.billing_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = BillingAgent(vector_store=mock_vector_store)

        streamed_chunks = []
        async for chunk in agent.stream_query(
            "What are your pricing plans?", "test-session", []
        ):
            streamed_chunks.append(chunk)

        assert len(streamed_chunks) > 0


@pytest.mark.asyncio
async def test_technical_agent_retrieval(mock_openai_chat, mock_documents):
    """Test technical agent document retrieval."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = mock_documents
    mock_vector_store.as_retriever.return_value = mock_retriever

    with patch("app.agents.technical_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = TechnicalAgent(vector_store=mock_vector_store)

        response = await agent.process_query(
            "How do I fix this bug?", "test-session", []
        )

        assert "Mock" in response or "Technical" in response
        mock_retriever.get_relevant_documents.assert_called_once()


@pytest.mark.asyncio
async def test_technical_agent_without_vector_store(mock_openai_chat):
    """Test technical agent without vector store."""
    with patch("app.agents.technical_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = TechnicalAgent(vector_store=None)

        response = await agent.process_query("How do I fix this?", "test-session", [])

        assert "not yet indexed" in response.lower() or "Mock" in response


@pytest.mark.asyncio
async def test_policy_agent_process_query(mock_openai_chat):
    """Test policy agent processing."""
    with patch("app.agents.policy_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = PolicyAgent()

        response = await agent.process_query(
            "What is your privacy policy?", "test-session", []
        )

        assert "Mock" in response or "Policy" in response


@pytest.mark.asyncio
async def test_policy_agent_streaming(mock_openai_chat):
    """Test policy agent streaming."""
    with patch("app.agents.policy_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = PolicyAgent()

        streamed_chunks = []
        async for chunk in agent.stream_query(
            "What is your privacy policy?", "test-session", []
        ):
            streamed_chunks.append(chunk)

        assert len(streamed_chunks) > 0


@pytest.mark.asyncio
async def test_agents_with_history(mock_openai_chat, sample_messages):
    """Test agents use conversation history."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = []
    mock_vector_store.as_retriever.return_value = mock_retriever

    with patch("app.agents.billing_agent.ChatOpenAI", return_value=mock_openai_chat):
        agent = BillingAgent(vector_store=mock_vector_store)

        await agent.process_query("Follow-up question", "test-session", sample_messages)

        # Verify history was included in LLM call
        assert mock_openai_chat.ainvoke.called
        call_args = mock_openai_chat.ainvoke.call_args
        if call_args:
            messages = call_args[0][0]
            assert len(messages) > 2  # System message + history + query
