"""
Health Check API - Standardized

Provides comprehensive health monitoring for all system components
and services with standardized response formats.
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

from app.api.common.responses import (
    APIResponse, ErrorCode, create_success_response, create_error_response,
    HealthCheckResponse
)
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["Health"])

# Service health check functions
async def check_database_health() -> Dict[str, str]:
    """Check database connectivity."""
    try:
        # Check file-based storage databases
        from app.services.user_database import get_user_database
        from app.services.investigation_storage import load_investigations
        
        # Test user database
        user_db = get_user_database()
        user_count = len(user_db.users) if user_db else 0
        
        # Test investigation storage
        investigations = load_investigations()
        investigation_count = len(investigations) if investigations else 0
        
        return {
            "database": "healthy", 
            "user_count": user_count,
            "investigation_count": investigation_count,
            "storage_type": "file_based"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"database": f"unhealthy: {str(e)}"}

async def check_redis_health() -> Dict[str, str]:
    """Check Redis connectivity."""
    try:
        # Try to import and test Redis if available
        try:
            import redis
            redis_client = redis.from_url(settings.REDIS_URL)
            redis_client.ping()
            return {"redis": "healthy", "storage_type": "redis"}
        except ImportError:
            return {"redis": "not_installed", "storage_type": "file_fallback"}
        except Exception as redis_error:
            logger.warning(f"Redis not available: {redis_error}")
            return {"redis": "unavailable", "storage_type": "file_fallback", "error": str(redis_error)}
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return {"redis": f"unhealthy: {str(e)}"}

async def check_llm_service_health() -> Dict[str, str]:
    """Check LLM service connectivity."""
    try:
        # Import here to avoid circular imports
        from app.services.openrouter import test_connection
        
        # Test actual LLM service connectivity
        llm_health = await test_connection()
        
        if llm_health["status"] == "healthy":
            return {
                "llm_service": "healthy", 
                "provider": llm_health["provider"],
                "model": llm_health.get("model", "unknown"),
                "base_url": llm_health.get("base_url", "default")
            }
        else:
            return {
                "llm_service": f"unhealthy: {llm_health.get('error', 'Unknown error')}",
                "provider": llm_health["provider"]
            }
            
    except Exception as e:
        logger.error(f"LLM service health check failed: {e}")
        return {"llm_service": f"unhealthy: {str(e)}"}

async def check_websocket_health() -> Dict[str, str]:
    """Check WebSocket service."""
    try:
        # Check WebSocket manager availability
        from app.api.websocket import manager
        
        # Test if WebSocket manager is initialized
        if manager and hasattr(manager, 'active_connections'):
            connection_count = len(manager.active_connections)
            return {
                "websocket": "healthy", 
                "active_connections": connection_count,
                "manager_status": "initialized"
            }
        else:
            return {
                "websocket": "degraded", 
                "active_connections": 0,
                "manager_status": "not_initialized"
            }
    except Exception as e:
        logger.error(f"WebSocket health check failed: {e}")
        return {"websocket": f"unhealthy: {str(e)}"}

async def check_agent_registry_health() -> Dict[str, str]:
    """Check agent registry service."""
    try:
        # Check agent registry and available agents
        from app.agents.registry import get_agent_registry
        
        registry = get_agent_registry()
        
        if registry:
            # Count available agents
            agent_count = len(registry.agents) if hasattr(registry, 'agents') else 0
            
            # Test basic agent functionality
            test_agents = []
            if hasattr(registry, 'list_agents'):
                try:
                    test_agents = registry.list_agents()
                except Exception:
                    test_agents = []
            
            return {
                "agent_registry": "healthy", 
                "registered_agents": agent_count,
                "available_agent_types": len(test_agents),
                "registry_status": "initialized"
            }
        else:
            return {
                "agent_registry": "unhealthy", 
                "registered_agents": 0,
                "registry_status": "not_initialized"
            }
    except Exception as e:
        logger.error(f"Agent registry health check failed: {e}")
        return {"agent_registry": f"unhealthy: {str(e)}"}

@router.get("", response_model=APIResponse)
async def health_check() -> APIResponse:
    """
    Comprehensive health check for all system components.
    
    Returns:
        APIResponse with detailed health status
        
    Note:
        This endpoint checks all critical services and components
        to ensure the system is operating properly.
    """
    try:
        # Run all health checks concurrently
        health_tasks = [
            check_database_health(),
            check_redis_health(),
            check_llm_service_health(),
            check_websocket_health(),
            check_agent_registry_health()
        ]
        
        health_results = await asyncio.gather(*health_tasks, return_exceptions=True)
        
        # Combine results
        services = {}
        overall_status = "healthy"
        
        for result in health_results:
            if isinstance(result, Exception):
                logger.error(f"Health check exception: {result}")
                overall_status = "degraded"
                continue
            
            for service, status in result.items():
                services[service] = status
                if "unhealthy" in status.lower():
                    overall_status = "unhealthy"
        
        # Build health response
        health_data = HealthCheckResponse(
            status=overall_status,
            version="v1",
            timestamp=datetime.utcnow(),
            services=services
        )
        
        # Determine appropriate HTTP status based on overall health
        if overall_status == "healthy":
            return create_success_response(
                data=health_data.dict(),
                message="All systems operational"
            )
        elif overall_status == "degraded":
            return create_success_response(
                data=health_data.dict(),
                message="Some systems degraded"
            )
        else:
            # Still return 200 for health checks, but indicate issues in response
            return create_success_response(
                data=health_data.dict(),
                message="Some systems unhealthy"
            )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        # Return minimal health response
        health_data = HealthCheckResponse(
            status="unhealthy",
            version="v1",
            timestamp=datetime.utcnow(),
            services={"health_check": f"failed: {str(e)}"}
        )
        
        return create_error_response(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Health check failed",
            details={"error": str(e)}
        )

@router.get("/simple", response_model=APIResponse)
async def simple_health_check() -> APIResponse:
    """
    Simple health check for load balancers.
    
    Returns:
        APIResponse with basic health status
        
    Note:
        This is a lightweight endpoint suitable for load balancer
        health checks that require fast responses.
    """
    try:
        # Quick system check - no external dependencies
        health_data = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "v1"
        }
        
        return create_success_response(
            data=health_data,
            message="Service healthy"
        )
        
    except Exception as e:
        logger.error(f"Simple health check failed: {e}")
        
        return create_error_response(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Service unavailable",
            details={"error": str(e)}
        )

@router.get("/ready", response_model=APIResponse)
async def readiness_check() -> APIResponse:
    """
    Readiness check for container orchestration.
    
    Returns:
        APIResponse with readiness status
        
    Note:
        This endpoint checks if the service is ready to accept traffic,
        including all critical dependencies.
    """
    try:
        # Check critical dependencies
        critical_checks = [
            check_database_health(),
            check_redis_health()
        ]
        
        critical_results = await asyncio.gather(*critical_checks, return_exceptions=True)
        
        services = {}
        ready = True
        
        for result in critical_results:
            if isinstance(result, Exception):
                ready = False
                continue
            
            for service, status in result.items():
                services[service] = status
                if "unhealthy" in status.lower():
                    ready = False
        
        readiness_data = {
            "ready": ready,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "v1",
            "services": services
        }
        
        if ready:
            return create_success_response(
                data=readiness_data,
                message="Service ready"
            )
        else:
            return create_error_response(
                error_code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Service not ready",
                details=readiness_data
            )
            
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        
        return create_error_response(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Readiness check failed",
            details={"error": str(e)}
        )

@router.get("/live", response_model=APIResponse)
async def liveness_check() -> APIResponse:
    """
    Liveness check for container orchestration.
    
    Returns:
        APIResponse with liveness status
        
    Note:
        This endpoint checks if the service is still alive and responsive.
        It should not depend on external services.
    """
    try:
        # Basic liveness check - just verify the service is responding
        import time
        
        # Calculate uptime if start time is available
        try:
            # Get process start time
            import psutil
            process = psutil.Process()
            create_time = process.create_time()
            uptime_seconds = time.time() - create_time
            
            # Format uptime
            days = int(uptime_seconds // 86400)
            hours = int((uptime_seconds % 86400) // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            
            uptime_str = f"{days}d {hours}h {minutes}m"
        except ImportError:
            # Fallback if psutil not available
            uptime_str = "unknown"
        
        liveness_data = {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "v1",
            "uptime": uptime_str
        }
        
        return create_success_response(
            data=liveness_data,
            message="Service alive"
        )
        
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        
        return create_error_response(
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            message="Service unresponsive",
            details={"error": str(e)}
        )