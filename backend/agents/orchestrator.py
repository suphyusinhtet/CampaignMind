# agents/orchestrator.py
import asyncio
from typing import Dict, List, Optional
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_core import CancellationToken

from agents.brief_analyzer import BriefAnalyzerAgent
from agents.trend_agent import TrendAgent
from agents.case_intelligence import CaseIntelligenceAgent
from agents.market_landscape import MarketLandscapeAgent
from agents.insight_generator import InsightGeneratorAgent
from config.agent_config import get_model_client


class MasterOrchestrator:
    """
    Master Orchestrator that intelligently coordinates all specialist agents.
    Uses Gemini 2.5 Pro for decision-making and team coordination.
    """
    
    def __init__(self):
        # Initialize all specialist agents
        self.brief_analyzer = BriefAnalyzerAgent()
        self.trend_agent = TrendAgent()
        self.case_agent = CaseIntelligenceAgent()
        self.landscape_agent = MarketLandscapeAgent()
        self.insight_agent = InsightGeneratorAgent()
        
        # Get Gemini 2.5 Pro for orchestrator (smarter model)
        self.model_client = get_model_client("gemini-2.5-pro")
    
    async def enhance_brief(
        self,
        brief: str,
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5
    ) -> Dict[str, str]:
        """
        Main orchestration method: analyzes brief and coordinates agents.
        
        Args:
            brief: The marketing campaign brief to enhance
            filters: Optional RAG query filters
            n_results: Number of RAG results per query
            
        Returns:
            Dict with all agent outputs and final insights
        """
        print(f"\n{'='*70}")
        print("MASTER ORCHESTRATOR - STARTING BRIEF ENHANCEMENT")
        print(f"{'='*70}\n")
        
        # Step 1: Analyze the brief to determine what's needed
        print("📋 Step 1: Analyzing brief...")
        brief_analysis = await self.brief_analyzer.analyze_brief(brief)
        
        # Extract enhancement plan from brief analysis
        enhancement_plan = self._parse_enhancement_plan(brief_analysis)
        print(f"   Completeness Score: {enhancement_plan.get('completeness_score', 'N/A')}")
        print(f"   Needs Trend Analysis: {enhancement_plan.get('needs_trend_analysis', True)}")
        print(f"   Needs Case Analysis: {enhancement_plan.get('needs_competitor_analysis', True)}")
        print(f"   Needs Landscape Analysis: {enhancement_plan.get('needs_market_landscape', True)}")
        
        # Extract brief context for RAG queries
        brief_context = self._extract_brief_context(brief)
        
        # Step 2: Coordinate specialist agents based on needs
        results = {
            "brief_analysis": brief_analysis,
            "trend_analysis": None,
            "case_analysis": None,
            "landscape_analysis": None,
            "final_insights": None
        }
        
        # Determine which agents to run
        agents_to_run = self._determine_agents(enhancement_plan)
        print(f"\n🤖 Step 2: Activating {len(agents_to_run)} specialist agents...")
        
        # Run agents in parallel for speed
        tasks = []
        
        if "trend" in agents_to_run:
            print("   - Trend Agent")
            tasks.append(("trend", self.trend_agent.analyze_trends(
                brief_context, filters, n_results
            )))
        
        if "case" in agents_to_run:
            print("   - Case Intelligence Agent")
            tasks.append(("case", self.case_agent.analyze_cases(
                brief_context, filters, n_results
            )))
        
        if "landscape" in agents_to_run:
            print("   - Market Landscape Agent")
            tasks.append(("landscape", self.landscape_agent.analyze_landscape(
                brief_context, filters, n_results
            )))
        
        # Execute agents in parallel
        if tasks:
            print("\n⚡ Running agents in parallel...")
            agent_results = await asyncio.gather(*[task[1] for task in tasks])
            
            # Map results back
            for i, (agent_type, _) in enumerate(tasks):
                if agent_type == "trend":
                    results["trend_analysis"] = agent_results[i]
                elif agent_type == "case":
                    results["case_analysis"] = agent_results[i]
                elif agent_type == "landscape":
                    results["landscape_analysis"] = agent_results[i]
        
        # Step 3: Synthesize insights
        print("\n💡 Step 3: Generating strategic insights...")
        results["final_insights"] = await self.insight_agent.generate_insights(
            brief_analysis=results["brief_analysis"],
            trend_analysis=results["trend_analysis"] or "No trend analysis requested",
            case_analysis=results["case_analysis"] or "No case analysis requested",
            landscape_analysis=results["landscape_analysis"] or "No landscape analysis requested",
            original_brief=brief
        )
        
        print(f"\n{'='*70}")
        print("✅ ORCHESTRATION COMPLETE")
        print(f"{'='*70}\n")
        
        return results
    
    def _parse_enhancement_plan(self, brief_analysis: str) -> Dict:
        """
        Parse the enhancement plan from brief analysis JSON.
        Returns dict with flags for which agents to run.
        """
        import json
        import re
        
        try:
            # Extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(.*?)\s*```', brief_analysis, re.DOTALL)
            if json_match:
                analysis_data = json.loads(json_match.group(1))
            else:
                analysis_data = json.loads(brief_analysis)
            
            enhancement_plan = analysis_data.get('enhancement_plan', {})
            enhancement_plan['completeness_score'] = analysis_data.get('completeness_score', 0)
            return enhancement_plan
        except Exception as e:
            print(f"   Warning: Could not parse enhancement plan: {e}")
            # Default: run all agents
            return {
                'needs_trend_analysis': True,
                'needs_competitor_analysis': True,
                'needs_market_landscape': True,
                'priority': 'high',
                'completeness_score': 0
            }
    
    def _determine_agents(self, enhancement_plan: Dict) -> List[str]:
        """
        Determine which specialist agents to activate based on enhancement plan.
        """
        agents = []
        
        if enhancement_plan.get('needs_trend_analysis', True):
            agents.append("trend")
        
        if enhancement_plan.get('needs_competitor_analysis', True):
            agents.append("case")
        
        if enhancement_plan.get('needs_market_landscape', True):
            agents.append("landscape")
        
        # Always run at least one agent if brief is very incomplete
        if not agents and enhancement_plan.get('completeness_score', 0) < 50:
            agents = ["trend", "case", "landscape"]
        
        return agents
    
    def _extract_brief_context(self, brief: str) -> Dict[str, str]:
        """
        Extract key context from the brief for RAG queries.
        This is a simple keyword-based extraction; could be enhanced with NLP.
        """
        brief_lower = brief.lower()
        
        context = {}
        
        # Extract objective
        if "awareness" in brief_lower:
            context["objective"] = "brand awareness"
        elif "conversion" in brief_lower or "sales" in brief_lower:
            context["objective"] = "conversion sales"
        elif "retention" in brief_lower or "loyalty" in brief_lower:
            context["objective"] = "retention loyalty"
        else:
            context["objective"] = "general marketing"
        
        # Extract industry keywords
        industry_keywords = []
        if "sneaker" in brief_lower or "footwear" in brief_lower or "shoe" in brief_lower:
            industry_keywords.append("footwear")
        if "sustainable" in brief_lower or "eco" in brief_lower or "recycled" in brief_lower:
            industry_keywords.append("sustainable fashion")
        if "tech" in brief_lower or "software" in brief_lower or "saas" in brief_lower:
            industry_keywords.append("technology")
        if "food" in brief_lower or "restaurant" in brief_lower or "beverage" in brief_lower:
            industry_keywords.append("food beverage")
        
        context["industry"] = " ".join(industry_keywords) if industry_keywords else "general"
        
        # Extract audience
        audience_keywords = []
        if "millennial" in brief_lower:
            audience_keywords.append("millennials")
        if "gen z" in brief_lower or "gen-z" in brief_lower:
            audience_keywords.append("gen z")
        if "environment" in brief_lower:
            audience_keywords.append("environmentally conscious")
        if "professional" in brief_lower:
            audience_keywords.append("professionals")
        if "parent" in brief_lower or "mom" in brief_lower or "dad" in brief_lower:
            audience_keywords.append("parents")
        
        context["audience"] = " ".join(audience_keywords) if audience_keywords else "general audience"
        
        # Extract product type
        if "sneaker" in brief_lower or "shoe" in brief_lower:
            context["product"] = "sustainable sneakers recycled materials"
        elif "app" in brief_lower or "software" in brief_lower:
            context["product"] = "software application"
        else:
            context["product"] = "consumer product"
        
        # Extract geography
        if "us" in brief_lower or "united states" in brief_lower or "america" in brief_lower:
            context["geography"] = "US"
            if "urban" in brief_lower:
                context["geography"] = "US urban"
        elif "global" in brief_lower or "international" in brief_lower:
            context["geography"] = "global"
        else:
            context["geography"] = "regional"
        
        return context


# Convenience function
async def orchestrate_brief_enhancement(
    brief: str,
    filters: Optional[Dict[str, str]] = None,
    n_results: int = 5
) -> Dict[str, str]:
    """
    Quick function to orchestrate brief enhancement.
    
    Args:
        brief: Marketing campaign brief
        filters: Optional RAG filters
        n_results: Number of RAG results per query
        
    Returns:
        Dict with all agent outputs
    """
    orchestrator = MasterOrchestrator()
    return await orchestrator.enhance_brief(brief, filters, n_results)