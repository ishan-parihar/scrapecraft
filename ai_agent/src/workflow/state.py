"""
Investigation State Management

This module defines the state structure for OSINT investigations
using LangGraph's state management system.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class InvestigationPhase(Enum):
    """Phases of an OSINT investigation"""
    PLANNING = "planning"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    COMPLETED = "completed"
    FAILED = "failed"


class InvestigationStatus(Enum):
    """Status of investigation components"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class InvestigationState(TypedDict):
    """
    State for OSINT investigation workflow.
    
    This TypedDict defines the structure of the state that flows through
    the LangGraph workflow, containing all information needed for
    investigation phases.
    """
    
    # === INPUT SECTION ===
    # Primary user request that initiates the investigation
    user_request: str
    
    # Unique identifier for this investigation
    investigation_id: str
    
    # Timestamp when investigation was initiated
    initiated_at: datetime
    
    # User or system that initiated the investigation
    initiator: str
    
    # Priority level of the investigation
    priority: str  # "low", "medium", "high", "critical"
    
    # === PHASE 1: PLANNING ===
    # Defined objectives from ObjectiveDefinitionAgent
    objectives: Dict[str, Any]
    
    # Investigation strategy from StrategyFormulationAgent
    strategy: Dict[str, Any]
    
    # Planning phase status
    planning_status: InvestigationStatus
    
    # Planning phase metadata
    planning_metadata: Dict[str, Any]
    
    # === PHASE 2: COLLECTION ===
    # Search coordination results
    search_coordination_results: Dict[str, Any]
    
    # Raw data collected from various sources
    search_results: Dict[str, List[Dict[str, Any]]]
    
    # Consolidated raw data
    raw_data: Dict[str, Any]
    
    # Collection phase status for each agent
    collection_status: Dict[str, InvestigationStatus]
    
    # Collection phase metadata
    collection_metadata: Dict[str, Any]
    
    # Data quality metrics
    data_quality_metrics: Dict[str, float]
    
    # === PHASE 3: ANALYSIS ===
    # Fused and correlated data
    fused_data: Dict[str, Any]
    
    # Detected patterns and anomalies
    patterns: List[Dict[str, Any]]
    
    # Contextual analysis results
    context_analysis: Dict[str, Any]
    
    # Analysis phase status
    analysis_status: Dict[str, InvestigationStatus]
    
    # Analysis phase metadata
    analysis_metadata: Dict[str, Any]
    
    # Confidence scores for analysis results
    analysis_confidence: Dict[str, float]
    
    # === PHASE 4: SYNTHESIS ===
    # Synthesized intelligence
    intelligence: Dict[str, Any]
    
    # Quality assessment results
    quality_assessment: Dict[str, Any]
    
    # Final investigation report
    final_report: Dict[str, Any]
    
    # Alternative report formats
    alternative_formats: Dict[str, Any]
    
    # Report generation metadata
    report_metadata: Dict[str, Any]
    
    # Synthesis phase status
    synthesis_status: Dict[str, InvestigationStatus]
    
    # Synthesis phase metadata
    synthesis_metadata: Dict[str, Any]
    
    # === GLOBAL METADATA ===
    # Current phase of investigation
    current_phase: InvestigationPhase
    
    # Overall investigation status
    overall_status: InvestigationStatus
    
    # Progress percentage (0-100)
    progress_percentage: float
    
    # Estimated completion time
    estimated_completion: Optional[datetime]
    
    # Actual completion time
    completed_at: Optional[datetime]
    
    # Total execution time in seconds
    total_execution_time: float
    
    # List of errors encountered
    errors: List[Dict[str, Any]]
    
    # List of warnings encountered
    warnings: List[Dict[str, Any]]
    
    # Sources used during investigation
    sources_used: List[str]
    
    # Tools and agents utilized
    tools_utilized: List[str]
    
    # Agents that participated
    agents_participated: List[str]
    
    # Overall confidence level
    confidence_level: float
    
    # Cost tracking
    resource_costs: Dict[str, float]
    
    # Additional metadata
    metadata: Dict[str, Any]


def create_initial_state(
    user_request: str,
    investigation_id: Optional[str] = None,
    initiator: str = "user",
    priority: str = "medium"
) -> InvestigationState:
    """
    Create initial investigation state.
    
    Args:
        user_request: The user's investigation request
        investigation_id: Unique ID for the investigation (generated if not provided)
        initiator: Who initiated the investigation
        priority: Priority level
    
    Returns:
        Initial InvestigationState
    """
    import uuid
    
    if investigation_id is None:
        investigation_id = str(uuid.uuid4())
    
    current_time = datetime.utcnow()
    
    state_dict = {
        "user_request": user_request,
        "investigation_id": investigation_id,
        "initiated_at": current_time,
        "initiator": initiator,
        "priority": priority,
        "objectives": {},
        "strategy": {},
        "planning_status": InvestigationStatus.PENDING,
        "planning_metadata": {},
        "search_coordination_results": {},
        "search_results": {},
        "raw_data": {},
        "collection_status": {},
        "collection_metadata": {},
        "data_quality_metrics": {},
        "fused_data": {},
        "patterns": [],
        "context_analysis": {},
        "analysis_status": {},
        "analysis_metadata": {},
        "analysis_confidence": {},
        "intelligence": {},
        "quality_assessment": {},
        "final_report": {},
        "alternative_formats": {},
        "report_metadata": {},
        "synthesis_status": {},
        "synthesis_metadata": {},
        "current_phase": InvestigationPhase.PLANNING,
        "overall_status": InvestigationStatus.PENDING,
        "progress_percentage": 0.0,
        "estimated_completion": None,
        "completed_at": None,
        "total_execution_time": 0.0,
        "errors": [],
        "warnings": [],
        "sources_used": [],
        "tools_utilized": [],
        "agents_participated": [],
        "confidence_level": 0.0,
        "resource_costs": {},
        "metadata": {
            "version": "1.0",
            "workflow_type": "osint_investigation",
            "created_at": current_time.isoformat()
        }
    }
    
    return state_dict


