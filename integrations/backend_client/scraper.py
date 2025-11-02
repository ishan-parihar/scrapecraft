import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)

class BackendScrapingClient:
    """
    Client for interacting with backend scraping services API
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_scraping(self, urls: List[str], prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute scraping task via backend API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/execute"
        payload = {
            "urls": urls,
            "prompt": prompt,
            "schema": schema
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Scraping execution failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except asyncio.TimeoutError:
            logger.error("Scraping execution timed out")
            return {"error": "Request timed out", "success": False}
        except Exception as e:
            logger.error(f"Scraping execution error: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a scraping task"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/status/{task_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Get task status failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except Exception as e:
            logger.error(f"Get task status error: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def get_task_results(self, task_id: str) -> List[Dict[str, Any]]:
        """Get results of a completed scraping task"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/results/{task_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Get task results failed: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Get task results error: {str(e)}")
            return []
    
    async def search_urls(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for URLs using backend service"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/search"
        payload = {"query": query, "max_results": max_results}
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("results", [])
                else:
                    error_text = await response.text()
                    logger.error(f"URL search failed: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"URL search error: {str(e)}")
            return []
    
    async def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate a URL using backend service"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        validate_url = f"{self.base_url}/api/scraping/validate-url"
        payload = {"url": url}
        
        try:
            async with self.session.post(validate_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"URL validation failed: {response.status} - {error_text}")
                    return {"valid": False, "error": error_text}
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            return {"valid": False, "error": str(e)}


class BackendScrapingAdapter:
    """
    Adapter to integrate backend scraping services with AI agent tools
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = BackendScrapingClient(base_url)
    
    async def scrape_urls(self, urls: List[str], prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape URLs using backend services
        """
        async with self.client as client:
            # Start scraping task
            execution_result = await client.execute_scraping(urls, prompt, schema)
            
            if not execution_result.get("success"):
                return {
                    "success": False,
                    "error": execution_result.get("error", "Unknown error"),
                    "data": None
                }
            
            # Get the task ID
            task_id = execution_result.get("task_id")
            if not task_id:
                return {
                    "success": False,
                    "error": "No task ID returned from backend",
                    "data": None
                }
            
            # Poll for task completion
            max_retries = 20  # 20 * 3 seconds = 60 seconds max wait
            retry_count = 0
            
            while retry_count < max_retries:
                status_result = await client.get_task_status(task_id)
                
                if status_result.get("status") == "completed":
                    # Get results
                    results = await client.get_task_results(task_id)
                    return {
                        "success": True,
                        "task_id": task_id,
                        "results": results,
                        "data": results
                    }
                elif status_result.get("status") in ["failed", "error"]:
                    return {
                        "success": False,
                        "error": status_result.get("error", "Task failed"),
                        "data": None
                    }
                
                # Wait before next check
                await asyncio.sleep(3)
                retry_count += 1
            
            return {
                "success": False,
                "error": "Task timeout - still running after maximum wait time",
                "data": None
            }
    
    async def search_and_scrape(self, query: str, max_results: int = 5, scraping_prompt: str = "") -> Dict[str, Any]:
        """
        Search for URLs and then scrape them
        """
        async with self.client as client:
            # First search for URLs
            search_results = await client.search_urls(query, max_results)
            
            if not search_results:
                return {
                    "success": False,
                    "error": "No URLs found for query",
                    "data": None
                }
            
            # Extract URLs
            urls = []
            for item in search_results:
                url = item.get("url")
                if url is not None:
                    urls.append(url)
            
            # Then scrape the URLs
            scraping_prompt = scraping_prompt or f"Extract all relevant information about: {query}"
            
            return await self.scrape_urls(urls, scraping_prompt)