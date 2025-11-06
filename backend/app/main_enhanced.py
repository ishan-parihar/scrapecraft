"""
Enhanced Main Application for ScrapeCraft OSINT Platform

This module provides the main FastAPI application with comprehensive security integration:
- Enhanced authentication and authorization
- Security headers and middleware
- Rate limiting and audit logging
- Health checks and monitoring
- WebSocket support with security
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import asyncio
import os

from app.config import settings

# Security imports
from app.security.integration import (
    setup_application_security, get_security_status, 
    perform_security_health_check, validate_security_environment
)

# Import routers with proper error handling
from app.api import pipelines, scraping, execution, workflow, osint, ai_investigation
# Use enhanced authentication instead of basic auth
try:
    from app.api.enhanced_auth import router as auth_router
except ImportError:
    # Fallback to basic auth if enhanced auth not available
    from app.api import auth as auth_router
    logger.warning("Enhanced authentication not available, using basic auth")

from app.services.websocket import ConnectionManager
from app.services.workflow_manager import get_workflow_manager
from app.services.task_storage import task_storage

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection manager for WebSocket
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with security integration."""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Setup security first
    security_setup_success = await setup_application_security(app)
    if not security_setup_success:
        logger.warning("Security setup failed - continuing with reduced security")
    
    # Validate security environment
    security_messages = validate_security_environment()
    for message in security_messages:
        if message.startswith("ERROR"):
            logger.error(message)
        elif message.startswith("WARNING"):
            logger.warning(message)
        else:
            logger.info(message)
    
    # Initialize Redis task storage
    try:
        await task_storage.connect()
        logger.info("Redis task storage initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis task storage: {e}")
        logger.info("Continuing without Redis...")
    
    # Start background task for WebSocket connection cleanup
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
    # Log security status
    security_status = get_security_status()
    logger.info(f"Security status: {security_status}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    
    # Cancel background task
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    
    try:
        if task_storage.redis_client:
            await task_storage.disconnect()
            logger.info("Redis task storage disconnected")
    except Exception as e:
        logger.error(f"Error disconnecting Redis: {e}")

async def periodic_cleanup():
    """Background task to periodically clean up stale connections."""
    while True:
        try:
            await manager.cleanup_stale_connections()
            await asyncio.sleep(300)  # Run every 5 minutes
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in periodic cleanup: {e}")
            await asyncio.sleep(60)  # Wait 1 minute before retrying

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="ScrapeCraft OSINT Platform - Enterprise-grade Open Source Intelligence gathering",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development").lower() != "production" else None,
    redoc_url="/redoc" if os.getenv("ENVIRONMENT", "development").lower() != "production" else None,
)

# Enhanced CORS middleware with security considerations
environment = os.getenv("ENVIRONMENT", "development").lower()
if environment == "production":
    cors_origins = [os.getenv("PRODUCTION_FRONTEND_URL", "https://app.scrapecraft.com")]
elif environment == "staging":
    cors_origins = [os.getenv("STAGING_FRONTEND_URL", "https://staging.scrapecraft.com")]
else:  # development
    cors_origins = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Requested-With",
        "Accept",
        "Origin",
        "User-Agent"
    ],
)

# Security middleware (will be added during setup)
# Security headers middleware is added in setup_application_security

# Include routers with enhanced security
app.include_router(auth_router, tags=["Authentication"])

# Core API routers
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["Pipelines"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["Scraping"])
app.include_router(execution.router, prefix="/api/execution", tags=["Execution"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["Workflow"])
app.include_router(osint.router, prefix="/api/osint", tags=["OSINT"])
app.include_router(ai_investigation.router, prefix="/api/ai-investigation", tags=["AI Investigation"])

logger.info("All routers included successfully")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with basic application info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "security_enabled": get_security_status().get("security_initialized", False)
    }

