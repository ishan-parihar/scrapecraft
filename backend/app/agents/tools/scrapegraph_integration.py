import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)

# Direct scraping implementation to avoid circular calls
class DirectScrapingClient:
    """
    Direct HTTP scraper that doesn't rely on backend APIs
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """Scrape a single URL directly"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    
                    # Extract basic content
                    title = soup.find('title')
                    title_text = title.get_text().strip() if title else ""
                    
                    # Extract main content (common selectors)
                    content_selectors = [
                        'main', 'article', '[role="main"]', 
                        '.content', '.main-content', '#content'
                    ]
                    
                    main_content = ""
                    for selector in content_selectors:
                        element = soup.select_one(selector)
                        if element:
                            main_content = element.get_text().strip()
                            break
                    
                    # Fallback to body if no main content found
                    if not main_content:
                        body = soup.find('body')
                        if body:
                            main_content = body.get_text().strip()
                    
                    return {
                        "success": True,
                        "url": url,
                        "title": title_text,
                        "content": main_content[:5000],  # Limit content length
                        "status_code": response.status
                    }
                else:
                    return {
                        "success": False,
                        "url": url,
                        "error": f"HTTP {response.status}",
                        "status_code": response.status
                    }
        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    async def scrape_urls(self, urls: List[str]) -> List[Dict[str, Any]]:
        """Scrape multiple URLs concurrently"""
        tasks = [self.scrape_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Convert exceptions to error results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "url": urls[i],
                    "error": str(result)
                })
            else:
                processed_results.append(result)
        
        return processed_results

# Adapter to integrate direct scraping with AI agent tools
class BackendScrapingAdapter:
    """
    Adapter to integrate direct scraping services with AI agent tools
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url  # Kept for compatibility but not used
        self.client = DirectScrapingClient()
    
    async def scrape_urls(self, urls: List[str], prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape URLs using direct HTTP requests
        """
        async with self.client as client:
            results = await client.scrape_urls(urls)
            
            # Filter successful results
            successful_results = [r for r in results if r.get("success")]
            failed_results = [r for r in results if not r.get("success")]
            
            if not successful_results:
                return {
                    "success": False,
                    "error": f"All scraping attempts failed: {[r.get('error', 'Unknown error') for r in failed_results]}",
                    "data": None
                }
            
            # Apply prompt-based filtering (simple keyword matching)
            if prompt:
                prompt_keywords = prompt.lower().split()
                filtered_results = []
                
                for result in successful_results:
                    content = result.get("content", "").lower()
                    title = result.get("title", "").lower()
                    
                    # Check if any prompt keywords are in the content
                    if any(keyword in content or keyword in title for keyword in prompt_keywords):
                        filtered_results.append(result)
                
                successful_results = filtered_results
            
            return {
                "success": True,
                "results": successful_results,
                "data": successful_results,
                "total_urls": len(urls),
                "successful_scrapes": len(successful_results),
                "failed_scrapes": len(failed_results)
            }
    
    async def search_and_scrape(self, query: str, max_results: int = 5, scraping_prompt: str = "") -> Dict[str, Any]:
        """
        Note: This method would need a search service. For now, return error to use proper search service
        """
        return {
            "success": False,
            "error": "Direct search not implemented. Use RealSearchService for searching, then call scrape_urls directly.",
            "data": None
        }

# Keep the old import structure for compatibility but don't use it
def _import_backend_client():
    """Placeholder to maintain compatibility"""
    raise ImportError("BackendScrapingClient not used - replaced with DirectScrapingClient")

# Get the module and class (placeholder)
try:
    import importlib.util
    import os
    
    client_module_path = os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'backend_scraping_client.py')
    spec = importlib.util.spec_from_file_location("backend_scraping_client", client_module_path)
    if spec is not None and spec.loader is not None:
        backend_scraping_client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_scraping_client_module)
        BackendScrapingClient = backend_scraping_client_module.BackendScrapingClient
    else:
        BackendScrapingClient = None
except:
    BackendScrapingClient = None