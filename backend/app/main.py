from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from datetime import datetime
import asyncio

from app.config import settings

# Import routers with proper error handling
from app.api import pipelines, scraping, execution, workflow, osint, ai_investigation, auth

from app.services.websocket import ConnectionManager
from app.services.workflow_manager import get_workflow_manager
from app.services.task_storage import task_storage

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure SQLAlchemy logging to reduce spam
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)

# Connection manager for WebSocket
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Initialize database persistence
    try:
        from app.services.database import db_persistence
        db_persistence.initialize_database()
        logger.info("Database persistence initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
    
    # Initialize Redis task storage
    try:
        await task_storage.connect()
        logger.info("Redis task storage initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize Redis task storage: {e}")
        logger.info("Continuing without Redis...")
    
    # Start background task for WebSocket connection cleanup
    cleanup_task = asyncio.create_task(periodic_cleanup())
    
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

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers - OSINT router first to avoid WebSocket route conflicts
app.include_router(osint.router, prefix="/api/osint", tags=["osint"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(chat.router, prefix="/api/chat", tags=["chat"])  # Temporarily disabled
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["scraping"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])
app.include_router(ai_investigation.router, prefix="/api/ai-investigation", tags=["AI Investigation"])

logger.info("OSINT and AI Investigation routers included successfully")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    """Overall system health check."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
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
            # Use the ensure_connection method which handles async properly
            ping_result = await task_storage.ensure_connection()
            health_status["services"]["redis"] = {
                "status": "healthy" if ping_result else "unhealthy",
                "connected": ping_result
            }
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

@app.websocket("/api/ws/{pipeline_id}")
async def websocket_endpoint(websocket: WebSocket, pipeline_id: str):
    await manager.connect(websocket, pipeline_id)
    try:
        while True:
            data = await websocket.receive_json()
            
            # Update connection metadata for ping messages
            if data.get("type") == "ping":
                connection_id = f"{pipeline_id}_{id(websocket)}"
                if connection_id in manager.connection_metadata:
                    manager.connection_metadata[connection_id]["last_ping"] = datetime.utcnow()
            
            try:
                # Process the message through the agent
                response = await manager.process_message(pipeline_id, data)
                await manager.send_personal_message(response, websocket)
            except Exception as processing_error:
                logger.error(f"Message processing error: {processing_error}")
                # Send error response but keep connection alive
                error_response = {
                    "type": "error",
                    "response": "Sorry, I encountered an error processing your message. Please try again.",
                    "error": str(processing_error)
                }
                await manager.send_personal_message(error_response, websocket)
    except WebSocketDisconnect:
        await manager.disconnect(websocket, pipeline_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await manager.disconnect(websocket, pipeline_id)
        except:
            pass
