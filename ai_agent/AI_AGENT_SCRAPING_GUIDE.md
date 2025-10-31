# AI Agent Production Scraping Guide
## ScrapeGraph Enhanced Implementation

## Overview

This guide provides AI Agents with comprehensive instructions for utilizing the ScrapeGraph Enhanced Implementation in production environments. The system offers robust, locally-hosted web scraping capabilities without external API dependencies.

## 🚀 Quick Start for AI Agents

### 1. Environment Setup

```python
# Required environment variables
import os
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379')
os.environ.setdefault('USE_LOCAL_SCRAPING', 'true')
os.environ.setdefault('SCRAPEGRAPH_API_KEY', 'not-used-with-local-scraping')

# Optional: OpenAI for enhanced extraction
os.environ.setdefault('OPENAI_API_KEY', 'your-openai-key-here')
```

### 2. API Client Initialization

```python
import httpx
import asyncio
from typing import List, Dict, Optional, Any
import json
import uuid

class ScrapeGraphAgent:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
```

## 📋 Core Operations

### 1. URL Validation

```python
async def validate_urls(self, urls: List[str]) -> Dict[str, Any]:
    """Validate multiple URLs before scraping."""
    results = {}
    
    for url in urls:
        try:
            response = await self.client.post(
                f"{self.base_url}/api/scraping/validate-url",
                json={"url": url}
            )
            results[url] = response.json()
        except Exception as e:
            results[url] = {"valid": False, "error": str(e)}
    
    return results
```

### 2. Basic Scraping

```python
async def scrape_basic(self, urls: List[str], prompt: str) -> str:
    """Basic scraping operation."""
    response = await self.client.post(
        f"{self.base_url}/api/scraping/execute",
        json={
            "urls": urls,
            "prompt": prompt
        }
    )
    
    task_data = response.json()
    task_id = task_data["task_id"]
    
    # Wait for completion and get results
    return await self._wait_for_results(task_id)
```

### 3. Structured Data Extraction

```python
async def scrape_structured(
    self, 
    urls: List[str], 
    prompt: str, 
    schema: Dict[str, Any]
) -> str:
    """Extract structured data using custom schema."""
    response = await self.client.post(
        f"{self.base_url}/api/scraping/execute",
        json={
            "urls": urls,
            "prompt": prompt,
            "schema": schema
        }
    )
    
    task_id = response.json()["task_id"]
    return await self._wait_for_results(task_id)

# Predefined schemas for common use cases
SCHEMAS = {
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
```

### 4. Task Management

```python
async def _wait_for_results(self, task_id: str, max_wait: int = 300) -> str:
    """Wait for task completion and return results."""
    start_time = asyncio.get_event_loop().time()
    
    while True:
        # Check status
        status_response = await self.client.get(
            f"{self.base_url}/api/scraping/status/{task_id}"
        )
        status = status_response.json()["status"]
        
        if status == "completed":
            # Get results
            results_response = await self.client.get(
                f"{self.base_url}/api/scraping/results/{task_id}"
            )
            return results_response.json()
        
        elif status == "failed":
            raise Exception(f"Scraping task failed: {status_response.json().get('error')}")
        
        # Check timeout
        if asyncio.get_event_loop().time() - start_time > max_wait:
            raise TimeoutError(f"Task {task_id} timed out after {max_wait} seconds")
        
        await asyncio.sleep(2)

async def get_task_status(self, task_id: str) -> Dict[str, Any]:
    """Get current task status."""
    response = await self.client.get(
        f"{self.base_url}/api/scraping/status/{task_id}"
    )
    return response.json()

async def get_task_results(self, task_id: str) -> List[Dict[str, Any]]:
    """Get task results (must be completed)."""
    response = await self.client.get(
        f"{self.base_url}/api/scraping/results/{task_id}"
    )
    return response.json()
```

## 🎯 Production Patterns

### 1. Batch Processing with Retry Logic

