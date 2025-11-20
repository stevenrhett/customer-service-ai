"""
Caching service for the Customer Service AI application.
Provides caching for LLM responses and vector store retrievals.
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from langchain_core.documents import Document

logger = logging.getLogger(__name__)


class CacheEntry:
    """A cache entry with expiration."""

    def __init__(self, value: Any, ttl_seconds: int = 3600):
        """
        Initialize cache entry.

        Args:
            value: The cached value
            ttl_seconds: Time to live in seconds (default: 1 hour)
        """
        self.value = value
        self.created_at = datetime.now()
        self.ttl_seconds = ttl_seconds

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        expiration_time = self.created_at + timedelta(seconds=self.ttl_seconds)
        return datetime.now() > expiration_time


class CacheService:
    """
    In-memory caching service.
    Can be replaced with Redis for distributed caching.

    Provides caching for:
    - LLM query responses
    - Vector store retrieval results
    """

    def __init__(self):
        """Initialize cache service."""
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from arguments.

        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create a deterministic string representation
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)

        # Sort kwargs for deterministic key generation
        sorted_kwargs = sorted(kwargs.items())
        key_parts.extend(f"{k}={v}" for k, v in sorted_kwargs)

        key_string = "|".join(key_parts)
        # Hash to keep keys manageable (using SHA-256 for security)
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[key]

        if entry.is_expired():
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 3600):
        """
        Store value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Time to live in seconds
        """
        self._cache[key] = CacheEntry(value, ttl_seconds)

    def delete(self, key: str):
        """Delete cache entry."""
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0

    def get_cache_query_response(
        self, query: str, session_id: str, agent_type: str
    ) -> Optional[str]:
        """
        Get cached query response.

        Args:
            query: User query
            session_id: Session ID
            agent_type: Type of agent (billing, technical, policy)

        Returns:
            Cached response or None
        """
        key = self._generate_key("query_response", query, session_id, agent_type)
        return self.get(key)

    def set_cache_query_response(
        self,
        query: str,
        session_id: str,
        agent_type: str,
        response: str,
        ttl_seconds: int = 3600,
    ):
        """
        Cache query response.

        Args:
            query: User query
            session_id: Session ID
            agent_type: Type of agent
            response: Response to cache
            ttl_seconds: Time to live in seconds
        """
        key = self._generate_key("query_response", query, session_id, agent_type)
        self.set(key, response, ttl_seconds)

    def get_cached_documents(
        self, query: str, collection_name: str, k: int
    ) -> Optional[List[Document]]:
        """
        Get cached vector store documents.

        Args:
            query: Search query
            collection_name: Vector store collection name
            k: Number of documents requested

        Returns:
            Cached documents or None
        """
        key = self._generate_key("vector_store", query, collection_name, k)
        return self.get(key)

    def set_cached_documents(
        self,
        query: str,
        collection_name: str,
        k: int,
        documents: List[Document],
        ttl_seconds: int = 7200,
    ):
        """
        Cache vector store documents.

        Args:
            query: Search query
            collection_name: Vector store collection name
            k: Number of documents
            documents: Documents to cache
            ttl_seconds: Time to live in seconds (default: 2 hours)
        """
        key = self._generate_key("vector_store", query, collection_name, k)
        self.set(key, documents, ttl_seconds)

    def cleanup_expired(self):
        """Remove expired cache entries."""
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]
        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        self.cleanup_expired()
        total_requests = self._hits + self._misses
        hit_rate = (self._hits / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "total_requests": total_requests,
        }


# Global cache instance
cache_service = CacheService()
