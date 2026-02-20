# agents/trend_agent.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import PathfinderAgent
from rag.knowledge_manager import get_knowledge_manager
from typing import Dict, Optional


class TrendAgent(PathfinderAgent):
    """
    Retrieves and analyzes market trends relevant to the campaign using RAG.
    """
    
    def __init__(self):
        super().__init__("trend_agent")
        self.knowledge_manager = get_knowledge_manager()
    
    async def analyze_trends(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5
    ) -> str:
        """
        Analyze trends relevant to the campaign brief.
        
        Args:
            brief_context: Dict with keys like 'objective', 'industry', 'audience', 'geography'
            filters: Optional metadata filters for RAG query (e.g., {"industry": "tech"})
            n_results: Number of trend documents to retrieve
            
        Returns:
            JSON-formatted trend analysis with sources
        """
        # Build query from brief context
        query_parts = [
            brief_context.get('objective', ''),
            brief_context.get('industry', ''),
            brief_context.get('audience', ''),
            brief_context.get('product', ''),
        ]
        query = ' '.join([p for p in query_parts if p]).strip()
        
        if not query:
            query = "marketing trends"
        
        # Retrieve relevant trends from RAG
        trend_results = self.knowledge_manager.query(
            query_text=query,
            doc_type="trends",
            filters=filters,
            n_results=n_results
        )
        
        # Format retrieved trends for the agent
        context = self._format_rag_results(trend_results)
        
        # Create prompt with RAG context
        prompt = f"""Analyze these trends and identify which are most relevant to this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

RETRIEVED TRENDS:
{context}

Analyze the relevance of each trend and provide your assessment in JSON format as specified in your system message.
Include only trends that are genuinely relevant and actionable."""

        # Run the agent
        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken()
        )
        
        return response.chat_message.content
    
    def _format_brief_context(self, context: Dict[str, str]) -> str:
        """Format brief context for the prompt."""
        lines = []
        for key, value in context.items():
            if value:
                lines.append(f"- {key.title()}: {value}")
        return '\n'.join(lines) if lines else "No context provided"
    
    def _format_rag_results(self, results: list) -> str:
        """Format RAG results for the agent prompt."""
        if not results:
            return "No relevant trends found in knowledge base."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"\n--- Trend {i} ---\n"
                f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                f"Industry: {result['metadata'].get('industry', 'N/A')}\n"
                f"Date: {result['metadata'].get('date', 'N/A')}\n"
                f"Content:\n{result['content']}\n"
            )
        
        return '\n'.join(formatted)


# Convenience function for quick testing
async def analyze_trends(brief_context: Dict[str, str]) -> str:
    """Quick function to analyze trends without instantiating the class."""
    agent = TrendAgent()
    return await agent.analyze_trends(brief_context)