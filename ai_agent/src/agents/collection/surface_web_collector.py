"""
Surface Web Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

from ..base.osint_agent import LLMOSINTAgent, AgentConfig
from ...utils.tools.scrapegraph_integration import get_global_tool_manager


class SurfaceWebCollectorAgent(LLMOSINTAgent):
    """
    Agent responsible for collecting information from the surface web.
    Handles search engines, public websites, and openly accessible content.
    """
    
    def __init__(self, agent_id: str = "surface_web_collector", tools: Optional[List[Any]] = None):
        config = AgentConfig(
            agent_id=agent_id,
            role="Surface Web Collector",
            description="Collects information from search engines, public websites, and surface web content"
        )
        # Initialize with tools
        super().__init__(config=config, tools=tools or [])
        self.tool_manager = get_global_tool_manager()
        self.supported_search_engines = [
            "google", "bing", "duckduckgo", "yahoo", "yandex"
        ]
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.request_delay = 1.0  # Delay between requests to avoid rate limiting
        self.supported_search_engines = [
            "google", "bing", "duckduckgo", "yahoo", "yandex"
        ]
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.request_delay = 1.0  # Delay between requests to avoid rate limiting
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Surface Web Collector Agent.
        """
        return """
        You are a Surface Web Collector Agent, specialized in gathering information from publicly accessible websites, 
        search engines, and surface web resources. Your role is to collect relevant information based on the user's 
        request while maintaining ethical standards and respecting website terms of service.

        You should:
        1. Use proper search techniques to find relevant information
        2. Extract meaningful content from web pages
        3. Identify and collect domain-related information
        4. Respect rate limits and website policies
        5. Structure the collected information in a clear, organized format
        """
    
    async def _execute_agent(self, input_data: Dict[str, Any]) -> str:
        """
        Execute the agent with actual collection task.
        """
        try:
            # Call the specialized execute_task method which handles the actual collection
            import json
            result = await self.execute_task(input_data)
            return json.dumps(result)
        except Exception as e:
            # If there's an error, return a structured error response
            error_result = {
                "error": str(e),
                "agent_type": "SurfaceWebCollector",
                "status": "failed"
            }
            import json
            return json.dumps(error_result)

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process and structure the raw output from the agent.
        """
        import json
        try:
            # Parse the raw JSON output from _execute_agent
            parsed_output = json.loads(raw_output)
            
            # If the output already has the expected structure (like from execute_task), return it
            if isinstance(parsed_output, dict):
                return parsed_output
            else:
                # For other cases, wrap in standard format
                return {
                    "collection_results": parsed_output,
                    "processed_at": time.time(),
                    "agent_type": "SurfaceWebCollector"
                }
        except json.JSONDecodeError:
            # If JSON parsing fails, return standard format with raw output
            return {
                "collection_results": raw_output,
                "processed_at": time.time(),
                "agent_type": "SurfaceWebCollector"
            }

    def _extract_sources(self, result: Dict[str, Any]) -> List[str]:
        """
        Extract source information from the result.
        Override to properly extract URLs from search results.
        """
        sources = []
        
        # Look for results in the result structure
        if "results" in result:
            results = result["results"]
            if isinstance(results, list):
                for result_item in results:
                    if isinstance(result_item, dict):
                        # Extract URLs from result items
                        if "url" in result_item and result_item["url"]:
                            sources.append(result_item["url"])
                        elif "urls" in result_item and isinstance(result_item["urls"], list):
                            sources.extend(result_item["urls"])
                        
                        # Check for nested 'results' in search results
                        if "results" in result_item:
                            nested_results = result_item["results"]
                            if isinstance(nested_results, list):
                                for nested_result in nested_results:
                                    if isinstance(nested_result, dict):
                                        if "url" in nested_result and nested_result["url"]:
                                            sources.append(nested_result["url"])
        
        # Remove duplicates and filter valid URLs
        unique_sources = list(set([s for s in sources if s and s.startswith(('http://', 'https://'))]))
        return unique_sources
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        """
        # Check if the input contains necessary information
        if not input_data:
            return False
        
        # For collection tasks, ensure we have a task type
        task_type = input_data.get("task_type")
        if not task_type or task_type not in ["search", "scrape", "domain"]:
            return False
        
        return True
        
    async def collect_from_search_engine(
        self, 
        query: str, 
        engine: str = "google",
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Collect information from search engines.
        
        Args:
            query: Search query
            engine: Search engine to use
            max_results: Maximum number of results to collect
            
        Returns:
            Dictionary containing search results and metadata
        """
        self.logger.info(f"Searching {engine} for: {query}")
        
        try:
            # Simulate search engine results (in production, would use actual APIs)
            results = await self._simulate_search_results(query, engine, max_results)
            
            collection_data = {
                "source": f"search_engine_{engine}",
                "query": query,
                "timestamp": time.time(),
                "results": results,
                "total_results": len(results),
                "search_engine": engine
            }
            
            self.logger.info(f"Found {len(results)} results from {engine}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error searching {engine}: {str(e)}")
            return {"error": str(e), "source": f"search_engine_{engine}"}
    
    async def scrape_website(
        self, 
        url: str, 
        extract_links: bool = True,
        max_depth: int = 1
    ) -> Dict[str, Any]:
        """
        Scrape content from a website.
        
        Args:
            url: URL to scrape
            extract_links: Whether to extract links from the page
            max_depth: Maximum depth for link extraction
            
        Returns:
            Dictionary containing scraped content and metadata
        """
        self.logger.info(f"Scraping website: {url}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {"User-Agent": self.user_agent}
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                # Parse HTML content
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract basic content
                content_data = self._extract_content(soup, url)
                
                if extract_links and max_depth > 0:
                    links = self._extract_links(soup, url)
                    content_data["links"] = links[:10]  # Limit to first 10 links
                    content_data["max_depth_reached"] = max_depth
                
                collection_data = {
                    "source": "website_scrape",
                    "url": url,
                    "timestamp": time.time(),
                    "status_code": response.status_code,
                    "content_type": response.headers.get("content-type", ""),
                    "content": content_data,
                    "scraped_successfully": True
                }
                
                self.logger.info(f"Successfully scraped {url}")
                return collection_data
                
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {str(e)}")
            return {
                "error": str(e), 
                "source": "website_scrape",
                "url": url,
                "scraped_successfully": False
            }
    
    async def collect_domain_info(self, domain: str) -> Dict[str, Any]:
        """
        Collect basic information about a domain.
        
        Args:
            domain: Domain name to investigate
            
        Returns:
            Dictionary containing domain information
        """
        self.logger.info(f"Collecting domain info for: {domain}")
        
        try:
            # Simulate domain information collection
            domain_info = {
                "domain": domain,
                "timestamp": time.time(),
                "whois_info": await self._simulate_whois_lookup(domain),
                "dns_records": await self._simulate_dns_lookup(domain),
                "subdomains": await self._simulate_subdomain_discovery(domain),
                "technologies": await self._simulate_technology_detection(domain),
                "ssl_info": await self._simulate_ssl_info(domain)
            }
            
            collection_data = {
                "source": "domain_analysis",
                "domain": domain,
                "timestamp": time.time(),
                "domain_info": domain_info,
                "collection_success": True
            }
            
            self.logger.info(f"Domain info collected for {domain}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error collecting domain info for {domain}: {str(e)}")
            return {
                "error": str(e),
                "source": "domain_analysis",
                "domain": domain,
                "collection_success": False
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a surface web collection task.
        
        Args:
            task: Task dictionary containing collection parameters
            
        Returns:
            Dictionary containing collection results
        """
        task_type = task.get("task_type", "search")
        results = []
        
        if task_type == "search":
            # Search engine collection
            queries = task.get("queries", [])
            engines = task.get("engines", ["google"])
            max_results = task.get("max_results", 10)
            
            for query in queries:
                for engine in engines:
                    result = await self.collect_from_search_engine(query, engine, max_results)
                    results.append(result)
                    await asyncio.sleep(self.request_delay)
        
        elif task_type == "scrape":
            # Use scraping tools for website scraping
            urls = task.get("urls", [])
            user_prompt = task.get("user_prompt", "Extract all relevant information")
            
            for url in urls:
                # Use the smart scraper tool if available
                tool_result = await self._use_smart_scraper_tool(url, user_prompt)
                if tool_result["success"]:
                    results.append(tool_result)
                else:
                    # Fall back to traditional scraping
                    result = await self.scrape_website(url)
                    results.append(result)
                await asyncio.sleep(self.request_delay)
        
        elif task_type == "crawl":
            # Use scraping tools for crawling websites
            urls = task.get("urls", [])
            user_prompt = task.get("user_prompt", "Extract all relevant information")
            max_depth = task.get("max_depth", 2)
            max_pages = task.get("max_pages", 5)
            
            for url in urls:
                # Use the smart crawler tool if available
                tool_result = await self._use_smart_crawler_tool(url, user_prompt, max_depth, max_pages)
                if tool_result["success"]:
                    results.append(tool_result)
                else:
                    # For now, we'll fall back to a basic approach
                    fallback_result = {
                        "url": url,
                        "error": "Crawler tool not available, using basic method",
                        "fallback_performed": True
                    }
                    results.append(fallback_result)
                await asyncio.sleep(self.request_delay)
        
        elif task_type == "domain":
            # Domain analysis
            domains = task.get("domains", [])
            
            for domain in domains:
                result = await self.collect_domain_info(domain)
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

    async def _use_smart_scraper_tool(self, url: str, user_prompt: str) -> Dict[str, Any]:
        """
        Use the smart scraper tool to extract data from a website.
        
        Args:
            url: URL to scrape
            user_prompt: Natural language description of what to extract
            
        Returns:
            Dictionary containing scraper tool results
        """
        try:
            # Run the smart scraper tool
            result = await self.tool_manager.execute_tool(
                "smart_scraper",
                website_url=url,
                user_prompt=user_prompt
            )
            return result
        except Exception as e:
            self.logger.error(f"Error using smart scraper tool for {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "tool_used": "smart_scraper"
            }
    
    async def _use_smart_crawler_tool(self, url: str, user_prompt: str, max_depth: int = 2, max_pages: int = 5) -> Dict[str, Any]:
        """
        Use the smart crawler tool to crawl and extract data from a website.
        
        Args:
            url: Starting URL to crawl
            user_prompt: Natural language description of what to extract
            max_depth: Maximum crawling depth
            max_pages: Maximum number of pages to crawl
            
        Returns:
            Dictionary containing crawler tool results
        """
        try:
            # Run the smart crawler tool
            result = await self.tool_manager.execute_tool(
                "smart_crawler",
                website_url=url,
                user_prompt=user_prompt,
                max_depth=max_depth,
                max_pages=max_pages
            )
            return result
        except Exception as e:
            self.logger.error(f"Error using smart crawler tool for {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "tool_used": "smart_crawler"
            }
    
    async def _use_search_scraper_tool(self, search_query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Use the search scraper tool to find and extract data from multiple websites.
        
        Args:
            search_query: Search query to find relevant websites
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary containing search scraper results
        """
        try:
            # Run the search scraper tool
            result = await self.tool_manager.execute_tool(
                "search_scraper",
                search_query=search_query,
                max_results=max_results
            )
            return result
        except Exception as e:
            self.logger.error(f"Error using search scraper tool for '{search_query}': {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": search_query,
                "tool_used": "search_scraper"
            }
    
    async def _use_markdownify_tool(self, url: str) -> Dict[str, Any]:
        """
        Use the markdownify tool to convert a website to markdown format.
        
        Args:
            url: URL to convert to markdown
            
        Returns:
            Dictionary containing markdown conversion results
        """
        try:
            # Run the markdownify tool
            result = await self.tool_manager.execute_tool(
                "markdownify",
                website_url=url
            )
            return result
        except Exception as e:
            self.logger.error(f"Error using markdownify tool for {url}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "url": url,
                "tool_used": "markdownify"
            }
    
    async def _simulate_search_results(
        self, 
        query: str, 
        engine: str, 
        max_results: int
    ) -> List[Dict[str, Any]]:
        """Simulate search engine results for demonstration."""
        results = []
        for i in range(min(max_results, 5)):
            results.append({
                "title": f"Search Result {i+1} for {query}",
                "url": f"https://example{i+1}.com/result/{query.replace(' ', '%20')}",
                "snippet": f"This is a sample search result snippet for the query '{query}' from {engine}.",
                "position": i + 1,
                "domain": f"example{i+1}.com",
                "cache_url": f"https://webcache.googleusercontent.com/search?q=cache:example{i+1}.com",
                "related_pages": [f"https://example{i+1}.com/related{j}" for j in range(3)]
            })
        return results
    
    def _extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract content from parsed HTML."""
        # Extract title safely
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
            title = str(title) if title else ""
        else:
            title = ""
        
        text_content = soup.get_text(strip=True)
        text_content = str(text_content) if text_content else ""
        
        word_text = soup.get_text()
        word_count = len(word_text.split())
        
        return {
            "title": title,
            "meta_description": self._get_meta_description(soup),
            "headings": self._extract_headings(soup),
            "text_content": text_content[:1000],  # First 1000 chars
            "images": [img.get('src', '') or '' for img in soup.find_all('img')[:5]],
            "forms": len(soup.find_all('form')),
            "links_count": len(soup.find_all('a')),
            "word_count": word_count
        }
    
    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from HTML."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            content = meta_desc.get('content', '')
            content = str(content) if content else ''
            return content
        return ''
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract headings from HTML."""
        headings = {}
        for level in range(1, 7):
            tags = soup.find_all(f'h{level}')
            heading_texts = []
            for tag in tags[:5]:
                text = tag.get_text().strip()
                heading_texts.append(text if text else '')
            headings[f'h{level}'] = heading_texts
        return headings
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract links from HTML."""
        links = []
        for link in soup.find_all('a', href=True)[:10]:
            href = link.get('href', '') or ''
            href = str(href) if href else ''
            absolute_url = urljoin(base_url, href)
            raw_text = link.get_text()
            text = str(raw_text).strip()
            title = link.get('title', '') or ''
            target = link.get('target', '') or ''
            links.append({
                "url": absolute_url,
                "text": text,
                "title": title,
                "target": target
            })
        return links
    
    async def _simulate_whois_lookup(self, domain: str) -> Dict[str, Any]:
        """Simulate WHOIS lookup."""
        return {
            "registrar": "Mock Registrar Inc.",
            "creation_date": "2020-01-15",
            "expiration_date": "2025-01-15",
            "status": "active",
            "name_servers": ["ns1.example.com", "ns2.example.com"],
            "registrant": {
                "organization": "Example Organization",
                "country": "US"
            }
        }
    
    async def _simulate_dns_lookup(self, domain: str) -> Dict[str, Any]:
        """Simulate DNS lookup."""
        return {
            "A": ["192.168.1.1", "192.168.1.2"],
            "AAAA": ["2001:db8::1"],
            "MX": ["mail.example.com"],
            "NS": ["ns1.example.com", "ns2.example.com"],
            "TXT": ["v=spf1 include:_spf.example.com ~all"]
        }
    
    async def _simulate_subdomain_discovery(self, domain: str) -> List[str]:
        """Simulate subdomain discovery."""
        return [f"www.{domain}", f"mail.{domain}", f"api.{domain}", f"blog.{domain}"]
    
    async def _simulate_technology_detection(self, domain: str) -> List[str]:
        """Simulate technology detection."""
        return ["Nginx", "React", "WordPress", "Google Analytics"]
    
    async def _simulate_ssl_info(self, domain: str) -> Dict[str, Any]:
        """Simulate SSL certificate information."""
        return {
            "issuer": "Let's Encrypt Authority X3",
            "valid_from": "2024-01-15",
            "valid_until": "2024-04-15",
            "protocol": "TLSv1.3",
            "cipher_suite": "TLS_AES_256_GCM_SHA384",
            "certificate_valid": True
        }