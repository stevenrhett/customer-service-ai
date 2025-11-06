"""
Technical Support Agent - Handles product features, bugs, and troubleshooting.

Implements Pure RAG model:
- Every query retrieves from the dynamic knowledge base
- No caching (information changes frequently with bug fixes, updates)
- Searches technical docs, bug reports, and forum posts
"""
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from app.config import get_settings
from app.services.cache_service import cache_service

settings = get_settings()


class TechnicalAgent:
    """
    Specialized agent for technical support queries.
    Uses Pure RAG for always-current information.
    """
    
    def __init__(self, vector_store: Chroma = None):
        """
        Initialize the technical support agent.
        
        Args:
            vector_store: ChromaDB vector store with technical documents (optional)
        """
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )
        
        # Create retriever with higher k for technical queries
        if vector_store:
            self.retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5}  # More context for technical issues
            )
        else:
            self.retriever = None
    
    async def process_query(
        self, 
        query: str, 
        session_id: str, 
        history: List[BaseMessage] = None
    ) -> str:
        """
        Process a technical support query using Pure RAG.
        
        Always retrieves fresh information from the knowledge base.
        
        Args:
            query: User's technical question
            session_id: Session identifier
            history: Conversation history
            
        Returns:
            Agent's response
        """
        # Retrieve relevant documents (cache retrieval results)
        if not self.retriever:
            context = "Technical documentation not yet indexed. Please run the data ingestion script."
        else:
            # Check cache for documents
            cached_docs = cache_service.get_cached_documents(query, "technical", k=5)
            if cached_docs:
                docs = cached_docs
            else:
                docs = self.retriever.get_relevant_documents(query)
                # Cache documents (shorter TTL for technical docs as they change frequently)
                cache_service.set_cached_documents(query, "technical", k=5, documents=docs, ttl_seconds=1800)
            
            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = metadata.get("source", "Unknown")
                doc_type = metadata.get("type", "document")
                
                context_parts.append(
                    f"[Source {i} - {doc_type} from {source}]\n{doc.page_content}"
                )
            
            context = "\n\n".join(context_parts) if context_parts else "No relevant technical documentation found."
        
        # Build system prompt for technical support
        system_prompt = """You are a knowledgeable technical support agent.
        Use the following technical documentation, bug reports, and forum posts to help the customer.
        
        Guidelines:
        - Provide step-by-step troubleshooting when appropriate
        - Reference specific error codes or messages if mentioned
        - Suggest workarounds for known issues
        - Be clear about what is a confirmed bug vs. expected behavior
        - Cite which source (by number) you're using if helpful
        
        Technical Knowledge Base:
        {context}
        """
        
        # Build message list
        messages = [
            SystemMessage(content=system_prompt.format(context=context))
        ]
        
        # Include recent conversation history for context
        if history:
            messages.extend(history[-4:])  # Last 4 messages for technical context
        
        messages.append(HumanMessage(content=query))
        
        # Generate response
        response = await self.llm.ainvoke(messages)
        
        return response.content
    
    async def stream_query(
        self, 
        query: str, 
        session_id: str, 
        history: List[BaseMessage] = None
    ):
        """
        Stream response for technical query token-by-token.
        
        Args:
            query: User's technical question
            session_id: Session identifier
            history: Conversation history
            
        Yields:
            Chunks of the response as they're generated
        """
        # Always retrieve relevant documents (Pure RAG - no caching)
        if not self.retriever:
            context = "Technical documentation not yet indexed. Please run the data ingestion script."
        else:
            docs = self.retriever.get_relevant_documents(query)
            
            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = metadata.get("source", "Unknown")
                doc_type = metadata.get("type", "document")
                
                context_parts.append(
                    f"[Source {i} - {doc_type} from {source}]\n{doc.page_content}"
                )
            
            context = "\n\n".join(context_parts) if context_parts else "No relevant technical documentation found."
        
        # Build system prompt for technical support
        system_prompt = """You are a knowledgeable technical support agent.
        Use the following technical documentation, bug reports, and forum posts to help the customer.
        
        Guidelines:
        - Provide step-by-step troubleshooting when appropriate
        - Reference specific error codes or messages if mentioned
        - Suggest workarounds for known issues
        - Be clear about what is a confirmed bug vs. expected behavior
        - Cite which source (by number) you're using if helpful
        
        Technical Knowledge Base:
        {context}
        """
        
        # Build message list
        messages = [
            SystemMessage(content=system_prompt.format(context=context))
        ]
        
        # Include recent conversation history for context
        if history:
            messages.extend(history[-4:])  # Last 4 messages for technical context
        
        messages.append(HumanMessage(content=query))
        
        # Stream response token-by-token
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    def get_relevant_docs(self, query: str, k: int = 5) -> List:
        """
        Retrieve relevant technical documents for a query.
        Useful for debugging or understanding what context the agent sees.
        
        Args:
            query: Search query
            k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if not self.retriever:
            return []
        return self.retriever.get_relevant_documents(query)
