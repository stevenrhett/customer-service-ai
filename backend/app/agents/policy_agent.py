"""
Policy Agent - Pure model adapter for policy queries.

This is a pure adapter that provides prompt templates.
Business logic is handled by PolicyService.
"""


class PolicyAgent:
    """
    Pure adapter for policy agent prompts.
    Contains only prompt templates and formatting logic.
    """

    def _get_system_prompt(self, context: str) -> str:
        """
        Get system prompt for policy queries.

        Args:
            context: Pre-loaded policy context

        Returns:
            Formatted system prompt
        """
        return """You are a policy and compliance support agent.
Use the following policy documents to answer the customer's question.

Guidelines:
- Provide accurate information based on the policies
- Quote specific sections when relevant
- Be clear and professional
- If information isn't in the policies, say so clearly
- For legal questions, remind users to consult legal counsel for specific advice

Policy Documents:
{context}""".format(
            context=context
        )
