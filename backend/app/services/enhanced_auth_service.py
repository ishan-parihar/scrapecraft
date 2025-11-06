"""
Enhanced Authentication Service for ScrapeCraft OSINT Platform

This module provides secure authentication with comprehensive security features:
- Secure password management with bcrypt
- JWT token management with blacklisting
- Rate limiting and account lockout
- Input validation and sanitization
- Security audit logging
- Role-based access control (RBAC)
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
import redis
import logging

from fastapi import HTTPException, Request, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt, ExpiredSignatureError
from pydantic import BaseModel, Field, validator, EmailStr

from app.security.config import (
    SecurityConfig, InputValidator, PasswordManager, TokenManager,
    RateLimiter, AuditLogger, EncryptionManager, security_config,
    rate_limiter, audit_logger
)
from app.config import settings

logger = logging.getLogger(__name__)

class UserRole(str, Enum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    SUSPENDED = "suspended"

class UserCreate(BaseModel):
    """User creation model with validation."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)
    role: UserRole = UserRole.VIEWER
    
    @validator('username')
    def validate_username(cls, v):
        return InputValidator.validate_username(v)
    
    @validator('password')
    def validate_password(cls, v):
        if security_config:
            return InputValidator.validate_password(v, security_config)
        return v

class UserInDB(BaseModel):
    """User model for database storage."""
    id: str
    username: str
    email: str
    full_name: Optional[str]
    hashed_password: str
    role: UserRole
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None

class LoginAttempt(BaseModel):
    """Login attempt tracking."""
    username: str
    ip_address: str
    user_agent: Optional[str]
    timestamp: datetime
    success: bool
    failure_reason: Optional[str] = None

