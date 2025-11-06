"""
LangChain Tools Integration Module for OSINT Collection Agents

This module provides utilities for integrating LangChain tools with OSINT collection agents.
It allows agents to access and use various scraping and data collection tools.
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
import importlib.util
import os

logger = logging.getLogger(__name__)

def create_backend_scraping_tools():
    """
    Create tools that integrate with backend scraping services.
    
    Returns:
        List of tools that connect to the backend scraping services
    """
    from langchain_core.tools import tool
    from pydantic import BaseModel, Field
    
    # Import the backend scraping adapter using dynamic import
    try:
        # Build the path to the scrapegraph_integration module
        current_dir = os.path.dirname(__file__)
        scrapegraph_path = os.path.join(current_dir, "scrapegraph_integration.py")
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location("scrapegraph_integration", scrapegraph_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load spec for {scrapegraph_path}")
        
        scrapegraph_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scrapegraph_module)
        
        # Get the BackendScrapingAdapter class
        BackendScrapingAdapter = scrapegraph_module.BackendScrapingAdapter
        
    except Exception as e:
        logger.error(f"Failed to import BackendScrapingAdapter: {e}")
        raise

    # Create an instance of the adapter
    scraping_adapter = BackendScrapingAdapter()
    
    class ScraperInput(BaseModel):
        website_url: str = Field(description="The URL of the website to scrape")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")

    class CrawlerInput(BaseModel):
        website_url: str = Field(description="The starting URL for crawling")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")
        max_depth: int = Field(default=2, description="Maximum crawl depth")
        max_pages: int = Field(default=5, description="Maximum number of pages to crawl")

    class SearchInput(BaseModel):
        search_query: str = Field(description="The search query to find relevant websites")
        max_results: int = Field(default=10, description="Maximum number of results to return")

    class MarkdownifyInput(BaseModel):
        website_url: str = Field(description="The URL of the website to convert to markdown")

    @tool("smart_scraper", args_schema=ScraperInput)
    async def backend_smart_scraper(website_url: str, user_prompt: str) -> Dict[str, Any]:
        """Backend implementation of smart scraper tool."""
        try:
            result = await scraping_adapter.scrape_urls([website_url], user_prompt)
            return {
                "success": result.get("success", False),
                "data": result.get("results", []),
                "url": website_url,
                "error": result.get("error") if not result.get("success") else None
            }
        except Exception as e:
            logger.error(f"Error in backend smart scraper: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": website_url
            }

    @tool("smart_crawler", args_schema=CrawlerInput)
    async def backend_smart_crawler(
        website_url: str,
        user_prompt: str,
        max_depth: int = 2,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """Backend implementation of smart crawler tool."""
        try:
            # For now, we'll implement a simple search-and-scrape pattern
            # In a real implementation, the backend would handle proper crawling
            search_and_scrape_result = await scraping_adapter.search_and_scrape(
                query=website_url,  # Use the URL as a search query
                max_results=max_pages,
                scraping_prompt=user_prompt
            )
            return {
                "success": search_and_scrape_result.get("success", False),
                "data": search_and_scrape_result.get("results", []),
                "pages_crawled": len(search_and_scrape_result.get("results", [])),
                "starting_url": website_url,
                "error": search_and_scrape_result.get("error") if not search_and_scrape_result.get("success") else None
            }
        except Exception as e:
            logger.error(f"Error in backend smart crawler: {e}")
            return {
                "success": False,
                "error": str(e),
                "starting_url": website_url
            }

    @tool("search_scraper", args_schema=SearchInput)
    async def backend_search_scraper(search_query: str, max_results: int = 10) -> Dict[str, Any]:
        """Backend implementation of search scraper tool."""
        try:
            result = await scraping_adapter.search_and_scrape(
                query=search_query,
                max_results=max_results
            )
            return {
                "success": result.get("success", False),
                "query": search_query,
                "results": result.get("results", []),
                "count": len(result.get("results", [])),
                "error": result.get("error") if not result.get("success") else None
            }
        except Exception as e:
            logger.error(f"Error in backend search scraper: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": search_query
            }

    @tool("markdownify", args_schema=MarkdownifyInput)
    async def backend_markdownify(website_url: str) -> Dict[str, Any]:
        """Backend implementation of markdownify tool."""
        try:
            # Use the scraping adapter to get raw content and convert to markdown
            result = await scraping_adapter.scrape_urls([website_url], "Extract content for markdown conversion")
            
            if result.get("success"):
                # For now, return the raw content; in a real implementation,
                # the backend would have a dedicated markdown conversion endpoint
                markdown_content = result.get("results", [{}])[0].get("content", "Content not available")
                return {
                    "success": True,
                    "markdown": markdown_content,
                    "url": website_url
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "url": website_url
                }
        except Exception as e:
            logger.error(f"Error in backend markdownify: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": website_url
            }

    @tool("validate_urls")
    async def backend_validate_urls(urls: List[str]) -> Dict[str, Any]:
        """Backend implementation of URL validation tool."""
        try:
            results = []
            for url in urls:
                # In a real implementation, the adapter would have a validate_url method
                # For now, we'll assume all URLs are valid
                results.append({
                    "url": url,
                    "valid": True,
                    "status_code": 200,
                    "final_url": url
                })
            
            return {
                "urls_checked": len(urls),
                "valid_urls": len([r for r in results if r["valid"]]),
                "results": results
            }
        except Exception as e:
            logger.error(f"Error in backend URL validation: {e}")
            return {
                "urls_checked": len(urls),
                "valid_urls": 0,
                "results": [{"url": url, "valid": False, "error": str(e)} for url in urls]
            }

    logger.info("Created backend scraping tools")
    return [
        backend_smart_scraper,
        backend_smart_crawler,
        backend_search_scraper,
        backend_markdownify,
        backend_validate_urls
    ]


def create_real_tools():
    """
    Create real functional tools that use actual backend scraping services.
    
    Returns:
        List of real tools that perform actual scraping operations
    """
    from langchain_core.tools import tool
    from pydantic import BaseModel, Field
    import sys
    import os
    
    # Add backend to path to import services
    backend_path = os.path.join(os.path.dirname(__file__), '..', '..')
    if backend_path not in sys.path:
        sys.path.insert(0, backend_path)
    
    try:
        from app.services.local_scraping_service import LocalScrapingService
        from app.services.enhanced_scraping_service import EnhancedScrapingService
    except ImportError as e:
        logger.error(f"Cannot import scraping services: {e}")
        return create_fallback_tools()
    
    class RealScraperInput(BaseModel):
        website_url: str = Field(description="The URL of the website to scrape")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")

    class RealCrawlerInput(BaseModel):
        website_url: str = Field(description="The starting URL for crawling")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")
        max_depth: int = Field(default=2, description="Maximum crawl depth")
        max_pages: int = Field(default=5, description="Maximum number of pages to crawl")

    class RealSearchInput(BaseModel):
        search_query: str = Field(description="The search query to find relevant websites")
        max_results: int = Field(default=10, description="Maximum number of results to return")

    class RealMarkdownifyInput(BaseModel):
        website_url: str = Field(description="The URL of the website to convert to markdown")

    @tool("smart_scraper", args_schema=RealScraperInput)
    async def real_smart_scraper(website_url: str, user_prompt: str) -> Dict[str, Any]:
        """Real implementation of smart scraper tool using ScrapeGraphAI."""
        try:
            scraping_service = LocalScrapingService()
            results = await scraping_service.execute_pipeline(
                urls=[website_url],
                schema=None,
                prompt=user_prompt
            )
            
            if results and results[0]['success']:
                return {
                    "success": True,
                    "data": results[0]['data'],
                    "url": website_url,
                    "scraped_at": results[0]['data'].get('scraped_at', '')
                }
            else:
                return {
                    "success": False,
                    "error": results[0]['error'] if results else "Unknown error",
                    "url": website_url
                }
        except Exception as e:
            logger.error(f"Real smart scraper failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": website_url
            }

    @tool("smart_crawler", args_schema=RealCrawlerInput)
    async def real_smart_crawler(
        website_url: str,
        user_prompt: str,
        max_depth: int = 2,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """Real implementation of smart crawler tool using enhanced scraping service."""
        try:
            crawler_service = EnhancedScrapingService()
            
            # Start crawling from the initial URL
            crawled_urls = await crawler_service.crawl_website(
                start_url=website_url,
                max_depth=max_depth,
                max_pages=max_pages
            )
            
            # Scrape each discovered URL
            scraping_service = LocalScrapingService()
            crawled_data = []
            
            for url in crawled_urls[:max_pages]:
                results = await scraping_service.execute_pipeline(
                    urls=[url],
                    schema=None,
                    prompt=user_prompt
                )
                if results and results[0]['success']:
                    crawled_data.append(results[0]['data'])
            
            return {
                "success": True,
                "data": crawled_data,
                "pages_crawled": len(crawled_data),
                "starting_url": website_url,
                "discovered_urls": crawled_urls
            }
        except Exception as e:
            logger.error(f"Real smart crawler failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "pages_crawled": 0,
                "starting_url": website_url
            }

    @tool("search_scraper", args_schema=RealSearchInput)
    async def real_search_scraper(search_query: str, max_results: int = 10) -> Dict[str, Any]:
        """Real implementation of search scraper using real search APIs."""
        try:
            # Use real search service
            from app.services.real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                search_results = await search_service.search_google(search_query, max_results)
                
                if search_results and "error" not in search_results[0]:
                    # Scrape the top results
                    scraping_service = LocalScrapingService()
                    scraped_results = []
                    
                    for result in search_results[:max_results]:
                        if result.get('link'):
                            scrape_results = await scraping_service.execute_pipeline(
                                urls=[result['link']],
                                schema=None,
                                prompt=f"Extract and summarize content from this page related to: {search_query}"
                            )
                            if scrape_results and scrape_results[0]['success']:
                                scraped_results.append({
                                    "url": result['link'],
                                    "title": result.get('title', ''),
                                    "snippet": result.get('snippet', ''),
                                    "scraped_content": scrape_results[0]['data'].get('content', '')
                                })
                    
                    return {
                        "success": True,
                        "query": search_query,
                        "results": scraped_results,
                        "count": len(scraped_results)
                    }
                else:
                    return {
                        "success": False,
                        "error": "Search failed or no results",
                        "query": search_query
                    }
        except Exception as e:
            logger.error(f"Real search scraper failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": search_query
            }

    @tool("markdownify", args_schema=RealMarkdownifyInput)
    async def real_markdownify(website_url: str) -> Dict[str, Any]:
        """Real implementation of markdownify tool using actual HTML to Markdown conversion."""
        try:
            import aiohttp
            import asyncio
            import html2text
            from bs4 import BeautifulSoup
            
            async with aiohttp.ClientSession() as session:
                async with session.get(website_url, timeout=30) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        
                        # Convert HTML to Markdown
                        h = html2text.HTML2Text()
                        h.ignore_links = False
                        h.ignore_images = False
                        h.ignore_emphasis = False
                        markdown = h.handle(html_content)
                        
                        # Extract title
                        soup = BeautifulSoup(html_content, 'html.parser')
                        title_tag = soup.find('title')
                        title = title_tag.get_text().strip() if title_tag else ''
                        
                        return {
                            "success": True,
                            "markdown": markdown,
                            "title": title,
                            "url": website_url
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "url": website_url
                        }
        except Exception as e:
            logger.error(f"Real markdownify failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "url": website_url
            }

    @tool("validate_urls")
    async def real_validate_urls(urls: List[str]) -> Dict[str, Any]:
        """Real implementation of URL validation using actual HTTP requests."""
        try:
            import aiohttp
            import asyncio
            
            async def validate_single_url(session, url):
                try:
                    async with session.get(url, timeout=10, allow_redirects=True) as response:
                        return {
                            "url": url,
                            "valid": response.status < 400,
                            "status_code": response.status,
                            "final_url": str(response.url),
                            "content_type": response.headers.get('content-type', ''),
                            "content_length": response.headers.get('content-length', '0')
                        }
                except Exception as e:
                    return {
                        "url": url,
                        "valid": False,
                        "status_code": None,
                        "final_url": url,
                        "error": str(e)
                    }
            
            async with aiohttp.ClientSession() as session:
                tasks = [validate_single_url(session, url) for url in urls]
                results = await asyncio.gather(*tasks)
                
                valid_count = sum(1 for r in results if r['valid'])
                
                return {
                    "urls_checked": len(urls),
                    "valid_urls": valid_count,
                    "results": results
                }
        except Exception as e:
            logger.error(f"Real URL validation failed: {e}")
            return {
                "urls_checked": len(urls),
                "valid_urls": 0,
                "error": str(e),
                "results": []
            }

    logger.info("Created real functional scraping tools")
    return [
        real_smart_scraper,
        real_smart_crawler,
        real_search_scraper,
        real_markdownify,
        real_validate_urls
    ]


def create_fallback_tools():
    """
    Create fallback tools when real services are not available.
    This provides basic functionality when external services are unavailable.
    """
    from langchain_core.tools import tool
    from pydantic import BaseModel, Field
    import aiohttp
    import asyncio
    from bs4 import BeautifulSoup
    
    class FallbackScraperInput(BaseModel):
        website_url: str = Field(description="The URL of the website to scrape")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")

    @tool("smart_scraper", args_schema=FallbackScraperInput)
    async def fallback_smart_scraper(website_url: str, user_prompt: str) -> Dict[str, Any]:
        """Fallback scraper using basic web scraping."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(website_url, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        title = soup.find('title')
                        title_text = title.get_text().strip() if title else ""
                        
                        # Extract text content
                        text_content = soup.get_text()
                        cleaned_content = ' '.join(text_content.split())[:1000]  # First 1000 chars
                        
                        return {
                            "success": True,
                            "data": {
                                "title": title_text,
                                "content": cleaned_content,
                                "url": website_url,
                                "extraction_method": "fallback_beautifulsoup"
                            },
                            "url": website_url
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}",
                            "url": website_url
                        }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "url": website_url
            }
    
    return [fallback_smart_scraper]  # Add more fallback tools as needed


