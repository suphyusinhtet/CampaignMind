# agents/agentic_trend_agent.py
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from agents.base_agent import CampaignMindAgent
from rag.knowledge_manager import get_knowledge_manager
from tools.tool_manager import AgenticToolManager
from typing import Dict, Optional, List

class AgenticTrendAgent(CampaignMindAgent):
    """
    Agentic Trend Agent with multi-step search and self-correction.
    
    Strategy:
    1. Try RAG first (fast, curated knowledge)
    2. If RAG results poor quality → Web search
    3. If search terms detected → Google Trends API
    4. Combine all sources intelligently
    5. Self-evaluate and retry if needed
    """
    
    def __init__(self):
        super().__init__("trend_agent")
        self.knowledge_manager = get_knowledge_manager()
        self.tools = AgenticToolManager()
        self.quality_threshold = 0.6  # Minimum acceptable quality
    
    async def analyze_trends(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]] = None,
        n_results: int = 5,
        max_retries: int = 2
    ) -> str:
        """
        Agentic trend analysis with multi-tool orchestration.
        
        Process:
        1. Extract keywords from brief
        2. Query RAG
        3. Evaluate quality → If poor, web search
        4. If search behavior relevant → Google Trends
        5. Combine sources
        6. Generate response
        7. Self-evaluate → Retry if needed
        """
        print("🤖 Agentic Trend Agent starting multi-step analysis...")
        
        # Step 1: Extract relevant keywords
        keywords = self._extract_keywords(brief_context)
        print(f"   📝 Extracted keywords: {keywords}")
        
        # Step 2: Try RAG first
        print("   📚 Step 1: Querying RAG knowledge base...")
        rag_results = self._query_rag(brief_context, filters, n_results)
        
        # Step 3: Evaluate RAG quality
        rag_quality = self.tools.evaluate_search_quality(
            rag_results,
            keywords
        )
        print(f"   ✅ RAG quality score: {rag_quality:.2f}")
        
        all_sources = rag_results
        
        # Step 4: If RAG quality low, search web
        if rag_quality < self.quality_threshold:
            print(f"   ⚠️  RAG quality below threshold ({self.quality_threshold})")
            print("   🌐 Step 2: Searching web for additional data...")
            
            web_results = self._search_web(brief_context, keywords)
            all_sources.extend(web_results)
            
            new_quality = self.tools.evaluate_search_quality(all_sources, keywords)
            print(f"   ✅ Combined quality score: {new_quality:.2f}")
        
        # Step 5: If search behavior is relevant, get Google Trends
        if self._needs_search_data(brief_context):
            print("   📊 Step 3: Fetching Google Trends data...")
            trends_data = self._get_google_trends(brief_context, keywords)
            if trends_data:
                all_sources.append(trends_data)
                print(f"   ✅ Added Google Trends data for {len(trends_data.get('data', {}))} keywords")
        
        # Step 6: Format all sources for LLM
        context = self._format_all_sources(all_sources)
        
        # Step 7: Generate response
        print("   🧠 Step 4: Generating analysis...")
        response = await self._generate_response(brief_context, context)
        
        # Step 8: Self-evaluate response quality
        response_quality = self._evaluate_response(response, keywords)
        print(f"   ✅ Response quality: {response_quality:.2f}")
        
        # Step 9: Retry if quality still low
        if response_quality < self.quality_threshold and max_retries > 0:
            print(f"   🔄 Response quality low, retrying with refined strategy...")
            # Refine keywords and try again
            refined_keywords = self._refine_keywords(keywords, response)
            brief_context["_refined_keywords"] = " ".join(refined_keywords)
            return await self.analyze_trends(brief_context, filters, n_results, max_retries - 1)
        
        print("   ✅ Agentic analysis complete!")
        return response
    
    def _extract_keywords(self, brief_context: Dict[str, str]) -> List[str]:
        """Extract key search terms from brief context"""
        keywords = []
        
        # Core keywords
        if "industry" in brief_context:
            keywords.extend(brief_context["industry"].split())
        if "product" in brief_context:
            keywords.extend(brief_context["product"].split())
        if "geography" in brief_context:
            keywords.append(brief_context["geography"])
        
        # Add generic terms
        keywords.extend(["trends", "marketing", "digital"])
        
        # Remove duplicates and common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at"}
        keywords = [kw for kw in set(keywords) if kw.lower() not in stop_words]
        
        return keywords
    
    def _query_rag(
        self,
        brief_context: Dict[str, str],
        filters: Optional[Dict[str, str]],
        n_results: int
    ) -> List[Dict]:
        """Query RAG and format results"""
        query_parts = [
            brief_context.get('industry', ''),
            brief_context.get('product', ''),
            brief_context.get('audience', ''),
            'trends marketing digital'
        ]
        query = ' '.join([p for p in query_parts if p]).strip()
        
        results = self.knowledge_manager.query(
            query_text=query,
            doc_type="trends",
            filters=filters,
            n_results=n_results
        )
        
        # Format as dicts
        formatted = []
        for r in results:
            formatted.append({
                "title": r['metadata'].get('title', 'Trend Analysis'),
                "content": r['content'],
                "source": "rag_database",
                "metadata": r['metadata']
            })
        
        return formatted
    
    def _search_web(
        self,
        brief_context: Dict[str, str],
        keywords: List[str]
    ) -> List[Dict]:
        """Search web for trend data"""
        # Build search queries
        product = brief_context.get('product', 'product')
        geography = brief_context.get('geography', 'market')
        
        queries = [
            f"{product} marketing trends {geography}",
            f"digital marketing trends {product} {geography}",
            f"{product} advertising trends 2024 2025"
        ]
        
        all_results = []
        for query in queries:
            results = self.tools.web_search(query, num_results=3)
            all_results.extend(results)
        
        # Scrape top results for full content
        scraped = []
        for result in all_results[:5]:  # Limit to top 5
            scraped_content = self.tools.scrape_url(result["url"])
            if "error" not in scraped_content:
                scraped.append(scraped_content)
        
        return scraped if scraped else all_results
    
    def _get_google_trends(
        self,
        brief_context: Dict[str, str],
        keywords: List[str]
    ) -> Optional[Dict]:
        """Get Google Trends data"""
        # Build keyword list for trends
        product_text = brief_context.get('product', '').strip()
        product = product_text.split()[0] if product_text else "insurance"
        
        trend_keywords = [
            product,
            f"{product} digital",
            f"{product} online",
            f"{product} app"
        ][:5]  # Max 5 keywords
        
        geography_code = self._get_geo_code(brief_context.get('geography', ''))
        
        trends_data = self.tools.get_google_trends(
            keywords=trend_keywords,
            timeframe="today 1-m",
            geo=geography_code
        )
        
        if "error" in trends_data:
            return None
        
        # Format for inclusion
        return {
            "title": "Google Trends Analysis",
            "content": self._format_trends_data(trends_data),
            "source": "google_trends",
            "data": trends_data
        }
    
    def _get_geo_code(self, geography: str) -> str:
        """Convert geography to Google Trends geo code"""
        geo_map = {
            "italy": "IT",
            "europe": "",
            "us": "US",
            "uk": "GB"
        }
        return geo_map.get(geography.lower(), "")
    
    def _format_trends_data(self, trends_data: Dict) -> str:
        """Format Google Trends data as text"""
        lines = ["Google Trends Data:\n"]
        
        for keyword, data in trends_data.get("data", {}).items():
            lines.append(f"\nKeyword: {keyword}")
            lines.append(f"- Average interest: {data['average']:.1f}")
            lines.append(f"- Peak value: {data['peak']:.1f} (on {data['peak_date']})")
            lines.append(f"- Current value: {data['current']:.1f}")
            lines.append(f"- Trend: {data['trend']}")
        
        return "\n".join(lines)
    
    def _needs_search_data(self, brief_context: Dict[str, str]) -> bool:
        """Determine if Google Trends data would be valuable"""
        # Check if brief mentions search, SEO, or digital channels
        text = " ".join(brief_context.values()).lower()
        search_indicators = ["search", "seo", "google", "online", "digital"]
        return any(indicator in text for indicator in search_indicators)
    
    def _format_all_sources(self, sources: List[Dict]) -> str:
        """Format all sources for LLM prompt"""
        formatted = []
        
        for i, source in enumerate(sources, 1):
            source_type = source.get("source", "unknown")
            formatted.append(f"\n--- Source {i} ({source_type}) ---")
            formatted.append(f"Title: {source.get('title', 'N/A')}")
            content = source.get("content", "")
            if isinstance(content, str):
                content = content[:2500]
            formatted.append(f"Content:\n{content}\n")
        
        return "\n".join(formatted)
    
    async def _generate_response(
        self,
        brief_context: Dict[str, str],
        context: str
    ) -> str:
        """Generate LLM response with all context"""
        prompt = f"""Analyze market trends relevant to this campaign:

CAMPAIGN CONTEXT:
{self._format_brief_context(brief_context)}

RETRIEVED DATA FROM MULTIPLE SOURCES:
{context}

Provide comprehensive trend analysis in the structured markdown format specified in your system message.
Include quantitative data, sources, and actionable insights."""

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
    
    def _evaluate_response(self, response: str, keywords: List[str]) -> float:
        """Evaluate quality of generated response"""
        # Simple quality checks
        response_lower = response.lower()
        
        # Check keyword coverage
        keyword_coverage = sum(1 for kw in keywords if kw.lower() in response_lower) / len(keywords)
        
        # Check length (prefer detailed responses)
        length_score = min(len(response) / 2000, 1.0)
        
        # Check for quantitative data (numbers, percentages)
        has_numbers = any(char.isdigit() for char in response)
        number_score = 1.0 if has_numbers else 0.5
        
        # Check for sources
        has_sources = "source:" in response_lower or "google trends" in response_lower
        source_score = 1.0 if has_sources else 0.5
        
        # Combined score
        quality = (keyword_coverage + length_score + number_score + source_score) / 4
        
        return quality
    
    def _refine_keywords(self, keywords: List[str], response: str) -> List[str]:
        """Refine keywords based on previous response"""
        # Extract key terms from response that weren't in original keywords
        response_words = set(response.lower().split())
        new_keywords = keywords.copy()
        
        # Add high-value terms if found in response
        value_terms = ["platform", "channel", "engagement", "adoption", "search", "social"]
        for term in value_terms:
            if term in response_words and term not in new_keywords:
                new_keywords.append(term)
        
        return new_keywords
