"""
Custom LLM Health Check API Endpoint

This module provides health check endpoints for custom LLM providers,
including configuration validation, connectivity testing, and performance monitoring.
"""

from fastapi import APIRouter, HTTPException, status
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime

from app.services.custom_llm_validator import (
    validate_custom_config,
    health_check_custom_provider,
    test_custom_provider_connection,
    custom_llm_validator
)
from app.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/custom-llm", response_model=Dict[str, Any])
async def get_custom_llm_health():
    """
    Get comprehensive health status of custom LLM provider.
    
    Returns:
        Dictionary with health status, configuration details, and performance metrics
    """
    try:
        # Basic configuration validation
        config_result = await validate_custom_config()
        
        health_response = {
            "timestamp": datetime.utcnow().isoformat(),
            "provider": "custom",
            "enabled": settings.CUSTOM_LLM_ENABLED,
            "configuration": config_result,
            "status": "not_configured"
        }
        
        # If custom LLM is not enabled, return early
        if not settings.CUSTOM_LLM_ENABLED:
            health_response["status"] = "disabled"
            return health_response
        
        # If configuration is invalid, return error status
        if not config_result.get("valid"):
            health_response["status"] = "configuration_error"
            return health_response
        
        # Perform connectivity test
        is_connected, conn_message = await test_custom_provider_connection()
        
        health_response["connectivity"] = {
            "connected": is_connected,
            "message": conn_message
        }
        
        if not is_connected:
            health_response["status"] = "connection_failed"
            return health_response
        
        # Perform comprehensive health check
        try:
            async with custom_llm_validator as validator:
                health_check = await validator.comprehensive_health_check(
                    settings.CUSTOM_LLM_BASE_URL,
                    settings.CUSTOM_LLM_MODEL,
                    settings.CUSTOM_LLM_PROVIDER_TYPE
                )
                
                health_response["health_check"] = health_check.dict()
                health_response["status"] = health_check.status
                
                # Add performance summary
                if health_check.performance_metrics:
                    metrics = health_check.performance_metrics
                    health_response["performance_summary"] = {
                        "success_rate": metrics.get("success_rate", 0),
                        "avg_response_time": metrics.get("avg_response_time", 0),
                        "requests_per_minute": 60 / metrics.get("avg_response_time", 1) if metrics.get("avg_response_time", 0) > 0 else 0
                    }
                
        except Exception as e:
            health_response["status"] = "health_check_failed"
            health_response["error"] = str(e)
        
        return health_response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/custom-llm/config", response_model=Dict[str, Any])
async def get_custom_llm_config():
    """
    Get current custom LLM configuration (without sensitive data).
    
    Returns:
        Dictionary with current configuration settings
    """
    try:
        config_result = await validate_custom_config()
        
        # Remove sensitive information
        safe_config = {
            "enabled": settings.CUSTOM_LLM_ENABLED,
            "provider_type": settings.CUSTOM_LLM_PROVIDER_TYPE,
            "base_url": settings.CUSTOM_LLM_BASE_URL,
            "model": settings.CUSTOM_LLM_MODEL,
            "has_api_key": bool(settings.CUSTOM_LLM_API_KEY),
            "validation": {
                "validate_model": settings.CUSTOM_LLM_VALIDATE_MODEL,
                "auto_discover_models": settings.CUSTOM_LLM_AUTO_DISCOVER_MODELS,
                "supported_models": settings.CUSTOM_LLM_SUPPORTED_MODELS
            },
            "performance": {
                "timeout": settings.CUSTOM_LLM_TIMEOUT,
                "max_retries": settings.CUSTOM_LLM_MAX_RETRIES,
                "retry_delay": settings.CUSTOM_LLM_RETRY_DELAY,
                "connection_pool_size": settings.CUSTOM_LLM_CONNECTION_POOL_SIZE,
                "streaming": settings.CUSTOM_LLM_STREAMING
            },
            "security": {
                "verify_ssl": settings.CUSTOM_LLM_VERIFY_SSL,
                "allow_self_signed": settings.CUSTOM_LLM_ALLOW_SELF_SIGNED
            },
            "monitoring": {
                "performance_monitoring": settings.CUSTOM_LLM_PERFORMANCE_MONITORING,
                "health_check_interval": settings.CUSTOM_LLM_HEALTH_CHECK_INTERVAL,
                "enable_cache": settings.CUSTOM_LLM_ENABLE_CACHE
            }
        }
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "configuration": safe_config,
            "validation_result": config_result
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration: {str(e)}"
        )