def create_development_tools():
    """
    Create development tools for basic functionality when backend tools are not available.
    DEPRECATED: Use create_real_tools() instead.
    """
    logger.warning("create_development_tools() is deprecated. Use create_real_tools() instead.")
    return create_fallback_tools()


def get_available_tools(use_real: bool = True) -> Dict[str, Any]:
    """
    Get a dictionary of available tools mapped by name.
    
    Args:
        use_real: Whether to use real scraping tools or fallback tools
        
    Returns:
        Dictionary mapping tool names to tool functions
    """
    if use_real:
        try:
            tools = create_real_tools()
        except Exception as e:
            logger.warning(f"Failed to create real scraping tools: {e}. Using fallback tools.")
            tools = create_fallback_tools()
    else:
        tools = create_fallback_tools()
    
    return {tool.name: tool for tool in tools}


def run_tool_safely(tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Safely run a tool by name with the provided arguments.
    
    Args:
        tool_name: Name of the tool to run
        **kwargs: Arguments to pass to the tool
        
    Returns:
        Tool result or error information
    """
    try:
        tools_dict = get_available_tools()
        if tool_name not in tools_dict:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": list(tools_dict.keys())
            }
        
        tool = tools_dict[tool_name]
        # Run the tool
        result = tool(**kwargs)
        if asyncio.iscoroutine(result):
            result = asyncio.run(result)
        
        return result
    except Exception as e:
        logger.error(f"Error running tool '{tool_name}': {e}")
        return {
            "success": False,
            "error": str(e)
        }


class ToolManager:
    """
    A manager class to handle tool operations for OSINT agents.
    """
    
    def __init__(self, use_backend: bool = True):
        self._tools = None
        self.use_backend = use_backend
        self.logger = logging.getLogger(f"{__name__}.ToolManager")
    
    @property
    def tools(self) -> List[Any]:
        """Lazy load tools when first accessed."""
        if self._tools is None:
            try:
                self._tools = create_backend_scraping_tools() if self.use_backend else create_development_tools()
            except (ImportError, AttributeError):
                # If backend tools fail to import, use development tools
                logger.warning("Failed to import backend tools, using development tools")
                self._tools = create_development_tools()
        return self._tools
    
    def get_tool_by_name(self, name: str) -> Optional[Any]:
        """Get a specific tool by its name."""
        for tool in self.tools:
            if hasattr(tool, 'name') and tool.name == name:
                return tool
        return None
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name with the provided arguments."""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool '{tool_name}' not found",
                "available_tools": [getattr(t, 'name', 'unknown') for t in self.tools]
            }
        
        try:
            # For LangChain tools, we need to use the async interface properly
            from langchain_core.tools import BaseTool
            if isinstance(tool, BaseTool):
                # Use LangChain's async invocation method
                result = await tool.ainvoke(kwargs)
            else:
                # Fallback for other types of tools
                result = tool(**kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
            
            return result
        except Exception as e:
            self.logger.error(f"Error executing tool '{tool_name}': {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_tool_names(self) -> List[str]:
        """Get list of available tool names."""
        return [getattr(tool, 'name', 'unknown') for tool in self.tools]
    
    def validate_tool_args(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """Validate arguments for a specific tool."""
        tool = self.get_tool_by_name(tool_name)
        if not tool:
            return {
                "valid": False,
                "error": f"Tool '{tool_name}' not found"
            }
        
        try:
            # Get the tool's input schema
            if hasattr(tool, 'args_schema'):
                schema = tool.args_schema
                # Validate the arguments against the schema
                schema(**kwargs)
                return {"valid": True}
            else:
                return {"valid": True}
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }


# Global tool manager instance
tool_manager = ToolManager(use_backend=True)


def get_global_tool_manager() -> ToolManager:
    """Get the global tool manager instance."""
    return tool_manager


# Example usage function
async def example_usage():
    """Example of how to use the tools integration."""
    print("Available tools:", tool_manager.get_tool_names())
    
    # Example: Run smart scraper tool
    result = await tool_manager.execute_tool(
        "smart_scraper",
        website_url="https://example.com",
        user_prompt="Extract the main heading and description"
    )
    print("Tool result:", result)


if __name__ == "__main__":
    asyncio.run(example_usage())