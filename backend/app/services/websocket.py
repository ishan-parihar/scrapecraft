from fastapi import WebSocket
from typing import Dict, List, Any, Optional
import json
import asyncio
import logging
from datetime import datetime
from app.config import settings

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time communication."""
    
    def __init__(self):
        # Initialize database persistence service
        try:
            from .database import DatabasePersistenceService
            self.db_persistence = DatabasePersistenceService()
            self.db_persistence.initialize_database()
            logger.info("WebSocket database persistence service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket database persistence: {e}")
            self.db_persistence = None
        
        # Fallback to in-memory storage if database fails
        # Store active connections by pipeline_id
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Store pipeline states
        self.pipeline_states: Dict[str, Dict] = {}
        # Store connection metadata using connection IDs as strings
        self.connection_metadata: Dict[str, Dict] = {}
        # Health status
        self.is_healthy = True
        self.last_health_check = datetime.utcnow()
    
    async def _store_websocket_connection(self, connection_id: str, pipeline_id: str, metadata: Dict[str, Any]) -> bool:
        """Store WebSocket connection data using database persistence with fallback."""
        if self.db_persistence:
            try:
                success = await self.db_persistence.store_websocket_connection(connection_id, pipeline_id, metadata)
                if success:
                    return True
            except Exception as e:
                logger.error(f"WebSocket database persistence failed, using fallback: {e}")
        
        # Fallback to in-memory storage
        self.connection_metadata[connection_id] = metadata
        return True
    
    async def _get_websocket_connections(self, pipeline_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get WebSocket connections using database persistence with fallback."""
        if self.db_persistence:
            try:
                connections = await self.db_persistence.get_websocket_connections(pipeline_id)
                if connections:
                    return connections
            except Exception as e:
                logger.error(f"WebSocket database retrieval failed, using fallback: {e}")
        
        # Fallback to in-memory storage
        if pipeline_id:
            return [
                {"connection_id": conn_id, "metadata": metadata}
                for conn_id, metadata in self.connection_metadata.items()
                if metadata.get("pipeline_id") == pipeline_id
            ]
        return [
            {"connection_id": conn_id, "metadata": metadata}
            for conn_id, metadata in self.connection_metadata.items()
        ]
    
    async def _remove_websocket_connection(self, connection_id: str) -> bool:
        """Remove WebSocket connection data using database persistence with fallback."""
        if self.db_persistence:
            try:
                success = await self.db_persistence.remove_websocket_connection(connection_id)
                if success:
                    # Also remove from fallback memory
                    if connection_id in self.connection_metadata:
                        del self.connection_metadata[connection_id]
                    return True
            except Exception as e:
                logger.error(f"WebSocket database deletion failed, using fallback: {e}")
        
        # Fallback to in-memory storage
        if connection_id in self.connection_metadata:
            del self.connection_metadata[connection_id]
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on WebSocket manager."""
        try:
            total_connections = sum(len(conns) for conns in self.active_connections.values())
            active_pipelines = len(self.active_connections)
            
            # Test connection health by checking if any connections are stale
            stale_connections = 0
            for pipeline_id, connections in self.active_connections.items():
                for conn in connections:
                    connection_id = f"{pipeline_id}_{id(conn)}"
                    metadata = self.connection_metadata.get(connection_id, {})
                    last_ping = metadata.get("last_ping")
                    if last_ping:
                        time_diff = (datetime.utcnow() - last_ping).total_seconds()
                        if time_diff > 300:  # 5 minutes
                            stale_connections += 1
            
            health_status = {
                "status": "healthy" if stale_connections == 0 else "degraded",
                "total_connections": total_connections,
                "active_pipelines": active_pipelines,
                "stale_connections": stale_connections,
                "last_health_check": self.last_health_check.isoformat()
            }
            
            self.last_health_check = datetime.utcnow()
            return health_status
            
        except Exception as e:
            logger.error(f"WebSocket health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "last_health_check": self.last_health_check.isoformat()
            }
    
    async def cleanup_stale_connections(self):
        """Remove stale WebSocket connections."""
        try:
            current_time = datetime.utcnow()
            connections_to_remove = []
            
            for pipeline_id, connections in list(self.active_connections.items()):
                for connection in connections:
                    connection_id = f"{pipeline_id}_{id(connection)}"
                    metadata = self.connection_metadata.get(connection_id, {})
                    last_ping = metadata.get("last_ping")
                    if last_ping:
                        time_diff = (current_time - last_ping).total_seconds()
                        if time_diff > 300:  # 5 minutes
                            connections_to_remove.append((pipeline_id, connection))
            
            # Remove stale connections
            for pipeline_id, connection in connections_to_remove:
                try:
                    await connection.close(code=1000, reason="Stale connection cleanup")
                    await self.disconnect(connection, pipeline_id)
                    logger.info(f"Cleaned up stale connection for pipeline {pipeline_id}")
                except Exception as e:
                    logger.error(f"Error closing stale connection: {e}")
                    # Force remove if close fails
                    await self.disconnect(connection, pipeline_id)
                    
        except Exception as e:
            logger.error(f"Error during stale connection cleanup: {e}")
    
    async def connect(self, websocket: WebSocket, pipeline_id: str):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        
        if pipeline_id not in self.active_connections:
            self.active_connections[pipeline_id] = []
            self.pipeline_states[pipeline_id] = {
                "urls": [],
                "schema": {},
                "generated_code": "",
                "status": "connected"
            }
        
        self.active_connections[pipeline_id].append(websocket)
        
        # Store connection metadata
        connection_id = f"{pipeline_id}_{id(websocket)}"
        metadata = {
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow(),
            "pipeline_id": pipeline_id,
            "websocket_id": id(websocket)
        }
        await self._store_websocket_connection(connection_id, pipeline_id, metadata)
        
        # Send initial state
        await self.send_personal_message({
            "type": "connection",
            "message": "Connected to pipeline",
            "pipeline_id": pipeline_id,
            "state": self.pipeline_states[pipeline_id]
        }, websocket)
    
    async def disconnect(self, websocket: WebSocket, pipeline_id: str):
        """Remove a WebSocket connection."""
        if pipeline_id in self.active_connections:
            try:
                self.active_connections[pipeline_id].remove(websocket)
            except ValueError:
                pass  # Connection already removed
            
            # Clean up connection metadata using persistence layer
            connection_id = f"{pipeline_id}_{id(websocket)}"
            await self._remove_websocket_connection(connection_id)
            
            # Clean up if no more connections
            if not self.active_connections[pipeline_id]:
                del self.active_connections[pipeline_id]
                if pipeline_id in self.pipeline_states:
                    del self.pipeline_states[pipeline_id]
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        await websocket.send_json({
            **message,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def broadcast(self, message: Dict, pipeline_id: str):
        """Broadcast a message to all connections for a pipeline."""
        if pipeline_id in self.active_connections:
            # Create tasks for all connections
            tasks = []
            for connection in self.active_connections[pipeline_id]:
                tasks.append(connection.send_json({
                    **message,
                    "timestamp": datetime.utcnow().isoformat()
                }))
            
            # Send to all connections concurrently
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def process_message(self, pipeline_id: str, data: Dict) -> Dict:
        """Process incoming WebSocket messages."""
        message_type = data.get("type", "chat")
        
        if message_type == "chat":
            # Process through the workflow manager
            from app.services.workflow_manager import get_workflow_manager
            
            workflow_manager = get_workflow_manager(self)
            result = await workflow_manager.process_message(
                pipeline_id=pipeline_id,
                message=data.get("message", ""),
                user=data.get("user", "user")
            )
            
            return {
                "type": "response",
                "response": result["response"],
                "workflow_state": result["workflow_state"],
                "requires_action": result["requires_action"]
            }
        
        elif message_type == "state_request":
            # Return current workflow state
            from app.services.workflow_manager import get_workflow_manager
            
            workflow_manager = get_workflow_manager(self)
            workflow = await workflow_manager.get_workflow(pipeline_id)
            
            if workflow:
                return {
                    "type": "workflow_state",
                    "workflow": workflow.model_dump(mode='json')
                }
            else:
                # Create initial workflow for new pipelines
                workflow = await workflow_manager.create_workflow(pipeline_id, data.get("user", "user"))
                return {
                    "type": "workflow_state",
                    "workflow": workflow.model_dump(mode='json')
                }
        
        elif message_type == "approval":
            # Handle approval response
            from app.services.workflow_manager import get_workflow_manager
            
            approval_id = data.get("approval_id")
            if not approval_id:
                return {
                    "type": "error",
                    "message": "approval_id is required for approval messages"
                }
            
            workflow_manager = get_workflow_manager(self)
            workflow = await workflow_manager.approve_action(
                pipeline_id=pipeline_id,
                approval_id=approval_id,
                approved=data.get("approved", False),
                user=data.get("user", "user")
            )
            
            return {
                "type": "approval_processed",
                "workflow": workflow.model_dump(mode='json')
            }
        
        elif message_type == "ping":
            # Health check - update last ping time
            # Note: We don't have direct access to the websocket object here, 
            # so we'll update on the next message or in a separate ping handler
            return {"type": "pong"}
        
        else:
            return {
                "type": "error",
                "message": f"Unknown message type: {message_type}"
            }
    
    async def stream_execution_updates(
        self,
        pipeline_id: str,
        url: str,
        status: str,
        data: Any = None,
        error: Optional[str] = None
    ):
        """Stream execution updates to connected clients."""
        await self.broadcast({
            "type": "execution_update",
            "url": url,
            "status": status,
            "data": data,
            "error": error
        }, pipeline_id)