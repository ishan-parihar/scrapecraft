"""
Simple Working Search Agent
A basic search agent that provides multi-engine search capabilities.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from urllib.parse import urlencode, quote_plus, unquote
import sys
import os

# Add path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../../..'))

from app.agents.base.osint_agent import OSINTAgent, LLMOSINTAgent, AgentConfig, AgentResult


class SimpleSearchAgent(OSINTAgent):
    """
    Simple multi-engine search agent with basic functionality.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        if config is None:
            config = AgentConfig(
                role="Simple Search Specialist",
                description="Performs basic multi-engine web searches",
                timeout=30,
                max_retries=2
            )
        super().__init__(config)
        
        self.search_engines = ['duckduckgo', 'brave']
        self.max_results = 10
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input for search."""
        if not input_data:
            return False
        
        query = (
            input_data.get("query") or 
            input_data.get("user_request") or 
            input_data.get("search_query") or
            input_data.get("request")
        )
        
        return bool(query and len(query.strip()) >= 3)
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        return "You are a simple search agent that performs web searches across multiple engines."
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """Process output from search execution."""
        return raw_output
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """Execute search using available engines."""
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
                    error_message="No search query provided"
                )
            
            self.logger.info(f"Executing search for: {query}")
            
            # Perform search
            search_results = await self._perform_search(query)
            
            return AgentResult(
                success=True,
                data=search_results,
                metadata={
                    "agent_id": "simple_search_agent",
                    "query": query,
                    "engines_used": search_results.get("engines_used", []),
                    "total_results": len(search_results.get("results", [])),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return AgentResult(
                success=False,
                data={},
                error_message=f"Search execution failed: {str(e)}"
            )
    
    async def _perform_search(self, query: str) -> Dict[str, Any]:
        """Perform search using DuckDuckGo HTML search."""
        results = []
        engines_used = []
        
        try:
            # DuckDuckGo search
            ddg_results = await self._search_duckduckgo(query)
            if ddg_results:
                results.extend(ddg_results)
                engines_used.append("duckduckgo")
        except Exception as e:
            self.logger.warning(f"DuckDuckGo search failed: {e}")
        
        try:
            # Brave search
            brave_results = await self._search_brave(query)
            if brave_results:
                results.extend(brave_results)
                engines_used.append("brave")
        except Exception as e:
            self.logger.warning(f"Brave search failed: {e}")
        
        # Remove duplicates
        results = self._deduplicate_results(results)
        
        return {
            "query": query,
            "results": results[:self.max_results],
            "total_results": len(results),
            "engines_used": engines_used,
            "search_time": 0.0,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _search_duckduckgo(self, query: str) -> List[Dict[str, Any]]:
        """Search DuckDuckGo with improved HTML parsing."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {'q': query}
                url = f"https://duckduckgo.com/html/?{urlencode(params)}"
                
                async with session.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }) as response:
                    html = await response.text()
                    
                    # Improved HTML parsing
                    results = []
                    import re
                    
                    # Pattern to extract result__a links ( DuckDuckGo's main result class )
                    pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>(.*?)(?=<a[^>]*class="result__a"|</div>|$)'
                    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
                    
                    for match in matches:
                        if len(match) >= 2:
                            url = match[0]
                            title = re.sub(r'<[^>]*>', '', match[1]).strip()
                            description = ""
                            
                            # Extract description from the following content
                            if len(match) > 2:
                                following_content = match[2]
                                # Look for snippet content
                                snippet_match = re.search(r'class="result__snippet"[^>]*>(.*?)</a>', following_content, re.IGNORECASE)
                                if snippet_match:
                                    description = re.sub(r'<[^>]*>', '', snippet_match.group(1)).strip()
                                else:
                                    # Try to extract any text content as description
                                    text_content = re.sub(r'<[^>]*>', '', following_content).strip()
                                    if text_content and len(text_content) > 20:
                                        description = text_content[:300]
                            
                            # Clean up title and description
                            title = re.sub(r'\s+', ' ', title)
                            title = title.replace('&amp;', '&').replace('&#x27;', "'").replace('&quot;', '"')
                            
                            if description:
                                description = re.sub(r'\s+', ' ', description)
                                description = description.replace('&amp;', '&').replace('&#x27;', "'").replace('&quot;', '"')
                                description = description[:300]  # Limit length
                            
                            # Handle DuckDuckGo redirect URLs
                            if url.startswith('//duckduckgo.com/l/'):
                                # Extract the real URL from the redirect
                                import urllib.parse
                                real_url_match = re.search(r'uddg=([^&]*)', url)
                                if real_url_match:
                                    url = urllib.parse.unquote(real_url_match.group(1))
                            elif url.startswith('/'):
                                url = f"https://duckduckgo.com{url}"
                            elif not url.startswith('http'):
                                url = f"https://{url}"
                            
                            # Validate URL and title
                            if url.startswith('http') and title and len(title) > 3:
                                # Avoid DuckDuckGo internal links
                                if not any(skip in url.lower() for skip in ['duckduckgo.com', 'html?q=', 'search']):
                                    results.append({
                                        "title": title,
                                        "url": url,
                                        "description": description,
                                        "source": "duckduckgo",
                                        "relevance_score": 0.8
                                    })
                    
                    # If still no results, try alternative pattern
                    if not results:
                        alt_pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>'
                        alt_matches = re.findall(alt_pattern, html, re.IGNORECASE)
                        
                        for url, title in alt_matches[:self.max_results]:
                            title = re.sub(r'<[^>]*>', '', title).strip()
                            title = title.replace('&amp;', '&').replace('&#x27;', "'").replace('&quot;', '"')
                            
                            # Handle DuckDuckGo redirect URLs
                            if url.startswith('//duckduckgo.com/l/'):
                                import urllib.parse
                                real_url_match = re.search(r'uddg=([^&]*)', url)
                                if real_url_match:
                                    url = urllib.parse.unquote(real_url_match.group(1))
                            elif not url.startswith('http'):
                                continue
                            
                            if (url.startswith('http') and title and len(title) > 5 and 
                                not any(skip in url.lower() for skip in ['duckduckgo', 'html', 'search'])):
                                results.append({
                                    "title": title,
                                    "url": url,
                                    "description": "",
                                    "source": "duckduckgo",
                                    "relevance_score": 0.7
                                })
                    
                    return results[:self.max_results]
                    
        except Exception as e:
            self.logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    async def _search_brave(self, query: str) -> List[Dict[str, Any]]:
        """Search Brave."""
        try:
            async with aiohttp.ClientSession() as session:
                params = {'q': query}
                url = f"https://search.brave.com/search?{urlencode(params)}"
                
                async with session.get(url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }) as response:
                    html = await response.text()
                    
                    # Simple HTML parsing
                    results = []
                    import re
                    
                    # Find result blocks
                    result_pattern = r'<div[^>]*data-type="web"[^>]*>.*?</div>'
                    matches = re.findall(result_pattern, html, re.DOTALL)
                    
                    for match in matches[:self.max_results]:
                        # Extract title and URL
                        title_match = re.search(r'<h3[^>]*>.*?<a[^>]*>(.*?)</a>', match, re.IGNORECASE)
                        url_match = re.search(r'href="([^"]*)"', match)
                        
                        if title_match and url_match:
                            title = re.sub(r'<[^>]*>', '', title_match.group(1)).strip()
                            url = url_match.group(1)
                            
                            results.append({
                                "title": title,
                                "url": url,
                                "description": "",
                                "source": "brave",
                                "relevance_score": 0.8
                            })
                    
                    return results
                    
        except Exception as e:
            self.logger.error(f"Brave search error: {e}")
            return []
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results