"""
Common API utilities and response models for standardization.

This module provides standardized response formats, error handling,
and utility functions for all API endpoints.
"""

from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

# Standard Error Codes
class ErrorCode:
    """Standard error codes for consistent error handling."""
    
    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Authentication/Authorization Errors
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INVALID_TOKEN = "INVALID_TOKEN"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"
    INSUFFICIENT_PERMISSIONS = "INSUFFICIENT_PERMISSIONS"
    
    # Resource Errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    
    # Business Logic Errors
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    OPERATION_NOT_ALLOWED = "OPERATION_NOT_ALLOWED"
    
    # System Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    TIMEOUT = "TIMEOUT"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # External Service Errors
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"
    LLM_SERVICE_ERROR = "LLM_SERVICE_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"


class ErrorDetail(BaseModel):
    """Detailed error information."""
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    field: Optional[str] = Field(default=None, description="Field name for validation errors")


class ResponseMetadata(BaseModel):
    """Response metadata for tracking and versioning."""
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    version: str = Field(default="v1", description="API version")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time in milliseconds")


class APIResponse(BaseModel):
    """Standard API response format."""
    success: bool = Field(..., description="Whether the request was successful")
    data: Optional[Any] = Field(default=None, description="Response data")
    error: Optional[ErrorDetail] = Field(default=None, description="Error information")
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata, description="Response metadata")


class PaginatedResponse(BaseModel):
    """Paginated response wrapper."""
    items: List[Any] = Field(..., description="List of items")
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Items per page")
    total_pages: int = Field(..., description="Total number of pages")


# Custom Exception Classes
class APIException(Exception):
    """Base API exception with standard error format."""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.field = field
        super().__init__(message)


class ValidationError(APIException):
    """Validation error exception."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        super().__init__(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details,
            field=field
        )


class NotFoundError(APIException):
    """Resource not found error exception."""
    
    def __init__(self, resource: str = "Resource"):
        super().__init__(
            error_code=ErrorCode.NOT_FOUND,
            message=f"{resource} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class UnauthorizedError(APIException):
    """Unauthorized access error exception."""
    
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(
            error_code=ErrorCode.UNAUTHORIZED,
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenError(APIException):
    """Forbidden access error exception."""
    
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(
            error_code=ErrorCode.FORBIDDEN,
            message=message,
            status_code=status.HTTP_403_FORBIDDEN
        )


class BusinessRuleError(APIException):
    """Business rule violation error exception."""
    
    def __init__(
        self,
        message: str = "Business rule violation",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            error_code=ErrorCode.BUSINESS_RULE_VIOLATION,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


# Response Utility Functions
def create_success_response(
    data: Any = None,
    message: Optional[str] = None,
    metadata: Optional[ResponseMetadata] = None
) -> APIResponse:
    """Create a successful API response."""
    return APIResponse(
        success=True,
        data=data,
        metadata=metadata or ResponseMetadata()
    )


def create_error_response(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    field: Optional[str] = None,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
) -> HTTPException:
    """Create an error response with HTTPException."""
    error_detail = ErrorDetail(
        code=error_code,
        message=message,
        details=details,
        field=field
    )
    
    response = APIResponse(
        success=False,
        error=error_detail,
        metadata=ResponseMetadata()
    )
    
    return HTTPException(
        status_code=status_code,
        detail=response.dict()
    )


def create_paginated_response(
    items: List[Any],
    total: int,
    page: int,
    page_size: int,
    message: Optional[str] = None
) -> APIResponse:
    """Create a paginated response."""
    total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    paginated_data = PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )
    
    return create_success_response(data=paginated_data)


def handle_api_exception(exc: APIException) -> HTTPException:
    """Convert APIException to HTTPException with standard format."""
    return create_error_response(
        error_code=exc.error_code,
        message=exc.message,
        details=exc.details,
        field=exc.field,
        status_code=exc.status_code
    )


# Logging and Request Tracking
def log_request(request_id: str, method: str, path: str, user_id: Optional[str] = None):
    """Log incoming request."""
    logger.info(
        f"Request {request_id}: {method} {path}",
        extra={
            "request_id": request_id,
            "method": method,
            "path": path,
            "user_id": user_id
        }
    )


def log_response(request_id: str, status_code: int, processing_time_ms: float):
    """Log response."""
    logger.info(
        f"Response {request_id}: {status_code} ({processing_time_ms:.2f}ms)",
        extra={
            "request_id": request_id,
            "status_code": status_code,
            "processing_time_ms": processing_time_ms
        }
    )


def log_error(request_id: str, error: Exception, context: Optional[Dict[str, Any]] = None):
    """Log error."""
    logger.error(
        f"Error {request_id}: {str(error)}",
        extra={
            "request_id": request_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        },
        exc_info=True
    )


# Validation Utilities
def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """Validate that all required fields are present."""
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            details={"missing_fields": missing_fields}
        )


def validate_email(email: str) -> bool:
    """Basic email validation."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


# Common Request Models
class BaseRequest(BaseModel):
    """Base request model with common fields."""
    
    class Config:
        extra = "forbid"  # Prevent additional fields
        str_strip_whitespace = True


class PaginationRequest(BaseRequest):
    """Pagination request parameters."""
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=10, ge=1, le=100, description="Items per page")


class SortRequest(BaseRequest):
    """Sorting request parameters."""
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: Optional[str] = Field(default="asc", pattern="^(asc|desc)$", description="Sort order")


class FilterRequest(BaseRequest):
    """Base filter request."""
    def apply_filters(self, query: Any) -> Any:
        """Apply filters to a query. Override in subclasses."""
        return query