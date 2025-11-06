"""
Real Search Engine Integration Service
Provides actual search functionality using multiple search engines.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote_plus
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

class RealSearchService:
    """
    Service for performing actual web searches using various search engines.
    """
    
    def __init__(self):
        self.session = None
        self.rate_limiters = {
            'google': {'last_request': 0, 'min_delay': 1.0},
            'bing': {'last_request': 0, 'min_delay': 1.0},
            'duckduckgo': {'last_request': 0, 'min_delay': 0.5}
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self, engine: str):
        """Apply rate limiting for search engines."""
        if engine in self.rate_limiters:
            limiter = self.rate_limiters[engine]
            time_since_last = asyncio.get_event_loop().time() - limiter['last_request']
            if time_since_last < limiter['min_delay']:
                await asyncio.sleep(limiter['min_delay'] - time_since_last)
            limiter['last_request'] = asyncio.get_event_loop().time()
    
    async def search_google(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using Google Custom Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not settings.GOOGLE_SEARCH_API_KEY or not settings.GOOGLE_SEARCH_ENGINE_ID:
            logger.warning("Google Search API credentials not configured")
            return await self._fallback_search(query, max_results, "google")
        
        await self._rate_limit('google')
        
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                'key': settings.GOOGLE_SEARCH_API_KEY,
                'cx': settings.GOOGLE_SEARCH_ENGINE_ID,
                'q': query,
                'num': min(max_results, 10),  # Google API limit
                'fields': 'items(title,link,snippet,pagemap/metatags,formattedUrl,displayLink)'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('items', []):
                        result = {
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'display_url': item.get('formattedUrl', item.get('link', '')),
                            'domain': item.get('displayLink', ''),
                            'source': 'google',
                            'position': len(results) + 1,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        
                        # Extract additional metadata if available
                        metatags = item.get('pagemap', {}).get('metatags', [{}])
                        if metatags:
                            result['meta_description'] = metatags[0].get('og:description', '') or metatags[0].get('description', '')
                        
                        results.append(result)
                    
                    logger.info(f"Google search returned {len(results)} results for query: {query}")
                    return results
                    
                else:
                    logger.error(f"Google Search API error: {response.status}")
                    return await self._fallback_search(query, max_results, "google")
                    
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return await self._fallback_search(query, max_results, "google")
    
    async def search_bing(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using Bing Search API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not settings.BING_SEARCH_API_KEY:
            logger.warning("Bing Search API key not configured")
            return await self._fallback_search(query, max_results, "bing")
        
        await self._rate_limit('bing')
        
        try:
            url = "https://api.bing.microsoft.com/v7.0/search"
            params = {
                'q': query,
                'count': min(max_results, 50),  # Bing API limit
                'offset': 0,
                'mkt': 'en-US',
                'safesearch': 'Moderate'
            }
            
            headers = {'Ocp-Apim-Subscription-Key': settings.BING_SEARCH_API_KEY}
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = []
                    
                    for item in data.get('webPages', {}).get('value', []):
                        result = {
                            'title': item.get('name', ''),
                            'url': item.get('url', ''),
                            'snippet': item.get('snippet', ''),
                            'display_url': item.get('displayUrl', item.get('url', '')),
                            'domain': item.get('url', '').split('/')[2] if '/' in item.get('url', '') else '',
                            'source': 'bing',
                            'position': len(results) + 1,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                        results.append(result)
                    
                    logger.info(f"Bing search returned {len(results)} results for query: {query}")
                    return results
                    
                else:
                    logger.error(f"Bing Search API error: {response.status}")
                    return await self._fallback_search(query, max_results, "bing")
                    
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            return await self._fallback_search(query, max_results, "bing")
    
    async def search_duckduckgo(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo (no API key required).
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not settings.DUCKDUCKGO_ENABLED:
            return []
        
        # Ensure session exists
        if not hasattr(self, 'session') or self.session is None:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={'User-Agent': settings.USER_AGENT}
            )
        
        await self._rate_limit('duckduckgo')
        
        try:
            # Use DuckDuckGo's HTML version (no API required)
            url = "https://html.duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en',
                'num': min(max_results, 30)
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status in [200, 202]:  # Accept both 200 and 202 as success
                    html = await response.text()
                    return await self._parse_duckduckgo_results(html, max_results)
                else:
                    logger.error(f"DuckDuckGo search error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return []
    
    async def _parse_duckduckgo_results(self, html: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo HTML results."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            # Find result containers
            result_divs = soup.find_all('div', class_='result')
            
            for i, div in enumerate(result_divs[:max_results]):
                title_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')
                
                if title_tag:
                    # Handle DuckDuckGo redirect URLs
                    href = title_tag.get('href', '')
                    if href.startswith('//duckduckgo.com/l/'):
                        # This is a redirect - extract the real URL
                        import urllib.parse
                        parsed = urllib.parse.urlparse('https:' + href)
                        query_params = urllib.parse.parse_qs(parsed.query)
                        uddg = query_params.get('uddg', [''])[0]
                        if uddg:
                            real_url = uddg
                        else:
                            real_url = href
                    else:
                        real_url = href
                    
                    result = {
                        'title': title_tag.get_text(strip=True),
                        'url': real_url,
                        'snippet': snippet_tag.get_text(strip=True) if snippet_tag else '',
                        'display_url': real_url,
                        'domain': real_url.split('/')[2] if '/' in real_url and real_url.startswith('http') else '',
                        'source': 'duckduckgo',
                        'position': i + 1,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    results.append(result)
            
            logger.info(f"DuckDuckGo search returned {len(results)} results")
            return results
            
        except ImportError:
            logger.warning("BeautifulSoup not available for DuckDuckGo parsing")
            return []
        except Exception as e:
            logger.error(f"Failed to parse DuckDuckGo results: {e}")
            return []
    
    async def _fallback_search(self, query: str, max_results: int, engine: str) -> List[Dict[str, Any]]:
        """
        Fallback search using DuckDuckGo when primary APIs fail.
        """
        logger.info(f"Using fallback search for {engine}")
        if settings.DUCKDUCKGO_ENABLED:
            return await self.search_duckduckgo(query, max_results)
        else:
            # Last resort - return empty but realistic structure
            return []
    
    async def multi_search(self, query: str, engines: List[str] = None, max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across multiple engines concurrently.
        
        Args:
            query: Search query
            engines: List of engines to use (google, bing, duckduckgo)
            max_results: Maximum results per engine
            
        Returns:
            Dictionary with engine names as keys and result lists as values
        """
        if engines is None:
            engines = ['duckduckgo']  # Default to DuckDuckGo since it doesn't require API keys
        
        if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_SEARCH_ENGINE_ID and 'google' not in engines:
            engines.append('google')
        if settings.BING_SEARCH_API_KEY and 'bing' not in engines:
            engines.append('bing')
        
        tasks = []
        for engine in engines:
            if engine == 'google':
                tasks.append(self.search_google(query, max_results))
            elif engine == 'bing':
                tasks.append(self.search_bing(query, max_results))
            elif engine == 'duckduckgo':
                tasks.append(self.search_duckduckgo(query, max_results))
        
        results = {}
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(task_results):
                engine = engines[i]
                if isinstance(result, Exception):
                    logger.error(f"Search failed for {engine}: {result}")
                    results[engine] = []
                else:
                    results[engine] = result
        
        return results


async def perform_search(query: str, engines: List[str] = None, max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function to perform a search.
    
    Args:
        query: Search query
        engines: List of search engines to use
        max_results: Maximum results per engine
        
    Returns:
        Dictionary with search results by engine
    """
    async with RealSearchService() as search_service:
        return await search_service.multi_search(query, engines, max_results)