"""
Comprehensive Testing Framework for ScrapeCraft OSINT Platform

This module provides:
- Unit test utilities and fixtures
- Integration test helpers
- Performance testing tools
- Test database management
- Mock services for testing
- Coverage reporting
- CI/CD integration helpers
"""

import asyncio
import pytest
import pytest_asyncio
import logging
from typing import Dict, List, Optional, Any, Generator, AsyncGenerator
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os
import json
from datetime import datetime
import sqlite3
from pathlib import Path

# FastAPI testing
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Database testing
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.pool import StaticPool

# Redis testing
import redis
from fakeredis import FakeAsyncRedis

# Project imports
from app.main import app
from app.config import settings
from app.services.database import get_db
from app.models.base import Base

logger = logging.getLogger(__name__)

class TestConfig:
    """Test configuration settings."""
    
    # Database
    TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
    TEST_SYNC_DATABASE_URL = "sqlite:///:memory:"
    
    # Redis
    TEST_REDIS_URL = "redis://localhost:6379/1"  # Use test DB
    
    # LLM
    TEST_LLM_PROVIDER = "openrouter"
    TEST_LLM_MODEL = "meta-llama/llama-3.2-3b-instruct:free"
    
    # Security
    TEST_JWT_SECRET = "test-secret-key-for-testing-only"
    TEST_JWT_ALGORITHM = "HS256"
    
    # Timeouts
    TEST_TIMEOUT = 30.0
    
    # Performance
    LOAD_TEST_CONCURRENCY = 10
    LOAD_TEST_DURATION = 60  # seconds

