# test_agentic_market_agent.py
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

from agents.agentic_market_agent import AgenticMarketLandscapeAgent

async def main():
    # Car insurance campaign context
    brief_context = {
        "objective": "brand awareness launch",
        "industry": "insurance car insurance",
        "audience": "millennials gen z digital-first price-sensitive",
        "product": "car insurance digital app-based",
        "geography": "Italy Europe"
    }
    
    print("Testing Agentic Market Landscape Agent...")
    print("="*70)
    
    agent = AgenticMarketLandscapeAgent()
    result = await agent.analyze_landscape(brief_context, n_results=5)
    
    print("\n" + "="*70)
    print("RESULT:")
    print("="*70)
    print(result)
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())