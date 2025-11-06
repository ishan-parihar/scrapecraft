"""
URL Discovery Agent

This agent handles intelligent URL search and relevance analysis.
Migrated from openrouter_agent.py with enhanced capabilities.
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging

from pydantic import BaseModel

from ...base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class URLResult(BaseModel):
    """Result from URL discovery with relevance analysis."""
    url: str
    title: str = ""
    description: str = ""
    relevance_score: float = 0.0
    source_type: str = "web"
    metadata: Dict[str, Any] = {}


class URLDiscoveryAgent(LLMOSINTAgent):
    """
    Agent responsible for intelligent URL discovery and relevance analysis.
    
    This agent searches for relevant URLs based on user queries and analyzes
    their relevance to the specific scraping task. Migrated functionality
    from openrouter_agent.py with enhanced analysis capabilities.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                role="URL Discovery Specialist",
                description="Finds and analyzes relevant URLs for scraping tasks",
                max_iterations=3,
                timeout=120,
                temperature=0.2
            )
        
        super().__init__(config=config, **kwargs)
        
        # Store last query for fallback URL generation
        self.last_query = ""
        
        # URL patterns and sources
        self.url_patterns = {
            'search_engines': [
                'google.com', 'bing.com', 'duckduckgo.com', 'yahoo.com'
            ],
            'social_media': [
                'twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com'
            ],
            'ecommerce': [
                'amazon.com', 'ebay.com', 'shopify.com', 'etsy.com'
            ],
            'news': [
                'cnn.com', 'bbc.com', 'reuters.com', 'ap.org'
            ],
            'professional': [
                'linkedin.com', 'indeed.com', 'glassdoor.com'
            ]
        }
        
        # Relevance factors
        self.relevance_factors = {
            'domain_authority': 0.3,
            'content_relevance': 0.4,
            'freshness': 0.2,
            'accessibility': 0.1
        }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for URL discovery."""
        required_fields = ["search_query"]
        
        for field in required_fields:
            if field not in input_data:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        search_query = input_data.get("search_query", "").strip()
        if len(search_query) < 3:
            self.logger.error("Search query too short")
            return False
        
        return True
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for URL discovery."""
        return """You are a URL Discovery Specialist for ScrapeCraft, an intelligent web scraping platform.

Your role is to:
1. Analyze user search queries to find relevant URLs
2. Evaluate URL relevance for specific scraping tasks
3. Filter and rank URLs based on relevance and quality
4. Suggest the most appropriate URLs for scraping

Key capabilities:
- Intelligent URL search and discovery
- Relevance analysis and scoring
- Domain authority assessment
- Content type identification
- Accessibility evaluation

When analyzing URLs, consider:
- How relevant is the URL to the user's specific scraping needs?
- Is the content likely to contain the desired data?
- Is the domain reputable and accessible?
- Is the content fresh and up-to-date?
- Are there any technical barriers to scraping?

Structure your response as valid JSON:
{
    "search_strategy": "description of search approach",
    "found_urls": [
        {
            "url": "complete URL",
            "title": "page title",
            "description": "brief description of content",
            "relevance_score": 0.0-1.0,
            "source_type": "web|social|ecommerce|news|professional",
            "confidence": 0.0-1.0,
            "reasoning": "why this URL is relevant"
        }
    ],
    "search_summary": {
        "total_found": number,
        "highly_relevant": number,
        "moderately_relevant": number,
        "filtered_out": number
    },
    "recommendations": ["list of recommendations for the user"],
    "next_suggestions": ["suggested follow-up queries or actions"]
}

Focus on quality over quantity. Better to provide 5 highly relevant URLs than 20 mediocre ones."""
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """Process the raw output from URL discovery."""
        try:
            # Check if this is a fallback response
            if "[This response was generated using local analysis" in raw_output:
                return self._generate_fallback_urls()
            
            # Clean and parse JSON output
            cleaned_output = self._clean_json_output(raw_output)
            
            if cleaned_output.strip().startswith('{'):
                structured_data = json.loads(cleaned_output)
            else:
                # Extract JSON from text
                json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback: generate real URLs using search service
                    structured_data = self._generate_real_urls(query=getattr(self, 'last_query', 'search query'))
            
            # Validate and enhance the response
            return self._validate_and_enhance_urls(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing URL discovery output: {e}")
            return self._generate_fallback_urls()
    
    def _clean_json_output(self, raw_output: str) -> str:
        """Clean raw output to extract valid JSON."""
        cleaned = raw_output.strip()
        
        # Remove markdown code blocks
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        # Extract JSON content
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace+1]
        
        return cleaned
    
    def _generate_real_urls(self, query: str) -> Dict[str, Any]:
        """Generate real URLs using actual search services."""
        try:
            import sys
            import os
            
            # Add backend to path
            backend_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')
            if backend_path not in sys.path:
                sys.path.insert(0, backend_path)
            
            from app.services.real_search_service import RealSearchService
            import asyncio
            
            # Run async search in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                results = loop.run_until_complete(self._perform_real_search(query))
                return results
            finally:
                loop.close()
                
        except Exception as e:
            self.logger.error(f"Real URL generation failed: {e}")
            return self._generate_fallback_urls()
    
    async def _perform_real_search(self, query: str) -> Dict[str, Any]:
        """Perform actual search using real search service."""
        try:
            async with RealSearchService() as search_service:
                # Try Google search first
                search_results = await search_service.search_google(query, max_results=10)
                
                if not search_results or "error" in search_results[0]:
                    # Fallback to DuckDuckGo
                    search_results = await search_service.search_duckduckgo(query, max_results=10)
                
                if not search_results or "error" in search_results[0]:
                    # Fallback to Bing
                    search_results = await search_service.search_bing(query, max_results=10)
                
                if search_results and "error" not in search_results[0]:
                    # Convert search results to URL discovery format
                    found_urls = []
                    for result in search_results:
                        found_urls.append({
                            "url": result.get('link', ''),
                            "title": result.get('title', ''),
                            "description": result.get('snippet', ''),
                            "relevance_score": 0.8,  # Default score
                            "source_type": "web",
                            "confidence": 0.7,
                            "reasoning": "Found via real search engine"
                        })
                    
                    return {
                        "search_strategy": "Real search engine query",
                        "found_urls": found_urls,
                        "search_summary": {
                            "total_found": len(found_urls),
                            "highly_relevant": len([u for u in found_urls if u['relevance_score'] > 0.7]),
                            "moderately_relevant": len([u for u in found_urls if 0.5 <= u['relevance_score'] <= 0.7]),
                            "filtered_out": 0
                        },
                        "recommendations": [
                            "Start with the highest relevance URL",
                            "Verify accessibility before scraping",
                            "Cross-reference information from multiple sources"
                        ],
                        "next_suggestions": [
                            "Refine search terms if needed",
                            "Consider specific domain filters",
                            "Use advanced search operators for better results"
                        ]
                    }
                else:
                    return self._generate_fallback_urls()
                    
        except Exception as e:
            self.logger.error(f"Real search failed: {e}")
            return self._generate_fallback_urls()
    
    def _validate_and_enhance_urls(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the URL discovery response."""
        enhanced = response.copy()
        
        # Ensure required fields exist
        if "found_urls" not in enhanced:
            enhanced["found_urls"] = []
        
        if "search_summary" not in enhanced:
            enhanced["search_summary"] = {
                "total_found": len(enhanced.get("found_urls", [])),
                "highly_relevant": 0,
                "moderately_relevant": 0,
                "filtered_out": 0
            }
        
        if "recommendations" not in enhanced:
            enhanced["recommendations"] = []
        
        if "next_suggestions" not in enhanced:
            enhanced["next_suggestions"] = []
        
        # Validate and enhance each URL
        validated_urls = []
        high_relevance = 0
        moderate_relevance = 0
        
        for url_data in enhanced.get("found_urls", []):
            if not isinstance(url_data, dict):
                continue
            
            # Ensure required URL fields
            url_entry = {
                "url": url_data.get("url", ""),
                "title": url_data.get("title", ""),
                "description": url_data.get("description", ""),
                "relevance_score": max(0.0, min(1.0, float(url_data.get("relevance_score", 0.5)))),
                "source_type": url_data.get("source_type", "web"),
                "confidence": max(0.0, min(1.0, float(url_data.get("confidence", 0.5)))),
                "reasoning": url_data.get("reasoning", "Relevance based on content analysis")
            }
            
            # Count relevance categories
            if url_entry["relevance_score"] >= 0.7:
                high_relevance += 1
            elif url_entry["relevance_score"] >= 0.4:
                moderate_relevance += 1
            
            validated_urls.append(url_entry)
        
        enhanced["found_urls"] = validated_urls
        enhanced["search_summary"].update({
            "total_found": len(validated_urls),
            "highly_relevant": high_relevance,
            "moderately_relevant": moderate_relevance
        })
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "processing_method": "ai_analysis"
        }
        
        return enhanced
    
    def _generate_fallback_urls(self) -> Dict[str, Any]:
        """Generate fallback URLs when processing fails."""
        return {
            "search_strategy": "Fallback URL generation",
            "found_urls": [
                {
                    "url": "https://example.com/search",
                    "title": "Search Results Page",
                    "description": "Generic search results for your query",
                    "relevance_score": 0.5,
                    "source_type": "web",
                    "confidence": 0.3,
                    "reasoning": "Fallback URL due to processing limitations"
                }
            ],
            "search_summary": {
                "total_found": 1,
                "highly_relevant": 0,
                "moderately_relevant": 1,
                "filtered_out": 0
            },
            "recommendations": [
                "Try refining your search query",
                "Check if the search service is properly configured"
            ],
            "next_suggestions": [
                "Provide more specific search terms",
                "Include domain preferences if any"
            ],
            "metadata": {
                "agent_id": self.config.agent_id,
                "fallback": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _get_required_output_fields(self) -> List[str]:
        """Get required output fields for this agent."""
        return [
            "found_urls",
            "search_summary",
            "recommendations"
        ]
    
    async def discover_urls(
        self,
        search_query: str,
        max_results: int = 10,
        source_types: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> List[URLResult]:
        """
        Discover URLs based on search query with advanced filtering.
        
        Args:
            search_query: The search query
            max_results: Maximum number of results to return
            source_types: Optional filter for source types
            exclude_domains: Optional list of domains to exclude
            
        Returns:
            List of URL results with relevance analysis
        """
        # Store query for fallback URL generation
        self.last_query = search_query
        
        # Prepare input for URL discovery
        input_data = {
            "search_query": search_query,
            "max_results": max_results,
            "source_types": source_types or [],
            "exclude_domains": exclude_domains or [],
            "request_type": "url_discovery"
        }
        
        # Execute URL discovery
        result = await self.execute(input_data)
        
        if result.success:
            response_data = result.data
            url_results = []
            
            for url_data in response_data.get("found_urls", []):
                url_result = URLResult(
                    url=url_data.get("url", ""),
                    title=url_data.get("title", ""),
                    description=url_data.get("description", ""),
                    relevance_score=url_data.get("relevance_score", 0.5),
                    source_type=url_data.get("source_type", "web"),
                    metadata={
                        "confidence": url_data.get("confidence", 0.5),
                        "reasoning": url_data.get("reasoning", ""),
                        "discovered_by": self.config.agent_id
                    }
                )
                url_results.append(url_result)
            
            return url_results
        else:
            self.logger.error(f"URL discovery failed: {result.error_message}")
            return []
    
    async def analyze_url_relevance(
        self,
        urls: List[str],
        search_query: str,
        user_context: Optional[str] = None
    ) -> List[URLResult]:
        """
        Analyze relevance of existing URLs to a search query.
        
        Args:
            urls: List of URLs to analyze
            search_query: The original search query
            user_context: Optional additional context from user
            
        Returns:
            List of URL results with relevance scores
        """
        # Prepare input for relevance analysis
        input_data = {
            "urls": urls,
            "search_query": search_query,
            "user_context": user_context or "",
            "request_type": "relevance_analysis"
        }
        
        # Execute relevance analysis
        result = await self.execute(input_data)
        
        if result.success:
            response_data = result.data
            url_results = []
            
            for url_data in response_data.get("found_urls", []):
                url_result = URLResult(
                    url=url_data.get("url", ""),
                    title=url_data.get("title", ""),
                    description=url_data.get("description", ""),
                    relevance_score=url_data.get("relevance_score", 0.5),
                    source_type=url_data.get("source_type", "web"),
                    metadata={
                        "confidence": url_data.get("confidence", 0.5),
                        "reasoning": url_data.get("reasoning", ""),
                        "analyzed_by": self.config.agent_id
                    }
                )
                url_results.append(url_result)
            
            return url_results
        else:
            self.logger.error(f"URL relevance analysis failed: {result.error_message}")
            return []
    
    def filter_urls_by_relevance(
        self,
        urls: List[URLResult],
        min_relevance: float = 0.5,
        max_results: int = 10
    ) -> List[URLResult]:
        """
        Filter URLs by relevance score and limit results.
        
        Args:
            urls: List of URL results
            min_relevance: Minimum relevance score to include
            max_results: Maximum number of results to return
            
        Returns:
            Filtered and sorted list of URL results
        """
        # Filter by relevance
        filtered = [url for url in urls if url.relevance_score >= min_relevance]
        
        # Sort by relevance (highest first)
        filtered.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit results
        return filtered[:max_results]