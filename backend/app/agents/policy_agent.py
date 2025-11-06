"""
Policy & Compliance Agent - Handles ToS, Privacy Policy, and legal questions.

Implements Pure CAG (Context-Augmented Generation) model:
- Static documents loaded once at initialization
- No vector search needed (documents are relatively small and unchanging)
- Fast, consistent responses
- Context is always the same (Terms of Service, Privacy Policy, etc.)
"""
from typing import List
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from app.config import get_settings
import os

settings = get_settings()


class PolicyAgent:
    """
    Specialized agent for policy and compliance queries.
    Uses Pure CAG for fast, consistent answers from static documents.
    """
    
    def __init__(self, policy_docs_path: str = None):
        """
        Initialize the policy agent.
        
        Args:
            policy_docs_path: Path to directory containing policy documents
        """
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,  # Zero temperature for consistent policy answers
            openai_api_key=settings.openai_api_key
        )
        
        # Load all policy documents into context (CAG approach)
        self.policy_context = self._load_policy_documents(policy_docs_path)
    
    def _load_policy_documents(self, docs_path: str = None) -> str:
        """
        Load all policy documents into a single context string.
        This is done once at initialization.
        
        Args:
            docs_path: Path to policy documents directory
            
        Returns:
            Combined context from all policy documents
        """
        if not docs_path:
            # Default path
            docs_path = os.path.join(
                os.path.dirname(__file__), 
                "../../data/raw/policy"
            )
        
        policy_docs = []
        
        # Try to load policy documents if they exist
        if os.path.exists(docs_path):
            for filename in os.listdir(docs_path):
                if filename.endswith(('.txt', '.md')):
                    filepath = os.path.join(docs_path, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            policy_docs.append(f"=== {filename} ===\n{content}")
                    except Exception as e:
                        print(f"Warning: Could not load {filename}: {e}")
        
        if policy_docs:
            return "\n\n".join(policy_docs)
        else:
            # Fallback if no documents loaded
            return """=== DEFAULT POLICY CONTEXT ===
            Policy documents not yet loaded. Please run the data ingestion script.
            """
    
    async def process_query(
        self, 
        query: str, 
        session_id: str, 
        history: List[BaseMessage] = None
    ) -> str:
        """
        Process a policy query using Pure CAG.
        
        Uses pre-loaded context (no retrieval needed).
        
        Args:
            query: User's policy question
            session_id: Session identifier
            history: Conversation history
            
        Returns:
            Agent's response
        """
        # Build system prompt with pre-loaded policy context
        system_prompt = """You are a policy and compliance support agent.
        Use the following policy documents to answer the customer's question.
        
        Guidelines:
        - Provide accurate information based on the policies
        - Quote specific sections when relevant
        - Be clear and professional
        - If information isn't in the policies, say so clearly
        - For legal questions, remind users to consult legal counsel for specific advice
        
        Policy Documents:
        {context}
        """
        
        # Build message list
        messages = [
            SystemMessage(content=system_prompt.format(context=self.policy_context))
        ]
        
        # Include recent conversation history
        if history:
            messages.extend(history[-3:])
        
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
        Stream response for policy query token-by-token.
        
        Args:
            query: User's policy question
            session_id: Session identifier
            history: Conversation history
            
        Yields:
            Chunks of the response as they're generated
        """
        # Build system prompt with pre-loaded policy context
        system_prompt = """You are a policy and compliance support agent.
        Use the following policy documents to answer the customer's question.
        
        Guidelines:
        - Provide accurate information based on the policies
        - Quote specific sections when relevant
        - Be clear and professional
        - If information isn't in the policies, say so clearly
        - For legal questions, remind users to consult legal counsel for specific advice
        
        Policy Documents:
        {context}
        """
        
        # Build message list
        messages = [
            SystemMessage(content=system_prompt.format(context=self.policy_context))
        ]
        
        # Include recent conversation history
        if history:
            messages.extend(history[-3:])
        
        messages.append(HumanMessage(content=query))
        
        # Stream response token-by-token
        async for chunk in self.llm.astream(messages):
            if chunk.content:
                yield chunk.content
    
    def reload_policy_documents(self, docs_path: str = None):
        """
        Reload policy documents from disk.
        Useful if policies are updated.
        
        Args:
            docs_path: Path to policy documents directory
        """
        self.policy_context = self._load_policy_documents(docs_path)
    
    def get_loaded_context(self) -> str:
        """
        Get the currently loaded policy context.
        Useful for debugging.
        
        Returns:
            The complete policy context string
        """
        return self.policy_context
