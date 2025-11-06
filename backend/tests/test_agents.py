"""
Integration tests for specialized agents.
"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage
from app.agents.billing_agent import BillingAgent
from app.agents.technical_agent import TechnicalAgent
from app.agents.policy_agent import PolicyAgent


@pytest.mark.asyncio
async def test_billing_agent_with_retriever(mock_openai_chat, mock_documents):
    """Test billing agent with vector store retriever."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = mock_documents
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    agent = BillingAgent(vector_store=mock_vector_store)
    
    # Mock LLM response
    agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="Billing answer"))
    
    response = await agent.process_query(
        "What are your pricing plans?",
        "test-session",
        []
    )
    
    assert response == "Billing answer"
    mock_retriever.get_relevant_documents.assert_called_once()


@pytest.mark.asyncio
async def test_billing_agent_streaming(mock_openai_chat, mock_documents):
    """Test billing agent streaming."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = mock_documents
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    agent = BillingAgent(vector_store=mock_vector_store)
    
    # Mock streaming
    chunks = [AIMessage(content="Billing "), AIMessage(content="response.")]
    agent.llm.astream = AsyncMock(return_value=iter(chunks))
    
    async def mock_astream(messages):
        for chunk in chunks:
            yield chunk
    
    agent.llm.astream = mock_astream
    
    streamed_chunks = []
    async for chunk in agent.stream_query("What are your pricing plans?", "test-session", []):
        streamed_chunks.append(chunk)
    
    assert len(streamed_chunks) > 0


@pytest.mark.asyncio
async def test_technical_agent_retrieval(mock_openai_chat, mock_documents):
    """Test technical agent document retrieval."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = mock_documents
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    agent = TechnicalAgent(vector_store=mock_vector_store)
    agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="Technical answer"))
    
    response = await agent.process_query(
        "How do I fix this bug?",
        "test-session",
        []
    )
    
    assert response == "Technical answer"
    mock_retriever.get_relevant_documents.assert_called_once()


@pytest.mark.asyncio
async def test_technical_agent_without_vector_store(mock_openai_chat):
    """Test technical agent without vector store."""
    agent = TechnicalAgent(vector_store=None)
    agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="No docs available"))
    
    response = await agent.process_query(
        "How do I fix this?",
        "test-session",
        []
    )
    
    assert "not yet indexed" in response.lower() or "No docs available" in response


@pytest.mark.asyncio
async def test_policy_agent_process_query(mock_openai_chat):
    """Test policy agent processing."""
    agent = PolicyAgent()
    agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="Policy answer"))
    
    response = await agent.process_query(
        "What is your privacy policy?",
        "test-session",
        []
    )
    
    assert response == "Policy answer"


@pytest.mark.asyncio
async def test_policy_agent_streaming(mock_openai_chat):
    """Test policy agent streaming."""
    agent = PolicyAgent()
    
    chunks = [AIMessage(content="Policy "), AIMessage(content="response.")]
    async def mock_astream(messages):
        for chunk in chunks:
            yield chunk
    
    agent.llm.astream = mock_astream
    
    streamed_chunks = []
    async for chunk in agent.stream_query("What is your privacy policy?", "test-session", []):
        streamed_chunks.append(chunk)
    
    assert len(streamed_chunks) > 0


@pytest.mark.asyncio
async def test_agents_with_history(mock_openai_chat, sample_messages):
    """Test agents use conversation history."""
    mock_vector_store = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.get_relevant_documents.return_value = []
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    agent = BillingAgent(vector_store=mock_vector_store)
    agent.llm.ainvoke = AsyncMock(return_value=AIMessage(content="Response"))
    
    await agent.process_query("Follow-up question", "test-session", sample_messages)
    
    # Verify history was included in LLM call
    call_args = agent.llm.ainvoke.call_args
    messages = call_args[0][0]
    assert len(messages) > 2  # System message + history + query

