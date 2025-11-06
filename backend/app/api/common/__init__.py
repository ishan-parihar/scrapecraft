"""
Common API utilities for standardization.

This module provides shared utilities, response models,
middleware, and schemas for consistent API implementation.
"""

from .responses import (
    # Error codes
    ErrorCode,
    
    # Response models
    APIResponse,
    ErrorDetail,
    ResponseMetadata,
    PaginatedResponse,
    
    # Exception classes
    APIException,
    ValidationError,
    NotFoundError,
    UnauthorizedError,
    ForbiddenError,
    BusinessRuleError,
    
    # Utility functions
    create_success_response,
    create_error_response,
    create_paginated_response,
    handle_api_exception,
    
    # Validation utilities
    validate_required_fields,
    validate_email,
    validate_uuid,
    
    # Base request models
    BaseRequest,
    PaginationRequest,
    SortRequest,
    FilterRequest,
)

from .middleware import (
    RequestTrackingMiddleware,
    ErrorHandlingMiddleware,
    CORSMiddleware,
    AuthenticationMiddleware,
    setup_middleware,
)

from .schemas import (
    # Common enums
    Status,
    Priority,
    Classification,
    WorkflowPhase,
    
    # Base schemas
    BaseSchema,
    TimestampedSchema,
    IdentifiedSchema,
    
    # User schemas
    User,
    UserCreate,
    UserUpdate,
    LoginRequest,
    Token,
    TokenData,
    
    # Investigation schemas
    Investigation,
    InvestigationCreate,
    InvestigationUpdate,
    InvestigationTarget,
    InvestigationTargetCreate,
    
    # Pipeline schemas
    Pipeline,
    PipelineCreate,
    PipelineUpdate,
    
    # Message schemas
    MessageRequest,
    MessageResponse,
    
    # Workflow schemas
    WorkflowState,
    WorkflowAction,
    ApprovalRequest,
    
    # Evidence and report schemas
    Evidence,
    EvidenceCreate,
    Report,
    ReportCreate,
    
    # Health check and bulk operations
    HealthCheckResponse,
    BulkOperationRequest,
    BulkOperationResponse,
)

__all__ = [
    # Error codes
    "ErrorCode",
    
    # Response models
    "APIResponse",
    "ErrorDetail", 
    "ResponseMetadata",
    "PaginatedResponse",
    
    # Exception classes
    "APIException",
    "ValidationError",
    "NotFoundError",
    "UnauthorizedError",
    "ForbiddenError",
    "BusinessRuleError",
    
    # Utility functions
    "create_success_response",
    "create_error_response",
    "create_paginated_response",
    "handle_api_exception",
    
    # Validation utilities
    "validate_required_fields",
    "validate_email",
    "validate_uuid",
    
    # Base request models
    "BaseRequest",
    "PaginationRequest",
    "SortRequest",
    "FilterRequest",
    
    # Middleware
    "RequestTrackingMiddleware",
    "ErrorHandlingMiddleware",
    "CORSMiddleware",
    "AuthenticationMiddleware",
    "setup_middleware",
    
    # Common enums
    "Status",
    "Priority",
    "Classification",
    "WorkflowPhase",
    
    # Base schemas
    "BaseSchema",
    "TimestampedSchema",
    "IdentifiedSchema",
    
    # User schemas
    "User",
    "UserCreate",
    "UserUpdate",
    "LoginRequest",
    "Token",
    "TokenData",
    
    # Investigation schemas
    "Investigation",
    "InvestigationCreate",
    "InvestigationUpdate",
    "InvestigationTarget",
    "InvestigationTargetCreate",
    
    # Pipeline schemas
    "Pipeline",
    "PipelineCreate",
    "PipelineUpdate",
    
    # Message schemas
    "MessageRequest",
    "MessageResponse",
    
    # Workflow schemas
    "WorkflowState",
    "WorkflowAction",
    "ApprovalRequest",
    
    # Evidence and report schemas
    "Evidence",
    "EvidenceCreate",
    "Report",
    "ReportCreate",
    
    # Health check and bulk operations
    "HealthCheckResponse",
    "BulkOperationRequest",
    "BulkOperationResponse",
]