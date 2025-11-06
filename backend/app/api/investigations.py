"""
Consolidated Investigation API - Standardized

This module provides unified investigation management by consolidating
functionality from both ai_investigation and osint APIs with standardized
patterns and consistent response formats.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)

from app.api.common.responses import (
    APIResponse, ErrorCode, ValidationError, NotFoundError, 
    BusinessRuleError, create_success_response, create_error_response,
    create_paginated_response, validate_required_fields
)
from app.api.common.schemas import (
    Investigation, InvestigationCreate, InvestigationUpdate,
    InvestigationTarget, InvestigationTargetCreate, Status, Priority,
    Classification, PaginationRequest, WorkflowPhase, Evidence, EvidenceCreate,
    Report, ReportCreate, BulkOperationRequest, BulkOperationResponse
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/investigations", tags=["Investigations"])

# In-memory storage for demonstration (replace with database)
investigations_db: Dict[str, Investigation] = {}
targets_db: Dict[str, InvestigationTarget] = {}
evidence_db: Dict[str, Evidence] = {}
reports_db: Dict[str, Report] = {}

# Initialize real data from storage if available
def initialize_real_data():
    """Initialize real investigation data from storage."""
    try:
        from app.services.investigation_storage import load_investigations
        
        loaded_investigations = load_investigations()
        for inv in loaded_investigations:
            investigations_db[inv.id] = inv
            
        logger.info(f"Loaded {len(loaded_investigations)} investigations from storage")
    except Exception as e:
        logger.error(f"Failed to load investigations: {e}")

# Replace test initialization with real data loading
initialize_real_data()

# Helper functions
def get_investigation_by_id(investigation_id: str) -> Optional[Investigation]:
    """Get investigation by ID."""
    return investigations_db.get(investigation_id)

def validate_investigation_exists(investigation_id: str) -> Investigation:
    """Validate investigation exists and return it."""
    investigation = get_investigation_by_id(investigation_id)
    if not investigation:
        raise NotFoundError("Investigation")
    return investigation

def validate_phase_transition(current_phase: str, target_phase: str) -> bool:
    """Validate if phase transition is allowed."""
    allowed_transitions = {
        "planning": ["reconnaissance"],
        "reconnaissance": ["collection"],
        "collection": ["analysis"],
        "analysis": ["synthesis"],
        "synthesis": ["reporting"],
        "reporting": [],
    }
    return target_phase in allowed_transitions.get(current_phase, [])

# Main Investigation Endpoints

@router.post("", response_model=APIResponse)
async def create_investigation(
    investigation_data: InvestigationCreate,
    background_tasks: BackgroundTasks
) -> APIResponse:
    """
    Create a new investigation.
    
    Args:
        investigation_data: Investigation creation data
        background_tasks: FastAPI background tasks
        
    Returns:
        APIResponse with created investigation
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Validate required fields
        validate_required_fields(
            investigation_data.dict(),
            ["title", "description"]
        )
        
        # Create investigation
        investigation_id = f"inv-{str(uuid.uuid4())[:8]}"
        
        investigation = Investigation(
            id=investigation_id,
            title=investigation_data.title,
            description=investigation_data.description,
            classification=investigation_data.classification,
            priority=investigation_data.priority,
            status=Status.ACTIVE,
            current_phase="planning",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Store investigation
        investigations_db[investigation_id] = investigation
        
        # Create initial targets if provided
        for target_data in investigation_data.targets or []:
            target_id = f"tgt-{str(uuid.uuid4())[:8]}"
            target = InvestigationTarget(
                id=target_id,
                investigation_id=investigation_id,
                type=target_data.type,
                identifier=target_data.identifier,
                aliases=target_data.aliases,
                priority=target_data.priority,
                collection_requirements=target_data.collection_requirements,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            targets_db[target_id] = target
            investigation.targets.append(target)
        
        logger.info(f"Created investigation: {investigation_id}")
        
        # Schedule AI analysis in background
        background_tasks.add_task(
            schedule_investigation_planning,
            investigation_id
        )
        
        return create_success_response(
            data=investigation.dict(),
            message="Investigation created successfully"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Create investigation error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to create investigation",
            details={"error": str(e)}
        )

@router.get("", response_model=APIResponse)
async def list_investigations(
    pagination: PaginationRequest = Depends(),
    classification: Optional[Classification] = Query(None, description="Filter by classification"),
    status: Optional[Status] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search term")
) -> APIResponse:
    """
    List investigations with filtering and pagination.
    
    Args:
        pagination: Pagination parameters
        classification: Filter by classification
        status: Filter by status
        priority: Filter by priority
        search: Search term
        
    Returns:
        APIResponse with paginated investigations
    """
    try:
        # Get all investigations
        investigations = list(investigations_db.values())
        
        # Apply filters
        if classification:
            investigations = [inv for inv in investigations if inv.classification == classification]
        if status:
            investigations = [inv for inv in investigations if inv.status == status]
        if priority:
            investigations = [inv for inv in investigations if inv.priority == priority]
        if search:
            search_lower = search.lower()
            investigations = [
                inv for inv in investigations 
                if search_lower in inv.title.lower() or search_lower in inv.description.lower()
            ]
        
        # Sort by creation date (newest first)
        investigations.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total = len(investigations)
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        paginated_items = investigations[start_idx:end_idx]
        
        return create_paginated_response(
            items=[inv.dict() for inv in paginated_items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
    except Exception as e:
        logger.error(f"List investigations error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve investigations",
            details={"error": str(e)}
        )

@router.get("/{investigation_id}", response_model=APIResponse)
async def get_investigation(investigation_id: str) -> APIResponse:
    """
    Get investigation by ID.
    
    Args:
        investigation_id: Investigation ID
        
    Returns:
        APIResponse with investigation data
        
    Raises:
        NotFoundError: If investigation not found
    """
    try:
        investigation = validate_investigation_exists(investigation_id)
        
        # Get related data
        investigation_targets = [
            target for target in targets_db.values() 
            if target.investigation_id == investigation_id
        ]
        investigation_evidence = [
            evidence for evidence in evidence_db.values() 
            if evidence.investigation_id == investigation_id
        ]
        investigation_reports = [
            report for report in reports_db.values() 
            if report.investigation_id == investigation_id
        ]
        
        # Build complete investigation data
        investigation_data = investigation.dict()
        investigation_data["targets"] = [target.dict() for target in investigation_targets]
        investigation_data["evidence"] = [evidence.dict() for evidence in investigation_evidence]
        investigation_data["reports"] = [report.dict() for report in investigation_reports]
        
        return create_success_response(
            data=investigation_data,
            message="Investigation retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Get investigation error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve investigation",
            details={"error": str(e)}
        )

@router.put("/{investigation_id}", response_model=APIResponse)
async def update_investigation(
    investigation_id: str,
    update_data: InvestigationUpdate
) -> APIResponse:
    """
    Update investigation.
    
    Args:
        investigation_id: Investigation ID
        update_data: Update data
        
    Returns:
        APIResponse with updated investigation
        
    Raises:
        NotFoundError: If investigation not found
        BusinessRuleError: If business rules are violated
    """
    try:
        investigation = validate_investigation_exists(investigation_id)
        
        # Validate phase transition if phase is being updated
        if update_data.current_phase and update_data.current_phase != investigation.current_phase:
            if not validate_phase_transition(investigation.current_phase, update_data.current_phase):
                raise BusinessRuleError(
                    message=f"Cannot transition from {investigation.current_phase} to {update_data.current_phase}",
                    details={
                        "current_phase": investigation.current_phase,
                        "target_phase": update_data.current_phase
                    }
                )
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(investigation, field, value)
        
        investigation.updated_at = datetime.utcnow()
        
        # Update progress based on phase
        investigation.progress_percentage = calculate_progress_percentage(investigation.current_phase)
        
        logger.info(f"Updated investigation: {investigation_id}")
        
        return create_success_response(
            data=investigation.dict(),
            message="Investigation updated successfully"
        )
        
    except (NotFoundError, BusinessRuleError):
        raise
    except Exception as e:
        logger.error(f"Update investigation error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to update investigation",
            details={"error": str(e)}
        )

@router.delete("/{investigation_id}", response_model=APIResponse)
async def delete_investigation(investigation_id: str) -> APIResponse:
    """
    Delete investigation.
    
    Args:
        investigation_id: Investigation ID
        
    Returns:
        APIResponse with success message
        
    Raises:
        NotFoundError: If investigation not found
        BusinessRuleError: If investigation cannot be deleted
    """
    try:
        investigation = validate_investigation_exists(investigation_id)
        
        # Check if investigation can be deleted
        if investigation.status == Status.RUNNING:
            raise BusinessRuleError(
                message="Cannot delete investigation that is currently running",
                details={"status": investigation.status}
            )
        
        # Delete related data
        targets_to_delete = [
            target_id for target_id, target in targets_db.items()
            if target.investigation_id == investigation_id
        ]
        for target_id in targets_to_delete:
            del targets_db[target_id]
        
        evidence_to_delete = [
            evidence_id for evidence_id, evidence in evidence_db.items()
            if evidence.investigation_id == investigation_id
        ]
        for evidence_id in evidence_to_delete:
            del evidence_db[evidence_id]
        
        reports_to_delete = [
            report_id for report_id, report in reports_db.items()
            if report.investigation_id == investigation_id
        ]
        for report_id in reports_to_delete:
            del reports_db[report_id]
        
        # Delete investigation
        del investigations_db[investigation_id]
        
        logger.info(f"Deleted investigation: {investigation_id}")
        
        return create_success_response(
            message="Investigation deleted successfully"
        )
        
    except (NotFoundError, BusinessRuleError):
        raise
    except Exception as e:
        logger.error(f"Delete investigation error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to delete investigation",
            details={"error": str(e)}
        )

# Target Management Endpoints

@router.post("/{investigation_id}/targets", response_model=APIResponse)
async def create_target(investigation_id: str, target_data: InvestigationTargetCreate) -> APIResponse:
    """
    Create target for investigation.
    
    Args:
        investigation_id: Investigation ID
        target_data: Target creation data
        
    Returns:
        APIResponse with created target
    """
    try:
        validate_investigation_exists(investigation_id)
        
        target_id = f"tgt-{str(uuid.uuid4())[:8]}"
        target = InvestigationTarget(
            id=target_id,
            investigation_id=investigation_id,
            type=target_data.type,
            identifier=target_data.identifier,
            aliases=target_data.aliases,
            priority=target_data.priority,
            collection_requirements=target_data.collection_requirements,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        targets_db[target_id] = target
        
        # Add to investigation
        investigation = investigations_db[investigation_id]
        investigation.targets.append(target)
        investigation.updated_at = datetime.utcnow()
        
        logger.info(f"Created target: {target_id} for investigation: {investigation_id}")
        
        return create_success_response(
            data=target.dict(),
            message="Target created successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Create target error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to create target",
            details={"error": str(e)}
        )

# Evidence Management Endpoints

@router.post("/{investigation_id}/evidence", response_model=APIResponse)
async def create_evidence(investigation_id: str, evidence_data: EvidenceCreate) -> APIResponse:
    """
    Create evidence for investigation.
    
    Args:
        investigation_id: Investigation ID
        evidence_data: Evidence creation data
        
    Returns:
        APIResponse with created evidence
    """
    try:
        validate_investigation_exists(investigation_id)
        
        evidence_id = f"ev-{str(uuid.uuid4())[:8]}"
        evidence = Evidence(
            id=evidence_id,
            investigation_id=investigation_id,
            source=evidence_data.source,
            source_type=evidence_data.source_type,
            content=evidence_data.content,
            metadata=evidence_data.metadata,
            reliability_score=evidence_data.reliability_score,
            relevance_score=evidence_data.relevance_score,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            collected_at=datetime.utcnow()
        )
        
        evidence_db[evidence_id] = evidence
        
        logger.info(f"Created evidence: {evidence_id} for investigation: {investigation_id}")
        
        return create_success_response(
            data=evidence.dict(),
            message="Evidence created successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Create evidence error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to create evidence",
            details={"error": str(e)}
        )

# Report Management Endpoints

@router.post("/{investigation_id}/reports", response_model=APIResponse)
async def create_report(investigation_id: str, report_data: ReportCreate) -> APIResponse:
    """
    Create report for investigation.
    
    Args:
        investigation_id: Investigation ID
        report_data: Report creation data
        
    Returns:
        APIResponse with created report
    """
    try:
        validate_investigation_exists(investigation_id)
        
        report_id = f"rep-{str(uuid.uuid4())[:8]}"
        report = Report(
            id=report_id,
            investigation_id=investigation_id,
            title=report_data.title,
            content=report_data.content,
            format=report_data.format,
            classification=report_data.classification,
            recipients=report_data.recipients,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            generated_at=datetime.utcnow()
        )
        
        reports_db[report_id] = report
        
        logger.info(f"Created report: {report_id} for investigation: {investigation_id}")
        
        return create_success_response(
            data=report.dict(),
            message="Report created successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Create report error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to create report",
            details={"error": str(e)}
        )

# Workflow Management Endpoints

@router.post("/{investigation_id}/advance-phase", response_model=APIResponse)
async def advance_phase(
    investigation_id: str,
    target_phase: WorkflowPhase,
    reason: Optional[str] = None
) -> APIResponse:
    """
    Advance investigation to next phase.
    
    Args:
        investigation_id: Investigation ID
        target_phase: Target phase
        reason: Transition reason
        
    Returns:
        APIResponse with updated investigation
    """
    try:
        investigation = validate_investigation_exists(investigation_id)
        
        # Validate transition
        if not validate_phase_transition(investigation.current_phase, target_phase.value):
            raise BusinessRuleError(
                message=f"Cannot transition from {investigation.current_phase} to {target_phase.value}",
                details={
                    "current_phase": investigation.current_phase,
                    "target_phase": target_phase.value
                }
            )
        
        # Advance phase
        old_phase = investigation.current_phase
        investigation.current_phase = target_phase.value
        investigation.progress_percentage = calculate_progress_percentage(target_phase.value)
        investigation.updated_at = datetime.utcnow()
        
        logger.info(f"Advanced investigation {investigation_id} from {old_phase} to {target_phase.value}")
        
        return create_success_response(
            data=investigation.dict(),
            message=f"Advanced to {target_phase.value} phase"
        )
        
    except (NotFoundError, BusinessRuleError):
        raise
    except Exception as e:
        logger.error(f"Advance phase error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to advance phase",
            details={"error": str(e)}
        )

# Utility Functions

async def schedule_investigation_planning(investigation_id: str):
    """Schedule AI-powered investigation planning."""
    try:
        # Integrate with AI investigation service
        from app.services.ai_investigation import AIInvestigationService
        
        logger.info(f"Scheduled AI planning for investigation: {investigation_id}")
        
        investigation = investigations_db.get(investigation_id)
        if not investigation:
            logger.error(f"Investigation not found: {investigation_id}")
            return
        
        # Initialize AI investigation service
        ai_service = AIInvestigationService()
        
        # Run AI planning
        try:
            planning_result = await ai_service.plan_investigation(
                target=investigation.target,
                objectives=investigation.objectives,
                scope=investigation.scope
            )
            
            # Update investigation with AI planning results
            investigation.status = Status.RUNNING
            investigation.updated_at = datetime.utcnow()
            
            # Store AI planning results
            if hasattr(investigation, 'ai_planning'):
                investigation.ai_planning = planning_result
            else:
                investigation.metadata['ai_planning'] = planning_result
            
            logger.info(f"AI planning completed for investigation: {investigation_id}")
            
        except Exception as ai_error:
            logger.error(f"AI planning failed for investigation {investigation_id}: {ai_error}")
            investigation.status = Status.FAILED
            investigation.error = str(ai_error)
            investigation.updated_at = datetime.utcnow()
            
    except Exception as e:
        logger.error(f"AI planning error for investigation {investigation_id}: {e}")
        # Fallback to manual status
        investigation = investigations_db.get(investigation_id)
        if investigation:
            investigation.status = Status.PLANNING
            investigation.updated_at = datetime.utcnow()

def calculate_progress_percentage(phase: str) -> float:
    """Calculate progress percentage based on phase."""
    phase_progress = {
        "planning": 10.0,
        "reconnaissance": 25.0,
        "collection": 50.0,
        "analysis": 75.0,
        "synthesis": 90.0,
        "reporting": 100.0,
    }
    return phase_progress.get(phase, 0.0)