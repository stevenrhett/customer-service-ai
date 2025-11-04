"""General inquiry agent for handling general questions."""
from langchain_openai import ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate
from typing import Dict, Any
from .base_agent import BaseAgent


class GeneralInquiryAgent(BaseAgent):
    """Agent for handling general customer inquiries."""
    
    def __init__(self, openai_api_key: str):
        """Initialize the general inquiry agent."""
        super().__init__(
            name="General Inquiry Agent",
            description="Handles general customer questions and inquiries"
        )
        self.llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-3.5-turbo",
            openai_api_key=openai_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful customer service agent. 
            Answer the customer's question in a friendly and professional manner.
            If you don't know the answer, politely say so and offer to help in other ways."""),
            ("user", "{query}")
        ])
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
    
    def process(self, query: str, context: Dict[str, Any]) -> str:
        """Process a general inquiry."""
        response = self.chain.run(query=query)
        return response
    
    def can_handle(self, query: str) -> bool:
        """This agent can handle any general query."""
        return True
