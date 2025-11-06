"""
Role-Based Access Control (RBAC) implementation for ScrapeCraft OSINT Platform.

This module provides comprehensive role and permission management for securing
investigation operations and system resources.
"""

from enum import Enum
from typing import List, Dict, Set, Optional, Union, TYPE_CHECKING
from functools import wraps
from fastapi import HTTPException, Depends, status
import logging

if TYPE_CHECKING:
    from app.api.auth import get_current_active_user, UserInDB

logger = logging.getLogger(__name__)


# Simple UserInDB class for runtime use to avoid circular imports
class UserInDB:
    def __init__(self, username: str, **kwargs):
        self.username = username
        for key, value in kwargs.items():
            setattr(self, key, value)


class UserRole(str, Enum):
    """User roles with hierarchical permissions."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    """System permissions."""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    USER_LIST = "user:list"
    
    # Investigation management
    INVESTIGATION_CREATE = "investigation:create"
    INVESTIGATION_READ = "investigation:read"
    INVESTIGATION_UPDATE = "investigation:update"
    INVESTIGATION_DELETE = "investigation:delete"
    INVESTIGATION_LIST = "investigation:list"
    INVESTIGATION_ADMIN = "investigation:admin"
    INVESTIGATION_ASSIGN = "investigation:assign"
    
    # Evidence management
    EVIDENCE_CREATE = "evidence:create"
    EVIDENCE_READ = "evidence:read"
    EVIDENCE_UPDATE = "evidence:update"
    EVIDENCE_DELETE = "evidence:delete"
    EVIDENCE_LIST = "evidence:list"
    
    # Report management
    REPORT_CREATE = "report:create"
    REPORT_READ = "report:read"
    REPORT_UPDATE = "report:update"
    REPORT_DELETE = "report:delete"
    REPORT_LIST = "report:list"
    REPORT_EXPORT = "report:export"
    
    # System management
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOGS = "system:logs"
    SYSTEM_HEALTH = "system:health"
    SYSTEM_MONITOR = "system:monitor"
    
    # AI and scraping
    AI_INVOKE = "ai:invoke"
    AI_CONFIGURE = "ai:configure"
    SCRAPING_EXECUTE = "scraping:execute"
    SCRAPING_CONFIGURE = "scraping:configure"


# Role-Permission Matrix
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.ADMIN: {
        # Full user management
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE,
        Permission.USER_DELETE, Permission.USER_LIST,
        
        # Full investigation management
        Permission.INVESTIGATION_CREATE, Permission.INVESTIGATION_READ,
        Permission.INVESTIGATION_UPDATE, Permission.INVESTIGATION_DELETE,
        Permission.INVESTIGATION_LIST, Permission.INVESTIGATION_ADMIN,
        Permission.INVESTIGATION_ASSIGN,
        
        # Full evidence management
        Permission.EVIDENCE_CREATE, Permission.EVIDENCE_READ,
        Permission.EVIDENCE_UPDATE, Permission.EVIDENCE_DELETE,
        Permission.EVIDENCE_LIST,
        
        # Full report management
        Permission.REPORT_CREATE, Permission.REPORT_READ,
        Permission.REPORT_UPDATE, Permission.REPORT_DELETE,
        Permission.REPORT_LIST, Permission.REPORT_EXPORT,
        
        # Full system access
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_LOGS,
        Permission.SYSTEM_HEALTH, Permission.SYSTEM_MONITOR,
        
        # Full AI and scraping access
        Permission.AI_INVOKE, Permission.AI_CONFIGURE,
        Permission.SCRAPING_EXECUTE, Permission.SCRAPING_CONFIGURE,
    },
    
    UserRole.ANALYST: {
        # Limited user access (own profile only)
        Permission.USER_READ,
        
        # Investigation management (no admin or delete)
        Permission.INVESTIGATION_CREATE, Permission.INVESTIGATION_READ,
        Permission.INVESTIGATION_UPDATE, Permission.INVESTIGATION_LIST,
        
        # Evidence management
        Permission.EVIDENCE_CREATE, Permission.EVIDENCE_READ,
        Permission.EVIDENCE_UPDATE, Permission.EVIDENCE_LIST,
        
        # Report management (limited)
        Permission.REPORT_CREATE, Permission.REPORT_READ,
        Permission.REPORT_UPDATE, Permission.REPORT_LIST,
        Permission.REPORT_EXPORT,
        
        # Basic system access
        Permission.SYSTEM_HEALTH,
        
        # AI and scraping access
        Permission.AI_INVOKE, Permission.SCRAPING_EXECUTE,
    },
    
    UserRole.VIEWER: {
        # Very limited user access (own profile only)
        Permission.USER_READ,
        
        # Read-only investigation access (assigned only)
        Permission.INVESTIGATION_READ, Permission.INVESTIGATION_LIST,
        
        # Read-only evidence access
        Permission.EVIDENCE_READ, Permission.EVIDENCE_LIST,
        
        # Read-only report access
        Permission.REPORT_READ, Permission.REPORT_LIST,
        
        # Basic system access
        Permission.SYSTEM_HEALTH,
    }
}


class RBACService:
    """Service for managing Role-Based Access Control."""
    
    @staticmethod
    def get_role_permissions(role: UserRole) -> Set[Permission]:
        """Get all permissions for a given role."""
        return ROLE_PERMISSIONS.get(role, set())
    
    @staticmethod
    def has_permission(user_role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission."""
        return permission in ROLE_PERMISSIONS.get(user_role, set())
    
    @staticmethod
    def has_any_permission(user_role: UserRole, permissions: List[Permission]) -> bool:
        """Check if a role has any of the specified permissions."""
        role_permissions = ROLE_PERMISSIONS.get(user_role, set())
        return any(perm in role_permissions for perm in permissions)
    
    @staticmethod
    def has_all_permissions(user_role: UserRole, permissions: List[Permission]) -> bool:
        """Check if a role has all of the specified permissions."""
        role_permissions = ROLE_PERMISSIONS.get(user_role, set())
        return all(perm in role_permissions for perm in permissions)
    
    @staticmethod
    def can_access_investigation(
        user_role: UserRole,
        user_id: str,
        investigation_owner_id: Optional[str],
        assigned_users: List[str],
        action: str
    ) -> bool:
        """
        Check if a user can access a specific investigation.
        
        Args:
            user_role: User's role
            user_id: User's ID
            investigation_owner_id: Owner of the investigation
            assigned_users: List of assigned user IDs
            action: Action being performed (read, update, delete, admin)
            
        Returns:
            True if access is allowed, False otherwise
        """
        # Admins can access everything
        if user_role == UserRole.ADMIN:
            return True
        
        # Viewers can only read assigned investigations
        if user_role == UserRole.VIEWER:
            if action != "read":
                return False
            return user_id in assigned_users
        
        # Analysts can access their own investigations and assigned ones
        if user_role == UserRole.ANALYST:
            # Can always read their own investigations
            if action == "read" and user_id == investigation_owner_id:
                return True
            
            # Can update their own investigations (but not delete or admin)
            if action in ["read", "update"] and user_id == investigation_owner_id:
                return True
            
            # Can read/update assigned investigations
            if action in ["read", "update"] and user_id in assigned_users:
                return True
            
            return False
        
        return False


