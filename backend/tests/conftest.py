"""
Pytest configuration and fixtures for testing.
"""
import os
import pytest

# Set test environment variables BEFORE any imports that use settings
# This must happen before importing modules that call get_settings()
os.environ.setdefault("OPENAI_API_KEY", "sk-test123456789012345678901234567890")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "AKIATEST123456789012345")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "test_secret_key_123456789012345678901234567890")
os.environ.setdefault("AWS_REGION", "us-west-2")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("LOG_LEVEL", "DEBUG")

from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.documents import Document
from app.services.session_manager import SessionManager
from app.services.vector_store import VectorStoreService


@pytest.fixture
def mock_llm_response():
    """Mock LLM response."""
    return AIMessage(content="This is a test response from the LLM.")


@pytest.fixture
def mock_streaming_chunks():
    """Mock streaming chunks from LLM."""
    chunks = [
        AIMessage(content="This "),
        AIMessage(content="is "),
        AIMessage(content="a "),
        AIMessage(content="test "),
        AIMessage(content="response."),
    ]
    return chunks


@pytest.fixture
def mock_documents():
    """Mock documents for vector store retrieval."""
    return [
        Document(
            page_content="Test document content about billing and pricing.",
            metadata={"source": "test_billing.txt", "type": "billing"}
        ),
        Document(
            page_content="More information about pricing plans.",
            metadata={"source": "test_billing.txt", "type": "billing"}
        ),
    ]


@pytest.fixture
def mock_vector_store():
    """Mock vector store."""
    mock_store = MagicMock()
    mock_retriever = MagicMock()
    mock_store.as_retriever.return_value = mock_retriever
    return mock_store


@pytest.fixture
def sample_messages():
    """Sample conversation messages."""
    return [
        HumanMessage(content="Hello"),
        AIMessage(content="Hi! How can I help you?"),
        HumanMessage(content="What are your pricing plans?"),
    ]


@pytest.fixture
def mock_openai_chat():
    """Mock OpenAI ChatOpenAI instance."""
    with patch('langchain_openai.ChatOpenAI') as mock_chat:
        mock_instance = MagicMock()
        mock_chat.return_value = mock_instance
        
        # Mock invoke
        mock_instance.invoke = AsyncMock(return_value=AIMessage(content="Mock response"))
        
        # Mock astream
        async def mock_astream(messages):
            chunks = [
                AIMessage(content="Mock "),
                AIMessage(content="streaming "),
                AIMessage(content="response."),
            ]
            for chunk in chunks:
                yield chunk
        
        mock_instance.astream = mock_astream
        
        # Mock ainvoke (async invoke)
        async def mock_ainvoke(messages):
            return AIMessage(content="Mock async response")
        
        mock_instance.ainvoke = mock_ainvoke
        
        mock_chat.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_bedrock_chat():
    """Mock AWS Bedrock ChatBedrock instance."""
    with patch('langchain_aws.ChatBedrock') as mock_bedrock:
        mock_instance = MagicMock()
        mock_bedrock.return_value = mock_instance
        
        # Mock invoke
        mock_instance.invoke = AsyncMock(return_value=AIMessage(content="billing"))
        mock_instance.ainvoke = AsyncMock(return_value=AIMessage(content="billing"))
        
        mock_bedrock.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def session_manager():
    """Create a fresh session manager for testing."""
    return SessionManager()


@pytest.fixture
def test_session_id():
    """Generate a test session ID."""
    return "test-session-123"


@pytest.fixture(autouse=True)
def reset_vector_store():
    """Reset vector store service before each test."""
    VectorStoreService().reset()
    yield
    VectorStoreService().reset()


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables for testing."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test1234567890")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "AKIATEST1234567890")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret_key_1234567890")
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

