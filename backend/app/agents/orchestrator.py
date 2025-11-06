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
from app.agents.billing_agent import BillingAgent
from app.agents.technical_agent import TechnicalAgent
from app.agents.policy_agent import PolicyAgent
from app.services.vector_store import vector_store_service
from app.utils.exceptions import AgentError, VectorStoreError

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
        """Initialize the orchestrator with routing LLM and specialized agents."""
        # Use AWS Bedrock Claude Haiku for fast routing
        self.routing_llm = ChatBedrock(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            region_name=settings.aws_region,
            credentials_profile_name=None,  # Uses environment variables
        )
        
        # Initialize specialized agents with vector stores
        billing_store = vector_store_service.get_billing_store()
        technical_store = vector_store_service.get_technical_store()
        
        self.billing_agent = BillingAgent(vector_store=billing_store)
        self.technical_agent = TechnicalAgent(vector_store=technical_store)
        self.policy_agent = PolicyAgent()
        
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
    
    async def _route_query(self, state: AgentState) -> AgentState:
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
        
        response = await self.routing_llm.ainvoke([HumanMessage(content=routing_prompt)])
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
    
    async def _handle_billing(self, state: AgentState) -> AgentState:
        """Handle billing queries using BillingAgent."""
        try:
            query = state["messages"][-1].content
            session_id = state["session_id"]
            history = state["messages"][:-1]  # All messages except the last one
            
            # Process query with billing agent (await async call)
            response_content = await self.billing_agent.process_query(
                query, session_id, history
            )
            
            # Add response to messages
            state["messages"].append(AIMessage(content=response_content))
            state["current_agent"] = "billing"
        except Exception as e:
            # Fallback response on error
            error_msg = f"I apologize, but I encountered an error processing your billing question. Please try rephrasing your question."
            state["messages"].append(AIMessage(content=error_msg))
            state["current_agent"] = "billing"
        return state
    
    async def _handle_technical(self, state: AgentState) -> AgentState:
        """Handle technical queries using TechnicalAgent."""
        try:
            if self.technical_agent.retriever is None:
                raise VectorStoreError("Technical vector store not available")
            
            query = state["messages"][-1].content
            session_id = state["session_id"]
            history = state["messages"][:-1]  # All messages except the last one
            
            # Process query with technical agent (await async call)
            response_content = await self.technical_agent.process_query(
                query, session_id, history
            )
            
            # Add response to messages
            state["messages"].append(AIMessage(content=response_content))
            state["current_agent"] = "technical"
        except Exception as e:
            # Fallback response on error
            error_msg = f"I apologize, but I encountered an error processing your technical question. Please try rephrasing your question."
            state["messages"].append(AIMessage(content=error_msg))
            state["current_agent"] = "technical"
        return state
    
    async def _handle_policy(self, state: AgentState) -> AgentState:
        """Handle policy queries using PolicyAgent."""
        try:
            query = state["messages"][-1].content
            session_id = state["session_id"]
            history = state["messages"][:-1]  # All messages except the last one
            
            # Process query with policy agent (await async call)
            response_content = await self.policy_agent.process_query(
                query, session_id, history
            )
            
            # Add response to messages
            state["messages"].append(AIMessage(content=response_content))
            state["current_agent"] = "policy"
        except Exception as e:
            # Fallback response on error
            error_msg = f"I apologize, but I encountered an error processing your policy question. Please try rephrasing your question."
            state["messages"].append(AIMessage(content=error_msg))
            state["current_agent"] = "policy"
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
        
        # Run the graph (use ainvoke for async support)
        result = await self.graph.ainvoke(initial_state)
        
        # Extract the response from the last message
        response_content = ""
        if result.get("messages"):
            last_message = result["messages"][-1]
            if isinstance(last_message, AIMessage):
                response_content = last_message.content
        
        return {
            "agent_used": result.get("current_agent", "unknown"),
            "session_id": session_id,
            "response": response_content,
            "state": result
        }
    
    async def stream_query(self, message: str, session_id: str, history: List[BaseMessage] = None):
        """
        Stream a user query through the orchestration system.
        
        Args:
            message: The user's message
            session_id: Session identifier
            history: Previous conversation messages
            
        Yields:
            Dict with agent_used and response chunks
        """
        # First, route to determine which agent to use
        initial_messages = history or []
        initial_messages.append(HumanMessage(content=message))
        
        routing_state = AgentState(
            messages=initial_messages,
            next_agent="",
            current_agent="orchestrator",
            session_id=session_id
        )
        
        # Route to determine agent
        routing_result = await self._route_query(routing_state)
        agent_name = routing_result.get("next_agent", "technical")
        
        # Stream from the appropriate agent
        query = message
        agent_history = history or []
        
        try:
            if agent_name == "billing":
                async for chunk in self.billing_agent.stream_query(query, session_id, agent_history):
                    yield {
                        "agent_used": "billing",
                        "content": chunk,
                        "is_final": False
                    }
            elif agent_name == "technical":
                async for chunk in self.technical_agent.stream_query(query, session_id, agent_history):
                    yield {
                        "agent_used": "technical",
                        "content": chunk,
                        "is_final": False
                    }
            elif agent_name == "policy":
                async for chunk in self.policy_agent.stream_query(query, session_id, agent_history):
                    yield {
                        "agent_used": "policy",
                        "content": chunk,
                        "is_final": False
                    }
        except Exception as e:
            # Fallback error message
            error_msg = f"I apologize, but I encountered an error. Please try again."
            yield {
                "agent_used": agent_name,
                "content": error_msg,
                "is_final": False
            }
        
        # Send final chunk
        yield {
            "agent_used": agent_name,
            "content": "",
            "is_final": True
        }