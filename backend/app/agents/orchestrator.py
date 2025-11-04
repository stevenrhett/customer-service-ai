"""Multi-agent orchestrator for routing queries to appropriate agents."""
from typing import List, Dict, Any
from .base_agent import BaseAgent
from .general_agent import GeneralInquiryAgent
from .technical_agent import TechnicalSupportAgent
from .document_agent import DocumentRetrievalAgent


class AgentOrchestrator:
    """Orchestrates multiple agents to handle customer queries."""
    
    def __init__(self, agents: List[BaseAgent]):
        """Initialize the orchestrator with a list of agents."""
        self.agents = agents
        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
    
    def route_query(self, query: str, conversation_id: str = None) -> tuple[str, str]:
        """
        Route a query to the most appropriate agent.
        Returns: (response, agent_name)
        """
        # Check conversation history
        if conversation_id and conversation_id in self.conversation_history:
            history = self.conversation_history[conversation_id]
        else:
            history = []
            if conversation_id:
                self.conversation_history[conversation_id] = history
        
        # Find the best agent for this query
        # Priority: Document Agent > Technical Agent > General Agent
        selected_agent = None
        
        for agent in self.agents:
            if agent.can_handle(query):
                selected_agent = agent
                break
        
        # Default to the last agent (should be General Agent)
        if not selected_agent:
            selected_agent = self.agents[-1]
        
        # Process the query
        context = {
            "conversation_history": history,
            "conversation_id": conversation_id
        }
        
        response = selected_agent.process(query, context)
        
        # Update conversation history
        if conversation_id:
            history.append({"role": "user", "content": query})
            history.append({"role": "assistant", "content": response})
        
        return response, selected_agent.name
    
    def get_conversation_history(self, conversation_id: str) -> List[Dict[str, str]]:
        """Get the conversation history for a given conversation ID."""
        return self.conversation_history.get(conversation_id, [])
    
    def clear_conversation(self, conversation_id: str):
        """Clear the conversation history for a given conversation ID."""
        if conversation_id in self.conversation_history:
            del self.conversation_history[conversation_id]
