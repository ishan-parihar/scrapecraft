from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings

# Import routers with proper error handling
# Temporarily disabling auth due to cryptography dependency issues
from app.api import pipelines, scraping, execution, workflow

# TODO: Re-enable auth once cryptography dependencies are resolved
# from app.api import auth

from app.services.websocket import ConnectionManager
from app.services.workflow_manager import get_workflow_manager
# TODO: Re-enable task_storage once redis is available
# from app.services.task_storage import task_storage

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection manager for WebSocket
manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Skip Redis for now to focus on OSINT integration
    logger.info("Skipping Redis initialization for development")
    # TODO: Re-enable once task_storage is available
    # try:
    #     await task_storage.connect()
    #     logger.info("Redis task storage initialized")
    # except Exception as e:
    #     logger.warning(f"Failed to initialize Redis task storage: {e}")
    #     logger.info("Continuing without Redis...")
    
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    # TODO: Re-enable once task_storage is available
    # try:
    #     await task_storage.disconnect()
    #     logger.info("Redis task storage disconnected")
    # except Exception as e:
    #     logger.error(f"Error disconnecting Redis: {e}")

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

# Include routers
# TODO: Re-enable auth router once cryptography dependencies are resolved
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(chat.router, prefix="/api/chat", tags=["chat"])  # Temporarily disabled
app.include_router(pipelines.router, prefix="/api/pipelines", tags=["pipelines"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["scraping"])
app.include_router(execution.router, prefix="/api/execution", tags=["execution"])
app.include_router(workflow.router, prefix="/api/workflow", tags=["workflow"])

# TODO: Enable AI investigation routers once dependencies are installed
# Currently disabled due to missing cryptography and other dependencies
# 
# try:
#     from app.api.osint import router as osint_router
#     app.include_router(osint_router, prefix="/api/osint", tags=["osint"])
#     logger.info("OSINT router included successfully")
# except ImportError as e:
#     logger.warning(f"OSINT router not available: {e}")
# 
# try:
#     from app.api.ai_investigation import router as investigation_router
#     app.include_router(investigation_router)
#     logger.info("AI Investigation router included successfully")
# except ImportError as e:
#     logger.warning(f"AI Investigation router not available: {e}")

logger.info("AI Investigation routers temporarily disabled - pending dependency installation")

@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.websocket("/ws/{pipeline_id}")
async def websocket_endpoint(websocket: WebSocket, pipeline_id: str):
    await manager.connect(websocket, pipeline_id)
    try:
        while True:
            data = await websocket.receive_json()
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
        manager.disconnect(websocket, pipeline_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            manager.disconnect(websocket, pipeline_id)
        except:
            pass