```python
async def batch_scrape_with_retry(
    self,
    url_batches: List[List[str]],
    prompt: str,
    schema: Optional[Dict] = None,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """Process multiple URL batches with retry logic."""
    all_results = []
    
    for batch_idx, batch in enumerate(url_batches):
        for attempt in range(max_retries):
            try:
                if schema:
                    results = await self.scrape_structured(batch, prompt, schema)
                else:
                    results = await self.scrape_basic(batch, prompt)
                
                all_results.extend(results)
                print(f"Batch {batch_idx + 1}/{len(url_batches)} completed successfully")
                break
                
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Batch {batch_idx + 1} failed after {max_retries} attempts: {e}")
                    # Add failed batch info
                    all_results.extend([{
                        "url": url,
                        "success": False,
                        "error": str(e),
                        "batch": batch_idx + 1
                    } for url in batch])
                else:
                    print(f"Batch {batch_idx + 1} attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(5 * (attempt + 1))  # Exponential backoff
    
    return all_results
```

### 2. Smart URL Validation and Filtering

```python
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
    batch_size: int = 5
) -> List[List[str]]:
    """Prepare validated URLs for batch processing."""
    categorized = await self.smart_url_filter(urls)
    
    # Only process valid URLs
    valid_urls = categorized["valid"]
    print(f"Found {len(valid_urls)} valid URLs out of {len(urls)} total")
    
    # Create batches
    batches = [
        valid_urls[i:i + batch_size] 
        for i in range(0, len(valid_urls), batch_size)
    ]
    
    return batches
```

### 3. Data Post-Processing

```python
def post_process_results(
    results: List[Dict[str, Any]], 
    output_format: str = "json"
) -> Any:
    """Post-process scraping results."""
    processed_data = {
        "summary": {
            "total_urls": len(results),
            "successful": sum(1 for r in results if r.get("success", False)),
            "failed": sum(1 for r in results if not r.get("success", False)),
            "timestamp": asyncio.get_event_loop().time()
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
    import csv
    import io
    
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
```

## 🏗️ Production Architecture

### 1. Configuration Management

```python
from dataclasses import dataclass
from typing import Optional

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
    allowed_content_types: List[str] = None
    
    def __post_init__(self):
        if self.allowed_content_types is None:
            self.allowed_content_types = [
                "text/html", "text/plain", "application/json"
            ]
```

### 2. Rate Limiting

```python
import time
from collections import deque

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
```

### 3. Monitoring and Logging

```python
import logging
from datetime import datetime

class ScrapingMonitor:
    """Monitor scraping operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("scraping_monitor")
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
            self.logger.info(f"Successfully scraped {len(urls)} URLs")
        else:
            self.stats["failed_scrapes"] += 1
            self.logger.error(f"Failed to scrape {len(urls)} URLs: {error}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        runtime = datetime.now() - self.stats["start_time"]
        return {
            **self.stats,
            "runtime_hours": runtime.total_seconds() / 3600,
            "success_rate": (
                self.stats["successful_scrapes"] / max(self.stats["total_requests"], 1)
            ) * 100,
            "urls_per_hour": (
                self.stats["total_urls_processed"] / max(runtime.total_seconds() / 3600, 1)
            )
        }
```

## 📊 Use Case Templates

### 1. E-commerce Product Monitoring

```python
async def monitor_ecommerce_products(
    self,
    product_urls: List[str],
    output_file: str = "products.json"
) -> str:
    """Monitor e-commerce products for price and availability changes."""
    
    config = ScrapingConfig(
        batch_size=3,
        max_retries=2,
        rate_limit_delay=2.0
    )
    
    monitor = ScrapingMonitor()
    rate_limiter = RateLimiter(requests_per_minute=30)
    
    async with self:
        # Validate URLs
        batches = await self.prepare_scraping_batches(product_urls, config.batch_size)
        
        # Scrape with monitoring
        all_results = []
        for batch in batches:
            await rate_limiter.wait_if_needed()
            
            try:
                results = await self.scrape_structured(
                    batch,
                    "Extract product information including price, availability, and description",
                    SCHEMAS["ecommerce"]
                )
                all_results.extend(results)
                monitor.log_request(batch, True)
                
            except Exception as e:
                monitor.log_request(batch, False, str(e))
        
        # Process and save results
        processed_data = self.post_process_results(all_results, "json")
        
        with open(output_file, 'w') as f:
            f.write(processed_data)
        
        # Log summary
        stats = monitor.get_stats()
        print(f"Monitoring completed: {stats}")
        
        return processed_data
```

### 2. News Article Aggregation

