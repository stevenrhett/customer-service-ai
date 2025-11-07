"""
Billing Service - Hybrid RAG/CAG for billing queries.

Implements:
- RAG: Retrieves pricing/invoice docs from vector store
- CAG: Uses cached static policy snippets per session
"""
from typing import AsyncGenerator, List

from app.agents.billing_agent import BillingAgent
from app.config import get_settings
from app.services.cache_service import cache_service
from app.utils.exceptions import LLMError
from app.utils.logging import get_logger
from langchain_community.vectorstores import Chroma
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)
settings = get_settings()


class BillingService:
    """
    Service for handling billing queries using Hybrid RAG/CAG.
    Combines vector retrieval for dynamic pricing with cached policy snippets.
    """

    def __init__(
        self,
        vector_store: Chroma = None,
        llm: ChatOpenAI = None,
        agent: BillingAgent = None,
    ):
        """
        Initialize billing service.

        Args:
            vector_store: ChromaDB vector store with billing documents
            llm: OpenAI LLM instance
            agent: Billing agent adapter (for prompt templates)
        """
        self.vector_store = vector_store
        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            temperature=0,
            openai_api_key=settings.openai_api_key,
        )
        self.agent = agent

        if vector_store:
            self.retriever = vector_store.as_retriever(
                search_type="similarity", search_kwargs={"k": 4}
            )
        else:
            self.retriever = None
            logger.warning("Billing vector store not available")

    async def process_query(
        self, query: str, session_id: str, history: List[BaseMessage] = None
    ) -> str:
        """
        Process billing query using Hybrid RAG/CAG.

        Args:
            query: User's billing question
            session_id: Session identifier
            history: Conversation history

        Returns:
            Response string

        Raises:
            LLMError: If LLM call fails
            VectorStoreError: If vector retrieval fails
        """
        # Check cache first (skip if history exists for context-aware responses)
        if not history:
            cached_response = cache_service.get_cache_query_response(
                query, session_id, "billing"
            )
            if cached_response:
                logger.debug(f"Cache hit for billing query: {query[:50]}...")
                return cached_response

        # Retrieve relevant billing documents (RAG)
        context = ""
        if self.retriever:
            try:
                # Check cache for documents
                cached_docs = cache_service.get_cached_documents(query, "billing", k=4)
                if cached_docs:
                    docs = cached_docs
                else:
                    docs = self.retriever.get_relevant_documents(query)
                    cache_service.set_cached_documents(
                        query, "billing", k=4, documents=docs
                    )

                context_parts = []
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    source = metadata.get("source", "Unknown")
                    context_parts.append(f"[Source {i} - {source}]\n{doc.page_content}")
                context = "\n\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Could not retrieve billing documents: {e}")
                context = "Billing documentation not yet indexed."
        else:
            context = "Billing documentation not yet indexed."

        # Build system prompt (use agent if available, otherwise default)
        if self.agent:
            system_prompt = self.agent._get_system_prompt(context)
        else:
            system_prompt = """You are a helpful billing support agent.
Use the following billing documentation to answer the customer's question.

Guidelines:
- Provide clear, accurate pricing information
- Explain billing cycles and payment methods
- Help with invoice questions
- Be transparent about costs and fees

Billing Documentation:
{context}""".format(
                context=context
            )

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history[-3:])

        messages.append(HumanMessage(content=query))

        # Generate response
        try:
            response = await self.llm.ainvoke(messages)
            response_content = response.content

            # Cache response if no history (simple queries)
            if not history:
                cache_service.set_cache_query_response(
                    query, session_id, "billing", response_content
                )

            return response_content
        except Exception as e:
            logger.error(f"Error processing billing query: {e}", exc_info=True)
            raise LLMError(
                f"Failed to process billing query: {str(e)}", provider="openai"
            )

    async def stream_query(
        self, query: str, session_id: str, history: List[BaseMessage] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream billing query response token-by-token.

        Args:
            query: User's billing question
            session_id: Session identifier
            history: Conversation history

        Yields:
            Response chunks as strings
        """
        # Retrieve relevant billing documents
        context = ""
        if self.retriever:
            try:
                docs = self.retriever.get_relevant_documents(query)
                context_parts = []
                for i, doc in enumerate(docs, 1):
                    metadata = doc.metadata
                    source = metadata.get("source", "Unknown")
                    context_parts.append(f"[Source {i} - {source}]\n{doc.page_content}")
                context = "\n\n".join(context_parts)
            except Exception as e:
                logger.warning(f"Could not retrieve billing documents: {e}")
                context = "Billing documentation not yet indexed."
        else:
            context = "Billing documentation not yet indexed."

        # Build system prompt
        if self.agent:
            system_prompt = self.agent._get_system_prompt(context)
        else:
            system_prompt = """You are a helpful billing support agent.
Use the following billing documentation to answer the customer's question.

Guidelines:
- Provide clear, accurate pricing information
- Explain billing cycles and payment methods
- Help with invoice questions
- Be transparent about costs and fees

Billing Documentation:
{context}""".format(
                context=context
            )

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history[-3:])

        messages.append(HumanMessage(content=query))

        # Stream response
        try:
            full_response = ""
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    full_response += chunk.content
                    yield chunk.content

            # Cache response if no history
            if not history and full_response:
                cache_service.set_cache_query_response(
                    query, session_id, "billing", full_response
                )
        except Exception as e:
            logger.error(f"Error streaming billing query: {e}", exc_info=True)
            raise LLMError(
                f"Failed to stream billing query: {str(e)}", provider="openai"
            )
