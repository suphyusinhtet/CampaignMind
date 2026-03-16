# tools/tool_manager.py
from typing import List, Dict, Any
try:
    from ddgs import DDGS
except Exception:
    from duckduckgo_search import DDGS
from pytrends.request import TrendReq
import requests
from bs4 import BeautifulSoup

class AgenticToolManager:
    """
    Manages multiple tools for agentic RAG:
    - RAG (vector database)
    - Web Search (DuckDuckGo)
    - Google Trends API
    - Web Scraping
    - Competitor APIs (if available)
    """
    
    def __init__(self):
        self.trends = TrendReq(hl='en-US', tz=360)
        self.search_cache = {}
    
    # ============================================================
    # TOOL 1: Web Search
    # ============================================================
    
    def web_search(
        self, 
        query: str, 
        num_results: int = 10,
        region: str = "wt-wt"
    ) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            num_results: Number of results to return
            region: Region code (wt-wt = worldwide, it-it = Italy, etc.)
            
        Returns:
            List of search results with title, link, snippet
        """
        # Check cache first
        cache_key = f"{query}_{region}"
        if cache_key in self.search_cache:
            return self.search_cache[cache_key]
        
        try:
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, region=region, max_results=num_results):
                    results.append({
                        "title": r.get("title", ""),
                        "url": r.get("link", ""),
                        "snippet": r.get("body", ""),
                        "source": "web_search"
                    })
                
                # Cache results
                self.search_cache[cache_key] = results
                return results
        except Exception as e:
            print(f"Web search error: {e}")
            return []
    
    # ============================================================
    # TOOL 2: Google Trends
    # ============================================================
    
    def get_google_trends(
        self,
        keywords: List[str],
        timeframe: str = "today 1-m",
        geo: str = ""
    ) -> Dict[str, Any]:
        """
        Get Google Trends data for keywords.
        
        Args:
            keywords: List of keywords to compare (max 5)
            timeframe: Time range (e.g., 'today 1-m', 'today 3-m', 'today 12-m')
            geo: Geographic region (e.g., 'IT' for Italy, 'US', '' for worldwide)
            
        Returns:
            Dictionary with trend data and insights
        """
        try:
            # Limit to 5 keywords (Google Trends API limit)
            keywords = keywords[:5]
            
            # Build payload
            self.trends.build_payload(keywords, cat=0, timeframe=timeframe, geo=geo)
            
            # Get interest over time
            interest_over_time = self.trends.interest_over_time()
            
            if interest_over_time.empty:
                return {"error": "No data available"}
            
            # Calculate statistics
            results = {
                "keywords": keywords,
                "timeframe": timeframe,
                "geo": geo,
                "data": {}
            }
            
            for keyword in keywords:
                if keyword in interest_over_time.columns:
                    series = interest_over_time[keyword]
                    results["data"][keyword] = {
                        "average": float(series.mean()),
                        "peak": float(series.max()),
                        "peak_date": series.idxmax().strftime("%Y-%m-%d"),
                        "current": float(series.iloc[-1]),
                        "trend": "rising" if series.iloc[-1] > series.mean() else "declining",
                        "values": series.to_dict()
                    }
            
            # Get related queries
            try:
                related_queries = self.trends.related_queries()
                results["related_queries"] = related_queries
            except:
                pass
            
            return results
        
        except Exception as e:
            print(f"Google Trends error: {e}")
            return {"error": str(e)}
    
    # ============================================================
    # TOOL 3: Web Scraping
    # ============================================================
    
    def scrape_url(self, url: str) -> Dict[str, str]:
        """
        Scrape content from a specific URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary with title, text content, links
        """
        if not url or url.strip() == '':
            return {"url": url, "error": "Empty URL provided"}
    
        if not url.startswith(('http://', 'https://')):
            return {"url": url, "error": f"Invalid URL scheme: {url}"}
            
        try:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = soup.find('title')
            title = title.get_text() if title else "No title"
            
            # Extract main content
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            return {
                "url": url,
                "title": title,
                "content": text[:5000],  # Limit to 5000 chars
                "source": "web_scrape"
            }
        
        except Exception as e:
            print(f"Scraping error for {url}: {e}")
            return {"url": url, "error": str(e)}
    
    # ============================================================
    # TOOL 4: Competitor Research
    # ============================================================
    
    def search_competitors(
        self,
        product: str,
        geography: str,
        num_results: int = 10
    ) -> List[Dict[str, str]]:
        """
        Search for competitors in a specific market.
        
        Args:
            product: Product category
            geography: Geographic market
            num_results: Number of competitors to find
            
        Returns:
            List of competitor information
        """
        queries = [
            f"{product} companies {geography}",
            f"top {product} providers {geography}",
            f"{product} market leaders {geography}",
            f"best {product} brands {geography}"
        ]
        
        all_results = []
        for query in queries:
            results = self.web_search(query, num_results=5, region=self._get_region_code(geography))
            all_results.extend(results)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for result in all_results:
            if result["url"] not in seen_urls:
                seen_urls.add(result["url"])
                unique_results.append(result)
        
        return unique_results[:num_results]
    
    def _get_region_code(self, geography: str) -> str:
        """Convert geography to DuckDuckGo region code"""
        region_map = {
            "italy": "it-it",
            "europe": "wt-wt",
            "us": "us-en",
            "uk": "uk-en",
            "global": "wt-wt"
        }
        return region_map.get(geography.lower(), "wt-wt")
    
    # ============================================================
    # TOOL 5: Search Quality Evaluation
    # ============================================================
    
    def evaluate_search_quality(
        self,
        results: List[Dict],
        required_keywords: List[str]
    ) -> float:
        """
        Evaluate the quality of search results.
        
        Args:
            results: Search results to evaluate
            required_keywords: Keywords that should appear in results
            
        Returns:
            Quality score (0.0 - 1.0)
        """
        if not results:
            return 0.0
        if not required_keywords:
            return 0.0
        
        scores = []
        for result in results:
            content = f"{result.get('title', '')} {result.get('snippet', '')} {result.get('content', '')}"
            content_lower = content.lower()
            
            # Check keyword coverage
            keyword_score = sum(1 for kw in required_keywords if kw.lower() in content_lower) / len(required_keywords)
            
            # Check content length (prefer substantial content)
            length_score = min(len(content) / 1000, 1.0)
            
            # Combined score
            scores.append((keyword_score + length_score) / 2)
        
        return sum(scores) / len(scores) if scores else 0.0
