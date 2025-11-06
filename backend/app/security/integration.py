"""
Security Integration Module for ScrapeCraft OSINT Platform

This module initializes and integrates all security components:
- Enhanced authentication service
- Security configuration
- Rate limiting and audit logging
- Security headers middleware
- RBAC and permissions
"""

import os
import secrets
import redis
import logging
from typing import Optional

from app.security.config import (
    SecurityConfig, SecurityLevel, initialize_security,
    SecurityHeadersMiddleware, security_config, audit_logger
)
from app.services.enhanced_auth_service import (
    AuthenticationService, initialize_auth_service, auth_service
)
from app.config import settings

logger = logging.getLogger(__name__)

def generate_secure_jwt_secret() -> str:
    """Generate a secure JWT secret for production use."""
    return secrets.token_urlsafe(64)  # 64+ characters for high security

def get_or_create_jwt_secret() -> str:
    """
    Get JWT secret from environment or generate a secure one.
    
    In production, this should always be set via environment variable.
    For development, a secure random secret will be generated.
    """
    # Check environment variable first
    jwt_secret = os.getenv("JWT_SECRET")
    if jwt_secret:
        if len(jwt_secret) < 64:
            logger.warning("JWT_SECRET is too short, should be at least 64 characters")
        return jwt_secret
    
    # Check if we're in development
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        raise ValueError(
            "JWT_SECRET environment variable must be set in production environment. "
            "Generate one with: openssl rand -base64 64"
        )
    
    # Generate a secure secret for development
    logger.warning(
        "Generating random JWT secret for development. "
        "Set JWT_SECRET environment variable for production use."
    )
    return generate_secure_jwt_secret()

def create_security_config() -> SecurityConfig:
    """
    Create security configuration based on environment.
    
    Returns:
        SecurityConfig instance with appropriate settings
    """
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    # Base configuration
    config_data = {
        "JWT_SECRET": get_or_create_jwt_secret(),
        "JWT_ALGORITHM": "HS256",
        "JWT_EXPIRATION_HOURS": 24 if environment == "production" else 8,
        "JWT_REFRESH_EXPIRATION_DAYS": 30,
        
        # Password security
        "PASSWORD_MIN_LENGTH": 12,
        "PASSWORD_MAX_LENGTH": 128,
        "PASSWORD_REQUIRE_UPPERCASE": True,
        "PASSWORD_REQUIRE_LOWERCASE": True,
        "PASSWORD_REQUIRE_NUMBERS": True,
        "PASSWORD_REQUIRE_SYMBOLS": environment == "production",
        "PASSWORD_SALT_ROUNDS": 12 if environment == "production" else 10,
        
        # Rate limiting (stricter in production)
        "RATE_LIMIT_ENABLED": True,
        "RATE_LIMIT_REQUESTS_PER_MINUTE": 30 if environment == "production" else 60,
        "RATE_LIMIT_REQUESTS_PER_HOUR": 500 if environment == "production" else 1000,
        "RATE_LIMIT_BURST_SIZE": 5 if environment == "production" else 10,
        
        # Session security
        "SESSION_TIMEOUT_MINUTES": 30 if environment == "production" else 60,
        "MAX_CONCURRENT_SESSIONS": 3,
        
        # API security
        "API_KEY_LENGTH": 32,
        "API_KEY_PREFIX": "sc_",
        
        # Encryption
        "ENCRYPTION_KEY": os.getenv("ENCRYPTION_KEY"),  # Will be generated if not provided
        
        # Audit logging
        "AUDIT_LOG_ENABLED": True,
        "AUDIT_LOG_RETENTION_DAYS": 90 if environment == "production" else 30,
        
        # Input validation
        "MAX_REQUEST_SIZE_MB": 5 if environment == "production" else 10,
        "MAX_FIELD_LENGTH": 1000,
        
        # CORS security
        "CORS_ORIGINS": get_cors_origins(environment),
        "CORS_ALLOW_CREDENTIALS": True,
        "CORS_MAX_AGE": 86400,
        
        # Security headers
        "SECURITY_HEADERS_ENABLED": True,
    }
    
    return SecurityConfig(**config_data)

def get_cors_origins(environment: str) -> list:
    """
    Get CORS origins based on environment.
    
    Args:
        environment: Current environment (development/staging/production)
        
    Returns:
        List of allowed CORS origins
    """
    if environment == "development":
        return ["http://localhost:3000", "http://localhost:3001", "*"]
    elif environment == "staging":
        staging_url = os.getenv("STAGING_FRONTEND_URL", "https://staging.scrapecraft.com")
        return [staging_url, "http://localhost:3000"]
    else:  # production
        prod_url = os.getenv("PRODUCTION_FRONTEND_URL", "https://app.scrapecraft.com")
        return [prod_url]

