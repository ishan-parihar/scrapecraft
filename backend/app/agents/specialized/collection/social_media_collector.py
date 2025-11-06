"""
Social Media Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from ...base.osint_agent import LLMOSINTAgent, AgentConfig

import importlib.util
import os

# Dynamically import the tool manager classes to avoid import issues
tool_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'agents', 'tools', 'langchain_tools.py')
tool_spec = importlib.util.spec_from_file_location("langchain_tools", tool_module_path)
if tool_spec is not None and tool_spec.loader is not None:
    tool_module = importlib.util.module_from_spec(tool_spec)
    tool_spec.loader.exec_module(tool_module)
    ToolManager = tool_module.ToolManager
    get_global_tool_manager = tool_module.get_global_tool_manager
else:
    raise ImportError("Could not load langchain tools module")

# Note: This agent now uses LangChain tools approach through the tool manager
# Direct adapter initialization is no longer needed


class SocialMediaCollectorAgent(LLMOSINTAgent):
    """
    Agent responsible for collecting information from social media platforms.
    Handles profiles, posts, connections, and public social media data.
    """
    
    def __init__(self, agent_id: str = "social_media_collector", tools: Optional[List[Any]] = None):
        config = AgentConfig(
            agent_id=agent_id,
            role="Social Media Collector",
            description="Collects information from social media platforms including profiles, posts, and connections"
        )
        # Initialize with tools
        super().__init__(config=config, tools=tools)
        self.tool_manager = ToolManager() if not tools else get_global_tool_manager()
        self.supported_platforms = [
            "twitter", "facebook", "instagram", "linkedin", 
            "tiktok", "reddit", "youtube", "telegram"
        ]
        self.request_delay = 2.0  # Longer delay for social media platforms
    
    async def use_web_scraper(self, website_url: str, user_prompt: str) -> Dict[str, Any]:
        """
        Use the web scraper tool to extract data from a social media website.
        
        Args:
            website_url: The URL of the social media website to scrape
            user_prompt: Natural language prompt describing what data to extract
            
        Returns:
            Dictionary containing the scraped data
        """
        self.logger.info(f"Using web scraper on {website_url} with prompt: {user_prompt}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "smart_scraper",
                website_url=website_url,
                user_prompt=user_prompt
            )
            self.logger.info(f"Web scraper result: {result.get('success', 'Unknown')}")
            return result
        except Exception as e:
            self.logger.error(f"Error using web scraper: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def use_web_crawler(self, website_url: str, user_prompt: str, max_depth: int = 2, max_pages: int = 5) -> Dict[str, Any]:
        """
        Use the web crawler tool to crawl and extract data from social media sites.
        
        Args:
            website_url: The starting URL for crawling
            user_prompt: Natural language prompt describing what data to extract
            max_depth: Maximum crawl depth (default: 2)
            max_pages: Maximum number of pages to crawl (default: 5)
            
        Returns:
            Dictionary containing the crawled data
        """
        self.logger.info(f"Using web crawler starting at {website_url}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "smart_crawler",
                website_url=website_url,
                user_prompt=user_prompt,
                max_depth=max_depth,
                max_pages=max_pages
            )
            self.logger.info(f"Web crawler result: {result.get('success', 'Unknown')}")
            return result
        except Exception as e:
            self.logger.error(f"Error using web crawler: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def use_search_tool(self, search_query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Use the search tool to find social media profiles and content.
        
        Args:
            search_query: The search query to find social media content
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            Dictionary containing search results
        """
        self.logger.info(f"Performing social media search for: {search_query}")
        
        try:
            result = await self.tool_manager.execute_tool(
                "search_scraper",
                search_query=search_query,
                max_results=max_results
            )
            self.logger.info(f"Search result count: {result.get('count', 0)}")
            return result
        except Exception as e:
            self.logger.error(f"Error using search tool: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
    
    async def use_markdown_converter(self, website_url: str) -> Dict[str, Any]:
        """
        Convert a social media website to markdown format for easier processing.
        
        Args:
            website_url: The URL of the social media website to convert to markdown
            
        Returns:
            Dictionary containing the markdown content
        """
        self.logger.info(f"Converting {website_url} to markdown")
        
        try:
            result = await self.tool_manager.execute_tool(
                "markdownify",
                website_url=website_url
            )
            self.logger.info(f"Markdown conversion result: {result.get('success', 'Unknown')}")
            return result
        except Exception as e:
            self.logger.error(f"Error converting to markdown: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "data": None
            }
        
    async def collect_profile_info(
        self, 
        username: str, 
        platform: str,
        include_posts: bool = False,
        post_limit: int = 20
    ) -> Dict[str, Any]:
        """
        Collect profile information from a social media platform using real data.
        
        Args:
            username: Username to search for
            platform: Social media platform
            include_posts: Whether to include recent posts
            post_limit: Maximum number of posts to collect
            
        Returns:
            Dictionary containing profile information
        """
        self.logger.info(f"Collecting profile info for {username} on {platform}")
        
        try:
            # Use real social media service for profile lookup
            from ....services.real_social_media_service import perform_social_media_search
            
            profile_result = await perform_social_media_search(
                platform=platform,
                search_type="profile",
                username=username
            )
            
            if "error" in profile_result:
                # Fall back to web scraping if API fails
                profile_data = await self._scrape_profile_fallback(username, platform)
            else:
                profile_data = profile_result
            
            if include_posts:
                posts_result = await perform_social_media_search(
                    platform=platform,
                    search_type="posts",
                    query=username,
                    max_results=post_limit
                )
                if "error" not in posts_result:
                    profile_data["recent_posts"] = posts_result.get("posts", [])
            
            collection_data = {
                "source": f"social_media_{platform}",
                "username": username,
                "platform": platform,
                "timestamp": time.time(),
                "profile": profile_data,
                "collection_success": "error" not in profile_data,
                "data_source": "real_api"
            }
            
            self.logger.info(f"Profile collected for {username} on {platform}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error collecting profile for {username} on {platform}: {str(e)}")
            return {
                "error": str(e),
                "source": f"social_media_{platform}",
                "username": username,
                "platform": platform,
                "collection_success": False
            }
    
    async def search_posts_by_keyword(
        self, 
        keyword: str, 
        platform: str,
        max_results: int = 50,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Search for posts containing specific keywords using real data.
        
        Args:
            keyword: Keyword to search for
            platform: Social media platform
            max_results: Maximum number of results
            date_range: Optional date range filter
            
        Returns:
            Dictionary containing search results
        """
        self.logger.info(f"Searching posts for '{keyword}' on {platform}")
        
        try:
            # Use real social media service for post search
            from ....services.real_social_media_service import perform_social_media_search
            
            posts_result = await perform_social_media_search(
                platform=platform,
                search_type="posts",
                query=keyword,
                max_results=max_results
            )
            
            if "error" not in posts_result:
                posts = posts_result.get("posts", [])
                # Apply date range filter if specified
                if date_range:
                    posts = self._filter_posts_by_date(posts, date_range)
            else:
                posts = []
            
            collection_data = {
                "source": f"social_media_search_{platform}",
                "keyword": keyword,
                "platform": platform,
                "timestamp": time.time(),
                "posts": posts,
                "total_results": len(posts),
                "date_range": date_range,
                "collection_success": True,
                "data_source": "real_api"
            }
            
            self.logger.info(f"Found {len(posts)} posts for '{keyword}' on {platform}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error searching posts for '{keyword}' on {platform}: {str(e)}")
            return {
                "error": str(e),
                "source": f"social_media_search_{platform}",
                "keyword": keyword,
                "platform": platform,
                "collection_success": False
            }
    
    async def collect_network_analysis(
        self, 
        username: str, 
        platform: str,
        depth: int = 2
    ) -> Dict[str, Any]:
        """
        Collect network analysis data using real profile information.
        
        Args:
            username: Username to analyze
            platform: Social media platform
            depth: Depth of network analysis
            
        Returns:
            Dictionary containing network analysis data
        """
        self.logger.info(f"Collecting network analysis for {username} on {platform}")
        
        try:
            # Use real social media service for network analysis
            from ....services.real_social_media_service import perform_social_media_search
            
            network_result = await perform_social_media_search(
                platform=platform,
                search_type="network",
                username=username
            )
            
            if "error" not in network_result:
                network_data = network_result
            else:
                # Fallback basic network analysis
                network_data = await self._basic_network_analysis(username, platform, depth)
            
            collection_data = {
                "source": f"social_media_network_{platform}",
                "username": username,
                "platform": platform,
                "timestamp": time.time(),
                "network": network_data,
                "analysis_depth": depth,
                "collection_success": "error" not in network_data,
                "data_source": "real_api"
            }
            
            self.logger.info(f"Network analysis completed for {username} on {platform}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in network analysis for {username} on {platform}: {str(e)}")
            return {
                "error": str(e),
                "source": f"social_media_network_{platform}",
                "username": username,
                "platform": platform,
                "collection_success": False
            }
    
    async def monitor_hashtag(
        self, 
        hashtag: str, 
        platform: str,
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Monitor hashtag activity using real post search.
        
        Args:
            hashtag: Hashtag to monitor
            platform: Social media platform
            timeframe: Timeframe for monitoring
            
        Returns:
            Dictionary containing hashtag analysis
        """
        self.logger.info(f"Monitoring hashtag #{hashtag} on {platform}")
        
        try:
            # Use real social media service to search for hashtag posts
            from ....services.real_social_media_service import perform_social_media_search
            
            hashtag_query = f"#{hashtag}"
            posts_result = await perform_social_media_search(
                platform=platform,
                search_type="posts",
                query=hashtag_query,
                max_results=50
            )
            
            if "error" not in posts_result:
                posts = posts_result.get("posts", [])
                hashtag_data = self._analyze_hashtag_data(posts, hashtag, timeframe)
            else:
                hashtag_data = {"error": "Failed to retrieve hashtag posts", "posts": []}
            
            collection_data = {
                "source": f"social_media_hashtag_{platform}",
                "hashtag": hashtag,
                "platform": platform,
                "timestamp": time.time(),
                "hashtag_analysis": hashtag_data,
                "timeframe": timeframe,
                "collection_success": "error" not in hashtag_data,
                "data_source": "real_api"
            }
            
            self.logger.info(f"Hashtag analysis completed for #{hashtag} on {platform}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error monitoring hashtag #{hashtag} on {platform}: {str(e)}")
            return {
                "error": str(e),
                "source": f"social_media_hashtag_{platform}",
                "hashtag": hashtag,
                "platform": platform,
                "collection_success": False
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a social media collection task.
        
        Args:
            task: Task dictionary containing collection parameters
            
        Returns:
            Dictionary containing collection results
        """
        task_type = task.get("task_type", "profile")
        
        # Handle LangChain tool-based tasks
        if task_type == "langchain_tool":
            return await self._execute_langchain_tool_task(task)
        
        # Handle traditional collection tasks
        results = []
        
        if task_type == "profile":
            # Profile collection
            profiles = task.get("profiles", [])
            include_posts = task.get("include_posts", False)
            post_limit = task.get("post_limit", 20)
            
            for profile in profiles:
                username = profile.get("username")
                platform = profile.get("platform")
                if username and platform:
                    result = await self.collect_profile_info(
                        username, platform, include_posts, post_limit
                    )
                    results.append(result)
                    await asyncio.sleep(self.request_delay)
        
        elif task_type == "search":
            # Keyword search
            searches = task.get("searches", [])
            max_results = task.get("max_results", 50)
            date_range = task.get("date_range")
            
            for search in searches:
                keyword = search.get("keyword")
                platform = search.get("platform")
                if keyword and platform:
                    result = await self.search_posts_by_keyword(
                        keyword, platform, max_results, date_range
                    )
                    results.append(result)
                    await asyncio.sleep(self.request_delay)
        
        elif task_type == "network":
            # Network analysis
            networks = task.get("networks", [])
            depth = task.get("depth", 2)
            
            for network in networks:
                username = network.get("username")
                platform = network.get("platform")
                if username and platform:
                    result = await self.collect_network_analysis(username, platform, depth)
                    results.append(result)
                    await asyncio.sleep(self.request_delay)
        
        elif task_type == "hashtag":
            # Hashtag monitoring
            hashtags = task.get("hashtags", [])
            timeframe = task.get("timeframe", "24h")
            
            for hashtag in hashtags:
                tag = hashtag.get("tag")
                platform = hashtag.get("platform")
                if tag and platform:
                    result = await self.monitor_hashtag(tag, platform, timeframe)
                    results.append(result)
                    await asyncio.sleep(self.request_delay)
        
        return {
            "agent_id": self.config.agent_id,
            "task_type": task_type,
            "timestamp": time.time(),
            "results": results,
            "total_collections": len(results),
            "status": "completed"
        }
    
    async def _execute_langchain_tool_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a LangChain tool-based task.

        Args:
            task: Task dictionary containing tool execution parameters

        Returns:
            Dictionary containing tool execution results
        """
        tool_name = task.get("tool_name")
        tool_args = task.get("tool_args", {})
        
        if not tool_name:
            return {
                "success": False,
                "error": "Tool name not specified in task",
                "agent_id": self.config.agent_id,
                "timestamp": time.time(),
                "status": "failed"
            }
        
        self.logger.info(f"Executing LangChain tool: {tool_name} with args: {tool_args}")
        
        try:
            result = await self.tool_manager.execute_tool(tool_name, **tool_args)
            return {
                "success": result.get("success", False),
                "tool_name": tool_name,
                "tool_args": tool_args,
                "result": result,
                "agent_id": self.config.agent_id,
                "timestamp": time.time(),
                "status": "completed"
            }
        except Exception as e:
            self.logger.error(f"Error executing LangChain tool {tool_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name,
                "tool_args": tool_args,
                "agent_id": self.config.agent_id,
                "timestamp": time.time(),
                "status": "failed"
            }

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Social Media Collector Agent.
        """
        return """
        You are a Social Media Collector Agent, specialized in gathering information from social media platforms 
        including profiles, posts, connections, and public social media data. Your role is to collect relevant 
        information based on the user's request while maintaining ethical standards and respecting platform terms 
        of service.
        
        You should:
        1. Collect profile information from various social media platforms
        2. Extract meaningful content from posts and comments
        3. Identify and analyze network connections
        4. Monitor hashtags and trending topics
        5. Structure the collected information in a clear, organized format
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process and structure the raw output from the agent.
        """
        # For the collection agent, we return the raw collected data
        return {
            "collection_results": raw_output,
            "processed_at": time.time(),
            "agent_type": "SocialMediaCollector"
        }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        """
        # Check if the input contains necessary information
        if not input_data:
            return False
        
        # For collection tasks, ensure we have a task type
        task_type = input_data.get("task_type")
        if not task_type or task_type not in ["profile", "search", "network", "hashtag"]:
            return False
        
        return True
    
    async def _scrape_profile_fallback(self, username: str, platform: str) -> Dict[str, Any]:
        """Fallback profile scraping using web scraping tools."""
        try:
            if platform == "twitter":
                url = f"https://twitter.com/{username}"
            elif platform == "instagram":
                url = f"https://instagram.com/{username}"
            elif platform == "reddit":
                url = f"https://reddit.com/user/{username}"
            else:
                return {"error": f"Platform {platform} not supported for fallback scraping"}
            
            # Use web scraper tool to extract profile data
            result = await self.tool_manager.execute_tool(
                "smart_scraper",
                website_url=url,
                user_prompt=f"Extract profile information for {username} including name, bio, follower counts, and any other public data"
            )
            
            if result.get("success"):
                return {
                    "username": username,
                    "platform": platform,
                    "scraped_data": result.get("data", {}),
                    "data_source": "web_scraping_fallback"
                }
            else:
                return {"error": "Web scraping failed", "username": username, "platform": platform}
                
        except Exception as e:
            return {"error": f"Fallback scraping failed: {str(e)}", "username": username, "platform": platform}
    
    def _filter_posts_by_date(self, posts: List[Dict[str, Any]], date_range: Dict[str, str]) -> List[Dict[str, Any]]:
        """Filter posts by date range."""
        try:
            from datetime import datetime
            
            start_date = date_range.get("start")
            end_date = date_range.get("end")
            
            filtered_posts = []
            for post in posts:
                post_timestamp = post.get("timestamp") or post.get("scraped_at")
                if not post_timestamp:
                    continue
                    
                try:
                    if isinstance(post_timestamp, str):
                        post_date = datetime.fromisoformat(post_timestamp.replace('Z', '+00:00'))
                    else:
                        continue
                    
                    # Apply date filters
                    if start_date:
                        start_dt = datetime.fromisoformat(start_date)
                        if post_date < start_dt:
                            continue
                    
                    if end_date:
                        end_dt = datetime.fromisoformat(end_date)
                        if post_date > end_dt:
                            continue
                    
                    filtered_posts.append(post)
                    
                except ValueError:
                    continue
            
            return filtered_posts
            
        except Exception as e:
            self.logger.error(f"Date filtering failed: {e}")
            return posts
    
    async def _basic_network_analysis(self, username: str, platform: str, depth: int) -> Dict[str, Any]:
        """Basic network analysis based on available profile data."""
        try:
            # Get profile data first
            profile_result = await self._scrape_profile_fallback(username, platform)
            
            if "error" not in profile_result:
                scraped_data = profile_result.get("scraped_data", {})
                
                # Extract network metrics from scraped data
                followers_count = scraped_data.get("followers_count", 0)
                following_count = scraped_data.get("following_count", 0)
                
                network_data = {
                    "username": username,
                    "platform": platform,
                    "followers_count": followers_count,
                    "following_count": following_count,
                    "follower_following_ratio": followers_count / max(following_count, 1),
                    "influence_score": min(followers_count / 1000, 100),
                    "analysis_method": "profile_data_extraction",
                    "data_source": "fallback_analysis"
                }
            else:
                network_data = {"error": "Profile data unavailable for network analysis"}
            
            return network_data
            
        except Exception as e:
            return {"error": f"Network analysis failed: {str(e)}"}
    
    def _analyze_hashtag_data(self, posts: List[Dict[str, Any]], hashtag: str, timeframe: str) -> Dict[str, Any]:
        """Analyze hashtag data from collected posts."""
        try:
            if not posts:
                return {"error": "No posts found for hashtag analysis", "total_posts": 0}
            
            # Basic metrics
            total_posts = len(posts)
            unique_authors = len(set(post.get("author", "") for post in posts))
            total_likes = sum(post.get("likes", 0) for post in posts)
            total_shares = sum(post.get("shares", 0) for post in posts)
            total_engagement = total_likes + total_shares
            
            # Top contributors
            author_posts = {}
            for post in posts:
                author = post.get("author", "Unknown")
                if author not in author_posts:
                    author_posts[author] = {"count": 0, "engagement": 0}
                author_posts[author]["count"] += 1
                author_posts[author]["engagement"] += post.get("likes", 0) + post.get("shares", 0)
            
            top_contributors = [
                {"username": author, "post_count": data["count"], "total_engagement": data["engagement"]}
                for author, data in sorted(author_posts.items(), key=lambda x: x[1]["engagement"], reverse=True)[:5]
            ]
            
            # Engagement rate calculation
            avg_engagement = total_engagement / total_posts if total_posts > 0 else 0
            
            hashtag_data = {
                "total_posts": total_posts,
                "unique_authors": unique_authors,
                "total_engagement": total_engagement,
                "average_engagement_per_post": avg_engagement,
                "top_contributors": top_contributors,
                "trending_score": min(total_engagement / 1000, 100),
                "posts_sample": posts[:10],  # Return first 10 posts as sample
                "analysis_method": "post_data_analysis"
            }
            
            return hashtag_data
            
        except Exception as e:
            return {"error": f"Hashtag analysis failed: {str(e)}"}
    
    def _generate_timestamp(self, hours_ago: int) -> str:
        """Generate timestamp for hours ago."""
        timestamp = datetime.now() - timedelta(hours=hours_ago)
        return timestamp.isoformat() + "Z"
    
    async def _use_scraping_tools_for_social_media(self, url: str, user_prompt: str) -> Dict[str, Any]:
        """
        Use scraping tools to extract social media content when direct API access is not available.
        
        Args:
            url: Social media URL to scrape
            user_prompt: Natural language description of what to extract
            
        Returns:
            Dictionary containing scraping tool results
        """
        try:
            # Run the smart scraper tool for social media content
            result = await self.tool_manager.execute_tool(
                "smart_scraper",
                website_url=url,
                user_prompt=user_prompt
            )
            return result
        except Exception as e:
            self.logger.error(f"Error using scraping tools for social media {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "tool_used": "smart_scraper"
            }
    
    async def _use_search_for_social_media_profile(self, search_query: str) -> Dict[str, Any]:
        """
        Use search tools to find social media profiles.
        
        Args:
            search_query: Search query to find social media profiles
            
        Returns:
            Dictionary containing search results
        """
        try:
            # Run the search scraper tool
            result = await self.tool_manager.execute_tool(
                "search_scraper",
                search_query=search_query,
                max_results=10
            )
            return result
        except Exception as e:
            self.logger.error(f"Error using search tools for social media profiles '{search_query}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": search_query,
                "tool_used": "search_scraper"
            }

    async def collect_social_media_data(self, target: str) -> Dict[str, Any]:
        """
        Collect social media data for a target.
        
        Args:
            target: The target to collect social media data for
            
        Returns:
            Dictionary containing social media collection results
        """
        self.logger.info(f"Collecting social media data for target: {target}")
        
        try:
            # Use real social media service to find social media content
            from ....services.real_social_media_service import perform_social_media_search
            
            # Search for posts related to the target
            posts_result = await perform_social_media_search(
                platform="twitter",  # Default to Twitter
                search_type="posts",
                query=target,
                max_results=20
            )
            
            if "error" not in posts_result:
                posts = posts_result.get("posts", [])
            else:
                posts = []
            
            # Also use search scraper tool for additional social media content
            tool_results = await self.use_search_tool(target, 10)
            
            collection_data = {
                "source": "social_media_search",
                "target": target,
                "timestamp": time.time(),
                "posts": posts,
                "tool_results": tool_results,
                "total_results": len(posts) + tool_results.get("count", 0),
                "collection_success": True,
                "data_source": "real_api"
            }
            
            self.logger.info(f"Social media data collected for {target}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error collecting social media data for {target}: {str(e)}")
            return {
                "error": str(e),
                "source": "social_media_search",
                "target": target,
                "collection_success": False
            }

# Add alias for backward compatibility
SocialMediaCollector = SocialMediaCollectorAgent