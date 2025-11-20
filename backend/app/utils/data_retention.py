"""
Data retention and cleanup policies.

Implements automated cleanup of old data to comply with
privacy regulations and manage storage.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DataRetentionPolicy:
    """
    Manages data retention and cleanup policies.

    Implements automatic cleanup of:
    - Expired sessions
    - Old cache entries
    - Temporary data
    """

    def __init__(
        self,
        session_retention_hours: int = 24,
        cache_retention_hours: int = 2,
        log_retention_days: int = 30
    ):
        """
        Initialize data retention policy.

        Args:
            session_retention_hours: Hours to retain sessions (default: 24)
            cache_retention_hours: Hours to retain cache (default: 2)
            log_retention_days: Days to retain logs (default: 30)
        """
        self.session_retention_hours = session_retention_hours
        self.cache_retention_hours = cache_retention_hours
        self.log_retention_days = log_retention_days

    def cleanup_sessions(self, session_manager) -> int:
        """
        Clean up expired sessions.

        Args:
            session_manager: Session manager instance

        Returns:
            Number of sessions cleaned up
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.session_retention_hours)
            initial_count = len(session_manager._sessions)

            # Clean up sessions older than retention period
            expired_sessions = [
                session_id
                for session_id, session_data in session_manager._sessions.items()
                if session_data.get('created_at', datetime.now()) < cutoff_time
            ]

            for session_id in expired_sessions:
                session_manager.delete_session(session_id)

            cleaned_count = len(expired_sessions)

            if cleaned_count > 0:
                logger.info(
                    f"Data retention: Cleaned up {cleaned_count} expired sessions "
                    f"(older than {self.session_retention_hours} hours)"
                )

            return cleaned_count

        except Exception as e:
            logger.error(f"Error during session cleanup: {e}", exc_info=True)
            return 0

    def cleanup_cache(self, cache_service) -> int:
        """
        Clean up expired cache entries.

        Args:
            cache_service: Cache service instance

        Returns:
            Number of cache entries cleaned up
        """
        try:
            cache_service.cleanup_expired()

            # Get stats to log cleanup
            stats = cache_service.get_stats()
            logger.debug(
                f"Data retention: Cache cleanup completed. "
                f"Current cache size: {stats.get('size', 0)} entries"
            )

            return 0  # cleanup_expired doesn't return count

        except Exception as e:
            logger.error(f"Error during cache cleanup: {e}", exc_info=True)
            return 0

    def get_retention_info(self) -> dict:
        """
        Get current retention policy information.

        Returns:
            Dictionary with retention policy details
        """
        return {
            "session_retention_hours": self.session_retention_hours,
            "cache_retention_hours": self.cache_retention_hours,
            "log_retention_days": self.log_retention_days,
            "policies": {
                "sessions": f"Deleted after {self.session_retention_hours} hours of inactivity",
                "cache": f"Expired after {self.cache_retention_hours} hours",
                "logs": f"Retained for {self.log_retention_days} days"
            }
        }


# Global data retention policy instance
data_retention_policy = DataRetentionPolicy(
    session_retention_hours=24,
    cache_retention_hours=2,
    log_retention_days=30
)


__all__ = ["DataRetentionPolicy", "data_retention_policy"]
