# agents/case_intelligence.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from rag.knowledge_manager import get_knowledge_manager
from typing import Dict, Optional


class CaseIntelligenceAgent(CampaignMindAgent):
    """
    Analyzes competitor campaigns and case studies using RAG.
    """
    
    def __init__(self):
        super().__init__("case_intelligence")
        self.knowledge_manager = get_knowledge_manager()
    
    async def analyze_cases(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5
    ) -> str:
        """
        Analyze relevant case studies and competitor campaigns.
        
        Args:
            brief_context: Dict with campaign details
            filters: Optional metadata filters (e.g., {"industry": "sportswear"})
            n_results: Number of case studies to retrieve
            
        Returns:
            Interactive markdown case analysis with learnings
        """
        # Build query
        query_parts = [
            brief_context.get('objective', ''),
            brief_context.get('industry', ''),
            brief_context.get('campaign_type', 'brand awareness'),
            'successful campaign',
        ]
        query = ' '.join([p for p in query_parts if p]).strip()
        
        # Retrieve case studies
        case_results = self.knowledge_manager.query(
            query_text=query,
            doc_type="case_studies",
            filters=filters,
            n_results=n_results
        )
        
        # Format for agent
        context = self._format_rag_results(case_results)
        
        prompt = f"""Analyze these case studies and extract learnings relevant to this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

RETRIEVED CASE STUDIES:
{context}

Provide your analysis using the interactive markdown structure specified in your system message.
Focus on extracting actionable learnings, not just summarizing campaigns."""

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
            return "No relevant case studies found in knowledge base."
        
        formatted = []
        for i, result in enumerate(results, 1):
            formatted.append(
                f"\n--- Case Study {i} ---\n"
                f"Brand: {result['metadata'].get('brand', 'Unknown')}\n"
                f"Source: {result['metadata'].get('source', 'Unknown')}\n"
                f"Industry: {result['metadata'].get('industry', 'N/A')}\n"
                f"Content:\n{result['content']}\n"
            )
        
        return '\n'.join(formatted)


# Convenience function
async def analyze_cases(brief_context: Dict[str, str]) -> str:
    """Quick function to analyze cases."""
    agent = CaseIntelligenceAgent()
    return await agent.analyze_cases(brief_context)