def update_phase_status(
    state: InvestigationState,
    phase: InvestigationPhase,
    status: InvestigationStatus,
    metadata: Optional[Dict[str, Any]] = None
) -> InvestigationState:
    """
    Update the status of a specific investigation phase.
    
    Args:
        state: Current investigation state
        phase: Phase to update
        status: New status for the phase
        metadata: Additional metadata for the update
    
    Returns:
        Updated investigation state
    """
    state["current_phase"] = phase
    
    if phase == InvestigationPhase.PLANNING:
        state["planning_status"] = status
        if metadata:
            state["planning_metadata"].update(metadata)
    elif phase == InvestigationPhase.COLLECTION:
        if metadata:
            state["collection_metadata"].update(metadata)
    elif phase == InvestigationPhase.ANALYSIS:
        if metadata:
            state["analysis_metadata"].update(metadata)
    elif phase == InvestigationPhase.SYNTHESIS:
        if metadata:
            state["synthesis_metadata"].update(metadata)
    
    # Update overall status based on phase
    if status == InvestigationStatus.FAILED:
        state["overall_status"] = InvestigationStatus.FAILED
    elif phase == InvestigationPhase.COMPLETED:
        state["overall_status"] = InvestigationStatus.COMPLETED
        state["completed_at"] = datetime.utcnow()
    
    return state


def calculate_progress(state: InvestigationState) -> float:
    """
    Calculate overall investigation progress based on completed phases.
    
    Args:
        state: Current investigation state
    
    Returns:
        Progress percentage (0-100)
    """
    phase_weights = {
        InvestigationPhase.PLANNING: 0.15,
        InvestigationPhase.COLLECTION: 0.35,
        InvestigationPhase.ANALYSIS: 0.35,
        InvestigationPhase.SYNTHESIS: 0.15
    }
    
    progress = 0.0
    
    # Check planning phase
    if state["planning_status"] == InvestigationStatus.COMPLETED:
        progress += phase_weights[InvestigationPhase.PLANNING] * 100
    elif state["planning_status"] == InvestigationStatus.IN_PROGRESS:
        progress += phase_weights[InvestigationPhase.PLANNING] * 50
    
    # Check collection phase
    collection_completed = sum(
        1 for status in state["collection_status"].values()
        if status == InvestigationStatus.COMPLETED
    )
    collection_total = len(state["collection_status"]) or 1
    
    if collection_total > 0:
        collection_progress = (collection_completed / collection_total) * 100
        progress += phase_weights[InvestigationPhase.COLLECTION] * collection_progress
    
    # Check analysis phase
    analysis_completed = sum(
        1 for status in state["analysis_status"].values()
        if status == InvestigationStatus.COMPLETED
    )
    analysis_total = len(state["analysis_status"]) or 1
    
    if analysis_total > 0:
        analysis_progress = (analysis_completed / analysis_total) * 100
        progress += phase_weights[InvestigationPhase.ANALYSIS] * analysis_progress
    
    # Check synthesis phase
    synthesis_completed = sum(
        1 for status in state["synthesis_status"].values()
        if status == InvestigationStatus.COMPLETED
    )
    synthesis_total = len(state["synthesis_status"]) or 1
    
    if synthesis_total > 0:
        synthesis_progress = (synthesis_completed / synthesis_total) * 100
        progress += phase_weights[InvestigationPhase.SYNTHESIS] * synthesis_progress
    
    return min(progress, 100.0)


def add_error(
    state: InvestigationState,
    error_message: str,
    phase: Optional[InvestigationPhase] = None,
    agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> InvestigationState:
    """
    Add an error to the investigation state.
    
    Args:
        state: Current investigation state
        error_message: Error description
        phase: Phase where error occurred
        agent: Agent that encountered the error
        details: Additional error details
    
    Returns:
        Updated investigation state
    """
    error = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": error_message,
        "phase": phase.value if phase else None,
        "agent": agent,
        "details": details or {}
    }
    
    state["errors"].append(error)
    return state


def add_warning(
    state: InvestigationState,
    warning_message: str,
    phase: Optional[InvestigationPhase] = None,
    agent: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> InvestigationState:
    """
    Add a warning to the investigation state.
    
    Args:
        state: Current investigation state
        warning_message: Warning description
        phase: Phase where warning occurred
        agent: Agent that issued the warning
        details: Additional warning details
    
    Returns:
        Updated investigation state
    """
    warning = {
        "timestamp": datetime.utcnow().isoformat(),
        "message": warning_message,
        "phase": phase.value if phase else None,
        "agent": agent,
        "details": details or {}
    }
    
    state["warnings"].append(warning)
    return state


def update_resource_costs(
    state: InvestigationState,
    cost_breakdown: Dict[str, float]
) -> InvestigationState:
    """
    Update resource costs for the investigation.
    
    Args:
        state: Current investigation state
        cost_breakdown: Dictionary of cost categories and amounts
    
    Returns:
        Updated investigation state
    """
    for category, cost in cost_breakdown.items():
        if category in state["resource_costs"]:
            state["resource_costs"][category] += cost
        else:
            state["resource_costs"][category] = cost
    
    return state