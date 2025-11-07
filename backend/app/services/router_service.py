"""
Router Service - Intent classification using AWS Bedrock (Claude Haiku).

This service classifies user queries into one of three categories:
- billing: Pricing, invoices, payments, refunds
- technical: Product features, bugs, troubleshooting
- policy: Terms of service, privacy policy, legal compliance
"""
from typing import Literal

from app.config import get_settings
from app.utils.exceptions import LLMError
from app.utils.logging import get_logger
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage

logger = get_logger(__name__)
settings = get_settings()


class RouterService:
    """
    Service for routing queries to appropriate specialized services.
    Uses AWS Bedrock Claude Haiku for fast, cost-effective intent classification.
    """

    def __init__(self, bedrock_client: ChatBedrock = None):
        """
        Initialize router service.

        Args:
            bedrock_client: Optional pre-configured Bedrock client
        """
        self.bedrock_client = bedrock_client or self._create_bedrock_client()

    def _create_bedrock_client(self) -> ChatBedrock:
        """Create Bedrock client from settings."""
        try:
            return ChatBedrock(
                model_id=settings.bedrock_model_id,
                region_name=settings.aws_region,
                credentials_profile_name=None,  # Uses environment variables
            )
        except Exception as e:
            logger.error(f"Failed to create Bedrock client: {e}")
            raise LLMError(
                f"Failed to initialize Bedrock client: {str(e)}", provider="bedrock"
            )

    async def classify_intent(
        self, query: str
    ) -> Literal["billing", "technical", "policy"]:
        """
        Classify user query intent.

        Args:
            query: User's message

        Returns:
            Intent classification: "billing", "technical", or "policy"

        Raises:
            LLMError: If classification fails
        """
        routing_prompt = """You are a routing assistant for a customer service system.
Analyze the following customer query and determine which department should handle it.

Departments:
- billing: Questions about pricing, invoices, payments, refunds, billing cycles
- technical: Questions about product features, bugs, troubleshooting, how-to questions
- policy: Questions about terms of service, privacy policy, legal compliance, account policies

Customer Query: {query}

Respond with ONLY one word: billing, technical, or policy"""

        try:
            response = await self.bedrock_client.ainvoke(
                [HumanMessage(content=routing_prompt.format(query=query))]
            )
            intent = response.content.strip().lower()

            # Validate response
            if intent not in ["billing", "technical", "policy"]:
                logger.warning(
                    f"Invalid intent classification: {intent}, defaulting to technical"
                )
                return "technical"

            logger.debug(f"Classified query as: {intent}")
            return intent

        except Exception as e:
            logger.error(f"Error classifying intent: {e}", exc_info=True)
            raise LLMError(
                f"Failed to classify query intent: {str(e)}", provider="bedrock"
            )
