# AI Agent Production Scraping Guide

## Overview

This document provides AI Agents with the necessary tools and documentation to utilize the ScrapeGraph Enhanced Implementation for production-grade data scraping projects.

## 📋 Files Created

1. **`AI_AGENT_SCRAPING_GUIDE.md`** - Comprehensive guide with detailed documentation
2. **`ai_agent_example.py`** - Production-ready implementation
3. **`ai_agent_requirements.txt`** - Required dependencies
4. **`test_sites.json`** - Test site database for validation

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r ai_agent_requirements.txt
```

### 2. Basic Usage

```python
import asyncio
from ai_agent_example import ProductionScrapingAgent, ScrapingConfig

async def main():
    config = ScrapingConfig(
        base_url="http://localhost:8000",
        batch_size=5,
        max_retries=3,
        requests_per_minute=60
    )
    
    async with ProductionScrapingAgent(config) as agent:
        # Health check
        health = await agent.health_check()
        print("Service Health:", health["service_status"])
        
        # Basic scraping
        results = await agent.scrape_basic(
            ["https://example.com"],
            "Extract main title and content"
        )
        print("Results:", results)

asyncio.run(main())
```

## 🎯 Production Use Cases

### 1. E-commerce Product Monitoring

```python
# Monitor product prices and availability
products = await agent.monitor_ecommerce_products(
    product_urls=[
        "https://store.com/product1",
        "https://store.com/product2"
    ],
    output_file="products.json"
)
```

### 2. News Article Aggregation

```python
# Aggregate news from multiple sources
articles = await agent.aggregate_news_articles(
    news_urls=[
        "https://news.com/article1",
        "https://news.com/article2"
    ],
    category="technology",
    output_file="articles.json"
)
```

### 3. Contact Information Extraction

```python
# Extract business contact information
contacts = await agent.extract_contacts(
    website_urls=[
        "https://business1.com",
        "https://business2.com"
    ],
    business_type="technology",
    output_file="contacts.csv"
)
```

## 🛠️ Configuration Options

### ScrapingConfig Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `base_url` | `"http://localhost:8000"` | ScrapeGraph service URL |
| `batch_size` | `5` | URLs per batch |
| `max_retries` | `3` | Retry attempts |
| `timeout_per_url` | `60` | Timeout per URL (seconds) |
| `rate_limit_delay` | `1.0` | Delay between requests |
| `requests_per_minute` | `60` | Rate limiting threshold |
| `output_format` | `"json"` | Output format (json/csv) |

## 📊 Features

### ✅ Core Capabilities

- **URL Validation**: Pre-validate URLs before scraping
- **Batch Processing**: Handle multiple URLs efficiently
- **Error Handling**: Comprehensive error recovery
- **Rate Limiting**: Built-in rate limiting for respectful scraping
- **Monitoring**: Performance metrics and health checks
- **Data Validation**: Post-processing and quality checks

### 🎨 Predefined Schemas

- **E-commerce**: Product name, price, availability, description
- **News Articles**: Title, author, date, content, category
- **Contact Info**: Company name, email, phone, address

### 📈 Performance Features

- **Connection Pooling**: Efficient HTTP connections
- **Caching**: Optional result caching
- **Concurrent Processing**: Parallel batch processing
- **Resource Management**: Memory and CPU monitoring

## 🔧 Advanced Usage

### Custom Schema Extraction

```python
custom_schema = {
    "event_name": {"description": "Name of the event"},
    "event_date": {"description": "Date of the event"},
    "location": {"description": "Event location"},
    "price_range": {"description": "Ticket price range"}
}

results = await agent.scrape_structured(
    urls=["https://events.com/conference"],
    prompt="Extract conference event information",
    schema=custom_schema
)
```

### Error Recovery

```python
# Safe scraping with automatic error recovery
results = await agent.batch_scrape_with_retry(
    url_batches=batches,
    prompt="Extract content",
    schema=schema,
    max_retries=5
)
```

### Health Monitoring

```python
# Comprehensive health check
health = await agent.health_check()
print(f"Service Status: {health['service_status']}")
print(f"API Endpoints: {health['api_endpoints']}")
print(f"Performance Test: {health['performance_test']}")
```

## 📋 Best Practices

### 1. Rate Limiting
- Always respect website rate limits
- Use built-in rate limiter
- Configure appropriate delays

### 2. Error Handling
- Implement retry logic
- Monitor failed requests
- Log errors for debugging

### 3. Data Quality
- Validate extracted data
- Filter low-quality content
- Use appropriate schemas

### 4. Resource Management
- Monitor memory usage
- Use batch processing
- Implement timeouts

## 🐳 Docker Deployment

```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY ai_agent_requirements.txt .
RUN pip install -r ai_agent_requirements.txt

COPY ai_agent_example.py .
CMD ["python", "ai_agent_example.py"]
```

## 📈 Monitoring and Metrics

### Statistics Tracking

```python
# Get scraping statistics
stats = agent.monitor.get_stats()
print(f"Success Rate: {stats['success_rate']:.2f}%")
print(f"URLs per Hour: {stats['urls_per_hour']:.2f}")
print(f"Runtime: {stats['runtime_hours']:.2f} hours")
```

### Performance Metrics

- **Response Time**: Average time per request
- **Success Rate**: Percentage of successful scrapes
- **Throughput**: URLs processed per hour
- **Error Rate**: Failed requests percentage

## 🔒 Security Considerations

### Input Validation
- Validate URL formats
- Sanitize user inputs
- Check content types

### Rate Limiting
- Implement per-IP limits
- Use exponential backoff
- Monitor request patterns

### Data Privacy
- Handle sensitive data carefully
- Implement data retention policies
- Use secure storage

## 🚨 Troubleshooting

### Common Issues

1. **Connection Timeout**
   - Check service availability
   - Increase timeout values
   - Verify network connectivity

2. **Rate Limiting**
   - Reduce request frequency
   - Increase delay between requests
   - Implement backoff strategies

3. **Memory Issues**
   - Reduce batch sizes
   - Implement content truncation
   - Monitor memory usage

4. **Data Quality**
   - Validate extraction schemas
   - Filter irrelevant content
   - Improve prompt specificity

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable detailed logging
logger = logging.getLogger("scraping_agent")
logger.setLevel(logging.DEBUG)
```

## 📚 Additional Resources

- **ScrapeGraph Enhanced User Guide**: `SCRAPEGRAPH_USER_GUIDE.md`
- **Test Report**: `SCRAPEGRAPH_TEST_REPORT.md`
- **Test Sites**: `test_sites.json`

## 🤝 Support

For issues and questions:

1. Check service logs
2. Verify URL accessibility
3. Test with simple URLs first
4. Monitor performance metrics
5. Review error messages

---

**Production Ready**: This AI agent implementation is designed for production use with comprehensive error handling, monitoring, and scalability features.