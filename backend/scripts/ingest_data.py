"""
Data Ingestion Script for Customer Service AI

This script processes mock documents and loads them into ChromaDB with embeddings.
It creates separate collections for each agent type (billing, technical, policy).
"""
import os
import sys
from pathlib import Path
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.schema import Document

# Add parent directory to path to import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings

settings = get_settings()


class DataIngester:
    """Handles ingestion of documents into vector database."""
    
    def __init__(self):
        """Initialize the data ingester."""
        self.persist_directory = settings.chroma_persist_directory
        
        # Initialize embeddings model
        print("Loading embedding model...")
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        # Document paths
        self.base_path = Path(__file__).parent.parent / "data" / "mock_documents"
        
    def load_documents_from_directory(self, directory: Path, doc_type: str) -> List[Document]:
        """
        Load all text documents from a directory.
        
        Args:
            directory: Path to directory containing documents
            doc_type: Type of document (billing, technical, policy)
            
        Returns:
            List of Document objects
        """
        documents = []
        
        if not directory.exists():
            print(f"Warning: Directory {directory} does not exist")
            return documents
        
        for file_path in directory.glob("*.txt"):
            print(f"Loading {file_path.name}...")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # Create document with metadata
                doc = Document(
                    page_content=content,
                    metadata={
                        "source": file_path.name,
                        "type": doc_type,
                        "path": str(file_path)
                    }
                )
                documents.append(doc)
        
        return documents
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks.
        
        Args:
            documents: List of documents to split
            
        Returns:
            List of chunked documents
        """
        return self.text_splitter.split_documents(documents)
    
    def ingest_to_collection(self, documents: List[Document], collection_name: str):
        """
        Ingest documents into a ChromaDB collection.
        
        Args:
            documents: List of documents to ingest
            collection_name: Name of the collection
        """
        if not documents:
            print(f"No documents to ingest for {collection_name}")
            return
        
        print(f"\nIngesting {len(documents)} documents into '{collection_name}' collection...")
        
        # Split documents into chunks
        chunks = self.split_documents(documents)
        print(f"Created {len(chunks)} chunks")
        
        # Create vector store
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            collection_name=collection_name,
            persist_directory=self.persist_directory
        )
        
        print(f"✓ Successfully ingested {collection_name} documents")
        return vector_store
    
    def ingest_all(self):
        """Ingest all document types into their respective collections."""
        print("=" * 60)
        print("Starting Data Ingestion Process")
        print("=" * 60)
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Ingest billing documents
        print("\n--- Billing Documents ---")
        billing_docs = self.load_documents_from_directory(
            self.base_path / "billing",
            "billing"
        )
        self.ingest_to_collection(billing_docs, "billing")
        
        # Ingest technical documents
        print("\n--- Technical Documents ---")
        technical_docs = self.load_documents_from_directory(
            self.base_path / "technical",
            "technical"
        )
        self.ingest_to_collection(technical_docs, "technical")
        
        # Ingest policy documents
        print("\n--- Policy Documents ---")
        policy_docs = self.load_documents_from_directory(
            self.base_path / "policy",
            "policy"
        )
        self.ingest_to_collection(policy_docs, "policy")
        
        print("\n" + "=" * 60)
        print("Data Ingestion Complete!")
        print("=" * 60)
        print(f"\nVector database location: {self.persist_directory}")
        print("\nCollections created:")
        print("  - billing")
        print("  - technical")
        print("  - policy")
        print("\nYou can now start the API server.")
    
    def verify_ingestion(self):
        """Verify that collections were created and contain data."""
        print("\n" + "=" * 60)
        print("Verifying Ingestion")
        print("=" * 60)
        
        client = chromadb.PersistentClient(path=self.persist_directory)
        
        collections = ["billing", "technical", "policy"]
        for collection_name in collections:
            try:
                collection = client.get_collection(collection_name)
                count = collection.count()
                print(f"✓ Collection '{collection_name}': {count} chunks")
            except Exception as e:
                print(f"✗ Collection '{collection_name}': Error - {e}")


def main():
    """Main entry point for the ingestion script."""
    try:
        ingester = DataIngester()
        ingester.ingest_all()
        ingester.verify_ingestion()
        
        print("\n✓ Ingestion successful! Ready to start the application.")
        
    except Exception as e:
        print(f"\n✗ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
