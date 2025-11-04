import asyncio
from typing import List, Dict, Any, Optional
import importlib.util
import os

# Dynamically import the BackendScrapingClient
def _import_backend_client():
    client_module_path = os.path.join(os.path.dirname(__file__), '..', 'clients', 'backend_scraping_client.py')
    spec = importlib.util.spec_from_file_location("backend_scraping_client", client_module_path)
    if spec is not None and spec.loader is not None:
        backend_scraping_client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(backend_scraping_client_module)
        return backend_scraping_client_module
    else:
        raise ImportError("Could not load backend scraping client module")

# Get the module and class
_client_module = _import_backend_client()
BackendScrapingClient = _client_module.BackendScrapingClient

# Add a class to handle the integration
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
            urls = [item.get("url") for item in search_results if item.get("url")]
            
            # Then scrape the URLs
            scraping_prompt = scraping_prompt or f"Extract all relevant information about: {query}"
            
            return await self.scrape_urls(urls, scraping_prompt)