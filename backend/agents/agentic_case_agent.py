# agents/agentic_case_agent.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from rag.knowledge_manager import get_knowledge_manager
from tools.tool_manager import AgenticToolManager
from typing import Dict, Optional, List
import json
import re

class AgenticCaseIntelligenceAgent(CampaignMindAgent):
    """
    Agentic Case Intelligence Agent with multi-step competitor research.
    
    Strategy:
    1. Try RAG first for known case studies
    2. If insufficient → Search web for competitor campaigns
    3. If competitor names found → Scrape their websites
    4. Extract structured campaign data
    5. Self-evaluate and retry if needed
    """
    
    def __init__(self):
        super().__init__("case_intelligence")
        self.knowledge_manager = get_knowledge_manager()
        self.tools = AgenticToolManager()
        self.quality_threshold = 0.6
    
    async def analyze_cases(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5,
        max_retries: int = 2
    ) -> str:
        """
        Agentic case study analysis with multi-tool orchestration.
        
        Process:
        1. Extract campaign context (product, industry, geography)
        2. Query RAG for existing case studies
        3. Evaluate quality → If poor, search web for competitors
        4. Find competitor campaigns via web search
        5. Scrape competitor websites for campaign details
        6. Combine all sources
        7. Generate structured analysis
        8. Self-evaluate → Retry if needed
        """
        print("🕵️ Agentic Case Intelligence Agent starting competitor research...")
        
        # Step 1: Extract context
        context_keys = self._extract_campaign_context(brief_context)
        print(f"   📝 Campaign context: {context_keys}")
        
        # Step 2: Try RAG first
        print("   📚 Step 1: Querying RAG for case studies...")
        rag_results = self._query_rag(brief_context, filters, n_results)
        
        # Step 3: Evaluate RAG quality
        rag_quality = self._evaluate_case_quality(rag_results, context_keys)
        print(f"   ✅ RAG quality score: {rag_quality:.2f}")
        
        all_sources = rag_results
        competitors_found = []
        
        # Step 4: If RAG insufficient, search for competitors
        if rag_quality < self.quality_threshold:
            print(f"   ⚠️  RAG quality below threshold ({self.quality_threshold})")
            print("   🌐 Step 2: Searching for competitor campaigns...")
            
            # Search for competitors
            competitor_results = self._search_competitor_campaigns(brief_context, context_keys)
            all_sources.extend(competitor_results)
            
            # Extract competitor names
            competitors_found = self._extract_competitor_names(competitor_results, brief_context)
            print(f"   ✅ Found {len(competitors_found)} competitors: {competitors_found}")
        
        # Step 5: Scrape competitor websites for campaign details
        if competitors_found:
            print("   🔍 Step 3: Scraping competitor websites...")
            scraped_campaigns = self._scrape_competitor_campaigns(
                competitors_found,
                brief_context
            )
            all_sources.extend(scraped_campaigns)
            print(f"   ✅ Scraped {len(scraped_campaigns)} competitor sites")
        
        # Step 6: Search for specific campaign examples
        print("   🎯 Step 4: Searching for campaign case studies...")
        case_study_results = self._search_case_studies(brief_context, context_keys)
        all_sources.extend(case_study_results)
        
        # Step 7: Format all sources
        context = self._format_all_sources(all_sources)
        
        # Step 8: Generate response
        print("   🧠 Step 5: Generating campaign analysis...")
        response = await self._generate_response(brief_context, context, competitors_found)
        
        # Step 9: Self-evaluate response
        response_quality = self._evaluate_response(response, context_keys)
        print(f"   ✅ Response quality: {response_quality:.2f}")
        
        # Step 10: Retry if quality still low
        if response_quality < self.quality_threshold and max_retries > 0:
            print(f"   🔄 Response quality low, retrying with refined strategy...")
            # Add more specific search terms
            refined_context = dict(brief_context)
            refined_context["_refined_search"] = "true"
            return await self.analyze_cases(refined_context, filters, n_results, max_retries - 1)
        
        print("   ✅ Agentic case analysis complete!")
        return response
    
    def _extract_campaign_context(self, brief_context: Dict[str, str]) -> Dict[str, str]:
        """Extract key context for case study search"""
        context = {}
        
        # Product/service
        if "product" in brief_context:
            context["product"] = brief_context["product"]
        
        # Industry
        if "industry" in brief_context:
            context["industry"] = brief_context["industry"]
        elif "sector" in brief_context:
            context["industry"] = brief_context["sector"]
        
        # Geography
        if "geography" in brief_context:
            context["geography"] = brief_context["geography"]
        if "brand_name" in brief_context:
            context["brand_name"] = brief_context["brand_name"]
        
        # Campaign type
        if "objective" in brief_context:
            obj = brief_context["objective"].lower()
            if "awareness" in obj:
                context["campaign_type"] = "awareness"
            elif "conversion" in obj or "sales" in obj:
                context["campaign_type"] = "conversion"
            elif "launch" in obj:
                context["campaign_type"] = "launch"
        
        return context

    def _normalize_name(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", (value or "").lower())

    def _excluded_brands(self, brief_context: Dict[str, str]) -> set[str]:
        candidates = []
        for key in ("brand_name", "target_brand", "brand", "company"):
            val = brief_context.get(key)
            if isinstance(val, str) and val.strip():
                candidates.extend([p.strip() for p in val.split(",") if p.strip()])
        return {self._normalize_name(x) for x in candidates if x}

    def _resolve_region(self, geography: str) -> str:
        """Map geography text to DuckDuckGo region code."""
        geo = (geography or "").lower()
        if "italy" in geo or "it" == geo:
            return "it-it"
        if "uk" in geo or "united kingdom" in geo or "britain" in geo:
            return "uk-en"
        if "us" in geo or "usa" in geo or "united states" in geo:
            return "us-en"
        return "wt-wt"
    
    def _query_rag(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]],
        n_results: int
    ) -> List[Dict]:
        """Query RAG for case studies"""
        query_parts = [
            brief_context.get('industry', ''),
            brief_context.get('product', ''),
            brief_context.get('geography', ''),
            'case study campaign competitor'
        ]
        query = ' '.join([p for p in query_parts if p]).strip()
        
        results = self.knowledge_manager.query(
            query_text=query,
            doc_type="case_studies",
            filters=filters,
            n_results=n_results
        )
        
        # Format as dicts
        formatted = []
        for r in results:
            formatted.append({
                "title": r['metadata'].get('brand', 'Campaign Case Study'),
                "content": r['content'],
                "source": "rag_database",
                "metadata": r['metadata']
            })
        
        return formatted
    
    def _search_competitor_campaigns(
        self,
        brief_context: Dict[str, str],
        context_keys: Dict[str, str]
    ) -> List[Dict]:
        """Search web for competitor campaigns"""
        product = context_keys.get('product', brief_context.get('product', 'product'))
        industry = context_keys.get('industry', brief_context.get('industry', 'industry'))
        geography = context_keys.get('geography', brief_context.get('geography', 'market'))
        region = self._resolve_region(geography)
        
        # Build multiple search queries
        queries = [
            f"{product} {industry} companies {geography}",
            f"{product} brands {geography} marketing campaigns",
            f"best {product} {industry} competitors {geography}",
            f"{product} market leaders {geography}",
        ]
        
        all_results = []
        for query in queries:
            results = self.tools.web_search(query, num_results=5, region=region)
            all_results.extend(results)
            
        # Deduplicate
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
        
        return unique_results[:10]  # Top 10
    
    def _extract_competitor_names(self, search_results: List[Dict], brief_context: Optional[Dict[str, str]] = None) -> List[str]:
        """Extract competitor brand names from search results"""
        competitors = set()
        excluded = self._excluded_brands(brief_context or {})
        
        for result in search_results:
            text = f"{result.get('title', '')} {result.get('snippet', '')}"
            
            # Common patterns for brand names (capitalized words)
            words = text.split()
            for i, word in enumerate(words):
                # Look for capitalized words that might be brand names
                if word and word[0].isupper() and len(word) > 2:
                    # Check if it's not a common word
                    if word.lower() not in ['the', 'and', 'for', 'with', 'from', 'this', 'that']:
                        # Check if followed by keywords like 'insurance', 'auto', etc.
                        if i + 1 < len(words):
                            next_word = words[i + 1].lower()
                            if next_word in ['insurance', 'auto', 'car', 'assurance', 'assicurazione']:
                                if self._normalize_name(word) not in excluded:
                                    competitors.add(word)
        
        return list(competitors)[:5]  # Top 5 competitors
    
    def _scrape_competitor_campaigns(
        self,
        competitors: List[str],
        brief_context: Dict[str, str]
    ) -> List[Dict]:
        """Scrape competitor websites for campaign information"""
        scraped_data = []
        product = brief_context.get('product', 'product')
        region = self._resolve_region(brief_context.get('geography', ''))
        
        for competitor in competitors:
            # Search for competitor's campaign pages
            query = f"{competitor} marketing campaign {product}"
            search_results = self.tools.web_search(query, num_results=2, region=region)
            
            for result in search_results[:2]:  # Top 2 per competitor
                try:
                    scraped = self.tools.scrape_url(result["url"])
                    if "error" not in scraped:
                        # Add competitor context
                        scraped["competitor"] = competitor
                        scraped["title"] = f"{competitor} Campaign"
                        scraped_data.append(scraped)
                except Exception as e:
                    print(f"   ⚠️  Scraping error for {competitor}: {e}")
                    continue
        
        return scraped_data
    
    def _search_case_studies(
        self,
        brief_context: Dict[str, str],
        context_keys: Dict[str, str]
    ) -> List[Dict]:
        """Search for specific campaign case studies"""
        product = context_keys.get('product', '')
        industry = context_keys.get('industry', '')
        campaign_type = context_keys.get('campaign_type', 'marketing')
        geography = context_keys.get('geography', brief_context.get('geography', ''))
        region = self._resolve_region(geography)
        
        queries = [
            f"{product} {campaign_type} campaign case study",
            f"{industry} successful campaigns examples",
            f"{product} advertising campaign analysis",
            f"best {product} marketing campaigns 2024"
        ]
        
        all_results = []
        for query in queries:
            results = self.tools.web_search(query, num_results=3, region=region)
            
            # Scrape promising case study pages
            for result in results:
                if any(keyword in result.get('title', '').lower() for keyword in ['case study', 'campaign', 'success']):
                    scraped = self.tools.scrape_url(result["url"])
                    if "error" not in scraped:
                        all_results.append(scraped)
        
        return all_results[:5]  # Top 5 case studies
    
    def _evaluate_case_quality(
        self,
        results: List[Dict],
        context_keys: Dict[str, str]
    ) -> float:
        """Evaluate quality of case study results"""
        if not results:
            return 0.0
        
        # Check for key information
        required_elements = ['campaign', 'brand', 'strategy', 'results']
        
        scores = []
        for result in results:
            content = result.get('content', '').lower()
            
            # Check for required elements
            element_score = sum(1 for elem in required_elements if elem in content) / len(required_elements)
            
            # Check for quantitative data (metrics)
            has_metrics = any(char.isdigit() and '%' in content for char in content)
            metric_score = 1.0 if has_metrics else 0.3
            
            # Check for context match
            context_score = 0.0
            for key, value in context_keys.items():
                if value.lower() in content:
                    context_score += 0.25
            context_score = min(context_score, 1.0)
            
            # Combined score
            scores.append((element_score + metric_score + context_score) / 3)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _format_all_sources(self, sources: List[Dict]) -> str:
        """Format all sources for LLM prompt"""
        formatted = []
        
        # Group by source type
        rag_sources = [s for s in sources if s.get('source') == 'rag_database']
        web_sources = [s for s in sources if s.get('source') == 'web_search']
        scraped_sources = [s for s in sources if s.get('source') == 'web_scrape']
        
        if rag_sources:
            formatted.append("\n=== CASE STUDIES FROM KNOWLEDGE BASE ===\n")
            for i, source in enumerate(rag_sources, 1):
                formatted.append(f"\n--- Case Study {i} ---")
                formatted.append(f"Brand: {source.get('title', 'N/A')}")
                formatted.append(f"Content:\n{source.get('content', '')}\n")
        
        if web_sources:
            formatted.append("\n=== COMPETITOR CAMPAIGNS FROM WEB SEARCH ===\n")
            for i, source in enumerate(web_sources, 1):
                formatted.append(f"\n--- Search Result {i} ---")
                formatted.append(f"Title: {source.get('title', 'N/A')}")
                formatted.append(f"URL: {source.get('url', 'N/A')}")
                formatted.append(f"Snippet: {source.get('snippet', '')}\n")
        
        if scraped_sources:
            formatted.append("\n=== DETAILED COMPETITOR CAMPAIGN DATA ===\n")
            for i, source in enumerate(scraped_sources, 1):
                formatted.append(f"\n--- Competitor: {source.get('competitor', 'Unknown')} ---")
                formatted.append(f"URL: {source.get('url', 'N/A')}")
                formatted.append(f"Content:\n{source.get('content', '')[:2000]}\n")  # Limit to 2000 chars
        
        return "\n".join(formatted)
    
    async def _generate_response(
        self,
        brief_context: Dict[str, str],
        context: str,
        competitors_found: List[str]
    ) -> str:
        """Generate LLM response with all context"""
        competitor_list = ", ".join(competitors_found) if competitors_found else "various competitors"
        target_brand = brief_context.get("brand_name", "the target brand")
        
        prompt = f"""Analyze competitor campaigns and case studies relevant to this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

COMPETITORS IDENTIFIED:
{competitor_list}

RETRIEVED CAMPAIGN DATA FROM MULTIPLE SOURCES:
{context}

Provide comprehensive case study analysis in the structured markdown format specified in your system message.

CRITICAL REQUIREMENTS:
1. Create detailed competitor comparison tables (use markdown tables)
2. Include specific campaign names, strategies, and results
3. Extract quantitative data (metrics, percentages, results)
4. Identify differentiation opportunities
5. Provide actionable insights for the campaign
6. Never include {target_brand} itself in competitor lists or competitor tables.

If competitor data is limited, clearly state what information is available and what requires further research."""

        response = await self.agent.on_messages(
            [TextMessage(content=prompt, source="user")],
            CancellationToken()
        )
        
        return response.chat_message.content
    
    def _format_brief_context(self, context: Dict[str, str]) -> str:
        """Format brief context"""
        lines = []
        for key, value in context.items():
            if not key.startswith('_'):  # Skip internal keys
                lines.append(f"- {key.title()}: {value}")
        return '\n'.join(lines)
    
    def _evaluate_response(self, response: str, context_keys: Dict[str, str]) -> float:
        """Evaluate quality of generated response"""
        response_lower = response.lower()
        
        # Check for tables (markdown table format)
        has_tables = '|' in response and '---' in response
        table_score = 1.0 if has_tables else 0.3
        
        # Check for competitor names
        has_competitors = any(word.istitle() for word in response.split())
        competitor_score = 1.0 if has_competitors else 0.5
        
        # Check for quantitative data
        has_metrics = any(char.isdigit() and '%' in response for char in response)
        metric_score = 1.0 if has_metrics else 0.5
        
        # Check for key sections
        required_sections = ['competitor', 'campaign', 'strategy', 'insight']
        section_score = sum(1 for section in required_sections if section in response_lower) / len(required_sections)
        
        # Combined quality score
        quality = (table_score + competitor_score + metric_score + section_score) / 4
        
        return quality
