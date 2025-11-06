"""
WebSocket SQLAlchemy models for data persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from .base import Base


class WebSocketConnection(Base):
    """WebSocket connection model for storing active connections."""
    
    __tablename__ = "websocket_connections"
    
    # Override base fields for this specific table
    connection_id = Column(String(100), nullable=False, unique=True, index=True)
    pipeline_id = Column(String(100), nullable=True, index=True)
    connection_metadata = Column(JSON, nullable=True)
    connected_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    last_activity = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert WebSocket connection to dictionary."""
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "pipeline_id": self.pipeline_id,
            "metadata": self.connection_metadata,
            "connected_at": self.connected_at.isoformat() if self.connected_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None
        }


class ConnectionMetadata(Base):
    """Connection metadata model for storing additional connection data."""
    
    __tablename__ = "connection_metadata"
    
    connection_id = Column(String(100), nullable=False, index=True)
    key = Column(String(100), nullable=False)
    value = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert connection metadata to dictionary."""
        return {
            "id": self.id,
            "connection_id": self.connection_id,
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }