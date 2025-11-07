"""
ChromaDB loader utility for initializing vector stores.
"""
from typing import Optional

from app.config import get_settings
from app.utils.logging import get_logger
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    # Fallback for older versions
    from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

logger = get_logger(__name__)
settings = get_settings()


def get_embeddings() -> HuggingFaceEmbeddings:
    """
    Get or create embeddings instance.

    Returns:
        HuggingFaceEmbeddings instance
    """
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
    )


def load_chroma_store(
    collection_name: str, persist_directory: Optional[str] = None
) -> Optional[Chroma]:
    """
    Load a ChromaDB vector store.

    Args:
        collection_name: Name of the collection
        persist_directory: Directory where ChromaDB is persisted

    Returns:
        Chroma vector store instance or None if not available
    """
    persist_dir = persist_directory or settings.chroma_persist_directory

    try:
        store = Chroma(
            persist_directory=persist_dir,
            collection_name=collection_name,
            embedding_function=get_embeddings(),
        )
        logger.info(f"Loaded ChromaDB collection: {collection_name}")
        return store
    except Exception as e:
        logger.warning(f"Could not load ChromaDB collection '{collection_name}': {e}")
        return None
