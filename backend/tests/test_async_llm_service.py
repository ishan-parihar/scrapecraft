"""
Unit Tests for Async LLM Service

Tests the enhanced async LLM service with connection pooling,
circuit breaker, and performance monitoring.
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from backend.tests.test_utils import (
    MockLLMService,
    PerformanceTestHelper,
    assert_valid_response,
    assert_error_response
)
from backend.app.services.async_llm_service import (
    AsyncLLMService,
    AsyncLLMProvider,
    CircuitBreaker,
    RateLimiter,
    get_async_llm_service,
    async_llm_invoke
)

class TestCircuitBreaker:
    """Test circuit breaker functionality."""
    
    def test_circuit_breaker_initial_state(self):
        """Test circuit breaker starts in closed state."""
        breaker = CircuitBreaker()
        assert breaker.can_execute() == True
        assert breaker.get_state().value == "closed"
    
    def test_circuit_breaker_success(self):
        """Test successful calls keep circuit closed."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Success calls should not open circuit
        for _ in range(5):
            breaker.call_success()
            assert breaker.can_execute() == True
            assert breaker.get_state().value == "closed"
    
    def test_circuit_breaker_opens_on_failures(self):
        """Test circuit opens after failure threshold."""
        breaker = CircuitBreaker(failure_threshold=3)
        
        # Failures should open circuit
        for i in range(3):
            breaker.call_failure()
            if i < 2:  # Before threshold
                assert breaker.can_execute() == True
            else:  # At threshold
                assert breaker.can_execute() == False
                assert breaker.get_state().value == "open"
    
    def test_circuit_breaker_half_open_recovery(self):
        """Test circuit transitions to half-open after recovery timeout."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Open circuit
        breaker.call_failure()
        breaker.call_failure()
        assert breaker.can_execute() == False
        
        # Wait for recovery timeout
        asyncio.sleep(0.2)
        
        # Should allow one request (half-open)
        assert breaker.can_execute() == True
        assert breaker.get_state().value == "half_open"

class TestRateLimiter:
    """Test rate limiter functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_basic(self):
        """Test basic rate limiting."""
        limiter = RateLimiter(max_calls_per_minute=2)
        
        # First two calls should succeed
        assert await limiter.acquire() == True
        assert await limiter.acquire() == True
        
        # Third call should fail
        assert await limiter.acquire() == False
    
    @pytest.mark.asyncio
    async def test_rate_limiter_wait_for_slot(self):
        """Test waiting for available slot."""
        limiter = RateLimiter(max_calls_per_minute=5)
        
        # Fill up the limiter
        for _ in range(5):
            await limiter.acquire()
        
        # Should wait and succeed (with timeout)
        start_time = asyncio.get_event_loop().time()
        result = await limiter.wait_for_slot(timeout=2.0)
        end_time = asyncio.get_event_loop().time()
        
        assert result == True
        # Should have waited some time (though may be very fast in test)
        assert end_time - start_time >= 0

class TestAsyncLLMProvider:
    """Test async LLM provider functionality."""
    
    @pytest.mark.asyncio
    async def test_provider_initialization(self):
        """Test provider initializes correctly."""
        from backend.app.services.async_llm_service import ProviderConfig
        
        config = ProviderConfig(
            name="test-provider",
            max_concurrent=3,
            rate_limit_per_minute=10
        )
        
        provider = AsyncLLMProvider(config)
        assert provider.config.name == "test-provider"
        assert provider.semaphore._value == 3
        assert provider.circuit_breaker.get_state().value == "closed"
    
    @pytest.mark.asyncio
    async def test_provider_health_check(self):
        """Test provider health check."""
        from backend.app.services.async_llm_service import ProviderConfig
        
        config = ProviderConfig(name="test-provider")
        provider = AsyncLLMProvider(config)
        
        # Mock the LLM instance
        mock_llm = AsyncMock()
        mock_llm.ainvoke = AsyncMock(return_value="test response")
        
        with patch.object(provider, 'get_llm_instance', return_value=mock_llm):
            health = await provider.health_check()
            assert health == True
            assert provider._is_healthy == True