```python
async def aggregate_news_articles(
    self,
    news_urls: List[str],
    category: str = "general"
) -> str:
    """Aggregate news articles from multiple sources."""
    
    async with self:
        # Validate and prepare URLs
        batches = await self.prepare_scraping_batches(news_urls, batch_size=2)
        
        # Scrape with article-specific schema
        all_results = []
        for batch in batches:
            try:
                results = await self.scrape_structured(
                    batch,
                    f"Extract article information for {category} news",
                    SCHEMAS["news_article"]
                )
                all_results.extend(results)
            except Exception as e:
                print(f"Failed to scrape batch: {e}")
        
        # Filter by content quality
        filtered_results = self._filter_articles_by_quality(all_results)
        
        return self.post_process_results(filtered_results, "json")

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
```

### 3. Contact Information Extraction

```python
async def extract_contacts(
    self,
    website_urls: List[str],
    business_type: str = "general"
) -> str:
    """Extract contact information from business websites."""
    
    async with self:
        batches = await self.prepare_scraping_batches(website_urls, batch_size=4)
        
        all_results = []
        for batch in batches:
            try:
                results = await self.scrape_structured(
                    batch,
                    f"Extract {business_type} business contact information",
                    SCHEMAS["contact_info"]
                )
                all_results.extend(results)
            except Exception as e:
                print(f"Failed to extract contacts: {e}")
        
        # Validate extracted contacts
        validated_contacts = self._validate_contact_data(all_results)
        
        return self.post_process_results(validated_contacts, "csv")

def _validate_contact_data(self, results: List[Dict]) -> List[Dict]:
    """Validate and clean contact information."""
    import re
    
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
```

## 🛡️ Error Handling and Recovery

### 1. Comprehensive Error Handling

```python
async def safe_scrape_operation(
    self,
    urls: List[str],
    prompt: str,
    schema: Optional[Dict] = None,
    error_recovery: bool = True
) -> Dict[str, Any]:
    """Safe scraping operation with comprehensive error handling."""
    
    result = {
        "success": False,
        "data": None,
        "error": None,
        "recovery_attempts": 0
    }
    
    try:
        # Pre-validation
        if not urls:
            raise ValueError("No URLs provided")
        
        # Validate URLs first
        validation = await self.validate_urls(urls[:1])  # Test first URL
        if not validation.get(urls[0], {}).get("valid", False):
            raise ValueError(f"URL validation failed: {validation}")
        
        # Attempt scraping
        if schema:
            scraped_data = await self.scrape_structured(urls, prompt, schema)
        else:
            scraped_data = await self.scrape_basic(urls, prompt)
        
        result["success"] = True
        result["data"] = scraped_data
        
    except Exception as e:
        result["error"] = str(e)
        
        # Error recovery
        if error_recovery:
            result["recovery_attempts"] = await self._attempt_recovery(urls, prompt, schema)
    
    return result

async def _attempt_recovery(
    self, 
    urls: List[str], 
    prompt: str, 
    schema: Optional[Dict]
) -> int:
    """Attempt to recover from scraping errors."""
    recovery_attempts = 0
    
    # Strategy 1: Reduce batch size
    if len(urls) > 1:
        try:
            for url in urls:
                if schema:
                    await self.scrape_structured([url], prompt, schema)
                else:
                    await self.scrape_basic([url], prompt)
                recovery_attempts += 1
        except:
            pass
    
    # Strategy 2: Simplify prompt
    if recovery_attempts == 0:
        try:
            simple_prompt = "Extract the main content"
            await self.scrape_basic(urls, simple_prompt)
            recovery_attempts += 1
        except:
            pass
    
    return recovery_attempts
```

### 2. Health Check and Diagnostics

```python
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
        response = await self.client.get(f"{self.base_url}/docs")
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
                        f"{self.base_url}{endpoint}",
                        json={"url": "https://example.com"}
                    )
                else:
                    response = await self.client.post(
                        f"{self.base_url}{endpoint}?query=test"
                    )
                
                health_status["api_endpoints"][endpoint] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "response_time": response.elapsed.total_seconds()
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
```

## 📈 Performance Optimization

### 1. Connection Pooling

