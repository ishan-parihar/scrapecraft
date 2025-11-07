"""
Robust Error Handling System
Implements specific error types, retry mechanisms, and circuit breaker patterns.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import json

logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Categories of errors for better handling."""
    NETWORK = "network"
    API = "api"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    CONTENT = "content"
    VALIDATION = "validation"
    SYSTEM = "system"
    TIMEOUT = "timeout"

@dataclass
class ErrorContext:
    """Context information for errors."""
    service: str
    operation: str
    url: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    retry_count: int = 0
    additional_data: Dict[str, Any] = field(default_factory=dict)

class ScrapingException(Exception):
    """Base exception for scraping operations."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.context = context
        self.cause = cause
        self.timestamp = datetime.now()

class NetworkException(ScrapingException):
    """Network-related errors."""
    
    def __init__(self, message: str, context: Optional[ErrorContext] = None, cause: Optional[Exception] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )

class ApiException(ScrapingException):
    """API-related errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.API,
            severity=ErrorSeverity.HIGH,
            context=context,
            cause=cause
        )
        self.status_code = status_code

class RateLimitException(ScrapingException):
    """Rate limiting errors."""
    
    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            context=context,
            cause=cause
        )
        self.retry_after = retry_after

class TimeoutException(ScrapingException):
    """Timeout errors."""
    
    def __init__(self, message: str, timeout_seconds: Optional[float] = None, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.HIGH,
            context=context
        )
        self.timeout_seconds = timeout_seconds

class ValidationException(ScrapingException):
    """Data validation errors."""
    
    def __init__(self, message: str, invalid_data: Optional[Dict] = None, context: Optional[ErrorContext] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            context=context
        )
        self.invalid_data = invalid_data or {}

@dataclass
class RetryConfig:
    """Configuration for retry mechanisms."""
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[type] = field(default_factory=lambda: [
        NetworkException,
        TimeoutException,
        RateLimitException
    ])

