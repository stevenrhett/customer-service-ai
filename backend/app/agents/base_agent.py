"""Base agent class for all customer service agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseAgent(ABC):
    """Abstract base class for customer service agents."""
    
    def __init__(self, name: str, description: str):
        """Initialize the agent."""
        self.name = name
        self.description = description
    
    @abstractmethod
    def process(self, query: str, context: Dict[str, Any]) -> str:
        """Process a query and return a response."""
        pass
    
    def can_handle(self, query: str) -> bool:
        """Determine if this agent can handle the query."""
        # Default implementation - can be overridden by subclasses
        return True
