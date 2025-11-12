"""
Dependency injection for services and clients.

Provides factory functions to create and configure service instances.
"""
import os
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


def _configure_bedrock_credentials():
    """
    Configure Bedrock credentials based on settings.
    Sets environment variables for bearer token if provided.
    """
    # If bearer token is provided, set it as environment variable
    # Boto3/ChatBedrock will automatically use AWS_BEARER_TOKEN_BEDROCK if set
    if settings.aws_bearer_token_bedrock:
        os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.aws_bearer_token_bedrock
        logger.debug("Using AWS Bedrock bearer token for authentication")
    elif settings.aws_access_key_id and settings.aws_secret_access_key:
        # Use traditional AWS credentials
        os.environ["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
        os.environ["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
        if settings.aws_session_token:
            os.environ["AWS_SESSION_TOKEN"] = settings.aws_session_token
        logger.debug("Using AWS access key credentials for authentication")
    else:
        # Will use default credential chain (IAM role, profile, etc.)
        logger.debug("Using default AWS credential chain")


@lru_cache()
def get_openai_client() -> ChatOpenAI:
    """
    Get or create OpenAI client.

    Returns:
        ChatOpenAI client instance
    
    Raises:
        ValueError: If OpenAI API key is not configured
    """
    if not settings.openai_api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
            "or enable USE_BEDROCK_FOR_SERVICES=true to use AWS Bedrock instead."
        )
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        openai_api_key=settings.openai_api_key,
    )


@lru_cache()
def get_bedrock_client() -> ChatBedrock:
    """
    Get or create Bedrock client for routing.

    Returns:
        ChatBedrock client instance
    """
    _configure_bedrock_credentials()
    return ChatBedrock(
        model_id=settings.bedrock_model_id,
        region_name=settings.aws_region,
        credentials_profile_name=None,
    )


@lru_cache()
def get_bedrock_service_client() -> ChatBedrock:
    """
    Get or create Bedrock client for services (uses Sonnet for better quality).

    Returns:
        ChatBedrock client instance
    """
    _configure_bedrock_credentials()
    return ChatBedrock(
        model_id=settings.bedrock_service_model_id,
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
    
    # Use Bedrock if configured, otherwise try OpenAI
    if settings.use_bedrock_for_services or not settings.openai_api_key:
        llm = get_bedrock_service_client()
    else:
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
