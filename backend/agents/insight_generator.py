# agents/insight_generator.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from typing import Dict


class InsightGeneratorAgent(CampaignMindAgent):
    """
    Synthesizes outputs from all specialist agents into strategic insights.
    """
    
    def __init__(self):
        super().__init__("insight_generator")
    
    async def generate_insights(
        self,
        brief_analysis: str,
        trend_analysis: str,
        case_analysis: str,
        landscape_analysis: str,
        original_brief: str
    ) -> str:
        """
        Synthesize all agent outputs into final strategic insights.
        
        Args:
            brief_analysis: Output from Brief Analyzer
            trend_analysis: Output from Trend Agent
            case_analysis: Output from Case Intelligence
            landscape_analysis: Output from Market Landscape
            original_brief: The original campaign brief
            
        Returns:
            Final enhanced brief in Markdown format
        """
        prompt = f"""Synthesize these analyses into a strategic brief enhancement:

ORIGINAL BRIEF:
{original_brief}

BRIEF ANALYSIS:
{brief_analysis}

TREND ANALYSIS:
{trend_analysis}

CASE STUDY ANALYSIS:
{case_analysis}

MARKET LANDSCAPE:
{landscape_analysis}

Generate a comprehensive brief enhancement in Markdown format as specified in your system message.
Resolve any contradictions between sources and prioritize insights by impact."""

        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken()
        )
        
        return response.chat_message.content


# Convenience function
async def generate_insights(
    brief_analysis: str,
    trend_analysis: str,
    case_analysis: str,
    landscape_analysis: str,
    original_brief: str
) -> str:
    """Quick function to generate insights."""
    agent = InsightGeneratorAgent()
    return await agent.generate_insights(
        brief_analysis,
        trend_analysis,
        case_analysis,
        landscape_analysis,
        original_brief
    )