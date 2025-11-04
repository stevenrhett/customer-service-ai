"""Document retrieval agent for answering questions based on stored documents."""
from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from typing import Dict, Any
from .base_agent import BaseAgent


class DocumentRetrievalAgent(BaseAgent):
    """Agent for answering questions using document retrieval."""
    
    def __init__(self, openai_api_key: str, retriever):
        """Initialize the document retrieval agent."""
        super().__init__(
            name="Document Retrieval Agent",
            description="Answers questions based on stored documentation"
        )
        self.llm = ChatOpenAI(
            temperature=0.3,
            model="gpt-3.5-turbo",
            openai_api_key=openai_api_key
        )
        
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
    
    def process(self, query: str, context: Dict[str, Any]) -> str:
        """Process a query using document retrieval."""
        result = self.qa_chain({"query": query})
        
        # Format response with sources
        answer = result["result"]
        sources = result.get("source_documents", [])
        
        if sources:
            answer += "\n\n---\nSources consulted:"
            for i, doc in enumerate(sources[:3], 1):
                source_name = doc.metadata.get("filename", "Unknown")
                answer += f"\n{i}. {source_name}"
        
        return answer
    
    def can_handle(self, query: str) -> bool:
        """Check if query seems to be asking about documentation."""
        doc_keywords = ["how to", "documentation", "guide", "instructions", "manual", "help with"]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in doc_keywords)
