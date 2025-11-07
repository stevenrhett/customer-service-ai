"""
Policy Service - Pure CAG for policy/compliance queries.

Implements Pure CAG:
- Static documents loaded once at initialization
- No vector search needed
- Fast, consistent responses
"""
import os
from typing import AsyncGenerator, List

from app.agents.policy_agent import PolicyAgent
from app.config import get_settings
from app.utils.exceptions import LLMError
from app.utils.logging import get_logger
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)
settings = get_settings()


class PolicyService:
    """
    Service for handling policy/compliance queries using Pure CAG.
    Uses pre-loaded static documents (no retrieval needed).
    """

    def __init__(
        self,
        policy_docs_path: str = None,
        llm: ChatOpenAI = None,
        agent: PolicyAgent = None,
    ):
        """
        Initialize policy service.

        Args:
            policy_docs_path: Path to directory containing policy documents
            llm: OpenAI LLM instance
            agent: Policy agent adapter (for prompt templates)
        """
        self.llm = llm or ChatOpenAI(
            model=settings.openai_model,
            temperature=0,  # Zero temperature for consistent policy answers
            openai_api_key=settings.openai_api_key,
        )
        self.agent = agent
        self.policy_context = self._load_policy_documents(policy_docs_path)

    def _load_policy_documents(self, docs_path: str = None) -> str:
        """
        Load all policy documents into a single context string.

        Args:
            docs_path: Path to policy documents directory

        Returns:
            Combined context from all policy documents
        """
        if not docs_path:
            # Default path relative to backend/
            docs_path = os.path.join(os.path.dirname(__file__), "../../data/raw/policy")
            docs_path = os.path.abspath(docs_path)

        policy_docs = []

        if os.path.exists(docs_path):
            for filename in os.listdir(docs_path):
                if filename.endswith((".txt", ".md")):
                    filepath = os.path.join(docs_path, filename)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read()
                            policy_docs.append(f"=== {filename} ===\n{content}")
                    except Exception as e:
                        logger.warning(f"Could not load {filename}: {e}")
        else:
            logger.warning(f"Policy documents path does not exist: {docs_path}")

        if policy_docs:
            return "\n\n".join(policy_docs)
        else:
            logger.warning("No policy documents loaded, using default context")
            return """=== DEFAULT POLICY CONTEXT ===
Policy documents not yet loaded. Please run the data ingestion script.
"""

    async def process_query(
        self, query: str, session_id: str, history: List[BaseMessage] = None
    ) -> str:
        """
        Process policy query using Pure CAG.

        Args:
            query: User's policy question
            session_id: Session identifier
            history: Conversation history

        Returns:
            Response string

        Raises:
            LLMError: If LLM call fails
        """
        # Build system prompt with pre-loaded policy context
        if self.agent:
            system_prompt = self.agent._get_system_prompt(self.policy_context)
        else:
            system_prompt = """You are a policy and compliance support agent.
Use the following policy documents to answer the customer's question.

Guidelines:
- Provide accurate information based on the policies
- Quote specific sections when relevant
- Be clear and professional
- If information isn't in the policies, say so clearly
- For legal questions, remind users to consult legal counsel for specific advice

Policy Documents:
{context}""".format(
                context=self.policy_context
            )

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history[-3:])

        messages.append(HumanMessage(content=query))

        # Generate response
        try:
            response = await self.llm.ainvoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error processing policy query: {e}", exc_info=True)
            raise LLMError(
                f"Failed to process policy query: {str(e)}", provider="openai"
            )

    async def stream_query(
        self, query: str, session_id: str, history: List[BaseMessage] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream policy query response token-by-token.

        Args:
            query: User's policy question
            session_id: Session identifier
            history: Conversation history

        Yields:
            Response chunks as strings
        """
        # Build system prompt with pre-loaded policy context
        if self.agent:
            system_prompt = self.agent._get_system_prompt(self.policy_context)
        else:
            system_prompt = """You are a policy and compliance support agent.
Use the following policy documents to answer the customer's question.

Guidelines:
- Provide accurate information based on the policies
- Quote specific sections when relevant
- Be clear and professional
- If information isn't in the policies, say so clearly
- For legal questions, remind users to consult legal counsel for specific advice

Policy Documents:
{context}""".format(
                context=self.policy_context
            )

        # Build message list
        messages = [SystemMessage(content=system_prompt)]

        if history:
            messages.extend(history[-3:])

        messages.append(HumanMessage(content=query))

        # Stream response
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"Error streaming policy query: {e}", exc_info=True)
            raise LLMError(
                f"Failed to stream policy query: {str(e)}", provider="openai"
            )

    def reload_policy_documents(self, docs_path: str = None):
        """
        Reload policy documents from disk.

        Args:
            docs_path: Path to policy documents directory
        """
        self.policy_context = self._load_policy_documents(docs_path)
        logger.info("Policy documents reloaded")