@router.get("/custom-llm/models", response_model=Dict[str, Any])
async def list_available_models():
    """
    List available models from the custom provider.
    
    Returns:
        Dictionary with available models and provider information
    """
    try:
        if not settings.CUSTOM_LLM_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom LLM is not enabled"
            )
        
        async with custom_llm_validator as validator:
            models = await validator.list_available_models(settings.CUSTOM_LLM_BASE_URL)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "provider_type": settings.CUSTOM_LLM_PROVIDER_TYPE or validator.detect_provider_type(settings.CUSTOM_LLM_BASE_URL),
                "base_url": settings.CUSTOM_LLM_BASE_URL,
                "total_models": len(models),
                "models": models,
                "current_model": settings.CUSTOM_LLM_MODEL,
                "current_model_available": settings.CUSTOM_LLM_MODEL in models if models else False
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list models: {str(e)}"
        )


@router.post("/custom-llm/test", response_model=Dict[str, Any])
async def test_custom_llm_connection():
    """
    Test connection to custom LLM provider with a simple request.
    
    Returns:
        Dictionary with test results and performance metrics
    """
    try:
        if not settings.CUSTOM_LLM_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom LLM is not enabled"
            )
        
        # Perform quick connectivity test
        is_connected, conn_message = await test_custom_provider_connection()
        
        test_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "connectivity_test": {
                "success": is_connected,
                "message": conn_message
            }
        }
        
        if not is_connected:
            test_result["status"] = "connection_failed"
            return test_result
        
        # Perform model validation test
        try:
            async with custom_llm_validator as validator:
                is_model_valid, model_error = await validator.validate_model(
                    settings.CUSTOM_LLM_BASE_URL,
                    settings.CUSTOM_LLM_MODEL
                )
                
                test_result["model_validation"] = {
                    "success": is_model_valid,
                    "message": model_error if not is_model_valid else "Model is valid and responsive"
                }
                
                if is_model_valid:
                    # Run performance benchmark
                    performance_metrics = await validator.performance_benchmark(
                        settings.CUSTOM_LLM_BASE_URL,
                        settings.CUSTOM_LLM_MODEL,
                        num_requests=3
                    )
                    
                    test_result["performance_metrics"] = performance_metrics
                    test_result["status"] = "healthy"
                    
                    # Add performance assessment
                    success_rate = performance_metrics.get("success_rate", 0)
                    avg_time = performance_metrics.get("avg_response_time", 0)
                    
                    if success_rate >= 0.9 and avg_time < 2.0:
                        test_result["performance_assessment"] = "excellent"
                    elif success_rate >= 0.8 and avg_time < 5.0:
                        test_result["performance_assessment"] = "good"
                    else:
                        test_result["performance_assessment"] = "needs_improvement"
                else:
                    test_result["status"] = "model_validation_failed"
                    
        except Exception as e:
            test_result["model_validation"] = {
                "success": False,
                "message": str(e)
            }
            test_result["status"] = "validation_error"
        
        return test_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test failed: {str(e)}"
        )


@router.get("/custom-llm/benchmark", response_model=Dict[str, Any])
async def benchmark_custom_llm(num_requests: int = 10):
    """
    Run performance benchmark for custom LLM provider.
    
    Args:
        num_requests: Number of test requests to make (default: 10)
        
    Returns:
        Dictionary with detailed benchmark results
    """
    try:
        if not settings.CUSTOM_LLM_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Custom LLM is not enabled"
            )
        
        if num_requests < 1 or num_requests > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Number of requests must be between 1 and 50"
            )
        
        async with custom_llm_validator as validator:
            # First validate the model
            is_model_valid, model_error = await validator.validate_model(
                settings.CUSTOM_LLM_BASE_URL,
                settings.CUSTOM_LLM_MODEL
            )
            
            if not is_model_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Model validation failed: {model_error}"
                )
            
            # Run benchmark
            performance_metrics = await validator.performance_benchmark(
                settings.CUSTOM_LLM_BASE_URL,
                settings.CUSTOM_LLM_MODEL,
                num_requests
            )
            
            # Calculate additional metrics
            if performance_metrics.get("success_rate", 0) > 0:
                avg_time = performance_metrics.get("avg_response_time", 0)
                min_time = performance_metrics.get("min_response_time", 0)
                max_time = performance_metrics.get("max_response_time", 0)
                
                performance_metrics["estimated_rpm"] = 60 / avg_time if avg_time > 0 else 0
                performance_metrics["time_variance"] = max_time - min_time
                performance_metrics["performance_score"] = (
                    performance_metrics["success_rate"] * 50 +  # 50% weight for success rate
                    (5 - min(5, avg_time)) * 10                 # 50% weight for speed (max 5s)
                )
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "benchmark_config": {
                    "provider": settings.CUSTOM_LLM_PROVIDER_TYPE,
                    "base_url": settings.CUSTOM_LLM_BASE_URL,
                    "model": settings.CUSTOM_LLM_MODEL,
                    "num_requests": num_requests
                },
                "results": performance_metrics,
                "recommendations": _generate_benchmark_recommendations(performance_metrics)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Benchmark failed: {str(e)}"
        )


