"""
Workflow-related SQLAlchemy models for data persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.sql import func

from .base import Base


class WorkflowState(Base):
    """Workflow state model for storing workflow execution states."""
    
    __tablename__ = "workflow_states"
    
    # Override base fields for this specific table
    workflow_id = Column(String(100), nullable=False, unique=True, index=True)
    workflow_data = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "workflow_data": self.workflow_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Workflow(Base):
    """Workflow model for managing workflow definitions."""
    
    __tablename__ = "workflows"
    
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    config = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class WorkflowTransition(Base):
    """Workflow transition model for tracking state changes."""
    
    __tablename__ = "workflow_transitions"
    
    workflow_id = Column(String(100), nullable=False, index=True)
    from_state = Column(String(100), nullable=False)
    to_state = Column(String(100), nullable=False)
    transition_data = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow transition to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "transition_data": self.transition_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class URLInfo(Base):
    """URL information model for storing URL metadata."""
    
    __tablename__ = "url_info"
    
    url = Column(String(1000), nullable=False)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    url_metadata = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert URL info to dictionary."""
        return {
            "id": self.id,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "metadata": self.url_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class SchemaField(Base):
    """Schema field model for defining data schemas."""
    
    __tablename__ = "schema_fields"
    
    name = Column(String(100), nullable=False)
    field_type = Column(String(50), nullable=False)
    required = Column(Boolean, nullable=False, default=False)
    default_value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert schema field to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "field_type": self.field_type,
            "required": self.required,
            "default_value": self.default_value,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class ApprovalRequest(Base):
    """Approval request model for workflow approvals."""
    
    __tablename__ = "approval_requests"
    
    workflow_id = Column(String(100), nullable=False, index=True)
    requester_id = Column(String(100), nullable=False)
    approver_id = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False, default='pending')
    request_data = Column(JSON, nullable=True)
    response_data = Column(JSON, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert approval request to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "requester_id": self.requester_id,
            "approver_id": self.approver_id,
            "status": self.status,
            "request_data": self.request_data,
            "response_data": self.response_data,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class PipelineExecution(Base):
    """Pipeline execution model for tracking pipeline runs."""
    
    __tablename__ = "pipeline_executions"
    
    pipeline_id = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, default='running')
    config = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pipeline execution to dictionary."""
        return {
            "id": self.id,
            "pipeline_id": self.pipeline_id,
            "status": self.status,
            "config": self.config,
            "result_data": self.result_data,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }