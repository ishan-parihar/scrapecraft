"""
Surface Web Collector Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup

from ..base.osint_agent import OSINTAgent


class SurfaceWebCollectorAgent(OSINTAgent):
    """
    Agent responsible for collecting information from the surface web.
    Handles search engines, public websites, and openly accessible content.
    """
    
    def __init__(self, agent_id: str = "surface_web_collector"):
        super().__init__(agent_id, "Surface Web Collector")
        self.supported_search_engines = [
            "google", "bing", "duckduckgo", "yahoo", "yandex"
        ]
        self.user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        self.request_delay = 1.0  # Delay between requests to avoid rate limiting
        
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
        self.log_activity(f"Searching {engine} for: {query}")
        
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
            
            self.log_activity(f"Found {len(results)} results from {engine}")
            return collection_data
            
        except Exception as e:
            self.log_activity(f"Error searching {engine}: {str(e)}", level="error")
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
        self.log_activity(f"Scraping website: {url}")
        
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
                
                self.log_activity(f"Successfully scraped {url}")
                return collection_data
                
        except Exception as e:
            self.log_activity(f"Error scraping {url}: {str(e)}", level="error")
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
        self.log_activity(f"Collecting domain info for: {domain}")
        
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
            
            self.log_activity(f"Domain info collected for {domain}")
            return collection_data
            
        except Exception as e:
            self.log_activity(f"Error collecting domain info for {domain}: {str(e)}", level="error")
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
            # Website scraping
            urls = task.get("urls", [])
            extract_links = task.get("extract_links", True)
            max_depth = task.get("max_depth", 1)
            
            for url in urls:
                result = await self.scrape_website(url, extract_links, max_depth)
                results.append(result)
                await asyncio.sleep(self.request_delay)
        
        elif task_type == "domain":
            # Domain analysis
            domains = task.get("domains", [])
            
            for domain in domains:
                result = await self.collect_domain_info(domain)
                results.append(result)
                await asyncio.sleep(self.request_delay)
        
        return {
            "agent_id": self.agent_id,
            "task_type": task_type,
            "timestamp": time.time(),
            "results": results,
            "total_collections": len(results),
            "status": "completed"
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
        return {
            "title": soup.title.string if soup.title else "",
            "meta_description": self._get_meta_description(soup),
            "headings": self._extract_headings(soup),
            "text_content": soup.get_text(strip=True)[:1000],  # First 1000 chars
            "images": [img.get('src', '') for img in soup.find_all('img')[:5]],
            "forms": len(soup.find_all('form')),
            "links_count": len(soup.find_all('a')),
            "word_count": len(soup.get_text().split())
        }
    
    def _get_meta_description(self, soup: BeautifulSoup) -> str:
        """Extract meta description from HTML."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        return meta_desc.get('content', '') if meta_desc else ''
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract headings from HTML."""
        headings = {}
        for level in range(1, 7):
            tags = soup.find_all(f'h{level}')
            headings[f'h{level}'] = [tag.get_text().strip() for tag in tags[:5]]
        return headings
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Extract links from HTML."""
        links = []
        for link in soup.find_all('a', href=True)[:10]:
            href = link['href']
            absolute_url = urljoin(base_url, href)
            links.append({
                "url": absolute_url,
                "text": link.get_text().strip(),
                "title": link.get('title', ''),
                "target": link.get('target', '')
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