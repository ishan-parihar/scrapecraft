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


def create_mock_tools():
    """
    Create mock tools for development when backend tools are not available.
    
    Returns:
        List of mock tools that simulate the actual tools
    """
    from langchain_core.tools import tool
    from pydantic import BaseModel, Field
    
    class MockScraperInput(BaseModel):
        website_url: str = Field(description="The URL of the website to scrape")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")

    class MockCrawlerInput(BaseModel):
        website_url: str = Field(description="The starting URL for crawling")
        user_prompt: str = Field(description="Natural language prompt describing what data to extract")
        max_depth: int = Field(default=2, description="Maximum crawl depth")
        max_pages: int = Field(default=5, description="Maximum number of pages to crawl")

    class MockSearchInput(BaseModel):
        search_query: str = Field(description="The search query to find relevant websites")
        max_results: int = Field(default=10, description="Maximum number of results to return")

    class MockMarkdownifyInput(BaseModel):
        website_url: str = Field(description="The URL of the website to convert to markdown")

    @tool("smart_scraper", args_schema=MockScraperInput)
    async def mock_smart_scraper(website_url: str, user_prompt: str) -> Dict[str, Any]:
        """Mock implementation of smart scraper tool."""
        return {
            "success": True,
            "data": f"Mock scraped data from {website_url} based on prompt: {user_prompt}",
            "url": website_url
        }

    @tool("smart_crawler", args_schema=MockCrawlerInput)
    async def mock_smart_crawler(
        website_url: str,
        user_prompt: str,
        max_depth: int = 2,
        max_pages: int = 5
    ) -> Dict[str, Any]:
        """Mock implementation of smart crawler tool."""
        return {
            "success": True,
            "data": f"Mock crawled data from {website_url}",
            "pages_crawled": min(max_pages, 2),  # Mock result
            "starting_url": website_url
        }

    @tool("search_scraper", args_schema=MockSearchInput)
    async def mock_search_scraper(search_query: str, max_results: int = 10) -> Dict[str, Any]:
        """Mock implementation of search scraper tool."""
        results = []
        for i in range(min(max_results, 5)):
            results.append({
                "url": f"https://mocksite{i+1}.com",
                "title": f"Mock result for {search_query} - {i+1}",
                "description": f"This is a mock description for query: {search_query}"
            })
        
        return {
            "success": True,
            "query": search_query,
            "results": results,
            "count": len(results)
        }

    @tool("markdownify", args_schema=MockMarkdownifyInput)
    async def mock_markdownify(website_url: str) -> Dict[str, Any]:
        """Mock implementation of markdownify tool."""
        return {
            "success": True,
            "markdown": f"# Mock Markdown Content\n\nThis is mocked markdown content from {website_url}",
            "url": website_url
        }

    @tool("validate_urls")
    async def mock_validate_urls(urls: List[str]) -> Dict[str, Any]:
        """Mock implementation of URL validation tool."""
        results = []
        for url in urls:
            results.append({
                "url": url,
                "valid": True,  # Mock all as valid
                "status_code": 200,
                "final_url": url
            })
        
        return {
            "urls_checked": len(urls),
            "valid_urls": len(urls),
            "results": results
        }

    logger.info("Created mock tools for development")
    return [
        mock_smart_scraper,
        mock_smart_crawler,
        mock_search_scraper,
        mock_markdownify,
        mock_validate_urls
    ]


def get_available_tools(use_backend: bool = True) -> Dict[str, Any]:
    """
    Get a dictionary of available tools mapped by name.
    
    Args:
        use_backend: Whether to use backend scraping tools or mock tools
        
    Returns:
        Dictionary mapping tool names to tool functions
    """
    if use_backend:
        try:
            tools = create_backend_scraping_tools()
        except Exception as e:
            logger.warning(f"Failed to create backend scraping tools: {e}. Falling back to mock tools.")
            tools = create_mock_tools()
    else:
        tools = create_mock_tools()
    
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
                self._tools = create_backend_scraping_tools() if self.use_backend else create_mock_tools()
            except (ImportError, AttributeError):
                # If backend tools fail to import, use mock tools
                logger.warning("Failed to import backend tools, using mock tools")
                self._tools = create_mock_tools()
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