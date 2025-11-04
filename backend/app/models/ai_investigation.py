"""
AI Investigation Models

Pydantic models for AI investigations.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class InvestigationPhase(str, Enum):
    PLANNING = "planning"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"

class InvestigationStatus(str, Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class InvestigationRequest(BaseModel):
    target: str = Field(..., description="Investigation target")
    objective: str = Field(..., description="Investigation objective")
    scope: List[str] = Field(default_factory=list, description="Investigation scope")
    priority: str = Field(default="medium", description="Investigation priority")
    requirements: Dict[str, Any] = Field(default_factory=dict)

class InvestigationResponse(BaseModel):
    investigation_id: str
    status: str
    current_phase: InvestigationPhase
    progress_percentage: float
    estimated_completion: Optional[datetime] = None
    message: str

class InvestigationState(BaseModel):
    investigation_id: str
    target: str
    objective: str
    scope: List[str]
    priority: str
    requirements: Dict[str, Any]
    status: InvestigationStatus
    current_phase: InvestigationPhase
    progress_percentage: float
    created_at: datetime
    updated_at: datetime
    phases_completed: List[str]
    results: Dict[str, Any]
    errors: List[str]

class AgentExecutionLog(BaseModel):
    agent_id: str
    agent_type: str
    investigation_id: str
    phase: InvestigationPhase
    execution_start: datetime
    execution_end: Optional[datetime] = None
    status: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

class InvestigationReport(BaseModel):
    investigation_id: str
    target: str
    objective: str
    summary: str
    findings: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    sources: List[str]
    metadata: Dict[str, Any]
    generated_at: datetime
    status: InvestigationStatus