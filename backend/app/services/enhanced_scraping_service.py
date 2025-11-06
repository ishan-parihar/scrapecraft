"""
Enhanced scraping service that provides real web scraping functionality
without depending on ScrapeGraphAI's langchain compatibility issues.
"""

from typing import List, Dict, Optional, Any
import asyncio
import logging
import json
import re
from urllib.parse import urljoin, urlparse
from pydantic import BaseModel, Field
import os

# Web scraping libraries
import httpx
from bs4 import BeautifulSoup
import html2text

# Optional AI integration
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None

logger = logging.getLogger(__name__)

class EnhancedScrapingService:
    """Enhanced scraping service with real web scraping capabilities."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        self.llm_config = llm_config or {}
        
        # Configure HTTP client
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            },
            follow_redirects=True
        )
        
        # Configure HTML to text converter
        self.html_converter = html2text.HTML2Text()
        self.html_converter.ignore_links = False
        self.html_converter.ignore_images = True
        self.html_converter.body_width = 0
        
        # Initialize OpenAI client if available
        self.openai_client = None
        if OPENAI_AVAILABLE and self.llm_config.get('api_key'):
            try:
                self.openai_client = AsyncOpenAI(
                    api_key=self.llm_config.get('api_key'),
                    base_url=self.llm_config.get('base_url')
                )
                logger.info("OpenAI client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client: {e}")
    
    async def execute_pipeline(
        self,
        urls: List[str],
        schema: Optional[Dict[str, Any]],
        prompt: str
    ) -> List[Dict]:
        """Execute scraping for multiple URLs."""
        results = []
        
        for url in urls:
            try:
                result = await self._scrape_single_url(url, schema, prompt)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
                results.append({
                    "url": url,
                    "success": False,
                    "data": None,
                    "error": str(e)
                })
        
        return results
    
    async def _scrape_single_url(
        self,
        url: str,
        schema: Optional[Dict[str, Any]],
        prompt: str
    ) -> Dict:
        """Scrape a single URL and extract content."""
        try:
            # Fetch the webpage
            response = await self.http_client.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract basic information
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            metadata = self._extract_metadata(soup, response)
            
            # Create base result
            result_data = {
                "url": url,
                "title": title,
                "content": content,
                "metadata": metadata,
                "scraped_at": asyncio.get_event_loop().time(),
                "status": "success"
            }
            
            # If schema is provided, try to extract structured data
            if schema:
                structured_data = await self._extract_structured_data(
                    content, prompt, schema, url
                )
                result_data.update(structured_data)
            
            # If OpenAI is available, enhance extraction
            elif self.openai_client:
                enhanced_data = await self._enhance_with_ai(content, prompt, url)
                result_data.update(enhanced_data)
            
            return {
                "url": url,
                "success": True,
                "data": result_data,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                "url": url,
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract the title from the page."""
        # Try different title sources
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            return title_text.strip() if title_text else "No title found"
        
        # Try h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.get_text()
            return h1_text.strip() if h1_text else "No title found"
        
        # Try og:title
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title:
            content = og_title.get('content', '')
            return content.strip() if content else "No title found"
        
        return "No title found"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract the main content from the page."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
            script.decompose()
        
        # Try to find main content area
        main_content = None
        
        # Look for common content containers
        for selector in ['main', 'article', '[role="main"]', '.content', '.main-content']:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # If no main content found, use body
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Convert to text
        text_content = self.html_converter.handle(str(main_content))
        
        # Clean up text
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        content = '\n'.join(lines)
        
        return content[:10000]  # Limit content length
    
    def _extract_metadata(self, soup: BeautifulSoup, response) -> Dict:
        """Extract metadata from the page."""
        metadata = {}
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            name = tag.get('name') or tag.get('property')
            content_attr = tag.get('content')
            if name and content_attr:
                metadata[name] = content_attr
        
        # Add response info
        metadata['status_code'] = response.status_code
        metadata['content_type'] = response.headers.get('content-type', '')
        metadata['content_length'] = len(response.content)
        
        # Extract links
        links = [a.get('href') for a in soup.find_all('a', href=True) if a.get('href')]
        metadata['link_count'] = len(links)
        
        # Extract external links safely
        external_links = []
        if response.url:
            try:
                current_domain = urlparse(response.url).netloc
                for link in links:
                    if link.startswith('http'):
                        link_domain = urlparse(link).netloc
                        if link_domain != current_domain:
                            external_links.append(link)
                            if len(external_links) >= 10:
                                break
            except Exception:
                pass
        
        metadata['external_links'] = external_links
        
        return metadata
    
    async def _extract_structured_data(
        self,
        content: str,
        prompt: str,
        schema: Dict,
        url: str
    ) -> Dict:
        """Extract structured data based on schema using regex and simple parsing."""
        structured_data = {}
        
        try:
            # Simple extraction based on schema field names
            for field_name, field_config in schema.items():
                if isinstance(field_config, dict) and 'description' in field_config:
                    description = field_config['description'].lower()
                    
                    # Try to extract based on common patterns
                    if 'email' in description:
                        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
                        structured_data[field_name] = emails[0] if emails else None
                    
                    elif 'phone' in description or 'telephone' in description:
                        phones = re.findall(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', content)
                        structured_data[field_name] = '-'.join(phones[0]) if phones else None
                    
                    elif 'price' in description or 'cost' in description:
                        prices = re.findall(r'\$[\d,]+\.?\d*', content)
                        structured_data[field_name] = prices[0] if prices else None
                    
                    elif 'date' in description:
                        dates = re.findall(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}', content)
                        structured_data[field_name] = dates[0] if dates else None
                    
                    else:
                        # Generic extraction - try to find relevant sentences
                        sentences = content.split('.')
                        relevant_sentences = [
                            s.strip() for s in sentences 
                            if any(word in s.lower() for word in description.split()[:3])
                        ]
                        structured_data[field_name] = relevant_sentences[0] if relevant_sentences else None
                
                else:
                    # If no description, try to extract based on field name
                    field_lower = field_name.lower()
                    if content:
                        if 'title' in field_lower:
                            structured_data[field_name] = content.split('\n')[0]
                        elif 'description' in field_lower:
                            structured_data[field_name] = content[:500]
                        else:
                            structured_data[field_name] = None
                    else:
                        structured_data[field_name] = None
            
        except Exception as e:
            logger.warning(f"Error extracting structured data: {e}")
        
        return structured_data
    
    async def _enhance_with_ai(
        self,
        content: str,
        prompt: str,
        url: str
    ) -> Dict:
        """Enhance extraction using OpenAI."""
        if not self.openai_client:
            return {}
        
        try:
            # Truncate content if too long
            truncated_content = content[:4000]
            
            system_prompt = """You are a web content extraction assistant. 
            Extract the most relevant information from the given webpage content based on the user's prompt.
            Return the result as a JSON object with the extracted information."""
            
            user_prompt = f"""
            URL: {url}
            User Prompt: {prompt}
            
            Content:
            {truncated_content}
            
            Extract relevant information based on the prompt and return as JSON.
            """
            
            response = await self.openai_client.chat.completions.create(
                model=self.llm_config.get('model', 'gpt-3.5-turbo'),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            # Parse the response
            result_text = response.choices[0].message.content
            
            try:
                # Try to parse as JSON
                extracted_data = json.loads(result_text)
                return {"ai_extracted": extracted_data}
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"ai_extracted": {"raw_response": result_text}}
            
        except Exception as e:
            logger.warning(f"AI enhancement failed: {e}")
            return {}
    
    async def search_urls(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for URLs using real search engines."""
        try:
            # Import real search service
            from .real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.multi_search(
                    query=query,
                    engines=['duckduckgo'],  # Use DuckDuckGo as it doesn't require API keys
                    max_results=max_results
                )
            
            # Convert search results to URL format
            urls = []
            for engine, results in search_results.items():
                for result in results:
                    if result.get('url'):
                        urls.append({
                            'url': result['url'],
                            'description': result.get('snippet', result.get('title', f'Found via {engine}')),
                            'title': result.get('title', ''),
                            'source': engine
                        })
            
            # If no results from search engines, provide fallback search URLs
            if not urls:
                urls = [
                    {
                        'url': f'https://duckduckgo.com/?q={query.replace(" ", "+")}',
                        'description': f'Search results for: {query}',
                        'title': f'DuckDuckGo Search: {query}',
                        'source': 'fallback'
                    },
                    {
                        'url': f'https://www.google.com/search?q={query.replace(" ", "+")}',
                        'description': f'Google search for: {query}',
                        'title': f'Google Search: {query}',
                        'source': 'fallback'
                    }
                ]
            
            return urls[:max_results]
            
        except Exception as e:
            logger.error(f"Enhanced search failed: {e}")
            # Fallback to basic search URLs
            return [
                {
                    'url': f'https://duckduckgo.com/?q={query.replace(" ", "+")}',
                    'description': f'Search results for: {query}',
                    'title': f'DuckDuckGo Search: {query}',
                    'source': 'fallback'
                }
            ]
    
    async def validate_config(self) -> bool:
        """Validate if the scraping configuration is working."""
        try:
            # Test HTTP client
            response = await self.http_client.get('https://httpbin.org/get')
            response.raise_for_status()
            
            # Test OpenAI if available
            if self.openai_client:
                # Simple test call
                await self.openai_client.models.list()
            
            logger.info("Enhanced scraping service validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Enhanced scraping service validation failed: {e}")
            return False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.http_client.aclose()