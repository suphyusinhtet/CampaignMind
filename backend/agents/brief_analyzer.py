# agents/brief_analyzer.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import PathfinderAgent


class BriefAnalyzerAgent(PathfinderAgent):
    """
    Analyzes campaign briefs to identify gaps, vague language, and contradictions.
    """
    
    def __init__(self):
        super().__init__("brief_analyzer")
    
    async def analyze_brief(self, brief_text: str) -> str:
        """
        Analyze a campaign brief and return enhancement recommendations.
        
        Args:
            brief_text: The raw campaign brief text
            
        Returns:
            Analysis with gaps, vague elements, contradictions, and enhancement plan
        """
        prompt = f"""Analyze this campaign brief and identify what's missing or unclear:

{brief_text}

Return your analysis in clear JSON format as specified in your system message."""

        # Run the agent
        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken()
        )
        
        # Extract the chat message content
        return response.chat_message.content


# Convenience function for quick testing
async def analyze_brief(brief_text: str) -> str:
    """Quick function to analyze a brief without instantiating the class."""
    analyzer = BriefAnalyzerAgent()
    return await analyzer.analyze_brief(brief_text)