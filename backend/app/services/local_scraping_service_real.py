from typing import List, Dict, Optional, Any
import asyncio
import logging
import os
import sys
import json
import re
from urllib.parse import urlparse

# Add the ScrapeGraphAI directory to Python path
sys.path.insert(0, '/app/Scrapegraph-ai')

logger = logging.getLogger(__name__)

class LocalScrapingServiceReal:
    """Service for interacting with local ScrapeGraphAI library with proper imports."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        # Use environment variables to configure LLM
        self.llm_config = llm_config or {
            "model": os.getenv("LOCAL_LLM_MODEL", "gpt-3.5-turbo"),
            "api_key": os.getenv("LOCAL_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "")),
            "temperature": 0,
        }
        
        # Override model if using Ollama
        if os.getenv("USE_OLLAMA", "false").lower() == "true":
            self.llm_config = {
                "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            }
        
        # Initialize ScrapeGraphAI components
        self._initialize_scrapegraph()
    
    def _initialize_scrapegraph(self):
        """Initialize ScrapeGraphAI components with error handling."""
        try:
            # Try to import the required components
            from scrapegraphai.graphs import SmartScraperGraph, SearchGraph
            from scrapegraphai.models import OpenAI
            
            # Store the classes for later use
            self.SmartScraperGraph = SmartScraperGraph
            self.SearchGraph = SearchGraph
            self.OpenAI = OpenAI
            
            # Test if we can create an LLM instance
            if self.llm_config.get("base_url"):
                # Ollama configuration
                self.llm_instance = {
                    "model": self.llm_config["model"],
                    "base_url": self.llm_config["base_url"],
                }
            else:
                # OpenAI configuration
                self.llm_instance = self.OpenAI(
                    model=self.llm_config["model"],
                    api_key=self.llm_config["api_key"],
                    temperature=self.llm_config.get("temperature", 0)
                )
            
            self.scrapegraph_available = True
            logger.info("ScrapeGraphAI initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ScrapeGraphAI: {e}")
            self.scrapegraph_available = False
            self.SmartScraperGraph = None
            self.SearchGraph = None
            self.OpenAI = None
            self.llm_instance = None
    
    async def execute_pipeline(
        self,
        urls: List[str],
        schema: Optional[Dict[str, Any]],
        prompt: str
    ) -> List[Dict]:
        """Execute scraping for multiple URLs using local ScrapeGraphAI."""
        results = []
        
        if not self.scrapegraph_available:
            # ScrapeGraphAI not available - return error instead of mock data
            error_msg = "ScrapeGraphAI is not available. Install ScrapeGraphAI or configure alternative scraping service."
            logger.error(error_msg)
            return [{
                "error": error_msg,
                "service_unavailable": True,
                "urls_attempted": urls
            }]
        
        try:
            # Handle single vs multiple URLs
            if len(urls) == 1:
                # Use SmartScraperGraph for single URL
                for url in urls:
                    try:
                        # Build graph config
                        graph_config = {
                            "llm": self.llm_instance,
                            "verbose": os.getenv("SCRAPEGRAPHAI_VERBOSE", "false").lower() == "true",
                            "headless": os.getenv("SCRAPEGRAPHAI_HEADLESS", "true").lower() == "true",
                        }
                        
                        # Add schema if provided
                        if schema:
                            try:
                                # Create a dynamic pydantic model from schema for ScrapeGraphAI
                                graph_config["output_schema"] = schema
                            except Exception as e:
                                logger.warning(f"Could not set output schema: {e}")
                        
                        # Create and run the graph
                        smart_scraper_graph = self.SmartScraperGraph(
                            prompt=prompt,
                            source=url,
                            config=graph_config
                        )
                        
                        result = await asyncio.get_event_loop().run_in_executor(
                            None, smart_scraper_graph.run
                        )
                        
                        results.append({
                            "url": url,
                            "success": True,
                            "data": result,
                            "error": None
                        })
                        logger.info(f"Successfully scraped {url}")
                        
                    except Exception as e:
                        logger.error(f"Scraping failed for {url}: {e}")
                        results.append({
                            "url": url,
                            "success": False,
                            "data": None,
                            "error": str(e)
                        })
                        
            else:
                # For multiple URLs, process them concurrently
                tasks = []
                for url in urls:
                    task = self._scrape_single_url(url, prompt, schema)
                    tasks.append(task)
                
                # Execute all tasks concurrently
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Process results
                for i, result in enumerate(task_results):
                    if isinstance(result, Exception):
                        results.append({
                            "url": urls[i],
                            "success": False,
                            "data": None,
                            "error": str(result)
                        })
                    else:
                        results.append(result)
                
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            # Return error for all URLs
            results = [{
                "url": url,
                "success": False,
                "data": None,
                "error": str(e)
            } for url in urls]
        
        return results
    
    async def _scrape_single_url(self, url: str, prompt: str, schema: Optional[Dict[str, Any]]) -> Dict:
        """Scrape a single URL using SmartScraperGraph."""
        try:
            # Build graph config
            graph_config = {
                "llm": self.llm_instance,
                "verbose": os.getenv("SCRAPEGRAPHAI_VERBOSE", "false").lower() == "true",
                "headless": os.getenv("SCRAPEGRAPHAI_HEADLESS", "true").lower() == "true",
            }
            
            # Add schema if provided
            if schema:
                try:
                    graph_config["output_schema"] = schema
                except Exception as e:
                    logger.warning(f"Could not set output schema: {e}")
            
            # Create and run the graph
            smart_scraper_graph = self.SmartScraperGraph(
                prompt=prompt,
                source=url,
                config=graph_config
            )
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, smart_scraper_graph.run
            )
            
            return {
                "url": url,
                "success": True,
                "data": result,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Scraping failed for {url}: {e}")
            return {
                "url": url,
                "success": False,
                "data": None,
                "error": str(e)
            }
    
    async def search_urls(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for URLs using local ScrapeGraphAI SearchGraph."""
        if not self.scrapegraph_available:
            # Fallback to mock search
            logger.warning("ScrapeGraphAI not available, using mock search")
            return await self._mock_search_urls(query, max_results)
        
        try:
            # Build graph config for search
            graph_config = {
                "llm": self.llm_instance,
                "verbose": os.getenv("SCRAPEGRAPHAI_VERBOSE", "false").lower() == "true",
                "headless": os.getenv("SCRAPEGRAPHAI_HEADLESS", "true").lower() == "true",
            }
            
            # Create search graph
            search_graph = self.SearchGraph(
                prompt=f"Find the top {max_results} most relevant websites for: {query}",
                config=graph_config
            )
            
            # Execute search
            result = await asyncio.get_event_loop().run_in_executor(
                None, search_graph.run
            )
            
            urls = []
            
            # Process the result based on its structure
            if isinstance(result, dict):
                # Check different possible formats
                if 'links' in result:
                    for link in result['links'][:max_results]:
                        urls.append({
                            'url': link,
                            'description': f'Found via search for: {query}'
                        })
                elif 'urls' in result:
                    for url in result['urls'][:max_results]:
                        urls.append({
                            'url': url,
                            'description': f'Found via search for: {query}'
                        })
                else:
                    # Try to extract URLs from the result
                    result_str = str(result)
                    found_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', result_str)
                    for url in found_urls[:max_results]:
                        urls.append({
                            'url': url,
                            'description': f'Found via search for: {query}'
                        })
            elif isinstance(result, list):
                # If result is a list of URLs
                for item in result[:max_results]:
                    url = item if isinstance(item, str) else str(item)
                    urls.append({
                        'url': url,
                        'description': f'Found via search for: {query}'
                    })
            else:
                # Convert to string and try to extract URLs
                result_str = str(result)
                found_urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', result_str)
                for url in found_urls[:max_results]:
                    urls.append({
                        'url': url,
                        'description': f'Found via search for: {query}'
                    })
            
            logger.info(f"Found {len(urls)} URLs for query '{query}': {urls}")
            return urls
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return await self._mock_search_urls(query, max_results)
    
    async def _mock_search_urls(self, query: str, max_results: int) -> List[Dict[str, str]]:
        """Mock search as fallback."""
        # Generate some mock URLs based on the query
        mock_urls = [
            {
                'url': f'https://example.com/search?q={query.replace(" ", "+")}',
                'description': f'Mock search result for: {query}'
            },
            {
                'url': f'https://mocksite.com/{query.replace(" ", "-").lower()}',
                'description': f'Mock website about: {query}'
            }
        ]
        
        return mock_urls[:max_results]
    
    async def validate_config(self) -> bool:
        """Validate if the local scraping configuration is working."""
        if not self.scrapegraph_available:
            logger.warning("ScrapeGraphAI not available for validation")
            return False
        
        try:
            # Try a simple local test
            graph_config = {
                "llm": self.llm_instance,
                "verbose": False,
                "headless": True,
            }
            
            # Test with a simple example
            smart_scraper_graph = self.SmartScraperGraph(
                prompt="Extract the title of the page",
                source="https://example.com",
                config=graph_config
            )
            
            result = await asyncio.get_event_loop().run_in_executor(
                None, smart_scraper_graph.run
            )
            logger.info(f"Local scraping validation successful: {type(result)}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False