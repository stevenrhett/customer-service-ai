"""
Billing Agent - Handles pricing, billing, and payment questions.

Implements Hybrid RAG + CAG model:
- Retrieves pricing docs from vector store (RAG for current prices)
- Uses cached billing policies (CAG for consistent policy answers)
"""
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_community.vectorstores import Chroma
from app.config import get_settings
from app.services.cache_service import cache_service

settings = get_settings()


class BillingAgent:
    """
    Specialized agent for billing and pricing queries.
    Uses Hybrid RAG+CAG for accurate pricing with consistent policies.
    """

    def __init__(self, vector_store: Chroma = None):
        """
        Initialize the billing agent.

        Args:
            vector_store: ChromaDB vector store with billing documents
        """
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            openai_api_key=settings.openai_api_key
        )

        if vector_store:
            self.retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4}
            )
        else:
            self.retriever = None

    async def process(
            self,
            message: str,
            session_id: str,
            history: List[BaseMessage] = None
    ) -> Dict[str, Any]:
        """
        Process a billing query.

        Args:
            message: User's message
            session_id: Session identifier
            history: Conversation history

        Returns:
            Dictionary with response content
        """
        content = await self.process_query(message, session_id, history)
        return {
            "content": content,
            "confidence": 0.85
        }

    async def process_query(
            self,
            query: str,
            session_id: str,
            history: List[BaseMessage] = None
    ) -> str:
        """
        Process a billing query using Hybrid RAG+CAG.

        Args:
            query: User's billing question
            session_id: Session identifier
            history: Conversation history

        Returns:
            Agent's response
        """
        # Check cache first (skip if history exists to ensure context-aware responses)
        if not history:
            cached_response = cache_service.get_cache_query_response(query, session_id, "billing")
            if cached_response:
                return cached_response
        
        # Retrieve relevant billing documents if available
        context = ""
        if self.retriever:
            try:
                # Check cache for documents
                cached_docs = cache_service.get_cached_documents(query, "billing", k=4)
                if cached_docs:
                    docs = cached_docs
                else:
                    docs = self.retriever.get_relevant_documents(query)
                    # Cache documents for future use
                    cache_service.set_cached_documents(query, "billing", k=4, documents=docs)
                
                context_parts = []
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    source = metadata.get("source", "Unknown")
                    context_parts.append(
                        f"[Source {i} - {source}]\n{doc.page_content}"
                    )
                context = "\n\n".join(context_parts)
            except Exception as e:
                print(f"Warning: Could not retrieve documents: {e}")
                context = "Billing documentation not yet indexed."
        else:
            context = "Billing documentation not yet indexed."

        # Build system prompt
        system_prompt = """You are a helpful billing support agent.
        Use the following billing documentation to answer the customer's question.

        Guidelines:
        - Provide clear, accurate pricing information
        - Explain billing cycles and payment methods
        - Help with invoice questions
        - Be transparent about costs and fees

        Billing Documentation:
        {context}
        """

        # Build message list
        messages = [
            SystemMessage(content=system_prompt.format(context=context))
        ]

        if history:
            messages.extend(history[-3:])

        messages.append(HumanMessage(content=query))

        # Generate response
        response = await self.llm.ainvoke(messages)
        response_content = response.content
        
        # Cache response if no history (simple queries)
        if not history:
            cache_service.set_cache_query_response(query, session_id, "billing", response_content)
        
        return response_content

    async def stream_query(
            self,
            query: str,
            session_id: str,
            history: List[BaseMessage] = None
    ):
        """
        Stream response for billing query token-by-token.
        
        Args:
            query: User's billing question
            session_id: Session identifier
            history: Conversation history
            
        Yields:
            Chunks of the response as they're generated
        """
        # Retrieve relevant billing documents if available
        context = ""
        if self.retriever:
            try:
                docs = self.retriever.get_relevant_documents(query)
                context_parts = []
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    source = metadata.get("source", "Unknown")
                    context_parts.append(
                        f"[Source {i} - {source}]\n{doc.page_content}"
                    )
                context = "\n\n".join(context_parts)
            except Exception as e:
                print(f"Warning: Could not retrieve documents: {e}")
                context = "Billing documentation not yet indexed."
        else:
            context = "Billing documentation not yet indexed."

        # Build system prompt
        system_prompt = """You are a helpful billing support agent.
        Use the following billing documentation to answer the customer's question.

        Guidelines:
        - Provide clear, accurate pricing information
        - Explain billing cycles and payment methods
        - Help with invoice questions
        - Be transparent about costs and fees

        Billing Documentation:
        {context}
        """

        # Build message list
        messages = [
            SystemMessage(content=system_prompt.format(context=context))
        ]

        if history:
            messages.extend(history[-3:])

        messages.append(HumanMessage(content=query))

        # Stream response token-by-token and collect full response for caching
        full_response = ""
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                full_response += chunk.content
                yield chunk.content
        
        # Cache response if no history (simple queries)
        if not history and full_response:
            cache_service.set_cache_query_response(query, session_id, "billing", full_response)