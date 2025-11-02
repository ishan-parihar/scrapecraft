"""
Bridge module to connect AI agent workflows with backend scraping services.
This module implements the integration plan by providing a unified interface
for AI agents to communicate with backend scraping services.
"""

from typing import Dict, Any, List, Optional
import asyncio
import logging

class AIBackendBridge:
    """
    Bridge class to connect AI agents with backend scraping services
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.backend_url = self.config.get("backend_url", "http://localhost:8000")
        # We'll import the adapter dynamically when needed to avoid circular imports
        self._adapter = None
        self.active_tasks = {}
    
    @property
    def scraping_adapter(self):
        """Lazily load the scraping adapter to avoid import issues"""
        if self._adapter is None:
            import importlib.util
            import os
            
            scraper_module_path = os.path.join(os.path.dirname(__file__), 'backend_client', 'scraper.py')
            scraper_spec = importlib.util.spec_from_file_location("scraper", scraper_module_path)
            if scraper_spec and scraper_spec.loader:
                scraper_module = importlib.util.module_from_spec(scraper_spec)
                scraper_spec.loader.exec_module(scraper_module)
                self._adapter = scraper_module.BackendScrapingAdapter(base_url=self.backend_url)
            else:
                raise ImportError("Could not load scraper module")
        return self._adapter

    async def execute_scraping_task(
        self, 
        urls: List[str], 
        prompt: str, 
        schema: Dict = None
    ) -> Dict[str, Any]:
        """
        Execute a scraping task through the backend service
        """
        try:
            result = await self.scraping_adapter.scrape_urls(
                urls=urls, 
                prompt=prompt, 
                schema=schema
            )
            return result
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Scraping task failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def execute_search_and_scrape_task(
        self, 
        query: str, 
        max_results: int = 5, 
        scraping_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Execute a search followed by scraping through the backend service
        """
        try:
            result = await self.scraping_adapter.search_and_scrape(
                query=query,
                max_results=max_results,
                scraping_prompt=scraping_prompt
            )
            return result
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Search and scrape task failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def update_investigation_state(
        self, 
        state: Dict,  # Use dict instead of typed state to avoid import issues
        task_result: Dict[str, Any]
    ) -> Dict:
        """
        Update the investigation state with results from backend services
        """
        # Add backend task tracking to state
        backend_task = {
            "task_id": task_result.get("task_id"),
            "timestamp": asyncio.get_event_loop().time(),
            "result_keys": list(task_result.keys()) if task_result else []
        }
        
        # Append to backend scraping tasks
        if "backend_scraping_tasks" not in state:
            state["backend_scraping_tasks"] = []
        state["backend_scraping_tasks"].append(backend_task)
        
        # Update collected data with new results
        if "collected_data" not in state:
            state["collected_data"] = []
        if task_result.get("success") and task_result.get("results"):
            state["collected_data"].extend(task_result["results"])
        
        # Update URLs scraped
        if "urls_scraped" not in state:
            state["urls_scraped"] = []
        
        # Add any new URLs that were processed
        # This is a simplified approach - in a real implementation,
        # you'd extract URLs from the task_result
        
        return state
    
    async def validate_url(self, url: str) -> bool:
        """
        Validate a URL through the backend service
        """
        try:
            result = await self.scraping_adapter.client.validate_url(url)
            return result.get("valid", False)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"URL validation failed: {str(e)}")
            return False

    def get_active_task_status(self) -> Dict[str, Any]:
        """
        Get status of active backend tasks
        """
        return {
            "active_task_count": len(self.active_tasks),
            "task_ids": list(self.active_tasks.keys())
        }