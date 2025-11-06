"""
Comprehensive audit logging service for ScrapeCraft OSINT Platform.

This module provides security-focused audit logging for tracking sensitive operations,
authentication events, and system access patterns.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Union, Callable
import json
import logging
import asyncio
from pathlib import Path
import uuid

from app.config import settings

logger = logging.getLogger(__name__)


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


class AuditSeverity(str, Enum):
    """Severity levels for audit events."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditEvent:
    """Represents a single audit event."""
    
    def __init__(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.id = str(uuid.uuid4())
        self.event_type = event_type
        self.user_id = user_id
        self.username = username
        self.user_role = user_role
        self.resource_id = resource_id
        self.resource_type = resource_type
        self.action = action
        self.severity = severity
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.session_id = session_id
        self.request_id = request_id
        self.details = details or {}
        self.success = success
        self.error_message = error_message
        self.timestamp = timestamp or datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit event to dictionary for logging."""
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "username": self.username,
            "user_role": self.user_role,
            "resource_id": self.resource_id,
            "resource_type": self.resource_type,
            "action": self.action,
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "details": self.details,
            "success": self.success,
            "error_message": self.error_message
        }
    
    def to_json(self) -> str:
        """Convert audit event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """
    Comprehensive audit logging service.
    
    This service handles structured audit logging for security events,
    authentication operations, and sensitive data access.
    """
    
    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file_path = log_file_path or "logs/audit.log"
        self._ensure_log_directory()
        self._setup_audit_logger()
        
        # Initialize database persistence service
        try:
            from .database import DatabasePersistenceService
            self.db_persistence = DatabasePersistenceService()
            self.db_persistence.initialize_database()
            logger.info("AuditLogger database persistence service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize AuditLogger database persistence: {e}")
            self.db_persistence = None
        
        # Fallback to in-memory storage if database fails
        self._event_queue: List[AuditEvent] = []
        self._batch_size = 100
        self._flush_interval = 60  # seconds
        self._last_flush = datetime.now(timezone.utc)
    
    def _ensure_log_directory(self):
        """Ensure the log directory exists."""
        log_path = Path(self.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def _setup_audit_logger(self):
        """Setup the dedicated audit logger."""
        self.audit_logger = logging.getLogger("scrapecraft.audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.audit_logger.handlers[:]:
            self.audit_logger.removeHandler(handler)
        
        # File handler for audit logs
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(
            self.log_file_path,
            maxBytes=100 * 1024 * 1024,  # 100MB
            backupCount=10
        )
        
        # JSON formatter for structured logging
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                try:
                    log_data = json.loads(record.getMessage())
                    return json.dumps(log_data, default=str)
                except (json.JSONDecodeError, AttributeError):
                    return record.getMessage()
        
        file_handler.setFormatter(JsonFormatter())
        self.audit_logger.addHandler(file_handler)
        
        # Prevent propagation to root logger
        self.audit_logger.propagate = False
    
    async def _store_audit_event(self, event: AuditEvent) -> bool:
        """Store audit event using database persistence with fallback."""
        event_data = event.to_dict()
        
        if self.db_persistence:
            try:
                success = await self.db_persistence.store_audit_event(event_data)
                if success:
                    return True
            except Exception as e:
                logger.error(f"Audit database persistence failed, using fallback: {e}")
        
        # Fallback to in-memory storage
        self._event_queue.append(event)
        return True
    
    async def _get_audit_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get audit events using database persistence with fallback."""
        if self.db_persistence:
            try:
                events_data = await self.db_persistence.get_audit_events(limit)
                if events_data:
                    # Reconstruct AuditEvent objects from dictionaries
                    events = []
                    for event_data in events_data:
                        # Filter database fields to match AuditEvent constructor
                        filtered_data = {
                            k: v for k, v in event_data.items() 
                            if k in ['event_type', 'user_id', 'username', 'user_role', 
                                   'resource_id', 'resource_type', 'action', 'severity',
                                   'ip_address', 'user_agent', 'session_id', 'request_id',
                                   'details', 'success', 'error_message', 'timestamp']
                        }
                        # Convert string timestamps back to datetime
                        if filtered_data.get('timestamp') and isinstance(filtered_data['timestamp'], str):
                            from datetime import datetime
                            filtered_data['timestamp'] = datetime.fromisoformat(filtered_data['timestamp'].replace('Z', '+00:00'))
                        
                        # Convert string enums back to enum objects
                        if filtered_data.get('event_type'):
                            filtered_data['event_type'] = AuditEventType(filtered_data['event_type'])
                        if filtered_data.get('severity'):
                            filtered_data['severity'] = AuditSeverity(filtered_data['severity'])
                            
                        events.append(AuditEvent(**filtered_data))
                    return events
            except Exception as e:
                logger.error(f"Audit database retrieval failed, using fallback: {e}")
        
        # Fallback to in-memory storage
        return self._event_queue[-limit:] if limit else self._event_queue.copy()

    async def log_event(self, event: AuditEvent):
        """
        Log an audit event.
        
        Args:
            event: The audit event to log
        """
        try:
            # Store using persistence layer
            await self._store_audit_event(event)
            
            # Log immediately for critical events
            if event.severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
                await self._flush_event(event)
            
            # Flush queue if needed (only for in-memory fallback)
            if not self.db_persistence:
                now = datetime.now(timezone.utc)
                if (len(self._event_queue) >= self._batch_size or
                    (now - self._last_flush).total_seconds() >= self._flush_interval):
                    await self._flush_queue()
        
        except Exception as e:
            # Never let audit logging failures crash the application
            logger.error(f"Failed to log audit event: {e}")
    
    async def _flush_event(self, event: AuditEvent):
        """Flush a single event to the log."""
        try:
            self.audit_logger.info(event.to_json())
        except Exception as e:
            logger.error(f"Failed to flush audit event: {e}")
    
    async def _flush_queue(self):
        """Flush all queued events to the log."""
        if not self._event_queue:
            return
        
        try:
            for event in self._event_queue:
                await self._flush_event(event)
            
            self._event_queue.clear()
            self._last_flush = datetime.now(timezone.utc)
        
        except Exception as e:
            logger.error(f"Failed to flush audit queue: {e}")
    
    async def flush(self):
        """Manually flush the audit queue."""
        await self._flush_queue()
    
    # Convenience methods for common event types
    
    async def log_auth_event(
        self,
        event_type: AuditEventType,
        username: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        error_message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an authentication event."""
        event = AuditEvent(
            event_type=event_type,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            action=event_type.value,  # Set action to event type value
            success=success,
            error_message=error_message,
            details=details,
            severity=AuditSeverity.HIGH if not success else AuditSeverity.MEDIUM
        )
        await self.log_event(event)
    
    async def log_user_management_event(
        self,
        event_type: AuditEventType,
        actor_user_id: str,
        actor_username: str,
        actor_role: str,
        target_user_id: Optional[str] = None,
        target_username: Optional[str] = None,
        success: bool = True,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a user management event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=actor_user_id,
            username=actor_username,
            user_role=actor_role,
            resource_id=target_user_id,
            resource_type="user",
            action=event_type.value,
            success=success,
            ip_address=ip_address,
            details=details or {"target_username": target_username},
            severity=AuditSeverity.HIGH
        )
        await self.log_event(event)
    
    async def log_investigation_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        username: str,
        user_role: str,
        investigation_id: str,
        success: bool = True,
        ip_address: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log an investigation event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            user_role=user_role,
            resource_id=investigation_id,
            resource_type="investigation",
            action=event_type.value,
            success=success,
            ip_address=ip_address,
            details=details,
            severity=AuditSeverity.MEDIUM
        )
        await self.log_event(event)
    
    async def log_security_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Log a security event."""
        event = AuditEvent(
            event_type=event_type,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
            error_message=error_message,
            success=False  # Security events are typically failures/risks
        )
        await self.log_event(event)
    
    async def log_system_event(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a system event."""
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            username=username,
            user_role=user_role,
            resource_type="system",
            action=event_type.value,
            success=success,
            details=details,
            severity=AuditSeverity.LOW
        )
        await self.log_event(event)
    
    async def get_audit_events(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve audit events from the log file.
        
        Note: In production, this should query a proper audit database.
        This is a simplified implementation for demonstration.
        """
        events = []
        
        try:
            with open(self.log_file_path, 'r') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        
                        # Apply filters
                        if event_type and event_data.get("event_type") != event_type.value:
                            continue
                        if user_id and event_data.get("user_id") != user_id:
                            continue
                        if username and event_data.get("username") != username:
                            continue
                        if severity and event_data.get("severity") != severity.value:
                            continue
                        
                        # Time filtering
                        event_time = datetime.fromisoformat(event_data["timestamp"])
                        if start_time and event_time < start_time:
                            continue
                        if end_time and event_time > end_time:
                            continue
                        
                        events.append(event_data)
                        
                        if len(events) >= limit:
                            break
                    
                    except json.JSONDecodeError:
                        continue
        
        except FileNotFoundError:
            logger.warning(f"Audit log file not found: {self.log_file_path}")
        except Exception as e:
            logger.error(f"Error reading audit log: {e}")
        
        # Sort by timestamp (newest first)
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:limit]


# Global audit logger instance
audit_logger = AuditLogger()


# Decorator for automatic audit logging
def audit_action(
    event_type: AuditEventType,
    resource_type: Optional[str] = None,
    get_resource_id: Optional[Callable] = None,
    get_details: Optional[Callable] = None,
    severity: AuditSeverity = AuditSeverity.MEDIUM
):
    """
    Decorator for automatically auditing function calls.
    
    Args:
        event_type: Type of audit event
        resource_type: Type of resource being accessed
        get_resource_id: Function to extract resource ID from function arguments
        get_details: Function to extract additional details from function arguments
        severity: Severity level of the event
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract user information from kwargs (FastAPI dependency injection)
            current_user = kwargs.get('current_user')
            user_role = kwargs.get('user_role')
            
            # Get request information if available
            request = kwargs.get('request')
            ip_address = getattr(request, 'client', {}).get('host') if request and hasattr(request, 'client') else None
            user_agent = getattr(request, 'headers', {}).get('user-agent') if request and hasattr(request, 'headers') else None
            
            # Extract resource ID and details
            resource_id = None
            details = {}
            
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception:
                    pass
            
            if get_details:
                try:
                    details = get_details(*args, **kwargs)
                except Exception:
                    pass
            
            # Create audit event
            event = AuditEvent(
                event_type=event_type,
                user_id=getattr(current_user, 'username', None) if current_user else None,
                username=getattr(current_user, 'username', None) if current_user else None,
                user_role=user_role.value if user_role else None,
                resource_id=resource_id,
                resource_type=resource_type,
                action=event_type.value,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details
            )
            
            # Execute the function and audit the result
            try:
                result = await func(*args, **kwargs)
                event.success = True
                return result
            except Exception as e:
                event.success = False
                event.error_message = str(e)
                raise
            finally:
                # Always log the event
                await audit_logger.log_event(event)
        
        return wrapper
    return decorator