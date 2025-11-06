"""
Audit log models for the ScrapeCraft OSINT Platform.

This module defines database models for storing audit logs and security events.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional
import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Text, JSON, Index
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEventType(str, Enum):
    """Types of audit events."""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth:login:success"
    AUTH_LOGIN_FAILURE = "auth:login:failure"
    AUTH_LOGOUT = "auth:logout"
    AUTH_TOKEN_REFRESH = "auth:token:refresh"
    AUTH_TOKEN_BLACKLIST = "auth:token:blacklist"
    AUTH_PASSWORD_CHANGE = "auth:password:change"
    AUTH_PASSWORD_RESET = "auth:password:reset"
    AUTH_ACCOUNT_LOCK = "auth:account:lock"
    AUTH_ACCOUNT_UNLOCK = "auth:account:unlock"
    
    # User management events
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_ROLE_CHANGE = "user:role:change"
    USER_PERMISSION_CHANGE = "user:permission:change"
    
    # Investigation events
    INVESTIGATION_CREATE = "investigation:create"
    INVESTIGATION_READ = "investigation:read"
    INVESTIGATION_UPDATE = "investigation:update"
    INVESTIGATION_DELETE = "investigation:delete"
    INVESTIGATION_ASSIGN = "investigation:assign"
    INVESTIGATION_UNASSIGN = "investigation:unassign"
    INVESTIGATION_CLASSIFICATION_CHANGE = "investigation:classification:change"
    INVESTIGATION_EXPORT = "investigation:export"
    
    # Evidence events
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_UPDATE = "evidence:update"
    EVIDENCE_DELETE = "evidence:delete"
    EVIDENCE_DOWNLOAD = "evidence:download"
    
    # Report events
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_UPDATE = "report:update"
    REPORT_DELETE = "report:delete"
    REPORT_EXPORT = "report:export"
    REPORT_SHARE = "report:share"
    
    # System events
    SYSTEM_CONFIG_CHANGE = "system:config:change"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"
    SYSTEM_MAINTENANCE = "system:maintenance"
    
    # AI and scraping events
    AI_INVOKE = "ai:invoke"
    AI_CONFIG_CHANGE = "ai:config:change"
    SCRAPING_EXECUTE = "scraping:execute"
    SCRAPING_CONFIG_CHANGE = "scraping:config:change"
    
    # Security events
    SECURITY_BREACH_ATTEMPT = "security:breach:attempt"
    SECURITY_PRIVILEGE_ESCALATION = "security:privilege:escalation"
    SECURITY_SUSPICIOUS_ACTIVITY = "security:suspicious:activity"
    SECURITY_RATE_LIMIT_EXCEEDED = "security:rate_limit:exceeded"


class AuditLog(Base):
    """
    Audit log model for storing security and operation events.
    """
    __tablename__ = "audit_logs"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), index=True)
    
    # User information
    user_id = Column(String(50), nullable=True, index=True)
    username = Column(String(50), nullable=True, index=True)
    user_role = Column(String(20), nullable=True, index=True)
    
    # Resource information
    resource_id = Column(String(50), nullable=True, index=True)
    resource_type = Column(String(50), nullable=True, index=True)
    action = Column(String(100), nullable=True)
    
    # Request information
    ip_address = Column(String(45), nullable=True, index=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    session_id = Column(String(100), nullable=True, index=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Event details
    details = Column(JSON, nullable=True)
    success = Column(Boolean, nullable=False, default=True, index=True)
    error_message = Column(Text, nullable=True)
    
    # Additional metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_audit_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_audit_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_audit_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_audit_resource_timestamp', 'resource_type', 'resource_id', 'timestamp'),
        Index('idx_audit_success_timestamp', 'success', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit log to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "action": self.action,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None
        }


class SecurityEvent(Base):
    """
    Security event model for storing security-specific incidents.
    """
    __tablename__ = "security_events"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    severity = Column(String(10), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), index=True)
    
    # Source information
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    username = Column(String(50), nullable=True, index=True)
    
    # Event details
    details = Column(JSON, nullable=True)
    description = Column(Text, nullable=False)
    
    # Status and resolution
    resolved = Column(Boolean, nullable=False, default=False)
    resolved_by = Column(String(50), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolution_notes = Column(Text, nullable=True)
    
    # Additional metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_security_event_type_timestamp', 'event_type', 'timestamp'),
        Index('idx_security_severity_timestamp', 'severity', 'timestamp'),
        Index('idx_security_ip_timestamp', 'ip_address', 'timestamp'),
        Index('idx_security_resolved_timestamp', 'resolved', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert security event to dictionary."""
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "username": self.username,
            "details": self.details,
            "description": self.description,
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at is not None else None,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at is not None else None
        }


class UserSession(Base):
    """
    User session model for tracking active sessions and devices.
    """
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # User information
    user_id = Column(String(50), nullable=False, index=True)
    username = Column(String(50), nullable=False, index=True)
    
    # Session information
    session_id = Column(String(100), nullable=False, unique=True, index=True)
    token_jti = Column(String(100), nullable=True, unique=True, index=True)  # JWT ID
    refresh_token_jti = Column(String(100), nullable=True, unique=True, index=True)
    
    # Device and location information
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    device_fingerprint = Column(String(100), nullable=True, index=True)
    
    # Timing information
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    last_accessed = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Status
    active = Column(Boolean, nullable=False, default=True, index=True)
    logout_reason = Column(String(50), nullable=True)  # manual, expired, forced, security
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_session_user_active', 'user_id', 'active'),
        Index('idx_session_expires', 'expires_at'),
        Index('idx_session_last_accessed', 'last_accessed'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user session to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "device_fingerprint": self.device_fingerprint,
            "created_at": self.created_at.isoformat() if self.created_at is not None else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed is not None else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at is not None else None,
            "active": self.active,
            "logout_reason": self.logout_reason
        }


class FailedLoginAttempt(Base):
    """
    Failed login attempt model for tracking brute force attempts.
    """
    __tablename__ = "failed_login_attempts"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Attempt information
    username = Column(String(50), nullable=False, index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text, nullable=True)
    
    # Timing
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.now(timezone.utc), index=True)
    
    # Additional details
    details = Column(JSON, nullable=True)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_failed_login_username_timestamp', 'username', 'timestamp'),
        Index('idx_failed_login_ip_timestamp', 'ip_address', 'timestamp'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert failed login attempt to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "timestamp": self.timestamp.isoformat() if self.timestamp is not None else None,
            "details": self.details
        }