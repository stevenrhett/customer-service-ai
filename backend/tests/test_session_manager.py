"""
Integration tests for session management.
"""
import pytest
from app.services.session_manager import session_manager


@pytest.mark.asyncio
async def test_create_session():
    """Test creating a new session."""
    session_id = session_manager.get_or_create_session(None)
    assert session_id is not None
    assert isinstance(session_id, str)
    assert len(session_id) > 0


@pytest.mark.asyncio
async def test_get_existing_session():
    """Test retrieving an existing session."""
    session_id = session_manager.get_or_create_session(None)
    retrieved_id = session_manager.get_or_create_session(session_id)
    assert retrieved_id == session_id


@pytest.mark.asyncio
async def test_add_message_to_session():
    """Test adding messages to a session."""
    session_id = session_manager.get_or_create_session(None)

    session_manager.add_message(session_id, "user", "Hello")
    session_manager.add_message(session_id, "assistant", "Hi there!")

    history = session_manager.get_session_history(session_id)
    assert len(history) == 2
    assert history[0].content == "Hello"
    assert history[1].content == "Hi there!"


@pytest.mark.asyncio
async def test_get_session_history():
    """Test retrieving session history."""
    session_id = session_manager.get_or_create_session(None)

    session_manager.add_message(session_id, "user", "Question 1")
    session_manager.add_message(session_id, "assistant", "Answer 1")
    session_manager.add_message(session_id, "user", "Question 2")

    history = session_manager.get_session_history(session_id)
    assert len(history) == 3
    assert history[0].content == "Question 1"
    assert history[1].content == "Answer 1"
    assert history[2].content == "Question 2"


@pytest.mark.asyncio
async def test_session_persistence():
    """Test that sessions persist across multiple operations."""
    session_id = session_manager.get_or_create_session(None)

    # Add messages
    session_manager.add_message(session_id, "user", "First message")

    # Retrieve session
    retrieved_id = session_manager.get_or_create_session(session_id)
    assert retrieved_id == session_id

    # Verify history persists
    history = session_manager.get_session_history(session_id)
    assert len(history) == 1
    assert history[0].content == "First message"


@pytest.mark.asyncio
async def test_multiple_sessions():
    """Test managing multiple sessions simultaneously."""
    session1 = session_manager.get_or_create_session(None)
    session2 = session_manager.get_or_create_session(None)

    assert session1 != session2

    session_manager.add_message(session1, "user", "Session 1 message")
    session_manager.add_message(session2, "user", "Session 2 message")

    history1 = session_manager.get_session_history(session1)
    history2 = session_manager.get_session_history(session2)

    assert len(history1) == 1
    assert len(history2) == 1
    assert history1[0].content == "Session 1 message"
    assert history2[0].content == "Session 2 message"


@pytest.mark.asyncio
async def test_empty_session_history():
    """Test getting history for a new session."""
    session_id = session_manager.get_or_create_session(None)
    history = session_manager.get_session_history(session_id)
    assert isinstance(history, list)
    assert len(history) == 0


@pytest.mark.asyncio
async def test_session_with_long_conversation():
    """Test session with a long conversation."""
    session_id = session_manager.get_or_create_session(None)

    # Add many messages
    for i in range(10):
        session_manager.add_message(session_id, "user", f"Question {i}")
        session_manager.add_message(session_id, "assistant", f"Answer {i}")

    history = session_manager.get_session_history(session_id)
    assert len(history) == 20

    # Verify order
    assert history[0].content == "Question 0"
    assert history[1].content == "Answer 0"
    assert history[18].content == "Question 9"
    assert history[19].content == "Answer 9"
