"""
AI Investigation API

API endpoints for AI-powered OSINT investigations.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

from app.services.ai_investigation import AIInvestigationService, InvestigationRequest, InvestigationResponse

router = APIRouter(prefix="/api/ai-investigation", tags=["AI Investigation"])

# Dependency to get investigation service
def get_investigation_service():
    return AIInvestigationService()

class InvestigationPhase(str, Enum):
    PLANNING = "planning"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"

class InvestigationRequestModel(BaseModel):
    target: str = Field(..., description="Investigation target")
    objective: str = Field(..., description="Investigation objective")
    scope: List[str] = Field(default_factory=list, description="Investigation scope")
    priority: str = Field(default="medium", description="Investigation priority")
    requirements: Dict[str, Any] = Field(default_factory=dict)

class InvestigationResponseModel(BaseModel):
    investigation_id: str
    status: str
    current_phase: InvestigationPhase
    progress_percentage: float
    estimated_completion: datetime = None
    message: str

class PhaseApprovalRequest(BaseModel):
    phase: str = Field(..., description="Phase to approve")
    notes: str = Field(default="", description="Approval notes")

@router.post("/start", response_model=InvestigationResponseModel)
async def start_investigation(
    request: InvestigationRequestModel,
    background_tasks: BackgroundTasks,
    service: AIInvestigationService = Depends(get_investigation_service)
) -> InvestigationResponseModel:
    """Start a new AI-powered OSINT investigation"""
    try:
        # Convert request model to service request
        investigation_request = InvestigationRequest(
            target=request.target,
            objective=request.objective,
            scope=request.scope,
            priority=request.priority,
            requirements=request.requirements
        )
        
        # Start investigation
        result = await service.start_investigation(investigation_request)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return InvestigationResponseModel(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{investigation_id}/status")
async def get_investigation_status(
    investigation_id: str,
    service: AIInvestigationService = Depends(get_investigation_service)
) -> Dict[str, Any]:
    """Get investigation status"""
    try:
        result = await service.get_investigation_status(investigation_id)
        
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{investigation_id}/approve-phase")
async def approve_investigation_phase(
    investigation_id: str,
    approval: PhaseApprovalRequest,
    service: AIInvestigationService = Depends(get_investigation_service)
) -> Dict[str, Any]:
    """Approve investigation phase"""
    try:
        result = await service.approve_phase(investigation_id, approval.phase)
        
        if result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{investigation_id}/report")
async def get_investigation_report(
    investigation_id: str,
    service: AIInvestigationService = Depends(get_investigation_service)
) -> Dict[str, Any]:
    """Get investigation report"""
    try:
        status_result = await service.get_investigation_status(investigation_id)
        
        if status_result.get("status") == "not_found":
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        if status_result.get("status") != "completed":
            raise HTTPException(status_code=400, detail="Investigation not completed yet")
        
        return {
            "investigation_id": investigation_id,
            "report": status_result.get("results", {}),
            "generated_at": datetime.utcnow(),
            "status": "completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/active")
async def get_active_investigations(
    service: AIInvestigationService = Depends(get_investigation_service)
) -> List[Dict[str, Any]]:
    """Get all active investigations"""
    try:
        active_investigations = []
        
        for investigation_id, investigation in service.active_investigations.items():
            if investigation["status"] in ["initializing", "running"]:
                active_investigations.append({
                    "investigation_id": investigation_id,
                    "target": investigation["target"],
                    "objective": investigation["objective"],
                    "status": investigation["status"],
                    "current_phase": investigation["current_phase"],
                    "progress_percentage": investigation["progress_percentage"],
                    "created_at": investigation["created_at"]
                })
        
        return active_investigations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{investigation_id}")
async def cancel_investigation(
    investigation_id: str,
    service: AIInvestigationService = Depends(get_investigation_service)
) -> Dict[str, Any]:
    """Cancel an investigation"""
    try:
        if investigation_id not in service.active_investigations:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        investigation = service.active_investigations[investigation_id]
        
        if investigation["status"] == "completed":
            raise HTTPException(status_code=400, detail="Cannot cancel completed investigation")
        
        # Update status to cancelled
        investigation["status"] = "cancelled"
        investigation["updated_at"] = datetime.utcnow()
        
        return {
            "investigation_id": investigation_id,
            "status": "cancelled",
            "message": "Investigation cancelled successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))