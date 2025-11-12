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
            # Configure credentials (bearer token or access keys)
            import os
            if settings.aws_bearer_token_bedrock:
                os.environ["AWS_BEARER_TOKEN_BEDROCK"] = settings.aws_bearer_token_bedrock
                logger.debug("Using AWS Bedrock bearer token for authentication")
            elif settings.aws_access_key_id and settings.aws_secret_access_key:
                os.environ["AWS_ACCESS_KEY_ID"] = settings.aws_access_key_id
                os.environ["AWS_SECRET_ACCESS_KEY"] = settings.aws_secret_access_key
                if settings.aws_session_token:
                    os.environ["AWS_SESSION_TOKEN"] = settings.aws_session_token
            
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
            error_str = str(e)
            logger.error(f"Error classifying intent: {e}", exc_info=True)
            
            # Check for expired token
            if "ExpiredTokenException" in error_str or "expired" in error_str.lower():
                raise LLMError(
                    "AWS security token has expired. Please refresh your AWS credentials. "
                    "If using SSO, get new credentials from AWS Console. "
                    "Update your .env file with new AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_SESSION_TOKEN.",
                    provider="bedrock",
                    details={"error_type": "ExpiredTokenException", "original_error": error_str}
                )
            
            # Check for access denied
            if "AccessDeniedException" in error_str or "access denied" in error_str.lower():
                raise LLMError(
                    "AWS Bedrock access denied. Please check your AWS credentials and IAM permissions. "
                    "Ensure your AWS account has Bedrock access enabled.",
                    provider="bedrock",
                    details={"error_type": "AccessDeniedException", "original_error": error_str}
                )
            
            raise LLMError(
                f"Failed to classify query intent: {str(e)}", provider="bedrock"
            )
