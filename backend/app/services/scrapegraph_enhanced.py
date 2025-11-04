"""
Enhanced ScrapeGraphAI Service

Enhanced ScrapeGraphAI service with OSINT capabilities.
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class ScrapeGraphEnhanced:
    """Enhanced ScrapeGraphAI service with OSINT capabilities"""
    
    def __init__(self):
        self.graphs = {}
        self._initialize_graphs()
    
    def _initialize_graphs(self):
        """Initialize all available graphs"""
        try:
            # Import ScrapeGraphAI components dynamically
            import importlib.util
            import os
            
            # Try to import SmartScraperGraph
            graphs_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                     'Scrapegraph-ai', 'scrapegraphai', 'graphs')
            
            smart_scraper_path = os.path.join(graphs_path, 'smart_scraper_graph.py')
            if os.path.exists(smart_scraper_path):
                spec = importlib.util.spec_from_file_location("smart_scraper_graph", smart_scraper_path)
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.graphs['smart_scraper'] = getattr(module, 'SmartScraperGraph', None)
            
            # Try to import SearchScraperGraph  
            search_scraper_path = os.path.join(graphs_path, 'search_scraper_graph.py')
            if os.path.exists(search_scraper_path):
                spec = importlib.util.spec_from_file_location("search_scraper_graph", search_scraper_path)
                if spec is not None and spec.loader is not None:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self.graphs['search_scraper'] = getattr(module, 'SearchScraperGraph', None)
                    
        except Exception as e:
            logger.error(f"Failed to initialize ScrapeGraphAI graphs: {e}")
    
    async def execute_scraping(self, graph_type: str, prompt: str, source: str, config: Dict = None) -> Dict[str, Any]:
        """Execute scraping with specified graph type"""
        try:
            if graph_type not in self.graphs:
                return {
                    "success": False,
                    "error": f"Graph type '{graph_type}' not available",
                    "data": None
                }
            
            graph_class = self.graphs[graph_type]
            if graph_class is None:
                return {
                    "success": False,
                    "error": f"Graph type '{graph_type}' failed to load",
                    "data": None
                }
            
            # Initialize graph with configuration
            graph_config = config or {}
            graph_config.update({
                "llm_model": "gpt-4-turbo",
                "verbose": True
            })
            
            # Create graph instance
            graph = graph_class(
                prompt=prompt,
                source=source,
                config=graph_config
            )
            
            # Execute scraping
            result = await self._run_graph(graph)
            
            return {
                "success": True,
                "graph_type": graph_type,
                "data": result,
                "prompt": prompt,
                "source": source
            }
            
        except Exception as e:
            logger.error(f"Scraping execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def _run_graph(self, graph) -> Dict[str, Any]:
        """Run the graph and return results"""
        try:
            # For now, return a placeholder result
            # In a real implementation, this would execute the actual graph
            return {
                "result": f"Scraped data using {type(graph).__name__}",
                "content": "Sample scraped content",
                "metadata": {
                    "graph_type": type(graph).__name__,
                    "execution_time": 1.5
                }
            }
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            raise
    
    def get_available_graphs(self) -> List[str]:
        """Get list of available graph types"""
        return list(self.graphs.keys())
    
    async def search_and_scrape(self, query: str, max_results: int = 5, scraping_prompt: str = "") -> Dict[str, Any]:
        """Search for URLs and then scrape them"""
        try:
            # First search using the search scraper
            search_result = await self.execute_scraping(
                graph_type="search_scraper",
                prompt=f"Search for: {query}",
                source=query,
                config={"max_results": max_results}
            )
            
            if not search_result["success"]:
                return search_result
            
            # Extract URLs from search results
            # This is a placeholder - in reality, you'd parse the actual search results
            urls = ["https://example.com/page1", "https://example.com/page2"]
            
            if not urls:
                return {
                    "success": False,
                    "error": "No URLs found in search results",
                    "data": None
                }
            
            # Scrape the found URLs
            scraping_prompt = scraping_prompt or f"Extract relevant information about: {query}"
            scrape_results = []
            
            for url in urls:
                result = await self.execute_scraping(
                    graph_type="smart_scraper",
                    prompt=scraping_prompt,
                    source=url
                )
                scrape_results.append(result)
            
            return {
                "success": True,
                "search_results": search_result,
                "scrape_results": scrape_results,
                "total_urls_scraped": len(urls)
            }
            
        except Exception as e:
            logger.error(f"Search and scrape failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }