# agents/market_landscape.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from rag.knowledge_manager import get_knowledge_manager
from typing import Dict, Optional


class MarketLandscapeAgent(CampaignMindAgent):
    """
    Analyzes competitive landscape and positioning opportunities using RAG.
    """
    
    def __init__(self):
        super().__init__("market_landscape")
        self.knowledge_manager = get_knowledge_manager()
    
    async def analyze_landscape(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5
    ) -> str:
        """
        Analyze market landscape and competitive positioning.
        
        Args:
            brief_context: Dict with campaign details
            filters: Optional metadata filters
            n_results: Number of research documents to retrieve
            
        Returns:
            Interactive markdown market analysis
        """
        # Build query
        query_parts = [
            brief_context.get('industry', ''),
            brief_context.get('audience', ''),
            brief_context.get('geography', ''),
            'market research competitive landscape',
        ]
        query = ' '.join([p for p in query_parts if p]).strip()
        
        # Retrieve market research
        market_results = self.knowledge_manager.query(
            query_text=query,
            doc_type="market_research",
            filters=filters,
            n_results=n_results
        )
        
        # Retrieve adjacent evidence for competitor/product/strategy details
        case_results = self.knowledge_manager.query(
            query_text=query,
            doc_type="case_studies",
            filters=filters,
            n_results=max(3, n_results // 2)
        )
        trend_results = self.knowledge_manager.query(
            query_text=query,
            doc_type="trends",
            filters=filters,
            n_results=max(3, n_results // 2)
        )
        
        # Format for agent
        context_market = self._format_rag_results(market_results, "Market Research")
        context_cases = self._format_rag_results(case_results, "Case Studies")
        context_trends = self._format_rag_results(trend_results, "Trend Evidence")
        
        prompt = f"""Analyze the competitive landscape for this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

RETRIEVED MARKET RESEARCH:
{context_market}

RELEVANT COMPETITOR CASES:
{context_cases}

RELEVANT TREND SIGNALS:
{context_trends}

Provide your analysis using the interactive markdown structure specified in your system message.
Focus on concise, source-backed competitive insights plus concrete implications for brief improvement.
Prioritize:
1) competitor examples,
2) product feature patterns,
3) digital strategy patterns."""

        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken()
        )
        
        return response.chat_message.content
    
    def _format_brief_context(self, context: Dict[str, str]) -> str:
        """Format brief context."""
        lines = []
        for key, value in context.items():
            if value:
                lines.append(f"- {key.title()}: {value}")
        return '\n'.join(lines) if lines else "No context provided"
    
    def _format_rag_results(self, results: list, section_name: str) -> str:
        """Format RAG results."""
        if not results:
            return f"No relevant {section_name.lower()} found in knowledge base."
        
        formatted = [f"[{section_name}]"]
        for i, result in enumerate(results, 1):
            formatted.append(
                f"\n--- Evidence {i} ---\n"
                f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                f"Brand: {result['metadata'].get('brand', 'N/A')}\n"
                f"Industry: {result['metadata'].get('industry', 'N/A')}\n"
                f"Geography: {result['metadata'].get('geography', 'N/A')}\n"
                f"Audience: {result['metadata'].get('audience', 'N/A')}\n"
                f"Content:\n{result['content']}\n"
            )
        
        return '\n'.join(formatted)


# Convenience function
async def analyze_landscape(brief_context: Dict[str, str]) -> str:
    """Quick function to analyze landscape."""
    agent = MarketLandscapeAgent()
    return await agent.analyze_landscape(brief_context)
