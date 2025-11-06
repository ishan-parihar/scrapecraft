"""
Common Pydantic schemas for API standardization.

This module provides standardized request and response models
for consistent API structure and validation.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
import uuid


# Common Enums
class Status(str, Enum):
    """Standard status values."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RUNNING = "running"
    IDLE = "idle"


class Priority(str, Enum):
    """Standard priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Classification(str, Enum):
    """Standard classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


# Base Models
class BaseSchema(BaseModel):
    """Base schema with common configuration."""
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
        use_enum_values = True


class TimestampedSchema(BaseSchema):
    """Schema with automatic timestamp fields."""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")


class IdentifiedSchema(BaseSchema):
    """Schema with ID field."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")


# User and Authentication Schemas
class UserBase(BaseSchema):
    """Base user schema."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    disabled: bool = Field(default=False, description="Whether the user is disabled")


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v


class UserUpdate(BaseSchema):
    """User update schema."""
    email: Optional[EmailStr] = Field(None, description="Email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name")
    disabled: Optional[bool] = Field(None, description="Whether the user is disabled")


class User(UserBase):
    """Complete user schema."""
    id: str = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# Authentication Schemas
class Token(BaseSchema):
    """Token response schema."""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")


class TokenData(BaseSchema):
    """Token data schema."""
    username: Optional[str] = Field(None, description="Username")
    user_id: Optional[str] = Field(None, description="User ID")
    permissions: List[str] = Field(default_factory=list, description="User permissions")


class LoginRequest(BaseSchema):
    """Login request schema."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# Investigation Schemas
class InvestigationTargetBase(BaseSchema):
    """Base investigation target schema."""
    type: str = Field(..., description="Target type (person, organization, domain, etc.)")
    identifier: str = Field(..., description="Target identifier")
    aliases: List[str] = Field(default_factory=list, description="Alternative identifiers")
    priority: Priority = Field(default=Priority.MEDIUM, description="Investigation priority")
    collection_requirements: Dict[str, Any] = Field(default_factory=dict, description="Collection requirements")


class InvestigationTargetCreate(InvestigationTargetBase):
    """Investigation target creation schema."""
    pass


class InvestigationTarget(InvestigationTargetBase, IdentifiedSchema, TimestampedSchema):
    """Complete investigation target schema."""
    investigation_id: Optional[str] = Field(None, description="Associated investigation ID")


class InvestigationBase(BaseSchema):
    """Base investigation schema."""
    title: str = Field(..., min_length=1, max_length=200, description="Investigation title")
    description: str = Field(..., min_length=1, description="Investigation description")
    classification: Classification = Field(default=Classification.INTERNAL, description="Classification level")
    priority: Priority = Field(default=Priority.MEDIUM, description="Investigation priority")


class InvestigationCreate(InvestigationBase):
    """Investigation creation schema."""
    targets: Optional[List[InvestigationTargetCreate]] = Field(default_factory=list, description="Initial targets")


class InvestigationUpdate(BaseSchema):
    """Investigation update schema."""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Investigation title")
    description: Optional[str] = Field(None, min_length=1, description="Investigation description")
    classification: Optional[Classification] = Field(None, description="Classification level")
    priority: Optional[Priority] = Field(None, description="Investigation priority")
    status: Optional[Status] = Field(None, description="Investigation status")
    current_phase: Optional[str] = Field(None, description="Current investigation phase")


class Investigation(InvestigationBase, IdentifiedSchema, TimestampedSchema):
    """Complete investigation schema."""
    status: Status = Field(default=Status.ACTIVE, description="Investigation status")
    current_phase: str = Field(default="planning", description="Current investigation phase")
    targets: List[InvestigationTarget] = Field(default_factory=list, description="Investigation targets")
    
    # Computed fields
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")


# Pipeline Schemas
class PipelineBase(BaseSchema):
    """Base pipeline schema."""
    name: str = Field(..., min_length=1, max_length=100, description="Pipeline name")
    description: str = Field(..., min_length=1, description="Pipeline description")


class PipelineCreate(PipelineBase):
    """Pipeline creation schema."""
    urls: List[str] = Field(default_factory=list, description="Target URLs")
    extraction_schema: Dict[str, Any] = Field(default_factory=dict, description="Data extraction schema")


class PipelineUpdate(BaseSchema):
    """Pipeline update schema."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Pipeline name")
    description: Optional[str] = Field(None, min_length=1, description="Pipeline description")
    urls: Optional[List[str]] = Field(None, description="Target URLs")
    extraction_schema: Optional[Dict[str, Any]] = Field(None, description="Data extraction schema")
    code: Optional[str] = Field(None, description="Generated code")


