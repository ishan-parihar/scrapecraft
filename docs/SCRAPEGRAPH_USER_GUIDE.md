# ScrapeGraph Enhanced - User Guide

## Overview

ScrapeGraph Enhanced is a powerful, locally-hosted web scraping service that provides the same functionality as ScrapeGraphAI but without external API dependencies. This guide will help you effectively use the enhanced scraping capabilities.

## 🚀 Quick Start

### 1. Setup and Installation

```bash
# Navigate to the backend directory
cd backend/

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi uvicorn httpx beautifulsoup4 html2text openai pydantic redis

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Basic Usage

The service provides REST API endpoints for web scraping. Here's how to use it:

```bash
# Start a scraping job
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://example.com"],
  "prompt": "Extract the main title and description"
}'

# Check status (replace TASK_ID with returned task_id)
curl -X GET 'http://localhost:8000/api/scraping/status/TASK_ID'

# Get results (replace TASK_ID with returned task_id)
curl -X GET 'http://localhost:8000/api/scraping/results/TASK_ID'
```

## 📋 API Endpoints

### 1. Execute Scraping

**Endpoint:** `POST /api/scraping/execute`

Start an asynchronous scraping job.

#### Request Body
```json
{
  "urls": ["https://example.com", "https://python.org"],
  "prompt": "Extract the main title, content, and any contact information",
  "schema": {
    "website_title": {"description": "The main title of the website"},
    "main_content": {"description": "The main content or description"},
    "contact_email": {"description": "Any email address found on the page"},
    "phone_number": {"description": "Any phone number found on the page"}
  }
}
```

#### Response
```json
{
  "task_id": "uuid-here",
  "status": "pending",
  "message": "Scraping task started"
}
```

### 2. Check Status

**Endpoint:** `GET /api/scraping/status/{task_id}`

Check the status of a scraping job.

#### Response
```json
{
  "task_id": "uuid-here",
  "status": "completed",
  "error": null
}
```

Status values: `pending`, `running`, `completed`, `failed`

### 3. Get Results

**Endpoint:** `GET /api/scraping/results/{task_id}`

Retrieve the results of a completed scraping job.

#### Response
```json
[
  {
    "url": "https://example.com/",
    "success": true,
    "data": {
      "url": "https://example.com/",
      "title": "Example Domain",
      "content": "# Example Domain\nThis domain is for use in documentation...",
      "metadata": {
        "status_code": 200,
        "content_type": "text/html",
        "content_length": 513,
        "link_count": 1,
        "external_links": []
      },
      "scraped_at": 10904.632,
      "status": "success",
      "website_title": "# Example Domain",
      "main_content": "This domain is for use in documentation examples",
      "contact_email": null,
      "phone_number": null
    },
    "error": null
  }
]
```

### 4. Search URLs

**Endpoint:** `POST /api/scraping/search`

Find URLs related to a search query.

#### Request
```
POST /api/scraping/search?query=python programming&max_results=5
```

#### Response
```json
{
  "query": "python programming",
  "max_results": 5,
  "results": [
    {
      "url": "https://duckduckgo.com/?q=python+programming",
      "description": "Search results for: python programming"
    },
    {
      "url": "https://www.google.com/search?q=python+programming",
      "description": "Google search for: python programming"
    }
  ],
  "count": 2
}
```

### 5. Validate URL

**Endpoint:** `POST /api/scraping/validate-url`

Check if a URL is accessible.

#### Request
```
POST /api/scraping/validate-url?url=https://python.org
```

#### Response
```json
{
  "url": "https://python.org/",
  "valid": true,
  "status_code": 200,
  "content_type": "text/html; charset=utf-8"
}
```

## 🔧 Advanced Features

### Structured Data Extraction

Use schemas to extract specific information from web pages:

```json
{
  "urls": ["https://example-ecommerce.com"],
  "prompt": "Extract product information",
  "schema": {
    "product_name": {"description": "The name of the product"},
    "price": {"description": "The price of the product"},
    "availability": {"description": "Whether the product is in stock"},
    "contact_email": {"description": "Customer service email"},
    "phone": {"description": "Contact phone number"}
  }
}
```

The system automatically detects and extracts:
- **Email addresses** using regex patterns
- **Phone numbers** in various formats
- **Prices** with currency symbols
- **Dates** in common formats
- **Custom fields** based on description matching

### AI-Enhanced Extraction (Optional)

Configure OpenAI for intelligent content extraction:

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

2. The system will automatically use AI to enhance extraction when available.

### Batch Processing

Process multiple URLs simultaneously:

```json
{
  "urls": [
    "https://example.com",
    "https://python.org",
    "https://httpbin.org/html"
  ],
  "prompt": "Extract the main content and metadata",
  "schema": {
    "title": {"description": "Page title"},
    "summary": {"description": "Brief summary of content"}
  }
}
```

## 💡 Usage Examples

### Example 1: E-commerce Product Scraping

```bash
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://example-store.com/product/123"],
  "prompt": "Extract product details including price, availability, and description",
  "schema": {
    "product_name": {"description": "Product name"},
    "price": {"description": "Product price"},
    "in_stock": {"description": "Product availability"},
    "description": {"description": "Product description"},
    "contact_email": {"description": "Support email"}
  }
}'
```

### Example 2: News Article Extraction

```bash
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://example-news.com/article/456"],
  "prompt": "Extract article title, content, and publication date",
  "schema": {
    "article_title": {"description": "Article headline"},
    "author": {"description": "Article author"},
    "publish_date": {"description": "Publication date"},
    "content": {"description": "Main article content"}
  }
}'
```

### Example 3: Contact Information Extraction

```bash
curl -X POST 'http://localhost:8000/api/scraping/execute' \
-H 'Content-Type: application/json' \
-d '{
  "urls": ["https://example-company.com/contact"],
  "prompt": "Extract all contact information",
  "schema": {
    "company_name": {"description": "Company name"},
    "email": {"description": "Contact email address"},
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
# Build the image
docker build -t scrapegraph-enhanced .

# Run the container
docker run -p 8000:8000 scrapegraph-enhanced
```

Or use docker-compose:

```yaml
version: '3.8'
services:
  scrapegraph:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

## 📊 Response Format

### Success Response

```json
{
  "url": "https://example.com",
  "success": true,
  "data": {
    "url": "https://example.com",
    "title": "Example Domain",
    "content": "Page content here...",
    "metadata": {
      "status_code": 200,
      "content_type": "text/html",
      "content_length": 513,
      "link_count": 10,
      "external_links": ["https://external-site.com"]
    },
    "scraped_at": 1234567890.123,
    "status": "success",
    // Custom schema fields
    "custom_field": "Extracted value"
  },
  "error": null
}
```

### Error Response

```json
{
  "url": "https://example.com",
  "success": false,
  "data": null,
  "error": "Connection timeout"
}
```

## 🔍 Error Handling

The system handles various error scenarios:

- **Network timeouts**: Returns timeout errors
- **Invalid URLs**: Validates URL format
- **DNS failures**: Handles domain resolution errors
- **HTTP errors**: Returns status code information
- **Content parsing**: Gracefully handles malformed HTML

## 📈 Performance Tips

1. **Batch URLs**: Process multiple URLs in a single request
2. **Specific schemas**: Use targeted field descriptions for better extraction
3. **Validate first**: Use the validate-url endpoint before scraping
4. **Monitor tasks**: Check task status before retrieving results
5. **Handle errors**: Always check the `success` field in results

## 🚨 Limitations

- **Search functionality**: Currently returns mock results (can be extended)
- **AI enhancement**: Requires OpenAI API key for advanced extraction
- **Rate limiting**: No built-in rate limiting (add for production)
- **JavaScript rendering**: Doesn't execute JavaScript (static HTML only)

## 🔄 Migration from ScrapeGraphAI

If you're migrating from the original ScrapeGraphAI API:

1. **Same endpoint structure**: Compatible API design
2. **Enhanced response format**: More detailed metadata included
3. **Local processing**: No external API dependencies
4. **Better error handling**: More informative error messages
5. **Schema support**: Enhanced structured data extraction

## 📞 Support

For issues and questions:

1. Check the server logs for detailed error information
2. Verify URL accessibility using the validate endpoint
3. Test with simple URLs first (example.com, python.org)
4. Ensure all dependencies are properly installed

## 🎯 Best Practices

1. **Start simple**: Test with basic extraction first
2. **Use specific prompts**: Clear, targeted prompts work better
3. **Validate URLs**: Check accessibility before bulk scraping
4. **Monitor tasks**: Use the status endpoint for long-running jobs
5. **Handle errors**: Always check success status in results
6. **Rate limit**: Be respectful when scraping external sites

---

**ScrapeGraph Enhanced** provides a powerful, reliable alternative to external scraping services with full control over your data and processing.