def create_redis_client() -> redis.Redis:
    """
    Create and configure Redis client for security features.
    
    Returns:
        Configured Redis client
    """
    try:
        # Use Redis URL from settings or environment
        redis_url = os.getenv("REDIS_URL", settings.REDIS_URL)
        
        # Create Redis client with security optimizations
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True,
            health_check_interval=30
        )
        
        # Test connection
        redis_client.ping()
        logger.info("Redis client connected successfully")
        
        return redis_client
        
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        # In development, continue without Redis but with reduced security
        if os.getenv("ENVIRONMENT", "development").lower() == "development":
            logger.warning("Continuing without Redis - rate limiting and caching disabled")
            return None
        else:
            raise RuntimeError("Redis connection required for production security features")

def initialize_security_components() -> bool:
    """
    Initialize all security components.
    
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        logger.info("Initializing security components...")
        
        # Create Redis client
        redis_client = create_redis_client()
        
        # Create and initialize security configuration
        security_config_instance = create_security_config()
        
        if redis_client:
            # Initialize security framework
            initialize_security(security_config_instance, redis_client)
            
            # Initialize authentication service
            initialize_auth_service(redis_client)
            
            logger.info("Security components initialized successfully")
            return True
        else:
            logger.error("Redis client not available - security components not fully initialized")
            return False
            
    except Exception as e:
        logger.error(f"Security initialization failed: {e}")
        return False

def validate_security_environment() -> list:
    """
    Validate security environment and return warnings/errors.
    
    Returns:
        List of security validation messages
    """
    messages = []
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    # Check for required environment variables in production
    if environment == "production":
        required_vars = ["JWT_SECRET", "REDIS_URL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            messages.append(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        
        # Check JWT secret strength
        jwt_secret = os.getenv("JWT_SECRET", "")
        if len(jwt_secret) < 64:
            messages.append("WARNING: JWT_SECRET should be at least 64 characters for production")
        
        # Check for HTTPS
        if not os.getenv("FORCE_HTTPS", "true").lower() == "true":
            messages.append("WARNING: HTTPS should be enforced in production")
    
    else:
        # Development warnings
        if not os.getenv("JWT_SECRET"):
            messages.append("INFO: Using generated JWT secret for development")
        
        messages.append("INFO: Development environment - security settings are relaxed")
    
    return messages

def get_security_middleware():
    """
    Get security middleware for FastAPI application.
    
    Returns:
        SecurityHeadersMiddleware instance or None
    """
    try:
        if security_config and security_config.SECURITY_HEADERS_ENABLED:
            return SecurityHeadersMiddleware()
        return None
    except Exception as e:
        logger.error(f"Failed to create security middleware: {e}")
        return None

def create_default_admin_user() -> bool:
    """
    Create default admin user for initial setup.
    
    Returns:
        True if user created successfully, False otherwise
    """
    try:
        if not auth_service:
            logger.warning("Auth service not initialized - cannot create default admin")
            return False
        
        # Check if admin already exists
        admin_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        existing_user = await auth_service.get_user(admin_username)
        
        if existing_user:
            logger.info(f"Admin user '{admin_username}' already exists")
            return True
        
        # Get admin password from environment or generate secure one
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")
        if not admin_password:
            from app.security.config import PasswordManager
            admin_password = PasswordManager.generate_secure_password(16)
            logger.warning(
                f"Generated admin password: {admin_password}. "
                "Set DEFAULT_ADMIN_PASSWORD environment variable in production."
            )
        
        # Create admin user
        from app.services.enhanced_auth_service import UserCreate, UserRole
        admin_user = UserCreate(
            username=admin_username,
            email=os.getenv("DEFAULT_ADMIN_EMAIL", f"{admin_username}@scrapecraft.com"),
            password=admin_password,
            full_name="Default Administrator",
            role=UserRole.ADMIN
        )
        
        await auth_service.create_user(admin_user)
        logger.info(f"Default admin user '{admin_username}' created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create default admin user: {e}")
        return False

async def setup_application_security(app):
    """
    Setup complete security for FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    try:
        logger.info("Setting up application security...")
        
        # Validate environment
        validation_messages = validate_security_environment()
        for message in validation_messages:
            if message.startswith("ERROR"):
                logger.error(message)
            elif message.startswith("WARNING"):
                logger.warning(message)
            else:
                logger.info(message)
        
        # Initialize security components
        if not initialize_security_components():
            logger.error("Security components initialization failed")
            return False
        
        # Add security middleware
        security_middleware = get_security_middleware()
        if security_middleware:
            app.add_middleware(SecurityHeadersMiddleware)
            logger.info("Security headers middleware added")
        
        # Create default admin user if needed
        if os.getenv("CREATE_DEFAULT_ADMIN", "true").lower() == "true":
            await create_default_admin_user()
        
        # Log security status
        environment = os.getenv("ENVIRONMENT", "development").lower()
        logger.info(f"Application security configured for {environment} environment")
        
        # Security features status
        features = {
            "Authentication": auth_service is not None,
            "Rate Limiting": security_config.RATE_LIMIT_ENABLED if security_config else False,
            "Audit Logging": security_config.AUDIT_LOG_ENABLED if security_config else False,
            "Security Headers": security_config.SECURITY_HEADERS_ENABLED if security_config else False,
            "Encryption": True,
        }
        
        logger.info(f"Security features status: {features}")
        return True
        
    except Exception as e:
        logger.error(f"Application security setup failed: {e}")
        return False

