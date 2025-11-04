"""ChromaDB vector store service for document storage and retrieval."""
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict
import os


class VectorStoreService:
    """Service for managing vector store operations with ChromaDB."""
    
    def __init__(self, persist_directory: str, openai_api_key: str):
        """Initialize the vector store service."""
        self.persist_directory = persist_directory
        os.makedirs(persist_directory, exist_ok=True)
        
        self.embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        
        self.vectorstore = Chroma(
            client=self.client,
            collection_name="customer_service_docs",
            embedding_function=self.embeddings
        )
    
    def add_document(self, text: str, metadata: Dict) -> str:
        """Add a document to the vector store."""
        # Split text into chunks
        chunks = self.text_splitter.split_text(text)
        
        # Add metadata to each chunk
        metadatas = [metadata.copy() for _ in chunks]
        for i, meta in enumerate(metadatas):
            meta["chunk_index"] = i
        
        # Add to vector store
        ids = self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)
        
        return metadata.get("document_id", ids[0] if ids else "")
    
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """Search for relevant documents."""
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            }
            for doc, score in results
        ]
    
    def get_retriever(self, k: int = 3):
        """Get a retriever for the vector store."""
        return self.vectorstore.as_retriever(search_kwargs={"k": k})