class Pipeline(PipelineBase, IdentifiedSchema, TimestampedSchema):
    """Complete pipeline schema."""
    urls: List[str] = Field(default_factory=list, description="Target URLs")
    extraction_schema: Dict[str, Any] = Field(default_factory=dict, description="Data extraction schema")
    code: str = Field(default="", description="Generated code")
    status: Status = Field(default=Status.IDLE, description="Pipeline status")


# Chat and Message Schemas
class MessageBase(BaseSchema):
    """Base message schema."""
    message: str = Field(..., min_length=1, description="Message content")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Message context")


class MessageRequest(MessageBase):
    """Message request schema."""
    pipeline_id: str = Field(..., description="Associated pipeline ID")


class MessageResponse(BaseSchema):
    """Message response schema."""
    response: str = Field(..., description="Response content")
    urls: List[str] = Field(default_factory=list, description="Extracted URLs")
    extraction_schema: Dict[str, Any] = Field(default_factory=dict, description="Generated schema")
    code: Optional[str] = Field(None, description="Generated code")
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Extraction results")
    status: str = Field(..., description="Response status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# Workflow Schemas
class WorkflowPhase(str, Enum):
    """Workflow phases."""
    PLANNING = "planning"
    RECONNAISSANCE = "reconnaissance"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    REPORTING = "reporting"


class WorkflowState(BaseSchema):
    """Workflow state schema."""
    phase: WorkflowPhase = Field(..., description="Current phase")
    status: Status = Field(default=Status.ACTIVE, description="Workflow status")
    progress: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WorkflowAction(BaseSchema):
    """Workflow action schema."""
    action_id: str = Field(..., description="Action ID")
    type: str = Field(..., description="Action type")
    description: str = Field(..., description="Action description")
    requires_approval: bool = Field(default=False, description="Whether action requires approval")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Action metadata")


class ApprovalRequest(BaseSchema):
    """Approval request schema."""
    approval_id: str = Field(..., description="Approval ID")
    approved: bool = Field(..., description="Approval decision")
    reason: Optional[str] = Field(None, description="Approval reason")


# Evidence and Report Schemas
class EvidenceBase(BaseSchema):
    """Base evidence schema."""
    source: str = Field(..., description="Evidence source")
    source_type: str = Field(..., description="Source type")
    content: str = Field(..., description="Evidence content")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Evidence metadata")
    reliability_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Reliability score")
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance score")


class EvidenceCreate(EvidenceBase):
    """Evidence creation schema."""
    investigation_id: str = Field(..., description="Associated investigation ID")


class Evidence(EvidenceBase, IdentifiedSchema, TimestampedSchema):
    """Complete evidence schema."""
    investigation_id: str = Field(..., description="Associated investigation ID")
    collected_at: datetime = Field(default_factory=datetime.utcnow, description="Collection timestamp")


class ReportBase(BaseSchema):
    """Base report schema."""
    title: str = Field(..., min_length=1, description="Report title")
    content: str = Field(..., min_length=1, description="Report content")
    format: str = Field(default="markdown", description="Report format")
    classification: Classification = Field(default=Classification.INTERNAL, description="Classification level")
    recipients: List[str] = Field(default_factory=list, description="Report recipients")


class ReportCreate(ReportBase):
    """Report creation schema."""
    investigation_id: str = Field(..., description="Associated investigation ID")


class Report(ReportBase, IdentifiedSchema, TimestampedSchema):
    """Complete report schema."""
    investigation_id: str = Field(..., description="Associated investigation ID")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Generation timestamp")


# Health Check Schemas
class HealthCheckResponse(BaseSchema):
    """Health check response schema."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Service statuses")


# Pagination Schemas
class PaginationRequest(BaseSchema):
    """Pagination request schema."""
    page: int = Field(default=1, ge=1, description="Page number (starting from 1)")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")
    offset: Optional[int] = Field(None, ge=0, description="Number of items to skip")


# Bulk Operation Schemas
class BulkOperationRequest(BaseSchema):
    """Bulk operation request schema."""
    operation: str = Field(..., description="Operation type")
    items: List[str] = Field(..., description="Item IDs")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Operation parameters")


class BulkOperationResponse(BaseSchema):
    """Bulk operation response schema."""
    operation: str = Field(..., description="Operation type")
    total: int = Field(..., description="Total items processed")
    successful: int = Field(..., description="Successful operations")
    failed: int = Field(..., description="Failed operations")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Operation errors")