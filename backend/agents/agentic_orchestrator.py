# agents/agentic_orchestrator.py
import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime
import json
import re

from agents.brief_analyzer import BriefAnalyzerAgent
from agents.agentic_trend_agent import AgenticTrendAgent
from agents.agentic_case_agent import AgenticCaseIntelligenceAgent
from agents.agentic_market_agent import AgenticMarketLandscapeAgent
from agents.insight_generator import InsightGeneratorAgent
from agents.creator_agent import CreatorAgent

class AgenticMasterOrchestrator:
    """
    Agentic Master Orchestrator for CampaignMind.
    
    Coordinates multiple agentic specialist agents with:
    - Multi-step search strategies
    - Self-correction capabilities
    - Multiple tool orchestration (RAG + Web + Scraping)
    - Parallel execution for performance
    - Status callbacks for real-time updates
    """
    
    def __init__(self):
        print("Initializing Agentic Master Orchestrator...")
        
        # Brief Analyzer (non-agentic - just analysis, no external data needed)
        self.brief_analyzer = BriefAnalyzerAgent()
        
        # Agentic Specialist Agents
        self.trend_agent = AgenticTrendAgent()
        self.case_agent = AgenticCaseIntelligenceAgent()
        self.landscape_agent = AgenticMarketLandscapeAgent()
        
        # Insight Generator (synthesizes all results)
        self.insight_agent = InsightGeneratorAgent()
        self.creator_agent = CreatorAgent()
        
        print("✅ Agentic Master Orchestrator ready!")
    
    async def enhance_brief(
        self,
        brief: str,
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5,
        status_callback: Optional[callable] = None,
        use_all_agents: bool = True
    ) -> Dict[str, str]:
        """
        Enhanced brief processing with agentic agents.
        
        Args:
            brief: Marketing brief text
            filters: Optional filters for RAG queries
            n_results: Number of results per agent
            status_callback: Optional callback for real-time status updates
            use_all_agents: Whether to run all agents or just Brief Analyzer
            
        Returns:
            Dictionary with all agent outputs
        """
        print(f"\n{'='*70}")
        print("🤖 AGENTIC MASTER ORCHESTRATOR - STARTING ANALYSIS")
        print(f"{'='*70}\n")
        
        start_time = datetime.now()
        
        # Notify: Brief Analyzer starting
        if status_callback:
            await status_callback("brief_analyzer", "working", "Analyzing brief completeness...")
        
        # ============================================================
        # STEP 1: Analyze Brief (Always Runs)
        # ============================================================
        print("📋 Step 1: Analyzing brief with Brief Analyzer...")
        brief_analysis = await self.brief_analyzer.analyze_brief(brief)
        
        if status_callback:
            await status_callback("brief_analyzer", "complete", "Brief analysis complete")
        
        # Extract enhancement plan and context
        enhancement_plan = self._parse_enhancement_plan(brief_analysis)
        brief_context = self._extract_brief_context(brief)
        
        print(f"\n✅ Brief Analysis Complete")
        print(f"   Agents to run: {list(enhancement_plan.keys())}")
        
        # Initialize results
        results = {
            "brief_analysis": brief_analysis,
            "trend_analysis": None,
            "case_analysis": None,
            "landscape_analysis": None,
            "final_insights": None,
            "creator_concepts": None,
        }
        
        # If only brief analysis requested, return early
        if not use_all_agents:
            return results
        
        # ============================================================
        # STEP 2: Run Agentic Specialist Agents in Parallel
        # ============================================================
        print(f"\n📊 Step 2: Running agentic specialist agents in parallel...")
        
        # Determine which agents to run
        agents_to_run = self._determine_agents(enhancement_plan)
        tasks = []
        task_names = []
        
        # Trend Agent
        if "trend" in agents_to_run:
            if status_callback:
                await status_callback("trend_agent", "working", "Searching for market trends...")
            
            print("   🔍 Starting Agentic Trend Agent...")
            tasks.append(self.trend_agent.analyze_trends(brief_context, filters, n_results))
            task_names.append("trend")
        
        # Case Intelligence Agent
        if "case" in agents_to_run:
            if status_callback:
                await status_callback("case_intelligence", "working", "Researching competitor campaigns...")
            
            print("   🕵️ Starting Agentic Case Intelligence Agent...")
            tasks.append(self.case_agent.analyze_cases(brief_context, filters, n_results))
            task_names.append("case")
        
        # Market Landscape Agent
        if "landscape" in agents_to_run:
            if status_callback:
                await status_callback("market_landscape", "working", "Analyzing competitive landscape...")
            
            print("   🗺️ Starting Agentic Market Landscape Agent...")
            tasks.append(self.landscape_agent.analyze_landscape(brief_context, filters, n_results))
            task_names.append("landscape")
        
        # Execute all agents in parallel
        if tasks:
            print(f"\n⚡ Executing {len(tasks)} agents in parallel...")
            parallel_start = datetime.now()
            
            agent_results = await asyncio.gather(*tasks)
            
            parallel_time = (datetime.now() - parallel_start).total_seconds()
            print(f"\n✅ Parallel execution complete in {parallel_time:.2f}s")
            
            # Map results back
            for i, task_name in enumerate(task_names):
                if task_name == "trend":
                    results["trend_analysis"] = agent_results[i]
                    if status_callback:
                        await status_callback("trend_agent", "complete", "Trend analysis complete")
                elif task_name == "case":
                    results["case_analysis"] = agent_results[i]
                    if status_callback:
                        await status_callback("case_intelligence", "complete", "Case analysis complete")
                elif task_name == "landscape":
                    results["landscape_analysis"] = agent_results[i]
                    if status_callback:
                        await status_callback("market_landscape", "complete", "Market analysis complete")
        
        # ============================================================
        # STEP 3: Generate Final Insights
        # ============================================================
        print("\n💡 Step 3: Generating strategic insights...")
        
        if status_callback:
            await status_callback("insight_generator", "working", "Synthesizing strategic insights...")
        
        results["final_insights"] = await self.insight_agent.generate_insights(
            brief_analysis=results["brief_analysis"],
            trend_analysis=results["trend_analysis"] or "No trend analysis requested",
            case_analysis=results["case_analysis"] or "No case analysis requested",
            landscape_analysis=results["landscape_analysis"] or "No landscape analysis requested",
            original_brief=brief
        )
        
        if status_callback:
            await status_callback("insight_generator", "complete", "Strategic insights generated")

        # ============================================================
        # STEP 4: Generate Creative Concepts
        # ============================================================
        print("\n🎨 Step 4: Generating creative campaign concepts...")
        if status_callback:
            await status_callback("creator_agent", "working", "Generating campaign concepts...")

        results["creator_concepts"] = await self.creator_agent.generate_concepts(
            brief_analysis=results["brief_analysis"],
            trend_analysis=results["trend_analysis"] or "No trend analysis requested",
            case_analysis=results["case_analysis"] or "No case analysis requested",
            landscape_analysis=results["landscape_analysis"] or "No landscape analysis requested",
            final_insights=results["final_insights"] or "",
            original_brief=brief,
            timing=brief_context.get("timing", ""),
        )

        if status_callback:
            await status_callback("creator_agent", "complete", "Campaign concepts generated")

        if results["creator_concepts"]:
            results["final_insights"] = (
                f"{results['final_insights']}\n\n---\n\n{results['creator_concepts']}"
            )
        
        # ============================================================
        # COMPLETION
        # ============================================================
        total_time = (datetime.now() - start_time).total_seconds()
        
        print(f"\n{'='*70}")
        print(f"✅ AGENTIC ORCHESTRATOR COMPLETE - Total time: {total_time:.2f}s")
        print(f"{'='*70}\n")
        
        return results
    
    def _parse_enhancement_plan(self, brief_analysis: str) -> Dict[str, bool]:
        """
        Parse brief analysis to determine which agents to run.
        
        Looks for "Guidance for Next Agents" section.
        """
        plan = {
            "trend": True,    # Default: run all
            "case": True,
            "landscape": True
        }
        
        # Try to parse from brief analysis
        analysis_lower = brief_analysis.lower()
        
        # Check if guidance section exists
        if "guidance for next agents" in analysis_lower:
            # If Trend Agent is mentioned, enable it
            if "trend agent" in analysis_lower or "trend analysis" in analysis_lower:
                plan["trend"] = True
            
            # If Case Agent is mentioned
            if "case agent" in analysis_lower or "case intelligence" in analysis_lower:
                plan["case"] = True
            
            # If Market/Landscape Agent is mentioned
            if "market agent" in analysis_lower or "landscape" in analysis_lower:
                plan["landscape"] = True
        
        return plan
    
    def _extract_brief_context(self, brief: str) -> Dict[str, str]:
        """
        Extract key context from brief for agent queries.
        
        Returns dict with: objective, industry, audience, product, geography
        """
        context = {}
        brief_lower = brief.lower()
        
        # Extract objective
        if "objective" in brief_lower or "goal" in brief_lower:
            context["objective"] = self._extract_section(brief, ["objective", "goal"])
        
        # Extract industry
        if "industry" in brief_lower or "sector" in brief_lower:
            context["industry"] = self._extract_section(brief, ["industry", "sector"])
        
        # Try to infer industry from keywords
        if not context.get("industry"):
            industries = {
                "insurance": ["insurance", "policy", "coverage", "premium"],
                "automotive": ["car", "vehicle", "automotive", "auto"],
                "technology": ["tech", "software", "app", "digital", "saas"],
                "retail": ["retail", "ecommerce", "shopping", "store"],
                "finance": ["banking", "financial", "fintech", "payment"]
            }
            for industry, keywords in industries.items():
                if any(kw in brief_lower for kw in keywords):
                    context["industry"] = industry
                    break
        
        # Extract audience
        if "audience" in brief_lower or "target" in brief_lower:
            context["audience"] = self._extract_section(brief, ["audience", "target"])
        
        # Extract product/service
        if "product" in brief_lower or "service" in brief_lower:
            context["product"] = self._extract_section(brief, ["product", "service"])
        
        # Extract geography
        if "geography" in brief_lower or "market" in brief_lower or "region" in brief_lower:
            context["geography"] = self._extract_section(brief, ["geography", "market", "region", "country"])

        # Extract timing / timeline
        if "timing" in brief_lower or "timeline" in brief_lower or "launch" in brief_lower:
            context["timing"] = self._extract_section(brief, ["timing", "timeline", "launch", "go live", "within"])
        
        # Try to infer geography from keywords
        if not context.get("geography"):
            geographies = ["italy", "europe", "us", "uk", "global", "asia", "americas"]
            for geo in geographies:
                if geo in brief_lower:
                    context["geography"] = geo
                    break
        
        return context
    
    def _extract_section(self, brief: str, keywords: List[str]) -> str:
        """Extract text section related to keywords"""
        lines = brief.split('\n')
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(kw in line_lower for kw in keywords):
                # Extract this line and next few lines
                section_lines = []
                for j in range(i, min(i + 3, len(lines))):
                    section_lines.append(lines[j].strip())
                return ' '.join(section_lines)
        
        # If no section found, try to find keywords in text
        for keyword in keywords:
            if keyword in brief.lower():
                # Extract surrounding text
                idx = brief.lower().find(keyword)
                start = max(0, idx - 50)
                end = min(len(brief), idx + 100)
                return brief[start:end].strip()
        
        return ""
    
    def _determine_agents(self, enhancement_plan: Dict[str, bool]) -> List[str]:
        """Determine which agents should run based on plan"""
        agents = []
        
        if enhancement_plan.get("trend", True):
            agents.append("trend")
        if enhancement_plan.get("case", True):
            agents.append("case")
        if enhancement_plan.get("landscape", True):
            agents.append("landscape")
        
        return agents
    
    def format_results_for_api(self, results: Dict[str, str]) -> Dict[str, Any]:
        """
        Format results for API response.
        
        Returns structured JSON with all analyses.
        """
        return {
            "brief_analysis": results["brief_analysis"],
            "trend_analysis": results["trend_analysis"],
            "case_analysis": results["case_analysis"],
            "landscape_analysis": results["landscape_analysis"],
            "creator_concepts": results.get("creator_concepts"),
            "final_insights": results["final_insights"],
            "timestamp": datetime.now().isoformat()
        }
