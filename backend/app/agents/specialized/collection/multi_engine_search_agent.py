"""
Multi-Engine Search Agent
Performs searches across multiple search engines for comprehensive results.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../../..'))

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from app.agents.base.osint_agent import OSINTAgent, AgentConfig, AgentResult
from backend.app.services.multi_search_service import MultiSearchEngine


class MultiEngineSearchAgent(OSINTAgent):
    """
    Advanced multi-engine search agent that queries multiple search engines
    and combines results for comprehensive research.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                role="Multi-Engine Search Specialist",
                description="Searches across multiple search engines simultaneously",
                timeout=60,
                max_retries=3
            )
        super().__init__(config)
        
        self.search_engines = ['duckduckgo', 'brave', 'startpage', 'qwant']
        self.max_results_per_engine = 20
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for search."""
        if not input_data:
            self.logger.error("No input data provided")
            return False
        
        # Extract query from various possible fields
        query = (
            input_data.get("query") or 
            input_data.get("user_request") or 
            input_data.get("search_query") or
            input_data.get("request")
        )
        
        if not query or len(query.strip()) < 3:
            self.logger.error("Invalid or too short search query")
            return False
        
        return True
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute multi-engine search."""
        try:
            # Extract search query
            query = (
                input_data.get("query") or 
                input_data.get("user_request") or 
                input_data.get("search_query") or
                input_data.get("request")
            )
            
            if not query:
                return AgentResult(
                    success=False,
                    data={},
                    error_message="No search query provided in input"
                )
            
            self.logger.info(f"Executing multi-engine search for: {query}")
            
            # Perform search
            async with MultiSearchEngine() as search_engine:
                search_results = await search_engine.search(
                    query=query,
                    engines=self.search_engines,
                    max_results=self.max_results_per_engine,
                    deduplicate=True
                )
            
            # Process and enhance results
            enhanced_results = self._enhance_search_results(search_results, query)
            
            return AgentResult(
                success=True,
                data=enhanced_results,
                metadata={
                    "agent_id": self.config.agent_id,
                    "search_engines_used": search_results.get("engines_used", []),
                    "total_results_found": len(enhanced_results.get("results", [])),
                    "search_time": search_results.get("search_time", 0.0),
                    "query": query,
                    "timestamp": search_results.get("timestamp")
                }
            )
            
        except Exception as e:
            self.logger.error(f"Multi-engine search failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error_message=f"Search execution failed: {str(e)}"
            )
    
    def _enhance_search_results(self, search_results: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Enhance search results with additional analysis."""
        enhanced = search_results.copy()
        
        # Add analysis metadata
        enhanced["analysis"] = {
            "query_complexity": self._analyze_query_complexity(query),
            "result_quality_score": self._calculate_result_quality(search_results.get("results", [])),
            "source_diversity": len(search_results.get("engines_used", [])),
            "content_types": self._identify_content_types(search_results.get("results", [])),
            "top_domains": self._extract_top_domains(search_results.get("results", []))
        }
        
        # Add categorized results
        enhanced["categorized_results"] = self._categorize_results(search_results.get("results", []))
        
        # Add key insights
        enhanced["key_insights"] = self._extract_key_insights(search_results.get("results", []), query)
        
        return enhanced
    
    def _analyze_query_complexity(self, query: str) -> str:
        """Analyze the complexity of the search query."""
        query_lower = query.lower()
        
        # Check for complex query indicators
        complex_indicators = [
            "and", "or", "not", "site:", "filetype:", "inurl:", 
            "intitle:", "intext:", "around:", "after:", "before:"
        ]
        
        complex_count = sum(1 for indicator in complex_indicators if indicator in query_lower)
        
        if complex_count >= 3 or len(query.split()) > 10:
            return "high"
        elif complex_count >= 1 or len(query.split()) > 5:
            return "medium"
        else:
            return "low"
    
    def _calculate_result_quality_score(self, results: List[Dict[str, Any]]) -> float:
        """Calculate quality score for search results."""
        if not results:
            return 0.0
        
        total_score = 0.0
        for result in results:
            score = 0.0
            
            # Title length (ideal: 30-100 characters)
            title_len = len(result.get("title", ""))
            if 30 <= title_len <= 100:
                score += 0.2
            elif title_len > 10:
                score += 0.1
            
            # Description length (ideal: 50-300 characters)
            desc_len = len(result.get("description", ""))
            if 50 <= desc_len <= 300:
                score += 0.2
            elif desc_len > 20:
                score += 0.1
            
            # URL quality (HTTPS, no excessive parameters)
            url = result.get("url", "")
            if url.startswith("https://"):
                score += 0.1
            if "?" not in url or url.count("?") <= 1:
                score += 0.1
            
            # Relevance score
            relevance = result.get("relevance_score", 0.0)
            score += relevance * 0.3
            
            total_score += min(score, 1.0)
        
        return total_score / len(results)
    
    def _identify_content_types(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """Identify different types of content in results."""
        content_types = {
            "news": 0,
            "academic": 0,
            "commercial": 0,
            "blog": 0,
            "government": 0,
            "organization": 0,
            "other": 0
        }
        
        for result in results:
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            
            if any(indicator in url or indicator in title for indicator in ["news", "article", "report"]):
                content_types["news"] += 1
            elif any(indicator in url for indicator in [".edu", "scholar", "academic", "research"]):
                content_types["academic"] += 1
            elif any(indicator in url for indicator in [".com", "shop", "store", "buy"]):
                content_types["commercial"] += 1
            elif any(indicator in url or indicator in title for indicator in ["blog", "post", "medium"]):
                content_types["blog"] += 1
            elif any(indicator in url for indicator in [".gov", ".org"]):
                content_types["government"] += 1
            else:
                content_types["other"] += 1
        
        return content_types
    
    def _extract_top_domains(self, results: List[Dict[str, Any]]) -> List[Dict[str, int]]:
        """Extract top domains from search results."""
        domain_counts = {}
        
        for result in results:
            url = result.get("url", "")
            domain = url.split("//")[-1].split("/")[0] if "//" in url else url.split("/")[0]
            domain = domain.replace("www.", "")
            
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Sort by count and return top 10
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        return [{"domain": domain, "count": count} for domain, count in top_domains]
    
    def _categorize_results(self, results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize search results by relevance and content type."""
        categories = {
            "high_relevance": [],
            "medium_relevance": [],
            "low_relevance": [],
            "news": [],
            "academic": [],
            "commercial": []
        }
        
        for result in results:
            relevance = result.get("relevance_score", 0.0)
            url = result.get("url", "").lower()
            title = result.get("title", "").lower()
            
            # Categorize by relevance
            if relevance >= 0.7:
                categories["high_relevance"].append(result)
            elif relevance >= 0.4:
                categories["medium_relevance"].append(result)
            else:
                categories["low_relevance"].append(result)
            
            # Categorize by content type
            if any(indicator in url or indicator in title for indicator in ["news", "article", "report"]):
                categories["news"].append(result)
            elif any(indicator in url for indicator in [".edu", "scholar", "academic", "research"]):
                categories["academic"].append(result)
            elif any(indicator in url for indicator in [".com", "shop", "store", "buy"]):
                categories["commercial"].append(result)
        
        return categories
    
    def _extract_key_insights(self, results: List[Dict[str, Any]], query: str) -> List[str]:
        """Extract key insights from search results."""
        insights = []
        
        if not results:
            return ["No search results available for analysis"]
        
        # General insights
        insights.append(f"Found {len(results)} relevant results across multiple search engines")
        
        # Top domains insight
        top_domains = self._extract_top_domains(results)
        if top_domains:
            insights.append(f"Top sources include: {', '.join([d['domain'] for d in top_domains[:3]])}")
        
        # Content type insights
        content_types = self._identify_content_types(results)
        dominant_type = max(content_types.items(), key=lambda x: x[1])
        if dominant_type[1] > 0:
            insights.append(f"Predominant content type: {dominant_type[0]} ({dominant_type[1]} results)")
        
        # Quality insight
        avg_quality = self._calculate_result_quality_score(results)
        if avg_quality > 0.7:
            insights.append("High-quality search results with relevant content")
        elif avg_quality > 0.4:
            insights.append("Moderate quality results with some relevant content")
        else:
            insights.append("Lower quality results, may need refined search query")
        
        return insights
    
    def _calculate_result_quality(self, results: List[Dict[str, Any]]) -> float:
        """Calculate overall result quality score."""
        return self._calculate_result_quality_score(results)