"""
Technical Service - Pure RAG for technical support queries.

Implements Pure RAG:
- Every query retrieves from dynamic knowledge base
- No caching (information changes frequently)
- Searches technical docs, bug reports, forum posts
"""
from typing import AsyncGenerator, List, Union

from app.agents.technical_agent import TechnicalAgent
from app.config import get_settings
from app.services.cache_service import cache_service
from app.utils.exceptions import LLMError, VectorStoreError
from app.utils.logging import get_logger
from langchain_aws import ChatBedrock
from langchain_community.vectorstores import Chroma
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)
settings = get_settings()


class TechnicalService:
    """
    Service for handling technical support queries using Pure RAG.
    Always retrieves fresh information from the knowledge base.
    """

    def __init__(
        self,
        vector_store: Chroma = None,
        llm: Union[ChatOpenAI, ChatBedrock] = None,
        agent: TechnicalAgent = None,
    ):
        """
        Initialize technical service.

        Args:
            vector_store: ChromaDB vector store with technical documents
            llm: LLM instance (OpenAI or Bedrock)
            agent: Technical agent adapter (for prompt templates)
        """
        self.vector_store = vector_store
        
        # Use provided LLM or create one based on configuration
        if llm:
            self.llm = llm
        elif settings.use_bedrock_for_services or not settings.openai_api_key:
            # Use Bedrock if configured or if OpenAI key is missing
            logger.info("Using AWS Bedrock (Claude) for technical service")
            # Configure credentials (bearer token or access keys)
            import os
            if settings.aws_bearer_token_bedrock:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.aws_bearer_token_bedrock
                logger.debug("Using AWS Bedrock bearer token for authentication")
            elif settings.aws_access_key_id and settings.aws_secret_access_key:
                os.environ["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
                os.environ["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
                if settings.aws_session_token:
                    os.environ["AWS_SESSION_TOKEN"] = settings.aws_session_token
            
            self.llm = ChatBedrock(
                model_id=settings.bedrock_service_model_id,
                region_name=settings.aws_region,
                credentials_profile_name=None,
            )
        else:
            # Default to OpenAI
            self.llm = ChatOpenAI(
                model=settings.openai_model,
                temperature=0,
                openai_api_key=settings.openai_api_key,
            )
        
        self.agent = agent

        if vector_store:
            self.retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 5},  # More context for technical issues
            )
        else:
            self.retriever = None
            logger.warning("Technical vector store not available")

    async def process_query(
        self, query: str, session_id: str, history: List[BaseMessage] = None
    ) -> str:
        """
        Process technical query using Pure RAG.

        Args:
            query: User's technical question
            session_id: Session identifier
            history: Conversation history

        Returns:
            Response string

        Raises:
            LLMError: If LLM call fails
            VectorStoreError: If vector store not available
        """
        if not self.retriever:
            raise VectorStoreError(
                "Technical vector store not available. Please run data ingestion."
            )

        # Retrieve relevant documents (cache retrieval results for performance)
        try:
            cached_docs = cache_service.get_cached_documents(query, "technical", k=5)
            if cached_docs:
                docs = cached_docs
            else:
                docs = self.retriever.get_relevant_documents(query)
                # Cache documents (shorter TTL for technical docs)
                cache_service.set_cached_documents(
                    query, "technical", k=5, documents=docs, ttl_seconds=1800
                )

            # Build context from retrieved documents
            context_parts = []
            for i, doc in enumerate(docs, 1):
                metadata = doc.metadata
                source = metadata.get("source", "Unknown")
                doc_type = metadata.get("type", "document")
                context_parts.append(
                    f"[Source {i} - {doc_type} from {source}]\n{doc.page_content}"
                )

            context = (
                "\n\n".join(context_parts)
                if context_parts
                else "No relevant technical documentation found."
            )
        except Exception as e:
            logger.error(f"Error retrieving technical documents: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to retrieve technical documents: {str(e)}")

        # Build system prompt
        if self.agent:
            system_prompt = self.agent._get_system_prompt(context)
        else:
            system_prompt = """You are a knowledgeable technical support agent.
Use the following technical documentation, bug reports, and forum posts to help the customer.

Guidelines:
- Provide step-by-step troubleshooting when appropriate
- Reference specific error codes or messages if mentioned
- Suggest workarounds for known issues
- Be clear about what is a confirmed bug vs. expected behavior
- Cite which source (by number) you're using if helpful

Technical Knowledge Base:
{context}""".format(
                context=context
            )

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history[-4:])  # Last 4 messages for technical context

        messages.append(HumanMessage(content=query))

        # Generate response
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error processing technical query: {e}", exc_info=True)
            raise LLMError(
                f"Failed to process technical query: {str(e)}", provider="openai"
            )

    async def stream_query(
        self, query: str, session_id: str, history: List[BaseMessage] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream technical query response token-by-token.

        Args:
            query: User's technical question
            session_id: Session identifier
            history: Conversation history

        Yields:
            Response chunks as strings
        """
        if not self.retriever:
            raise VectorStoreError(
                "Technical vector store not available. Please run data ingestion."
            )

        # Retrieve relevant documents
        try:
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

            context = (
                "\n\n".join(context_parts)
                if context_parts
                else "No relevant technical documentation found."
            )
        except Exception as e:
            logger.error(f"Error retrieving technical documents: {e}", exc_info=True)
            raise VectorStoreError(f"Failed to retrieve technical documents: {str(e)}")

        # Build system prompt
        if self.agent:
            system_prompt = self.agent._get_system_prompt(context)
        else:
            system_prompt = """You are a knowledgeable technical support agent.
Use the following technical documentation, bug reports, and forum posts to help the customer.

Guidelines:
- Provide step-by-step troubleshooting when appropriate
- Reference specific error codes or messages if mentioned
- Suggest workarounds for known issues
- Be clear about what is a confirmed bug vs. expected behavior
- Cite which source (by number) you're using if helpful

Technical Knowledge Base:
{context}""".format(
                context=context
            )

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history[-4:])

        messages.append(HumanMessage(content=query))

        # Stream response
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming technical query: {e}", exc_info=True)
            raise LLMError(
                f"Failed to stream technical query: {str(e)}", provider="openai"
            )
