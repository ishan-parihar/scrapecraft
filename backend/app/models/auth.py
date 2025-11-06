"""
Shared user and authentication models to avoid circular imports.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from app.api.common.schemas import BaseSchema


class UserInDB(BaseSchema):
    """User model with database fields."""
    id: str = Field(..., description="User ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    full_name: Optional[str] = Field(None, description="Full name")
    disabled: bool = Field(default=False, description="Whether the user is disabled")
    hashed_password: str = Field(..., description="Hashed password")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")