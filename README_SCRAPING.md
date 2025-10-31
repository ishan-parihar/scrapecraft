# ScrapeGraph Enhanced - Complete Documentation

## 🎯 Overview

ScrapeGraph Enhanced is a **production-ready, locally-hosted web scraping service** that provides superior functionality compared to external ScrapeGraphAI services. It offers real web scraping capabilities without API dependencies, giving you full control over your data and processing.

## 🚀 Quick Start

### Step 1: Setup Environment

```bash
# Navigate to project directory
cd /path/to/scrapecraft

# Go to backend
cd backend/

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx beautifulsoup4 html2text openai pydantic redis
```

### Step 2: Start the Service

```bash
# Start the API server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Or run the quick start demo
cd ..
python quick_start.py
```

### Step 3: Test It

```bash
# Test basic scraping
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://example.com"],
  "prompt": "Extract the main title and description"
}'

# View API documentation
open http://localhost:8000/docs
```

## 📋 Core Features

### ✅ **Real Web Scraping**
- **Static HTML parsing** with BeautifulSoup
- **Content extraction** with html2text
- **Metadata extraction** (status codes, content types, links)
- **Error handling** for network issues and invalid URLs

### ✅ **Structured Data Extraction**
- **Schema-based extraction** with regex patterns
- **Automatic detection** of emails, phones, prices, dates
- **Custom field extraction** based on descriptions
- **Flexible data structures** for any use case

### ✅ **AI Enhancement (Optional)**
- **OpenAI integration** for intelligent extraction
- **Fallback to basic extraction** when AI unavailable
- **Configurable models** and parameters
- **Cost-effective** usage patterns

### ✅ **Production Features**
- **Asynchronous processing** with task queues
- **RESTful API** with comprehensive endpoints
- **Error handling** and retry logic
- **Scalable architecture** for high-volume usage

## 🔧 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scraping/execute` | Start scraping job |
| GET | `/api/scraping/status/{task_id}` | Check job status |
| GET | `/api/scraping/results/{task_id}` | Get job results |
| POST | `/api/scraping/search` | Search for URLs |
| POST | `/api/scraping/validate-url` | Validate URL accessibility |

### Request/Response Formats

#### Execute Scraping
```json
// Request
{
  "urls": ["https://example.com"],
  "prompt": "Extract the main title and description",
  "schema": {
    "title": {"description": "Page title"},
    "content": {"description": "Main content"}
  }
}

// Response
{
  "task_id": "uuid-here",
  "status": "pending",
  "message": "Scraping task started"
}
```

#### Results
```json
[
  {
    "url": "https://example.com/",
    "success": true,
    "data": {
      "url": "https://example.com/",
      "title": "Example Domain",
      "content": "Page content here...",
      "metadata": {
        "status_code": 200,
        "content_type": "text/html",
        "content_length": 513,
        "link_count": 1,
        "external_links": []
      },
      "scraped_at": 1234567890.123,
      "status": "success",
      "title": "# Example Domain",
      "content": "This domain is for use in documentation..."
    },
    "error": null
  }
]
```

## 💡 Usage Examples

### Example 1: E-commerce Scraping

```bash
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://example-store.com/product/123"],
  "prompt": "Extract product information",
  "schema": {
    "product_name": {"description": "Product name"},
    "price": {"description": "Product price"},
    "availability": {"description": "Stock status"},
    "description": {"description": "Product description"}
  }
}'
```

### Example 2: News Article Extraction

```bash
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://news-site.com/article/456"],
  "prompt": "Extract article details",
  "schema": {
    "headline": {"description": "Article title"},
    "author": {"description": "Article author"},
    "publish_date": {"description": "Publication date"},
    "content": {"description": "Article content"}
  }
}'
```

### Example 3: Contact Information

```bash
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://company.com/contact"],
  "prompt": "Extract contact details",
  "schema": {
    "company_name": {"description": "Company name"},
    "email": {"description": "Contact email"},
    "phone": {"description": "Phone number"},
    "address": {"description": "Physical address"}
  }
}'
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
# OpenAI Configuration (Optional)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Redis Configuration (for task storage)
REDIS_URL=redis://localhost:6379

# Application Settings
USE_LOCAL_SCRAPING=true
SCRAPEGRAPH_API_KEY=not-used-with-local-scraping
```

### Docker Deployment

```bash
# Build and run with Docker
docker-compose up -d

# Or build manually
docker build -t scrapegraph-enhanced -f backend/Dockerfile backend/
docker run -p 8000:8000 scrapegraph-enhanced
```

### Docker Compose