```python
class OptimizedScrapeGraphAgent(ScrapeGraphAgent):
    """Optimized agent with connection pooling and caching."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        super().__init__(base_url)
        self.client = httpx.AsyncClient(
            timeout=60.0,
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=100)
        )
        self._cache = {}
    
    async def scrape_with_cache(
        self, 
        urls: List[str], 
        prompt: str, 
        use_cache: bool = True
    ) -> List[Dict]:
        """Scrape with caching support."""
        cache_key = f"{hash(str(sorted(urls)))}_{hash(prompt)}"
        
        if use_cache and cache_key in self._cache:
            print("Returning cached results")
            return self._cache[cache_key]
        
        # Perform scraping
        results = await self.scrape_basic(urls, prompt)
        
        # Cache results
        if use_cache:
            self._cache[cache_key] = results
        
        return results
```

### 2. Concurrent Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def concurrent_scrape(
    self,
    url_batches: List[List[str]],
    prompt: str,
    max_concurrent: int = 5
) -> List[Dict]:
    """Scrape multiple batches concurrently."""
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def scrape_batch(batch):
        async with semaphore:
            return await self.scrape_basic(batch, prompt)
    
    tasks = [scrape_batch(batch) for batch in url_batches]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Flatten results and handle exceptions
    flattened_results = []
    for result in results:
        if isinstance(result, Exception):
            print(f"Batch failed: {result}")
        else:
            flattened_results.extend(result)
    
    return flattened_results
```

## 🔧 Deployment and Scaling

### 1. Docker Configuration

```dockerfile
# Dockerfile for AI Agent
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY ai_agent.py .
COPY config.py .

CMD ["python", "ai_agent.py"]
```

### 2. Kubernetes Deployment

```yaml
# k8s-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: scraping-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: scraping-agent
  template:
    metadata:
      labels:
        app: scraping-agent
    spec:
      containers:
      - name: agent
        image: scraping-agent:latest
        env:
        - name: SCRAPEGRAPH_URL
          value: "http://scraping-service:8000"
        - name: REDIS_URL
          value: "redis://redis:6379"
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 📚 Best Practices

### 1. Data Quality Assurance

```python
def validate_scraped_data(self, data: Dict[str, Any], schema: Dict) -> Dict[str, Any]:
    """Validate scraped data against expected schema."""
    validation_result = {
        "is_valid": True,
        "errors": [],
        "warnings": []
    }
    
    for field_name, field_config in schema.items():
        field_value = data.get(field_name)
        
        if field_config.get("required", False) and not field_value:
            validation_result["errors"].append(f"Required field '{field_name}' is missing")
            validation_result["is_valid"] = False
        
        # Type validation
        expected_type = field_config.get("type")
        if expected_type and field_value and not isinstance(field_value, expected_type):
            validation_result["warnings"].append(
                f"Field '{field_name}' has incorrect type, expected {expected_type.__name__}"
            )
    
    return validation_result
```

### 2. Resource Management

```python
async def scrape_with_resource_management(
    self,
    urls: List[str],
    prompt: str,
    max_memory_mb: int = 1024
) -> List[Dict]:
    """Scrape with memory and resource management."""
    import psutil
    
    process = psutil.Process()
    
    # Check available memory
    available_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    if available_memory > max_memory_mb:
        raise MemoryError(f"Memory usage ({available_memory}MB) exceeds limit ({max_memory_mb}MB)")
    
    # Process in smaller batches if needed
    batch_size = max(1, len(urls) // 4)  # Adjust based on memory constraints
    
    results = []
    for i in range(0, len(urls), batch_size):
        batch = urls[i:i + batch_size]
        batch_results = await self.scrape_basic(batch, prompt)
        results.extend(batch_results)
        
        # Check memory after each batch
        current_memory = process.memory_info().rss / 1024 / 1024
        if current_memory > max_memory_mb:
            print(f"Memory limit reached, stopping after {i + batch_size} URLs")
            break
    
    return results
```

## 🎯 Conclusion

This guide provides AI Agents with a comprehensive framework for production-grade web scraping using the ScrapeGraph Enhanced Implementation. Key features include:

- **Robust Error Handling**: Comprehensive error recovery and validation
- **Performance Optimization**: Connection pooling, caching, and concurrent processing
- **Scalability**: Batch processing and resource management
- **Monitoring**: Health checks and performance metrics
- **Flexibility**: Support for various data extraction schemas and formats

The system is designed to handle large-scale scraping operations while maintaining data quality and system reliability. AI Agents can leverage these patterns to build sophisticated scraping solutions for various use cases including e-commerce monitoring, news aggregation, and contact information extraction.