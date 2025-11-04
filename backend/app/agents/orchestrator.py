"""
Orchestrator Agent - The supervisor that routes queries to specialized agents.

This agent analyzes incoming user queries and determines which specialized
agent should handle the request (Billing, Technical, or Policy).
"""
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from app.config import get_settings

settings = get_settings()


class AgentState(TypedDict):
    """State structure for the agent graph."""
    messages: Annotated[List[BaseMessage], "The conversation messages"]
    next_agent: Annotated[str, "Which agent to route to next"]
    current_agent: Annotated[str, "Current agent handling the request"]
    session_id: Annotated[str, "Session identifier"]


class OrchestratorAgent:
    """
    The main orchestrator that routes queries to specialized agents.
    Uses AWS Bedrock (Claude Haiku) for fast, cost-effective routing decisions.
    """
    
    def __init__(self):
        """Initialize the orchestrator with routing LLM."""
        # Use AWS Bedrock Claude Haiku for fast routing
        self.routing_llm = ChatBedrock(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            region_name=settings.aws_region,
            credentials_profile_name=None,  # Uses environment variables
        )
        
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for orchestration."""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("route", self._route_query)
        workflow.add_node("billing", self._handle_billing)
        workflow.add_node("technical", self._handle_technical)
        workflow.add_node("policy", self._handle_policy)
        
        # Set entry point
        workflow.set_entry_point("route")
        
        # Add conditional edges from router
        workflow.add_conditional_edges(
            "route",
            self._determine_next_agent,
            {
                "billing": "billing",
                "technical": "technical",
                "policy": "policy",
                "end": END
            }
        )
        
        # All specialized agents end after processing
        workflow.add_edge("billing", END)
        workflow.add_edge("technical", END)
        workflow.add_edge("policy", END)
        
        return workflow.compile()
    
    def _route_query(self, state: AgentState) -> AgentState:
        """
        Analyze the query and determine which specialized agent should handle it.
        """
        last_message = state["messages"][-1]
        
        routing_prompt = f"""You are a routing assistant for a customer service system. 
        Analyze the following customer query and determine which department should handle it.
        
        Departments:
        - billing: Questions about pricing, invoices, payments, refunds, billing cycles
        - technical: Questions about product features, bugs, troubleshooting, how-to questions
        - policy: Questions about terms of service, privacy policy, legal compliance, account policies
        
        Customer Query: {last_message.content}
        
        Respond with ONLY one word: billing, technical, or policy"""
        
        response = self.routing_llm.invoke([HumanMessage(content=routing_prompt)])
        next_agent = response.content.strip().lower()
        
        # Validate response
        if next_agent not in ["billing", "technical", "policy"]:
            next_agent = "technical"  # Default fallback
        
        state["next_agent"] = next_agent
        state["current_agent"] = "orchestrator"
        
        return state
    
    def _determine_next_agent(self, state: AgentState) -> str:
        """Determine which node to visit next based on routing decision."""
        return state.get("next_agent", "end")
    
    def _handle_billing(self, state: AgentState) -> AgentState:
        """Handle billing queries (placeholder for BillingAgent integration)."""
        state["current_agent"] = "billing"
        # TODO: Integrate with BillingAgent
        return state
    
    def _handle_technical(self, state: AgentState) -> AgentState:
        """Handle technical queries (placeholder for TechnicalAgent integration)."""
        state["current_agent"] = "technical"
        # TODO: Integrate with TechnicalAgent
        return state
    
    def _handle_policy(self, state: AgentState) -> AgentState:
        """Handle policy queries (placeholder for PolicyAgent integration)."""
        state["current_agent"] = "policy"
        # TODO: Integrate with PolicyAgent
        return state
    
    async def process_query(self, message: str, session_id: str, history: List[BaseMessage] = None) -> dict:
        """
        Process a user query through the orchestration system.
        
        Args:
            message: The user's message
            session_id: Session identifier
            history: Previous conversation messages
            
        Returns:
            dict with response and metadata
        """
        # Initialize state
        messages = history or []
        messages.append(HumanMessage(content=message))
        
        initial_state = AgentState(
            messages=messages,
            next_agent="",
            current_agent="orchestrator",
            session_id=session_id
        )
        
        # Run the graph
        result = self.graph.invoke(initial_state)
        
        return {
            "agent_used": result.get("current_agent", "unknown"),
            "session_id": session_id,
            "state": result
        }
