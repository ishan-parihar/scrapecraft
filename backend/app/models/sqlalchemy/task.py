"""
Task-related SQLAlchemy models for data persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from .base import Base


class TaskResult(Base):
    """Task result model for storing execution results."""
    
    __tablename__ = "task_results"
    
    # Override base fields for this specific table
    task_id = Column(String(100), nullable=False, unique=True, index=True)
    task_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task result to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "task_data": self.task_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Task(Base):
    """Task model for storing task definitions."""
    
    __tablename__ = "tasks"
    
    task_id = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, default='pending')
    config = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }