"""
Enhanced Security Configuration for ScrapeCraft OSINT Platform

This module provides comprehensive security hardening including:
- Secure configuration management
- Input validation and sanitization
- Security headers implementation
- Rate limiting and DDoS protection
- Audit logging and monitoring
"""

import os
import secrets
import hashlib
import hmac
import re
import time
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from functools import wraps
import logging
from enum import Enum

from pydantic import BaseModel, Field, validator, EmailStr
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import redis
import bcrypt
import jwt
from cryptography.fernet import Fernet
import bleach
import html

logger = logging.getLogger(__name__)

class SecurityConfig(BaseModel):
    """Enhanced security configuration."""
    
    # JWT Configuration
    JWT_SECRET: str = Field(..., min_length=64)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week
    JWT_REFRESH_EXPIRATION_DAYS: int = Field(default=30, ge=1, le=365)
    
    # Password Security
    PASSWORD_MIN_LENGTH: int = Field(default=12, ge=8, le=128)
    PASSWORD_MAX_LENGTH: int = Field(default=128, ge=12, le=512)
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = True
    PASSWORD_SALT_ROUNDS: int = Field(default=12, ge=10, le=15)
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60, ge=1, le=1000)
    RATE_LIMIT_REQUESTS_PER_HOUR: int = Field(default=1000, ge=10, le=10000)
    RATE_LIMIT_BURST_SIZE: int = Field(default=10, ge=1, le=100)
    
    # Session Security
    SESSION_TIMEOUT_MINUTES: int = Field(default=30, ge=5, le=480)
    MAX_CONCURRENT_SESSIONS: int = Field(default=3, ge=1, le=10)
    
    # API Security
    API_KEY_LENGTH: int = Field(default=32, ge=16, le=64)
    API_KEY_PREFIX: str = "sc_"
    
    # Encryption
    ENCRYPTION_KEY: Optional[str] = None  # Will be generated if not provided
    
    # Audit Logging
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_LOG_RETENTION_DAYS: int = Field(default=90, ge=7, le=365)
    
    # Input Validation
    MAX_REQUEST_SIZE_MB: int = Field(default=10, ge=1, le=100)
    MAX_FIELD_LENGTH: int = Field(default=1000, ge=100, le=10000)
    
    # CORS Security
    CORS_ORIGINS: List[str] = Field(default_factory=list)
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_MAX_AGE: int = Field(default=86400, ge=0, le=86400)
    
    # Security Headers
    SECURITY_HEADERS_ENABLED: bool = True
    
    @validator('JWT_SECRET')
    def validate_jwt_secret(cls, v):
        if len(v) < 64:
            raise ValueError('JWT secret must be at least 64 characters long')
        return v
    
    @validator('CORS_ORIGINS')
    def validate_cors_origins(cls, v):
        allowed_origins = []
        for origin in v:
            if origin.startswith(('http://', 'https://')):
                allowed_origins.append(origin)
            elif origin == '*':
                logger.warning("Wildcard CORS origin detected - use only in development")
                allowed_origins.append(origin)
        return allowed_origins

class SecurityLevel(str, Enum):
    """Security levels for different environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class InputValidator:
    """Input validation and sanitization utilities."""
    
    # Regex patterns for validation
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')
    SAFE_STRING_PATTERN = re.compile(r'^[a-zA-Z0-9\s\-_.,!?@#$%&*()+=\[\]{}|;:<>"]*$')
    URL_PATTERN = re.compile(
        r'^https?:\/\/(?:[-\w.])+(?:[:\d]+)?(?:\/(?:[\w\/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))?)?$'
    )
    DOMAIN_PATTERN = re.compile(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    # Malicious patterns to block
    SQL_INJECTION_PATTERNS = [
        r'(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)',
        r'(--|#|\/\*|\*\/)',
        r'(\bOR\b.*=.*\bOR\b)',
        r'(\bAND\b.*=.*\bAND\b)',
        r'(\'\s*OR\s*\')',
        r'(\|\|)',
        r'(1=1|1 = 1)',
    ]
    
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'<link[^>]*>',
        r'<meta[^>]*>',
    ]
    
    @classmethod
    def sanitize_string(cls, value: str, max_length: Optional[int] = None) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Remove null bytes and control characters
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')
        
        # Trim whitespace
        value = value.strip()
        
        # Apply length limit
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        # HTML entity encoding for XSS prevention
        value = html.escape(value, quote=True)
        
        return value
    
    @classmethod
    def validate_username(cls, username: str) -> str:
        """Validate and sanitize username."""
        if not username:
            raise ValueError("Username is required")
        
        username = cls.sanitize_string(username, 50)
        
        if not cls.USERNAME_PATTERN.match(username):
            raise ValueError("Username must be 3-50 characters, alphanumeric, underscore, or hyphen only")
        
        return username
    
    @classmethod
    def validate_email(cls, email: str) -> str:
        """Validate email address."""
        if not email:
            raise ValueError("Email is required")
        
        email = cls.sanitize_string(email, 255).lower()
        
        # Basic email validation
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            raise ValueError("Invalid email format")
        
        return email
    
    @classmethod
    def validate_password(cls, password: str, config: SecurityConfig) -> str:
        """Validate password strength."""
        if not password:
            raise ValueError("Password is required")
        
        if len(password) < config.PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {config.PASSWORD_MIN_LENGTH} characters long")
        
        if len(password) > config.PASSWORD_MAX_LENGTH:
            raise ValueError(f"Password must not exceed {config.PASSWORD_MAX_LENGTH} characters")
        
        errors = []
        
        if config.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("uppercase letter")
        
        if config.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("lowercase letter")
        
        if config.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("number")
        
        if config.PASSWORD_REQUIRE_SYMBOLS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("special character")
        
        if errors:
            raise ValueError(f"Password must contain at least: {', '.join(errors)}")
        
        return password
    
    @classmethod
    def detect_sql_injection(cls, value: str) -> bool:
        """Detect potential SQL injection attempts."""
        if not isinstance(value, str):
            return False
        
        value_upper = value.upper()
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value_upper, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def detect_xss(cls, value: str) -> bool:
        """Detect potential XSS attempts."""
        if not isinstance(value, str):
            return False
        
        value_lower = value.lower()
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        return False
    
    @classmethod
    def validate_url(cls, url: str) -> str:
        """Validate and sanitize URL."""
        if not url:
            raise ValueError("URL is required")
        
        url = cls.sanitize_string(url, 2048)
        
        if not cls.URL_PATTERN.match(url):
            raise ValueError("Invalid URL format")
        
        return url
    
    @classmethod
    def validate_domain(cls, domain: str) -> str:
        """Validate and sanitize domain name."""
        if not domain:
            raise ValueError("Domain is required")
        
        domain = cls.sanitize_string(domain, 253).lower()
        
        if not cls.DOMAIN_PATTERN.match(domain):
            raise ValueError("Invalid domain format")
        
        return domain

class PasswordManager:
    """Secure password management utilities."""
    
    @staticmethod
    def hash_password(password: str, salt_rounds: int = 12) -> str:
        """Hash password using bcrypt."""
        salt = bcrypt.gensalt(rounds=salt_rounds)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash."""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate a secure random password."""
        import string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

class TokenManager:
    """JWT token management utilities."""
    
    @staticmethod
    def generate_token(payload: Dict[str, Any], secret: str, 
                      algorithm: str = "HS256", expires_in: Optional[int] = None) -> str:
        """Generate JWT token."""
        if expires_in:
            payload['exp'] = datetime.utcnow() + timedelta(seconds=expires_in)
        else:
            payload['exp'] = datetime.utcnow() + timedelta(hours=24)
        
        payload['iat'] = datetime.utcnow()
        payload['jti'] = secrets.token_urlsafe(32)
        
        return jwt.encode(payload, secret, algorithm=algorithm)
    
    @staticmethod
    def verify_token(token: str, secret: str, algorithm: str = "HS256") -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            return jwt.decode(token, secret, algorithms=[algorithm])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

class EncryptionManager:
    """Data encryption utilities."""
    
    def __init__(self, key: Optional[str] = None):
        if key:
            self.key = key.encode()
        else:
            self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

class RateLimiter:
    """Rate limiting implementation using Redis."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Rate limit key (e.g., user ID, IP address)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (allowed, info_dict)
        """
        now = int(time.time())
        pipeline = self.redis.pipeline()
        
        # Remove expired entries
        pipeline.zremrangebyscore(key, 0, now - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(now): now})
        
        # Set expiration
        pipeline.expire(key, window)
        
        results = pipeline.execute()
        current_requests = results[1]
        
        # Remove oldest if over limit
        if current_requests > limit:
            pipeline.zremrangebyrank(key, 0, current_requests - limit - 1)
            pipeline.execute()
        
        allowed = current_requests < limit
        
        return allowed, {
            'current': current_requests,
            'limit': limit,
            'remaining': max(0, limit - current_requests),
            'reset_time': now + window
        }

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
        
        # HSTS (HTTPS only)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",  # Adjust based on needs
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self'",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        return response

class AuditLogger:
    """Security audit logging."""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    def log_security_event(self, event_type: str, severity: str, 
                          user_id: Optional[str] = None, 
                          ip_address: Optional[str] = None,
                          user_agent: Optional[str] = None,
                          details: Optional[Dict[str, Any]] = None):
        """Log security event."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'event_type': event_type,
            'severity': severity,
            'user_id': user_id,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'details': details or {}
        }
        
        # Store in Redis for recent events
        key = f"security_audit:{datetime.utcnow().strftime('%Y-%m-%d')}"
        self.redis.lpush(key, str(event))
        self.redis.expire(key, 86400 * 90)  # 90 days retention
        
        # Log to file as well
        logger.warning(f"Security Event: {event_type} - {severity} - User: {user_id} - IP: {ip_address}")

# Global instances (to be initialized with proper dependencies)
security_config: Optional[SecurityConfig] = None
rate_limiter: Optional[RateLimiter] = None
audit_logger: Optional[AuditLogger] = None
encryption_manager: Optional[EncryptionManager] = None

def initialize_security(config: SecurityConfig, redis_client: redis.Redis):
    """Initialize security components."""
    global security_config, rate_limiter, audit_logger, encryption_manager
    
    security_config = config
    rate_limiter = RateLimiter(redis_client)
    audit_logger = AuditLogger(redis_client)
    encryption_manager = EncryptionManager(config.ENCRYPTION_KEY)
    
    logger.info("Security components initialized")

def require_security_level(level: SecurityLevel):
    """Decorator to require minimum security level."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not security_config:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Security not initialized"
                )
            
            # Add level-specific checks here if needed
            return await func(*args, **kwargs)
        return wrapper
    return decorator