@app.get("/health")
async def health_check():
    """Comprehensive system health check with security status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "services": {},
        "security": {}
    }
    
    # Check security status
    try:
        security_health = perform_security_health_check()
        health_status["security"] = security_health
        
        if security_health["overall_status"] in ["unhealthy", "error"]:
            health_status["status"] = "degraded"
        elif security_health["overall_status"] == "degraded":
            if health_status["status"] == "healthy":
                health_status["status"] = "degraded"
                
    except Exception as e:
        health_status["security"] = {
            "overall_status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check WebSocket manager
    try:
        ws_health = await manager.health_check()
        health_status["services"]["websocket"] = ws_health
        if ws_health["status"] != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["websocket"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check Redis/Task Storage
    try:
        if task_storage.redis_client:
            ping_result = await task_storage.ensure_connection()
            health_status["services"]["redis"] = {
                "status": "healthy" if ping_result else "unhealthy",
                "connected": ping_result
            }
            if not ping_result:
                health_status["status"] = "degraded"
        else:
            health_status["services"]["redis"] = {
                "status": "disabled",
                "connected": False
            }
    except Exception as e:
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "connected": False,
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    # Check LLM Provider
    try:
        from app.services.openrouter import test_connection
        llm_health = await test_connection()
        health_status["services"]["llm"] = llm_health
        if llm_health.get("status") != "healthy":
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["services"]["llm"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "degraded"
    
    return health_status

@app.get("/health/security")
async def security_health_check():
    """Detailed security system health check."""
    try:
        security_health = perform_security_health_check()
        security_status = get_security_status()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "security_health": security_health,
            "security_status": security_status,
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "error",
            "error": str(e),
            "environment": os.getenv("ENVIRONMENT", "development")
        }

@app.get("/health/redis")
async def redis_health():
    """Redis connectivity health check."""
    try:
        if task_storage.redis_client:
            ping_result = await task_storage.ensure_connection()
            return {
                "status": "healthy" if ping_result else "unhealthy",
                "connected": ping_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "disabled",
                "connected": False,
                "timestamp": datetime.utcnow().isoformat()
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connected": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health/websocket")
async def websocket_health():
    """WebSocket connection manager health check."""
    try:
        ws_health = await manager.health_check()
        return ws_health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/health/llm")
async def llm_health():
    """LLM provider connectivity health check."""
    try:
        from app.services.openrouter import test_connection
        llm_health = await test_connection()
        return llm_health
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

# Security endpoints (protected)
@app.get("/api/security/status")
async def security_status_endpoint(request: Request):
    """Get current security system status."""
    try:
        # This endpoint should be protected in production
        client_ip = request.client.host if request.client else "unknown"
        
        # Log access to security status
        logger.info(f"Security status accessed from IP: {client_ip}")
        
        security_status = get_security_status()
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "security_status": security_status,
            "client_ip": client_ip
        }
    except Exception as e:
        logger.error(f"Security status endpoint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security status"
        )

# Rate limiting test endpoint (for development)
@app.get("/api/rate-limit-test")
async def rate_limit_test(request: Request):
    """Test endpoint for rate limiting functionality."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.info(f"Rate limit test accessed from IP: {client_ip}, User-Agent: {user_agent}")
    
    return {
        "message": "Rate limit test successful",
        "timestamp": datetime.utcnow().isoformat(),
        "client_ip": client_ip
    }

# Enhanced WebSocket endpoint with security considerations
@app.websocket("/ws/{pipeline_id}")
async def websocket_endpoint(websocket: WebSocket, pipeline_id: str):
    """WebSocket endpoint with enhanced security."""
    # Get client information for security logging
    client_info = {
        "client_host": websocket.client.host if websocket.client else "unknown",
        "client_port": websocket.client.port if websocket.client else None,
        "user_agent": websocket.headers.get("user-agent", "unknown"),
        "origin": websocket.headers.get("origin", "unknown")
    }
    
    logger.info(f"WebSocket connection attempt for pipeline {pipeline_id} from {client_info['client_host']}")
    
    # In production, you might want to add authentication checks here
    # For example, checking for a valid JWT token in query parameters or headers
    
    await manager.connect(websocket, pipeline_id)
    logger.info(f"WebSocket connected for pipeline {pipeline_id}")
    
    try:
        while True:
            data = await websocket.receive_json()
            
            # Basic message validation
            if not isinstance(data, dict):
                logger.warning(f"Invalid message format from {client_info['client_host']}")
                continue
            
            # Update connection metadata for ping messages
            if data.get("type") == "ping":
                connection_id = f"{pipeline_id}_{id(websocket)}"
                if connection_id in manager.connection_metadata:
                    manager.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
                continue
            
            # Log message for security auditing
            message_type = data.get("type", "unknown")
            logger.debug(f"Processing {message_type} message from {client_info['client_host']}")
            
            try:
                # Process the message through the agent
                response = await manager.process_message(pipeline_id, data)
                await manager.send_personal_message(response, websocket)
            except Exception as processing_error:
                logger.error(f"Message processing error from {client_info['client_host']}: {processing_error}")
                
                # Send error response but keep connection alive
                error_response = {
                    "type": "error",
                    "response": "Sorry, I encountered an error processing your message. Please try again.",
                    "error": "processing_error"
                }
                await manager.send_personal_message(error_response, websocket)
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for pipeline {pipeline_id} from {client_info['client_host']}")
        await manager.disconnect(websocket, pipeline_id)
    except Exception as e:
        logger.error(f"WebSocket error from {client_info['client_host']}: {e}")
        try:
            await manager.disconnect(websocket, pipeline_id)
        except:
            pass

# Global exception handlers for security
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Global HTTP exception handler with security logging."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Log security-relevant exceptions
    if exc.status_code >= 400:
        logger.warning(
            f"HTTP {exc.status_code} from {client_ip} - {request.method} {request.url.path} - "
            f"User-Agent: {user_agent} - Detail: {exc.detail}"
        )
    
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unexpected errors."""
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    logger.error(
        f"Unhandled exception from {client_ip} - {request.method} {request.url.path} - "
        f"User-Agent: {user_agent} - Error: {str(exc)}"
    )
    
    # Don't expose internal errors in production
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        detail = "Internal server error"
    else:
        detail = f"Internal server error: {str(exc)}"
    
    return {
        "error": detail,
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }

# Application startup complete
logger.info(f"{settings.APP_NAME} application initialized with enhanced security")