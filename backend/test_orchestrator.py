# test_orchestrator.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from agents.orchestrator import MasterOrchestrator


async def main():
    # Test briefs with different completeness levels
    
    print("\n" + "="*70)
    print("TEST 1: INCOMPLETE BRIEF (Should activate all agents)")
    print("="*70)
    
    incomplete_brief = """
    Campaign Objective: Launch awareness campaign for new sustainable sneaker line
    Target Audience: Environmentally conscious millennials and Gen Z
    Product: Eco-friendly sneakers made from recycled ocean plastic
    Timeline: Q2 2025
    Geography: United States, urban markets
    """
    
    orchestrator = MasterOrchestrator()
    results = await orchestrator.enhance_brief(incomplete_brief, n_results=2)
    
    print("\n" + "="*70)
    print("RESULTS SUMMARY:")
    print("="*70)
    print(f"Brief Analysis: {len(results['brief_analysis'])} chars")
    print(f"Trend Analysis: {'✓' if results['trend_analysis'] else '✗'}")
    print(f"Case Analysis: {'✓' if results['case_analysis'] else '✗'}")
    print(f"Landscape Analysis: {'✓' if results['landscape_analysis'] else '✗'}")
    print(f"Final Insights: {len(results['final_insights'])} chars")
    
    print("\n" + "="*70)
    print("FINAL INSIGHTS PREVIEW:")
    print("="*70)
    print(results['final_insights'][:500] + "...\n")
    
    # Test 2: More complete brief
    print("\n" + "="*70)
    print("TEST 2: SOMEWHAT COMPLETE BRIEF")
    print("="*70)
    
    complete_brief = """
    Campaign: "Ocean Strides" Sustainable Sneaker Launch
    
    Objective: Achieve 10M impressions and 100K website visits in Q2 2025
    
    Target Audience:
    - Ages: 25-35 (millennials) and 18-24 (Gen Z)
    - Income: $50K-$100K household
    - Values: Environmental activism, sustainable lifestyle
    - Behavior: Active on TikTok/Instagram, trust peer reviews
    
    Product: EcoKicks sustainable sneakers
    - Made from 100% recycled ocean plastic
    - Price point: $120-$150
    - Style: Minimalist, modern aesthetic
    - Comfort: Memory foam insoles, breathable design
    
    Budget: $500K
    Markets: NYC, LA, San Francisco, Seattle, Portland
    Timeline: April 1 - June 30, 2025
    
    KPIs: Impressions, website traffic, social engagement, brand recall
    """
    
    orchestrator2 = MasterOrchestrator()
    results2 = await orchestrator2.enhance_brief(complete_brief, n_results=2)
    
    print("\n" + "="*70)
    print("RESULTS SUMMARY:")
    print("="*70)
    print(f"Brief Analysis: {len(results2['brief_analysis'])} chars")
    print(f"Trend Analysis: {'✓' if results2['trend_analysis'] else '✗'}")
    print(f"Case Analysis: {'✓' if results2['case_analysis'] else '✗'}")
    print(f"Landscape Analysis: {'✓' if results2['landscape_analysis'] else '✗'}")
    print(f"Final Insights: {len(results2['final_insights'])} chars")
    
    print("\n" + "="*70)
    print("ORCHESTRATOR TESTS COMPLETE ✓")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())