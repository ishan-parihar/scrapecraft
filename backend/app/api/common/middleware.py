"""
API middleware for request tracking, logging, and error handling.

This module provides middleware functions to ensure consistent
request handling across all API endpoints.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .responses import APIException, handle_api_exception, log_request, log_response, log_error

logger = logging.getLogger(__name__)


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking requests and responses with consistent logging."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID and start timing
        request_id = request.headers.get("X-Request-ID") or f"req-{int(time.time() * 1000)}"
        start_time = time.time()
        
        # Add request ID to request state for use in endpoints
        request.state.request_id = request_id
        request.state.start_time = start_time
        
        # Log incoming request
        user_id = getattr(request.state, "user_id", None)
        log_request(request_id, request.method, str(request.url.path), user_id)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # Log successful response
            log_response(request_id, response.status_code, processing_time)
            
            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
            
            return response
            
        except Exception as exc:
            # Calculate processing time for errors
            processing_time = (time.time() - start_time) * 1000
            
            # Log error
            log_error(request_id, exc, {"method": request.method, "path": str(request.url.path)})
            
            # Handle different exception types
            if isinstance(exc, APIException):
                http_exc = handle_api_exception(exc)
            elif isinstance(exc, HTTPException):
                http_exc = exc
            else:
                # Convert unknown exceptions to standard format
                from .responses import create_error_response, ErrorCode
                http_exc = create_error_response(
                    error_code=ErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred",
                    details={"exception_type": type(exc).__name__}
                )
            
            # Create JSON response with standard format
            response_content = http_exc.detail
            if isinstance(response_content, str):
                # Handle legacy error responses
                from .responses import APIResponse, ErrorDetail, ResponseMetadata
                response_content = APIResponse(
                    success=False,
                    error=ErrorDetail(
                        code=ErrorCode.INTERNAL_ERROR,
                        message=response_content
                    ),
                    metadata=ResponseMetadata()
                ).dict()
            
            response = JSONResponse(
                status_code=http_exc.status_code,
                content=response_content
            )
            
            # Add tracking headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time"] = f"{processing_time:.2f}ms"
            
            return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for consistent error handling and response formatting."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except APIException as exc:
            # Handle custom API exceptions
            http_exc = handle_api_exception(exc)
            return JSONResponse(
                status_code=http_exc.status_code,
                content=http_exc.detail
            )
        except HTTPException as exc:
            # Handle FastAPI HTTP exceptions - convert to standard format
            if isinstance(exc.detail, dict) and "success" in exc.detail:
                # Already in standard format
                return JSONResponse(
                    status_code=exc.status_code,
                    content=exc.detail
                )
            else:
                # Convert to standard format
                from .responses import APIResponse, ErrorDetail, ResponseMetadata, ErrorCode
                standard_response = APIResponse(
                    success=False,
                    error=ErrorDetail(
                        code=self._get_error_code_from_status(exc.status_code),
                        message=str(exc.detail)
                    ),
                    metadata=ResponseMetadata()
                )
                return JSONResponse(
                    status_code=exc.status_code,
                    content=standard_response.dict()
                )
        except Exception as exc:
            # Handle unexpected exceptions
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            
            from .responses import APIResponse, ErrorDetail, ResponseMetadata, ErrorCode
            standard_response = APIResponse(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message="An unexpected error occurred",
                    details={"exception_type": type(exc).__name__}
                ),
                metadata=ResponseMetadata()
            )
            return JSONResponse(
                status_code=500,
                content=standard_response.dict()
            )
    
    def _get_error_code_from_status(self, status_code: int) -> str:
        """Map HTTP status codes to standard error codes."""
        from .responses import ErrorCode
        
        mapping = {
            400: ErrorCode.VALIDATION_ERROR,
            401: ErrorCode.UNAUTHORIZED,
            403: ErrorCode.FORBIDDEN,
            404: ErrorCode.NOT_FOUND,
            409: ErrorCode.RESOURCE_CONFLICT,
            422: ErrorCode.VALIDATION_ERROR,
            429: ErrorCode.RATE_LIMIT_EXCEEDED,
            500: ErrorCode.INTERNAL_ERROR,
            502: ErrorCode.EXTERNAL_SERVICE_ERROR,
            503: ErrorCode.SERVICE_UNAVAILABLE,
            504: ErrorCode.TIMEOUT,
        }
        
        return mapping.get(status_code, ErrorCode.INTERNAL_ERROR)


class CORSMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with proper security headers."""
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins: list = None,
        allow_methods: list = None,
        allow_headers: list = None,
        allow_credentials: bool = True
    ):
        super().__init__(app)
        self.allow_origins = allow_origins or ["http://localhost:3000", "http://localhost:3001"]
        self.allow_methods = allow_methods or ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
        self.allow_headers = allow_headers or ["*"]
        self.allow_credentials = allow_credentials
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
        else:
            response = await call_next(request)
        
        # Add CORS headers
        if origin in self.allow_origins or "*" in self.allow_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allow_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allow_headers)
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication and authorization."""
    
    # Paths that don't require authentication
    PUBLIC_PATHS = {
        "/api/auth/login",
        "/api/auth/register",
        "/api/health",
        "/docs",
        "/openapi.json",
        "/redoc"
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip authentication for public paths
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            from .responses import create_error_response, ErrorCode
            http_exc = create_error_response(
                error_code=ErrorCode.UNAUTHORIZED,
                message="Missing or invalid authorization header",
                status_code=401
            )
            return JSONResponse(
                status_code=401,
                content=http_exc.detail
            )
        
        token = auth_header.split(" ")[1]
        
        try:
            # Validate token and extract user info
            # This would integrate with your actual authentication service
            user_info = await self._validate_token(token)
            
            # Add user info to request state
            request.state.user_id = user_info.get("user_id")
            request.state.user = user_info
            
            return await call_next(request)
            
        except Exception as exc:
            logger.warning(f"Authentication failed: {exc}")
            from .responses import create_error_response, ErrorCode
            http_exc = create_error_response(
                error_code=ErrorCode.INVALID_TOKEN,
                message="Invalid or expired token",
                status_code=401
            )
            return JSONResponse(
                status_code=401,
                content=http_exc.detail
            )
    
    async def _validate_token(self, token: str) -> dict:
        """Validate JWT token and return user information."""
        # This would integrate with your actual JWT validation logic
        # For now, return a placeholder user info
        import jwt
        from app.config import settings
        
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return {
                "user_id": payload.get("sub"),
                "username": payload.get("username"),
                "permissions": payload.get("permissions", [])
            }
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except jwt.InvalidTokenError:
            raise Exception("Invalid token")


def setup_middleware(app):
    """Setup all middleware for the FastAPI application."""
    # Add CORS middleware first
    app.add_middleware(CORSMiddleware)
    
    # Add error handling middleware
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Add request tracking middleware
    app.add_middleware(RequestTrackingMiddleware)
    
    # Add authentication middleware (last, so it runs first)
    app.add_middleware(AuthenticationMiddleware)