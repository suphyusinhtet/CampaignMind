# test_brief_analyzer.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from agents.brief_analyzer import BriefAnalyzerAgent


async def main():
    # Sample incomplete brief
    brief = """
    Campaign Objective: Increase brand awareness for our new product
    
    Target Audience: Young professionals
    
    Timeline: Q2 2025
    
    We want something modern and engaging that resonates with our audience.
    """
    
    print("=" * 60)
    print("Testing Brief Analyzer Agent")
    print("=" * 60)
    print()
    print("INPUT BRIEF:")
    print("-" * 60)
    print(brief)
    print()
    print("ANALYSIS:")
    print("-" * 60)
    
    analyzer = BriefAnalyzerAgent()
    result = await analyzer.analyze_brief(brief)
    
    print(result)
    print()
    print("=" * 60)
    print("Test complete ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())