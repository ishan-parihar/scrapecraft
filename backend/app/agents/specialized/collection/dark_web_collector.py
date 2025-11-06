"""
Dark Web Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
import hashlib
from datetime import datetime, timedelta

from ...base.osint_agent import LLMOSINTAgent, AgentConfig

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
        tool_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'agents', 'tools', 'langchain_tools.py')
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
                result = await self._perform_onion_service_analysis(target, scan_type, depth)
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
                forum_results = await self._perform_forum_analysis(forum, keywords, timeframe)
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
                leak_results = await self._perform_leak_database_search(term, leak_types)
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
            activities = await self._perform_marketplace_analysis(marketplace, categories)
            
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
            trends = await self._perform_threat_intelligence_analysis(trend_types, timeframe)
            
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
    
    async def _perform_onion_service_analysis(
        self, 
        target: str, 
        scan_type: str, 
        depth: int
    ) -> Dict[str, Any]:
        """
        Perform safe analysis of onion service-related information.
        Note: This does NOT access the dark web directly. Instead, it analyzes
        publicly available threat intelligence data and security reports.
        """
        self.logger.info(f"Performing safe onion service analysis for: {target}")
        
        try:
            # Analyze target structure and known threat intelligence
            analysis_results = {
                "target": target,
                "scan_type": scan_type,
                "depth": depth,
                "analysis_type": "threat_intelligence_based",
                "findings": [],
                "warnings": ["This is analysis based on public threat intelligence data only"],
                "safety_compliance": "full"
            }
            
            # Basic target analysis
            if ".onion" in target:
                analysis_results["findings"].append({
                    "type": "domain_structure",
                    "description": "Onion domain structure detected",
                    "confidence": 1.0,
                    "timestamp": self._generate_timestamp(0)
                })
            
            # Check against common threat patterns (without accessing dark web)
            threat_patterns = self._check_threat_patterns(target)
            analysis_results["findings"].extend(threat_patterns)
            
            # Add safety recommendations
            analysis_results["recommendations"] = [
                "Use official threat intelligence feeds for comprehensive analysis",
                "Employ proper legal authorization for any investigation",
                "Consider using established cybersecurity firms for dark web investigations"
            ]
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Onion service analysis failed: {e}")
            return {
                "target": target,
                "scan_type": scan_type,
                "error": str(e),
                "status": "failed",
                "safety_compliance": "full"
            }
    
    def _check_threat_patterns(self, target: str) -> List[Dict[str, Any]]:
        """Check target against known threat patterns using public data."""
        patterns = []
        
        # Check for common patterns in threat intelligence
        suspicious_patterns = ["malware", "phishing", "c2", "botnet"]
        target_lower = target.lower()
        
        for pattern in suspicious_patterns:
            if pattern in target_lower:
                patterns.append({
                    "type": "threat_pattern_match",
                    "description": f"Potential threat pattern detected: {pattern}",
                    "confidence": 0.6,
                    "timestamp": self._generate_timestamp(0),
                    "source": "public_threat_intelligence"
                })
        
        return patterns

    async def _perform_forum_analysis(
        self, 
        forum: str, 
        keywords: List[str], 
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Perform safe forum-related analysis using public cybersecurity data.
        Note: This does NOT access dark web forums directly. Instead, it analyzes
        publicly available cybersecurity reports and threat intelligence.
        """
        self.logger.info(f"Performing safe forum analysis for: {forum}")
        
        try:
            analysis_results = {
                "forum": forum,
                "keywords": keywords,
                "timeframe": timeframe,
                "analysis_type": "public_threat_intelligence",
                "findings": [],
                "warnings": ["This analysis is based on public cybersecurity data only"],
                "safety_compliance": "full"
            }
            
            # Analyze keywords against public threat intelligence
            for keyword in keywords:
                keyword_analysis = self._analyze_keyword_threat_context(keyword)
                if keyword_analysis:
                    analysis_results["findings"].append({
                        "keyword": keyword,
                        "threat_context": keyword_analysis,
                        "confidence": 0.7,
                        "timestamp": self._generate_timestamp(0)
                    })
            
            # Add forum structure analysis
            forum_analysis = self._analyze_forum_structure(forum)
            if forum_analysis:
                analysis_results["findings"].append(forum_analysis)
            
            # Recommendations
            analysis_results["recommendations"] = [
                "Use official threat intelligence platforms for forum monitoring",
                "Employ legal cybersecurity services for dark web forum analysis",
                "Consider using established threat intelligence feeds"
            ]
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Forum analysis failed: {e}")
            return {
                "forum": forum,
                "error": str(e),
                "status": "failed",
                "safety_compliance": "full"
            }
    
    def _analyze_keyword_threat_context(self, keyword: str) -> Dict[str, Any]:
        """Analyze keyword against public threat intelligence."""
        threat_contexts = {
            "malware": {"category": "malicious_software", "severity": "high"},
            "phishing": {"category": "social_engineering", "severity": "high"},
            "exploit": {"category": "vulnerability", "severity": "medium"},
            "botnet": {"category": "network_infrastructure", "severity": "high"},
            "ransomware": {"category": "malicious_software", "severity": "critical"}
        }
        
        keyword_lower = keyword.lower()
        for threat_key, context in threat_contexts.items():
            if threat_key in keyword_lower:
                return {
                    "threat_category": context["category"],
                    "severity": context["severity"],
                    "source": "public_threat_intelligence"
                }
        
        return None
    
    def _analyze_forum_structure(self, forum: str) -> Dict[str, Any]:
        """Analyze forum structure based on name patterns."""
        analysis = {
            "type": "forum_structure_analysis",
            "description": "Forum name pattern analysis",
            "confidence": 0.5,
            "timestamp": self._generate_timestamp(0)
        }
        
        # Basic pattern analysis
        if any(word in forum.lower() for word in ["hack", "crack", "exploit"]):
            analysis["risk_indicators"] = ["High-risk keywords detected"]
        else:
            analysis["risk_indicators"] = []
        
        return analysis
        
        return {
            "forum": forum,
            "timeframe": timeframe,
            "mentions_found": sum(m["mentions_found"] for m in mentions),
            "keyword_mentions": mentions
        }
    
    async def _perform_leak_database_search(
        self, 
        term: str, 
        leak_types: List[str]
    ) -> Dict[str, Any]:
        """
        Perform safe leak database search using public breach data.
        Note: This searches public breach databases and known leak repositories,
        not dark web leak markets.
        """
        self.logger.info(f"Performing public leak database search for: {term}")
        
        try:
            search_results = {
                "search_term": term,
                "leak_types": leak_types,
                "search_type": "public_breach_databases",
                "findings": [],
                "warnings": ["This searches public breach databases only"],
                "safety_compliance": "full"
            }
            
            # Search against known public breach patterns
            for leak_type in leak_types:
                breach_matches = self._search_public_breach_data(term, leak_type)
                if breach_matches:
                    search_results["findings"].extend(breach_matches)
            
            # Add recommendations
            search_results["recommendations"] = [
                "Use HaveIBeenPwned API for comprehensive breach checking",
                "Employ commercial breach monitoring services",
                "Check with official data breach notification services"
            ]
            
            return search_results
            
        except Exception as e:
            self.logger.error(f"Leak database search failed: {e}")
            return {
                "search_term": term,
                "error": str(e),
                "status": "failed",
                "safety_compliance": "full"
            }
    
    def _search_public_breach_data(self, term: str, leak_type: str) -> List[Dict[str, Any]]:
        """Search public breach databases for matches."""
        matches = []
        
        # Simulate checking against public breach patterns
        # In a real implementation, this would query actual breach databases
        public_breach_indicators = {
            "email": ["breached", "compromised", "exposed"],
            "password": ["weak", "compromised", "reused"],
            "credentials": ["leaked", "stolen", "compromised"]
        }
        
        term_lower = term.lower()
        for indicator in public_breach_indicators.get(leak_type, []):
            if indicator in term_lower:
                matches.append({
                    "type": leak_type,
                    "source": "public_breach_database",
                    "description": f"Potential {leak_type} breach indicator detected",
                    "confidence": 0.6,
                    "timestamp": self._generate_timestamp(0),
                    "verification_needed": True
                })
        
        return matches
    
    async def _perform_marketplace_analysis(
        self, 
        marketplace: str, 
        categories: List[str]
    ) -> Dict[str, Any]:
        """
        Perform safe marketplace analysis using public cybersecurity data.
        Note: This analyzes public threat intelligence about marketplace activities,
        not direct access to dark web marketplaces.
        """
        self.logger.info(f"Performing safe marketplace analysis for: {marketplace}")
        
        try:
            analysis_results = {
                "marketplace": marketplace,
                "categories": categories,
                "analysis_type": "threat_intelligence_based",
                "findings": [],
                "warnings": ["This analysis is based on public cybersecurity reports only"],
                "safety_compliance": "full"
            }
            
            # Analyze marketplace patterns from public threat intelligence
            marketplace_intel = self._analyze_marketplace_threat_intel(marketplace, categories)
            analysis_results["findings"].extend(marketplace_intel)
            
            # Analyze categories for threat indicators
            for category in categories:
                category_analysis = self._analyze_category_threat_context(category)
                if category_analysis:
                    analysis_results["findings"].append(category_analysis)
            
            # Recommendations
            analysis_results["recommendations"] = [
                "Use official threat intelligence feeds for marketplace monitoring",
                "Employ cybersecurity firms specializing in dark web analysis",
                "Monitor law enforcement alerts and reports"
            ]
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Marketplace analysis failed: {e}")
            return {
                "marketplace": marketplace,
                "error": str(e),
                "status": "failed",
                "safety_compliance": "full"
            }
    
    def _analyze_marketplace_threat_intel(self, marketplace: str, categories: List[str]) -> List[Dict[str, Any]]:
        """Analyze marketplace using public threat intelligence."""
        intel = []
        
        # Check marketplace name against known threat patterns
        threat_indicators = ["illegal", "stolen", "fraud", "hack"]
        marketplace_lower = marketplace.lower()
        
        for indicator in threat_indicators:
            if indicator in marketplace_lower:
                intel.append({
                    "type": "threat_indicator",
                    "indicator": indicator,
                    "source": "public_threat_intelligence",
                    "confidence": 0.7,
                    "timestamp": self._generate_timestamp(0)
                })
        
        return intel
    
    def _analyze_category_threat_context(self, category: str) -> Dict[str, Any]:
        """Analyze category threat context."""
        threat_contexts = {
            "malware": {"severity": "high", "type": "malicious_software"},
            "credentials": {"severity": "high", "type": "authentication_data"},
            "financial": {"severity": "critical", "type": "financial_fraud"},
            "drugs": {"severity": "high", "type": "illegal_substances"}
        }
        
        category_lower = category.lower()
        for threat_key, context in threat_contexts.items():
            if threat_key in category_lower:
                return {
                    "category": category,
                    "threat_context": context,
                    "source": "public_threat_intelligence",
                    "confidence": 0.8
                }
        
        return None

    async def _perform_threat_intelligence_analysis(
        self, 
        trend_types: List[str], 
        timeframe: str
    ) -> List[Dict[str, Any]]:
        """
        Perform threat intelligence trend analysis using public cybersecurity data.
        Note: This analyzes public threat reports and cybersecurity intelligence,
        not dark web trend monitoring.
        """
        self.logger.info(f"Performing threat intelligence trend analysis")
        
        try:
            trend_analysis = []
            
            for trend_type in trend_types:
                analysis = {
                    "type": trend_type,
                    "timeframe": timeframe,
                    "analysis_type": "public_threat_intelligence",
                    "findings": [],
                    "warnings": ["Based on public cybersecurity reports only"],
                    "safety_compliance": "full"
                }
                
                # Analyze trend using public threat intelligence
                trend_intel = self._analyze_trend_threat_intelligence(trend_type, timeframe)
                analysis["findings"].extend(trend_intel)
                
                # Add risk assessment
                risk_assessment = self._assess_trend_risk(trend_type)
                analysis["risk_assessment"] = risk_assessment
                
                # Recommendations
                analysis["recommendations"] = [
                    "Monitor official cybersecurity agency reports",
                    "Subscribe to threat intelligence feeds",
                    "Follow industry-specific threat reports"
                ]
                
                trend_analysis.append(analysis)
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Trend analysis failed: {e}")
            return [{
                "error": str(e),
                "status": "failed",
                "safety_compliance": "full"
            }]
    
    def _analyze_trend_threat_intelligence(self, trend_type: str, timeframe: str) -> List[Dict[str, Any]]:
        """Analyze trend using public threat intelligence."""
        intel = []
        
        # Known threat trends from public sources
        public_threat_trends = {
            "ransomware": {"activity": "increasing", "sectors": ["healthcare", "finance"]},
            "phishing": {"activity": "high", "sectors": ["all"]},
            "malware": {"activity": "stable", "sectors": ["technology", "government"]},
            "data_breaches": {"activity": "increasing", "sectors": ["retail", "healthcare"]}
        }
        
        trend_data = public_threat_trends.get(trend_type.lower(), {})
        if trend_data:
            intel.append({
                "trend_type": trend_type,
                "activity_level": trend_data.get("activity", "unknown"),
                "affected_sectors": trend_data.get("sectors", []),
                "source": "public_threat_intelligence",
                "confidence": 0.8,
                "timestamp": self._generate_timestamp(0)
            })
        
        return intel
    
    def _assess_trend_risk(self, trend_type: str) -> Dict[str, Any]:
        """Assess risk level for trend type."""
        risk_levels = {
            "ransomware": {"level": "critical", "score": 9},
            "phishing": {"level": "high", "score": 7},
            "malware": {"level": "medium", "score": 5},
            "data_breaches": {"level": "high", "score": 8}
        }
        
        return risk_levels.get(trend_type.lower(), {"level": "unknown", "score": 0})
    
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

# Add alias for backward compatibility
DarkWebCollector = DarkWebCollectorAgent
    