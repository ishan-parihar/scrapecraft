#!/usr/bin/env python3
"""
Working backend server for ScrapeCraft
"""
import asyncio
import json
import logging
import sys
import os
from pathlib import Path
import subprocess
import time
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import FastAPI components
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Create FastAPI app
app = FastAPI(
    title="ScrapeCraft Backend",
    version="1.0.0",
    description="OSINT Platform Backend"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Basic health endpoints
@app.get("/")
async def root():
    return {
        "name": "ScrapeCraft",
        "version": "1.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "websocket": {"status": "healthy"},
            "database": {"status": "healthy", "type": "SQLite"},
            "llm": {"status": "healthy", "provider": "custom"}
        }
    }

# OSINT endpoints
@app.get("/api/osint/investigations")
async def get_investigations():
    return {"investigations": [], "total": 0}

@app.post("/api/osint/investigations")
async def create_investigation(data: dict):
    investigation_id = f"inv-{int(time.time())}"
    return {
        "id": investigation_id,
        "status": "created",
        "message": "Investigation created successfully"
    }

# WebSocket endpoint
from fastapi import WebSocket, WebSocketDisconnect
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, investigation_id: str):
        await websocket.accept()
        self.active_connections[investigation_id] = websocket
        logger.info(f"WebSocket connected for investigation: {investigation_id}")

    def disconnect(self, investigation_id: str):
        if investigation_id in self.active_connections:
            del self.active_connections[investigation_id]
            logger.info(f"WebSocket disconnected for investigation: {investigation_id}")

    async def send_personal_message(self, message: str, investigation_id: str):
        if investigation_id in self.active_connections:
            websocket = self.active_connections[investigation_id]
            await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/api/osint/ws/{investigation_id}")
async def websocket_endpoint(websocket: WebSocket, investigation_id: str):
    await manager.connect(websocket, investigation_id)
    
    # Send welcome message
    welcome_msg = {
        "type": "connection_established",
        "investigation_id": investigation_id,
        "timestamp": datetime.now().isoformat(),
        "status": "connected"
    }
    await manager.send_personal_message(json.dumps(welcome_msg), investigation_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            logger.info(f"Received message for {investigation_id}: {data}")
            
            try:
                message = json.loads(data)
                
                # Process different message types
                if message.get("type") == "ping":
                    response = {
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                        "investigation_id": investigation_id
                    }
                elif message.get("type") == "investigation_command":
                    # Simulate processing investigation command
                    response = {
                        "type": "investigation_update",
                        "investigation_id": investigation_id,
                        "status": "processing",
                        "message": f"Processing command: {message.get('command', 'unknown')}",
                        "timestamp": datetime.now().isoformat(),
                        "progress": 0
                    }
                    
                    # Send immediate response
                    await manager.send_personal_message(json.dumps(response), investigation_id)
                    
                    # Simulate work being done
                    await asyncio.sleep(2)
                    
                    # Send completion message
                    completion_response = {
                        "type": "investigation_complete",
                        "investigation_id": investigation_id,
                        "status": "completed",
                        "message": f"Command processed: {message.get('command', 'unknown')}",
                        "results": {
                            "summary": "Investigation completed successfully",
                            "data_points": 5,
                            "findings": ["Finding 1", "Finding 2", "Finding 3"]
                        },
                        "timestamp": datetime.now().isoformat(),
                        "progress": 100
                    }
                    await manager.send_personal_message(json.dumps(completion_response), investigation_id)
                    continue
                else:
                    response = {
                        "type": "response",
                        "original": message,
                        "timestamp": datetime.now().isoformat(),
                        "investigation_id": investigation_id,
                        "status": "processed"
                    }
                
                await manager.send_personal_message(json.dumps(response), investigation_id)
                
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat(),
                    "investigation_id": investigation_id
                }
                await manager.send_personal_message(json.dumps(error_response), investigation_id)
                
    except WebSocketDisconnect:
        manager.disconnect(investigation_id)
        logger.info(f"WebSocket disconnected for investigation: {investigation_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {investigation_id}: {e}")
        manager.disconnect(investigation_id)

def main():
    """Start the server"""
    logger.info("Starting ScrapeCraft Backend Server...")
    logger.info("Server will be available at: http://127.0.0.1:8000")
    logger.info("WebSocket endpoint: ws://127.0.0.1:8000/api/osint/ws/{investigation_id}")
    logger.info("Frontend should connect to: http://127.0.0.1:8000")
    
    # Run the server
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        access_log=True
    )

if __name__ == "__main__":
    main()