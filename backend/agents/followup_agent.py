# agents/followup_agent.py
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from typing import List, Dict


FOLLOWUP_SYSTEM_MSG = """You are CampaignMind AI, a marketing strategy assistant.
You previously helped the user enhance a marketing campaign brief using multi-agent analysis.
Now you are continuing that conversation with follow-up questions and refinements.

Context: The user's original brief was enhanced with:
- Brief gap analysis (completeness score, missing elements)
- Trend analysis (market momentum, relevance scores)
- Case intelligence (competitor campaigns, analogous cases)
- Market landscape (saturation, positioning whitespace)

Guidelines:
- Answer follow-up questions about the brief, recommendations, or strategy
- If asked to refine a specific section, provide updated Markdown
- Reference the relevant analysis sections when answering (Trends, Cases, Landscape, etc.)
- Be concise and actionable — avoid repeating the full brief unless asked
- Use Markdown formatting (headers, bullets, bold) for clarity
- If asked something outside the brief scope, redirect politely to the campaign context"""


class FollowUpAgent(CampaignMindAgent):
    """
    Lightweight agent for follow-up chat turns after the initial brief analysis.
    Uses conversation history as context — no RAG, no orchestration overhead.
    """

    def __init__(self):
        super().__init__("insight_generator")

    async def chat(self, message: str, history: List[Dict]) -> str:
        """
        Generate a follow-up response given the conversation history.

        Args:
            message: The new user message
            history: List of {'role': 'user'|'assistant', 'content': str} dicts
                     Should include all previous messages including the current one
                     (the current message will be in the prompt separately)

        Returns:
            Markdown-formatted assistant response
        """
        # Build history context (exclude the last entry which is the current user message)
        prior_messages = history[:-1] if history else []

        if prior_messages:
            history_text = "\n\n".join([
                f"{'USER' if m['role'] == 'user' else 'ASSISTANT'}: {m['content']}"
                for m in prior_messages
            ])
            context_section = f"""CONVERSATION HISTORY (most recent last):
{history_text}

---"""
        else:
            context_section = "CONVERSATION HISTORY: (no prior messages)"

        prompt = f"""{FOLLOWUP_SYSTEM_MSG}

{context_section}

NEW USER MESSAGE:
{message}

Respond as CampaignMind AI. Reference the conversation context as needed. Use Markdown formatting."""

        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken(),
        )

        return response.chat_message.content
