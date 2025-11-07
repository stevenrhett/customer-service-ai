"""
Orchestrator Chain - LangGraph composition that routes queries to services.

This builds a LangGraph graph that:
1. Routes queries using RouterService
2. Calls appropriate service (BillingService, TechnicalService, PolicyService)
"""
from typing import Annotated, List, TypedDict

from app.services.billing_service import BillingService
from app.services.policy_service import PolicyService
from app.services.router_service import RouterService
from app.services.technical_service import TechnicalService
from app.utils.logging import get_logger
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, StateGraph

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State structure for the agent graph."""

    messages: Annotated[List[BaseMessage], "The conversation messages"]
    next_agent: Annotated[str, "Which agent to route to next"]
    current_agent: Annotated[str, "Current agent handling the request"]
    session_id: Annotated[str, "Session identifier"]


class OrchestratorChain:
    """
    LangGraph orchestrator that routes queries to specialized services.
    """

    def __init__(
        self,
        router_service: RouterService,
        billing_service: BillingService,
        technical_service: TechnicalService,
        policy_service: PolicyService,
    ):
        """
        Initialize orchestrator with services.

        Args:
            router_service: Service for intent classification
            billing_service: Service for billing queries
            technical_service: Service for technical queries
            policy_service: Service for policy queries
        """
        self.router_service = router_service
        self.billing_service = billing_service
        self.technical_service = technical_service
        self.policy_service = policy_service

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
                "end": END,
            },
        )

        # All specialized services end after processing
        workflow.add_edge("billing", END)
        workflow.add_edge("technical", END)
        workflow.add_edge("policy", END)

        return workflow.compile()

    async def _route_query(self, state: AgentState) -> AgentState:
        """
        Analyze the query and determine which service should handle it.
        """
        last_message = state["messages"][-1]
        query = last_message.content

        try:
            intent = await self.router_service.classify_intent(query)
            state["next_agent"] = intent
            state["current_agent"] = "orchestrator"
        except Exception as e:
            logger.error(f"Error in routing: {e}", exc_info=True)
            # Default to technical on routing error
            state["next_agent"] = "technical"
            state["current_agent"] = "orchestrator"

        return state

    def _determine_next_agent(self, state: AgentState) -> str:
        """Determine which node to visit next based on routing decision."""
        return state.get("next_agent", "end")

    async def _handle_billing(self, state: AgentState) -> AgentState:
        """Handle billing queries using BillingService."""
        try:
            query = state["messages"][-1].content
            session_id = state["session_id"]
            history = state["messages"][:-1]

            response_content = await self.billing_service.process_query(
                query, session_id, history
            )

            state["messages"].append(AIMessage(content=response_content))
            state["current_agent"] = "billing"
        except Exception as e:
            logger.error(f"Error in billing service: {e}", exc_info=True)
            error_msg = "I apologize, but I encountered an error processing your billing question. Please try rephrasing your question."
            state["messages"].append(AIMessage(content=error_msg))
            state["current_agent"] = "billing"
        return state

    async def _handle_technical(self, state: AgentState) -> AgentState:
        """Handle technical queries using TechnicalService."""
        try:
            query = state["messages"][-1].content
            session_id = state["session_id"]
            history = state["messages"][:-1]

            response_content = await self.technical_service.process_query(
                query, session_id, history
            )

            state["messages"].append(AIMessage(content=response_content))
            state["current_agent"] = "technical"
        except Exception as e:
            logger.error(f"Error in technical service: {e}", exc_info=True)
            error_msg = "I apologize, but I encountered an error processing your technical question. Please try rephrasing your question."
            state["messages"].append(AIMessage(content=error_msg))
            state["current_agent"] = "technical"
        return state

    async def _handle_policy(self, state: AgentState) -> AgentState:
        """Handle policy queries using PolicyService."""
        try:
            query = state["messages"][-1].content
            session_id = state["session_id"]
            history = state["messages"][:-1]

            response_content = await self.policy_service.process_query(
                query, session_id, history
            )

            state["messages"].append(AIMessage(content=response_content))
            state["current_agent"] = "policy"
        except Exception as e:
            logger.error(f"Error in policy service: {e}", exc_info=True)
            error_msg = "I apologize, but I encountered an error processing your policy question. Please try rephrasing your question."
            state["messages"].append(AIMessage(content=error_msg))
            state["current_agent"] = "policy"
        return state

    async def process_query(
        self, message: str, session_id: str, history: List[BaseMessage] = None
    ) -> dict:
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
            session_id=session_id,
        )

        # Run the graph
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
            "state": result,
        }

    async def stream_query(
        self, message: str, session_id: str, history: List[BaseMessage] = None
    ):
        """
        Stream a user query through the orchestration system.

        Args:
            message: The user's message
            session_id: Session identifier
            history: Previous conversation messages

        Yields:
            Dict with agent_used and response chunks
        """
        # First, route to determine which service to use
        initial_messages = history or []
        initial_messages.append(HumanMessage(content=message))

        routing_state = AgentState(
            messages=initial_messages,
            next_agent="",
            current_agent="orchestrator",
            session_id=session_id,
        )

        # Route to determine service
        routing_result = await self._route_query(routing_state)
        agent_name = routing_result.get("next_agent", "technical")

        # Stream from the appropriate service
        query = message
        agent_history = history or []

        try:
            if agent_name == "billing":
                async for chunk in self.billing_service.stream_query(
                    query, session_id, agent_history
                ):
                    yield {"agent_used": "billing", "content": chunk, "is_final": False}
            elif agent_name == "technical":
                async for chunk in self.technical_service.stream_query(
                    query, session_id, agent_history
                ):
                    yield {
                        "agent_used": "technical",
                        "content": chunk,
                        "is_final": False,
                    }
            elif agent_name == "policy":
                async for chunk in self.policy_service.stream_query(
                    query, session_id, agent_history
                ):
                    yield {"agent_used": "policy", "content": chunk, "is_final": False}
        except Exception as e:
            logger.error(f"Error streaming query: {e}", exc_info=True)
            error_msg = "I apologize, but I encountered an error. Please try again."
            yield {"agent_used": agent_name, "content": error_msg, "is_final": False}

        # Send final chunk
        yield {"agent_used": agent_name, "content": "", "is_final": True}
