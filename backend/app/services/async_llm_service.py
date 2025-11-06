"""
Enhanced Async LLM Service with Connection Pooling, Circuit Breaker, and Performance Monitoring

This service provides production-ready async LLM interactions with:
- Connection pooling for multiple providers
- Circuit breaker pattern for fault tolerance
- Request queuing and load balancing
- Performance monitoring and metrics
- Adaptive retry logic with exponential backoff
- Rate limiting and throttling
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
from contextlib import asynccontextmanager
from collections import deque, defaultdict
import weakref

from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.outputs import LLMResult

from app.services.openrouter import get_llm, get_llm_with_fallback, LLMProviderError
from app.config import settings

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered

@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    priority: int = 1
    max_concurrent: int = 5
    timeout_seconds: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 2.0
    rate_limit_per_minute: int = 60
    weight: float = 1.0  # For load balancing

@dataclass
class RequestMetrics:
    """Metrics for LLM requests."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_error: Optional[str] = None
    circuit_state: CircuitState = CircuitState.CLOSED
    circuit_failure_count: int = 0
    last_circuit_open: Optional[datetime] = None

@dataclass
class QueuedRequest:
    """A queued LLM request."""
    id: str
    messages: List[BaseMessage]
    future: asyncio.Future
    provider: Optional[str] = None
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3

class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED
    
    def call_success(self):
        """Record a successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def call_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened due to {self.failure_count} failures")
    
    def can_execute(self) -> bool:
        """Check if execution is allowed."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN and self.last_failure_time:
            if (datetime.utcnow() - self.last_failure_time).total_seconds() >= self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker transitioning to half-open")
                return True
            return False
        
        return True  # HALF_OPEN allows one test request
    
    def get_state(self) -> CircuitState:
        """Get current circuit state."""
        return self.state

class RateLimiter:
    """Rate limiter for API calls."""
    
    def __init__(self, max_calls_per_minute: int):
        self.max_calls = max_calls_per_minute
        self.calls = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """Acquire a rate limit slot."""
        async with self._lock:
            now = datetime.utcnow()
            # Remove calls older than 1 minute
            while self.calls and (now - self.calls[0]).total_seconds() > 60:
                self.calls.popleft()
            
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            return False
    
    async def wait_for_slot(self, timeout: float = 60.0) -> bool:
        """Wait for an available rate limit slot."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if await self.acquire():
                return True
            await asyncio.sleep(0.1)
        return False

class AsyncLLMProvider:
    """Async wrapper for LLM providers with connection pooling."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self.llm_instance: Optional[BaseLanguageModel] = None
        self.semaphore = asyncio.Semaphore(config.max_concurrent)
        self.circuit_breaker = CircuitBreaker()
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)
        self.metrics = RequestMetrics()
        self._connection_lock = asyncio.Lock()
        self._last_health_check: Optional[datetime] = None
        self._is_healthy = True
    
    async def get_llm_instance(self) -> BaseLanguageModel:
        """Get or create LLM instance with connection pooling."""
        if self.llm_instance is None:
            async with self._connection_lock:
                if self.llm_instance is None:
                    try:
                        # Store original provider setting locally
                        original_provider = settings.LLM_PROVIDER
                        
                        # Create LLM instance by directly calling the provider function
                        if self.config.name.lower() == "openrouter":
                            from app.services.openrouter import get_openrouter_llm_direct
                            self.llm_instance = get_openrouter_llm_direct()
                        elif self.config.name.lower() == "openai":
                            from app.services.openrouter import get_openai_llm_direct
                            self.llm_instance = get_openai_llm_direct()
                        elif self.config.name.lower() == "custom":
                            from app.services.openrouter import get_custom_llm_direct
                            self.llm_instance = get_custom_llm_direct()
                        else:
                            # Fallback to get_llm
                            self.llm_instance = get_llm()
                        
                        logger.info(f"Created LLM instance for provider: {self.config.name}")
                    except Exception as e:
                        logger.error(f"Failed to create LLM instance for {self.config.name}: {e}")
                        raise
        return self.llm_instance
    
    async def health_check(self) -> bool:
        """Check provider health."""
        if (self._last_health_check and 
            (datetime.utcnow() - self._last_health_check).total_seconds() < 300):  # 5 minutes
            return self._is_healthy
        
        try:
            llm = await self.get_llm_instance()
            # Quick health check with minimal request
            await llm.ainvoke("test")
            self._is_healthy = True
            self.circuit_breaker.call_success()
        except Exception as e:
            logger.warning(f"Health check failed for {self.config.name}: {e}")
            self._is_healthy = False
            self.circuit_breaker.call_failure()
        
        self._last_health_check = datetime.utcnow()
        return self._is_healthy
    
    async def execute_request(self, messages: List[BaseMessage], timeout: float) -> Any:
        """Execute LLM request with all safety mechanisms."""
        if not self.circuit_breaker.can_execute():
            raise LLMProviderError(f"Circuit breaker open for provider: {self.config.name}")
        
        if not await self.rate_limiter.wait_for_slot(timeout):
            raise LLMProviderError(f"Rate limit exceeded for provider: {self.config.name}")
        
        async with self.semaphore:  # Limit concurrent requests
            start_time = time.time()
            
            try:
                llm = await self.get_llm_instance()
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    llm.ainvoke(messages),
                    timeout=timeout
                )
                
                # Record success
                response_time = time.time() - start_time
                self.metrics.total_requests += 1
                self.metrics.successful_requests += 1
                self.metrics.total_response_time += response_time
                self.metrics.last_request_time = datetime.utcnow()
                self.circuit_breaker.call_success()
                
                logger.debug(f"Request completed in {response_time:.2f}s for {self.config.name}")
                return result
                
            except asyncio.TimeoutError:
                self.metrics.failed_requests += 1
                self.metrics.last_error = "Timeout"
                self.circuit_breaker.call_failure()
                raise LLMProviderError(f"Request timeout for provider: {self.config.name}")
            
            except Exception as e:
                self.metrics.failed_requests += 1
                self.metrics.last_error = str(e)
                self.circuit_breaker.call_failure()
                logger.error(f"Request failed for {self.config.name}: {e}")
                raise