class AuthenticationService:
    """Enhanced authentication service with security features."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")
        
        # Rate limiting configurations
        self.rate_limits = {
            "login": {"requests": 5, "window": 300},  # 5 per 5 minutes
            "register": {"requests": 3, "window": 300},  # 3 per 5 minutes
            "password_reset": {"requests": 3, "window": 3600},  # 3 per hour
            "token_refresh": {"requests": 10, "window": 3600},  # 10 per hour
        }
        
        # Account lockout configuration
        self.max_failed_attempts = 5
        self.lockout_duration = 900  # 15 minutes
    
    def _get_user_key(self, username: str) -> str:
        """Get Redis key for user data."""
        return f"user:{username}"
    
    def _get_failed_attempts_key(self, username: str) -> str:
        """Get Redis key for failed login attempts."""
        return f"failed_attempts:{username}"
    
    def _get_account_lockout_key(self, username: str) -> str:
        """Get Redis key for account lockout."""
        return f"account_lockout:{username}"
    
    def _get_token_blacklist_key(self, token_jti: str) -> str:
        """Get Redis key for token blacklist."""
        return f"token_blacklist:{token_jti}"
    
    def _get_refresh_token_key(self, token_jti: str) -> str:
        """Get Redis key for refresh token."""
        return f"refresh_token:{token_jti}"
    
    async def create_user(self, user_data: UserCreate) -> UserInDB:
        """
        Create a new user with security validation.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user object
            
        Raises:
            HTTPException: If user creation fails
        """
        try:
            # Check if user already exists
            existing_user = await self.get_user(user_data.username)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already exists"
                )
            
            # Hash password securely
            hashed_password = PasswordManager.hash_password(
                user_data.password, 
                security_config.PASSWORD_SALT_ROUNDS if security_config else 12
            )
            
            # Create user object
            user = UserInDB(
                id=f"user_{secrets.token_urlsafe(16)}",
                username=user_data.username,
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                role=user_data.role,
                status=UserStatus.ACTIVE,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Store user in Redis
            user_key = self._get_user_key(user.username)
            user_data = user.dict()
            user_data['created_at'] = user.created_at.isoformat()
            user_data['updated_at'] = user.updated_at.isoformat()
            if user.last_login:
                user_data['last_login'] = user.last_login.isoformat()
            if user.locked_until:
                user_data['locked_until'] = user.locked_until.isoformat()
            
            self.redis.setex(
                user_key,
                86400 * 365,  # 1 year expiration
                json.dumps(user_data)
            )
            
            # Log user creation
            if audit_logger:
                audit_logger.log_security_event(
                    event_type="USER_CREATED",
                    severity="INFO",
                    user_id=user.username,
                    details={"role": user.role.value}
                )
            
            logger.info(f"User created: {user.username}")
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="User creation failed"
            )
    
    async def get_user(self, username: str) -> Optional[UserInDB]:
        """
        Get user by username.
        
        Args:
            username: Username to lookup
            
        Returns:
            User object or None if not found
        """
        try:
            user_key = self._get_user_key(username)
            user_data = self.redis.get(user_key)
            
            if not user_data:
                return None
            
            data = json.loads(user_data)
            
            # Convert string timestamps back to datetime objects
            data['created_at'] = datetime.fromisoformat(data['created_at'])
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
            if data.get('last_login'):
                data['last_login'] = datetime.fromisoformat(data['last_login'])
            if data.get('locked_until'):
                data['locked_until'] = datetime.fromisoformat(data['locked_until'])
            
            return UserInDB(**data)
            
        except Exception as e:
            logger.error(f"Get user error: {e}")
            return None
    
    async def update_user(self, username: str, updates: Dict[str, Any]) -> bool:
        """
        Update user information.
        
        Args:
            username: Username to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            user = await self.get_user(username)
            if not user:
                return False
            
            # Update fields
            for field, value in updates.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.now(timezone.utc)
            
            # Save updated user
            user_key = self._get_user_key(username)
            user_data = user.dict()
            user_data['created_at'] = user.created_at.isoformat()
            user_data['updated_at'] = user.updated_at.isoformat()
            if user.last_login:
                user_data['last_login'] = user.last_login.isoformat()
            if user.locked_until:
                user_data['locked_until'] = user.locked_until.isoformat()
            
            self.redis.setex(
                user_key,
                86400 * 365,
                json.dumps(user_data)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Update user error: {e}")
            return False
    
    async def check_rate_limit(self, key: str, endpoint_type: str, ip_address: str) -> bool:
        """
        Check if request exceeds rate limits.
        
        Args:
            key: Rate limit key (username or IP)
            endpoint_type: Type of endpoint
            ip_address: Client IP address
            
        Returns:
            True if allowed, False if rate limited
        """
        try:
            if not rate_limiter:
                return True  # Allow if rate limiter not initialized
            
            config = self.rate_limits.get(endpoint_type, {"requests": 10, "window": 300})
            redis_key = f"rate_limit:{endpoint_type}:{key}"
            
            allowed, info = rate_limiter.is_allowed(
                redis_key, 
                config["requests"], 
                config["window"]
            )
            
            if not allowed and audit_logger:
                audit_logger.log_security_event(
                    event_type="RATE_LIMIT_EXCEEDED",
                    severity="MEDIUM",
                    ip_address=ip_address,
                    details={
                        "endpoint_type": endpoint_type,
                        "key": key,
                        "current": info['current'],
                        "limit": info['limit']
                    }
                )
            
            return allowed
            
        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return True  # Fail open
    
    async def check_account_lockout(self, username: str, ip_address: str) -> bool:
        """
        Check if account is locked.
        
        Args:
            username: Username to check
            ip_address: Client IP address
            
        Returns:
            True if locked, False otherwise
        """
        try:
            user = await self.get_user(username)
            if not user:
                return False
            
            # Check if user is manually locked
            if user.status == UserStatus.LOCKED:
                if audit_logger:
                    audit_logger.log_security_event(
                        event_type="ACCOUNT_LOCKED",
                        severity="HIGH",
                        user_id=username,
                        ip_address=ip_address,
                        details={"reason": "manual_lock"}
                    )
                return True
            
            # Check temporary lockout due to failed attempts
            if user.locked_until and datetime.now(timezone.utc) < user.locked_until:
                if audit_logger:
                    audit_logger.log_security_event(
                        event_type="ACCOUNT_TEMPORARILY_LOCKED",
                        severity="HIGH",
                        user_id=username,
                        ip_address=ip_address,
                        details={
                            "locked_until": user.locked_until.isoformat(),
                            "failed_attempts": user.failed_login_attempts
                        }
                    )
                return True
            
            # Reset lockout if expired
            if user.locked_until and datetime.now(timezone.utc) >= user.locked_until:
                await self.update_user(username, {
                    "failed_login_attempts": 0,
                    "locked_until": None
                })
            
            return False
            
        except Exception as e:
            logger.error(f"Account lockout check error: {e}")
            return False
    
    async def record_failed_attempt(self, username: str, ip_address: str, 
                                  user_agent: Optional[str] = None, 
                                  reason: str = "invalid_credentials"):
        """
        Record a failed login attempt.
        
        Args:
            username: Username that failed
            ip_address: Client IP address
            user_agent: Client user agent
            reason: Failure reason
        """
        try:
            user = await self.get_user(username)
            if user:
                # Increment failed attempts
                new_failed_count = user.failed_login_attempts + 1
                updates = {"failed_login_attempts": new_failed_count}
                
                # Lock account if threshold reached
                if new_failed_count >= self.max_failed_attempts:
                    locked_until = datetime.now(timezone.utc) + timedelta(seconds=self.lockout_duration)
                    updates["locked_until"] = locked_until
                    updates["status"] = UserStatus.LOCKED
                    
                    if audit_logger:
                        audit_logger.log_security_event(
                            event_type="ACCOUNT_AUTO_LOCKED",
                            severity="HIGH",
                            user_id=username,
                            ip_address=ip_address,
                            user_agent=user_agent,
                            details={
                                "failed_attempts": new_failed_count,
                                "locked_until": locked_until.isoformat(),
                                "reason": reason
                            }
                        )
                
                await self.update_user(username, updates)
            
            # Record attempt in Redis for tracking
            attempt_key = self._get_failed_attempts_key(username)
            attempt_data = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "ip_address": ip_address,
                "user_agent": user_agent,
                "reason": reason
            }
            
            self.redis.lpush(attempt_key, json.dumps(attempt_data))
            self.redis.expire(attempt_key, 3600)  # Keep for 1 hour
            self.redis.ltrim(attempt_key, 0, self.max_failed_attempts - 1)
            
        except Exception as e:
            logger.error(f"Record failed attempt error: {e}")
    
    async def authenticate_user(self, username: str, password: str, 
                              ip_address: str, user_agent: Optional[str] = None) -> Optional[UserInDB]:
        """
        Authenticate user with comprehensive security checks.
        
        Args:
            username: Username
            password: Plain text password
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            User object if successful, None otherwise
        """
        try:
            # Check rate limits
            if not await self.check_rate_limit(username, "login", ip_address):
                if audit_logger:
                    audit_logger.log_security_event(
                        event_type="LOGIN_RATE_LIMITED",
                        severity="MEDIUM",
                        user_id=username,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                return None
            
            # Check account lockout
            if await self.check_account_lockout(username, ip_address):
                return None
            
            # Get user
            user = await self.get_user(username)
            if not user:
                await self.record_failed_attempt(username, ip_address, user_agent, "user_not_found")
                return None
            
            # Check user status
            if user.status != UserStatus.ACTIVE:
                await self.record_failed_attempt(username, ip_address, user_agent, f"account_{user.status}")
                return None
            
            # Verify password
            if not PasswordManager.verify_password(password, user.hashed_password):
                await self.record_failed_attempt(username, ip_address, user_agent, "invalid_password")
                return None
            
            # Successful authentication - reset failed attempts
            if user.failed_login_attempts > 0:
                await self.update_user(username, {
                    "failed_login_attempts": 0,
                    "locked_until": None,
                    "last_login": datetime.now(timezone.utc)
                })
            else:
                await self.update_user(username, {
                    "last_login": datetime.now(timezone.utc)
                })
            
            # Log successful login
            if audit_logger:
                audit_logger.log_security_event(
                    event_type="LOGIN_SUCCESS",
                    severity="INFO",
                    user_id=username,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details={"role": user.role.value}
                )
            
            logger.info(f"User authenticated: {username} from {ip_address}")
            return user
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
    
    async def create_access_token(self, user: UserInDB, expires_delta: Optional[timedelta] = None) -> Tuple[str, str]:
        """
        Create JWT access token.
        
        Args:
            user: User object
            expires_delta: Custom expiration time
            
        Returns:
            Tuple of (access_token, token_jti)
        """
        try:
            if not security_config:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Security not initialized"
                )
            
            # Prepare token payload
            payload = {
                "sub": user.username,
                "role": user.role.value,
                "user_id": user.id,
                "type": "access"
            }
            
            # Set expiration
            if expires_delta:
                expires_in = int(expires_delta.total_seconds())
            else:
                expires_in = security_config.JWT_EXPIRATION_HOURS * 3600
            
            # Generate token
            token = TokenManager.generate_token(
                payload=payload,
                secret=security_config.JWT_SECRET,
                algorithm=security_config.JWT_ALGORITHM,
                expires_in=expires_in
            )
            
            # Extract JTI from token
            decoded = jwt.decode(token, options={"verify_signature": False})
            token_jti = decoded.get("jti")
            
            return token, token_jti
            
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Token creation failed"
            )
    
    async def create_refresh_token(self, user: UserInDB, access_token_jti: str,
                                 ip_address: str, user_agent: Optional[str] = None) -> str:
        """
        Create refresh token.
        
        Args:
            user: User object
            access_token_jti: JWT ID of access token
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            Refresh token string
        """
        try:
            if not security_config:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Security not initialized"
                )
            
            # Prepare refresh token payload
            payload = {
                "sub": user.username,
                "user_id": user.id,
                "access_jti": access_token_jti,
                "type": "refresh"
            }
            
            # Generate refresh token with longer expiration
            expires_in = security_config.JWT_REFRESH_EXPIRATION_DAYS * 86400
            refresh_token = TokenManager.generate_token(
                payload=payload,
                secret=security_config.JWT_SECRET,
                algorithm=security_config.JWT_ALGORITHM,
                expires_in=expires_in
            )
            
            # Extract JTI
            decoded = jwt.decode(refresh_token, options={"verify_signature": False})
            refresh_jti = decoded.get("jti")
            
            # Store refresh token metadata
            refresh_key = self._get_refresh_token_key(refresh_jti)
            refresh_data = {
                "user_id": user.username,
                "access_jti": access_token_jti,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": (datetime.now(timezone.utc) + timedelta(seconds=expires_in)).isoformat()
            }
            
            self.redis.setex(
                refresh_key,
                expires_in,
                json.dumps(refresh_data)
            )
            
            return refresh_token
            
        except Exception as e:
            logger.error(f"Refresh token creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Refresh token creation failed"
            )
    
    async def validate_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Validate refresh token.
        
        Args:
            refresh_token: Refresh token to validate
            
        Returns:
            Decoded token payload
            
        Raises:
            HTTPException: If token is invalid
        """
        try:
            if not security_config:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Security not initialized"
                )
            
            # Decode token
            payload = TokenManager.verify_token(
                token=refresh_token,
                secret=security_config.JWT_SECRET,
                algorithm=security_config.JWT_ALGORITHM
            )
            
            # Validate token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )
            
            # Check if refresh token exists in Redis
            refresh_jti = payload.get("jti")
            if not refresh_jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token format"
                )
            
            refresh_key = self._get_refresh_token_key(refresh_jti)
            refresh_data = self.redis.get(refresh_key)
            
            if not refresh_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Refresh token not found or expired"
                )
            
            return payload
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Refresh token validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token validation failed"
            )
    
    async def blacklist_token(self, token_jti: str, expires_at: datetime, 
                            user_id: str, reason: str = "logout"):
        """
        Add token to blacklist.
        
        Args:
            token_jti: JWT ID of token
            expires_at: Token expiration time
            user_id: User ID
            reason: Reason for blacklisting
        """
        try:
            blacklist_key = self._get_token_blacklist_key(token_jti)
            blacklist_data = {
                "blacklisted_at": datetime.now(timezone.utc).isoformat(),
                "expires_at": expires_at.isoformat(),
                "user_id": user_id,
                "reason": reason
            }
            
            # Calculate TTL until token expiration
            ttl = int((expires_at - datetime.now(timezone.utc)).total_seconds())
            if ttl > 0:
                self.redis.setex(
                    blacklist_key,
                    ttl,
                    json.dumps(blacklist_data)
                )
                
                if audit_logger:
                    audit_logger.log_security_event(
                        event_type="TOKEN_BLACKLISTED",
                        severity="INFO",
                        user_id=user_id,
                        details={
                            "token_jti": token_jti,
                            "reason": reason,
                            "expires_at": expires_at.isoformat()
                        }
                    )
            
        except Exception as e:
            logger.error(f"Token blacklisting error: {e}")
    
    async def is_token_blacklisted(self, token_jti: str) -> bool:
        """
        Check if token is blacklisted.
        
        Args:
            token_jti: JWT ID of token
            
        Returns:
            True if blacklisted, False otherwise
        """
        try:
            blacklist_key = self._get_token_blacklist_key(token_jti)
            return self.redis.exists(blacklist_key)
        except Exception as e:
            logger.error(f"Token blacklist check error: {e}")
            return False
    
    async def get_current_user(self, token: str, request: Request) -> UserInDB:
        """
        Get current user from JWT token with comprehensive validation.
        
        Args:
            token: JWT access token
            request: FastAPI request object
            
        Returns:
            Current user object
            
        Raises:
            HTTPException: If authentication fails
        """
        try:
            if not security_config:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Security not initialized"
                )
            
            # Decode token
            payload = TokenManager.verify_token(
                token=token,
                secret=security_config.JWT_SECRET,
                algorithm=security_config.JWT_ALGORITHM
            )
            
            username = payload.get("sub")
            token_jti = payload.get("jti")
            
            if not username or not token_jti:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            # Check if token is blacklisted
            if await self.is_token_blacklisted(token_jti):
                ip_address = request.client.host if request.client else None
                user_agent = request.headers.get("user-agent")
                
                if audit_logger:
                    audit_logger.log_security_event(
                        event_type="BLACKLISTED_TOKEN_USED",
                        severity="HIGH",
                        user_id=username,
                        ip_address=ip_address,
                        user_agent=user_agent
                    )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )
            
            # Get user
            user = await self.get_user(username)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check user status
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Account is {user.status.value}"
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed"
            )

# Global authentication service instance
auth_service: Optional[AuthenticationService] = None

def initialize_auth_service(redis_client: redis.Redis):
    """Initialize authentication service."""
    global auth_service
    auth_service = AuthenticationService(redis_client)
    logger.info("Authentication service initialized")

# Dependency to get current user
async def get_current_user(
    request: Request,
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/token"))
) -> UserInDB:
    """FastAPI dependency to get current authenticated user."""
    if not auth_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service not initialized"
        )
    
    return await auth_service.get_current_user(token, request)

# Role-based access control decorators
def require_role(required_role: UserRole):
    """Decorator to require specific user role."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user from kwargs if available
            user = None
            for key, value in kwargs.items():
                if isinstance(value, UserInDB):
                    user = value
                    break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Role hierarchy: ADMIN > ANALYST > VIEWER
            role_hierarchy = {
                UserRole.VIEWER: 1,
                UserRole.ANALYST: 2,
                UserRole.ADMIN: 3
            }
            
            if role_hierarchy.get(user.role, 0) < role_hierarchy.get(required_role, 0):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Requires {required_role.value} role or higher"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get user from kwargs if available
            user = None
            for key, value in kwargs.items():
                if isinstance(value, UserInDB):
                    user = value
                    break
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            # Define permissions per role
            role_permissions = {
                UserRole.VIEWER: ["read"],
                UserRole.ANALYST: ["read", "write", "execute"],
                UserRole.ADMIN: ["read", "write", "execute", "delete", "admin"]
            }
            
            user_permissions = role_permissions.get(user.role, [])
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions for {permission}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator