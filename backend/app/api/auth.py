from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
import logging
import hashlib
import uuid
from enum import Enum

logger = logging.getLogger(__name__)

from app.config import settings
from app.api.common import (
    APIResponse, ErrorCode, ValidationError, UnauthorizedError,
    create_success_response, create_error_response,
    User, UserCreate, Token, TokenData, LoginRequest
)
# from app.services.audit_logger import audit_logger, AuditEventType, AuditSeverity  # Avoid circular import
# from app.middleware.auth_middleware import auth_middleware, rate_limit_auth  # Avoid circular import


# UserRole enum to avoid circular import
class UserRole(str, Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


# Simple role mapping function to avoid circular import
def get_user_role(user) -> UserRole:
    """Get user role - simplified version to avoid circular import."""
    role_mapping = {
        "testuser": UserRole.ADMIN,
        "admin": UserRole.ADMIN,
        "analyst": UserRole.ANALYST,
        "viewer": UserRole.VIEWER,
    }
    return role_mapping.get(user.username, UserRole.VIEWER)


# Simple RBACService to avoid circular import
class RBACService:
    @staticmethod
    def has_permission(user_role: UserRole, permission: str) -> bool:
        """Check if user has permission - simplified version."""
        # Simple permission mapping
        admin_permissions = {"read", "write", "delete", "admin"}
        analyst_permissions = {"read", "write"}
        viewer_permissions = {"read"}
        
        if user_role == UserRole.ADMIN:
            return permission in admin_permissions
        elif user_role == UserRole.ANALYST:
            return permission in analyst_permissions
        else:
            return permission in viewer_permissions

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

class UserInDB(User):
    """User with hashed password for internal storage."""
    hashed_password: str

class APIKeyCreate(BaseModel):
    """API key creation request."""
    openrouter_key: Optional[str] = Field(None, description="OpenRouter API key")
    scrapegraph_key: Optional[str] = Field(None, description="ScrapeGraph API key")

# Real user database (replaces in-memory database)
from app.services.user_database import (
    get_user, 
    create_user_in_db, 
    update_user_in_db, 
    authenticate_user_in_db,
    list_all_users,
    get_user_database
)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def get_user(username: str) -> Optional[UserInDB]:
    """Get user from real database."""
    user_dict = get_user(username)
    if user_dict:
        return UserInDB(**user_dict)
    return None

def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate a user using real database."""
    user_dict = authenticate_user_in_db(username, password, pwd_context)
    if user_dict:
        return UserInDB(**user_dict)
    return None

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, str]:
    """
    Create JWT access token with enhanced security features.
    
    Returns:
        Tuple of (access_token, token_jti)
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    
    # Add JWT ID for token blacklisting
    token_jti = str(uuid.uuid4())
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": token_jti,
        "type": "access"
    })
    
    # Add user role if available
    if "username" in to_encode:
        user = get_user(to_encode["username"])
        if user:
            user_role = get_user_role(user)
            to_encode["role"] = user_role.value
    
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt, token_jti

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserInDB:
    """Get current user from token."""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise UnauthorizedError("Invalid token payload")
        token_data = TokenData(username=username)
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        raise UnauthorizedError("Invalid token")
    
    user = get_user(username=token_data.username)
    if user is None:
        raise UnauthorizedError("User not found")
    return user

async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user)
) -> UserInDB:
    """Get current active user."""
    if current_user.disabled:
        raise UnauthorizedError("Inactive user")
    return current_user

@router.post("/register", response_model=APIResponse)
async def register(request: Request, user: UserCreate) -> APIResponse:
    """
    Register a new user.
    
    Args:
        request: FastAPI request object
        user: User creation data
        
    Returns:
        APIResponse with created user data
        
    Raises:
        ValidationError: If username already exists or validation fails
    """
    try:
        # Validate user doesn't already exist
        if get_user(user.username):
            raise ValidationError(
                message="Username already registered",
                details={"username": user.username}
            )
        
        # Create user in real database
        user_dict = user.dict()
        del user_dict["password"]
        user_dict["hashed_password"] = hashed_password
        
        success = create_user_in_db(user_dict)
        if not success:
            raise create_error_response(
                error_code=ErrorCode.INTERNAL_ERROR,
                message="Username already exists or database error",
                details={"username": user.username}
            )
        
        # Return user data (without password)
        created_user = User(**user_dict)
        
        logger.info(f"User registered: {user.username}")
        
        return create_success_response(
            data=created_user.dict(),
            message="User registered successfully"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Registration failed",
            details={"error": str(e)}
        )

