"""
Vector Store Service - Manages initialization and access to ChromaDB vector stores.
"""
from typing import Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import get_settings
import os

settings = get_settings()


class VectorStoreService:
    """
    Service for managing vector store instances.
    Uses singleton pattern to ensure vector stores are initialized once.
    """
    
    _instance = None
    _billing_store: Optional[Chroma] = None
    _technical_store: Optional[Chroma] = None
    _embeddings: Optional[HuggingFaceEmbeddings] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the vector store service."""
        if self._embeddings is None:
            self._embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={'device': 'cpu'}
            )
    
    def get_billing_store(self) -> Optional[Chroma]:
        """
        Get or create the billing vector store.
        
        Returns:
            Chroma vector store instance or None if not initialized
        """
        if self._billing_store is None:
            try:
                self._billing_store = Chroma(
                    persist_directory=settings.chroma_persist_directory,
                    collection_name="billing",
                    embedding_function=self._embeddings
                )
            except Exception as e:
                print(f"Warning: Could not load billing vector store: {e}")
                return None
        return self._billing_store
    
    def get_technical_store(self) -> Optional[Chroma]:
        """
        Get or create the technical vector store.
        
        Returns:
            Chroma vector store instance or None if not initialized
        """
        if self._technical_store is None:
            try:
                self._technical_store = Chroma(
                    persist_directory=settings.chroma_persist_directory,
                    collection_name="technical",
                    embedding_function=self._embeddings
                )
            except Exception as e:
                print(f"Warning: Could not load technical vector store: {e}")
                return None
        return self._technical_store
    
    def reset(self):
        """Reset all vector stores (useful for testing)."""
        self._billing_store = None
        self._technical_store = None


# Global instance
vector_store_service = VectorStoreService()