class TestDatabase:
    """Test database management."""
    
    def __init__(self):
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
    
    async def setup(self):
        """Setup test database."""
        # Create async engine
        self.async_engine = create_async_engine(
            TestConfig.TEST_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        # Create sync engine for migrations
        self.engine = create_engine(
            TestConfig.TEST_SYNC_DATABASE_URL,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False
        )
        
        # Create session factories
        self.AsyncSessionLocal = sessionmaker(
            self.async_engine, class_=AsyncSession, expire_on_commit=False
        )
        self.SessionLocal = sessionmaker(
            self.engine, autocommit=False, autoflush=False
        )
        
        # Create tables
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def teardown(self):
        """Cleanup test database."""
        if self.async_engine:
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await self.async_engine.dispose()
        
        if self.engine:
            self.engine.dispose()
    
    def get_sync_session(self):
        """Get sync database session."""
        return self.SessionLocal()
    
    async def get_async_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get async database session."""
        async with self.AsyncSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

class TestRedis:
    """Test Redis management."""
    
    def __init__(self):
        self.redis_client = None
        self.fake_redis = None
    
    async def setup(self):
        """Setup test Redis."""
        try:
            # Try to use real Redis for integration tests
            self.redis_client = redis.from_url(TestConfig.TEST_REDIS_URL, db=1)
            self.redis_client.ping()
            logger.info("Using real Redis for testing")
        except Exception:
            # Fallback to fake Redis
            self.fake_redis = FakeAsyncRedis()
            logger.info("Using fake Redis for testing")
    
    async def teardown(self):
        """Cleanup test Redis."""
        if self.redis_client:
            try:
                self.redis_client.flushdb()  # Clear test database
                self.redis_client.close()
            except Exception:
                pass
        
        if self.fake_redis:
            await self.fake_redis.close()
    
    def get_client(self):
        """Get Redis client."""
        return self.redis_client or self.fake_redis

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

# Global test instances
test_db = TestDatabase()
test_redis = TestRedis()
mock_llm = MockLLMService()
mock_scraping = MockScrapingService()

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def setup_test_environment():
    """Setup test environment."""
    logger.info("Setting up test environment...")
    
    # Setup test database
    await test_db.setup()
    
    # Setup test Redis
    await test_redis.setup()
    
    # Configure test settings
    settings.DATABASE_URL = TestConfig.TEST_DATABASE_URL
    settings.REDIS_URL = TestConfig.TEST_REDIS_URL
    settings.JWT_SECRET_KEY = TestConfig.TEST_JWT_SECRET
    settings.JWT_ALGORITHM = TestConfig.TEST_JWT_ALGORITHM
    settings.LLM_PROVIDER = TestConfig.TEST_LLM_PROVIDER
    settings.OPENROUTER_MODEL = TestConfig.TEST_LLM_MODEL
    
    yield {
        "database": test_db,
        "redis": test_redis,
        "mock_llm": mock_llm,
        "mock_scraping": mock_scraping
    }
    
    # Cleanup
    logger.info("Cleaning up test environment...")
    await test_db.teardown()
    await test_redis.teardown()

@pytest.fixture
def test_client(setup_test_environment):
    """Create FastAPI test client."""
    def override_get_db():
        try:
            db = test_db.get_sync_session()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def async_test_client(setup_test_environment):
    """Create async test client."""
    async def override_get_async_db():
        async for session in test_db.get_async_session():
            yield session
    
    app.dependency_overrides[get_db] = override_get_async_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_llm_service():
    """Mock LLM service fixture."""
    return mock_llm

@pytest.fixture
def mock_scraping_service():
    """Mock scraping service fixture."""
    return mock_scraping

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123",
        "role": "analyst"
    }

@pytest.fixture
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

@pytest.fixture
def sample_osint_data():
    """Sample OSINT data for testing."""
    return {
        "target": "example.com",
        "investigation_id": "test-investigation-123",
        "data_sources": ["dns", "whois", "social_media"],
        "collection_methods": ["passive", "active"]
    }

class PerformanceTestHelper:
    """Helper for performance testing."""
    
    def __init__(self):
        self.results = []
    
    async def run_concurrent_requests(
        self,
        func,
        args_list: List[tuple],
        concurrency: int = TestConfig.LOAD_TEST_CONCURRENCY
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

@pytest.fixture
def performance_helper():
    """Performance testing helper fixture."""
    return PerformanceTestHelper()

class IntegrationTestHelper:
    """Helper for integration testing."""
    
    @staticmethod
    async def create_test_user(client, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a test user via API."""
        response = client.post("/api/auth/register", json=user_data)
        assert response.status_code == 201
        return response.json()
    
    @staticmethod
    async def login_test_user(client, username: str, password: str) -> Dict[str, Any]:
        """Login test user and get tokens."""
        login_data = {"username": username, "password": password}
        response = client.post("/api/auth/login", data=login_data)
        assert response.status_code == 200
        return response.json()
    
    @staticmethod
    async def create_test_investigation(
        client,
        investigation_data: Dict[str, Any],
        access_token: str
    ) -> Dict[str, Any]:
        """Create a test investigation via API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/investigations",
            json=investigation_data,
            headers=headers
        )
        assert response.status_code == 201
        return response.json()
    
    @staticmethod
    async def start_osint_collection(
        client,
        osint_data: Dict[str, Any],
        access_token: str
    ) -> Dict[str, Any]:
        """Start OSINT collection via API."""
        headers = {"Authorization": f"Bearer {access_token}"}
        response = client.post(
            "/api/osint/collect",
            json=osint_data,
            headers=headers
        )
        assert response.status_code == 200
        return response.json()

@pytest.fixture
def integration_helper():
    """Integration testing helper fixture."""
    return IntegrationTestHelper()

# Custom pytest markers
pytest_plugins = []

def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as authentication related"
    )
    config.addinivalue_line(
        "markers", "osint: mark test as OSINT related"
    )

# Coverage configuration
def pytest_collection_modifyitems(config, items):
    """Modify test collection for coverage."""
    for item in items:
        # Add markers based on test location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)

# Async test configuration
@pytest_asyncio.fixture
async def async_session():
    """Get async database session for tests."""
    async for session in test_db.get_async_session():
        yield session

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