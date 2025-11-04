"""Technical support agent for handling technical issues."""
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any
from .base_agent import BaseAgent


class TechnicalSupportAgent(BaseAgent):
    """Agent for handling technical support requests."""
    
    def __init__(self, openai_api_key: str):
        """Initialize the technical support agent."""
        super().__init__(
            name="Technical Support Agent",
            description="Handles technical issues and troubleshooting"
        )
        self.llm = ChatOpenAI(
            temperature=0.5,
            model="gpt-3.5-turbo",
            openai_api_key=openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a technical support specialist. 
            Help customers troubleshoot technical issues with clear, step-by-step instructions.
            Be patient and ask clarifying questions when needed.
            Always maintain a professional and helpful tone."""),
            ("user", "{query}")
        ])
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def process(self, query: str, context: Dict[str, Any]) -> str:
        """Process a technical support request."""
        response = self.chain.run(query=query)
        return response
    
    def can_handle(self, query: str) -> bool:
        """Check if query is related to technical issues."""
        tech_keywords = ["error", "not working", "broken", "issue", "problem", "bug", "crash", "fail"]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in tech_keywords)
