# Integration Plan: AI Agent Workflow with Backend Scraping Services

## Overview

This document outlines the integration plan between the AI agent system and the backend scraping services to create a unified OSINT investigation platform. The goal is to leverage the comprehensive investigation capabilities of the AI agent system while utilizing the robust scraping infrastructure provided by the backend services.

## Current System Architecture

### AI Agent System
- **Location**: `/ai_agent/`
- **Main Components**:
  - LangGraph-based workflow orchestrator (`ai_agent/src/workflow/graph.py`)
  - Specialized OSINT agents for planning, collection, analysis, and synthesis
  - Integration with ScrapeGraphAI tools for data collection
  - Comprehensive investigation lifecycle management

### Backend Scraping Services
- **Location**: `/backend/`
- **Main Components**:
  - Enhanced scraping service (`backend/app/services/enhanced_scraping_service.py`)
  - API endpoints for scraping operations (`backend/app/api/scraping.py`)
  - Task management and storage systems
  - Workflow management for agent coordination

## Integration Strategy

### 1. Direct API Integration
The AI agents will communicate with backend scraping services through REST API calls to maintain separation of concerns while enabling seamless data flow.

### 2. Tool Integration
Enhance the existing ScrapeGraphAI integration tools to use backend scraping services as the primary data source, with fallback to direct scraping when needed.

### 3. Unified State Management
Synchronize state between AI agent investigations and backend scraping tasks for consistent tracking and reporting.

## Detailed Integration Plan

### Phase 1: API Client Development
**Objective**: Create a unified client to interface with backend scraping services

```python
# Create new file: ai_agent/src/utils/clients/backend_scraping_client.py

import asyncio
from typing import List, Dict, Any, Optional
import aiohttp
import logging

logger = logging.getLogger(__name__)

class BackendScrapingClient:
    """
    Client for interacting with backend scraping services API
    """
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def execute_scraping(self, urls: List[str], prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute scraping task via backend API"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/execute"
        payload = {
            "urls": urls,
            "prompt": prompt,
            "schema": schema
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Scraping execution failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except asyncio.TimeoutError:
            logger.error("Scraping execution timed out")
            return {"error": "Request timed out", "success": False}
        except Exception as e:
            logger.error(f"Scraping execution error: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get status of a scraping task"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/status/{task_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Get task status failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except Exception as e:
            logger.error(f"Get task status error: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def get_task_results(self, task_id: str) -> List[Dict[str, Any]]:
        """Get results of a completed scraping task"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/results/{task_id}"
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Get task results failed: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"Get task results error: {str(e)}")
            return []
    
    async def search_urls(self, query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """Search for URLs using backend service"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        url = f"{self.base_url}/api/scraping/search"
        payload = {"query": query, "max_results": max_results}
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("results", [])
                else:
                    error_text = await response.text()
                    logger.error(f"URL search failed: {response.status} - {error_text}")
                    return []
        except Exception as e:
            logger.error(f"URL search error: {str(e)}")
            return []
    
    async def validate_url(self, url: str) -> Dict[str, Any]:
        """Validate a URL using backend service"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use as async context manager.")
        
        validate_url = f"{self.base_url}/api/scraping/validate-url"
        payload = {"url": url}
        
        try:
            async with self.session.post(validate_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"URL validation failed: {response.status} - {error_text}")
                    return {"valid": False, "error": error_text}
        except Exception as e:
            logger.error(f"URL validation error: {str(e)}")
            return {"valid": False, "error": str(e)} 
```

### Phase 2: Enhanced Tool Integration
Modify the existing ScrapeGraphAI integration tools to use backend scraping services:

