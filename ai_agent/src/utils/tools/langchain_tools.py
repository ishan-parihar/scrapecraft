"""
LangChain Tools Integration Module for OSINT Collection Agents

This module provides utilities for integrating LangChain tools with OSINT collection agents.
It allows agents to access and use various scraping and data collection tools.
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

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


def get_available_tools() -> Dict[str, Any]:
    """
    Get a dictionary of available tools mapped by name.
    
    Returns:
        Dictionary mapping tool names to tool functions
    """
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
    
    def __init__(self):
        self._tools = None
        self.logger = logging.getLogger(f"{__name__}.ToolManager")
    
    @property
    def tools(self) -> List[Any]:
        """Lazy load tools when first accessed."""
        if self._tools is None:
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
            result = tool(**kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            
            return result
        except Exception as e:
            self.logger.error(f"Error executing tool '{tool_name}': {e}")
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
tool_manager = ToolManager()


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