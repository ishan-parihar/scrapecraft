"""
Search Result Processing Pipeline
Processes search results with content extraction, relevance scoring, and quality filtering.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from urllib.parse import urlparse
import re

from app.services.enhanced_web_scraping_service import EnhancedWebScrapingService, ScrapedContent
from app.services.real_search_service import RealSearchService

logger = logging.getLogger(__name__)

@dataclass
class ProcessedSearchResult:
    """Enhanced search result with scraped content and metadata."""
    # Original search result data
    title: str
    url: str
    snippet: str
    source: str
    position: int
    
    # Enhanced content
    scraped_content: Optional[ScrapedContent] = None
    full_text: str = ""
    cleaned_content: str = ""
    
    # Quality metrics
    relevance_score: float = 0.0
    content_quality_score: float = 0.0
    trust_score: float = 0.0
    
    # Metadata
    word_count: int = 0
    content_length: int = 0
    link_count: int = 0
    image_count: int = 0
    
    # Processing metadata
    processed_at: datetime = field(default_factory=datetime.now)
    scrape_success: bool = False
    processing_time_ms: int = 0
    
    # Extracted entities (placeholder for future NLP)
    entities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)

@dataclass
class ProcessingStats:
    """Statistics for search result processing."""
    total_results: int = 0
    successfully_scraped: int = 0
    failed_scrapes: int = 0
    average_relevance: float = 0.0
    processing_time_ms: int = 0
    content_sources: Dict[str, int] = field(default_factory=dict)

class ContentQualityScorer:
    """Scores content quality based on various factors."""
    
    def __init__(self):
        self.spam_patterns = [
            r'click here',
            r'buy now',
            r'limited time',
            r'act now',
            r'free.*money',
            r'guarantee.*result',
            r'risk.*free'
        ]
        
        self.quality_indicators = [
            r'\b\d{4}\b',  # Years (dates)
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper names
            r'\b\d+,\d+\b',  # Numbers with commas
            r'\b\w+\.\w+',  # Domain names
        ]
        
        self.trustworthy_domains = {
            'wikipedia.org', 'github.com', 'stackoverflow.com',
            'reddit.com', 'news.', 'bbc.com', 'cnn.com',
            'reuters.com', 'ap.org', 'nasa.gov', 'nih.gov',
            'edu', 'gov'
        }
    
    def calculate_quality_score(self, content: ScrapedContent, search_result: Dict) -> float:
        """Calculate content quality score (0.0 to 1.0)."""
        score = 0.0
        
        # Base score for having content
        if content and content.content_length > 100:
            score += 0.3
        
        # Content length factor
        if content:
            if content.content_length > 1000:
                score += 0.2
            elif content.content_length > 500:
                score += 0.1
            
            # Word count factor
            if content.word_count > 200:
                score += 0.1
            elif content.word_count > 100:
                score += 0.05
        
        # Title and snippet relevance
        title = search_result.get('title', '').lower()
        snippet = search_result.get('snippet', '').lower()
        
        if len(title) > 10 and len(snippet) > 20:
            score += 0.1
        
        # Domain trustworthiness
        domain = urlparse(search_result.get('url', '')).netloc.lower()
        if any(trust in domain for trust in self.trustworthy_domains):
            score += 0.2
        
        # Content structure (has links, images)
        if content:
            if len(content.links) > 5:
                score += 0.05
            if len(content.images) > 2:
                score += 0.05
        
        # Penalize spam indicators
        combined_text = f"{title} {snippet}"
        if content:
            combined_text += f" {content.content}"
        
        spam_matches = sum(1 for pattern in self.spam_patterns if re.search(pattern, combined_text, re.IGNORECASE))
        score -= min(spam_matches * 0.1, 0.3)
        
        # Quality indicators
        quality_matches = sum(1 for pattern in self.quality_indicators if re.search(pattern, combined_text))
        score += min(quality_matches * 0.05, 0.15)
        
        return max(0.0, min(1.0, score))
    
    def calculate_trust_score(self, url: str, content: Optional[ScrapedContent] = None) -> float:
        """Calculate trust score based on domain and content factors."""
        score = 0.5  # Base score
        
        # Domain analysis
        domain = urlparse(url).netloc.lower()
        
        # Trustworthy TLDs
        if domain.endswith(('.edu', '.gov', '.mil')):
            score += 0.3
        elif domain.endswith(('.org', '.int')):
            score += 0.2
        
        # Trustworthy domains
        if any(trust in domain for trust in self.trustworthy_domains):
            score += 0.2
        
        # HTTPS
        if url.startswith('https://'):
            score += 0.1
        
        # Content factors
        if content:
            # Has metadata
            if content.metadata.get('meta_description'):
                score += 0.05
            
            # Structured content
            if len(content.links) > 3 and content.word_count > 100:
                score += 0.1
        
        return max(0.0, min(1.0, score))

class RelevanceScorer:
    """Scores relevance of search results to the original query."""
    
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
    
    def calculate_relevance_score(self, query: str, search_result: Dict, content: Optional[ScrapedContent] = None) -> float:
        """Calculate relevance score (0.0 to 1.0)."""
        query_terms = self._extract_terms(query.lower())
        
        # Title relevance
        title = search_result.get('title', '').lower()
        title_score = self._calculate_text_relevance(query_terms, title)
        
        # Snippet relevance
        snippet = search_result.get('snippet', '').lower()
        snippet_score = self._calculate_text_relevance(query_terms, snippet)
        
        # URL relevance
        url = search_result.get('url', '').lower()
        url_score = self._calculate_text_relevance(query_terms, url)
        
        # Content relevance (if available)
        content_score = 0.0
        if content:
            content_text = content.content.lower()
            content_score = self._calculate_text_relevance(query_terms, content_text) * 0.5
        
        # Weighted combination
        total_score = (
            title_score * 0.4 +
            snippet_score * 0.3 +
            url_score * 0.2 +
            content_score * 0.1
        )
        
        return min(1.0, total_score)
    
    def _extract_terms(self, text: str) -> List[str]:
        """Extract meaningful terms from text."""
        # Simple tokenization and stop word removal
        terms = re.findall(r'\b\w+\b', text)
        return [term for term in terms if term not in self.stop_words and len(term) > 2]
    
    def _calculate_text_relevance(self, query_terms: List[str], text: str) -> float:
        """Calculate relevance of text to query terms."""
        if not query_terms:
            return 0.0
        
        text_terms = self._extract_terms(text)
        if not text_terms:
            return 0.0
        
        # Count matching terms
        matches = sum(1 for term in query_terms if term in text_terms)
        
        # Calculate coverage
        coverage = matches / len(query_terms)
        
        # Calculate density (matches in text)
        density = matches / len(text_terms) if text_terms else 0
        
        # Combined score
        return (coverage * 0.7 + density * 0.3)

class SearchResultProcessingPipeline:
    """Main pipeline for processing search results with content extraction."""
    
    def __init__(self):
        self.quality_scorer = ContentQualityScorer()
        self.relevance_scorer = RelevanceScorer()
        
    async def process_search_results(
        self,
        search_results: List[Dict[str, Any]],
        original_query: str,
        scrape_content: bool = True,
        max_concurrent_scrapes: int = 5
    ) -> Tuple[List[ProcessedSearchResult], ProcessingStats]:
        """
        Process a list of search results with content extraction and scoring.
        
        Args:
            search_results: List of search results from search engines
            original_query: The original search query
            scrape_content: Whether to scrape full content from URLs
            max_concurrent_scrapes: Maximum concurrent scraping operations
            
        Returns:
            Tuple of (processed_results, processing_stats)
        """
        start_time = datetime.now()
        
        # Initialize stats
        stats = ProcessingStats(total_results=len(search_results))
        
        # Create processed results without scraping first
        processed_results = []
        for result in search_results:
            processed_result = ProcessedSearchResult(
                title=result.get('title', ''),
                url=result.get('url', ''),
                snippet=result.get('snippet', ''),
                source=result.get('source', 'unknown'),
                position=result.get('position', 0)
            )
            processed_results.append(processed_result)
        
        # Scrape content if requested
        if scrape_content and processed_results:
            scraped_contents = await self._scrape_contents(
                [r.url for r in processed_results],
                max_concurrent_scrapes
            )
            
            # Map scraped content back to results
            url_to_content = {content.url: content for content in scraped_contents}
            
            for result in processed_results:
                content = url_to_content.get(result.url)
                if content:
                    result.scraped_content = content
                    result.full_text = content.text_content
                    result.cleaned_content = content.content
                    result.word_count = content.word_count
                    result.content_length = content.content_length
                    result.link_count = len(content.links)
                    result.image_count = len(content.images)
                    result.scrape_success = True
                    stats.successfully_scraped += 1
                else:
                    stats.failed_scrapes += 1
        
        # Calculate scores for all results
        total_relevance = 0.0
        for result in processed_results:
            # Relevance score
            result.relevance_score = self.relevance_scorer.calculate_relevance_score(
                original_query,
                {
                    'title': result.title,
                    'snippet': result.snippet,
                    'url': result.url
                },
                result.scraped_content
            )
            
            # Quality and trust scores
            if result.scraped_content:
                result.content_quality_score = self.quality_scorer.calculate_quality_score(
                    result.scraped_content,
                    {
                        'title': result.title,
                        'snippet': result.snippet,
                        'url': result.url
                    }
                )
            
            result.trust_score = self.quality_scorer.calculate_trust_score(
                result.url,
                result.scraped_content
            )
            
            total_relevance += result.relevance_score
            
            # Update source stats
            source = result.source
            stats.content_sources[source] = stats.content_sources.get(source, 0) + 1
        
        # Calculate final stats
        stats.average_relevance = total_relevance / len(processed_results) if processed_results else 0.0
        stats.processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        logger.info(f"Processed {len(processed_results)} results in {stats.processing_time_ms}ms")
        logger.info(f"Successfully scraped: {stats.successfully_scraped}/{stats.total_results}")
        
        return processed_results, stats
    
    async def _scrape_contents(self, urls: List[str], max_concurrent: int) -> List[ScrapedContent]:
        """Scrape content from multiple URLs concurrently."""
        async with EnhancedWebScrapingService() as scraper:
            return await scraper.scrape_multiple_urls(urls, max_concurrent)
    
    def filter_results(
        self,
        results: List[ProcessedSearchResult],
        min_relevance: float = 0.1,
        min_quality: float = 0.0,
        min_trust: float = 0.0,
        max_results: int = 50
    ) -> List[ProcessedSearchResult]:
        """Filter results based on quality thresholds and limits."""
        filtered = []
        
        for result in results:
            if (result.relevance_score >= min_relevance and
                result.content_quality_score >= min_quality and
                result.trust_score >= min_trust):
                filtered.append(result)
        
        # Sort by combined score (relevance + quality + trust)
        filtered.sort(key=lambda r: (
            r.relevance_score * 0.5 +
            r.content_quality_score * 0.3 +
            r.trust_score * 0.2
        ), reverse=True)
        
        return filtered[:max_results]