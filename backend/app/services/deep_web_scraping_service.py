"""
Deep Web Scraping Service with JavaScript Support
Provides advanced scraping capabilities for JavaScript-heavy websites with anti-bot detection evasion.
"""

import asyncio
import time
import random
import json
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin, urlparse
from datetime import datetime
import hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, 
    WebDriverException, ElementNotInteractableException
)
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

from app.config import settings
from app.services.error_handling import handle_errors, ScrapingException, TimeoutException as ScrapingTimeoutException
from app.services.enhanced_web_scraping_service import EnhancedWebScrapingService

logger = logging.getLogger(__name__)

class DeepWebScrapingService:
    """
    Advanced web scraping service with JavaScript rendering and anti-bot evasion.
    """
    
    def __init__(self):
        self.driver = None
        self.scraping_service = EnhancedWebScrapingService()
        self.session_id = hashlib.md5(str(time.time()).encode()).hexdigest()[:8]
        self._setup_driver_options()
        
    def _setup_driver_options(self):
        """Setup Chrome driver options for stealth scraping."""
        self.chrome_options = Options()
        
        # Basic stealth options
        self.chrome_options.add_argument('--headless')  # Run in headless mode
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-dev-shm-usage')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument('--disable-plugins')
        self.chrome_options.add_argument('--disable-images')  # Speed up scraping
        self.chrome_options.add_argument('--disable-javascript')  # Will be enabled as needed
        
        # Anti-detection options
        self.chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        self.chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        self.chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Realistic user agent
        self.chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # Window size for realistic viewport
        self.chrome_options.add_argument('--window-size=1920,1080')
        
        # Language and locale
        self.chrome_options.add_argument('--lang=en-US,en;q=0.9')
        self.chrome_options.add_argument('--disable-features=VizDisplayCompositor')
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._initialize_driver()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._cleanup_driver()
    
    @handle_errors(
        service_name="deep_web_scraper",
        operation_name="initialize_driver"
    )
    async def _initialize_driver(self):
        """Initialize Chrome driver with anti-detection measures."""
        try:
            # Try to use selenium-manager (ChromeDriver 4.6+)
            self.driver = webdriver.Chrome(options=self.chrome_options)
            
            # Execute anti-detection scripts
            await self._setup_stealth_mode()
            
            # Set realistic page load timeout
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            logger.info(f"Deep web scraper initialized with session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            # Fallback to basic scraping without JavaScript
            self.driver = None
            logger.warning("Falling back to basic HTTP scraping (no JavaScript support)")
    
    async def _cleanup_driver(self):
        """Clean up Chrome driver."""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                logger.info("Chrome driver cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up driver: {e}")
    
    async def _setup_stealth_mode(self):
        """Setup stealth mode to avoid bot detection."""
        if not self.driver:
            return
        
        stealth_scripts = [
            # Remove navigator.webdriver flag
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})",
            
            # Override plugins
            "Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})",
            
            # Override languages
            "Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})",
            
            # Override chrome runtime
            "window.chrome = {runtime: {}}",
            
            # Override permissions
            "const originalQuery = window.navigator.permissions.query;",
            "window.navigator.permissions.query = (parameters) => (",
            "    parameters.name === 'notifications' ?",
            "        Promise.resolve({ state: Notification.permission }) :",
            "        originalQuery(parameters)",
            ");",
            
            # Randomize screen properties
            f"""
            Object.defineProperty(screen, 'availWidth', {{
                get: () => {random.randint(1800, 1920)}
            }});
            Object.defineProperty(screen, 'availHeight', {{
                get: () => {random.randint(900, 1080)}
            }});
            """
        ]
        
        for script in stealth_scripts:
            try:
                self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source': script})
            except Exception as e:
                logger.debug(f"Failed to add stealth script: {e}")
    
    @handle_errors(
        service_name="deep_web_scraper",
        operation_name="scrape_dynamic_content"
    )
    async def scrape_dynamic_content(
        self, 
        url: str, 
        wait_for_elements: List[str] = None,
        scroll_down: bool = False,
        extract_images: bool = False,
        extract_links: bool = True,
        max_scrolls: int = 3
    ) -> Dict[str, Any]:
        """
        Scrape dynamic content from JavaScript-heavy websites.
        
        Args:
            url: URL to scrape
            wait_for_elements: CSS selectors to wait for before extraction
            scroll_down: Whether to scroll down to load lazy content
            extract_images: Whether to extract image data
            extract_links: Whether to extract link data
            max_scrolls: Maximum number of scroll operations
            
        Returns:
            Dictionary with scraped content and metadata
        """
        if not self.driver:
            # Fallback to basic scraping
            logger.info("Using fallback scraping for dynamic content")
            return await self.scraping_service.scrape_content(url)
        
        try:
            # Navigate to URL with random delay
            await self._human_like_delay(1, 3)
            self.driver.get(url)
            
            # Wait for specific elements if provided
            if wait_for_elements:
                await self._wait_for_elements(wait_for_elements)
            else:
                # Wait for page to load
                await self._wait_for_page_load()
            
            # Scroll to load lazy content if requested
            if scroll_down:
                await self._scroll_to_load_content(max_scrolls)
            
            # Extract content
            content = await self._extract_dynamic_content(
                url, extract_images, extract_links
            )
            
            # Add session metadata
            content['scraping_session'] = self.session_id
            content['scraping_method'] = 'dynamic_javascript'
            content['scraped_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"Successfully scraped dynamic content from {url}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to scrape dynamic content from {url}: {e}")
            # Fallback to basic scraping
            return await self.scraping_service.scrape_content(url)
    
    async def _human_like_delay(self, min_seconds: float, max_seconds: float):
        """Add human-like random delay."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    async def _wait_for_elements(self, selectors: List[str], timeout: int = 10):
        """Wait for elements to be present on the page."""
        wait = WebDriverWait(self.driver, timeout)
        
        for selector in selectors:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                logger.debug(f"Element found: {selector}")
            except TimeoutException:
                logger.warning(f"Element not found within timeout: {selector}")
    
    async def _wait_for_page_load(self, timeout: int = 10):
        """Wait for page to fully load."""
        try:
            # Wait for either document ready or basic content
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except TimeoutException:
            logger.warning("Page load timeout, proceeding anyway")
    
    async def _scroll_to_load_content(self, max_scrolls: int):
        """Scroll down to load lazy-loaded content."""
        if not self.driver:
            return
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for scroll_num in range(max_scrolls):
            # Scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
            # Wait for new content to load
            await self._human_like_delay(1, 2)
            
            # Check if new content loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                logger.info(f"No new content after scroll {scroll_num + 1}, stopping")
                break
            
            last_height = new_height
            logger.info(f"Scroll {scroll_num + 1} completed, new content loaded")
    
    async def _extract_dynamic_content(
        self, 
        url: str, 
        extract_images: bool = False, 
        extract_links: bool = True
    ) -> Dict[str, Any]:
        """Extract content from dynamically loaded page."""
        try:
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            current_url = self.driver.current_url
            
            # Use BeautifulSoup for parsing
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')
            
            content = {
                'url': current_url,
                'original_url': url,
                'title': self._safe_extract(soup.find('title')),
                'text_content': self._extract_main_text(soup),
                'meta_description': self._extract_meta_description(soup),
                'meta_keywords': self._extract_meta_keywords(soup),
                'structured_data': self._extract_structured_data(soup),
                'javascript_rendered': True,
                'final_url': current_url,
                'redirected': current_url != url
            }
            
            # Extract links if requested
            if extract_links:
                content['links'] = await self._extract_dynamic_links(soup, current_url)
            
            # Extract images if requested
            if extract_images:
                content['images'] = await self._extract_dynamic_images(soup, current_url)
            
            # Extract dynamic data (AJAX-loaded content)
            content['dynamic_data'] = await self._extract_dynamic_data()
            
            return content
            
        except Exception as e:
            logger.error(f"Error extracting dynamic content: {e}")
            raise ScrapingException(f"Failed to extract dynamic content: {e}")
    
    def _safe_extract(self, element, default: str = "") -> str:
        """Safely extract text from an element."""
        if element and hasattr(element, 'get_text'):
            return element.get_text(strip=True)
        return default
    
    def _extract_main_text(self, soup) -> str:
        """Extract main text content from page."""
        # Remove unwanted elements
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # Try to find main content area
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=lambda x: x and ('content' in x.lower() or 'main' in x.lower())) or
            soup.find('div', class_=lambda x: x and 'article' in x.lower())
        )
        
        if main_content:
            return main_content.get_text(separator=' ', strip=True)
        
        # Fallback to body
        return soup.get_text(separator=' ', strip=True)
    
    def _extract_meta_description(self, soup) -> str:
        """Extract meta description."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '').strip()
        
        # Try Open Graph description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            return og_desc.get('content', '').strip()
        
        return ""
    
    def _extract_meta_keywords(self, soup) -> str:
        """Extract meta keywords."""
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            return meta_keywords.get('content', '').strip()
        return ""
    
    def _extract_structured_data(self, soup) -> List[Dict[str, Any]]:
        """Extract structured data (JSON-LD, microdata, etc.)."""
        structured_data = []
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                structured_data.append({
                    'type': 'json-ld',
                    'data': data
                })
            except json.JSONDecodeError:
                logger.warning("Failed to parse JSON-LD structured data")
        
        # Extract microformats (basic)
        microdata_items = soup.find_all(attrs={'itemscope': True})
        for item in microdata_items:
            try:
                microdata = {
                    'type': 'microdata',
                    'itemtype': item.get('itemtype', ''),
                    'properties': {}
                }
                
                # Extract properties
                for prop in item.find_all(attrs={'itemprop': True}):
                    prop_name = prop.get('itemprop')
                    prop_value = prop.get('content') or prop.get_text(strip=True)
                    microdata['properties'][prop_name] = prop_value
                
                structured_data.append(microdata)
            except Exception as e:
                logger.warning(f"Failed to extract microdata: {e}")
        
        return structured_data
    
    async def _extract_dynamic_links(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract links with dynamic content detection."""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            title = link.get('title', '')
            
            # Convert relative URLs to absolute
            if href.startswith('/'):
                href = urljoin(base_url, href)
            elif not href.startswith(('http://', 'https://')):
                href = urljoin(base_url, href)
            
            # Filter out invalid links
            if href.startswith('http') and self._is_valid_url(href):
                links.append({
                    'url': href,
                    'text': text,
                    'title': title,
                    'type': self._classify_link(href),
                    'is_external': urlparse(href).netloc != urlparse(base_url).netloc
                })
        
        return links[:100]  # Limit to first 100 links
    
    async def _extract_dynamic_images(self, soup, base_url: str) -> List[Dict[str, str]]:
        """Extract images with dynamic loading detection."""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src') or img.get('data-original')
            alt = img.get('alt', '')
            title = img.get('title', '')
            
            if src:
                # Convert relative URLs to absolute
                if src.startswith('/'):
                    src = urljoin(base_url, src)
                elif not src.startswith(('http://', 'https://')):
                    src = urljoin(base_url, src)
                
                if self._is_valid_url(src):
                    images.append({
                        'url': src,
                        'alt': alt,
                        'title': title,
                        'width': img.get('width', ''),
                        'height': img.get('height', '')
                    })
        
        return images[:50]  # Limit to first 50 images
    
    async def _extract_dynamic_data(self) -> Dict[str, Any]:
        """Extract data loaded dynamically via JavaScript."""
        if not self.driver:
            return {}
        
        try:
            # Extract data from common JavaScript variables
            dynamic_data = {}
            
            # Try to extract common data structures
            scripts_to_try = [
                "window.__INITIAL_STATE__",
                "window.__PRELOADED_STATE__",
                "window.appData",
                "window.pageData",
                "window.config"
            ]
            
            for script_var in scripts_to_try:
                try:
                    data = self.driver.execute_script(f"return {script_var};")
                    if data:
                        dynamic_data[script_var] = data
                except Exception:
                    continue
            
            # Extract data from localStorage
            try:
                local_storage = self.driver.execute_script("return Object.assign({}, localStorage);")
                if local_storage:
                    dynamic_data['localStorage'] = local_storage
            except Exception:
                pass
            
            # Extract data from sessionStorage
            try:
                session_storage = self.driver.execute_script("return Object.assign({}, sessionStorage);")
                if session_storage:
                    dynamic_data['sessionStorage'] = session_storage
            except Exception:
                pass
            
            return dynamic_data
            
        except Exception as e:
            logger.warning(f"Failed to extract dynamic data: {e}")
            return {}
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid for scraping."""
        try:
            parsed = urlparse(url)
            return bool(parsed.netloc) and parsed.scheme in ('http', 'https')
        except:
            return False
    
    def _classify_link(self, url: str) -> str:
        """Classify the type of link."""
        url_lower = url.lower()
        
        if any(social in url_lower for social in ['twitter.com', 'facebook.com', 'linkedin.com', 'instagram.com']):
            return 'social_media'
        elif any(gov in url_lower for gov in ['.gov', '.mil']):
            return 'government'
        elif any(edu in url_lower for edu in ['.edu', '.ac.']):
            return 'academic'
        elif any(news in url_lower for news in ['news', 'cnn', 'bbc', 'reuters']):
            return 'news'
        elif any(doc in url_lower for doc in ['.pdf', '.doc', '.docx']):
            return 'document'
        elif any(video in url_lower for video in ['youtube.com', 'vimeo.com', 'video']):
            return 'video'
        elif any(img in url_lower for img in ['.jpg', '.jpeg', '.png', '.gif', '.svg']):
            return 'image'
        else:
            return 'general'
    
    async def scrape_multiple_pages(
        self, 
        base_url: str, 
        page_patterns: List[str] = None,
        max_pages: int = 5,
        delay_between_pages: float = 2.0
    ) -> List[Dict[str, Any]]:
        """
        Scrape multiple pages from a website following pagination patterns.
        
        Args:
            base_url: Starting URL
            page_patterns: List of URL patterns for pagination (e.g., ['?page={}', '/page/{}'])
            max_pages: Maximum number of pages to scrape
            delay_between_pages: Delay between page requests
            
        Returns:
            List of scraped content from multiple pages
        """
        results = []
        
        # Scrape first page
        first_page = await self.scrape_dynamic_content(base_url)
        results.append(first_page)
        
        # Find pagination links
        pagination_links = await self._find_pagination_links(first_page, page_patterns)
        
        # Scrape additional pages
        for i, page_url in enumerate(pagination_links[:max_pages-1]):
            logger.info(f"Scraping page {i+2}: {page_url}")
            
            await self._human_like_delay(delay_between_pages, delay_between_pages + 1)
            page_content = await self.scrape_dynamic_content(page_url)
            results.append(page_content)
        
        logger.info(f"Scraped {len(results)} pages from {base_url}")
        return results
    
    async def _find_pagination_links(
        self, 
        page_content: Dict[str, Any], 
        patterns: List[str] = None
    ) -> List[str]:
        """Find pagination links in page content."""
        links = []
        
        if not patterns:
            patterns = ['?page={}', '/page/{}', '/p/{}']
        
        base_url = page_content.get('url', '')
        page_links = page_content.get('links', [])
        
        for link in page_links:
            link_url = link['url']
            
            # Check if link matches pagination patterns
            for pattern in patterns:
                if pattern.format('1') in link_url or pattern.format('2') in link_url:
                    links.append(link_url)
                    break
        
        # Remove duplicates and sort
        links = list(set(links))
        links.sort()
        
        return links[:10]  # Limit to 10 pagination links


async def perform_deep_scraping(
    url: str,
    wait_for_elements: List[str] = None,
    scroll_down: bool = False,
    max_scrolls: int = 3,
    **kwargs
) -> Dict[str, Any]:
    """
    Convenience function for deep web scraping.
    
    Args:
        url: URL to scrape
        wait_for_elements: CSS selectors to wait for
        scroll_down: Whether to scroll for lazy content
        max_scrolls: Maximum number of scroll operations
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with scraped content
    """
    async with DeepWebScrapingService() as scraper:
        return await scraper.scrape_dynamic_content(
            url, wait_for_elements, scroll_down, 
            kwargs.get('extract_images', False),
            kwargs.get('extract_links', True),
            max_scrolls
        )