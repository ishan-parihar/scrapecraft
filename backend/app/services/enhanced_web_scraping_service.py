"""
Enhanced Web Scraping Service
Implements real content extraction with BeautifulSoup, rate limiting, and content normalization.
"""

import asyncio
import logging
import re
import time
from typing import List, Dict, Optional, Any, Set
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
from bs4 import BeautifulSoup
import html2text

from app.config import settings

logger = logging.getLogger(__name__)

@dataclass
class ScrapedContent:
    """Structured data for scraped content."""
    url: str
    title: str
    content: str
    text_content: str
    metadata: Dict[str, Any]
    links: List[str]
    images: List[str]
    scrape_timestamp: datetime
    content_length: int
    word_count: int

@dataclass
class RateLimitInfo:
    """Rate limiting information for a domain."""
    domain: str
    last_request: datetime
    request_count: int
    window_start: datetime

class RateLimiter:
    """Implements rate limiting and politeness policies."""
    
    def __init__(self):
        self.domain_limits: Dict[str, RateLimitInfo] = {}
        self.global_last_request = datetime.now()
        self.min_delay = settings.SCRAPE_DELAY_SECONDS
        self.max_requests_per_minute = 30  # Politeness policy
        self.max_concurrent = settings.MAX_CONCURRENT_REQUESTS
        self.current_requests = 0
        
    async def acquire(self, domain: str) -> bool:
        """Check if request can proceed and apply rate limiting."""
        now = datetime.now()
        
        # Global rate limiting
        time_since_global = (now - self.global_last_request).total_seconds()
        if time_since_global < self.min_delay:
            await asyncio.sleep(self.min_delay - time_since_global)
        
        # Domain-specific rate limiting
        if domain not in self.domain_limits:
            self.domain_limits[domain] = RateLimitInfo(
                domain=domain,
                last_request=now,
                request_count=1,
                window_start=now
            )
            return True
        
        limit_info = self.domain_limits[domain]
        
        # Reset window if more than a minute has passed
        if now - limit_info.window_start > timedelta(minutes=1):
            limit_info.request_count = 0
            limit_info.window_start = now
        
        # Check rate limit
        if limit_info.request_count >= self.max_requests_per_minute:
            wait_time = 60 - (now - limit_info.window_start).total_seconds()
            if wait_time > 0:
                logger.info(f"Rate limiting {domain}: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
        
        # Update tracking
        limit_info.last_request = now
        limit_info.request_count += 1
        self.global_last_request = now
        
        return True
    
    async def release(self):
        """Release request slot."""
        if self.current_requests > 0:
            self.current_requests -= 1

class ContentCleaner:
    """Handles content cleaning and normalization."""
    
    def __init__(self):
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = False
        self.html_converter.body_width = 0  # No line wrapping
        
        # Patterns to clean up
        self.script_pattern = re.compile(r'<script[^>]*>.*?</script>', re.DOTALL | re.IGNORECASE)
        self.style_pattern = re.compile(r'<style[^>]*>.*?</style>', re.DOTALL | re.IGNORECASE)
        self.comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
        self.extra_whitespace = re.compile(r'\s+')
        self.empty_lines = re.compile(r'\n\s*\n\s*\n')
    
    def clean_html(self, html: str) -> str:
        """Clean HTML content by removing scripts, styles, and comments."""
        # Remove scripts, styles, and comments
        html = self.script_pattern.sub('', html)
        html = self.style_pattern.sub('', html)
        html = self.comment_pattern.sub('', html)
        
        # Convert to structured text
        try:
            text = self.html_converter.handle(html)
            # Clean up extra whitespace
            text = self.extra_whitespace.sub(' ', text)
            text = self.empty_lines.sub('\n\n', text)
            return text.strip()
        except Exception as e:
            logger.warning(f"HTML to text conversion failed: {e}")
            return html
    
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from page."""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'scrape_timestamp': datetime.now().isoformat(),
        }
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if content:
                if name in ['description', 'keywords', 'author']:
                    metadata[f'meta_{name}'] = content
                elif property_attr in ['og:title', 'og:description', 'og:type']:
                    metadata[property_attr.replace(':', '_')] = content
        
        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag.get('lang')
        
        return metadata
    
    def extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page."""
        links = set()
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            elif not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # Clean and validate
            if href.startswith(('http://', 'https://')):
                links.add(href)
        
        return list(links)
    
    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all image URLs from the page."""
        images = set()
        for img in soup.find_all('img', src=True):
            src = img['src']
            # Convert relative URLs to absolute
            if src.startswith('/'):
                src = urljoin(base_url, src)
            elif not src.startswith(('http://', 'https://')):
                src = urljoin(base_url, src)
            
            images.add(src)
        
        return list(images)

class EnhancedWebScrapingService:
    """Enhanced web scraping service with rate limiting and content processing."""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.content_cleaner = ContentCleaner()
        self.session: Optional[httpx.AsyncClient] = None
        self.user_agent = settings.USER_AGENT
        self.timeout = 30
        self.max_content_length = 5 * 1024 * 1024  # 5MB limit
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout),
            headers={'User-Agent': self.user_agent},
            follow_redirects=True,
            max_redirects=5
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.aclose()
    
    async def scrape_url(self, url: str) -> Optional[ScrapedContent]:
        """
        Scrape a single URL with rate limiting and content processing.
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapedContent object or None if scraping fails
        """
        try:
            # Parse domain for rate limiting
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            
            if not domain:
                logger.warning(f"Invalid URL: {url}")
                return None
            
            # Apply rate limiting
            await self.rate_limiter.acquire(domain)
            
            # Make request
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                logger.warning(f"Skipping non-HTML content: {content_type} for {url}")
                return None
            
            # Check content length
            content_length = len(response.content)
            if content_length > self.max_content_length:
                logger.warning(f"Content too large ({content_length} bytes) for {url}")
                return None
            
            # Parse HTML
            html = response.text
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract content
            title = self._extract_title(soup)
            clean_content = self.content_cleaner.clean_html(html)
            text_content = soup.get_text(separator=' ', strip=True)
            
            # Extract metadata and links
            metadata = self.content_cleaner.extract_metadata(soup, url)
            links = self.content_cleaner.extract_links(soup, url)
            images = self.content_cleaner.extract_images(soup, url)
            
            # Create structured result
            scraped_content = ScrapedContent(
                url=url,
                title=title,
                content=clean_content,
                text_content=text_content,
                metadata=metadata,
                links=links,
                images=images,
                scrape_timestamp=datetime.now(),
                content_length=content_length,
                word_count=len(text_content.split())
            )
            
            logger.info(f"Successfully scraped {url}: {len(clean_content)} chars, {len(links)} links")
            return scraped_content
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error scraping {url}: {e.response.status_code}")
        except httpx.RequestError as e:
            logger.error(f"Request error scraping {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {e}")
        
        finally:
            await self.rate_limiter.release()
        
        return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title with fallbacks."""
        # Try title tag first
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            if title:
                return title
        
        # Try og:title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content']
        
        # Try h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        # Fallback to domain
        return "Untitled Page"
    
    async def scrape_multiple_urls(self, urls: List[str], max_concurrent: int = None) -> List[ScrapedContent]:
        """
        Scrape multiple URLs with concurrency control.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum concurrent requests
            
        Returns:
            List of successfully scraped content
        """
        if max_concurrent is None:
            max_concurrent = self.rate_limiter.max_concurrent
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Optional[ScrapedContent]:
            async with semaphore:
                return await self.scrape_url(url)
        
        # Create tasks and run them concurrently
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        scraped_contents = []
        for result in results:
            if isinstance(result, ScrapedContent):
                scraped_contents.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraping task failed: {result}")
        
        logger.info(f"Successfully scraped {len(scraped_contents)}/{len(urls)} URLs")
        return scraped_contents
    
    async def validate_url(self, url: str) -> bool:
        """Validate if URL is accessible and scrapeable."""
        try:
            parsed_url = urlparse(url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return False
            
            # Make a lightweight HEAD request first
            response = await self.session.head(url)
            return response.status_code == 200
            
        except Exception:
            return False