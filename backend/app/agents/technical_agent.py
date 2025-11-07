"""
Technical Agent - Pure model adapter for technical queries.

This is a pure adapter that provides prompt templates.
Business logic is handled by TechnicalService.
"""


class TechnicalAgent:
    """
    Pure adapter for technical agent prompts.
    Contains only prompt templates and formatting logic.
    """

    def _get_system_prompt(self, context: str) -> str:
        """
        Get system prompt for technical queries.

        Args:
            context: Retrieved context from vector store

        Returns:
            Formatted system prompt
        """
        return """You are a knowledgeable technical support agent.
Use the following technical documentation, bug reports, and forum posts to help the customer.

Guidelines:
- Provide step-by-step troubleshooting when appropriate
- Reference specific error codes or messages if mentioned
- Suggest workarounds for known issues
- Be clear about what is a confirmed bug vs. expected behavior
- Cite which source (by number) you're using if helpful

Technical Knowledge Base:
{context}""".format(
            context=context
        )