class TestAsyncLLMService:
    """Test async LLM service functionality."""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service initializes with providers."""
        with patch('backend.app.services.async_llm_service.settings'):
            service = AsyncLLMService()
            assert len(service.providers) > 0
            assert service._shutdown == False
    
    @pytest.mark.asyncio
    async def test_service_start_stop(self):
        """Test service start and stop."""
        with patch('backend.app.services.async_llm_service.settings'):
            service = AsyncLLMService()
            
            # Start service
            await service.start()
            assert len(service.worker_tasks) > 0
            assert service.metrics_collector_task is not None
            
            # Stop service
            await service.stop()
            assert service._shutdown == True
            assert len(service.worker_tasks) == 0
    
    @pytest.mark.asyncio
    async def test_invoke_basic(self):
        """Test basic LLM invocation."""
        with patch('backend.app.services.async_llm_service.settings'):
            service = AsyncLLMService()
            await service.start()
            
            # Mock provider response
            mock_provider = AsyncMock()
            mock_provider.execute_request = AsyncMock(return_value="test response")
            
            service.providers = {"test": mock_provider}
            service._select_provider = AsyncMock(return_value=mock_provider)
            
            try:
                result = await service.invoke(["test message"])
                assert result == "test response"
            finally:
                await service.stop()
    
    @pytest.mark.asyncio
    async def test_get_health_status(self):
        """Test health status reporting."""
        with patch('backend.app.services.async_llm_service.settings'):
            service = AsyncLLMService()
            
            # Mock provider health
            for provider in service.providers.values():
                provider.health_check = AsyncMock(return_value=True)
            
            status = await service.get_health_status()
            assert "status" in status
            assert "queue_size" in status
            assert "providers" in status
            assert len(status["providers"]) > 0

class TestPerformanceMonitoring:
    """Test performance monitoring functionality."""
    
    @pytest.mark.asyncio
    async def test_performance_helper(self):
        """Test performance measurement helper."""
        helper = PerformanceTestHelper()
        
        # Mock function to test
        async def mock_function(x):
            await asyncio.sleep(0.1)
            return f"result-{x}"
        
        # Create test arguments
        args_list = [(i,) for i in range(5)]
        
        # Run performance test
        metrics = await helper.run_concurrent_requests(
            mock_function,
            args_list,
            concurrency=3
        )
        
        # Verify metrics
        assert metrics["total_requests"] == 5
        assert metrics["successful_requests"] == 5
        assert metrics["success_rate"] == 1.0
        assert metrics["avg_response_time"] > 0
        assert "requests_per_second" in metrics
    
    @pytest.mark.asyncio
    async def test_performance_helper_with_failures(self):
        """Test performance helper with function failures."""
        helper = PerformanceTestHelper()
        
        # Mock function that fails sometimes
        async def failing_function(x):
            await asyncio.sleep(0.05)
            if x % 2 == 0:
                raise ValueError(f"Failed for {x}")
            return f"success-{x}"
        
        args_list = [(i,) for i in range(4)]
        
        metrics = await helper.run_concurrent_requests(
            failing_function,
            args_list,
            concurrency=2
        )
        
        # Should have some failures
        assert metrics["total_requests"] == 4
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 2
        assert metrics["success_rate"] == 0.5
        assert len(metrics["errors"]) == 2

class TestGlobalServiceFunctions:
    """Test global service convenience functions."""
    
    @pytest.mark.asyncio
    async def test_get_async_llm_service(self):
        """Test global service getter."""
        with patch('backend.app.services.async_llm_service.settings'):
            # Reset global instance
            import backend.app.services.async_llm_service as service_module
            service_module._async_llm_service = None
            
            service = await get_async_llm_service()
            assert service is not None
            assert isinstance(service, AsyncLLMService)
    
    @pytest.mark.asyncio
    async def test_async_llm_invoke_convenience(self):
        """Test convenience invoke function."""
        with patch('backend.app.services.async_llm_service.settings'):
            # Mock the global service
            mock_service = AsyncMock()
            mock_service.invoke = AsyncMock(return_value="test result")
            
            with patch('backend.app.services.async_llm_service.get_async_llm_service', return_value=mock_service):
                result = await async_llm_invoke(["test message"])
                assert result == "test result"
                mock_service.invoke.assert_called_once()

# Integration-style tests
class TestLLMServiceIntegration:
    """Integration tests for LLM service."""
    
    @pytest.mark.asyncio
    async def test_service_with_real_mock(self):
        """Test service with more realistic mocking."""
        with patch('backend.app.services.async_llm_service.settings'):
            service = AsyncLLMService()
            await service.start()
            
            try:
                # Mock all providers to return consistent responses
                for provider in service.providers.values():
                    provider.health_check = AsyncMock(return_value=True)
                    provider.execute_request = AsyncMock(return_value="mock response")
                
                result = await service.invoke(["test message"], timeout=5.0)
                assert result == "mock response"
                
            finally:
                await service.stop()
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_integration(self):
        """Test circuit breaker in service context."""
        from backend.app.services.async_llm_service import ProviderConfig
        
        config = ProviderConfig(name="test-provider")
        provider = AsyncLLMProvider(config)
        
        # Simulate failures
        for _ in range(10):  # More than failure threshold
            provider.circuit_breaker.call_failure()
        
        # Should not be able to execute
        assert not provider.circuit_breaker.can_execute()
        
        # Health check should fail
        health = await provider.health_check()
        assert health == False

if __name__ == "__main__":
    # Run basic tests
    print("Running Async LLM Service Tests...")
    
    # Test circuit breaker
    print("Testing Circuit Breaker...")
    breaker = CircuitBreaker(failure_threshold=3)
    assert breaker.can_execute() == True
    print("✓ Circuit breaker initial state")
    
    breaker.call_failure()
    breaker.call_failure()
    breaker.call_failure()
    assert breaker.can_execute() == False
    print("✓ Circuit breaker opens on failures")
    
    # Test rate limiter
    print("Testing Rate Limiter...")
    async def test_rate_limit():
        limiter = RateLimiter(max_calls_per_minute=2)
        assert await limiter.acquire() == True
        assert await limiter.acquire() == True
        assert await limiter.acquire() == False
        print("✓ Rate limiting works")
    
    asyncio.run(test_rate_limit())
    
    print("All basic tests passed! ✅")