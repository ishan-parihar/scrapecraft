"""
Dark Web Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import hashlib
from datetime import datetime, timedelta

from ..base.osint_agent import LLMOSINTAgent, AgentConfig

class DarkWebCollectorAgent(LLMOSINTAgent):
    """
    Agent responsible for collecting information from the dark web.
    Handles onion sites, hidden services, dark web forums, and marketplaces.
    
    WARNING: This agent is for educational and authorized security research purposes only.
    Unauthorized access to dark web content may be illegal.
    """
    
    def __init__(self, agent_id: str = "dark_web_collector", tools: Optional[List] = None):
        config = AgentConfig(
            agent_id=agent_id,
            role="Dark Web Collector",
            description="Collects information from dark web sources including onion services, forums, marketplaces, and leak sites"
        )
        # Dynamically import the tool manager classes to avoid import issues
        import importlib.util
        import os
        
        # Import the tool module dynamically
        tool_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils', 'tools', 'langchain_tools.py')
        spec = importlib.util.spec_from_file_location("langchain_tools", tool_module_path)
        if spec is not None and spec.loader is not None:
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            ToolManager = tool_module.ToolManager
            get_global_tool_manager = tool_module.get_global_tool_manager
        else:
            raise ImportError("Could not load langchain tools module")
        
        super().__init__(config=config, tools=tools)
        self.tool_manager = ToolManager() if not tools else get_global_tool_manager()
        
        # Initialize backend scraping adapter
        from ...utils.tools.scrapegraph_integration import BackendScrapingAdapter

        # Dynamically import the IntegrationConfig to avoid import issues
        config_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'integration_config.py')
        config_spec = importlib.util.spec_from_file_location("integration_config", config_module_path)
        if config_spec is not None and config_spec.loader is not None:
            config_module = importlib.util.module_from_spec(config_spec)
            config_spec.loader.exec_module(config_module)
            IntegrationConfig = config_module.IntegrationConfig
        else:
            raise ImportError("Could not load integration config module")
        
        integration_config = IntegrationConfig()
        self.scraping_adapter = BackendScrapingAdapter(base_url=integration_config.backend_scraping_base_url)
        
        self.supported_platforms = [
            "tor_network", "i2p_network", "freenet", "zero_net",
            "dark_web_forums", "marketplaces", "leak_sites", "whistleblower_sites"
        ]
        self.request_delay = 5.0  # Longer delay for dark web operations
        self.safety_level = "high"  # Always operate with high safety settings
    
    async def use_web_scraper(self, website_url: str, user_prompt: str) -> Dict[str, Any]:
        """
        Use the web scraper tool to extract data from a website.
        Note: For dark web operations, ensure proper authorization and safety measures.
        
        Args:
            website_url: The URL of the website to scrape
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
        Use the web crawler tool to crawl and extract data from a website.
        Note: For dark web operations, ensure proper authorization and safety measures.
        
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
        Use the search tool to find relevant websites for dark web research.
        Note: For dark web operations, ensure proper authorization and safety measures.
        
        Args:
            search_query: The search query to find relevant websites
            max_results: Maximum number of results to return (default: 10)
            
        Returns:
            Dictionary containing search results
        """
        self.logger.info(f"Performing dark web search for: {search_query}")
        
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
        Convert a website to markdown format for easier processing.
        Note: For dark web operations, ensure proper authorization and safety measures.
        
        Args:
            website_url: The URL of the website to convert to markdown
            
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
        
    async def scan_onion_services(
        self, 
        targets: List[str],
        scan_type: str = "passive",
        depth: int = 1
    ) -> Dict[str, Any]:
        """
        Scan onion services for information.
        
        Args:
            targets: List of onion service URLs or identifiers
            scan_type: Type of scan ("passive", "active", "deep")
            depth: Depth of scanning
            
        Returns:
            Dictionary containing scan results
        """
        self.logger.info(f"Scanning {len(targets)} onion services (type: {scan_type})")
        
        try:
            results = []
            
            for target in targets:
                result = await self._simulate_onion_service_scan(target, scan_type, depth)
                results.append(result)
                await asyncio.sleep(self.request_delay)
            
            collection_data = {
                "source": "dark_web_onion_services",
                "scan_type": scan_type,
                "targets_scanned": len(targets),
                "timestamp": time.time(),
                "results": results,
                "total_findings": sum(r["findings_count"] for r in results),
                "collection_success": True,
                "safety_level": self.safety_level
            }
            
            self.logger.info(f"Onion service scan completed, {collection_data['total_findings']} findings")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in onion service scan: {str(e)}")
            return {
                "error": str(e),
                "source": "dark_web_onion_services",
                "collection_success": False
            }
    
    async def monitor_dark_web_forums(
        self, 
        keywords: List[str],
        forums: List[str],
        timeframe: str = "7d"
    ) -> Dict[str, Any]:
        """
        Monitor dark web forums for specific keywords or topics.
        
        Args:
            keywords: Keywords to monitor for
            forums: List of forum identifiers or URLs
            timeframe: Timeframe for monitoring
            
        Returns:
            Dictionary containing monitoring results
        """
        self.logger.info(f"Monitoring {len(forums)} forums for {len(keywords)} keywords")
        
        try:
            results = []
            
            for forum in forums:
                forum_results = await self._simulate_forum_monitoring(forum, keywords, timeframe)
                results.append(forum_results)
                await asyncio.sleep(self.request_delay)
            
            collection_data = {
                "source": "dark_web_forums",
                "keywords": keywords,
                "forums_monitored": len(forums),
                "timeframe": timeframe,
                "timestamp": time.time(),
                "results": results,
                "total_mentions": sum(r["mentions_found"] for r in results),
                "collection_success": True,
                "safety_level": self.safety_level
            }
            
            self.logger.info(f"Forum monitoring completed, {collection_data['total_mentions']} mentions found")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in forum monitoring: {str(e)}")
            return {
                "error": str(e),
                "source": "dark_web_forums",
                "collection_success": False
            }
    
    async def scan_data_leaks(
        self, 
        search_terms: List[str],
        leak_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Scan for data leaks and breached information.
        
        Args:
            search_terms: Terms to search for in leaks
            leak_types: Types of leaks to search for
            
        Returns:
            Dictionary containing leak scan results
        """
        if leak_types is None:
            leak_types = ["credentials", "personal_data", "financial", "corporate"]
            
        self.logger.info(f"Scanning for data leaks related to {len(search_terms)} terms")
        
        try:
            results = []
            
            for term in search_terms:
                leak_results = await self._simulate_leak_scan(term, leak_types)
                results.append(leak_results)
                await asyncio.sleep(self.request_delay)
            
            collection_data = {
                "source": "dark_web_leaks",
                "search_terms": search_terms,
                "leak_types": leak_types,
                "timestamp": time.time(),
                "results": results,
                "total_leaks_found": sum(r["leaks_count"] for r in results),
                "collection_success": True,
                "safety_level": self.safety_level
            }
            
            self.logger.info(f"Leak scan completed, {collection_data['total_leaks_found']} leaks found")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in leak scan: {str(e)}")
            return {
                "error": str(e),
                "source": "dark_web_leaks",
                "collection_success": False
            }
    
    async def monitor_marketplace_activities(
        self, 
        marketplace: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Monitor dark web marketplace activities.
        
        Args:
            marketplace: Marketplace identifier
            categories: Categories to monitor
            
        Returns:
            Dictionary containing marketplace monitoring results
        """
        if categories is None:
            categories = ["data", "services", "software", "fraud"]
            
        self.logger.info(f"Monitoring marketplace: {marketplace}")
        
        try:
            activities = await self._simulate_marketplace_monitoring(marketplace, categories)
            
            collection_data = {
                "source": "dark_web_marketplaces",
                "marketplace": marketplace,
                "categories": categories,
                "timestamp": time.time(),
                "activities": activities,
                "total_listings": len(activities["listings"]),
                "total_vendors": len(activities["vendors"]),
                "collection_success": True,
                "safety_level": self.safety_level
            }
            
            self.logger.info(f"Marketplace monitoring completed, {collection_data['total_listings']} listings found")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in marketplace monitoring: {str(e)}")
            return {
                "error": str(e),
                "source": "dark_web_marketplaces",
                "collection_success": False
            }
    
    async def analyze_cybercrime_trends(
        self, 
        trend_types: Optional[List[str]] = None,
        timeframe: str = "30d"
    ) -> Dict[str, Any]:
        """
        Analyze cybercrime trends from dark web sources.
        
        Args:
            trend_types: Types of trends to analyze
            timeframe: Timeframe for trend analysis
            
        Returns:
            Dictionary containing trend analysis
        """
        if trend_types is None:
            trend_types = ["malware", "ransomware", "phishing", "data_breaches", "fraud"]
            
        self.logger.info(f"Analyzing cybercrime trends for {len(trend_types)} categories")
        
        try:
            trends = await self._simulate_trend_analysis(trend_types, timeframe)
            
            collection_data = {
                "source": "dark_web_trends",
                "trend_types": trend_types,
                "timeframe": timeframe,
                "timestamp": time.time(),
                "trends": trends,
                "total_trends": len(trends),
                "collection_success": True,
                "safety_level": self.safety_level
            }
            
            self.logger.info(f"Trend analysis completed for {len(trends)} categories")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error in trend analysis: {str(e)}")
            return {
                "error": str(e),
                "source": "dark_web_trends",
                "collection_success": False
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a dark web collection task.
        
        Args:
            task: Task dictionary containing collection parameters
            
        Returns:
            Dictionary containing collection results
        """
        # Check if this is a LangChain tool-based task
        if task.get("use_langchain", False):
            return await self._execute_langchain_task(task)
        
        task_type = task.get("task_type", "onion_scan")
        results = []
        
        # Safety check - ensure authorization for dark web activities
        if not task.get("authorized", False):
            return {
                "agent_id": self.config.agent_id,
                "error": "Dark web activities require explicit authorization",
                "status": "denied",
                "safety_level": self.safety_level
            }
        
        if task_type == "onion_scan":
            # Onion service scanning
            targets = task.get("targets", [])
            scan_type = task.get("scan_type", "passive")
            depth = task.get("depth", 1)
            
            if targets:
                result = await self.scan_onion_services(targets, scan_type, depth)
                results.append(result)
        
        elif task_type == "forum_monitor":
            # Forum monitoring
            keywords = task.get("keywords", [])
            forums = task.get("forums", [])
            timeframe = task.get("timeframe", "7d")
            
            if keywords and forums:
                result = await self.monitor_dark_web_forums(keywords, forums, timeframe)
                results.append(result)
        
        elif task_type == "leak_scan":
            # Data leak scanning
            search_terms = task.get("search_terms", [])
            leak_types = task.get("leak_types")
            
            if search_terms:
                result = await self.scan_data_leaks(search_terms, leak_types)
                results.append(result)
        
        elif task_type == "marketplace_monitor":
            # Marketplace monitoring
            marketplace = task.get("marketplace")
            categories = task.get("categories")
            
            if marketplace:
                result = await self.monitor_marketplace_activities(marketplace, categories)
                results.append(result)
        
        elif task_type == "trend_analysis":
            # Cybercrime trend analysis
            trend_types = task.get("trend_types")
            timeframe = task.get("timeframe", "30d")
            
            result = await self.analyze_cybercrime_trends(trend_types, timeframe)
            results.append(result)
        
        return {
            "agent_id": self.config.agent_id,
            "task_type": task_type,
            "timestamp": time.time(),
            "results": results,
            "total_collections": len(results),
            "status": "completed",
            "safety_level": self.safety_level,
            "authorization": task.get("authorized", False)
        }

    async def _execute_langchain_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task using LangChain tools.
        
        Args:
            task: Task dictionary containing tool parameters
            
        Returns:
            Dictionary containing tool execution results
        """
        try:
            tool_name = task.get("tool_name")
            tool_params = task.get("tool_params", {})
            
            if tool_name == "web_scraper":
                result = await self.use_web_scraper(
                    website_url=tool_params.get("website_url"),
                    user_prompt=tool_params.get("user_prompt", "")
                )
            elif tool_name == "web_crawler":
                result = await self.use_web_crawler(
                    website_url=tool_params.get("website_url"),
                    user_prompt=tool_params.get("user_prompt", ""),
                    max_depth=tool_params.get("max_depth", 2),
                    max_pages=tool_params.get("max_pages", 5)
                )
            elif tool_name == "search_tool":
                result = await self.use_search_tool(
                    search_query=tool_params.get("search_query"),
                    max_results=tool_params.get("max_results", 10)
                )
            elif tool_name == "markdown_converter":
                result = await self.use_markdown_converter(
                    website_url=tool_params.get("website_url")
                )
            else:
                return {
                    "agent_id": self.config.agent_id,
                    "error": f"Unknown tool: {tool_name}",
                    "status": "error"
                }
            
            return {
                "agent_id": self.config.agent_id,
                "tool_name": tool_name,
                "result": result,
                "status": "completed"
            }
        except Exception as e:
            self.logger.error(f"Error executing LangChain task: {str(e)}")
            return {
                "agent_id": self.config.agent_id,
                "error": str(e),
                "status": "error"
            }
    
    async def _simulate_onion_service_scan(
        self, 
        target: str, 
        scan_type: str, 
        depth: int
    ) -> Dict[str, Any]:
        """Simulate onion service scanning."""
        return {
            "target": target,
            "scan_type": scan_type,
            "depth": depth,
            "findings_count": 3,
            "findings": [
                {
                    "type": "service_identification",
                    "description": f"Service identified: {target}",
                    "confidence": 0.85,
                    "timestamp": self._generate_timestamp(0)
                },
                {
                    "type": "content_analysis",
                    "description": "Basic content analysis completed",
                    "confidence": 0.70,
                    "timestamp": self._generate_timestamp(1)
                },
                {
                    "type": "security_assessment",
                    "description": "Basic security assessment performed",
                    "confidence": 0.60,
                    "timestamp": self._generate_timestamp(2)
                }
            ]
        }
    
    async def _simulate_forum_monitoring(
        self, 
        forum: str, 
        keywords: List[str], 
        timeframe: str
    ) -> Dict[str, Any]:
        """Simulate forum monitoring."""
        mentions = []
        for i, keyword in enumerate(keywords[:3]):
            mention = {
                "keyword": keyword,
                "mentions_found": i + 1,
                "posts": [
                    {
                        "post_id": f"post_{forum}_{i}_{j}",
                        "title": f"Discussion about {keyword}",
                        "author": f"anon_user_{i}_{j}",
                        "timestamp": self._generate_timestamp(i * 24 + j * 6),
                        "relevance_score": 0.8 - (i * 0.1)
                    }
                    for j in range(i + 1)
                ]
            }
            mentions.append(mention)
        
        return {
            "forum": forum,
            "timeframe": timeframe,
            "mentions_found": sum(m["mentions_found"] for m in mentions),
            "keyword_mentions": mentions
        }
    
    async def _simulate_leak_scan(
        self, 
        term: str, 
        leak_types: List[str]
    ) -> Dict[str, Any]:
        """Simulate data leak scanning."""
        leaks = []
        for i, leak_type in enumerate(leak_types[:2]):
            leak = {
                "type": leak_type,
                "source": f"leak_site_{i + 1}",
                "description": f"Potential leak data related to {term}",
                "date_found": self._generate_timestamp(i * 7),
                "confidence": 0.75 - (i * 0.1),
                "sample_data": f"sample_{term}_{leak_type}_data",
                "verification_status": "unverified"
            }
            leaks.append(leak)
        
        return {
            "search_term": term,
            "leaks_count": len(leaks),
            "leaks": leaks
        }
    
    async def _simulate_marketplace_monitoring(
        self, 
        marketplace: str, 
        categories: List[str]
    ) -> Dict[str, Any]:
        """Simulate marketplace monitoring."""
        listings = []
        vendors = set()
        
        for i, category in enumerate(categories[:3]):
            for j in range(2):
                vendor = f"vendor_{i}_{j}"
                vendors.add(vendor)
                
                listing = {
                    "id": f"listing_{marketplace}_{i}_{j}",
                    "title": f"Product in {category} category",
                    "category": category,
                    "vendor": vendor,
                    "price": f"${100 + i * 50 + j * 25}",
                    "description": f"Description for {category} product",
                    "posted_date": self._generate_timestamp(i * 3 + j),
                    "reputation_score": 4.5 - (i * 0.3)
                }
                listings.append(listing)
        
        return {
            "listings": listings,
            "vendors": list(vendors),
            "marketplace_stats": {
                "total_listings": len(listings),
                "categories_found": len(set(l["category"] for l in listings)),
                "average_price": 125.0,
                "active_vendors": len(vendors)
            }
        }
    
    async def _simulate_trend_analysis(
        self, 
        trend_types: List[str], 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """Simulate cybercrime trend analysis."""
        trends = []
        
        for i, trend_type in enumerate(trend_types):
            trend = {
                "type": trend_type,
                "timeframe": timeframe,
                "activity_level": "high" if i < 2 else "medium",
                "trend_direction": "increasing" if i < 3 else "stable",
                "indicators": [
                    {
                        "indicator": f"{trend_type}_activity",
                        "count": 100 + i * 50,
                        "change_percent": 15 + i * 5
                    },
                    {
                        "indicator": f"{trend_type}_mentions",
                        "count": 200 + i * 75,
                        "change_percent": 20 + i * 3
                    }
                ],
                "risk_assessment": {
                    "current_risk": "high" if i < 2 else "medium",
                    "threat_level": 7 + i,
                    "affected_sectors": ["technology", "finance", "healthcare"][:i + 1]
                }
            }
            trends.append(trend)
        
        return trends
    
    def _generate_timestamp(self, hours_ago: int) -> str:
        """Generate timestamp for hours ago."""
        timestamp = datetime.now() - timedelta(hours=hours_ago)
        return timestamp.isoformat() + "Z"
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the LLM."""
        return """
        You are an expert Dark Web Collector AI assistant. Your role is to collect information 
        from dark web sources including onion services, forums, marketplaces, and leak sites.
        
        When given a request, you should:
        1. Identify the specific type of dark web source to query
        2. Determine the appropriate search parameters
        3. Execute the search using the available tools
        4. Return structured results in the appropriate format
        5. Always prioritize safety and legal compliance
        
        Available platforms: tor_network, i2p_network, freenet, zero_net, 
        dark_web_forums, marketplaces, leak_sites, whistleblower_sites
        """
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate the input data before processing."""
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """Process the LLM response and extract structured output."""
        # For now, return the raw response - in a real implementation,
        # this would parse the LLM response into structured data
        return {"raw_response": raw_output}
    