def _generate_benchmark_recommendations(metrics: Dict[str, Any]) -> list:
    """Generate optimization recommendations based on benchmark results."""
    recommendations = []
    
    success_rate = metrics.get("success_rate", 0)
    avg_time = metrics.get("avg_response_time", 0)
    max_time = metrics.get("max_response_time", 0)
    
    # Success rate recommendations
    if success_rate < 0.8:
        recommendations.append({
            "category": "reliability",
            "priority": "high",
            "message": "Low success rate detected. Consider increasing timeout values or reducing request frequency."
        })
    elif success_rate < 0.95:
        recommendations.append({
            "category": "reliability",
            "priority": "medium",
            "message": "Some requests are failing. Check provider health and resource utilization."
        })
    
    # Response time recommendations
    if avg_time > 10:
        recommendations.append({
            "category": "performance",
            "priority": "high",
            "message": "Very slow response times. Consider hardware upgrades or model optimization."
        })
    elif avg_time > 5:
        recommendations.append({
            "category": "performance",
            "priority": "medium",
            "message": "Slow response times. Enable caching or reduce model size."
        })
    
    # Consistency recommendations
    if max_time > avg_time * 3:
        recommendations.append({
            "category": "consistency",
            "priority": "medium",
            "message": "High response time variance. Check for resource contention or system load."
        })
    
    # Hardware recommendations
    if success_rate >= 0.9 and avg_time < 2:
        recommendations.append({
            "category": "optimization",
            "priority": "low",
            "message": "Good performance! Consider increasing request rate for better throughput."
        })
    
    return recommendations


@router.get("/custom-llm/diagnostics", response_model=Dict[str, Any])
async def get_custom_llm_diagnostics():
    """
    Get comprehensive diagnostic information for troubleshooting.
    
    Returns:
        Dictionary with diagnostic data and system information
    """
    try:
        import platform
        import sys
        
        # Get configuration validation
        config_result = await validate_custom_config()
        
        # Get provider info
        provider_info = config_result.get("provider_info", {})
        
        diagnostics = {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "platform": platform.platform(),
                "python_version": sys.version,
                "architecture": platform.architecture()[0]
            },
            "scrapecraft": {
                "custom_llm_enabled": settings.CUSTOM_LLM_ENABLED,
                "provider_type": settings.CUSTOM_LLM_PROVIDER_TYPE,
                "base_url": settings.CUSTOM_LLM_BASE_URL,
                "model": settings.CUSTOM_LLM_MODEL,
                "has_api_key": bool(settings.CUSTOM_LLM_API_KEY)
            },
            "configuration": config_result,
            "recommendations": []
        }
        
        # Generate specific recommendations based on diagnostics
        if not config_result.get("valid"):
            diagnostics["recommendations"].append({
                "type": "error",
                "message": "Fix configuration errors before proceeding",
                "details": config_result.get("errors", [])
            })
        
        if provider_info.get("detected_type") == "ollama":
            diagnostics["recommendations"].extend([
                {
                    "type": "optimization",
                    "message": "Consider GPU acceleration with OLLAMA_GPU_LAYERS"
                },
                {
                    "type": "maintenance",
                    "message": "Pull models before use: ollama pull llama3.2:instruct"
                }
            ])
        elif provider_info.get("detected_type") == "localai":
            diagnostics["recommendations"].extend([
                {
                    "type": "optimization",
                    "message": "Adjust LOCALAI_THREADS based on CPU cores"
                },
                {
                    "type": "maintenance",
                    "message": "Monitor disk space for model storage"
                }
            ])
        elif provider_info.get("detected_type") == "vllm":
            diagnostics["recommendations"].extend([
                {
                    "type": "optimization",
                    "message": "Configure VLLM_TENSOR_PARALLEL_SIZE for multi-GPU setups"
                },
                {
                    "type": "monitoring",
                    "message": "Monitor GPU memory usage"
                }
            ])
        
        # Security recommendations
        if not settings.CUSTOM_LLM_VERIFY_SSL:
            diagnostics["recommendations"].append({
                "type": "security",
                "message": "Enable SSL verification for production use"
            })
        
        return diagnostics
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Diagnostics failed: {str(e)}"
        )