class RetryMechanism:
    """Implements retry logic with exponential backoff and jitter."""
    
    def __init__(self, config: RetryConfig = None):
        self.config = config or RetryConfig()
    
    def calculate_delay(self, retry_count: int) -> float:
        """Calculate delay before next retry using exponential backoff with jitter."""
        delay = self.config.base_delay * (self.config.exponential_base ** retry_count)
        delay = min(delay, self.config.max_delay)
        
        if self.config.jitter:
            # Add jitter to prevent thundering herd
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        return max(0, delay)
    
    def should_retry(self, exception: Exception, retry_count: int) -> bool:
        """Determine if operation should be retried."""
        if retry_count >= self.config.max_retries:
            return False
        
        # Check if exception type is retryable
        for retryable_type in self.config.retryable_exceptions:
            if isinstance(exception, retryable_type):
                return True
        
        # Special handling for rate limit exceptions
        if isinstance(exception, RateLimitException):
            return True
        
        return False
    
    async def execute_with_retry(
        self,
        operation: Callable,
        *args,
        context: Optional[ErrorContext] = None,
        **kwargs
    ):
        """Execute operation with retry logic."""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if context:
                    context.retry_count = attempt
                
                return await operation(*args, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt == self.config.max_retries:
                    logger.error(f"Operation failed after {attempt + 1} attempts: {e}")
                    break
                
                if not self.should_retry(e, attempt):
                    logger.warning(f"Exception not retryable: {e}")
                    break
                
                delay = self.calculate_delay(attempt)
                
                # Special handling for rate limit
                if isinstance(e, RateLimitException) and e.retry_after:
                    delay = max(delay, e.retry_after)
                
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
        
        # Re-raise the last exception
        if last_exception:
            raise last_exception

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    expected_exception: type = ScrapingException
    success_threshold: int = 3  # Successes needed to close circuit

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """Implements circuit breaker pattern for external services."""
    
    def __init__(self, service_name: str, config: CircuitBreakerConfig = None):
        self.service_name = service_name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_success_time = None
        
    def is_closed(self) -> bool:
        """Check if circuit is closed (allowing requests)."""
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if (self.last_failure_time and 
                time.time() - self.last_failure_time > self.config.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker for {self.service_name} entering HALF_OPEN state")
                return True
            
            return False
        
        # HALF_OPEN state
        return True
    
    def record_success(self):
        """Record a successful operation."""
        self.last_success_time = time.time()
        
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker for {self.service_name} CLOSED - service recovered")
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success in closed state
            self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self, exception: Exception):
        """Record a failed operation."""
        self.last_failure_time = time.time()
        
        if isinstance(exception, self.config.expected_exception):
            self.failure_count += 1
            
            if self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    logger.error(f"Circuit breaker for {self.service_name} OPEN - too many failures")
            
            elif self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker for {self.service_name} OPEN - failure in HALF_OPEN state")
    
    async def call(self, operation: Callable, *args, **kwargs):
        """Execute operation through circuit breaker."""
        if not self.is_closed():
            raise ScrapingException(
                f"Circuit breaker OPEN for {self.service_name} - service unavailable",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.HIGH
            )
        
        try:
            result = await operation(*args, **kwargs)
            self.record_success()
            return result
            
        except Exception as e:
            self.record_failure(e)
            raise

class ErrorHandler:
    """Centralized error handling and logging."""
    
    def __init__(self):
        self.error_stats: Dict[str, Dict] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    def get_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create circuit breaker for a service."""
        if service_name not in self.circuit_breakers:
            self.circuit_breakers[service_name] = CircuitBreaker(service_name, config)
        return self.circuit_breakers[service_name]
    
    def log_error(self, error: ScrapingException):
        """Log error with structured information."""
        error_key = f"{error.category.value}:{error.service if error.context else 'unknown'}"
        
        # Update statistics
        if error_key not in self.error_stats:
            self.error_stats[error_key] = {
                'count': 0,
                'last_occurrence': None,
                'severity_distribution': {}
            }
        
        self.error_stats[error_key]['count'] += 1
        self.error_stats[error_key]['last_occurrence'] = error.timestamp
        
        severity = error.severity.value
        self.error_stats[error_key]['severity_distribution'][severity] = \
            self.error_stats[error_key]['severity_distribution'].get(severity, 0) + 1
        
        # Log with appropriate level
        log_message = f"[{error.category.value.upper()}] {error.message}"
        if error.context:
            log_message += f" | Service: {error.context.service}, Operation: {error.context.operation}"
            if error.context.url:
                log_message += f", URL: {error.context.url}"
        
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)
    
    def create_error_context(
        self,
        service: str,
        operation: str,
        url: Optional[str] = None,
        **kwargs
    ) -> ErrorContext:
        """Create error context with common fields."""
        return ErrorContext(
            service=service,
            operation=operation,
            url=url,
            additional_data=kwargs
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get current error statistics."""
        return {
            'total_error_types': len(self.error_stats),
            'circuit_breakers': {
                name: {
                    'state': cb.state.value,
                    'failure_count': cb.failure_count,
                    'success_count': cb.success_count
                }
                for name, cb in self.circuit_breakers.items()
            },
            'error_breakdown': self.error_stats
        }

# Global error handler instance
error_handler = ErrorHandler()

# Decorators for easy use
def handle_errors(
    service_name: str,
    operation_name: str = "unknown",
    retry_config: RetryConfig = None,
    circuit_breaker_config: CircuitBreakerConfig = None
):
    """Decorator for handling errors with retry and circuit breaker."""
    
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Create retry mechanism and circuit breaker
            retry_mechanism = RetryMechanism(retry_config)
            circuit_breaker = error_handler.get_circuit_breaker(service_name, circuit_breaker_config)
            
            # Create context for error reporting
            context = error_handler.create_error_context(
                service=service_name,
                operation=operation_name,
                url=kwargs.get('url')
            )
            
            async def operation():
                return await circuit_breaker.call(func, *args, **kwargs)
            
            try:
                return await retry_mechanism.execute_with_retry(operation, context=context)
            
            except ScrapingException as e:
                error_handler.log_error(e)
                raise
            
            except Exception as e:
                # Wrap unexpected exceptions
                wrapped_error = ScrapingException(
                    message=f"Unexpected error in {service_name}.{operation_name}: {str(e)}",
                    category=ErrorCategory.SYSTEM,
                    severity=ErrorSeverity.HIGH,
                    context=context,
                    cause=e
                )
                error_handler.log_error(wrapped_error)
                raise wrapped_error
        
        return wrapper
    return decorator