```python
# Update file: ai_agent/src/utils/tools/scrapegraph_integration.py

# Import the new client
from ai_agent.src.utils.clients.backend_scraping_client import BackendScrapingClient
import asyncio

# Add a class to handle the integration
class BackendScrapingAdapter:
    """
    Adapter to integrate backend scraping services with AI agent tools
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = BackendScrapingClient(base_url)
    
    async def scrape_urls(self, urls: List[str], prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Scrape URLs using backend services
        """
        async with self.client as client:
            # Start scraping task
            execution_result = await client.execute_scraping(urls, prompt, schema)
            
            if not execution_result.get("success"):
                return {
                    "success": False,
                    "error": execution_result.get("error", "Unknown error"),
                    "data": None
                }
            
            # Get the task ID
            task_id = execution_result.get("task_id")
            if not task_id:
                return {
                    "success": False,
                    "error": "No task ID returned from backend",
                    "data": None
                }
            
            # Poll for task completion
            max_retries = 20  # 20 * 3 seconds = 60 seconds max wait
            retry_count = 0
            
            while retry_count < max_retries:
                status_result = await client.get_task_status(task_id)
                
                if status_result.get("status") == "completed":
                    # Get results
                    results = await client.get_task_results(task_id)
                    return {
                        "success": True,
                        "task_id": task_id,
                        "results": results,
                        "data": results
                    }
                elif status_result.get("status") in ["failed", "error"]:
                    return {
                        "success": False,
                        "error": status_result.get("error", "Task failed"),
                        "data": None
                    }
                
                # Wait before next check
                await asyncio.sleep(3)
                retry_count += 1
            
            return {
                "success": False,
                "error": "Task timeout - still running after maximum wait time",
                "data": None
            }
    
    async def search_and_scrape(self, query: str, max_results: int = 5, scraping_prompt: str = "") -> Dict[str, Any]:
        """
        Search for URLs and then scrape them
        """
        async with self.client as client:
            # First search for URLs
            search_results = await client.search_urls(query, max_results)
            
            if not search_results:
                return {
                    "success": False,
                    "error": "No URLs found for query",
                    "data": None
                }
            
            # Extract URLs
            urls = [item.get("url") for item in search_results if item.get("url")]
            
            # Then scrape the URLs
            scraping_prompt = scraping_prompt or f"Extract all relevant information about: {query}"
            
            return await self.scrape_urls(urls, scraping_prompt)
```

### Phase 3: Agent Integration
Update collection agents to use the backend scraping services:

```python
# Example update for surface_web_collector.py

from ai_agent.src.utils.tools.scrapegraph_integration import BackendScrapingAdapter

class SurfaceWebCollectorAgent:
    """
    Updated SurfaceWebCollectorAgent that uses backend scraping services
    """
    
    def __init__(self, tools=None, scraping_base_url: str = "http://localhost:8000"):
        self.tools = tools or []
        self.scraping_adapter = BackendScrapingAdapter(base_url=scraping_base_url)
        self.logger = logging.getLogger(f"{__name__}.SurfaceWebCollectorAgent")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute surface web collection using backend scraping services
        """
        try:
            task_type = input_data.get("task_type", "search")
            
            if task_type == "search":
                queries = input_data.get("queries", [])
                engines = input_data.get("engines", ["google"])
                max_results = input_data.get("max_results", 5)
                
                # Use the scraping adapter to search and scrape
                results = []
                for query in queries:
                    search_and_scrape_result = await self.scraping_adapter.search_and_scrape(
                        query, max_results, f"Extract relevant information about: {query}"
                    )
                    
                    if search_and_scrape_result["success"]:
                        results.extend(search_and_scrape_result.get("results", []))
                    else:
                        self.logger.warning(f"Search and scrape failed for query '{query}': {search_and_scrape_result.get('error')}")
                
                return AgentResult(
                    success=True,
                    data={"results": results},
                    confidence=0.8,
                    metadata={"source": "backend_scraping_service"}
                )
            
            elif task_type == "scrape_urls":
                urls = input_data.get("urls", [])
                prompt = input_data.get("prompt", "Extract all relevant information")
                
                scraping_result = await self.scraping_adapter.scrape_urls(urls, prompt)
                
                if scraping_result["success"]:
                    return AgentResult(
                        success=True,
                        data={"results": scraping_result["results"]},
                        confidence=0.9,
                        metadata={"source": "backend_scraping_service"}
                    )
                else:
                    return AgentResult(
                        success=False,
                        error_message=scraping_result.get("error"),
                        data={},
                        confidence=0.0
                    )
            
            else:
                # Fallback to existing tools if task type is not supported
                # Implementation would depend on the specific fallback needs
                pass
                
        except Exception as e:
            self.logger.error(f"Surface web collection failed: {str(e)}")
            return AgentResult(
                success=False,
                error_message=str(e),
                data={},
                confidence=0.0
            )
```