# Security status and health checks
def get_security_status() -> dict:
    """
    Get current security system status.
    
    Returns:
        Dictionary with security system status information
    """
    try:
        status = {
            "security_initialized": security_config is not None,
            "auth_service_initialized": auth_service is not None,
            "redis_connected": False,
            "features": {},
            "environment": os.getenv("ENVIRONMENT", "development").lower(),
        }
        
        # Check Redis connection
        try:
            if auth_service and auth_service.redis:
                auth_service.redis.ping()
                status["redis_connected"] = True
        except:
            pass
        
        # Feature status
        if security_config:
            status["features"] = {
                "rate_limiting": security_config.RATE_LIMIT_ENABLED,
                "audit_logging": security_config.AUDIT_LOG_ENABLED,
                "security_headers": security_config.SECURITY_HEADERS_ENABLED,
                "password_validation": True,
                "jwt_tokens": True,
                "rbac": True,
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get security status: {e}")
        return {"error": str(e)}

def perform_security_health_check() -> dict:
    """
    Perform comprehensive security health check.
    
    Returns:
        Dictionary with health check results
    """
    health_status = {
        "overall_status": "healthy",
        "checks": {},
        "recommendations": [],
    }
    
    try:
        # Check JWT secret
        jwt_secret = os.getenv("JWT_SECRET")
        if jwt_secret:
            health_status["checks"]["jwt_secret"] = {
                "status": "pass" if len(jwt_secret) >= 64 else "warn",
                "message": f"JWT secret length: {len(jwt_secret)} characters"
            }
            if len(jwt_secret) < 64:
                health_status["recommendations"].append("Use longer JWT secret (64+ characters)")
        else:
            health_status["checks"]["jwt_secret"] = {
                "status": "fail",
                "message": "No JWT secret configured"
            }
            health_status["overall_status"] = "unhealthy"
        
        # Check Redis connection
        try:
            if auth_service and auth_service.redis:
                auth_service.redis.ping()
                health_status["checks"]["redis"] = {
                    "status": "pass",
                    "message": "Redis connection healthy"
                }
            else:
                health_status["checks"]["redis"] = {
                    "status": "fail",
                    "message": "Redis not connected"
                }
                health_status["overall_status"] = "degraded"
        except Exception as e:
            health_status["checks"]["redis"] = {
                "status": "fail",
                "message": f"Redis error: {e}"
            }
            health_status["overall_status"] = "degraded"
        
        # Check security components
        if security_config:
            health_status["checks"]["security_config"] = {
                "status": "pass",
                "message": "Security configuration loaded"
            }
        else:
            health_status["checks"]["security_config"] = {
                "status": "fail",
                "message": "Security configuration not loaded"
            }
            health_status["overall_status"] = "unhealthy"
        
        if auth_service:
            health_status["checks"]["auth_service"] = {
                "status": "pass",
                "message": "Authentication service ready"
            }
        else:
            health_status["checks"]["auth_service"] = {
                "status": "fail",
                "message": "Authentication service not ready"
            }
            health_status["overall_status"] = "unhealthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Security health check failed: {e}")
        return {
            "overall_status": "error",
            "error": str(e),
            "checks": {},
            "recommendations": ["Fix security system errors"]
        }