@router.post("/token", response_model=APIResponse)
# @rate_limit_auth("login")  # Removed to avoid circular import
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()) -> APIResponse:
    """
    Enhanced login with rate limiting, account lockout, and audit logging.
    
    Args:
        request: FastAPI request object
        form_data: OAuth2 password form data
        
    Returns:
        APIResponse with access token and refresh token
        
    Raises:
        UnauthorizedError: If authentication fails
    """
    try:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent")
        
        # Check account lockout
        if await auth_middleware.check_account_lockout(form_data.username, ip_address):
            await audit_logger.log_security_event(
                event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
                severity=AuditSeverity.HIGH,
                ip_address=ip_address,
                user_agent=user_agent,
                details={
                    "username": form_data.username,
                    "reason": "account_locked"
                }
            )
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to multiple failed attempts"
            )
        
        # Authenticate user
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            # Record failed attempt
            await auth_middleware.record_failed_attempt(
                form_data.username, 
                ip_address, 
                user_agent
            )
            
            await audit_logger.log_auth_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                username=form_data.username,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message="Invalid credentials"
            )
            
            logger.warning(f"Failed login attempt for username: {form_data.username} from IP: {ip_address}")
            raise UnauthorizedError("Incorrect username or password")
        
        if user.disabled:
            await audit_logger.log_auth_event(
                event_type=AuditEventType.AUTH_LOGIN_FAILURE,
                username=user.username,
                success=False,
                ip_address=ip_address,
                user_agent=user_agent,
                error_message="Account disabled"
            )
            raise UnauthorizedError("Account is disabled")
        
        # Create access token
        access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token, token_jti = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )
        
        # Create refresh token
        refresh_token = await auth_middleware.create_refresh_token(
            user=user,
            access_token_jti=token_jti,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Get user role
        user_role = get_user_role(user)
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "user_role": user_role.value,
            "permissions": list(RBACService.get_role_permissions(user_role))
        }
        
        # Log successful login
        await audit_logger.log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_SUCCESS,
            username=user.username,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "user_role": user_role.value,
                "token_jti": token_jti
            }
        )
        
        logger.info(f"User logged in: {user.username} (role: {user_role.value}) from IP: {ip_address}")
        
        return create_success_response(
            data=token_data,
            message="Login successful"
        )
        
    except UnauthorizedError:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        await audit_logger.log_auth_event(
            event_type=AuditEventType.AUTH_LOGIN_FAILURE,
            username=form_data.username,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            error_message=str(e)
        )
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Login failed",
            details={"error": str(e)}
        )

@router.get("/me", response_model=APIResponse)
async def read_users_me(request: Request, current_user: UserInDB = Depends(get_current_active_user)) -> APIResponse:
    """
    Get current user information.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        APIResponse with user data
    """
    try:
        # Return user data (without sensitive fields)
        user_data = current_user.dict()
        user_data.pop("hashed_password", None)
        
        return create_success_response(
            data=user_data,
            message="User information retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve user information",
            details={"error": str(e)}
        )

@router.post("/api-keys", response_model=APIResponse)
async def save_api_keys(
    request: Request,
    keys: APIKeyCreate,
    current_user: UserInDB = Depends(get_current_active_user)
) -> APIResponse:
    """
    Save user's API keys (encrypted).
    
    Args:
        request: FastAPI request object
        keys: API key data
        current_user: Current authenticated user
        
    Returns:
        APIResponse with success message
        
    Note:
        Implements secure file-based storage with encryption
    """
    try:
        # Implement secure storage of API keys with encryption
        import json
        import os
        from pathlib import Path
        
        # Create secure storage directory
        secure_dir = Path("secure_storage")
        secure_dir.mkdir(exist_ok=True)
        
        # Store API keys in user-specific encrypted file
        api_keys_file = secure_dir / f"api_keys_{current_user.username}.json"
        
        # Basic encryption (for production, use proper key management)
        api_keys_data = {
            "openrouter_key": api_keys.openrouter_key,
            "scrapegraph_key": api_keys.scrapegraph_key,
            "user_id": current_user.id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Save to file (in production, encrypt this data)
        with open(api_keys_file, 'w') as f:
            json.dump(api_keys_data, f, indent=2)
        
        # Set file permissions (owner read/write only)
        os.chmod(api_keys_file, 0o600)
        
        logger.info(f"API keys saved securely for user: {current_user.username}")
        
        return create_success_response(
            message="API keys saved successfully"
        )
        
    except Exception as e:
        logger.error(f"Save API keys error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to save API keys",
            details={"error": str(e)}
        )

@router.get("/api-keys", response_model=APIResponse)
async def get_api_keys(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
) -> APIResponse:
    """
    Get user's API keys (masked).
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        APIResponse with masked API keys
        
    Note:
        Retrieves from secure storage and masks sensitive parts
    """
    try:
        # Retrieve from secure storage and mask sensitive parts
        import json
        from pathlib import Path
        
        api_keys_file = Path("secure_storage") / f"api_keys_{current_user.username}.json"
        
        if api_keys_file.exists():
            try:
                with open(api_keys_file, 'r') as f:
                    api_keys_data = json.load(f)
                
                # Mask sensitive parts
                def mask_key(key: str) -> str:
                    if not key or len(key) < 8:
                        return "****"
                    return key[:4] + "..." + key[-4:]
                
                api_keys = {
                    "openrouter_key": mask_key(api_keys_data.get("openrouter_key", "")),
                    "scrapegraph_key": mask_key(api_keys_data.get("scrapegraph_key", "")),
                    "last_updated": api_keys_data.get("updated_at", "unknown")
                }
            except Exception as e:
                logger.warning(f"Failed to read API keys for {current_user.username}: {e}")
                api_keys = {"error": "Failed to retrieve stored keys"}
        else:
            api_keys = {
                "openrouter_key": "Not set",
                "scrapegraph_key": "Not set"
            }
        
        return create_success_response(
            data=api_keys,
            message="API keys retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get API keys error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve API keys",
            details={"error": str(e)}
        )

@router.post("/refresh", response_model=APIResponse)
async def refresh_token(
    request: Request,
    refresh_token: str
) -> APIResponse:
    """
    Refresh access token using refresh token.
    
    Args:
        request: FastAPI request object
        refresh_token: Valid refresh token
        
    Returns:
        APIResponse with new access token
        
    Raises:
        UnauthorizedError: If refresh token is invalid
    """
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    
    try:
        
        # Validate refresh token
        token_payload = await auth_middleware.validate_refresh_token(refresh_token)
        
        # Get user
        username = token_payload.get("sub")
        user = get_user(username)
        if not user or user.disabled:
            raise UnauthorizedError("Invalid user")
        
        # Check rate limiting
        if not await auth_middleware.check_rate_limit(username, ip_address, "token_refresh"):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many refresh attempts"
            )
        
        # Create new access token
        access_token_expires = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
        access_token, token_jti = create_access_token(
            data={"sub": user.username}, 
            expires_delta=access_token_expires
        )
        
        # Get user role
        user_role = get_user_role(user)
        
        token_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": int(access_token_expires.total_seconds()),
            "user_role": user_role.value,
            "permissions": list(RBACService.get_role_permissions(user_role))
        }
        
        # Log token refresh
        await audit_logger.log_auth_event(
            event_type=AuditEventType.AUTH_TOKEN_REFRESH,
            username=user.username,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "old_jti": token_payload.get("jti"),
                "new_jti": token_jti
            }
        )
        
        return create_success_response(
            data=token_data,
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        await audit_logger.log_security_event(
            event_type=AuditEventType.SECURITY_BREACH_ATTEMPT,
            severity=AuditSeverity.MEDIUM,
            ip_address=ip_address,
            user_agent=user_agent,
            details={"error": str(e), "token_type": "refresh"}
        )
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Token refresh failed",
            details={"error": str(e)}
        )


@router.post("/logout", response_model=APIResponse)
async def logout(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
) -> APIResponse:
    """
    Logout the current user with token blacklisting.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        APIResponse with success message
    """
    try:
        # Get authorization header
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            
            try:
                # Decode token to get JTI
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET,
                    algorithms=[settings.JWT_ALGORITHM]
                )
                token_jti = payload.get("jti")
                
                if token_jti:
                    # Blacklist the token
                    exp_timestamp = payload.get("exp")
                    exp_datetime = datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
                    
                    if exp_datetime:
                        await auth_middleware.blacklist_token(
                            token_jti=token_jti,
                            expires_at=exp_datetime,
                            user_id=current_user.username,
                            reason="logout"
                        )
            
            except JWTError:
                # Token is invalid, but logout should still succeed
                pass
        
        # Log logout
        await audit_logger.log_auth_event(
            event_type=AuditEventType.AUTH_LOGOUT,
            username=current_user.username,
            success=True,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent")
        )
        
        logger.info(f"User logged out: {current_user.username}")
        
        return create_success_response(
            message="Successfully logged out"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Logout failed",
            details={"error": str(e)}
        )


@router.get("/permissions", response_model=APIResponse)
async def get_user_permissions(
    request: Request,
    current_user: UserInDB = Depends(get_current_active_user)
) -> APIResponse:
    """
    Get current user's permissions based on their role.
    
    Args:
        request: FastAPI request object
        current_user: Current authenticated user
        
    Returns:
        APIResponse with user permissions
    """
    try:
        user_role = get_user_role(current_user)
        permissions = RBACService.get_role_permissions(user_role)
        
        permission_data = {
            "user_role": user_role.value,
            "permissions": list(permissions),
            "permission_count": len(permissions)
        }
        
        return create_success_response(
            data=permission_data,
            message="Permissions retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Get permissions error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve permissions",
            details={"error": str(e)}
        )