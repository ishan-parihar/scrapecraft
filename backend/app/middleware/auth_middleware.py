"""
Enhanced authentication middleware for ScrapeCraft OSINT Platform.

This middleware provides comprehensive authentication features including:
- JWT token validation and refresh
- Rate limiting for authentication endpoints
- Account lockout after failed attempts
- Session management and security monitoring
- Audit logging integration
"""

from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
import redis
import hashlib
import json
import asyncio
from collections import defaultdict
import logging
from enum import Enum

from app.config import settings
# from app.services.audit_logger import audit_logger, AuditEventType, AuditSeverity  # Avoid circular import for now

logger = logging.getLogger(__name__)


# Simple classes to avoid circular imports
class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class UserInDB:
    def __init__(self, username: str, **kwargs):
        self.username = username
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_user_role(user) -> UserRole:
    """Get user role - simplified version."""
    role_mapping = {
        "testuser": UserRole.ADMIN,
        "admin": UserRole.ADMIN,
        "analyst": UserRole.ANALYST,
        "viewer": UserRole.VIEWER,
    }
    return role_mapping.get(user.username, UserRole.VIEWER)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user from real database."""
    from app.services.user_database import get_user as get_user_from_db
    user_dict = get_user_from_db(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None


# Mock audit logger to avoid circular import
class MockAuditLogger:
    def log_event(self, *args, **kwargs):
        pass

audit_logger = MockAuditLogger()

# Redis client for token blacklist and rate limiting
# Note: Using sync Redis for now to avoid async complications
# In production, use redis.asyncio for better performance
redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Rate limiting configuration
RATE_LIMITS = {
    "login": {"requests": 5, "window": 300},  # 5 login attempts per 5 minutes
    "register": {"requests": 3, "window": 300},  # 3 registrations per 5 minutes
    "password_reset": {"requests": 3, "window": 3600},  # 3 password resets per hour
    "token_refresh": {"requests": 10, "window": 3600},  # 10 token refreshes per hour
}

# Account lockout configuration
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = 900  # 15 minutes


class AuthenticationMiddleware:
    """
    Enhanced authentication middleware with security features.
    """
    
    def __init__(self):
        self._failed_attempts = defaultdict(list)
        self._rate_limit_cache = defaultdict(list)
    
    async def check_rate_limit(
        self,
        key: str,
        ip_address: str,
        endpoint_type: str
    ) -> bool:
        """
        Check if the request exceeds rate limits.
        
        Args:
            key: Unique key for rate limiting (e.g., username or IP)
            ip_address: Client IP address
            endpoint_type: Type of endpoint (login, register, etc.)
            
        Returns:
            True if request is allowed, False otherwise
        """
        try:
            config = RATE_LIMITS.get(endpoint_type, {"requests": 10, "window": 300})
            redis_key = f"rate_limit:{endpoint_type}:{key}"
            
# Get current request count
            current_count = redis_client.get(redis_key)
            if current_count is None:
                # First request in window
                redis_client.setex(redis_key, config["window"], 1)
                return True
            
            current_count = int(current_count)
            if current_count >= config["requests"]:
                # Rate limit exceeded
                await audit_logger.log_security_event(
                    event_type=AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED,
                    severity=AuditSeverity.MEDIUM,
                    ip_address=ip_address,
                    details={
                        "endpoint_type": endpoint_type,
                        "key": key,
                        "current_count": current_count,
                        "limit": config["requests"]
                    }
                )
                return False
            
            # Increment counter
            redis_client.incr(redis_key)
            return True
            
            current_count = int(current_count)
            if current_count >= config["requests"]:
                # Rate limit exceeded
                await audit_logger.log_security_event(
                    event_type=AuditEventType.SECURITY_RATE_LIMIT_EXCEEDED,
                    severity=AuditSeverity.MEDIUM,
                    ip_address=ip_address,
                    details={
                        "endpoint_type": endpoint_type,
                        "key": key,
                        "current_count": current_count,
                        "limit": config["requests"]
                    }
                )
                return False
            
            # Increment counter
            redis_client.incr(redis_key)
            return True
        
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiting fails
            return True
    
    async def check_account_lockout(self, username: str, ip_address: str) -> bool:
        """
        Check if account is locked due to failed attempts.
        
        Args:
            username: Username to check
            ip_address: Client IP address
            
        Returns:
            True if account is locked, False otherwise
        """
        try:
            lockout_key = f"account_lockout:{username}"
            lockout_data = redis_client.get(lockout_key)
            
            if lockout_data:
                lockout_info = json.loads(lockout_data)
                lockout_time = datetime.fromisoformat(lockout_info["locked_at"])
                
                if datetime.now(timezone.utc) < lockout_time + timedelta(seconds=LOCKOUT_DURATION):
                    # Account is still locked
                    await audit_logger.log_security_event(
                        event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                        severity=AuditSeverity.HIGH,
                        ip_address=ip_address,
                        details={
                            "username": username,
                            "reason": "account_locked",
                            "locked_at": lockout_info["locked_at"],
                            "failed_attempts": lockout_info["failed_attempts"]
                        }
                    )
                    return True
                else:
                    # Lockout expired, remove it
                    redis_client.delete(lockout_key)
            
            return False
        
        except Exception as e:
            logger.error(f"Account lockout check error: {e}")
            return False
    
    async def record_failed_attempt(
        self,
        username: str,
        ip_address: str,
        user_agent: Optional[str] = None
    ):
        """
        Record a failed login attempt and lock account if necessary.
        
        Args:
            username: Username that failed to login
            ip_address: Client IP address
            user_agent: Client user agent
        """
        try:
            # Record failed attempt in Redis
            failed_key = f"failed_attempts:{username}"
            redis_client.lpush(failed_key, json.dumps({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent
            }))
            
            # Set expiration and trim list
            redis_client.expire(failed_key, 3600)  # Keep for 1 hour
            redis_client.ltrim(failed_key, 0, MAX_FAILED_ATTEMPTS - 1)
            
            # Check if account should be locked
            failed_count = redis_client.llen(failed_key)
            if failed_count >= MAX_FAILED_ATTEMPTS:
                # Lock the account
                lockout_key = f"account_lockout:{username}"
                lockout_data = {
                    "locked_at": datetime.now(timezone.utc).isoformat(),
                    "failed_attempts": failed_count,
                    "ip_address": ip_address
                }
                redis_client.setex(
                    lockout_key,
                    LOCKOUT_DURATION,
                    json.dumps(lockout_data)
                )
                
                await audit_logger.log_security_event(
                    event_type=AuditEventType.AUTH_ACCOUNT_LOCK,
                    severity=AuditSeverity.HIGH,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={
                        "username": username,
                        "failed_attempts": failed_count,
                        "lockout_duration": LOCKOUT_DURATION
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed attempt recording error: {e}")
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """
        Check if a JWT token is blacklisted.
        
        Args:
            token_jti: JWT ID of the token
            
        Returns:
            True if token is blacklisted, False otherwise
        """
        try:
            blacklist_key = f"token_blacklist:{token_jti}"
            return redis_client.exists(blacklist_key)
        except Exception as e:
            logger.error(f"Token blacklist check error: {e}")
            return False
    
    async def blacklist_token(
        self,
        token_jti: str,
        expires_at: datetime,
        user_id: str,
        reason: str = "logout"
    ):
        """
        Add a JWT token to the blacklist.
        
        Args:
            token_jti: JWT ID of the token
            expires_at: Token expiration time
            user_id: User ID who owns the token
            reason: Reason for blacklisting
        """
        try:
            blacklist_key = f"token_blacklist:{token_jti}"
            blacklist_data = {
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "user_id": user_id,
                "reason": reason
            }
            
            # Set blacklist entry with expiration
            ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                redis_client.setex(
                    blacklist_key,
                    ttl,
                    json.dumps(blacklist_data)
                )
                
                await audit_logger.log_auth_event(
                    event_type=AuditEventType.AUTH_TOKEN_BLACKLIST,
                    username=user_id,
                    success=True,
                    details={
                        "token_jti": token_jti,
                        "reason": reason,
                        "expires_at": expires_at.isoformat()
                    }
                )
        
        except Exception as e:
            logger.error(f"Token blacklisting error: {e}")
    
    async def create_refresh_token(
        self,
        user: UserInDB,
        access_token_jti: str,
        ip_address: str,
        user_agent: Optional[str] = None
    ) -> str:
        """
        Create a refresh token for the user.
        
        Args:
            user: User to create refresh token for
            access_token_jti: JWT ID of the access token
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Refresh token string
        """
        try:
            # Generate refresh token with longer expiration
            refresh_expires = datetime.utcnow() + timedelta(days=30)
            refresh_jti = str(hashlib.sha256(f"{user.username}{datetime.utcnow().isoformat()}".encode()).hexdigest())
            
            refresh_payload = {
                "sub": user.username,
                "jti": refresh_jti,
                "access_jti": access_token_jti,
                "type": "refresh",
                "exp": refresh_expires.timestamp()
            }
            
            refresh_token = jwt.encode(
                refresh_payload,
                settings.JWT_SECRET,
                algorithm=settings.JWT_ALGORITHM
            )
            
            # Store refresh token metadata
            refresh_key = f"refresh_token:{refresh_jti}"
            refresh_data = {
                "user_id": user.username,
                "access_jti": access_token_jti,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": refresh_expires.isoformat()
            }
            
            redis_client.setex(
                refresh_key,
                int(timedelta(days=30).total_seconds()),
                json.dumps(refresh_data)
            )
            
            return refresh_token
        
        except Exception as e:
            logger.error(f"Refresh token creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create refresh token"
            )
    
    async def validate_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Validate and decode a refresh token.
        
        Args:
            refresh_token: Refresh token to validate
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            # Decode the token
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Validate token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if refresh token exists in Redis
            refresh_key = f"refresh_token:{payload['jti']}"
            refresh_data = redis_client.get(refresh_key)
            
            if not refresh_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found"
                )
            
            return payload
        
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid refresh token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Refresh token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token validation failed"
            )


# Global authentication middleware instance
auth_middleware = AuthenticationMiddleware()


# Enhanced dependency for getting current user with RBAC and audit logging
async def get_current_user_with_permissions(
    request: Request,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/token"))
) -> tuple[UserInDB, UserRole]:
    """
    Get current user with role permissions and comprehensive security checks.
    
    Args:
        request: FastAPI request object
        token: JWT access token
        
    Returns:
        Tuple of (User, UserRole)
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        username = payload.get("sub")
        token_jti = payload.get("jti")
        
        if username is None or token_jti is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        # Check if token is blacklisted
        if await auth_middleware.is_token_blacklisted(token_jti):
            await audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                severity=AuditSeverity.HIGH,
                ip_address=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                details={
                    "username": username,
                    "reason": "blacklisted_token_used"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked"
            )
        
        # Get user
        user = get_user(username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if user.disabled:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is disabled"
            )
        
        # Get user role
        user_role = get_user_role(user)
        
        # Log successful authentication
        await audit_logger.log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            username=username,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        return user, user_role
    
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except JWTError as e:
        await audit_logger.log_security_event(
            event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
            severity=AuditSeverity.MEDIUM,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


# Rate limiting decorator for authentication endpoints
def rate_limit_auth(endpoint_type: str):
    """
    Decorator to apply rate limiting to authentication endpoints.
    
    Args:
        endpoint_type: Type of endpoint (login, register, etc.)
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract request and username/IP from args/kwargs
            request = None
            username = None
            
            # Try to get request from kwargs
            if 'request' in kwargs:
                request = kwargs['request']
            else:
                # Try to get request from args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                return await func(*args, **kwargs)
            
            ip_address = request.client.host if request.client else "unknown"
            
            # Try to get username from form data or JSON body
            if 'form_data' in kwargs:
                username = kwargs['form_data'].username
            elif 'user' in kwargs:
                username = kwargs['user'].username
            
            # Use IP address as key if no username
            key = username or ip_address
            
            # Check rate limit
            if not await auth_middleware.check_rate_limit(key, ip_address, endpoint_type):
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded for {endpoint_type}. Please try again later."
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator