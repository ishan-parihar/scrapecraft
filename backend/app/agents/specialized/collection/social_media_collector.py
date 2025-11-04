"""
Social Media Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, timedelta

from ..base.osint_agent import LLMOSINTAgent, AgentConfig

import importlib.util
import os

# Dynamically import the tool manager classes to avoid import issues
tool_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils', 'tools', 'langchain_tools.py')
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
        Collect profile information from a social media platform.
        
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
            # Simulate profile data collection
            profile_data = await self._simulate_profile_lookup(username, platform)
            
            if include_posts:
                posts = await self._collect_recent_posts(username, platform, post_limit)
                profile_data["recent_posts"] = posts
            
            collection_data = {
                "source": f"social_media_{platform}",
                "username": username,
                "platform": platform,
                "timestamp": time.time(),
                "profile": profile_data,
                "collection_success": True
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
        Search for posts containing specific keywords.
        
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
            posts = await self._simulate_keyword_search(keyword, platform, max_results, date_range)
            
            collection_data = {
                "source": f"social_media_search_{platform}",
                "keyword": keyword,
                "platform": platform,
                "timestamp": time.time(),
                "posts": posts,
                "total_results": len(posts),
                "date_range": date_range,
                "collection_success": True
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
        Collect network analysis data (connections, followers, etc.).
        
        Args:
            username: Username to analyze
            platform: Social media platform
            depth: Depth of network analysis
            
        Returns:
            Dictionary containing network analysis data
        """
        self.logger.info(f"Collecting network analysis for {username} on {platform}")
        
        try:
            network_data = await self._simulate_network_analysis(username, platform, depth)
            
            collection_data = {
                "source": f"social_media_network_{platform}",
                "username": username,
                "platform": platform,
                "timestamp": time.time(),
                "network": network_data,
                "analysis_depth": depth,
                "collection_success": True
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
        Monitor hashtag activity and trends.
        
        Args:
            hashtag: Hashtag to monitor
            platform: Social media platform
            timeframe: Timeframe for monitoring
            
        Returns:
            Dictionary containing hashtag analysis
        """
        self.logger.info(f"Monitoring hashtag #{hashtag} on {platform}")
        
        try:
            hashtag_data = await self._simulate_hashtag_monitoring(hashtag, platform, timeframe)
            
            collection_data = {
                "source": f"social_media_hashtag_{platform}",
                "hashtag": hashtag,
                "platform": platform,
                "timestamp": time.time(),
                "hashtag_analysis": hashtag_data,
                "timeframe": timeframe,
                "collection_success": True
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
        
        # Handle traditional simulation tasks
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
    
    async def _simulate_profile_lookup(self, username: str, platform: str) -> Dict[str, Any]:
        """Simulate profile lookup for demonstration."""
        base_data = {
            "username": username,
            "display_name": f"{username.title()} User",
            "bio": f"This is the bio for {username} on {platform}",
            "profile_image": f"https://example.com/avatars/{username}.jpg",
            "verified": False,
            "private": False,
            "created_at": "2020-01-15T10:30:00Z",
            "last_active": "2024-01-20T15:45:00Z"
        }
        
        platform_specific = {}
        
        if platform == "twitter":
            platform_specific = {
                "followers_count": 1250,
                "following_count": 450,
                "tweets_count": 3200,
                "likes_count": 8900,
                "location": "San Francisco, CA",
                "website": "https://example.com",
                "protected": False
            }
        elif platform == "instagram":
            platform_specific = {
                "followers_count": 2500,
                "following_count": 180,
                "posts_count": 156,
                "igtv_count": 12,
                "reels_count": 34,
                "business_account": False,
                "external_url": "https://example.com"
            }
        elif platform == "linkedin":
            platform_specific = {
                "connections_count": 750,
                "followers_count": 1200,
                "headline": "Software Engineer at Tech Company",
                "company": "Tech Company",
                "position": "Senior Software Engineer",
                "experience_years": 8,
                "education": "BS Computer Science, University Name"
            }
        elif platform == "facebook":
            platform_specific = {
                "friends_count": 350,
                "followers_count": 180,
                "groups_count": 12,
                "pages_count": 5,
                "relationship_status": "Single",
                "workplace": "Tech Company",
                "education": "University Name"
            }
        elif platform == "reddit":
            platform_specific = {
                "karma": 15420,
                "cake_day": "2020-01-15",
                "trophies": ["Helpful", "Verified Email", "Gold"],
                "moderated_subreddits": ["r/example"],
                "post_karma": 12000,
                "comment_karma": 3420
            }
        
        return {**base_data, **platform_specific}
    
    async def _collect_recent_posts(
        self, 
        username: str, 
        platform: str, 
        limit: int
    ) -> List[Dict[str, Any]]:
        """Simulate collecting recent posts."""
        posts = []
        for i in range(min(limit, 10)):
            post = {
                "post_id": f"{platform}_{username}_{i+1}",
                "content": f"This is sample post {i+1} from {username} on {platform}",
                "timestamp": self._generate_timestamp(i),
                "likes": 10 + i * 5,
                "shares": 2 + i,
                "comments": 3 + i * 2,
                "hashtags": ["#example", f"#post{i+1}"],
                "mentions": [f"@user{j}" for j in range(1, min(i+2, 4))]
            }
            
            # Platform-specific post data
            if platform == "twitter":
                post["retweets"] = 5 + i * 3
                post["quoted_tweets"] = 1 + i
            elif platform == "instagram":
                post["image_url"] = f"https://example.com/posts/{username}_{i+1}.jpg"
                post["carousel"] = i % 3 == 0
            elif platform == "youtube":
                post["video_url"] = f"https://youtube.com/watch?v=example{i+1}"
                post["views"] = 1000 + i * 200
                post["duration"] = f"{3 + i}:{30 + i * 10:02d}"
            
            posts.append(post)
        
        return posts
    
    async def _simulate_keyword_search(
        self, 
        keyword: str, 
        platform: str, 
        max_results: int,
        date_range: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Simulate keyword search in posts."""
        results = []
        for i in range(min(max_results, 15)):
            result = {
                "post_id": f"{platform}_search_{i+1}",
                "author": f"user{i+1}",
                "content": f"Here's a post about {keyword} - sample content {i+1}",
                "timestamp": self._generate_timestamp(i),
                "likes": 20 + i * 8,
                "shares": 4 + i * 2,
                "relevance_score": 0.9 - (i * 0.05),
                "source_url": f"https://{platform}.com/post/{i+1}"
            }
            results.append(result)
        
        return results
    
    async def _simulate_network_analysis(
        self, 
        username: str, 
        platform: str, 
        depth: int
    ) -> Dict[str, Any]:
        """Simulate network analysis."""
        connections = []
        for i in range(min(20, depth * 10)):
            connection = {
                "username": f"connection_{i+1}",
                "connection_type": "follower" if i % 2 == 0 else "following",
                "mutual_connections": 5 + i,
                "interaction_frequency": "high" if i < 5 else "medium" if i < 15 else "low",
                "verified": i < 3,
                "influence_score": 0.8 - (i * 0.03)
            }
            connections.append(connection)
        
        return {
            "total_connections": len(connections),
            "followers": len([c for c in connections if c["connection_type"] == "follower"]),
            "following": len([c for c in connections if c["connection_type"] == "following"]),
            "verified_connections": len([c for c in connections if c["verified"]]),
            "average_mutual_connections": sum(c["mutual_connections"] for c in connections) / len(connections),
            "connections": connections,
            "network_metrics": {
                "clustering_coefficient": 0.35,
                "betweenness_centrality": 0.12,
                "eigenvector_centrality": 0.45,
                "network_density": 0.28
            }
        }
    
    async def _simulate_hashtag_monitoring(
        self, 
        hashtag: str, 
        platform: str, 
        timeframe: str
    ) -> Dict[str, Any]:
        """Simulate hashtag monitoring."""
        posts = []
        for i in range(30):  # Sample 30 posts
            post = {
                "post_id": f"{platform}_hashtag_{i+1}",
                "author": f"user_{i+1}",
                "content": f"Using #{hashtag} in this post #{i+1}",
                "timestamp": self._generate_timestamp(i),
                "likes": 15 + i * 7,
                "shares": 3 + i,
                "reach": 100 + i * 50
            }
            posts.append(post)
        
        return {
            "total_posts": len(posts),
            "unique_authors": len(set(p["author"] for p in posts)),
            "total_engagement": sum(p["likes"] + p["shares"] for p in posts),
            "total_reach": sum(p["reach"] for p in posts),
            "top_contributors": [
                {"username": "user1", "post_count": 3, "total_engagement": 450},
                {"username": "user5", "post_count": 2, "total_engagement": 380}
            ],
            "trending_score": 0.75,
            "sentiment_analysis": {
                "positive": 0.45,
                "neutral": 0.40,
                "negative": 0.15
            },
            "posts": posts[:10]  # Return top 10 posts
        }
    
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