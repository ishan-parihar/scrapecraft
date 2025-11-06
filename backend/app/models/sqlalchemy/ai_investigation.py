"""
AI Investigation SQLAlchemy models for data persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func

from .base import Base


class AIInvestigation(Base):
    """AI Investigation model for storing AI-driven investigation data."""
    
    __tablename__ = "ai_investigations"
    
    investigation_id = Column(String(100), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default='active')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert AI investigation to dictionary."""
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "title": self.title,
            "description": self.description,
            "config": self.config,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class AgentExecutionLog(Base):
    """Agent execution log model for tracking agent activity."""
    
    __tablename__ = "agent_execution_logs"
    
    investigation_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False)
    execution_data = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default='running')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent execution log to dictionary."""
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "agent_name": self.agent_name,
            "execution_data": self.execution_data,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class InvestigationState(Base):
    """Investigation state model for storing investigation states."""
    
    __tablename__ = "investigation_states"
    
    investigation_id = Column(String(100), nullable=False, unique=True, index=True)
    state_data = Column(Text, nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert investigation state to dictionary."""
        return {
            "id": self.id,
            "investigation_id": self.investigation_id,
            "state_data": self.state_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }