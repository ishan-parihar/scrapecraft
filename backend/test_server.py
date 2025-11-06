#!/usr/bin/env python3
"""
Simple test server to verify backend functionality
"""
import asyncio
import json
import logging
from fastapi import FastAPI
from fastapi.testclient import TestClient
import websockets
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the app
from app.main import app

# Global server state
server_running = False
websocket_handler = None

class SimpleWebSocketHandler:
    def __init__(self):
        self.connections = {}
    
    async def handle_connection(self, websocket):
        """Handle WebSocket connection"""
        path = websocket.path
        logger.info(f"WebSocket connection received: {path}")
        
        try:
            # Extract investigation ID from path
            investigation_id = path.split('/')[-1] if '/' in path else 'default'
            logger.info(f"Connected to investigation: {investigation_id}")
            
            # Store connection
            self.connections[investigation_id] = websocket
            
            # Send welcome message
            welcome_msg = {
                "type": "connection_established",
                "investigation_id": investigation_id,
                "timestamp": time.time(),
                "status": "connected"
            }
            await websocket.send(json.dumps(welcome_msg))
            
            # Handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    logger.info(f"Received message: {data}")
                    
                    # Echo back or process the message
                    response = {
                        "type": "response",
                        "original": data,
                        "timestamp": time.time(),
                        "status": "processed"
                    }
                    await websocket.send(json.dumps(response))
                    
                except json.JSONDecodeError:
                    error_msg = {
                        "type": "error",
                        "message": "Invalid JSON",
                        "timestamp": time.time()
                    }
                    await websocket.send(json.dumps(error_msg))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"WebSocket connection closed for investigation: {investigation_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up connection
            if investigation_id in self.connections:
                del self.connections[investigation_id]

async def start_websocket_server():
    """Start WebSocket server"""
    global websocket_handler
    websocket_handler = SimpleWebSocketHandler()
    
    logger.info("Starting WebSocket server on ws://127.0.0.1:8001")
    async with websockets.serve(websocket_handler.handle_connection, "127.0.0.1", 8001):
        logger.info("WebSocket server running...")
        await asyncio.Future()  # Run forever

def start_http_server():
    """Start HTTP server using FastAPI test client approach"""
    import subprocess
    import sys
    
    # Create a simple HTTP server using subprocess
    logger.info("Starting HTTP server...")
    
    # Use a simple approach - run the server with a different method
    cmd = [
        sys.executable, "-c", 
        """
import uvicorn
from app.main import app
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")
"""
    ]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    logger.info(f"HTTP server started with PID: {process.pid}")
    return process

async def main():
    """Main function to start servers"""
    global server_running
    server_running = True
    
    # Start WebSocket server
    ws_task = asyncio.create_task(start_websocket_server())
    
    # Start HTTP server in a separate thread
    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True
    http_thread.start()
    
    # Wait a bit for servers to start
    await asyncio.sleep(3)
    
    # Test the servers
    logger.info("Testing servers...")
    
    # Test HTTP with TestClient (since we know it works)
    client = TestClient(app)
    try:
        response = client.get('/')
        logger.info(f"HTTP Test: Root endpoint - Status: {response.status_code}")
    except Exception as e:
        logger.error(f"HTTP Test failed: {e}")
    
    # Test WebSocket
    try:
        async with websockets.connect("ws://127.0.0.1:8001/api/osint/ws/test-123") as ws:
            logger.info("WebSocket test: Connected successfully!")
            await ws.send(json.dumps({"type": "test", "message": "Hello"}))
            response = await asyncio.wait_for(ws.recv(), timeout=5.0)
            logger.info(f"WebSocket test: Received - {response}")
    except Exception as e:
        logger.error(f"WebSocket test failed: {e}")
    
    logger.info("Servers are running! Press Ctrl+C to stop.")
    
    try:
        # Keep running
        while server_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server_running = False

if __name__ == "__main__":
    asyncio.run(main())