def get_user_role(user: UserInDB) -> UserRole:
    """Get the role for a user. In a real implementation, this would come from the database."""
    # For now, use a simple convention or default to VIEWER
    # In production, this would be stored in the user record
    role_mapping = {
        "testuser": UserRole.ADMIN,  # Default test user is admin
        "admin": UserRole.ADMIN,
        "analyst": UserRole.ANALYST,
        "viewer": UserRole.VIEWER,
    }
    return role_mapping.get(user.username, UserRole.VIEWER)


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission.
    
    Usage:
        @require_permission(Permission.INVESTIGATION_CREATE)
        async def create_investigation(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get current_user from kwargs or FastAPI dependency injection
            current_user = kwargs.get('current_user')
            if not current_user:
                # This will work if the function has FastAPI dependency injection
                try:
                    from fastapi import Request
                    request = next(arg for arg in args if isinstance(arg, Request))
                    # This is a simplified approach - in practice, you'd use FastAPI's dependency system
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                except StopIteration:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
            
            user_role = get_user_role(current_user)
            
            if not RBACService.has_permission(user_role, permission):
                logger.warning(
                    f"Access denied: user {current_user.username} (role: {user_role}) "
                    f"attempted to access {permission.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value}"
                )
            
            # Add role to kwargs for downstream use
            kwargs['user_role'] = user_role
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @require_any_permission([Permission.INVESTIGATION_READ, Permission.INVESTIGATION_ADMIN])
        async def get_investigation(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = get_user_role(current_user)
            
            if not RBACService.has_any_permission(user_role, permissions):
                logger.warning(
                    f"Access denied: user {current_user.username} (role: {user_role}) "
                    f"attempted to access one of {[p.value for p in permissions]}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: requires one of {[p.value for p in permissions]}"
                )
            
            kwargs['user_role'] = user_role
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(role: UserRole):
    """
    Decorator to require a specific role.
    
    Usage:
        @require_role(UserRole.ADMIN)
        async def admin_function(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            user_role = get_user_role(current_user)
            
            if user_role != role:
                logger.warning(
                    f"Access denied: user {current_user.username} (role: {user_role}) "
                    f"attempted to access role-protected resource requiring {role.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied: requires {role.value} role"
                )
            
            kwargs['user_role'] = user_role
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Moved to auth.py to avoid circular import
# def get_current_user_with_role(...


# FastAPI dependency helpers - moved to auth.py to avoid circular import
# def require_permission_dependency(...


# Moved to auth.py to avoid circular import
# def require_role_dependency(...)