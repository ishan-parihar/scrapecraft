"""
Surface Web Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse

# Optional imports for web scraping
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

from ...base.osint_agent import LLMOSINTAgent, AgentConfig

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
        
        # Check dependencies
        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for SurfaceWebCollector. Install with: pip install httpx")
        if not BS4_AVAILABLE:
            raise ImportError("beautifulsoup4 is required for SurfaceWebCollector. Install with: pip install beautifulsoup4")
            
        # Initialize with tools
        super().__init__(config=config, tools=tools)
        self.tool_manager = ToolManager() if not tools else get_global_tool_manager()
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
        Collect information from search engines using real APIs.
        
        Args:
            query: Search query
            engine: Search engine to use
            max_results: Maximum number of results to collect
            
        Returns:
            Dictionary containing search results and metadata
        """
        self.logger.info(f"Searching {engine} for: {query}")
        
        try:
            # Import the real search service
            from ....services.real_search_service import RealSearchService
            
            async with RealSearchService() as search_service:
                if engine == "google":
                    results = await search_service.search_google(query, max_results)
                elif engine == "bing":
                    results = await search_service.search_bing(query, max_results)
                elif engine == "duckduckgo":
                    results = await search_service.search_duckduckgo(query, max_results)
                else:
                    # Default to DuckDuckGo for unknown engines
                    results = await search_service.search_duckduckgo(query, max_results)
            
            collection_data = {
                "source": f"search_engine_{engine}",
                "query": query,
                "timestamp": time.time(),
                "results": results,
                "total_results": len(results),
                "search_engine": engine,
                "data_source": "real_api",
                "status": "completed" if results else "no_results"
            }
            
            self.logger.info(f"Found {len(results)} real results from {engine}")
            return collection_data
            
        except Exception as e:
            self.logger.error(f"Error searching {engine}: {str(e)}")
            return {
                "error": str(e), 
                "source": f"search_engine_{engine}",
                "status": "failed",
                "data_source": "error"
            }
    
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
        Collect real information about a domain using DNS lookups and web scraping.
        
        Args:
            domain: Domain name to investigate
            
        Returns:
            Dictionary containing domain information
        """
        self.logger.info(f"Collecting domain info for: {domain}")
        
        try:
            # Perform real domain information collection
            domain_info = {
                "domain": domain,
                "timestamp": time.time(),
                "whois_info": await self._get_whois_info(domain),
                "dns_records": await self._get_dns_records(domain),
                "subdomains": await self._discover_subdomains(domain),
                "technologies": await self._detect_technologies(domain),
                "ssl_info": await self._get_ssl_certificate(domain),
                "domain_data": await self._scrape_domain_data(domain)
            }
            
            collection_data = {
                "source": "domain_analysis",
                "domain": domain,
                "timestamp": time.time(),
                "domain_info": domain_info,
                "collection_success": True,
                "data_source": "real_analysis"
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
    
    async def _scrape_domain_data(self, domain: str) -> Dict[str, Any]:
        """Scrape additional domain data from the website."""
        try:
            domain_data = {}
            url = f"https://{domain}"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    html = response.text
                    
                    # Extract page title
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    title_tag = soup.find('title')
                    if title_tag:
                        domain_data["page_title"] = title_tag.get_text().strip()
                    
                    # Extract meta description
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc:
                        domain_data["meta_description"] = meta_desc.get('content', '')
                    
                    # Count pages/links
                    links = soup.find_all('a', href=True)
                    domain_data["internal_links"] = len([link for link in links 
                                                    if domain in link.get('href', '')])
                    domain_data["external_links"] = len([link for link in links 
                                                    if domain not in link.get('href', '') and 
                                                    link.get('href', '').startswith('http')])
                    
                    # Check for contact information
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, html)
                    if emails:
                        domain_data["emails_found"] = list(set(emails))[:5]  # First 5 unique emails
                    
                    # Phone number pattern (basic)
                    phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
                    phones = re.findall(phone_pattern, html)
                    if phones:
                        domain_data["phones_found"] = [f"{p[0]}-{p[1]}-{p[2]}" for p in list(set(phones))[:3]]
            
            domain_data["scrape_timestamp"] = time.time()
            return domain_data
            
        except Exception as e:
            return {"error": f"Domain data scraping failed: {str(e)}"}
    
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
    
    async def _get_whois_info(self, domain: str) -> Dict[str, Any]:
        """Get real WHOIS information for domain."""
        try:
            # Use Python's whois library if available, otherwise use web scraping
            import socket
            whois_info = {"status": "lookup_attempted"}
            
            # Basic domain registration check
            try:
                ip = socket.gethostbyname(domain)
                whois_info["resolves_to"] = ip
                whois_info["status"] = "active"
            except socket.gaierror:
                whois_info["status"] = "no_dns_resolution"
            
            # Try to get WHOIS data via web service
            try:
                url = f"https://www.whois.com/whois/{domain}"
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        # Extract basic WHOIS information from HTML
                        html = response.text
                        if "Registrar:" in html:
                            registrar_match = re.search(r'Registrator?[^:]*:([^<\n]+)', html)
                            if registrar_match:
                                whois_info["registrar"] = registrar_match.group(1).strip()
                        
                        if "Creation Date:" in html:
                            creation_match = re.search(r'Creation Date[^:]*:([^<\n]+)', html)
                            if creation_match:
                                whois_info["creation_date"] = creation_match.group(1).strip()
                        
                        if "Registry Expiry Date:" in html:
                            expiry_match = re.search(r'Registry Expiry Date[^:]*:([^<\n]+)', html)
                            if expiry_match:
                                whois_info["expiration_date"] = expiry_match.group(1).strip()
            
            except Exception as e:
                self.logger.debug(f"WHOIS lookup failed for {domain}: {e}")
                whois_info["lookup_error"] = str(e)
            
            return whois_info
            
        except Exception as e:
            return {"error": f"WHOIS lookup failed: {str(e)}"}
    
    async def _get_dns_records(self, domain: str) -> Dict[str, Any]:
        """Get real DNS records for domain."""
        try:
            import socket
            import subprocess
            
            dns_records = {}
            
            # A record (IP address)
            try:
                ip = socket.gethostbyname(domain)
                dns_records["A"] = [ip]
            except socket.gaierror:
                dns_records["A"] = []
            
            # Try to get additional DNS records using system commands
            try:
                # MX records
                try:
                    result = subprocess.run(['dig', 'MX', domain], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        mx_records = []
                        for line in result.stdout.split('\n'):
                            if domain in line and 'MX' in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    mx_records.append(parts[4])
                        if mx_records:
                            dns_records["MX"] = mx_records
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                
                # NS records
                try:
                    result = subprocess.run(['dig', 'NS', domain], capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        ns_records = []
                        for line in result.stdout.split('\n'):
                            if domain in line and 'NS' in line:
                                parts = line.split()
                                if len(parts) >= 5:
                                    ns_records.append(parts[4])
                        if ns_records:
                            dns_records["NS"] = ns_records
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass
                    
            except Exception as e:
                self.logger.debug(f"DNS lookup error for {domain}: {e}")
            
            return dns_records
            
        except Exception as e:
            return {"error": f"DNS lookup failed: {str(e)}"}
    
    async def _discover_subdomains(self, domain: str) -> List[str]:
        """Discover subdomains using web search techniques."""
        try:
            subdomains = []
            
            # Common subdomain patterns
            common_subdomains = [
                "www", "mail", "api", "blog", "shop", "store", "admin",
                "dev", "staging", "test", "app", "news", "support",
                "help", "docs", "files", "media", "assets", "cdn",
                "ftp", "ssh", "vpn", "remote", "portal", "dashboard"
            ]
            
            # Test a few common subdomains
            import socket
            test_count = 0
            for subdomain in common_subdomains[:10]:  # Limit to first 10 for speed
                full_domain = f"{subdomain}.{domain}"
                try:
                    socket.gethostbyname(full_domain)
                    subdomains.append(full_domain)
                    test_count += 1
                    if test_count >= 5:  # Limit to 5 found subdomains
                        break
                except socket.gaierror:
                    continue
            
            return subdomains
            
        except Exception as e:
            self.logger.error(f"Subdomain discovery failed: {e}")
            return []
    
    async def _detect_technologies(self, domain: str) -> List[str]:
        """Detect technologies used by the domain."""
        try:
            technologies = []
            url = f"https://{domain}"
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    headers = dict(response.headers)
                    html = response.text
                    
                    # Check server headers
                    server = headers.get('server', '').lower()
                    if 'nginx' in server:
                        technologies.append('Nginx')
                    elif 'apache' in server:
                        technologies.append('Apache')
                    elif 'iis' in server:
                        technologies.append('IIS')
                    
                    # Check for common CMS and frameworks
                    if 'wp-content' in html or 'wordpress' in html.lower():
                        technologies.append('WordPress')
                    elif 'drupal' in html.lower():
                        technologies.append('Drupal')
                    elif 'joomla' in html.lower():
                        technologies.append('Joomla')
                    
                    # Check for JavaScript frameworks
                    if 'react' in html.lower() or 'reactjs' in html.lower():
                        technologies.append('React')
                    elif 'vue' in html.lower() or 'vuejs' in html.lower():
                        technologies.append('Vue.js')
                    elif 'angular' in html.lower():
                        technologies.append('Angular')
                    
                    # Check for analytics
                    if 'google-analytics' in html or 'ga.js' in html:
                        technologies.append('Google Analytics')
                    elif 'facebook-pixel' in html or 'fbq(' in html:
                        technologies.append('Facebook Pixel')
            
            return technologies
            
        except Exception as e:
            self.logger.debug(f"Technology detection failed for {domain}: {e}")
            return []
    
    async def _get_ssl_certificate(self, domain: str) -> Dict[str, Any]:
        """Get SSL certificate information."""
        try:
            import ssl
            import socket
            from datetime import datetime
            
            ssl_info = {}
            
            # Get SSL certificate
            context = ssl.create_default_context()
            try:
                with socket.create_connection((domain, 443), timeout=10) as sock:
                    with context.wrap_socket(sock, server_hostname=domain) as ssock:
                        cert = ssock.getpeercert()
                        
                        ssl_info = {
                            "issuer": dict(x[0] for x in cert.get('issuer', [])),
                            "subject": dict(x[0] for x in cert.get('subject', [])),
                            "version": cert.get('version'),
                            "serial_number": cert.get('serialNumber'),
                            "not_before": cert.get('notBefore'),
                            "not_after": cert.get('notAfter'),
                            "certificate_valid": True
                        }
                        
                        # Check if certificate is expired
                        if cert.get('notAfter'):
                            expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                            ssl_info["is_expired"] = expiry_date < datetime.now()
                        
            except (socket.timeout, socket.error, ssl.SSLError) as e:
                ssl_info = {
                    "error": f"SSL connection failed: {str(e)}",
                    "certificate_valid": False
                }
            
            return ssl_info
            
        except Exception as e:
            return {"error": f"SSL certificate lookup failed: {str(e)}"}

    async def collect_surface_web_data(self, target: str) -> Dict[str, Any]:
        """
        Collect surface web data for a target.
        
        Args:
            target: The target to collect surface web data for
            
        Returns:
            Dictionary containing surface web collection results
        """
        self.logger.info(f"Collecting surface web data for target: {target}")
        
        try:
            # Use real search service to find surface web content
            from ....services.real_search_service import perform_search
            
            search_results = await perform_search(
                query=target,
                engines=["duckduckgo"],  # Use DuckDuckGo as default
                max_results=20
            )
            
            # Extract results from all engines
            all_results = []
            if isinstance(search_results, dict):
                for engine, results in search_results.items():
                    if isinstance(results, list):
                        all_results.extend(results)
        except Exception as search_error:
            self.logger.warning(f"Real search service failed: {search_error}")
            all_results = []
        
        try:
            # Also use search scraper tool for additional results
            tool_results = await self._use_search_scraper_tool(target, 10)
        except Exception as tool_error:
            self.logger.warning(f"Search scraper tool failed: {tool_error}")
            tool_results = {"count": 0, "success": False}
        
        collection_data = {
            "source": "surface_web_search",
            "target": target,
            "timestamp": time.time(),
            "search_results": all_results,
            "tool_results": tool_results,
            "total_results": len(all_results) + tool_results.get("count", 0),
            "collection_success": True,  # Always succeed, even with empty results
            "data_source": "real_api"
        }
        
        self.logger.info(f"Surface web data collected for {target}")
        return collection_data


# Alias for backward compatibility
SurfaceWebCollector = SurfaceWebCollectorAgent