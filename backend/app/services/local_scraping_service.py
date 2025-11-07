from typing import List, Dict, Optional, Any
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List as ListType
import os
import sys

logger = logging.getLogger(__name__)

# Import compatibility shim for langchain
try:
    from .langchain_compatibility import LangchainPrompts, LangchainOutputParsers
    sys.modules['langchain.prompts'] = LangchainPrompts()
    sys.modules['langchain.output_parsers'] = LangchainOutputParsers()
    logger.info("Langchain compatibility shim loaded")
except Exception as e:
    logger.warning(f"Could not load compatibility shim: {e}")

# Import from local ScrapeGraphAI - temporarily disabled for testing
try:
    from scrapegraphai.graphs import SmartScraperGraph, SearchGraph, SmartScraperMultiGraph
    from scrapegraphai.models import OpenAI
    SCRAPEGRAPH_AVAILABLE = True
except ImportError as e:
    logger.warning(f"ScrapeGraphAI not available: {e}")
    SmartScraperGraph = None
    SearchGraph = None
    SmartScraperMultiGraph = None
    OpenAI = None
    SCRAPEGRAPH_AVAILABLE = False

class LocalScrapingService:
    """Service for interacting with local ScrapeGraphAI library."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        # Use environment variables to configure LLM
        # Default to a free/local-friendly model configuration
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
    
    async def execute_pipeline(
        self,
        urls: List[str],
        schema: Optional[Dict[str, Any]],
        prompt: str
    ) -> List[Dict]:
        """Execute scraping for multiple URLs using local ScrapeGraphAI."""
        results = []
        
        if not SCRAPEGRAPH_AVAILABLE:
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
                            "llm": self.llm_config,
                            "verbose": True,
                            "headless": True,
                        }
                        
                        # Add schema if provided
                        if schema:
                            try:
                                # Create a dynamic pydantic model from schema for ScrapeGraphAI
                                import json
                                graph_config["output_schema"] = schema
                            except Exception as e:
                                logger.warning(f"Could not set output schema: {e}")
                        
                        # Create and run the graph
                        smart_scraper_graph = SmartScraperGraph(
                            prompt=prompt,
                            source=url,
                            config=graph_config
                        )
                        
                        result = smart_scraper_graph.run()
                        
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
                # Use SmartScraperMultiGraph for multiple URLs
                try:
                    graph_config = {
                        "llm": self.llm_config,
                        "verbose": True,
                        "headless": True,
                    }
                    
                    # Add schema if provided
                    if schema:
                        try:
                            graph_config["output_schema"] = schema
                        except Exception as e:
                            logger.warning(f"Could not set output schema: {e}")
                    
                    # Create multi graph
                    smart_scraper_multi_graph = SmartScraperMultiGraph(
                        prompt=prompt,
                        sources=urls,
                        config=graph_config
                    )
                    
                    # Execute with error handling for each URL
                    results_dict = smart_scraper_multi_graph.run()
                    
                    # Format results to match expected format
                    for url in urls:
                        if url in results_dict:
                            results.append({
                                "url": url,
                                "success": True,
                                "data": results_dict[url],
                                "error": None
                            })
                        else:
                            results.append({
                                "url": url,
                                "success": False,
                                "data": None,
                                "error": "No result returned for this URL"
                            })
                            
                except Exception as e:
                    logger.error(f"Multi-scraping failed: {e}")
                    # Return error for all URLs
                    results = [{
                        "url": url,
                        "success": False,
                        "data": None,
                        "error": str(e)
                    } for url in urls]
                
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
    
    async def search_urls(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for URLs using local ScrapeGraphAI SearchGraph."""
        if not SCRAPEGRAPH_AVAILABLE:
            # ScrapeGraphAI not available - return error instead of mock data
            error_msg = "ScrapeGraphAI is not available. Install ScrapeGraphAI or configure alternative search service."
            logger.error(error_msg)
            return [{
                "error": error_msg,
                "service_unavailable": True,
                "query": query
            }]
        
        try:
            # Build graph config for search
            graph_config = {
                "llm": self.llm_config,
                "max_results": max_results,
                "verbose": True,
                "headless": True,
            }
            
            # Create search graph - use duckduckgo search as it's free
            search_graph = SearchGraph(
                prompt=f"Find the top {max_results} most relevant websites for: {query}",
                config=graph_config
            )
            
            # Execute search
            result = search_graph.run()
            
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
                    import re
                    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                    found_urls = re.findall(url_pattern, result_str)
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
                import re
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                found_urls = re.findall(url_pattern, result_str)
                for url in found_urls[:max_results]:
                    urls.append({
                        'url': url,
                        'description': f'Found via search for: {query}'
                    })
            
            logger.info(f"Found {len(urls)} URLs for query '{query}': {urls}")
            return urls
            
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            return [{
                "error": f"Search unavailable: {e}",
                "service_unavailable": True,
                "query": query
            }]
    
    async def validate_config(self) -> bool:
        """Validate if the local scraping configuration is working."""
        if not SCRAPEGRAPH_AVAILABLE:
            logger.warning("ScrapeGraphAI not available for validation")
            return False
        
        try:
            # Try a simple local test
            graph_config = {
                "llm": self.llm_config,
                "verbose": False,
                "headless": True,
            }
            
            # Test with a simple example
            smart_scraper_graph = SmartScraperGraph(
                prompt="Extract the title of the page",
                source="https://example.com",
                config=graph_config
            )
            
            result = smart_scraper_graph.run()
            logger.info(f"Local scraping validation successful: {type(result)}")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
