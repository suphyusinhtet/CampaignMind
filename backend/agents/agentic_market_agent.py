# agents/agentic_market_agent.py
import asyncio
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from rag.knowledge_manager import get_knowledge_manager
from tools.tool_manager import AgenticToolManager
from typing import Dict, Optional, List

class AgenticMarketLandscapeAgent(CampaignMindAgent):
    """
    Agentic Market Landscape Agent with multi-step competitive research.
    
    Strategy:
    1. Try RAG first for known market research
    2. If insufficient → Search web for competitor landscape
    3. Extract competitor details from search results
    4. Scrape competitor websites for positioning data
    5. Combine all sources into structured analysis
    6. Self-evaluate and retry if needed
    """
    
    def __init__(self):
        super().__init__("market_landscape")
        self.knowledge_manager = get_knowledge_manager()
        self.tools = AgenticToolManager()
        self.quality_threshold = 0.6
    
    async def analyze_landscape(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5,
        max_retries: int = 2
    ) -> str:
        """
        Agentic market landscape analysis with multi-tool orchestration.
        
        Process:
        1. Extract market context (product, industry, geography)
        2. Query RAG for market research data
        3. Evaluate quality → If poor, search web for competitors
        4. Find competitor positioning via web search
        5. Scrape competitor websites for detailed data
        6. Extract pricing, features, positioning
        7. Combine all sources
        8. Generate structured analysis with tables
        9. Self-evaluate → Retry if needed
        """
        print("🗺️ Agentic Market Landscape Agent starting competitive analysis...")
        
        # Step 1: Extract context
        market_context = self._extract_market_context(brief_context)
        print(f"   📝 Market context: {market_context}")
        
        # Step 2: Try RAG first
        print("   📚 Step 1: Querying RAG for market research...")
        rag_results = self._query_rag(brief_context, filters, n_results)
        
        # Step 3: Evaluate RAG quality
        rag_quality = self._evaluate_market_quality(rag_results, market_context)
        print(f"   ✅ RAG quality score: {rag_quality:.2f}")
        
        all_sources = rag_results
        competitor_data = []
        
        # Step 4: If RAG insufficient, search for market landscape
        if rag_quality < self.quality_threshold:
            print(f"   ⚠️  RAG quality below threshold ({self.quality_threshold})")
            print("   🌐 Step 2: Searching for market landscape data...")
            
            # Search for market analysis
            market_results = self._search_market_landscape(brief_context, market_context)
            all_sources.extend(market_results)
            
            # Search for competitor positioning
            print("   🎯 Step 3: Searching for competitor positioning...")
            competitor_results = self._search_competitor_positioning(brief_context, market_context)
            all_sources.extend(competitor_results)
            
            # Extract competitor names
            competitors_found = self._extract_competitor_names(all_sources, brief_context)
            print(f"   ✅ Identified {len(competitors_found)} competitors: {competitors_found}")
            
            # Step 5: Scrape competitor websites for details
            if competitors_found:
                print("   🔍 Step 4: Researching competitor details...")
                competitor_data = self._research_competitors(
                    competitors_found,
                    brief_context,
                    market_context
                )
                all_sources.extend(competitor_data)
                print(f"   ✅ Researched {len(competitor_data)} competitors in detail")
        
        # Step 6: Format all sources
        context = self._format_all_sources(all_sources, competitor_data)
        
        # Step 7: Generate response
        print("   🧠 Step 5: Generating market landscape analysis...")
        response = await self._generate_response(brief_context, context)
        
        # Step 8: Self-evaluate response
        response_quality = self._evaluate_response(response, market_context)
        print(f"   ✅ Response quality: {response_quality:.2f}")
        
        # Step 9: Retry if quality still low
        if response_quality < self.quality_threshold and max_retries > 0:
            print(f"   🔄 Response quality low, retrying with refined strategy...")
            # Add more specific search terms
            refined_context = dict(brief_context)
            refined_context["_refined_market_search"] = "true"
            return await self.analyze_landscape(refined_context, filters, n_results, max_retries - 1)
        
        print("   ✅ Agentic market analysis complete!")
        return response
    
    def _extract_market_context(self, brief_context: Dict[str, str]) -> Dict[str, str]:
        """Extract key market context"""
        context = {}
        
        if "product" in brief_context:
            context["product"] = brief_context["product"]
        
        if "industry" in brief_context:
            context["industry"] = brief_context["industry"]
        elif "sector" in brief_context:
            context["industry"] = brief_context["sector"]
        
        if "geography" in brief_context:
            context["geography"] = brief_context["geography"]
        
        if "audience" in brief_context:
            context["audience"] = brief_context["audience"]
        if "brand_name" in brief_context:
            context["brand_name"] = brief_context["brand_name"]
        
        return context

    def _normalize_name(self, value: str) -> str:
        return "".join(ch for ch in (value or "").lower() if ch.isalnum())

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
        if "italy" in geo or geo == "it":
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
        """Query RAG for market research"""
        query_parts = [
            brief_context.get('industry', ''),
            brief_context.get('product', ''),
            brief_context.get('geography', ''),
            'market research competitive landscape positioning'
        ]
        query = ' '.join([p for p in query_parts if p]).strip()
        
        results = self.knowledge_manager.query(
            query_text=query,
            doc_type="market_research",
            filters=filters,
            n_results=n_results
        )
        
        # Format as dicts
        formatted = []
        for r in results:
            formatted.append({
                "title": r['metadata'].get('title', 'Market Research'),
                "content": r['content'],
                "source": "rag_database",
                "metadata": r['metadata']
            })
        
        return formatted
    
    def _search_market_landscape(
        self,
        brief_context: Dict[str, str],
        market_context: Dict[str, str]
    ) -> List[Dict]:
        """Search web for market landscape data"""
        product = market_context.get('product', brief_context.get('product', 'product'))
        industry = market_context.get('industry', brief_context.get('industry', 'industry'))
        geography = market_context.get('geography', brief_context.get('geography', 'market'))
        region = self._resolve_region(geography)
        
        queries = [
            f"{product} {industry} market analysis {geography}",
            f"{product} competitive landscape {geography}",
            f"{industry} market leaders {geography}",
            f"{product} market share {geography} 2024"
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
        
        return unique_results[:10]
    
    def _search_competitor_positioning(
        self,
        brief_context: Dict[str, str],
        market_context: Dict[str, str]
    ) -> List[Dict]:
        """Search for competitor positioning information"""
        product = market_context.get('product', '')
        geography = market_context.get('geography', '')
        region = self._resolve_region(geography)
        
        queries = [
            f"{product} companies comparison {geography}",
            f"best {product} providers {geography}",
            f"{product} pricing comparison {geography}",
            f"{product} features comparison {geography}"
        ]
        
        all_results = []
        for query in queries:
            results = self.tools.web_search(query, num_results=3, region=region)
            
            # Scrape promising comparison pages
            for result in results:
                if any(keyword in result.get('title', '').lower() 
                      for keyword in ['comparison', 'vs', 'review', 'best']):
                    scraped = self.tools.scrape_url(result["url"])
                    if "error" not in scraped:
                        all_results.append(scraped)
                else:
                    all_results.append(result)
        
        return all_results[:8]
    
    def _extract_competitor_names(self, search_results: List[Dict], brief_context: Optional[Dict[str, str]] = None) -> List[str]:
        """Extract competitor brand names from search results - IMPROVED"""
        competitors = set()
        excluded = self._excluded_brands(brief_context or {})
        
        # Known insurance brands (European/Italian focus)
        known_brands = {
            'allianz', 'genertel', 'linear', 'verti', 'prima', 'quixa', 
            'sara', 'unipolsai', 'reale mutua', 'axa', 'zurich', 'generali',
            'direct line', 'admiral', 'churchill', 'neosurance', 'yolo',
            'covéa', 'mapfre', 'groupama', 'aviva', 'telepass', 'preventivass',
            'octo', 'autosicura'
        }
        
        # Generic words to exclude
        exclude_words = {
            'car', 'cheap', 'best', 'compare', 'find', 'top', 'insurance',
            'moneysupermarket', 'comparethemarket', 'gocompare'  # UK aggregators
        }
        
        for result in search_results:
            text = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('content', '')}".lower()
            
            # Check for known brands
            for brand in known_brands:
                if brand in text:
                    # Capitalize properly
                    candidate = brand.title()
                    if self._normalize_name(candidate) not in excluded:
                        competitors.add(candidate)
            
            # Extract from titles (but filter carefully)
            title_words = result.get('title', '').split()
            for i, word in enumerate(title_words):
                word_lower = word.lower()
                
                # Skip if excluded
                if word_lower in exclude_words:
                    continue
                
                # Must be capitalized and 3+ chars
                if word and word[0].isupper() and len(word) > 2:
                    # Check if followed by insurance keywords
                    if i + 1 < len(title_words):
                        next_word = title_words[i + 1].lower()
                        if next_word in ['insurance', 'assicurazioni', 'auto', 'car', 'assurance']:
                            if self._normalize_name(word) not in excluded:
                                competitors.add(word)
        
        # Filter out any remaining generic words
        competitors = {c for c in competitors if c.lower() not in exclude_words and self._normalize_name(c) not in excluded}
        
        return list(competitors)[:10]
    
    def _research_competitors(
        self,
        competitors: List[str],
        brief_context: Dict[str, str],
        market_context: Dict[str, str]
    ) -> List[Dict]:
        """Research competitor details via web search and scraping"""
        competitor_data = []
        product = market_context.get('product', 'product')
        geography = market_context.get('geography', brief_context.get('geography', ''))
        region = self._resolve_region(geography)
        
        for competitor in competitors[:5]:  # Limit to top 5 for performance
            # Search for competitor info
            queries = [
                f"{competitor} {product} pricing",
                f"{competitor} {product} features",
                f"{competitor} positioning strategy"
            ]
            
            for query in queries[:1]:  # Only first query per competitor
                results = self.tools.web_search(query, num_results=2, region=region)
                
                for result in results[:1]:  # Top result only
                    try:
                        scraped = self.tools.scrape_url(result["url"])
                        if "error" not in scraped:
                            scraped["competitor"] = competitor
                            scraped["research_type"] = "competitor_detail"
                            competitor_data.append(scraped)
                            break  # Got data, move to next competitor
                    except:
                        continue
        
        return competitor_data
    
    def _evaluate_market_quality(
        self,
        results: List[Dict],
        market_context: Dict[str, str]
    ) -> float:
        """Evaluate quality of market research results"""
        if not results:
            return 0.0
        
        # Check for key market information
        required_elements = ['competitor', 'market', 'segment', 'positioning', 'strategy']
        
        scores = []
        for result in results:
            content = result.get('content', '').lower()
            
            # Check for required elements
            element_score = sum(1 for elem in required_elements if elem in content) / len(required_elements)
            
            # Check for comparison data (tables, vs, comparison)
            has_comparison = any(keyword in content for keyword in ['|', 'vs', 'comparison', 'table'])
            comparison_score = 1.0 if has_comparison else 0.3
            
            # Check for context match
            context_score = 0.0
            for key, value in market_context.items():
                if value and value.lower() in content:
                    context_score += 0.25
            context_score = min(context_score, 1.0)
            
            # Combined score
            scores.append((element_score + comparison_score + context_score) / 3)
        
        return sum(scores) / len(scores) if scores else 0.0
    
    def _format_all_sources(self, sources: List[Dict], competitor_data: List[Dict]) -> str:
        """Format all sources for LLM prompt"""
        formatted = []
        
        # Group by source type
        rag_sources = [s for s in sources if s.get('source') == 'rag_database']
        web_sources = [s for s in sources if s.get('source') == 'web_search']
        scraped_sources = [s for s in sources if s.get('source') == 'web_scrape']
        
        if rag_sources:
            formatted.append("\n=== MARKET RESEARCH FROM KNOWLEDGE BASE ===\n")
            for i, source in enumerate(rag_sources, 1):
                formatted.append(f"\n--- Research {i} ---")
                formatted.append(f"Title: {source.get('title', 'N/A')}")
                formatted.append(f"Content:\n{source.get('content', '')}\n")
        
        if web_sources:
            formatted.append("\n=== MARKET DATA FROM WEB SEARCH ===\n")
            for i, source in enumerate(web_sources, 1):
                formatted.append(f"\n--- Source {i} ---")
                formatted.append(f"Title: {source.get('title', 'N/A')}")
                formatted.append(f"URL: {source.get('url', 'N/A')}")
                formatted.append(f"Snippet: {source.get('snippet', '')}\n")
        
        if scraped_sources or competitor_data:
            formatted.append("\n=== DETAILED COMPETITOR DATA ===\n")
            all_competitor_data = scraped_sources + competitor_data
            for i, source in enumerate(all_competitor_data, 1):
                competitor = source.get('competitor', 'Unknown')
                formatted.append(f"\n--- Competitor: {competitor} ---")
                formatted.append(f"URL: {source.get('url', 'N/A')}")
                formatted.append(f"Content:\n{source.get('content', '')[:2000]}\n")  # Limit to 2000 chars
        
        return "\n".join(formatted)
    
    async def _generate_response(
        self,
        brief_context: Dict[str, str],
        context: str
    ) -> str:
        """Generate LLM response with all context"""
        target_brand = brief_context.get("brand_name", "the target brand")
        prompt = f"""Analyze the competitive market landscape for this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

RETRIEVED MARKET DATA FROM MULTIPLE SOURCES:
{context}

Provide comprehensive market landscape analysis in the structured markdown format specified in your system message.

CRITICAL REQUIREMENTS:
1. Create detailed competitor comparison tables (COMPANY, PRODUCT, SEGMENTS, DISTRIBUTION)
2. Create summary table (COMPANY, SUMMARY, STRATEGIC FOCUS)
3. Include specific competitor names, products, pricing, positioning
4. Extract quantitative data (market share, pricing, metrics)
5. Identify whitespace opportunities and positioning gaps
6. Provide actionable strategic recommendations
7. Never include {target_brand} itself in competitor lists or competitor tables.

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
            if not key.startswith('_'):
                lines.append(f"- {key.title()}: {value}")
        return '\n'.join(lines)
    
    def _evaluate_response(self, response: str, market_context: Dict[str, str]) -> float:
        """Evaluate quality of generated response"""
        response_lower = response.lower()
        
        # Check for tables
        has_tables = '|' in response and '---' in response
        table_score = 1.0 if has_tables else 0.3
        
        # Check for competitor names
        has_competitors = sum(1 for word in response.split() if word.istitle()) > 10
        competitor_score = 1.0 if has_competitors else 0.5
        
        # Check for positioning/strategy content
        required_sections = ['positioning', 'whitespace', 'strategy', 'recommendation']
        section_score = sum(1 for section in required_sections if section in response_lower) / len(required_sections)
        
        # Check for market analysis depth
        has_depth = len(response) > 2000
        depth_score = 1.0 if has_depth else 0.7
        
        # Combined quality score
        quality = (table_score + competitor_score + section_score + depth_score) / 4
        
        return quality
