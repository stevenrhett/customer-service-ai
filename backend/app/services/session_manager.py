"""
Session Management Service - Handles conversation session persistence.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.utils.exceptions import SessionError
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

logger = logging.getLogger(__name__)

# In-memory session storage (use Redis in production)
_sessions: Dict[str, Dict] = {}

# Session configuration
SESSION_TIMEOUT_HOURS = 24  # Sessions expire after 24 hours of inactivity
MAX_SESSION_SIZE = 1000  # Maximum messages per session


class SessionManager:
    """
    Manages conversation sessions.
    Stores conversation history in memory (replace with Redis in production).
    Includes session validation, expiration, and size limits.
    """

    def __init__(
        self,
        timeout_hours: int = SESSION_TIMEOUT_HOURS,
        max_size: int = MAX_SESSION_SIZE,
    ):
        """
        Initialize session manager.

        Args:
            timeout_hours: Hours of inactivity before session expires
            max_size: Maximum number of messages per session
        """
        self.timeout_hours = timeout_hours
        self.max_size = max_size

    def _validate_session_id(self, session_id: str) -> None:
        """Validate session ID format."""
        if not session_id or not isinstance(session_id, str):
            raise SessionError("Invalid session ID format", session_id=session_id)

        # Check if it's a valid UUID format
        try:
            uuid.UUID(session_id)
        except ValueError:
            # Allow non-UUID session IDs but validate they're not empty
            if len(session_id.strip()) == 0:
                raise SessionError("Session ID cannot be empty", session_id=session_id)

    def _is_session_expired(self, session: Dict) -> bool:
        """Check if session has expired based on last activity."""
        if "updated_at" not in session:
            return True

        updated_at = session["updated_at"]
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)

        expiration_time = updated_at + timedelta(hours=self.timeout_hours)
        return datetime.now() > expiration_time

    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        expired_sessions = [
            sid
            for sid, session in _sessions.items()
            if self._is_session_expired(session)
        ]
        for sid in expired_sessions:
            logger.debug(f"Cleaning up expired session: {sid}")
            del _sessions[sid]

    def get_or_create_session(self, session_id: Optional[str] = None) -> str:
        """
        Get existing session or create a new one.

        Args:
            session_id: Optional session ID to retrieve

        Returns:
            Session ID string

        Raises:
            SessionError: If session ID is invalid
        """
        # Cleanup expired sessions periodically
        self._cleanup_expired_sessions()

        if session_id:
            self._validate_session_id(session_id)

            # Check if session exists and is not expired
            if session_id in _sessions:
                if self._is_session_expired(_sessions[session_id]):
                    logger.info(f"Session {session_id} expired, creating new session")
                    del _sessions[session_id]
                else:
                    return session_id

        # Create new session
        new_session_id = session_id or str(uuid.uuid4())
        _sessions[new_session_id] = {
            "id": new_session_id,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": [],
        }
        logger.debug(f"Created new session: {new_session_id}")
        return new_session_id

    def get_session_history(self, session_id: str) -> List[BaseMessage]:
        """
        Get conversation history for a session.

        Args:
            session_id: Session identifier

        Returns:
            List of LangChain messages

        Raises:
            SessionError: If session doesn't exist or is invalid
        """
        self._validate_session_id(session_id)

        if session_id not in _sessions:
            logger.warning(f"Session {session_id} not found")
            return []

        session = _sessions[session_id]

        # Check if session expired
        if self._is_session_expired(session):
            logger.info(f"Session {session_id} expired")
            del _sessions[session_id]
            raise SessionError("Session has expired", session_id=session_id)

        # Convert stored messages to LangChain messages
        stored_messages = session["messages"]
        messages = []

        for msg in stored_messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        return messages

    def add_message(self, session_id: str, role: str, content: str):
        """
        Add a message to the session history.

        Args:
            session_id: Session identifier
            role: Message role ("user" or "assistant")
            content: Message content

        Raises:
            SessionError: If session doesn't exist, is expired, or exceeds size limit
        """
        self._validate_session_id(session_id)

        if role not in ["user", "assistant"]:
            raise SessionError(
                f"Invalid message role: {role}. Must be 'user' or 'assistant'",
                session_id=session_id,
            )

        if session_id not in _sessions:
            self.get_or_create_session(session_id)

        session = _sessions[session_id]

        # Check if session expired
        if self._is_session_expired(session):
            logger.info(f"Session {session_id} expired during message add")
            del _sessions[session_id]
            raise SessionError("Session has expired", session_id=session_id)

        # Check session size limit
        if len(session["messages"]) >= self.max_size:
            logger.warning(f"Session {session_id} reached maximum size limit")
            raise SessionError(
                f"Session has reached maximum size limit ({self.max_size} messages). "
                "Please start a new session.",
                session_id=session_id,
            )

        session["messages"].append(
            {"role": role, "content": content, "timestamp": datetime.now()}
        )
        session["updated_at"] = datetime.now()
        logger.debug(f"Added {role} message to session {session_id}")

    def clear_session(self, session_id: str):
        """
        Clear a session's history.

        Args:
            session_id: Session identifier

        Raises:
            SessionError: If session doesn't exist
        """
        self._validate_session_id(session_id)

        if session_id not in _sessions:
            raise SessionError("Session not found", session_id=session_id)

        _sessions[session_id]["messages"] = []
        _sessions[session_id]["updated_at"] = datetime.now()
        logger.info(f"Cleared session {session_id}")

    def delete_session(self, session_id: str):
        """
        Delete a session entirely.

        Args:
            session_id: Session identifier
        """
        self._validate_session_id(session_id)

        if session_id in _sessions:
            del _sessions[session_id]
            logger.info(f"Deleted session {session_id}")

    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """
        Get session metadata.

        Args:
            session_id: Session identifier

        Returns:
            Session info dict or None
        """
        self._validate_session_id(session_id)

        if session_id not in _sessions:
            return None

        session = _sessions[session_id].copy()

        # Don't include full message content in info
        session["message_count"] = len(session["messages"])
        session["messages"] = None  # Don't return full messages

        return session

    def get_all_sessions(self) -> List[str]:
        """
        Get list of all active session IDs.

        Returns:
            List of session IDs
        """
        self._cleanup_expired_sessions()
        return list(_sessions.keys())


# Global instance
session_manager = SessionManager()
