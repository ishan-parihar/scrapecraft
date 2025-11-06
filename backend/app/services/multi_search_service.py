"""
Enhanced Search Service with Multi-Engine Support
Provides access to multiple search engines and data sources
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
from urllib.parse import urlencode, quote_plus

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from bs4 import BeautifulSoup


@dataclass
class SearchResult:
    """Individual search result."""
    title: str
    url: str
    description: str
    source: str
    relevance_score: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class SearchResponse:
    """Complete search response."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time: float
    engine: str
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class MultiSearchEngine:
    """
    Advanced multi-engine search service that combines results from multiple sources.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.session = None
        
        # Search engine configurations
        self.engines = {
            'duckduckgo': {
                'url': 'https://duckduckgo.com/html/',
                'enabled': True,
                'rate_limit': 1.0,  # seconds between requests
                'last_request': None
            },
            'brave': {
                'url': 'https://search.brave.com/search',
                'enabled': True,
                'rate_limit': 1.0,
                'last_request': None
            },
            'startpage': {
                'url': 'https://www.startpage.com/do/search',
                'enabled': True,
                'rate_limit': 1.5,
                'last_request': None
            },
            'qwant': {
                'url': 'https://www.qwant.com/',
                'enabled': True,
                'rate_limit': 1.0,
                'last_request': None
            }
        }
        
        # API-based engines (require API keys)
        self.api_engines = {
            'google': {
                'enabled': bool(self.config.get('GOOGLE_SEARCH_API_KEY')),
                'api_key': self.config.get('GOOGLE_SEARCH_API_KEY'),
                'search_engine_id': self.config.get('GOOGLE_SEARCH_ENGINE_ID'),
                'rate_limit': 0.1,
                'last_request': None
            },
            'bing': {
                'enabled': bool(self.config.get('BING_SEARCH_API_KEY')),
                'api_key': self.config.get('BING_SEARCH_API_KEY'),
                'rate_limit': 0.1,
                'last_request': None
            }
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def search(
        self, 
        query: str,
        engines: Optional[List[str]] = None,
        max_results: int = 20,
        deduplicate: bool = True
    ) -> Dict[str, Any]:
        """
        Search across multiple engines simultaneously.
        
        Args:
            query: Search query
            engines: List of engines to use (None for all enabled)
            max_results: Maximum results per engine
            deduplicate: Whether to deduplicate results
            
        Returns:
            Combined search results with metadata
        """
        if not self.session:
            raise RuntimeError("MultiSearchEngine must be used as async context manager")
        
        start_time = datetime.utcnow()
        
        # Determine which engines to use
        if engines is None:
            engines = [name for name, config in self.engines.items() if config['enabled']]
            engines.extend([name for name, config in self.api_engines.items() if config['enabled']])
        
        # Search all engines concurrently
        search_tasks = []
        for engine in engines:
            if engine in self.engines and self.engines[engine]['enabled']:
                search_tasks.append(self._search_web_engine(engine, query, max_results))
            elif engine in self.api_engines and self.api_engines[engine]['enabled']:
                search_tasks.append(self._search_api_engine(engine, query, max_results))
        
        # Wait for all searches to complete
        engine_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        
        # Process results
        all_results = []
        successful_engines = []
        failed_engines = []
        
        for i, result in enumerate(engine_results):
            engine_name = engines[i]
            
            if isinstance(result, Exception):
                self.logger.error(f"Search engine {engine_name} failed: {result}")
                failed_engines.append(engine_name)
                continue
            
            if result and result.results:
                all_results.extend(result.results)
                successful_engines.append(engine_name)
        
        # Deduplicate results if requested
        if deduplicate:
            all_results = self._deduplicate_results(all_results)
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit total results
        final_results = all_results[:max_results * len(successful_engines)]
        
        search_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            'query': query,
            'results': [self._serialize_result(r) for r in final_results],
            'total_results': len(final_results),
            'search_time': search_time,
            'engines_used': successful_engines,
            'failed_engines': failed_engines,
            'deduplication_enabled': deduplicate,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _search_web_engine(self, engine: str, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search a web-based search engine."""
        engine_config = self.engines[engine]
        
        # Rate limiting
        if engine_config['last_request']:
            time_since_last = datetime.utcnow() - engine_config['last_request']
            if time_since_last.total_seconds() < engine_config['rate_limit']:
                await asyncio.sleep(engine_config['rate_limit'] - time_since_last.total_seconds())
        
        try:
            if engine == 'duckduckgo':
                results = await self._search_duckduckgo(query, max_results)
            elif engine == 'brave':
                results = await self._search_brave(query, max_results)
            elif engine == 'startpage':
                results = await self._search_startpage(query, max_results)
            elif engine == 'qwant':
                results = await self._search_qwant(query, max_results)
            else:
                return None
            
            engine_config['last_request'] = datetime.utcnow()
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching {engine}: {e}")
            return None
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> SearchResponse:
        """Search DuckDuckGo."""
        params = {'q': query}
        url = f"https://duckduckgo.com/html/?{urlencode(params)}"
        
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result')
            
            for div in result_divs[:max_results]:
                title_tag = div.find('a', class_='result__a')
                snippet_tag = div.find('a', class_='result__snippet')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', '')
                    description = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='duckduckgo',
                        relevance_score=self._calculate_relevance(title, description, query)
                    ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=0.0,
                engine='duckduckgo'
            )
    
    async def _search_brave(self, query: str, max_results: int) -> SearchResponse:
        """Search Brave Search."""
        params = {'q': query}
        url = f"https://search.brave.com/search?{urlencode(params)}"
        
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', {'data-type': 'web'})
            
            for div in result_divs[:max_results]:
                title_tag = div.find('a')
                snippet_tag = div.find('div', class_='snippet-description')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', '')
                    description = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='brave',
                        relevance_score=self._calculate_relevance(title, description, query)
                    ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=0.0,
                engine='brave'
            )
    
    async def _search_startpage(self, query: str, max_results: int) -> SearchResponse:
        """Search Startpage."""
        params = {'query': query}
        url = f"https://www.startpage.com/do/search?{urlencode(params)}"
        
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='w-gl__result')
            
            for div in result_divs[:max_results]:
                title_tag = div.find('h3')
                link_tag = title_tag.find('a') if title_tag else None
                snippet_tag = div.find('p', class_='w-gl__description')
                
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    url = link_tag.get('href', '')
                    description = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='startpage',
                        relevance_score=self._calculate_relevance(title, description, query)
                    ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=0.0,
                engine='startpage'
            )
    
    async def _search_qwant(self, query: str, max_results: int) -> SearchResponse:
        """Search Qwant."""
        params = {'q': query, 't': 'web'}
        url = f"https://www.qwant.com/?{urlencode(params)}"
        
        async with self.session.get(url) as response:
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            results = []
            result_divs = soup.find_all('div', class_='result')
            
            for div in result_divs[:max_results]:
                title_tag = div.find('a', class_='result--web')
                snippet_tag = div.find('p', class_='result__desc')
                
                if title_tag:
                    title = title_tag.get_text(strip=True)
                    url = title_tag.get('href', '')
                    description = snippet_tag.get_text(strip=True) if snippet_tag else ''
                    
                    results.append(SearchResult(
                        title=title,
                        url=url,
                        description=description,
                        source='qwant',
                        relevance_score=self._calculate_relevance(title, description, query)
                    ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_time=0.0,
                engine='qwant'
            )
    
    async def _search_api_engine(self, engine: str, query: str, max_results: int) -> Optional[SearchResponse]:
        """Search an API-based search engine."""
        engine_config = self.api_engines[engine]
        
        # Rate limiting
        if engine_config['last_request']:
            time_since_last = datetime.utcnow() - engine_config['last_request']
            if time_since_last.total_seconds() < engine_config['rate_limit']:
                await asyncio.sleep(engine_config['rate_limit'] - time_since_last.total_seconds())
        
        try:
            if engine == 'google':
                results = await self._search_google_api(query, max_results)
            elif engine == 'bing':
                results = await self._search_bing_api(query, max_results)
            else:
                return None
            
            engine_config['last_request'] = datetime.utcnow()
            return results
            
        except Exception as e:
            self.logger.error(f"Error searching {engine} API: {e}")
            return None
    
    async def _search_google_api(self, query: str, max_results: int) -> SearchResponse:
        """Search using Google Custom Search API."""
        api_key = self.api_engines['google']['api_key']
        search_engine_id = self.api_engines['google']['search_engine_id']
        
        if not api_key or not search_engine_id:
            raise ValueError("Google API key or search engine ID not configured")
        
        params = {
            'key': api_key,
            'cx': search_engine_id,
            'q': query,
            'num': min(max_results, 10)  # Google API limit
        }
        
        url = f"https://www.googleapis.com/customsearch/v1?{urlencode(params)}"
        
        async with self.session.get(url) as response:
            data = await response.json()
            
            results = []
            for item in data.get('items', []):
                results.append(SearchResult(
                    title=item.get('title', ''),
                    url=item.get('link', ''),
                    description=item.get('snippet', ''),
                    source='google',
                    relevance_score=self._calculate_relevance(
                        item.get('title', ''), 
                        item.get('snippet', ''), 
                        query
                    )
                ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=data.get('searchInformation', {}).get('totalResults', len(results)),
                search_time=float(data.get('searchInformation', {}).get('searchTime', 0)),
                engine='google'
            )
    
    async def _search_bing_api(self, query: str, max_results: int) -> SearchResponse:
        """Search using Bing Search API."""
        api_key = self.api_engines['bing']['api_key']
        
        if not api_key:
            raise ValueError("Bing API key not configured")
        
        params = {
            'q': query,
            'count': min(max_results, 50),  # Bing API limit
            'mkt': 'en-US'
        }
        
        headers = {
            'Ocp-Apim-Subscription-Key': api_key
        }
        
        url = f"https://api.bing.microsoft.com/v7.0/search?{urlencode(params)}"
        
        async with self.session.get(url, headers=headers) as response:
            data = await response.json()
            
            results = []
            for item in data.get('webPages', {}).get('value', []):
                results.append(SearchResult(
                    title=item.get('name', ''),
                    url=item.get('url', ''),
                    description=item.get('snippet', ''),
                    source='bing',
                    relevance_score=self._calculate_relevance(
                        item.get('name', ''), 
                        item.get('snippet', ''), 
                        query
                    )
                ))
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=data.get('webPages', {}).get('totalEstimatedMatches', len(results)),
                search_time=0.0,  # Bing doesn't provide search time
                engine='bing'
            )
    
    def _calculate_relevance(self, title: str, description: str, query: str) -> float:
        """Calculate relevance score for a search result."""
        query_terms = query.lower().split()
        title_lower = title.lower()
        desc_lower = description.lower()
        
        score = 0.0
        
        # Title matches
        for term in query_terms:
            if term in title_lower:
                score += 2.0
            if term in desc_lower:
                score += 1.0
        
        # Exact query match
        if query.lower() in title_lower:
            score += 3.0
        if query.lower() in desc_lower:
            score += 1.5
        
        # Normalize score
        max_possible = len(query_terms) * 3.0 + 4.5
        return min(score / max_possible, 1.0)
    
    def _deduplicate_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate results based on URL similarity."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            # Normalize URL for comparison
            normalized_url = self._normalize_url(result.url)
            
            if normalized_url not in seen_urls:
                seen_urls.add(normalized_url)
                unique_results.append(result)
        
        return unique_results
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        # Remove protocol, www, and trailing slashes
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        url = url.rstrip('/')
        return url.lower()
    
    def _serialize_result(self, result: SearchResult) -> Dict[str, Any]:
        """Serialize SearchResult to dictionary."""
        return {
            'title': result.title,
            'url': result.url,
            'description': result.description,
            'source': result.source,
            'relevance_score': result.relevance_score,
            'timestamp': result.timestamp.isoformat()
        }


# Global instance
multi_search = MultiSearchEngine()