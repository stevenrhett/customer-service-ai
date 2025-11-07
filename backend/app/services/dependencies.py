"""
Dependency injection for services and clients.

Provides factory functions to create and configure service instances.
"""
from functools import lru_cache

from app.agents.billing_agent import BillingAgent
from app.agents.policy_agent import PolicyAgent
from app.agents.technical_agent import TechnicalAgent
from app.chains.orchestrator import OrchestratorChain
from app.config import get_settings
from app.services.billing_service import BillingService
from app.services.policy_service import PolicyService
from app.services.router_service import RouterService
from app.services.technical_service import TechnicalService
from app.utils.chroma_loader import load_chroma_store
from app.utils.logging import get_logger
from langchain_aws import ChatBedrock
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)
settings = get_settings()


@lru_cache()
def get_openai_client() -> ChatOpenAI:
    """
    Get or create OpenAI client.

    Returns:
        ChatOpenAI client instance
    """
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        openai_api_key=settings.openai_api_key,
    )


@lru_cache()
def get_bedrock_client() -> ChatBedrock:
    """
    Get or create Bedrock client.

    Returns:
        ChatBedrock client instance
    """
    return ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        credentials_profile_name=None,
    )


@lru_cache()
def get_router_service() -> RouterService:
    """
    Get or create router service.

    Returns:
        RouterService instance
    """
    bedrock_client = get_bedrock_client()
    return RouterService(bedrock_client=bedrock_client)


@lru_cache()
def get_billing_service() -> BillingService:
    """
    Get or create billing service.

    Returns:
        BillingService instance
    """
    vector_store = load_chroma_store("billing")
    llm = get_openai_client()
    agent = BillingAgent()
    return BillingService(vector_store=vector_store, llm=llm, agent=agent)


@lru_cache()
def get_technical_service() -> TechnicalService:
    """
    Get or create technical service.

    Returns:
        TechnicalService instance
    """
    vector_store = load_chroma_store("technical")
    llm = get_openai_client()
    agent = TechnicalAgent()
    return TechnicalService(vector_store=vector_store, llm=llm, agent=agent)


@lru_cache()
def get_policy_service() -> PolicyService:
    """
    Get or create policy service.

    Returns:
        PolicyService instance
    """
    llm = get_openai_client()
    agent = PolicyAgent()
    return PolicyService(llm=llm, agent=agent)


@lru_cache()
def get_orchestrator_chain() -> OrchestratorChain:
    """
    Get or create orchestrator chain.

    Returns:
        OrchestratorChain instance
    """
    router_service = get_router_service()
    billing_service = get_billing_service()
    technical_service = get_technical_service()
    policy_service = get_policy_service()

    return OrchestratorChain(
        router_service=router_service,
        billing_service=billing_service,
        technical_service=technical_service,
        policy_service=policy_service,
    )