### Phase 4: State Synchronization
Update the workflow state to track backend task IDs and integrate results:

```python
# In state.py, add fields for tracking backend tasks

class InvestigationState(TypedDict):
    # ... existing fields ...
    
    # New fields for backend scraping integration
    backend_scraping_tasks: List[Dict[str, Any]]  # Track running backend tasks
    backend_api_base_url: str  # Base URL for backend API
    backend_auth_token: Optional[str]  # Authentication token if needed
```

### Phase 5: Configuration Management
Create a unified configuration system that allows both systems to be configured from a single source:

```python
# Create new file: ai_agent/src/config/integration_config.py

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os

@dataclass
class IntegrationConfig:
    """
    Configuration for AI agent to backend scraping service integration
    """
    # Backend scraping service configuration
    backend_scraping_base_url: str = os.getenv("BACKEND_SCRAPING_URL", "http://localhost:8000")
    backend_api_key: Optional[str] = os.getenv("BACKEND_API_KEY")
    backend_timeout: int = int(os.getenv("BACKEND_TIMEOUT", "30"))
    
    # Feature flags
    use_backend_scraping: bool = os.getenv("USE_BACKEND_SCRAPING", "true").lower() == "true"
    fallback_to_local_scraping: bool = os.getenv("FALLBACK_TO_LOCAL", "true").lower() == "true"
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_BACKEND_TASKS", "5"))
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'IntegrationConfig':
        """Create config from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})
```

## Implementation Steps

### Step 1: Core Integration Components
1. Implement the `BackendScrapingClient` with full error handling and connection management
2. Create the `BackendScrapingAdapter` to provide a unified interface to agents
3. Add integration configuration management

### Step 2: Agent Updates
1. Update all collection agents (SurfaceWebCollectorAgent, SocialMediaCollectorAgent, etc.) to optionally use backend services
2. Maintain backward compatibility with existing local scraping tools
3. Add fallback mechanisms in case backend services are unavailable

### Step 3: Workflow Integration
1. Update the workflow graph to initialize and pass the backend scraping adapter to collection agents
2. Add state management for backend tasks
3. Implement proper error handling and recovery mechanisms

### Step 4: Testing and Validation
1. Create integration tests to validate the connection between AI agents and backend services
2. Test fallback mechanisms when backend services are unavailable
3. Validate data consistency between systems

## Benefits of Integration

1. **Enhanced Scalability**: Backend services can handle larger scraping tasks and distribute load
2. **Resource Optimization**: Centralize scraping infrastructure to avoid duplication
3. **Improved Reliability**: Backend services may have better error handling and recovery
4. **Unified Monitoring**: Monitor all scraping activities through backend service dashboards
5. **API Consistency**: Standardized API interface for all scraping operations

## Risks and Mitigation

1. **Network Dependency**: AI agents now depend on network connectivity to backend services
   - Mitigation: Implement robust fallback to local scraping when backend is unavailable

2. **Latency**: Network calls to backend services may introduce delays
   - Mitigation: Implement asynchronous calls with proper timeout handling

3. **Coupling**: Systems become more tightly coupled
   - Mitigation: Maintain clear API contracts and allow independent operation

## Next Steps

1. Implement the core integration components as outlined in Phase 1
2. Update collection agents to use the new integration (Phase 2)
3. Test the integration in a development environment
4. Refine error handling and fallback mechanisms
5. Document the integration for other developers