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

        # Generate response
        response = self.llm.invoke(messages)

        return response.content

    async def stream(
            self,
            message: str,
            session_id: str,
            history: List[BaseMessage] = None
    ):
        """Stream response for billing query."""
        content = await self.process_query(message, session_id, history)

        # Simulate streaming by yielding chunks
        words = content.split()
        chunk_size = 5

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size])
            yield {
                "content": chunk + " ",
                "is_final": False
            }

        yield {
            "content": "",
            "is_final": True
        }