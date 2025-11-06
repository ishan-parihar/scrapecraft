"""
Audit log SQLAlchemy models for data persistence.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from .base import Base


class AuditLog(Base):
    """Audit log model for tracking security events."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    severity = Column(String(20), nullable=False, default='info')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        timestamp_val = self.timestamp
        if timestamp_val and hasattr(timestamp_val, 'isoformat'):
            timestamp_val = timestamp_val.isoformat()
        
        return {
            "id": self.id,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "details": self.details,
            "timestamp": timestamp_val,
            "severity": self.severity
        }


class UserSession(Base):
    """User session model for tracking active sessions."""
    
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    last_activity = Column(DateTime, nullable=False, default=func.now())
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    session_data = Column(Text, nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user session to dictionary."""
        created_at_val = self.created_at
        if created_at_val and hasattr(created_at_val, 'isoformat'):
            created_at_val = created_at_val.isoformat()
            
        last_activity_val = self.last_activity
        if last_activity_val and hasattr(last_activity_val, 'isoformat'):
            last_activity_val = last_activity_val.isoformat()
            
        expires_at_val = self.expires_at
        if expires_at_val and hasattr(expires_at_val, 'isoformat'):
            expires_at_val = expires_at_val.isoformat()
        
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "created_at": created_at_val,
            "last_activity": last_activity_val,
            "expires_at": expires_at_val,
            "is_active": self.is_active,
            "session_data": self.session_data
        }


class SystemEvent(Base):
    """System event model for tracking system-level events."""
    
    __tablename__ = "system_events"
    
    event_type = Column(String(100), nullable=False, index=True)
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default='info')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system event to dictionary."""
        created_at_val = self.created_at
        if created_at_val and hasattr(created_at_val, 'isoformat'):
            created_at_val = created_at_val.isoformat()
            
        updated_at_val = self.updated_at
        if updated_at_val and hasattr(updated_at_val, 'isoformat'):
            updated_at_val = updated_at_val.isoformat()
        
        return {
            "id": self.id,
            "event_type": self.event_type,
            "source": self.source,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
            "created_at": created_at_val,
            "updated_at": updated_at_val
        }