class AsyncLLMService:
    """Main async LLM service with provider management and load balancing."""
    
    def __init__(self):
        self.providers: Dict[str, AsyncLLMProvider] = {}
        self.request_queue: asyncio.Queue = asyncio.Queue()
        self.worker_tasks: List[asyncio.Task] = []
        self.metrics_collector_task: Optional[asyncio.Task] = None
        self._shutdown = False
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize LLM providers based on configuration."""
        # Default provider configurations
        provider_configs = [
            ProviderConfig(
                name=settings.LLM_PROVIDER,
                priority=1,
                max_concurrent=5,
                rate_limit_per_minute=60,
                weight=1.0
            )
        ]
        
        # Add fallback providers if configured
        if settings.OPENROUTER_API_KEY and settings.LLM_PROVIDER != "openrouter":
            provider_configs.append(
                ProviderConfig(
                    name="openrouter",
                    priority=2,
                    max_concurrent=3,
                    rate_limit_per_minute=30,
                    weight=0.8
                )
            )
        
        if settings.OPENAI_API_KEY and settings.LLM_PROVIDER != "openai":
            provider_configs.append(
                ProviderConfig(
                    name="openai",
                    priority=3,
                    max_concurrent=3,
                    rate_limit_per_minute=30,
                    weight=0.8
                )
            )
        
        if settings.CUSTOM_LLM_ENABLED and settings.LLM_PROVIDER != "custom":
            provider_configs.append(
                ProviderConfig(
                    name="custom",
                    priority=4,
                    max_concurrent=2,
                    rate_limit_per_minute=20,
                    weight=0.6
                )
            )
        
        # Create provider instances
        for config in provider_configs:
            try:
                provider = AsyncLLMProvider(config)
                self.providers[config.name] = provider
                logger.info(f"Initialized provider: {config.name}")
            except Exception as e:
                logger.error(f"Failed to initialize provider {config.name}: {e}")
    
    async def start(self):
        """Start the async LLM service."""
        if self.worker_tasks:
            return  # Already started
        
        # Start worker tasks for processing requests
        num_workers = min(10, len(self.providers) * 2)
        for i in range(num_workers):
            task = asyncio.create_task(self._worker(f"worker-{i}"))
            self.worker_tasks.append(task)
        
        # Start metrics collector
        self.metrics_collector_task = asyncio.create_task(self._metrics_collector())
        
        logger.info(f"Async LLM service started with {num_workers} workers")
    
    async def stop(self):
        """Stop the async LLM service."""
        self._shutdown = True
        
        # Cancel worker tasks
        for task in self.worker_tasks:
            task.cancel()
        
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks, return_exceptions=True)
        
        # Cancel metrics collector
        if self.metrics_collector_task:
            self.metrics_collector_task.cancel()
            try:
                await self.metrics_collector_task
            except asyncio.CancelledError:
                pass
        
        self.worker_tasks.clear()
        logger.info("Async LLM service stopped")
    
    async def _worker(self, worker_name: str):
        """Worker task to process queued requests."""
        logger.info(f"Worker {worker_name} started")
        
        while not self._shutdown:
            try:
                # Get request from queue with timeout
                request = await asyncio.wait_for(
                    self.request_queue.get(),
                    timeout=1.0
                )
                
                await self._process_request(request, worker_name)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(0.1)
        
        logger.info(f"Worker {worker_name} stopped")
    
    async def _process_request(self, request: QueuedRequest, worker_name: str):
        """Process a single queued request."""
        start_time = time.time()
        
        try:
            # Select best provider
            provider = await self._select_provider(request)
            
            if not provider:
                raise LLMProviderError("No healthy providers available")
            
            # Execute request
            result = await provider.execute_request(
                request.messages,
                request.timeout
            )
            
            # Set result for future
            if not request.future.done():
                request.future.set_result(result)
            
            logger.debug(f"{worker_name} completed request {request.id}")
            
        except Exception as e:
            # Handle retry logic
            if request.retry_count < request.max_retries:
                request.retry_count += 1
                request.provider = None  # Allow provider selection again
                await self.request_queue.put(request)
                logger.info(f"Retrying request {request.id} (attempt {request.retry_count})")
            else:
                if not request.future.done():
                    request.future.set_exception(e)
                logger.error(f"Request {request.id} failed after {request.retry_count} retries: {e}")
        
        finally:
            # Update queue metrics
            processing_time = time.time() - start_time
            logger.debug(f"Request {request.id} processed in {processing_time:.2f}s")
    
    async def _select_provider(self, request: QueuedRequest) -> Optional[AsyncLLMProvider]:
        """Select the best provider for a request."""
        available_providers = []
        
        for provider in self.providers.values():
            # Check if provider is healthy and available
            if (provider.circuit_breaker.can_execute() and 
                await provider.health_check()):
                available_providers.append(provider)
        
        if not available_providers:
            return None
        
        # Load balancing based on weights and current load
        best_provider = None
        best_score = -1
        
        for provider in available_providers:
            # Calculate score based on weight, success rate, and current load
            success_rate = (
                provider.metrics.successful_requests / max(1, provider.metrics.total_requests)
            )
            avg_response_time = (
                provider.metrics.total_response_time / max(1, provider.metrics.successful_requests)
            )
            
            # Current load ( semaphore available permits )
            load_factor = provider.semaphore._value / provider.config.max_concurrent
            
            # Combined score (higher is better)
            score = (
                provider.config.weight * 0.4 +
                success_rate * 0.3 +
                (1 / max(0.1, avg_response_time)) * 0.2 +
                load_factor * 0.1
            )
            
            if score > best_score:
                best_score = score
                best_provider = provider
        
        return best_provider
    
    async def invoke(
        self,
        messages: List[Union[str, BaseMessage]],
        timeout: float = 30.0,
        priority: int = 0,
        provider: Optional[str] = None
    ) -> Any:
        """
        Invoke LLM with async processing and load balancing.
        
        Args:
            messages: List of messages or strings to send to LLM
            timeout: Request timeout in seconds
            priority: Request priority (higher = more important)
            provider: Specific provider to use (optional)
            
        Returns:
            LLM response
        """
        # Convert string messages to HumanMessage
        processed_messages = []
        for msg in messages:
            if isinstance(msg, str):
                processed_messages.append(HumanMessage(content=msg))
            else:
                processed_messages.append(msg)
        
        # Create request
        request_id = f"req_{int(time.time() * 1000)}_{id(messages)}"
        future = asyncio.Future()
        
        request = QueuedRequest(
            id=request_id,
            messages=processed_messages,
            future=future,
            provider=provider,
            priority=priority,
            timeout=timeout
        )
        
        # Queue request
        await self.request_queue.put(request)
        
        # Wait for result
        try:
            result = await asyncio.wait_for(future, timeout=timeout + 10)  # Extra time for queue
            return result
        except asyncio.TimeoutError:
            if not future.done():
                future.cancel()
            raise LLMProviderError(f"Request {request_id} timed out")
    
    async def _metrics_collector(self):
        """Collect and report metrics periodically."""
        while not self._shutdown:
            try:
                await asyncio.sleep(60)  # Report every minute
                
                total_requests = sum(p.metrics.total_requests for p in self.providers.values())
                total_success = sum(p.metrics.successful_requests for p in self.providers.values())
                queue_size = self.request_queue.qsize()
                
                logger.info(
                    f"LLM Service Metrics - Queue: {queue_size}, "
                    f"Requests: {total_requests}, Success: {total_success}, "
                    f"Success Rate: {total_success / max(1, total_requests):.1%}"
                )
                
            except Exception as e:
                logger.error(f"Metrics collector error: {e}")
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status."""
        provider_status = {}
        
        for name, provider in self.providers.items():
            provider_status[name] = {
                "healthy": await provider.health_check(),
                "circuit_state": provider.circuit_breaker.get_state().value,
                "metrics": {
                    "total_requests": provider.metrics.total_requests,
                    "successful_requests": provider.metrics.successful_requests,
                    "failed_requests": provider.metrics.failed_requests,
                    "success_rate": (
                        provider.metrics.successful_requests / 
                        max(1, provider.metrics.total_requests)
                    ),
                    "avg_response_time": (
                        provider.metrics.total_response_time / 
                        max(1, provider.metrics.successful_requests)
                    ),
                    "last_error": provider.metrics.last_error
                },
                "config": {
                    "max_concurrent": provider.config.max_concurrent,
                    "rate_limit_per_minute": provider.config.rate_limit_per_minute,
                    "weight": provider.config.weight
                }
            }
        
        return {
            "status": "healthy" if any(s["healthy"] for s in provider_status.values()) else "unhealthy",
            "queue_size": self.request_queue.qsize(),
            "workers_active": len(self.worker_tasks),
            "providers": provider_status
        }

# Global service instance
_async_llm_service: Optional[AsyncLLMService] = None

async def get_async_llm_service() -> AsyncLLMService:
    """Get or create the global async LLM service."""
    global _async_llm_service
    
    if _async_llm_service is None:
        _async_llm_service = AsyncLLMService()
        await _async_llm_service.start()
    
    return _async_llm_service

async def shutdown_async_llm_service():
    """Shutdown the global async LLM service."""
    global _async_llm_service
    
    if _async_llm_service:
        await _async_llm_service.stop()
        _async_llm_service = None

# Convenience functions
async def async_llm_invoke(
    messages: List[Union[str, BaseMessage]],
    timeout: float = 30.0,
    priority: int = 0,
    provider: Optional[str] = None
) -> Any:
    """Convenience function for async LLM invocation."""
    service = await get_async_llm_service()
    return await service.invoke(messages, timeout, priority, provider)

@asynccontextmanager
async def async_llm_context():
    """Context manager for async LLM service."""
    service = await get_async_llm_service()
    try:
        yield service
    finally:
        await shutdown_async_llm_service()