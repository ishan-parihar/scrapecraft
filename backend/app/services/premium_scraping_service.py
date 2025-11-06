"""
Premium Scraping Service - Advanced search engine scraping without APIs
Provides proxy rotation, browser automation, and anti-detection measures
"""

import asyncio
import random
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from urllib.parse import urlencode, quote_plus, urlparse
import json
import hashlib

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import httpx
from bs4 import BeautifulSoup
import fake_useragent

logger = logging.getLogger(__name__)

class EngineType(Enum):
    GOOGLE = "google"
    BING = "bing"
    YAHOO = "yahoo"
    YANDEX = "yandex"
    BAIDU = "baidu"
    DUCKDUCKGO = "duckduckgo"
    BRAVE = "brave"

@dataclass
class ProxyConfig:
    """Proxy configuration for rotation"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "http"  # http, socks5
    country: Optional[str] = None
    last_used: float = 0

@dataclass
class BrowserConfig:
    """Browser configuration for anti-detection"""
    user_agent: str
    viewport: Dict[str, int]
    locale: str = "en-US"
    timezone: str = "America/New_York"
    permissions: List[str] = None
    
    def __post_init__(self):
        if self.permissions is None:
            self.permissions = []

class PremiumScrapingService:
    """
    Advanced scraping service for premium search engines without APIs
    """
    
    def __init__(self):
        self.proxies: List[ProxyConfig] = []
        self.current_proxy_index = 0
        self.browser_configs: List[BrowserConfig] = []
        self.session = httpx.AsyncClient(timeout=30.0)
        self._init_browser_configs()
        self._init_proxies()
        
        # Rate limiting per engine
        self.engine_delays = {
            EngineType.GOOGLE: (2.0, 5.0),
            EngineType.BING: (1.5, 3.0),
            EngineType.YAHOO: (1.0, 2.5),
            EngineType.YANDEX: (2.0, 4.0),
            EngineType.BAIDU: (1.5, 3.0),
            EngineType.DUCKDUCKGO: (0.5, 1.5),
            EngineType.BRAVE: (0.8, 2.0)
        }
        
        # Engine-specific configurations
        self.engine_configs = {
            EngineType.GOOGLE: {
                "base_url": "https://www.google.com/search",
                "results_selector": "div.g",
                "title_selector": "h3",
                "link_selector": "a",
                "snippet_selector": "div.VwiC3b",
                "pagination_param": "start"
            },
            EngineType.BING: {
                "base_url": "https://www.bing.com/search",
                "results_selector": "li.b_algo",
                "title_selector": "h2",
                "link_selector": "a",
                "snippet_selector": "p",
                "pagination_param": "first"
            }
        }

    def _init_browser_configs(self):
        """Initialize realistic browser configurations"""
        ua = fake_useragent.UserAgent()
        
        configs = [
            BrowserConfig(
                user_agent=ua.chrome,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone="America/New_York"
            ),
            BrowserConfig(
                user_agent=ua.firefox,
                viewport={"width": 1366, "height": 768},
                locale="en-US",
                timezone="America/Los_Angeles"
            ),
            BrowserConfig(
                user_agent=ua.safari,
                viewport={"width": 1440, "height": 900},
                locale="en-GB",
                timezone="Europe/London"
            ),
            BrowserConfig(
                user_agent=ua.edge,
                viewport={"width": 1536, "height": 864},
                locale="en-US",
                timezone="America/Chicago"
            )
        ]
        
        self.browser_configs = configs

    def _init_proxies(self):
        """Initialize proxy configurations (placeholder - would load from config)"""
        # In production, these would be loaded from configuration or proxy service
        # For demo, we'll use empty list (no proxy)
        self.proxies = []
        
        # Example proxy configs (commented out):
        # self.proxies.append(ProxyConfig(
        #     host="proxy1.example.com",
        #     port=8080,
        #     username="user1",
        #     password="pass1",
        #     country="US"
        # ))

    def _get_next_proxy(self) -> Optional[ProxyConfig]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
            
        # Simple round-robin rotation
        proxy = self.proxies[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)
        proxy.last_used = time.time()
        return proxy

    def _get_random_browser_config(self) -> BrowserConfig:
        """Get random browser configuration"""
        return random.choice(self.browser_configs)

    async def _delay_for_engine(self, engine: EngineType):
        """Apply rate limiting delay for specific engine"""
        min_delay, max_delay = self.engine_delays.get(engine, (1.0, 3.0))
        delay = random.uniform(min_delay, max_delay)
        await asyncio.sleep(delay)

    def _build_search_url(self, engine: EngineType, query: str, page: int = 0) -> str:
        """Build search URL for specific engine"""
        if engine == EngineType.GOOGLE:
            params = {
                "q": query,
                "num": 10,  # Number of results
                "hl": "en",
                "gl": "us"
            }
            if page > 0:
                params["start"] = page * 10
            return f"https://www.google.com/search?{urlencode(params)}"
        
        elif engine == EngineType.BING:
            params = {
                "q": query,
                "count": 10,
                "mkt": "en-US"
            }
            if page > 0:
                params["first"] = page * 10 + 1
            return f"https://www.bing.com/search?{urlencode(params)}"
        
        elif engine == EngineType.DUCKDUCKGO:
            params = {
                "q": query,
                "kl": "us-en"
            }
            return f"https://html.duckduckgo.com/html/?{urlencode(params)}"
        
        elif engine == EngineType.BRAVE:
            params = {
                "q": query,
                "source": "web"
            }
            return f"https://search.brave.com/search?{urlencode(params)}"
        
        # Default fallback
        return f"https://www.google.com/search?q={quote_plus(query)}"

    async def _scrape_with_playwright(self, engine: EngineType, query: str, page: int = 0) -> List[Dict[str, Any]]:
        """Scrape using Playwright browser automation"""
        results = []
        browser_config = self._get_random_browser_config()
        proxy = self._get_next_proxy()
        
        proxy_config = None
        if proxy:
            proxy_config = {
                "server": f"{proxy.proxy_type}://{proxy.host}:{proxy.port}",
                "username": proxy.username,
                "password": proxy.password
            }
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=[
                    "--no-sandbox",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-features=VizDisplayCompositor",
                    "--disable-extensions",
                    "--disable-plugins",
                    "--disable-images",  # Faster loading
                    "--disable-javascript",  # Sometimes needed for basic scraping
                ]
            )
            
            context = await browser.new_context(
                user_agent=browser_config.user_agent,
                viewport=browser_config.viewport,
                locale=browser_config.locale,
                timezone_id=browser_config.timezone,
                permissions=browser_config.permissions,
                # Additional anti-detection
                extra_http_headers={
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }
            )
            
            # Add stealth scripts
            await context.add_init_script("""
                // Remove webdriver traces
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                // Override plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en'],
                });
            """)
            
            page = await context.new_page()
            
            try:
                url = self._build_search_url(engine, query, page)
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Wait a bit for dynamic content
                await asyncio.sleep(random.uniform(1, 3))
                
                # Check for CAPTCHA or blocking
                page_content = await page.content()
                if self._is_blocked(page_content, engine):
                    logger.warning(f"Page blocked for {engine.value}, trying alternative approach")
                    results = await self._scrape_with_httpx(engine, query, page)
                else:
                    results = await self._parse_results_page(page.content(), engine)
                
            except Exception as e:
                logger.error(f"Playwright scraping failed for {engine.value}: {e}")
                # Fallback to HTTP scraping
                results = await self._scrape_with_httpx(engine, query, page)
            
            finally:
                await browser.close()
        
        return results

    async def _scrape_with_httpx(self, engine: EngineType, query: str, page: int = 0) -> List[Dict[str, Any]]:
        """Scrape using HTTP requests (faster but less sophisticated)"""
        results = []
        proxy = self._get_next_proxy()
        browser_config = self._get_random_browser_config()
        
        proxies = None
        if proxy:
            proxies = f"{proxy.proxy_type}://"
            if proxy.username and proxy.password:
                proxies += f"{proxy.username}:{proxy.password}@"
            proxies += f"{proxy.host}:{proxy.port}"
        
        headers = {
            "User-Agent": browser_config.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        
        try:
            url = self._build_search_url(engine, query, page)
            
            # Prepare request parameters
            request_kwargs = {
                "headers": headers,
                "follow_redirects": True
            }
            
            # Add proxy if available
            if proxies:
                request_kwargs["proxies"] = proxies
            
            response = await self.session.get(url, **request_kwargs)
            
            if response.status_code == 200:
                results = await self._parse_results_page(response.text, engine)
            else:
                logger.warning(f"HTTP scraping failed for {engine.value}: {response.status_code}")
                
        except Exception as e:
            logger.error(f"HTTP scraping error for {engine.value}: {e}")
        
        return results

    def _is_blocked(self, content: str, engine: EngineType) -> bool:
        """Check if page is blocked or showing CAPTCHA"""
        content_lower = content.lower()
        
        # Common blocking indicators
        blocking_indicators = [
            "captcha",
            "unusual traffic",
            "blocked",
            "access denied",
            "robot check",
            "verify you are human",
            "security check",
            "please complete",
            "recaptcha",
            "prove you are human"
        ]
        
        for indicator in blocking_indicators:
            if indicator in content_lower:
                return True
        
        # Engine-specific blocking patterns
        if engine == EngineType.GOOGLE:
            return any(indicator in content_lower for indicator in [
                "our systems have detected unusual traffic",
                "captcha/show",
                "sorry, we can't verify that you're not a robot"
            ])
        elif engine == EngineType.BING:
            return any(indicator in content_lower for indicator in [
                "prove you are human",
                "security challenge"
            ])
        
        return False

    async def _parse_results_page(self, html: str, engine: EngineType) -> List[Dict[str, Any]]:
        """Parse search results from HTML page"""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        if engine == EngineType.GOOGLE:
            results = self._parse_google_results(soup)
        elif engine == EngineType.BING:
            results = self._parse_bing_results(soup)
        elif engine == EngineType.DUCKDUCKGO:
            results = self._parse_duckduckgo_results(soup)
        elif engine == EngineType.BRAVE:
            results = self._parse_brave_results(soup)
        
        return results

    def _parse_google_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse Google search results"""
        results = []
        
        # Multiple selectors for Google results (they change frequently)
        result_selectors = [
            "div.g",  # Standard
            "div.tF2Cxc",  # New layout
            "div.hlcw0c",  # Alternative
            "div.yuRUbf",  # Another variation
        ]
        
        for selector in result_selectors:
            result_divs = soup.select(selector)
            if result_divs:
                logger.info(f"Using Google selector: {selector}")
                break
        else:
            logger.warning("No Google result elements found")
            return results
        
        for div in result_divs[:10]:  # Limit to 10 results
            try:
                # Title and URL
                title_elem = div.select_one("h3") or div.select_one("h3.LC20lb")
                link_elem = div.select_one("a")
                
                if not title_elem or not link_elem or not link_elem.get('href'):
                    continue
                
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href')
                
                # Skip Google internal links
                if url.startswith('/url?') or 'google.com' in url:
                    continue
                
                # Clean URL
                if url.startswith('/url?'):
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(url[5:])
                    url = parsed.get('url', [''])[0]
                
                # Snippet
                snippet_elem = (
                    div.select_one("div.VwiC3b") or 
                    div.select_one("div.s") or 
                    div.select_one("span.aCOpRe")
                )
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Meta data
                meta_elem = div.select_one("div.xSXRi") or div.select_one("cite")
                meta = meta_elem.get_text(strip=True) if meta_elem else ""
                
                result = {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "meta": meta,
                    "engine": "google",
                    "rank": len(results) + 1,
                    "timestamp": time.time()
                }
                
                # Calculate relevance score
                result["relevance_score"] = self._calculate_relevance_score(result)
                
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error parsing Google result: {e}")
                continue
        
        return results

    def _parse_bing_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse Bing search results"""
        results = []
        
        result_divs = soup.select("li.b_algo")
        
        for div in result_divs[:10]:
            try:
                # Title and URL
                title_elem = div.select_one("h2")
                link_elem = div.select_one("a")
                
                if not title_elem or not link_elem or not link_elem.get('href'):
                    continue
                
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href')
                
                # Snippet
                snippet_elem = div.select_one("p") or div.select_one("div.b_caption p")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Meta data
                meta_elem = div.select_one("cite")
                meta = meta_elem.get_text(strip=True) if meta_elem else ""
                
                result = {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "meta": meta,
                    "engine": "bing",
                    "rank": len(results) + 1,
                    "timestamp": time.time()
                }
                
                result["relevance_score"] = self._calculate_relevance_score(result)
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error parsing Bing result: {e}")
                continue
        
        return results

    def _parse_duckduckgo_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse DuckDuckGo search results"""
        results = []
        
        result_divs = soup.select("div.result")
        
        for div in result_divs[:10]:
            try:
                # Title and URL
                title_elem = div.select_one("h2") or div.select_one("a.result__a")
                link_elem = div.select_one("a.result__a") or div.select_one("h2 a")
                
                if not title_elem or not link_elem or not link_elem.get('href'):
                    continue
                
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href')
                
                # Skip DuckDuckGo internal links
                if url.startswith('/l/?uddg='):
                    # Extract real URL from redirect
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(url[3:])
                    url = parsed.get('uddg', [''])[0]
                elif url.startswith('/l/?'):
                    # Alternative DDG redirect format
                    import urllib.parse
                    parsed = urllib.parse.parse_qs(url[3:])
                    url = parsed.get('uddg', [''])[0]
                
                # Snippet
                snippet_elem = div.select_one("a.result__snippet")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                result = {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "meta": "",
                    "engine": "duckduckgo",
                    "rank": len(results) + 1,
                    "timestamp": time.time()
                }
                
                result["relevance_score"] = self._calculate_relevance_score(result)
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error parsing DuckDuckGo result: {e}")
                continue
        
        return results

    def _parse_brave_results(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse Brave search results"""
        results = []
        
        result_divs = soup.select("div.web-result")
        
        for div in result_divs[:10]:
            try:
                # Title and URL
                title_elem = div.select_one("h3") or div.select_one("a.snippet-title")
                link_elem = div.select_one("a")
                
                if not title_elem or not link_elem or not link_elem.get('href'):
                    continue
                
                title = title_elem.get_text(strip=True)
                url = link_elem.get('href')
                
                # Snippet
                snippet_elem = div.select_one("div.snippet-description") or div.select_one("p")
                snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                result = {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "meta": "",
                    "engine": "brave",
                    "rank": len(results) + 1,
                    "timestamp": time.time()
                }
                
                result["relevance_score"] = self._calculate_relevance_score(result)
                results.append(result)
                
            except Exception as e:
                logger.warning(f"Error parsing Brave result: {e}")
                continue
        
        return results

    def _calculate_relevance_score(self, result: Dict[str, Any]) -> float:
        """Calculate relevance score for a result"""
        score = 0.5  # Base score
        
        # Title relevance (basic keyword matching)
        title = result.get("title", "").lower()
        snippet = result.get("snippet", "").lower()
        
        # Boost for longer titles (more descriptive)
        if len(title) > 30:
            score += 0.1
        
        # Boost for snippets
        if snippet:
            score += 0.2
        
        # Boost for HTTPS
        url = result.get("url", "")
        if url.startswith("https://"):
            score += 0.1
        
        # Boost for common domains
        trusted_domains = ["wikipedia.org", "github.com", "stackoverflow.com", "reddit.com"]
        if any(domain in url for domain in trusted_domains):
            score += 0.1
        
        return min(score, 1.0)

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

    async def search_engine(self, engine: EngineType, query: str, max_pages: int = 1, use_browser: bool = False) -> List[Dict[str, Any]]:
        """
        Search using specific engine with advanced scraping techniques
        
        Args:
            engine: Search engine to use
            query: Search query
            max_pages: Maximum pages to scrape
            use_browser: Whether to use browser automation (slower but more effective)
        
        Returns:
            List of search results
        """
        logger.info(f"Searching {engine.value} for: {query}")
        
        all_results = []
        
        for page in range(max_pages):
            try:
                # Rate limiting
                await self._delay_for_engine(engine)
                
                # Choose scraping method
                if use_browser:
                    results = await self._scrape_with_playwright(engine, query, page)
                else:
                    results = await self._scrape_with_httpx(engine, query, page)
                
                if not results:
                    logger.warning(f"No results found on page {page + 1} for {engine.value}")
                    break
                
                all_results.extend(results)
                
                # Add page offset to ranks
                for result in results:
                    result["rank"] += page * 10
                
            except Exception as e:
                logger.error(f"Error scraping {engine.value} page {page + 1}: {e}")
                continue
        
        logger.info(f"Found {len(all_results)} results from {engine.value}")
        return all_results

    async def multi_engine_search(self, query: str, engines: List[EngineType] = None, 
                                 use_browser: bool = False) -> List[Dict[str, Any]]:
        """
        Search across multiple engines concurrently
        
        Args:
            query: Search query
            engines: List of engines to use (default: DuckDuckGo, Brave)
            use_browser: Whether to use browser automation
        
        Returns:
            Combined and deduplicated results
        """
        if engines is None:
            engines = [EngineType.DUCKDUCKGO, EngineType.BRAVE]
        
        # Create tasks for concurrent execution
        tasks = []
        for engine in engines:
            task = self.search_engine(engine, query, max_pages=1, use_browser=use_browser)
            tasks.append(task)
        
        # Execute concurrently
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and deduplicate results
        all_results = []
        seen_urls = set()
        
        for i, results in enumerate(results_lists):
            if isinstance(results, Exception):
                logger.error(f"Engine {engines[i].value} failed: {results}")
                continue
            
            for result in results:
                url = result.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    all_results.append(result)
        
        # Sort by relevance score
        all_results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
        
        logger.info(f"Multi-engine search found {len(all_results)} unique results")
        return all_results

    async def test_engines(self) -> Dict[str, bool]:
        """Test connectivity to different search engines"""
        test_query = "test query"
        results = {}
        
        for engine in [EngineType.DUCKDUCKGO, EngineType.BRAVE, EngineType.GOOGLE, EngineType.BING]:
            try:
                engine_results = await self.search_engine(engine, test_query, max_pages=1, use_browser=False)
                results[engine.value] = len(engine_results) > 0
            except Exception as e:
                logger.error(f"Test failed for {engine.value}: {e}")
                results[engine.value] = False
        
        return results

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.aclose()