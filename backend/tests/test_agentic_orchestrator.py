# test_agentic_orchestrator.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from agents.agentic_orchestrator import AgenticMasterOrchestrator

async def main():
    # Car insurance brief
    brief = """
BRIEF – ACME INSURANCE Digital and social campaign – Products: Car Insurance
SECTION DESCRIPTION CONTEXT SCOPE & DELIVERABLES - Creation of a digital and social campaign
GOALS - Increase the awareness of our car insurance
TARGET BRAND ACME Insurance
PRODUCT OR SERVICE Car insurance: third party only, third party fire and theft, 
fully comprehensive, optional breakdown cover
Value proposition: Comprehensive protection, flexible to suit vehicle use and driver profile, 
with tailored advice
Advantages: instant online quote, access to expert support, full digital policy management 
through app or portal
COMPETITORS TIMING & BUDGET Timing: go live campaign within 1 month
Target Audience: Millennials and Gen Z, digital-first, price-sensitive
Geography: Italy, Europe
"""
    
    print("="*70)
    print("TESTING AGENTIC MASTER ORCHESTRATOR")
    print("="*70)
    
    orchestrator = AgenticMasterOrchestrator()
    
    print("\n🚀 Running complete agentic pipeline...\n")
    
    results = await orchestrator.enhance_brief(
        brief=brief,
        n_results=5,
        use_all_agents=True
    )
    
    print("\n" + "="*70)
    print("RESULTS SUMMARY")
    print("="*70)
    
    print("\n1. BRIEF ANALYSIS:")
    print("-" * 70)
    print(results["brief_analysis"][:500] + "...")
    
    print("\n2. TREND ANALYSIS:")
    print("-" * 70)
    if results["trend_analysis"]:
        print(results["trend_analysis"][:500] + "...")
    else:
        print("Not generated")
    
    print("\n3. CASE ANALYSIS:")
    print("-" * 70)
    if results["case_analysis"]:
        print(results["case_analysis"][:500] + "...")
    else:
        print("Not generated")
    
    print("\n4. LANDSCAPE ANALYSIS:")
    print("-" * 70)
    if results["landscape_analysis"]:
        print(results["landscape_analysis"][:500] + "...")
    else:
        print("Not generated")
    
    print("\n5. FINAL INSIGHTS:")
    print("-" * 70)
    if results["final_insights"]:
        print(results["final_insights"][:500] + "...")
    else:
        print("Not generated")
    
    print("\n" + "="*70)
    print("✅ TEST COMPLETE")
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())