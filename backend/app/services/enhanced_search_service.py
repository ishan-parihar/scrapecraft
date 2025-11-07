"""
Enhanced Search Service with Specialized Search and Result Processing
Provides advanced search capabilities including deduplication, ranking, and specialized search types.
"""

import asyncio
import hashlib
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import logging

from app.services.real_search_service import RealSearchService
from app.services.data_validation import ContentValidator
from app.config import settings

logger = logging.getLogger(__name__)

class EnhancedSearchService:
    """
    Enhanced search service with specialized search capabilities and intelligent result processing.
    """
    
    def __init__(self):
        self.content_validator = ContentValidator()
        self.domain_authority = self._load_domain_authority()
        
    def _load_domain_authority(self) -> Dict[str, float]:
        """Load domain authority scores for common domains."""
        return {
            # High authority domains
            'wikipedia.org': 9.5,
            'gov': 9.0,
            'edu': 8.8,
            'mil': 8.7,
            'org': 7.5,
            'news': 7.8,
            'bbc.com': 8.5,
            'cnn.com': 8.2,
            'reuters.com': 8.6,
            'ap.org': 8.4,
            'nasa.gov': 9.0,
            'nature.com': 8.9,
            'science.org': 8.8,
            'academic': 8.0,
            'scholar.google': 9.2,
            'arxiv.org': 8.7,
            'pubmed.ncbi.nlm': 8.9,
            # Social media
            'twitter.com': 6.5,
            'linkedin.com': 6.8,
            'facebook.com': 5.5,
            'reddit.com': 6.2,
            'youtube.com': 7.0,
            # Medium authority
            'medium.com': 6.8,
            'substack.com': 7.2,
            'github.com': 7.5,
            'stackoverflow.com': 8.1,
        }
    
    async def search_news(self, query: str, max_results: int = 10, time_range: str = "7d") -> List[Dict[str, Any]]:
        """
        Perform news-specific search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            time_range: Time range (1d, 7d, 30d, 365d)
            
        Returns:
            List of news search results
        """
        logger.info(f"Performing news search for: {query}")
        
        # Enhance query for news
        news_query = f"{query} news latest"
        
        async with RealSearchService() as search_service:
            # Use Google for news search (has better news integration)
            results = await search_service.search_google(news_query, max_results)
            
            # Filter and enhance news results
            news_results = []
            for result in results:
                if self._is_news_source(result['url']) or self._is_news_content(result):
                    # Enhance with news-specific metadata
                    result['content_type'] = 'news'
                    result['freshness_score'] = self._calculate_freshness_score(result.get('timestamp'), time_range)
                    result['news_source'] = self._extract_news_source(result['url'])
                    news_results.append(result)
            
            # Sort by relevance and freshness
            news_results.sort(key=lambda x: (x['freshness_score'], self._calculate_domain_authority(x['domain'])), reverse=True)
            
            logger.info(f"News search returned {len(news_results)} results")
            return news_results[:max_results]
    
    async def search_academic(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform academic/scholar search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of academic search results
        """
        logger.info(f"Performing academic search for: {query}")
        
        # Enhance query for academic content
        academic_query = f"{query} research study academic paper"
        
        async with RealSearchService() as search_service:
            # Try multiple engines for academic content
            multi_results = await search_service.multi_search(
                academic_query, 
                engines=['google', 'duckduckgo'], 
                max_results=max_results
            )
            
            academic_results = []
            for engine, results in multi_results.items():
                for result in results:
                    if self._is_academic_source(result['url']) or self._is_academic_content(result):
                        # Enhance with academic-specific metadata
                        result['content_type'] = 'academic'
                        result['academic_score'] = self._calculate_academic_score(result)
                        result['citation_count'] = self._estimate_citation_count(result)
                        academic_results.append(result)
            
            # Sort by academic authority
            academic_results.sort(key=lambda x: x['academic_score'], reverse=True)
            
            logger.info(f"Academic search returned {len(academic_results)} results")
            return academic_results[:max_results]
    
    async def search_images(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        Perform image search.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of image search results
        """
        logger.info(f"Performing image search for: {query}")
        
        # For now, we'll search for pages that likely contain images
        # In a full implementation, this would use specialized image search APIs
        image_query = f"{query} images gallery photo"
        
        async with RealSearchService() as search_service:
            results = await search_service.search_google(image_query, max_results)
            
            image_results = []
            for result in results:
                # Mark as image search result
                result['content_type'] = 'images'
                result['likely_images'] = True
                result['image_score'] = self._calculate_image_score(result)
                image_results.append(result)
            
            logger.info(f"Image search returned {len(image_results)} results")
            return image_results[:max_results]
    
    async def search_social_media(self, query: str, platforms: List[str] = None, max_results: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        """
        Perform social media search across platforms.
        
        Args:
            query: Search query
            platforms: List of platforms (twitter, reddit, linkedin, etc.)
            max_results: Maximum results per platform
            
        Returns:
            Dictionary with platform names as keys and result lists as values
        """
        if platforms is None:
            platforms = ['twitter', 'reddit']
        
        logger.info(f"Performing social media search for: {query} on platforms: {platforms}")
        
        results = {}
        
        if 'twitter' in platforms:
            results['twitter'] = await self._search_twitter(query, max_results)
        
        if 'reddit' in platforms:
            results['reddit'] = await self._search_reddit(query, max_results)
        
        # Add other platforms as needed
        if 'linkedin' in platforms:
            results['linkedin'] = await self._search_linkedin(query, max_results)
        
        return results
    
    async def deduplicate_and_rank(self, search_results: Dict[str, List[Dict[str, Any]]], query: str) -> List[Dict[str, Any]]:
        """
        Deduplicate and rank search results from multiple engines.
        
        Args:
            search_results: Dictionary of results by engine
            query: Original search query for relevance calculation
            
        Returns:
            Deduplicated and ranked list of results
        """
        logger.info("Deduplicating and ranking search results")
        
        # Flatten all results
        all_results = []
        for engine, results in search_results.items():
            for result in results:
                result['engines'] = [engine]
                all_results.append(result)
        
        # Deduplicate based on URL similarity
        deduplicated = self._deduplicate_results(all_results)
        
        # Calculate comprehensive scores
        for result in deduplicated:
            result.update({
                'relevance_score': self._calculate_relevance_score(result, query),
                'authority_score': self._calculate_domain_authority(result['domain']),
                'freshness_score': self._calculate_freshness_score(result.get('timestamp')),
                'quality_score': self._calculate_quality_score(result),
                'composite_score': 0.0  # Will be calculated below
            })
            
            # Calculate composite score
            result['composite_score'] = self._calculate_composite_score(result)
        
        # Sort by composite score
        deduplicated.sort(key=lambda x: x['composite_score'], reverse=True)
        
        logger.info(f"Deduplicated {len(all_results)} results to {len(deduplicated)} unique results")
        return deduplicated
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL similarity."""
        seen_urls = set()
        deduplicated = []
        
        for result in results:
            url = result['url']
            url_hash = hashlib.md5(self._normalize_url(url).encode()).hexdigest()
            
            if url_hash not in seen_urls:
                seen_urls.add(url_hash)
                deduplicated.append(result)
            else:
                # Merge engine information if this URL appeared in multiple engines
                existing = next((r for r in deduplicated if hashlib.md5(self._normalize_url(r['url']).encode()).hexdigest() == url_hash), None)
                if existing:
                    existing['engines'] = list(set(existing['engines'] + result['engines']))
                    existing['position'] = min(existing['position'], result['position'])
        
        return deduplicated
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        try:
            parsed = urlparse(url.lower())
            # Remove www prefix and trailing slashes
            netloc = parsed.netloc.replace('www.', '')
            path = parsed.path.rstrip('/')
            return f"{netloc}{path}"
        except:
            return url.lower()
    
    def _calculate_relevance_score(self, result: Dict[str, Any], query: str) -> float:
        """Calculate relevance score based on query match."""
        query_terms = query.lower().split()
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        url = result.get('url', '').lower()
        
        score = 0.0
        
        # Title matches are most important
        for term in query_terms:
            if term in title:
                score += 0.3
            if term in snippet:
                score += 0.2
            if term in url:
                score += 0.1
        
        # Exact phrase bonus
        if query.lower() in title:
            score += 0.5
        
        return min(score, 1.0)
    
    def _calculate_domain_authority(self, domain: str) -> float:
        """Calculate domain authority score."""
        if not domain:
            return 5.0
        
        # Check against known high-authority domains
        for known_domain, authority in self.domain_authority.items():
            if known_domain in domain:
                return authority
        
        # Base score for unknown domains
        base_score = 5.0
        
        # Adjust based on domain characteristics
        if domain.endswith('.gov') or domain.endswith('.edu') or domain.endswith('.mil'):
            base_score += 3.0
        elif domain.endswith('.org'):
            base_score += 1.5
        elif domain.endswith('.com'):
            base_score += 0.5
        
        # Penalty for suspicious patterns
        if any(pattern in domain for pattern in ['spam', 'ads', 'popup']):
            base_score -= 2.0
        
        return max(1.0, min(10.0, base_score))
    
    def _calculate_freshness_score(self, timestamp: str = None, time_range: str = "30d") -> float:
        """Calculate freshness score based on content age."""
        if not timestamp:
            return 5.0  # Neutral score for unknown dates
        
        try:
            content_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            now = datetime.utcnow()
            age_days = (now - content_date.replace(tzinfo=None)).days
            
            # Calculate score based on time range
            if time_range == "1d":
                return max(0.0, 10.0 - (age_days * 10))
            elif time_range == "7d":
                return max(0.0, 10.0 - (age_days * 1.4))
            elif time_range == "30d":
                return max(0.0, 10.0 - (age_days * 0.33))
            else:  # 365d or longer
                return max(0.0, 10.0 - (age_days * 0.027))
                
        except:
            return 5.0
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate content quality score."""
        score = 5.0  # Base score
        
        # Title length check
        title = result.get('title', '')
        if 10 <= len(title) <= 100:
            score += 1.0
        
        # Snippet length check
        snippet = result.get('snippet', '')
        if 50 <= len(snippet) <= 300:
            score += 1.0
        
        # Domain authority bonus
        score += (self._calculate_domain_authority(result.get('domain', '')) - 5.0) * 0.3
        
        # Content type bonuses
        content_type = result.get('content_type', '')
        if content_type in ['news', 'academic']:
            score += 1.5
        
        return max(1.0, min(10.0, score))
    
    def _calculate_composite_score(self, result: Dict[str, Any]) -> float:
        """Calculate composite score from all individual scores."""
        weights = {
            'relevance_score': 0.35,
            'authority_score': 0.25,
            'freshness_score': 0.20,
            'quality_score': 0.20
        }
        
        composite = 0.0
        for score_name, weight in weights.items():
            composite += result.get(score_name, 5.0) * weight
        
        # Bonus for appearing in multiple search engines
        engines_count = len(result.get('engines', []))
        if engines_count > 1:
            composite += 0.5 * (engines_count - 1)
        
        return min(10.0, composite)
    
    def _is_news_source(self, url: str) -> bool:
        """Check if URL is from a known news source."""
        news_domains = [
            'cnn.com', 'bbc.com', 'reuters.com', 'ap.org', 'nbcnews.com',
            'foxnews.com', 'wsj.com', 'washingtonpost.com', 'nytimes.com',
            'theguardian.com', 'news', 'cbsnews.com', 'abcnews.go.com'
        ]
        return any(domain in url.lower() for domain in news_domains)
    
    def _is_news_content(self, result: Dict[str, Any]) -> bool:
        """Check if content appears to be news-related."""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        news_keywords = [
            'breaking', 'news', 'report', 'update', 'latest', 'today',
            'yesterday', 'announced', 'according to', 'sources say'
        ]
        
        return any(keyword in title or keyword in snippet for keyword in news_keywords)
    
    def _extract_news_source(self, url: str) -> str:
        """Extract news source name from URL."""
        try:
            domain = urlparse(url).netloc
            return domain.replace('www.', '').split('.')[0].title()
        except:
            return 'Unknown'
    
    def _is_academic_source(self, url: str) -> bool:
        """Check if URL is from an academic source."""
        academic_domains = [
            'scholar.google', 'arxiv.org', 'pubmed.ncbi.nlm', 'nature.com',
            'science.org', 'academic', 'research', 'journal', 'ieee.org',
            'acm.org', 'springer', 'elsevier', 'jstor', 'ssrn.com'
        ]
        return any(domain in url.lower() for domain in academic_domains)
    
    def _is_academic_content(self, result: Dict[str, Any]) -> bool:
        """Check if content appears to be academic."""
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        academic_keywords = [
            'research', 'study', 'paper', 'journal', 'abstract', 'methodology',
            'results', 'conclusion', 'hypothesis', 'experiment', 'analysis',
            'university', 'college', 'institute', 'laboratory'
        ]
        
        return any(keyword in title or keyword in snippet for keyword in academic_keywords)
    
    def _calculate_academic_score(self, result: Dict[str, Any]) -> float:
        """Calculate academic relevance score."""
        score = 5.0
        
        # Domain authority bonus
        if self._is_academic_source(result['url']):
            score += 3.0
        
        # Content keywords
        title = result.get('title', '').lower()
        snippet = result.get('snippet', '').lower()
        
        academic_keywords = [
            'research', 'study', 'paper', 'journal', 'abstract', 'methodology',
            'results', 'conclusion', 'hypothesis', 'experiment'
        ]
        
        keyword_count = sum(1 for keyword in academic_keywords if keyword in title or keyword in snippet)
        score += min(keyword_count * 0.5, 2.0)
        
        return min(10.0, score)
    
    def _estimate_citation_count(self, result: Dict[str, Any]) -> int:
        """Estimate citation count (placeholder for real implementation)."""
        # This would typically integrate with academic APIs
        # For now, return a placeholder based on source authority
        if self._is_academic_source(result['url']):
            return 10  # Placeholder
        return 0
    
    def _calculate_image_score(self, result: Dict[str, Any]) -> float:
        """Calculate image relevance score."""
        score = 5.0
        
        # URL patterns suggesting images
        url_lower = result['url'].lower()
        if any(pattern in url_lower for pattern in ['image', 'photo', 'pic', 'gallery', 'img']):
            score += 2.0
        
        # Title keywords
        title = result.get('title', '').lower()
        if any(keyword in title for keyword in ['image', 'photo', 'picture', 'gallery']):
            score += 1.5
        
        return min(10.0, score)
    
    async def _search_twitter(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Twitter using real API integration."""
        from app.services.social_media_service import SocialMediaService
        
        async with SocialMediaService() as social_service:
            return await social_service.search_twitter(query, max_results)
    
    async def _search_reddit(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Reddit using real API integration."""
        from app.services.social_media_service import SocialMediaService
        
        async with SocialMediaService() as social_service:
            return await social_service.search_reddit(query, max_results)
    
    async def _search_linkedin(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search LinkedIn (placeholder for real API integration)."""
        # This would require LinkedIn API access
        logger.info(f"LinkedIn search not yet implemented for query: {query}")
        return []


async def perform_enhanced_search(
    query: str, 
    search_type: str = "general",
    max_results: int = 10,
    engines: List[str] = None,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Convenience function for enhanced search.
    
    Args:
        query: Search query
        search_type: Type of search (general, news, academic, images, social)
        max_results: Maximum number of results
        engines: List of search engines to use
        **kwargs: Additional parameters for specific search types
        
    Returns:
        List of enhanced search results
    """
    enhanced_service = EnhancedSearchService()
    
    if search_type == "news":
        return await enhanced_service.search_news(query, max_results, kwargs.get('time_range', '7d'))
    elif search_type == "academic":
        return await enhanced_service.search_academic(query, max_results)
    elif search_type == "images":
        return await enhanced_service.search_images(query, max_results)
    elif search_type == "social":
        platforms = kwargs.get('platforms', ['twitter', 'reddit'])
        return await enhanced_service.search_social_media(query, platforms, max_results)
    else:  # general search
        async with RealSearchService() as search_service:
            multi_results = await search_service.multi_search(query, engines, max_results)
            return await enhanced_service.deduplicate_and_rank(multi_results, query)