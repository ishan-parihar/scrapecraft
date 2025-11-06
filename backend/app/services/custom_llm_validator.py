"""
Custom LLM Provider Validation and Testing Utilities

This module provides comprehensive validation, testing, and health checking
for custom LLM providers including Ollama, LocalAI, vLLM, and other
OpenAI-compatible endpoints.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from pydantic import BaseModel, Field
from app.config import settings

logger = logging.getLogger(__name__)

class CustomLLMValidationError(Exception):
    """Custom exception for LLM validation failures."""
    pass

class ProviderHealthCheck(BaseModel):
    """Model for provider health check results."""
    provider_type: str
    base_url: str
    model: str
    status: str  # "healthy", "unhealthy", "degraded"
    response_time: Optional[float] = None
    error_message: Optional[str] = None
    last_check: datetime
    available_models: Optional[List[str]] = None
    performance_metrics: Optional[Dict[str, Any]] = None

class CustomLLMValidator:
    """Comprehensive validator for custom LLM providers."""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.health_cache: Dict[str, ProviderHealthCheck] = {}
        self.cache_ttl = timedelta(seconds=settings.CUSTOM_LLM_HEALTH_CHECK_INTERVAL)
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=settings.CUSTOM_LLM_TIMEOUT)
            connector = aiohttp.TCPConnector(
                limit=settings.CUSTOM_LLM_CONNECTION_POOL_SIZE,
                keepalive_timeout=settings.CUSTOM_LLM_TIMEOUT if settings.CUSTOM_LLM_KEEP_ALIVE else 0
            )
            
            ssl_context = None if settings.CUSTOM_LLM_ALLOW_SELF_SIGNED else True
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector
            )
    
    def detect_provider_type(self, base_url: str) -> str:
        """
        Automatically detect provider type based on URL patterns.
        
        Args:
            base_url: The base URL of the custom provider
            
        Returns:
            Detected provider type
        """
        base_url_lower = base_url.lower()
        
        if "ollama" in base_url_lower or ":11434" in base_url_lower:
            return "ollama"
        elif "localai" in base_url_lower or ":8080" in base_url_lower:
            return "localai"
        elif "vllm" in base_url_lower or ":8000" in base_url_lower:
            return "vllm"
        else:
            return "openai-compatible"
    
    async def test_connectivity(self, base_url: str) -> Tuple[bool, float, Optional[str]]:
        """
        Test basic connectivity to the custom provider.
        
        Args:
            base_url: The base URL to test
            
        Returns:
            Tuple of (success, response_time, error_message)
        """
        start_time = time.time()
        
        await self._ensure_session()
        
        if not self.session:
            return False, time.time() - start_time, "Failed to create HTTP session"
        
        try:
            # Try different endpoints for connectivity check
            endpoints = ["/v1/models", "/health", "/", "/status"]
            
            for endpoint in endpoints:
                try:
                    url = f"{base_url.rstrip('/')}{endpoint}"
                    headers = {}
                    
                    # Add API key if provided
                    if settings.CUSTOM_LLM_API_KEY:
                        headers[settings.CUSTOM_LLM_API_KEY_HEADER] = (
                            settings.CUSTOM_LLM_API_KEY_PREFIX + settings.CUSTOM_LLM_API_KEY
                        )
                    
                    async with self.session.get(url, headers=headers) as response:
                        response_time = time.time() - start_time
                        
                        if response.status in [200, 401, 403]:  # 401/403 means server is reachable
                            return True, response_time, None
                            
                except aiohttp.ClientError:
                    continue
            
            return False, time.time() - start_time, "All connectivity endpoints failed"
            
        except Exception as e:
            return False, time.time() - start_time, f"Connectivity test failed: {str(e)}"
    
    async def list_available_models(self, base_url: str) -> List[str]:
        """
        List available models from the custom provider.
        
        Args:
            base_url: The base URL of the provider
            
        Returns:
            List of available model names
        """
        await self._ensure_session()
        
        if not self.session:
            logger.warning("No HTTP session available for model listing")
            return self._get_fallback_models(base_url)
        
        try:
            # Try standard OpenAI-compatible models endpoint
            models_url = f"{base_url.rstrip('/')}/v1/models"
            headers = {}
            
            if settings.CUSTOM_LLM_API_KEY:
                headers[settings.CUSTOM_LLM_API_KEY_HEADER] = (
                    settings.CUSTOM_LLM_API_KEY_PREFIX + settings.CUSTOM_LLM_API_KEY
                )
            
            async with self.session.get(models_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    models = []
                    
                    # Handle different response formats
                    if "data" in data and isinstance(data["data"], list):
                        models = [model.get("id", "") for model in data["data"] if model.get("id")]
                    elif isinstance(data, list):
                        models = [model.get("id", str(model)) for model in data if model.get("id")]
                    
                    return [model for model in models if model]
                    
        except Exception as e:
            logger.warning(f"Failed to list models from {base_url}: {str(e)}")
        
        return self._get_fallback_models(base_url)
    
    def _get_fallback_models(self, base_url: str) -> List[str]:
        """Get fallback model names based on provider type."""
        provider_type = self.detect_provider_type(base_url)
        
        if provider_type == "ollama":
            return ["llama3.2:instruct", "codellama:7b", "mistral:7b", "qwen2.5:7b"]
        elif provider_type == "localai":
            return ["ggml-gpt4all-j", "ggml-mpt-7b-chat", "ggml-gpt-2-7b-chat"]
        elif provider_type == "vllm":
            return ["your-model", "llama2-7b", "llama2-13b"]
        else:
            return ["gpt-3.5-turbo", "gpt-4", "claude-instant", "your-custom-model"]
    
    async def validate_model(self, base_url: str, model: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a specific model is available and working.
        
        Args:
            base_url: The base URL of the provider
            model: The model name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # First check if model is in available models list
            if settings.CUSTOM_LLM_VALIDATE_MODEL:
                available_models = await self.list_available_models(base_url)
                
                if available_models and model not in available_models:
                    # Try partial matching for tagged models (e.g., "llama3.2" matches "llama3.2:instruct")
                    partial_matches = [
                        available_model for available_model in available_models
                        if model in available_model or available_model in model
                    ]
                    
                    if not partial_matches:
                        return False, f"Model '{model}' not found. Available models: {available_models[:10]}"
            
            # Try a simple completion request to validate the model
            await self._ensure_session()
            
            if not self.session:
                return False, "Failed to create HTTP session for model validation"
            
            chat_url = f"{base_url.rstrip('/')}/v1/chat/completions"
            headers = {
                "Content-Type": "application/json"
            }
            
            if settings.CUSTOM_LLM_API_KEY:
                headers[settings.CUSTOM_LLM_API_KEY_HEADER] = (
                    settings.CUSTOM_LLM_API_KEY_PREFIX + settings.CUSTOM_LLM_API_KEY
                )
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 10,
                "temperature": 0.1
            }
            
            async with self.session.post(chat_url, headers=headers, json=payload) as response:
                if response.status == 200:
                    return True, None
                else:
                    error_text = await response.text()
                    return False, f"Model validation failed (HTTP {response.status}): {error_text[:200]}"
                    
        except Exception as e:
            return False, f"Model validation error: {str(e)}"
    
    async def performance_benchmark(self, base_url: str, model: str, num_requests: int = 3) -> Dict[str, float]:
        """
        Benchmark the performance of a custom provider.
        
        Args:
            base_url: The base URL of the provider
            model: The model to benchmark
            num_requests: Number of test requests to make
            
        Returns:
            Dictionary with performance metrics
        """
        await self._ensure_session()
        
        if not self.session:
            logger.warning("No HTTP session available for benchmarking")
            return {
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "success_rate": 0.0,
                "total_requests": num_requests
            }
        
        response_times = []
        success_count = 0
        
        for i in range(num_requests):
            try:
                request_start_time = time.time()
                
                chat_url = f"{base_url.rstrip('/')}/v1/chat/completions"
                headers = {
                    "Content-Type": "application/json"
                }
                
                if settings.CUSTOM_LLM_API_KEY:
                    headers[settings.CUSTOM_LLM_API_KEY_HEADER] = (
                        settings.CUSTOM_LLM_API_KEY_PREFIX + settings.CUSTOM_LLM_API_KEY
                    )
                
                payload = {
                    "model": model,
                    "messages": [{"role": "user", "content": f"Test request {i+1}"}],
                    "max_tokens": 50,
                    "temperature": 0.1
                }
                
                async with self.session.post(chat_url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        await response.json()  # Consume the response
                        response_time = time.time() - request_start_time
                        response_times.append(response_time)
                        success_count += 1
                        
            except Exception as e:
                logger.warning(f"Benchmark request {i+1} failed: {str(e)}")
        
        if response_times:
            return {
                "avg_response_time": sum(response_times) / len(response_times),
                "min_response_time": min(response_times),
                "max_response_time": max(response_times),
                "success_rate": success_count / num_requests,
                "total_requests": num_requests
            }
        else:
            return {
                "avg_response_time": 0.0,
                "min_response_time": 0.0,
                "max_response_time": 0.0,
                "success_rate": 0.0,
                "total_requests": num_requests
            }
    
    async def comprehensive_health_check(self, base_url: str, model: str, provider_type: Optional[str] = None) -> ProviderHealthCheck:
        """
        Perform a comprehensive health check of a custom provider.
        
        Args:
            base_url: The base URL of the provider
            model: The model to check
            provider_type: Optional provider type override
            
        Returns:
            ProviderHealthCheck with detailed results
        """
        cache_key = f"{base_url}:{model}"
        
        # Check cache first
        if cache_key in self.health_cache:
            cached_check = self.health_cache[cache_key]
            if datetime.utcnow() - cached_check.last_check < self.cache_ttl:
                return cached_check
        
        # Auto-detect provider type if not provided
        if not provider_type:
            provider_type = settings.CUSTOM_LLM_PROVIDER_TYPE or self.detect_provider_type(base_url)
        
        health_check_start_time = time.time()
        
        # Initialize health check
        health_check = ProviderHealthCheck(
            provider_type=provider_type,
            base_url=base_url,
            model=model,
            status="unhealthy",
            last_check=datetime.utcnow()
        )
        
        try:
            # 1. Test connectivity
            is_connected, connectivity_time, conn_error = await self.test_connectivity(base_url)
            
            if not is_connected:
                health_check.error_message = f"Connectivity failed: {conn_error}"
                health_check.response_time = connectivity_time
                return health_check
            
            # 2. List available models
            available_models = await self.list_available_models(base_url)
            health_check.available_models = available_models
            
            # 3. Validate specific model
            is_model_valid, model_error = await self.validate_model(base_url, model)
            
            if not is_model_valid:
                health_check.error_message = f"Model validation failed: {model_error}"
                health_check.status = "degraded" if available_models else "unhealthy"
                health_check.response_time = time.time() - health_check_start_time
                return health_check
            
            # 4. Performance benchmark (optional, only if monitoring is enabled)
            if settings.CUSTOM_LLM_PERFORMANCE_MONITORING:
                performance_metrics = await self.performance_benchmark(base_url, model, num_requests=2)
                health_check.performance_metrics = performance_metrics
                
                # Determine status based on performance
                if performance_metrics["success_rate"] >= 0.8:
                    if performance_metrics["avg_response_time"] < 5.0:
                        health_check.status = "healthy"
                    else:
                        health_check.status = "degraded"
                        health_check.error_message = f"Slow response times: {performance_metrics['avg_response_time']:.2f}s"
                else:
                    health_check.status = "degraded"
                    health_check.error_message = f"Low success rate: {performance_metrics['success_rate']:.1%}"
            else:
                health_check.status = "healthy"
            
            health_check.response_time = time.time() - health_check_start_time
            
        except Exception as e:
            health_check.error_message = f"Health check failed: {str(e)}"
            health_check.response_time = time.time() - health_check_start_time
        
        # Cache the result
        self.health_cache[cache_key] = health_check
        
        return health_check
    
    async def validate_custom_llm_config(self) -> Dict[str, Any]:
        """
        Validate the complete custom LLM configuration.
        
        Returns:
            Dictionary with validation results and recommendations
        """
        results = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "recommendations": [],
            "provider_info": {},
            "health_check": None
        }
        
        try:
            # Check if custom LLM is enabled
            if not settings.CUSTOM_LLM_ENABLED:
                results["errors"].append("Custom LLM is not enabled (CUSTOM_LLM_ENABLED=false)")
                return results
            
            # Validate required settings
            if not settings.CUSTOM_LLM_BASE_URL:
                results["errors"].append("CUSTOM_LLM_BASE_URL is required")
                return results
            
            if not settings.CUSTOM_LLM_MODEL:
                results["errors"].append("CUSTOM_LLM_MODEL is required")
                return results
            
            # Provider type detection and validation
            detected_type = self.detect_provider_type(settings.CUSTOM_LLM_BASE_URL)
            configured_type = settings.CUSTOM_LLM_PROVIDER_TYPE
            
            if configured_type != "openai-compatible" and configured_type != detected_type:
                results["warnings"].append(
                    f"Provider type mismatch. Detected: {detected_type}, Configured: {configured_type}"
                )
            
            results["provider_info"] = {
                "detected_type": detected_type,
                "configured_type": configured_type,
                "base_url": settings.CUSTOM_LLM_BASE_URL,
                "model": settings.CUSTOM_LLM_MODEL,
                "has_api_key": bool(settings.CUSTOM_LLM_API_KEY)
            }
            
            # Perform health check
            async with self as validator:
                health_check = await self.comprehensive_health_check(
                    settings.CUSTOM_LLM_BASE_URL,
                    settings.CUSTOM_LLM_MODEL,
                    configured_type
                )
                
                results["health_check"] = health_check.dict()
                
                if health_check.status == "healthy":
                    results["valid"] = True
                elif health_check.status == "degraded":
                    results["valid"] = True  # Still usable but with warnings
                    results["warnings"].append(f"Provider health is degraded: {health_check.error_message}")
                else:
                    results["errors"].append(f"Provider health check failed: {health_check.error_message}")
            
            # Add recommendations based on provider type
            if detected_type == "ollama":
                results["recommendations"].extend([
                    "Consider using GPU acceleration with OLLAMA_GPU_LAYERS",
                    "Pull models before use: ollama pull llama3.2:instruct",
                    "Monitor resource usage as Ollama can be memory-intensive"
                ])
            elif detected_type == "localai":
                results["recommendations"].extend([
                    "Adjust LOCALAI_THREADS based on your CPU cores",
                    "Consider GPU acceleration if supported",
                    "Monitor disk space for model storage"
                ])
            elif detected_type == "vllm":
                results["recommendations"].extend([
                    "Configure VLLM_TENSOR_PARALLEL_SIZE for multi-GPU setups",
                    "Monitor GPU memory usage",
                    "Consider batch processing for better throughput"
                ])
            
            # Security recommendations
            if not settings.CUSTOM_LLM_VERIFY_SSL:
                results["warnings"].append("SSL verification is disabled - only use for development")
            
            if not settings.CUSTOM_LLM_API_KEY and "localhost" not in settings.CUSTOM_LLM_BASE_URL:
                results["warnings"].append("No API key configured for remote provider")
            
        except Exception as e:
            results["errors"].append(f"Configuration validation failed: {str(e)}")
        
        return results

# Singleton instance for convenient access
custom_llm_validator = CustomLLMValidator()

# Convenience functions
async def validate_custom_config() -> Dict[str, Any]:
    """Validate custom LLM configuration."""
    return await custom_llm_validator.validate_custom_llm_config()

async def health_check_custom_provider() -> ProviderHealthCheck:
    """Perform health check on configured custom provider."""
    async with custom_llm_validator as validator:
        return await validator.comprehensive_health_check(
            settings.CUSTOM_LLM_BASE_URL,
            settings.CUSTOM_LLM_MODEL,
            settings.CUSTOM_LLM_PROVIDER_TYPE
        )

async def test_custom_provider_connection() -> Tuple[bool, str]:
    """Quick connection test for custom provider."""
    try:
        health_check = await health_check_custom_provider()
        return health_check.status == "healthy", health_check.error_message or "Connection successful"
    except Exception as e:
        return False, f"Connection test failed: {str(e)}"