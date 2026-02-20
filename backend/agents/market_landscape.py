# agents/market_landscape.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import PathfinderAgent
from rag.knowledge_manager import get_knowledge_manager
from typing import Dict, Optional


class MarketLandscapeAgent(PathfinderAgent):
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
            JSON-formatted market analysis
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
        research_results = self.knowledge_manager.query(
            query_text=query,
            doc_type="market_research",
            filters=filters,
            n_results=n_results
        )
        
        # Format for agent
        context = self._format_rag_results(research_results)
        
        prompt = f"""Analyze the competitive landscape for this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

RETRIEVED MARKET RESEARCH:
{context}

Provide your analysis in JSON format as specified in your system message.
Focus on identifying positioning opportunities and whitespace."""

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
    
    def _format_rag_results(self, results: list) -> str:
        """Format RAG results."""
        if not results:
            return "No relevant market research found in knowledge base."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"\n--- Research {i} ---\n"
                f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                f"Industry: {result['metadata'].get('industry', 'N/A')}\n"
                f"Audience: {result['metadata'].get('audience', 'N/A')}\n"
                f"Content:\n{result['content']}\n"
            )
        
        return '\n'.join(formatted)


# Convenience function
async def analyze_landscape(brief_context: Dict[str, str]) -> str:
    """Quick function to analyze landscape."""
    agent = MarketLandscapeAgent()
    return await agent.analyze_landscape(brief_context)