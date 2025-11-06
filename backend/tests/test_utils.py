"""
Simplified Testing Framework for ScrapeCraft OSINT Platform

This module provides essential testing utilities without complex dependencies.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Generator
from unittest.mock import Mock, AsyncMock
import tempfile
import os
from datetime import datetime

# FastAPI testing
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Project imports
from app.main import app

logger = logging.getLogger(__name__)

class MockLLMService:
    """Mock LLM service for testing."""
    
    def __init__(self):
        self.responses = {}
        self.call_count = 0
        self.last_request = None
        self.response_delay = 0.1
    
    def set_response(self, prompt: str, response: str):
        """Set a mock response for a prompt."""
        self.responses[prompt] = response
    
    def set_default_response(self, response: str):
        """Set default response for any prompt."""
        self.responses["_default"] = response
    
    async def ainvoke(self, messages: List[Any]) -> Mock:
        """Mock async invoke."""
        await asyncio.sleep(self.response_delay)
        
        self.call_count += 1
        if isinstance(messages, list) and messages:
            content = messages[0].content if hasattr(messages[0], 'content') else str(messages[0])
        else:
            content = str(messages)
        
        self.last_request = content
        
        response_text = self.responses.get(content, self.responses.get("_default", "Mock response"))
        
        mock_response = Mock()
        mock_response.content = response_text
        return mock_response

class MockScrapingService:
    """Mock scraping service for testing."""
    
    def __init__(self):
        self.scraped_data = {}
        self.call_count = 0
    
    def set_scraped_data(self, url: str, data: Dict[str, Any]):
        """Set mock scraped data for a URL."""
        self.scraped_data[url] = data
    
    async def scrape_url(self, url: str, **kwargs) -> Dict[str, Any]:
        """Mock scrape URL."""
        self.call_count += 1
        await asyncio.sleep(0.1)  # Simulate network delay
        
        return self.scraped_data.get(url, {
            "url": url,
            "title": "Mock Title",
            "content": "Mock content for testing",
            "status_code": 200,
            "scraped_at": datetime.utcnow().isoformat()
        })

class PerformanceTestHelper:
    """Helper for performance testing."""
    
    def __init__(self):
        self.results = []
    
    async def run_concurrent_requests(
        self,
        func,
        args_list: List[tuple],
        concurrency: int = 10
    ) -> Dict[str, Any]:
        """Run requests concurrently and measure performance."""
        start_time = datetime.utcnow()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(concurrency)
        
        async def limited_request(args):
            async with semaphore:
                request_start = datetime.utcnow()
                try:
                    result = await func(*args)
                    request_end = datetime.utcnow()
                    return {
                        "success": True,
                        "result": result,
                        "duration": (request_end - request_start).total_seconds(),
                        "error": None
                    }
                except Exception as e:
                    request_end = datetime.utcnow()
                    return {
                        "success": False,
                        "result": None,
                        "duration": (request_end - request_start).total_seconds(),
                        "error": str(e)
                    }
        
        # Run all requests
        tasks = [limited_request(args) for args in args_list]
        results = await asyncio.gather(*tasks)
        
        end_time = datetime.utcnow()
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate metrics
        successful_requests = [r for r in results if r["success"]]
        failed_requests = [r for r in results if not r["success"]]
        
        response_times = [r["duration"] for r in successful_requests]
        
        metrics = {
            "total_requests": len(results),
            "successful_requests": len(successful_requests),
            "failed_requests": len(failed_requests),
            "success_rate": len(successful_requests) / len(results) if results else 0,
            "total_duration": total_duration,
            "requests_per_second": len(results) / total_duration if total_duration > 0 else 0,
            "avg_response_time": sum(response_times) / len(response_times) if response_times else 0,
            "min_response_time": min(response_times) if response_times else 0,
            "max_response_time": max(response_times) if response_times else 0,
            "p95_response_time": self._percentile(response_times, 95) if response_times else 0,
            "p99_response_time": self._percentile(response_times, 99) if response_times else 0,
            "errors": [r["error"] for r in failed_requests]
        }
        
        self.results.append(metrics)
        return metrics
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all performance tests."""
        if not self.results:
            return {}
        
        return {
            "total_tests": len(self.results),
            "avg_success_rate": sum(r["success_rate"] for r in self.results) / len(self.results),
            "avg_rps": sum(r["requests_per_second"] for r in self.results) / len(self.results),
            "avg_response_time": sum(r["avg_response_time"] for r in self.results) / len(self.results),
            "tests": self.results
        }

# Test fixtures
def test_client():
    """Create FastAPI test client."""
    return TestClient(app)

async def async_test_client():
    """Create async test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

def mock_llm_service():
    """Mock LLM service fixture."""
    return MockLLMService()

def mock_scraping_service():
    """Mock scraping service fixture."""
    return MockScrapingService()

def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "analyst"
    }

def sample_investigation_data():
    """Sample investigation data for testing."""
    return {
        "title": "Test Investigation",
        "description": "A test investigation for unit testing",
        "target": "test.target.com",
        "objective": "Test objective",
        "priority": "medium",
        "status": "planning"
    }

def sample_osint_data():
    """Sample OSINT data for testing."""
    return {
        "target": "example.com",
        "investigation_id": "test-investigation-123",
        "data_sources": ["dns", "whois", "social_media"],
        "collection_methods": ["passive", "active"]
    }

def performance_helper():
    """Performance testing helper fixture."""
    return PerformanceTestHelper()

# Test utilities
def create_test_headers(access_token: str) -> Dict[str, str]:
    """Create headers with authorization token."""
    return {"Authorization": f"Bearer {access_token}"}

def assert_valid_response(
    response,
    expected_status: int = 200,
    expected_fields: Optional[List[str]] = None
):
    """Assert response is valid and contains expected fields."""
    assert response.status_code == expected_status
    
    if expected_fields:
        response_data = response.json()
        for field in expected_fields:
            assert field in response_data, f"Missing field: {field}"

def assert_error_response(
    response,
    expected_status: int = 400,
    expected_error: Optional[str] = None
):
    """Assert error response is valid."""
    assert response.status_code == expected_status
    
    if expected_error:
        response_data = response.json()
        assert "detail" in response_data
        assert expected_error.lower() in response_data["detail"].lower()

# Global instances
mock_llm = MockLLMService()
mock_scraping = MockScrapingService()