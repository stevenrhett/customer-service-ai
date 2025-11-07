"""
Billing Agent - Pure model adapter for billing queries.

This is a pure adapter that provides prompt templates.
Business logic is handled by BillingService.
"""


class BillingAgent:
    """
    Pure adapter for billing agent prompts.
    Contains only prompt templates and formatting logic.
    """

    def _get_system_prompt(self, context: str) -> str:
        """
        Get system prompt for billing queries.

        Args:
            context: Retrieved context from vector store

        Returns:
            Formatted system prompt
        """
        return """You are a helpful billing support agent.
        Use the following billing documentation to answer the customer's question.

        Guidelines:
        - Provide clear, accurate pricing information
        - Explain billing cycles and payment methods
        - Help with invoice questions
        - Be transparent about costs and fees

        Billing Documentation:
{context}""".format(
            context=context
        )
