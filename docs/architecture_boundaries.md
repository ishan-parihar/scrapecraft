# Architecture Boundaries: AI Agents vs Backend Services

## Overview
This document defines the clear boundaries and responsibilities between the AI agent system and backend services in the Scrapecraft/OSINT-OS project. These boundaries ensure a maintainable, scalable architecture with well-defined interfaces.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Agent Layer                           │
├─────────────────────────────────────────────────────────────────┤
│ • Planning Agents (define investigation strategy)              │
│ • Collection Agents (gather data through tools)                │
│ • Analysis Agents (analyze collected data)                     │
│ • Synthesis Agents (create reports and summaries)              │
│ • LangChain Tools (interface to backend services)              │
│ • State Management (track investigation progress)              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ (API calls via LangChain tools)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend Services Layer                     │
├─────────────────────────────────────────────────────────────────┤
│ • FastAPI Web Server (API endpoints for scraping operations)   │
│ • Enhanced Scraping Service (scraping logic)                   │
│ • Task Management (async task handling)                        │
│ • Result Storage & Retrieval (scraping results)                │
│ • API Authentication & Rate Limiting                           │
└─────────────────────────────────────────────────────────────────┘
```

## Responsibility Matrix

### AI Agent Layer Responsibilities

| Component | Responsibilities |
|-----------|------------------|
| **Planning Agents** | • Define investigation strategy and objectives<br>• Determine what data needs to be collected<br>• Plan collection phases and priorities<br>• Adapt strategy based on findings |
| **Collection Agents** | • Use LangChain tools to execute data collection tasks<br>• Handle tool selection based on collection needs<br>• Process and validate data received from tools<br>• Retry failed collection attempts when appropriate |
| **Analysis Agents** | • Analyze collected data for patterns and insights<br>• Cross-reference information from multiple sources<br>• Identify data quality issues and inconsistencies<br>• Generate analysis summaries |
| **LangChain Tools** | • Provide interface between agents and backend services<br>• Handle input validation and schema definition<br>• Format responses for agent consumption<br>• Handle error propagation and reporting |
| **State Management** | • Track investigation progress and phases<br>• Store collected data and analysis results<br>• Maintain context between agent interactions<br>• Provide checkpoint/recovery capabilities |

### Backend Services Responsibilities

| Component | Responsibilities |
|-----------|------------------|
| **API Endpoints** | • Validate incoming requests<br>• Authenticate and authorize requests<br>• Initiate scraping tasks<br>• Provide task status updates<br>• Return results in standardized format |
| **Enhanced Scraping Service** | • Execute actual web scraping operations<br>• Handle HTTP requests and responses<br>• Parse and extract data from web content<br>• Handle different website structures and formats<br>• Manage anti-bot detection circumvention |
| **Task Management** | • Queue and manage long-running scraping tasks<br>• Handle concurrent scraping operations<br>• Monitor task status and progress<br>• Provide task completion notifications |
| **Result Storage** | • Store temporary and permanent scraping results<br>• Provide efficient retrieval of results<br>• Handle data format conversion as needed<br>• Manage data lifecycle and cleanup |

## Clear Interface Specifications

### 1. AI Agent → Backend Service Interface

**Primary Interface**: LangChain Tools in `ai_agent/src/utils/tools/langchain_tools.py`

**Methods**:
- `backend_smart_scraper(website_url: str, user_prompt: str)`: Extract structured data from a single URL based on natural language prompt
- `backend_smart_crawler(website_url: str, user_prompt: str, max_depth: int, max_pages: int)`: Crawl a website to extract data from multiple pages
- `backend_search_scraper(search_query: str, max_results: int)`: Search for relevant websites and scrape them
- `backend_markdownify(website_url: str)`: Convert web page content to markdown format
- `backend_validate_urls(urls: List[str])`: Validate a list of URLs for accessibility

**Data Contract**:
- Input: Structured parameters validated by Pydantic schemas
- Output: Standardized response format with `success`, `data`, `error`, and `metadata` fields
- Error handling: All errors returned in standard format, no exceptions passed to agents

### 2. Backend Service Internal Interface

**Primary Interface**: API endpoints in `backend/app/api/scraping.py`

**Methods**:
- `POST /api/scraping/execute`: Initiate a scraping task with URLs, prompt, and schema
- `GET /api/scraping/status/{task_id}`: Get status of a running task
- `GET /api/scraping/results/{task_id}`: Get results of a completed task
- `POST /api/scraping/search`: Search for URLs relevant to a query
- `POST /api/scraping/validate-url`: Validate a URL for scraping

**Data Contract**:
- Input: JSON payloads with validation
- Output: Standardized API response format
- Async handling: Long-running tasks return task IDs for polling

## Data Flow Patterns

### 1. Synchronous Data Flow (Quick Operations)
```
AI Agent → LangChain Tool → Direct API Call → Backend Response → AI Agent
```

### 2. Asynchronous Data Flow (Long-Running Operations)
```
AI Agent → LangChain Tool → Initiate Task → Task ID → Poll Status → Get Results → AI Agent
```

## Error Handling Boundaries

### AI Agent Layer Error Handling
- Handles tool selection errors
- Manages agent state when tools fail
- Implements retry logic for failed tools
- Reports errors to planning agents for strategy adjustment

### Backend Service Error Handling
- Validates input parameters
- Handles network and scraping errors
- Manages resource constraints
- Provides meaningful error messages to tools

**Boundary Rule**: Backend services should never allow exceptions to propagate to the AI agent layer; all errors must be caught and converted to the standardized response format.

## Performance Considerations

### AI Agent Layer
- Should not perform heavy computation
- Focus on decision-making and orchestration
- Use caching for repeated operations when appropriate

### Backend Service Layer
- Handle all computational heavy lifting
- Implement efficient scraping algorithms
- Manage resource usage and rate limiting
- Optimize for concurrent operations

## Integration Points Summary

The primary integration point between AI agents and backend services is through the **LangChain tools interface**, which provides:

1. **Abstraction**: AI agents don't need to know backend implementation details
2. **Standardization**: Consistent interface regardless of backend changes
3. **Validation**: Input validation at the boundary
4. **Error Containment**: Backend errors don't crash AI agents
5. **Observability**: Tool usage can be monitored and logged

This architecture ensures that AI agents focus on intelligence and decision-making while backend services handle operational concerns like scraping, data processing, and resource management.