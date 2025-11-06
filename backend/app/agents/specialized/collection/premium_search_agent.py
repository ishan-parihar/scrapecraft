"""
Premium Search Agent - Advanced search capabilities without API dependencies
Integrates with PremiumScrapingService for high-quality search results
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
import logging

from app.agents.base.osint_agent import OSINTAgent, AgentConfig, AgentResult
from app.services.premium_scraping_service import PremiumScrapingService, EngineType

logger = logging.getLogger(__name__)

class PremiumSearchAgent(OSINTAgent):
    """
    Advanced search agent that scrapes premium search engines without APIs
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        default_config = AgentConfig(
            role="Premium Search Specialist",
            description="Advanced search agent that scrapes premium search engines without API dependencies",
            timeout=60,
            retry_attempts=3,
            verbose=True
        )
        
        super().__init__(config or default_config)
        self.scraping_service = None
        
    async def _initialize(self):
        """Initialize the scraping service"""
        self.scraping_service = PremiumScrapingService()
        logger.info(f"Agent initialized with role: {self.config.role}")

    async def _search_with_strategy(self, query: str, engines: List[str], 
                                   use_browser: bool = False, max_pages: int = 1) -> List[Dict[str, Any]]:
        """
        Execute search with optimal strategy based on query and engines
        """
        if not self.scraping_service:
            await self._initialize()
        
        # Convert string engine names to EngineType enum
        engine_types = []
        for engine in engines:
            try:
                engine_type = EngineType(engine.lower())
                engine_types.append(engine_type)
            except ValueError:
                logger.warning(f"Unknown engine: {engine}")
        
        if not engine_types:
            engine_types = [EngineType.DUCKDUCKGO, EngineType.BRAVE]
        
        # Choose search strategy
        if len(engine_types) == 1:
            # Single engine search
            results = await self.scraping_service.search_engine(
                engine_types[0], query, max_pages=max_pages, use_browser=use_browser
            )
        else:
            # Multi-engine concurrent search
            results = await self.scraping_service.multi_engine_search(
                query, engine_types, use_browser=use_browser
            )
        
        return results

    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute premium search with advanced capabilities
        
        Expected input_data:
        - query: Search query string
        - engines: List of engine names (optional, default: ["duckduckgo", "brave"])
        - max_pages: Number of pages to scrape (optional, default: 1)
        - use_browser: Whether to use browser automation (optional, default: False)
        - investigation_id: Investigation ID for context (optional)
        """
        start_time = time.time()
        
        try:
            # Extract parameters
            query = input_data.get("query", "").strip()
            engines = input_data.get("engines", ["duckduckgo", "brave"])
            max_pages = input_data.get("max_pages", 1)
            use_browser = input_data.get("use_browser", False)
            investigation_id = input_data.get("investigation_id")
            
            # Validate query
            if not query:
                return AgentResult(
                    success=False,
                    data={},
                    error="Search query is required",
                    execution_time=time.time() - start_time
                )
            
            logger.info(f"Executing premium search: '{query}' on engines {engines}")
            
            # Execute search
            results = await self._search_with_strategy(
                query, engines, use_browser=use_browser, max_pages=max_pages
            )
            
            if not results:
                return AgentResult(
                    success=False,
                    data={"query": query, "engines": engines},
                    error="No results found",
                    execution_time=time.time() - start_time
                )
            
            # Enhance results with metadata
            enhanced_results = []
            for result in results:
                enhanced_result = {
                    **result,
                    "investigation_id": investigation_id,
                    "agent_id": self.config.agent_id,
                    "query_hash": self._hash_query(query),
                    "collection_method": "premium_scraping",
                    "quality_score": self.scraping_service._assess_quality(result),
                    "extracted_entities": self._extract_entities(result),
                    "content_type": self.scraping_service._classify_content(result),
                    "timestamp_collected": time.time()
                }
                enhanced_results.append(enhanced_result)
            
            # Create summary statistics
            engine_stats = {}
            for result in enhanced_results:
                engine = result.get("engine", "unknown")
                if engine not in engine_stats:
                    engine_stats[engine] = {"count": 0, "avg_relevance": 0}
                engine_stats[engine]["count"] += 1
                engine_stats[engine]["avg_relevance"] += result.get("relevance_score", 0)
            
            # Calculate averages
            for stats in engine_stats.values():
                if stats["count"] > 0:
                    stats["avg_relevance"] /= stats["count"]
            
            summary = {
                "query": query,
                "engines_used": engines,
                "total_results": len(enhanced_results),
                "engine_statistics": engine_stats,
                "average_relevance": sum(r.get("relevance_score", 0) for r in enhanced_results) / len(enhanced_results),
                "quality_distribution": self._analyze_quality_distribution(enhanced_results),
                "content_types": self._analyze_content_types(enhanced_results),
                "search_method": "browser_automation" if use_browser else "http_requests",
                "pages_scraped": max_pages,
                "execution_time": time.time() - start_time
            }
            
            return AgentResult(
                success=True,
                data={
                    "results": enhanced_results,
                    "summary": summary,
                    "metadata": {
                        "agent_version": "1.0.0",
                        "scraping_method": "advanced",
                        "anti_detection": True,
                        "rate_limited": True
                    }
                },
                confidence=0.85,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Premium search failed: {e}")
            return AgentResult(
                success=False,
                data={"query": input_data.get("query", "")},
                error=f"Search execution failed: {str(e)}",
                execution_time=time.time() - start_time
            )

    def _hash_query(self, query: str) -> str:
        """Create hash for query identification"""
        import hashlib
        return hashlib.md5(query.encode()).hexdigest()[:8]

    def _assess_quality(self, result: Dict[str, Any]) -> float:
        """Assess quality of individual result"""
        quality = 0.0
        
        # Base relevance
        quality += result.get("relevance_score", 0) * 0.4
        
        # Title quality
        title = result.get("title", "")
        if len(title) > 20 and len(title) < 100:
            quality += 0.2
        
        # Snippet quality
        snippet = result.get("snippet", "")
        if len(snippet) > 50:
            quality += 0.2
        
        # URL quality
        url = result.get("url", "")
        if url.startswith("https://"):
            quality += 0.1
        
        # Trusted sources
        trusted_domains = ["wikipedia.org", "github.com", "stackoverflow.com", "reddit.com", 
                          "medium.com", "nytimes.com", "bbc.com", "cnn.com"]
        if any(domain in url for domain in trusted_domains):
            quality += 0.1
        
        return min(quality, 1.0)

    def _extract_entities(self, result: Dict[str, Any]) -> List[str]:
        """Extract basic entities from result"""
        entities = []
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        combined = f"{title} {snippet}"
        
        # Simple entity extraction (basic patterns)
        import re
        
        # Years
        years = re.findall(r'\b(19|20)\d{2}\b', combined)
        entities.extend([f"year:{year}" for year in years])
        
        # Money amounts
        money = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', combined)
        entities.extend([f"money:{amount}" for amount in money])
        
        # Common tech terms
        tech_terms = ["api", "python", "javascript", "machine learning", "ai", "data", "security"]
        for term in tech_terms:
            if term in combined:
                entities.append(f"tech:{term}")
        
        return list(set(entities))

    def _classify_content(self, result: Dict[str, Any]) -> str:
        """Classify content type of result"""
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        url = result.get("url", "").lower()
        combined = f"{title} {snippet} {url}"
        
        # Classification patterns
        if any(term in combined for term in ["wikipedia", "wiki"]):
            return "encyclopedia"
        elif any(term in combined for term in ["github", "gitlab", "bitbucket"]):
            return "code_repository"
        elif any(term in combined for term in ["stack overflow", "stackoverflow"]):
            return "qa_forum"
        elif any(term in combined for term in ["news", "article", "blog"]):
            return "news_article"
        elif any(term in combined for term in ["pdf", "document", "paper"]):
            return "document"
        elif any(term in combined for term in ["video", "youtube", "vimeo"]):
            return "video"
        elif any(term in combined for term in ["shopping", "buy", "price", "amazon"]):
            return "ecommerce"
        else:
            return "general"

    def _analyze_quality_distribution(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of quality scores"""
        distribution = {"high": 0, "medium": 0, "low": 0}
        
        for result in results:
            quality = result.get("quality_score", 0)
            if quality >= 0.7:
                distribution["high"] += 1
            elif quality >= 0.4:
                distribution["medium"] += 1
            else:
                distribution["low"] += 1
        
        return distribution

    def _analyze_content_types(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze distribution of content types"""
        type_counts = {}
        
        for result in results:
            content_type = result.get("content_type", "general")
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        
        return type_counts

    async def test_connectivity(self) -> Dict[str, bool]:
        """Test connectivity to search engines"""
        if not self.scraping_service:
            await self._initialize()
        
        return await self.scraping_service.test_engines()

    async def get_supported_engines(self) -> List[str]:
        """Get list of supported search engines"""
        return [engine.value for engine in EngineType]

    async def __aenter__(self):
        await self._initialize()
        return self

    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent"""
        return "You are an advanced search agent that scrapes premium search engines without using APIs."

    def _process_output(self, raw_output: Any) -> Dict[str, Any]:
        """Process raw output from the agent"""
        return raw_output if isinstance(raw_output, dict) else {"output": raw_output}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data"""
        return "query" in input_data and isinstance(input_data["query"], str)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.scraping_service:
            await self.scraping_service.__aexit__(exc_type, exc_val, exc_tb)