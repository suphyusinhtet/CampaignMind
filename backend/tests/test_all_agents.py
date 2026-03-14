# test_all_agents.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from agents.brief_analyzer import BriefAnalyzerAgent
from agents.trend_agent import TrendAgent
from agents.case_intelligence import CaseIntelligenceAgent
from agents.market_landscape import MarketLandscapeAgent
from agents.insight_generator import InsightGeneratorAgent


async def main():
    # Sample brief
    brief = """
    Campaign Objective: Launch awareness campaign for new sustainable sneaker line
    
    Target Audience: Environmentally conscious millennials and Gen Z
    
    Product: Eco-friendly sneakers made from recycled ocean plastic
    
    Timeline: Q2 2025
    
    Geography: United States, urban markets
    """
    
    print("=" * 70)
    print("CampaignMind AI - FULL AGENT PIPELINE TEST")
    print("=" * 70)
    print()
    
    # Step 1: Brief Analysis
    print("Step 1: Analyzing Brief...")
    print("-" * 70)
    brief_analyzer = BriefAnalyzerAgent()
    brief_analysis = await brief_analyzer.analyze_brief(brief)
    print(brief_analysis[:300] + "...\n")
    
    # Brief context for other agents
    brief_context = {
        "objective": "brand awareness launch",
        "industry": "footwear sustainable fashion",
        "audience": "millennials gen z environmentally conscious",
        "product": "sustainable sneakers recycled materials",
        "geography": "US urban"
    }
    
    # Step 2: Trend Analysis
    print("Step 2: Analyzing Trends...")
    print("-" * 70)
    trend_agent = TrendAgent()
    trend_analysis = await trend_agent.analyze_trends(brief_context, n_results=2)
    print(trend_analysis[:300] + "...\n")
    
    # Step 3: Case Intelligence
    print("Step 3: Analyzing Case Studies...")
    print("-" * 70)
    case_agent = CaseIntelligenceAgent()
    case_analysis = await case_agent.analyze_cases(brief_context, n_results=2)
    print(case_analysis[:300] + "...\n")
    
    # Step 4: Market Landscape
    print("Step 4: Analyzing Market Landscape...")
    print("-" * 70)
    landscape_agent = MarketLandscapeAgent()
    landscape_analysis = await landscape_agent.analyze_landscape(brief_context, n_results=2)
    print(landscape_analysis[:300] + "...\n")
    
    # Step 5: Generate Final Insights
    print("Step 5: Generating Strategic Insights...")
    print("-" * 70)
    insight_agent = InsightGeneratorAgent()
    final_insights = await insight_agent.generate_insights(
        brief_analysis,
        trend_analysis,
        case_analysis,
        landscape_analysis,
        brief
    )
    print(final_insights)
    print()
    
    print("=" * 70)
    print("PIPELINE TEST COMPLETE ✓")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())