```yaml
version: '3.8'
services:
  scrapegraph:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## 📊 Advanced Features

### Structured Data Patterns

The system automatically extracts common data types:

- **Emails**: `user@domain.com` patterns
- **Phones**: `(555) 123-4567`, `555-123-4567`, `+1 555 123 4567`
- **Prices**: `$19.99`, `€25.50`, "19.99 USD"
- **Dates**: `MM/DD/YYYY`, `YYYY-MM-DD`, `Month DD, YYYY`

### Custom Field Extraction

Define custom fields with descriptive names:

```json
{
  "product_sku": {"description": "Product SKU or model number"},
  "release_date": {"description": "Product release date"},
  "warranty_info": {"description": "Warranty period or information"}
}
```

### Batch Processing

Process multiple URLs efficiently:

```json
{
  "urls": [
    "https://site1.com/page1",
    "https://site2.com/page2",
    "https://site3.com/page3"
  ],
  "prompt": "Extract product information",
  "schema": {
    "title": {"description": "Product title"},
    "price": {"description": "Product price"}
  }
}
```

## 🔒 Security & Best Practices

### Rate Limiting
- Be respectful when scraping external sites
- Implement rate limiting for production use
- Monitor your scraping frequency

### Error Handling
- Always check the `success` field in results
- Handle network timeouts gracefully
- Validate URLs before scraping

### Data Quality
- Use specific, targeted prompts
- Test with sample URLs first
- Validate extracted data

## 🚀 Performance Optimization

### Tips for Better Performance

1. **Batch URLs**: Process multiple URLs in one request
2. **Specific Schemas**: Use targeted field descriptions
3. **Validate First**: Check URL accessibility
4. **Monitor Tasks**: Use status endpoints for long jobs
5. **Handle Errors**: Check success status in results

### Scaling Considerations

- **Redis**: Use Redis for task storage in production
- **Load Balancing**: Deploy multiple instances behind a load balancer
- **Monitoring**: Add logging and monitoring
- **Caching**: Implement caching for frequently accessed URLs

## 🔄 Migration from ScrapeGraphAI

### Key Differences

| Feature | ScrapeGraphAI | ScrapeGraph Enhanced |
|---------|---------------|---------------------|
| **API Dependency** | External API | Local processing |
| **Data Privacy** | Data sent externally | Full data control |
| **Cost** | Pay-per-use | No recurring costs |
| **Reliability** | External dependencies | Self-contained |
| **Customization** | Limited | Fully customizable |
| **Performance** | Network latency | Local processing |

### Migration Steps

1. **Update endpoints**: Same API structure, local host
2. **Test existing code**: Compatible response formats
3. **Remove API keys**: No external API dependencies
4. **Update configuration**: Local environment variables
5. **Enhance schemas**: Better structured extraction

## 📞 Support & Troubleshooting

### Common Issues

**Server not starting**
```bash
# Check dependencies
pip install fastapi uvicorn httpx beautifulsoup4 html2text

# Check virtual environment
source venv/bin/activate
which python
```

**Scraping failures**
```bash
# Test URL accessibility
curl -I https://example.com

# Check server logs
# Look for error messages in console output
```

**Connection issues**
```bash
# Verify server is running
curl http://localhost:8000/docs

# Check port availability
netstat -tlnp | grep 8000
```

### Debug Mode

Start server with debug logging:

```bash
uvicorn app.main:app --reload --log-level debug
```

### Performance Monitoring

Monitor task performance:

```bash
# Check task status
curl http://localhost:8000/api/scraping/status/{task_id}

# View system resources
top, htop, or docker stats
```

## 🎯 Use Cases

### Perfect For

- **E-commerce monitoring**: Price tracking, product details
- **News aggregation**: Article extraction, content monitoring
- **Lead generation**: Contact information extraction
- **Market research**: Competitor analysis, data collection
- **Content aggregation**: Blog posts, tutorials, documentation

### Limitations

- **JavaScript rendering**: No JS execution (static HTML only)
- **Authentication**: No login/form support
- **Rate limiting**: No built-in rate limiting
- **File downloads**: No binary file handling

## 📈 Roadmap

### Planned Enhancements

- [ ] Real search API integration (DuckDuckGo, Google)
- [ ] JavaScript rendering with Playwright
- [ ] Advanced rate limiting and caching
- [ ] Authentication and session support
- [ ] File download capabilities
- [ ] Webhook notifications for completed jobs
- [ ] Advanced error handling and retry logic
- [ ] Performance monitoring and metrics

### Contributing

Welcome contributions for:
- Bug fixes and improvements
- New extraction patterns
- Performance optimizations
- Documentation enhancements
- Test coverage improvements

---

## 🎉 Summary

ScrapeGraph Enhanced provides a **powerful, reliable, and cost-effective** alternative to external scraping services. With **full data control**, **local processing**, and **comprehensive features**, it's the ideal solution for production web scraping needs.

**Get started now:**
1. `cd backend && source venv/bin/activate`
2. `uvicorn app.main:app --reload`
3. Visit `http://localhost:8000/docs`
4. Check out `SCRAPEGRAPH_USER_GUIDE.md` for detailed instructions

**Happy scraping!** 🚀