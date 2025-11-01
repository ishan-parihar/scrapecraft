#!/usr/bin/env python3
"""
AI Agent Example for ScrapeGraph Enhanced Implementation
Production-ready web scraping client with comprehensive features.
"""

import asyncio
import httpx
import json
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from collections import deque
import re
import csv
import io

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("scraping_agent")

@dataclass
class ScrapingConfig:
    """Production scraping configuration."""
    base_url: str = "http://localhost:8000"
    batch_size: int = 5
    max_retries: int = 3
    timeout_per_url: int = 60
    max_concurrent_tasks: int = 10
    rate_limit_delay: float = 1.0
    output_format: str = "json"
    enable_ai_enhancement: bool = False
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # Content filtering
    max_content_length: int = 100000  # 100KB
    allowed_content_types: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.allowed_content_types is None:
            self.allowed_content_types = [
                "text/html", "text/plain", "application/json"
            ]

class RateLimiter:
    """Simple rate limiter for production use."""
    
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.requests = deque()
    
    async def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        
        # Remove old requests (older than 1 minute)
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()
        
        # Check if we would exceed the limit
        if len(self.requests) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.requests[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Add current request
        self.requests.append(now)

class ScrapingMonitor:
    """Monitor scraping operations."""
    
    def __init__(self):
        self.stats = {
            "total_requests": 0,
            "successful_scrapes": 0,
            "failed_scrapes": 0,
            "total_urls_processed": 0,
            "start_time": datetime.now()
        }
    
    def log_request(self, urls: List[str], success: bool, error: Optional[str] = None):
        """Log scraping request."""
        self.stats["total_requests"] += 1
        self.stats["total_urls_processed"] += len(urls)
        
        if success:
            self.stats["successful_scrapes"] += 1
            logger.info(f"Successfully scraped {len(urls)} URLs")
        else:
            self.stats["failed_scrapes"] += 1
            logger.error(f"Failed to scrape {len(urls)} URLs: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        runtime = datetime.now() - self.stats["start_time"]
        return {
            **self.stats,
            "start_time": self.stats["start_time"].isoformat(),  # Convert datetime to string
            "runtime_hours": runtime.total_seconds() / 3600,
            "success_rate": (
                self.stats["successful_scrapes"] / max(self.stats["total_requests"], 1)
            ) * 100,
            "urls_per_hour": (
                self.stats["total_urls_processed"] / max(runtime.total_seconds() / 3600, 1)
            )
        }

class ProductionScrapingAgent:
    """Production-grade scraping agent for ScrapeGraph Enhanced."""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        self.rate_limiter = RateLimiter(config.requests_per_minute)
        self.monitor = ScrapingMonitor()
        self._cache = {}
        
        # Predefined schemas for common use cases
        self.SCHEMAS = {
            "ecommerce": {
                "product_name": {"description": "Name of the product"},
                "price": {"description": "Price of the product"},
                "availability": {"description": "Product availability"},
                "description": {"description": "Product description"},
                "images": {"description": "Product image URLs"},
                "rating": {"description": "Product rating"}
            },
            "news_article": {
                "article_title": {"description": "Article headline"},
                "author": {"description": "Article author"},
                "publish_date": {"description": "Publication date"},
                "content": {"description": "Main article content"},
                "category": {"description": "Article category"},
                "tags": {"description": "Article tags"}
            },
            "contact_info": {
                "company_name": {"description": "Company name"},
                "contact_email": {"description": "Email address"},
                "phone_number": {"description": "Phone number"},
                "address": {"description": "Physical address"},
                "social_media": {"description": "Social media links"}
            }
        }
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def validate_urls(self, urls: List[str]) -> Dict[str, Any]:
        """Validate multiple URLs before scraping."""
        results = {}
        
        for url in urls:
            try:
                await self.rate_limiter.wait_if_needed()
                response = await self.client.post(
                    f"{self.config.base_url}/api/scraping/validate-url",
                    json={"url": url}
                )
                results[url] = response.json()
            except Exception as e:
                results[url] = {"valid": False, "error": str(e)}
        
        return results
    
    async def smart_url_filter(self, urls: List[str]) -> Dict[str, List[str]]:
        """Validate and categorize URLs."""
        validation_results = await self.validate_urls(urls)
        
        categorized = {
            "valid": [],
            "invalid": [],
            "timeout": [],
            "error": []
        }
        
        for url, result in validation_results.items():
            if result.get("valid", False):
                categorized["valid"].append(url)
            elif "timeout" in str(result.get("error", "")).lower():
                categorized["timeout"].append(url)
            else:
                categorized["invalid"].append(url)
        
        return categorized
    
    async def prepare_scraping_batches(
        self, 
        urls: List[str], 
        batch_size: Optional[int] = None
    ) -> List[List[str]]:
        """Prepare validated URLs for batch processing."""
        batch_size = batch_size or self.config.batch_size
        categorized = await self.smart_url_filter(urls)
        
        # Only process valid URLs
        valid_urls = categorized["valid"]
        logger.info(f"Found {len(valid_urls)} valid URLs out of {len(urls)} total")
        
        # Create batches
        batches = [
            valid_urls[i:i + batch_size] 
            for i in range(0, len(valid_urls), batch_size)
        ]
        
        return batches
    
    async def scrape_basic(self, urls: List[str], prompt: str) -> List[Dict[str, Any]]:
        """Basic scraping operation."""
        await self.rate_limiter.wait_if_needed()
        
        response = await self.client.post(
            f"{self.config.base_url}/api/scraping/execute",
            json={
                "urls": urls,
                "prompt": prompt
            }
        )
        
        task_data = response.json()
        task_id = task_data["task_id"]
        
        # Wait for completion and get results
        return await self._wait_for_results(task_id)
    
    async def scrape_structured(
        self, 
        urls: List[str], 
        prompt: str, 
        schema: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract structured data using custom schema."""
        await self.rate_limiter.wait_if_needed()
        
        response = await self.client.post(
            f"{self.config.base_url}/api/scraping/execute",
            json={
                "urls": urls,
                "prompt": prompt,
                "schema": schema
            }
        )
        
        task_id = response.json()["task_id"]
        return await self._wait_for_results(task_id)
    
    async def _wait_for_results(self, task_id: str, max_wait: int = 300) -> List[Dict[str, Any]]:
        """Wait for task completion and return results."""
        start_time = time.time()
        
        while True:
            # Check status
            status_response = await self.client.get(
                f"{self.config.base_url}/api/scraping/status/{task_id}"
            )
            status = status_response.json()["status"]
            
            if status == "completed":
                # Get results
                results_response = await self.client.get(
                    f"{self.config.base_url}/api/scraping/results/{task_id}"
                )
                return results_response.json()
            
            elif status == "failed":
                raise Exception(f"Scraping task failed: {status_response.json().get('error')}")
            
            # Check timeout
            if time.time() - start_time > max_wait:
                raise TimeoutError(f"Task {task_id} timed out after {max_wait} seconds")
            
            await asyncio.sleep(2)
    
    async def batch_scrape_with_retry(
        self,
        url_batches: List[List[str]],
        prompt: str,
        schema: Optional[Dict] = None,
        max_retries: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Process multiple URL batches with retry logic."""
        max_retries = max_retries or self.config.max_retries
        all_results = []
        
        for batch_idx, batch in enumerate(url_batches):
            for attempt in range(max_retries):
                try:
                    if schema:
                        results = await self.scrape_structured(batch, prompt, schema)
                    else:
                        results = await self.scrape_basic(batch, prompt)
                    
                    all_results.extend(results)
                    logger.info(f"Batch {batch_idx + 1}/{len(url_batches)} completed successfully")
                    self.monitor.log_request(batch, True)
                    break
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Batch {batch_idx + 1} failed after {max_retries} attempts: {e}")
                        self.monitor.log_request(batch, False, str(e))
                        # Add failed batch info
                        all_results.extend([{
                            "url": url,
                            "success": False,
                            "error": str(e),
                            "batch": batch_idx + 1
                        } for url in batch])
                    else:
                        logger.warning(f"Batch {batch_idx + 1} attempt {attempt + 1} failed, retrying...")
                        await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
        
        return all_results
    
    def post_process_results(
        self, 
        results: List[Dict[str, Any]], 
        output_format: str = "json"
    ) -> Any:
        """Post-process scraping results."""
        processed_data = {
            "summary": {
                "total_urls": len(results),
                "successful": sum(1 for r in results if r.get("success", False)),
                "failed": sum(1 for r in results if not r.get("success", False)),
                "timestamp": time.time()
            },
            "results": []
        }
        
        for result in results:
            if result.get("success", False) and result.get("data"):
                processed_data["results"].append({
                    "url": result["url"],
                    "title": result["data"].get("title"),
                    "content": result["data"].get("content", "")[:500],  # Preview
                    "metadata": result["data"].get("metadata", {}),
                    "extracted_fields": {
                        k: v for k, v in result["data"].items() 
                        if k not in ["url", "title", "content", "metadata", "scraped_at", "status"]
                    }
                })
            else:
                processed_data["results"].append({
                    "url": result["url"],
                    "success": False,
                    "error": result.get("error")
                })
        
        if output_format == "json":
            return json.dumps(processed_data, indent=2)
        elif output_format == "csv":
            return self._convert_to_csv(processed_data["results"])
        else:
            return processed_data
    
    def _convert_to_csv(self, results: List[Dict]) -> str:
        """Convert results to CSV format."""
        if not results:
            return ""
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        headers = set()
        for result in results:
            headers.update(result.keys())
        writer.writerow(sorted(headers))
        
        # Write rows
        for result in results:
            row = [result.get(header, "") for header in sorted(headers)]
            writer.writerow(row)
        
        return output.getvalue()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "service_status": "unknown",
            "api_endpoints": {},
            "performance_test": {},
            "error_count": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test service availability
            response = await self.client.get(f"{self.config.base_url}/docs")
            health_status["service_status"] = "healthy" if response.status_code == 200 else "unhealthy"
            
            # Test key endpoints
            endpoints_to_test = [
                "/api/scraping/validate-url",
                "/api/scraping/search"
            ]
            
            for endpoint in endpoints_to_test:
                try:
                    if "validate-url" in endpoint:
                        response = await self.client.post(
                            f"{self.config.base_url}{endpoint}",
                            json={"url": "https://example.com"}
                        )
                    else:
                        response = await self.client.post(
                            f"{self.config.base_url}{endpoint}",
                            params={"query": "test"}
                        )
                    
                    health_status["api_endpoints"][endpoint] = {
                        "status": "healthy" if response.status_code == 200 else "unhealthy",
                        "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else "unknown"
                    }
                except Exception as e:
                    health_status["api_endpoints"][endpoint] = {
                        "status": "error",
                        "error": str(e)
                    }
                    health_status["error_count"] += 1
            
            # Performance test
            start_time = time.time()
            test_result = await self.scrape_basic(
                ["https://example.com"], 
                "Test extraction"
            )
            end_time = time.time()
            
            health_status["performance_test"] = {
                "test_url": "https://example.com",
                "response_time": end_time - start_time,
                "success": len(test_result) > 0 and test_result[0].get("success", False)
            }
            
        except Exception as e:
            health_status["service_status"] = "error"
            health_status["error"] = str(e)
            health_status["error_count"] += 1
        
        return health_status
    
    # Use case methods
    
    async def monitor_ecommerce_products(
        self,
        product_urls: List[str],
        output_file: str = "products.json"
    ) -> str:
        """Monitor e-commerce products for price and availability changes."""
        
        # Validate and prepare URLs
        batches = await self.prepare_scraping_batches(product_urls)
        
        # Scrape with monitoring
        all_results = await self.batch_scrape_with_retry(
            batches,
            "Extract product information including price, availability, and description",
            self.SCHEMAS["ecommerce"]
        )
        
        # Process and save results
        processed_data = self.post_process_results(all_results, "json")
        
        with open(output_file, 'w') as f:
            f.write(processed_data)
        
        # Log summary
        stats = self.monitor.get_stats()
        logger.info(f"E-commerce monitoring completed: {stats}")
        
        return processed_data
    
    async def aggregate_news_articles(
        self,
        news_urls: List[str],
        category: str = "general",
        output_file: str = "articles.json"
    ) -> str:
        """Aggregate news articles from multiple sources."""
        
        # Validate and prepare URLs
        batches = await self.prepare_scraping_batches(news_urls, batch_size=2)
        
        # Scrape with article-specific schema
        all_results = await self.batch_scrape_with_retry(
            batches,
            f"Extract article information for {category} news",
            self.SCHEMAS["news_article"]
        )
        
        # Filter by content quality
        filtered_results = self._filter_articles_by_quality(all_results)
        
        # Process and save results
        processed_data = self.post_process_results(filtered_results, "json")
        
        with open(output_file, 'w') as f:
            f.write(processed_data)
        
        return processed_data
    
    async def extract_contacts(
        self,
        website_urls: List[str],
        business_type: str = "general",
        output_file: str = "contacts.csv"
    ) -> str:
        """Extract contact information from business websites."""
        
        # Validate and prepare URLs
        batches = await self.prepare_scraping_batches(website_urls, batch_size=4)
        
        # Scrape contact information
        all_results = await self.batch_scrape_with_retry(
            batches,
            f"Extract {business_type} business contact information",
            self.SCHEMAS["contact_info"]
        )
        
        # Validate extracted contacts
        validated_contacts = self._validate_contact_data(all_results)
        
        # Process and save results
        processed_data = self.post_process_results(validated_contacts, "csv")
        
        with open(output_file, 'w') as f:
            f.write(processed_data)
        
        return processed_data
    
    def _filter_articles_by_quality(self, results: List[Dict]) -> List[Dict]:
        """Filter articles by quality criteria."""
        filtered = []
        
        for result in results:
            if result.get("success") and result.get("data"):
                data = result["data"]
                
                # Quality checks
                content_length = len(data.get("content", ""))
                has_title = bool(data.get("article_title"))
                has_content = content_length > 200
                
                if has_title and has_content:
                    filtered.append(result)
        
        return filtered
    
    def _validate_contact_data(self, results: List[Dict]) -> List[Dict]:
        """Validate and clean contact information."""
        validated = []
        
        for result in results:
            if result.get("success") and result.get("data"):
                data = result["data"]
                
                # Validate email
                email = data.get("contact_email")
                if email and not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                    data["contact_email"] = None
                
                # Validate phone
                phone = data.get("phone_number")
                if phone and not re.match(r'[\d\-\+\(\)\s]+', phone):
                    data["phone_number"] = None
                
                validated.append(result)
        
        return validated

# Example usage
async def main():
    """Example usage of the ProductionScrapingAgent."""
    
    # Configuration
    config = ScrapingConfig(
        base_url="http://localhost:8000",
        batch_size=3,
        max_retries=2,
        rate_limit_delay=2.0,
        requests_per_minute=30
    )
    
    async with ProductionScrapingAgent(config) as agent:
        # Health check
        health = await agent.health_check()
        print("Health Check Results:")
        print(json.dumps(health, indent=2))
        
        # Example 1: E-commerce monitoring
        product_urls = [
            "https://example-store.com/product1",
            "https://example-store.com/product2"
        ]
        
        try:
            products = await agent.monitor_ecommerce_products(
                product_urls, 
                "products.json"
            )
            print(f"E-commerce monitoring completed. Results saved to products.json")
        except Exception as e:
            print(f"E-commerce monitoring failed: {e}")
        
        # Example 2: News aggregation
        news_urls = [
            "https://example-news.com/article1",
            "https://example-news.com/article2"
        ]
        
        try:
            articles = await agent.aggregate_news_articles(
                news_urls,
                "technology",
                "articles.json"
            )
            print(f"News aggregation completed. Results saved to articles.json")
        except Exception as e:
            print(f"News aggregation failed: {e}")
        
        # Example 3: Contact extraction
        business_urls = [
            "https://example-business1.com",
            "https://example-business2.com"
        ]
        
        try:
            contacts = await agent.extract_contacts(
                business_urls,
                "technology",
                "contacts.csv"
            )
            print(f"Contact extraction completed. Results saved to contacts.csv")
        except Exception as e:
            print(f"Contact extraction failed: {e}")
        
        # Print final statistics
        stats = agent.monitor.get_stats()
        print("\nFinal Statistics:")
        print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(main())