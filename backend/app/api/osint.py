from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import logging

# Import models with a simple approach
from app.models.osint import (
    Investigation,
    InvestigationCreate,
    InvestigationUpdate,
    InvestigationTarget,
    TargetCreate,
    CollectedEvidence,
    EvidenceCreate,
    ThreatAssessment,
    ThreatAssessmentCreate,
    InvestigationReport,
    ReportCreate,
    InvestigationPhase,
    InvestigationStatus,
    InvestigationClassification,
    InvestigationPriority,
    AgentAssignment,
    AgentType,
    AgentStatus,
)
from app.services.websocket import ConnectionManager
from app.services.enhanced_websocket import enhanced_manager as enhanced_connection_manager
from app.services.task_storage import task_storage

# Import premium search agent
from app.agents.specialized.collection.premium_search_agent import PremiumSearchAgent

# Initialize the router
router = APIRouter(prefix="", tags=["osint"])

# For now, we'll use in-memory storage - in production this would connect to a database
investigations_db: Dict[str, Investigation] = {}
targets_db: Dict[str, InvestigationTarget] = {}
evidence_db: Dict[str, CollectedEvidence] = {}
threats_db: Dict[str, ThreatAssessment] = {}
reports_db: Dict[str, InvestigationReport] = {}

# Initialize real data from database if available
def initialize_real_data():
    """Initialize real data from database if available."""
    try:
        # Try to load investigations from database or file storage
        from app.services.investigation_storage import load_investigations
        
        loaded_investigations = load_investigations()
        for inv in loaded_investigations:
            investigations_db[inv.id] = inv
            
        logger.info(f"Loaded {len(loaded_investigations)} investigations from storage")
    except ImportError:
        logger.warning("Investigation storage not available, starting with empty database")
    except Exception as e:
        logger.error(f"Failed to load investigations: {e}")

# Remove test initialization - start with empty database
# initialize_test_data()

logger = logging.getLogger(__name__)

initialize_real_data()

@router.get("/investigations", response_model=List[Investigation])
async def list_investigations(
    classification: Optional[InvestigationClassification] = None,
    status: Optional[InvestigationStatus] = None,
    priority: Optional[InvestigationPriority] = None
) -> List[Investigation]:
    """List all investigations with optional filtering."""
    investigations = list(investigations_db.values())
    
    if classification:
        investigations = [inv for inv in investigations if inv.classification == classification]
    if status:
        investigations = [inv for inv in investigations if inv.status == status]
    if priority:
        investigations = [inv for inv in investigations if inv.priority == priority]
        
    return investigations


@router.post("/investigations", response_model=Investigation)
async def create_investigation(investigation_create: InvestigationCreate) -> Investigation:
    """Create a new investigation."""
    investigation_id = f"inv-{str(uuid.uuid4())[:8]}"
    
    investigation = Investigation(
        id=investigation_id,
        title=investigation_create.title,
        description=investigation_create.description,
        classification=investigation_create.classification,
        priority=investigation_create.priority,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    investigations_db[investigation_id] = investigation
    
    # Send WebSocket notification using enhanced manager
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "investigation:created",
            "investigation": investigation.dict()
        }
    )
    
    return investigation


@router.get("/investigations/{investigation_id}", response_model=Investigation)
async def get_investigation(investigation_id: str) -> Investigation:
    """Get a specific investigation by ID."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return investigations_db[investigation_id]


@router.put("/investigations/{investigation_id}", response_model=Investigation)
async def update_investigation(
    investigation_id: str,
    investigation_update: InvestigationUpdate
) -> Investigation:
    """Update a specific investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    
    # Update fields if provided
    if investigation_update.title is not None:
        investigation.title = investigation_update.title
    if investigation_update.description is not None:
        investigation.description = investigation_update.description
    if investigation_update.classification is not None:
        investigation.classification = investigation_update.classification
    if investigation_update.priority is not None:
        investigation.priority = investigation_update.priority
    if investigation_update.status is not None:
        investigation.status = investigation_update.status
    if investigation_update.current_phase is not None:
        old_phase = investigation.current_phase
        investigation.current_phase = investigation_update.current_phase
        # Add phase transition
        investigation.add_phase_transition(investigation_update.current_phase)
        
        # Send WebSocket notification for phase change
        await enhanced_connection_manager.broadcast(
            f"investigation_{investigation_id}",
            {
                "type": "investigation:phase_changed",
                "investigation_id": investigation_id,
                "old_phase": old_phase.value,
                "new_phase": investigation_update.current_phase.value
            }
        )
    
    investigation.updated_at = datetime.utcnow()
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "investigation:updated",
            "investigation_id": investigation_id,
            "updates": investigation_update.dict(exclude_unset=True)
        }
    )
    
    return investigation


@router.delete("/investigations/{investigation_id}")
async def delete_investigation(investigation_id: str) -> Dict[str, str]:
    """Delete a specific investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    del investigations_db[investigation_id]
    
    # Remove related data
    # In a real implementation, you'd want cascading deletes
    # Filter targets that belong to this investigation
    targets_to_remove = [target_id for target_id, target in targets_db.items() 
                         if getattr(target, 'investigation_id', '').startswith('inv-') and 
                         getattr(target, 'investigation_id', '') == investigation_id]
    for target_id in targets_to_remove:
        del targets_db[target_id]
    
    return {"message": f"Investigation {investigation_id} deleted successfully"}


@router.post("/investigations/{investigation_id}/targets", response_model=InvestigationTarget)
async def create_target(
    investigation_id: str,
    target_create: TargetCreate
) -> InvestigationTarget:
    """Create a new target for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    target_id = f"tgt-{str(uuid.uuid4())[:8]}"
    
    target = InvestigationTarget(
        id=target_id,
        type=target_create.type,
        identifier=target_create.identifier,
        aliases=target_create.aliases,
        priority=target_create.priority,
        collection_requirements=target_create.collection_requirements,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    targets_db[target_id] = target
    
    # Add target to investigation
    investigation = investigations_db[investigation_id]
    investigation.add_target(target)
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "target:created",
            "target": target.dict(),
            "investigation_id": investigation_id
        }
    )
    
    return target


@router.get("/investigations/{investigation_id}/targets", response_model=List[InvestigationTarget])
async def list_targets(investigation_id: str) -> List[InvestigationTarget]:
    """List all targets for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    return investigation.targets


@router.get("/investigations/{investigation_id}/evidence", response_model=List[CollectedEvidence])
async def list_evidence(investigation_id: str) -> List[CollectedEvidence]:
    """List all evidence for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    return investigation.collected_evidence


@router.post("/investigations/{investigation_id}/evidence", response_model=CollectedEvidence)
async def create_evidence(
    investigation_id: str,
    evidence_create: EvidenceCreate
) -> CollectedEvidence:
    """Create a new piece of evidence for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    evidence_id = f"ev-{str(uuid.uuid4())[:8]}"
    
    evidence = CollectedEvidence(
        id=evidence_id,
        investigation_id=investigation_id,
        source=evidence_create.source,
        source_type=evidence_create.source_type,
        content=evidence_create.content,
        metadata=evidence_create.metadata,
        reliability_score=evidence_create.reliability_score,
        relevance_score=evidence_create.relevance_score
    )
    
    evidence_db[evidence_id] = evidence
    
    # Add evidence to investigation
    investigation = investigations_db[investigation_id]
    investigation.add_evidence(evidence)
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "evidence:collected",
            "evidence": evidence.dict()
        }
    )
    
    return evidence


@router.get("/investigations/{investigation_id}/threats", response_model=List[ThreatAssessment])
async def list_threats(investigation_id: str) -> List[ThreatAssessment]:
    """List all threats for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    return investigation.threat_assessments


@router.post("/investigations/{investigation_id}/threats", response_model=ThreatAssessment)
async def create_threat(
    investigation_id: str,
    threat_create: ThreatAssessmentCreate
) -> ThreatAssessment:
    """Create a new threat assessment for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    threat_id = f"thr-{str(uuid.uuid4())[:8]}"
    
    threat = ThreatAssessment(
        id=threat_id,
        investigation_id=investigation_id,
        title=threat_create.title,
        description=threat_create.description,
        threat_level=threat_create.threat_level,
        threat_type=threat_create.threat_type,
        targets=threat_create.targets,
        likelihood=threat_create.likelihood,
        impact=threat_create.impact,
        risk_score=threat_create.likelihood * threat_create.impact  # Simple calculation
    )
    
    threats_db[threat_id] = threat
    
    # Add threat to investigation
    investigation = investigations_db[investigation_id]
    investigation.add_threat_assessment(threat)
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "threat:identified",
            "threat": threat.dict()
        }
    )
    
    return threat


@router.get("/investigations/{investigation_id}/reports", response_model=List[InvestigationReport])
async def list_reports(investigation_id: str) -> List[InvestigationReport]:
    """List all reports for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    return investigation.generated_reports


@router.post("/investigations/{investigation_id}/reports", response_model=InvestigationReport)
async def create_report(
    investigation_id: str,
    report_create: ReportCreate
) -> InvestigationReport:
    """Create a new report for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    report_id = f"rep-{str(uuid.uuid4())[:8]}"
    
    report = InvestigationReport(
        id=report_id,
        investigation_id=investigation_id,
        title=report_create.title,
        content=report_create.content,
        format=report_create.format,
        classification=report_create.classification,
        recipients=report_create.recipients
    )
    
    reports_db[report_id] = report
    
    # Add report to investigation
    investigation = investigations_db[investigation_id]
    investigation.generated_reports.append(report)
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "report:generated",
            "report": report.dict()
        }
    )
    
    return report


@router.get("/investigations/{investigation_id}/timeline")
async def get_investigation_timeline(investigation_id: str) -> Dict[str, Any]:
    """Get the full timeline of events for an investigation."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    
    # Combine all events in chronological order
    timeline_events = []
    
    # Add phase transitions
    for transition in investigation.phase_history:
        timeline_events.append({
            "type": "phase_change",
            "timestamp": transition.timestamp,
            "from_phase": transition.from_phase.value,
            "to_phase": transition.to_phase.value,
            "reason": transition.reason,
            "triggered_by": transition.triggered_by
        })
    
    # Add targets
    for target in investigation.targets:
        timeline_events.append({
            "type": "target_added",
            "timestamp": target.created_at,
            "target_id": target.id,
            "identifier": target.identifier
        })
    
    # Add evidence
    for evidence in investigation.collected_evidence:
        timeline_events.append({
            "type": "evidence_collected",
            "timestamp": evidence.collected_at,
            "evidence_id": evidence.id,
            "source": evidence.source
        })
    
    # Add threats
    for threat in investigation.threat_assessments:
        timeline_events.append({
            "type": "threat_identified",
            "timestamp": threat.created_at,
            "threat_id": threat.id,
            "title": threat.title
        })
    
    # Sort by timestamp
    timeline_events.sort(key=lambda x: x["timestamp"])
    
    return {
        "investigation_id": investigation_id,
        "timeline": timeline_events
    }


@router.post("/investigations/{investigation_id}/advance-phase")
async def advance_investigation_phase(
    investigation_id: str,
    next_phase: InvestigationPhase
) -> Investigation:
    """Advance an investigation to the next phase."""
    if investigation_id not in investigations_db:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    investigation = investigations_db[investigation_id]
    
    # Check if transition is allowed
    allowed_transitions = {
        InvestigationPhase.PLANNING: [InvestigationPhase.RECONNAISSANCE],
        InvestigationPhase.RECONNAISSANCE: [InvestigationPhase.COLLECTION],
        InvestigationPhase.COLLECTION: [InvestigationPhase.ANALYSIS],
        InvestigationPhase.ANALYSIS: [InvestigationPhase.SYNTHESIS],
        InvestigationPhase.SYNTHESIS: [InvestigationPhase.REPORTING],
        InvestigationPhase.REPORTING: [],
    }
    
    if next_phase not in allowed_transitions.get(investigation.current_phase, []):
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot transition from {investigation.current_phase.value} to {next_phase.value}"
        )
    
    old_phase = investigation.current_phase
    investigation.add_phase_transition(next_phase, reason="Manual phase advancement")
    investigations_db[investigation_id] = investigation
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "investigation:phase_changed",
            "investigation_id": investigation_id,
            "old_phase": old_phase.value,
            "new_phase": next_phase.value
        }
    )
    
    return investigation


# Agent Coordination Endpoints

@router.get("/investigations/{investigation_id}/agents")
async def get_investigation_agents(investigation_id: str):
    """Get all agents assigned to an investigation."""
    investigation = investigations_db.get(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return {
        "investigation_id": investigation_id,
        "agents": investigation.assigned_agents,
        "total_count": len(investigation.assigned_agents)
    }

@router.post("/investigations/{investigation_id}/agents/assign")
async def assign_agent_to_investigation(investigation_id: str, agent_assignment: dict):
    """Assign an agent to an investigation with specific tasks."""
    investigation = investigations_db.get(investigation_id)
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    # Create new agent assignment
    agent_id = agent_assignment.get("agent_id")
    if not agent_id:
        raise HTTPException(status_code=400, detail="agent_id is required")
    
    new_assignment = AgentAssignment(
        agent_id=agent_id,
        agent_type=AgentType(agent_assignment.get("agent_type", "COLLECTION")),
        assigned_targets=agent_assignment.get("assigned_targets", []),
        current_task=agent_assignment.get("current_task"),
        status=AgentStatus(agent_assignment.get("status", "IDLE")),
        performance_metrics=agent_assignment.get("performance_metrics", {})
    )
    
    # Add to investigation
    investigation.assigned_agents.append(new_assignment)
    investigation.updated_at = datetime.utcnow()
    
    # Send WebSocket notification
    await enhanced_connection_manager.broadcast(
        f"investigation_{investigation_id}",
        {
            "type": "agent:assigned",
            "investigation_id": investigation_id,
            "agent_id": new_assignment.agent_id,
            "agent_type": new_assignment.agent_type.value,
            "status": new_assignment.status.value
        }
    )
    
    return new_assignment

@router.put("/agents/{agent_id}/status")
async def update_agent_status(agent_id: str, status_update: dict):
    """Update the status of a specific agent."""
    new_status = AgentStatus(status_update.get("status"))
    task_details = status_update.get("task_details", {})
    
    # Find and update the agent across all investigations
    updated_agent = None
    for investigation in investigations_db.values():
        for agent in investigation.assigned_agents:
            if agent.agent_id == agent_id:
                agent.status = new_status
                agent.updated_at = datetime.utcnow()
                if task_details:
                    agent.current_task = task_details
                updated_agent = agent
                
                # Send WebSocket notification
                await enhanced_connection_manager.broadcast(
                    f"investigation_{investigation.id}",
                    {
                        "type": "agent:status_changed",
                        "agent_id": agent_id,
                        "status": new_status.value,
                        "investigation_id": investigation.id,
                        "task_details": task_details
                    }
                )
                break
    
    if not updated_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return updated_agent

@router.post("/agents/{agent_id}/tasks")
async def assign_task_to_agent(agent_id: str, task_assignment: dict):
    """Assign a new task to an agent."""
    task = {
        "id": str(uuid.uuid4()),
        "type": task_assignment.get("type"),
        "description": task_assignment.get("description"),
        "priority": task_assignment.get("priority", "MEDIUM"),
        "assigned_at": datetime.utcnow().isoformat(),
        "status": "PENDING",
        "details": task_assignment.get("details", {})
    }
    
    # Find and update the agent
    updated_agent = None
    investigation_id = None
    
    for investigation in investigations_db.values():
        for agent in investigation.assigned_agents:
            if agent.agent_id == agent_id:
                agent.current_task = task
                agent.status = AgentStatus.ACTIVE
                agent.updated_at = datetime.utcnow()
                updated_agent = agent
                investigation_id = investigation.id
                
                # Send WebSocket notification
                await enhanced_connection_manager.broadcast(
                    f"investigation_{investigation.id}",
                    {
                        "type": "agent:task_assigned",
                        "agent_id": agent_id,
                        "task": task,
                        "investigation_id": investigation.id
                    }
                )
                break
    
    if not updated_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return updated_agent

@router.get("/agents/{agent_id}/performance")
async def get_agent_performance(agent_id: str):
    """Get performance metrics for a specific agent."""
    agent_info = None
    investigation_id = None
    
    for investigation in investigations_db.values():
        for agent in investigation.assigned_agents:
            if agent.agent_id == agent_id:
                agent_info = agent
                investigation_id = investigation.id
                break
    
    if not agent_info:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Calculate performance metrics
    performance = {
        "agent_id": agent_id,
        "investigation_id": investigation_id,
        "agent_type": agent_info.agent_type.value,
        "current_status": agent_info.status.value,
        "assigned_at": agent_info.assigned_at.isoformat(),
        "last_updated": agent_info.updated_at.isoformat(),
        "current_task": agent_info.current_task,
        "performance_metrics": agent_info.performance_metrics or {
            "tasks_completed": 0,
            "success_rate": 0.0,
            "average_task_time": 0.0,
            "error_count": 0
        }
    }
    
    return performance


@router.websocket("/ws/{investigation_id}")
async def investigation_websocket(websocket: WebSocket, investigation_id: str):
    """WebSocket endpoint for real-time investigation updates."""
    user_id = f"ws-{str(uuid.uuid4())[:8]}"  # Generate a temporary user ID for WebSocket
    await enhanced_connection_manager.connect(websocket, f"investigation_{investigation_id}", user_id)
    
    try:
        while True:
            # Listen for messages (though for OSINT, most updates will be server-initiated)
            data = await websocket.receive_json()
            # Process any client commands if needed
            response = {"type": "ack", "message": "Command received"}
            await enhanced_connection_manager._send_safe(websocket, response)
    except WebSocketDisconnect:
        enhanced_connection_manager.disconnect(websocket, f"investigation_{investigation_id}", user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        enhanced_connection_manager.disconnect(websocket, f"investigation_{investigation_id}", user_id)


# Search endpoints
@router.post("/search", response_model=Dict[str, Any])
async def search_web(query: str, max_results: Optional[int] = 10, engines: Optional[List[str]] = None):
    """
    Perform a web search using available search engines.
    """
    try:
        # Import the search agent
        from app.agents.specialized.collection.simple_search_agent import SimpleSearchAgent
        from app.agents.base.osint_agent import AgentConfig
        
        # Initialize search agent
        config = AgentConfig(
            role="Search Specialist",
            description="Performs web searches",
            timeout=30,
            max_retries=2
        )
        search_agent = SimpleSearchAgent(config)
        
        # Set max results if provided
        if max_results:
            search_agent.max_results = max_results
        
        # Perform search
        input_data = {"query": query}
        result = await search_agent.execute(input_data)
        
        if result.success:
            return {
                "success": True,
                "query": query,
                "results": result.data.get("results", []),
                "total_results": result.data.get("total_results", 0),
                "engines_used": result.data.get("engines_used", []),
                "search_time": result.data.get("search_time", 0.0),
                "timestamp": result.data.get("timestamp", datetime.utcnow().isoformat())
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Search failed: {result.error_message}"
            )
            
    except Exception as e:
        logger.error(f"Search API error: {e}")
        raise HTTPException(status_code=500, detail=f"Search operation failed: {str(e)}")


@router.post("/investigations/{investigation_id}/search")
async def search_in_investigation(investigation_id: str, query: str, max_results: Optional[int] = 10):
    """
    Perform a search within the context of an investigation and store results as evidence.
    """
    try:
        # First verify investigation exists
        if investigation_id not in investigations_db:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Perform search
        search_result = await search_web(query, max_results)
        
        if search_result["success"]:
            # Store search results as evidence
            evidence_items = []
            for idx, result in enumerate(search_result["results"]):
                evidence_id = f"evidence-{str(uuid.uuid4())[:8]}"
                
                evidence = CollectedEvidence(
                    id=evidence_id,
                    investigation_id=investigation_id,
                    source_type="web_search",
                    source_name=result.get("source", "unknown"),
                    collection_method="automated_search",
                    title=result.get("title", ""),
                    content=result.get("description", ""),
                    url=result.get("url", ""),
                    relevance_score=result.get("relevance_score", 0.5),
                    collection_timestamp=datetime.utcnow(),
                    tags=["search", "web", result.get("source", "unknown")],
                    metadata={
                        "search_query": query,
                        "search_engine": result.get("source"),
                        "result_index": idx,
                        "total_results": search_result["total_results"]
                    }
                )
                
                evidence_db[evidence_id] = evidence
                evidence_items.append({
                    "id": evidence_id,
                    "title": evidence.title,
                    "url": evidence.url,
                    "source": evidence.source_name,
                    "relevance_score": evidence.relevance_score
                })
            
            # Update investigation with new evidence count
            investigation = investigations_db[investigation_id]
            investigation.collected_evidence.extend(evidence_items)
            
            # Send WebSocket update
            await enhanced_connection_manager.broadcast_to_group(
                f"investigation_{investigation_id}",
                {
                    "type": "search_completed",
                    "investigation_id": investigation_id,
                    "query": query,
                    "results_count": len(evidence_items),
                    "evidence_items": evidence_items,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "query": query,
                "investigation_id": investigation_id,
                "evidence_added": len(evidence_items),
                "evidence_items": evidence_items,
                "total_results": search_result["total_results"],
                "engines_used": search_result["engines_used"]
            }
        else:
            raise HTTPException(status_code=500, detail="Search operation failed")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Investigation search error: {e}")
        raise HTTPException(status_code=500, detail=f"Investigation search failed: {str(e)}")


# Premium Search endpoints - Advanced scraping without APIs

@router.post("/premium-search", response_model=Dict[str, Any])
async def premium_search_web(
    query: str,
    engines: Optional[List[str]] = None,
    max_pages: Optional[int] = 1,
    use_browser: Optional[bool] = False
):
    """
    Perform advanced web search using premium scraping techniques without APIs.
    
    Args:
        query: Search query string
        engines: List of engines (duckduckgo, brave, google, bing, yahoo, yandex, baidu)
        max_pages: Number of pages to scrape per engine
        use_browser: Use browser automation (slower but more effective)
    """
    try:
        # Initialize premium search agent
        premium_agent = PremiumSearchAgent()
        
        # Prepare input data
        input_data = {
            "query": query,
            "engines": engines or ["duckduckgo", "brave"],
            "max_pages": max_pages,
            "use_browser": use_browser
        }
        
        # Execute premium search
        result = await premium_agent.execute(input_data)
        
        if result.success:
            data = result.data
            return {
                "success": True,
                "query": query,
                "results": data.get("results", []),
                "summary": data.get("summary", {}),
                "metadata": data.get("metadata", {}),
                "total_results": len(data.get("results", [])),
                "execution_time": result.execution_time,
                "confidence": result.confidence,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Premium search failed: {result.error_message}"
            )
            
    except Exception as e:
        logger.error(f"Premium search API error: {e}")
        raise HTTPException(status_code=500, detail=f"Premium search failed: {str(e)}")


@router.post("/investigations/{investigation_id}/premium-search")
async def premium_search_investigation(
    investigation_id: str,
    query: str,
    engines: Optional[List[str]] = None,
    max_pages: Optional[int] = 1,
    use_browser: Optional[bool] = False,
    store_as_evidence: Optional[bool] = True
):
    """
    Perform premium search within investigation context with evidence collection.
    """
    try:
        # Verify investigation exists
        if investigation_id not in investigations_db:
            raise HTTPException(status_code=404, detail="Investigation not found")
        
        # Initialize premium search agent
        premium_agent = PremiumSearchAgent()
        
        # Prepare input data with investigation context
        input_data = {
            "query": query,
            "engines": engines or ["duckduckgo", "brave"],
            "max_pages": max_pages,
            "use_browser": use_browser,
            "investigation_id": investigation_id
        }
        
        # Execute premium search
        result = await premium_agent.execute(input_data)
        
        if result.success:
            data = result.data
            results = data.get("results", [])
            evidence_items = []
            
            # Store results as evidence if requested
            if store_as_evidence and results:
                for search_result in results:
                    evidence_id = f"ev-{str(uuid.uuid4())[:8]}"
                    
                    evidence = CollectedEvidence(
                        id=evidence_id,
                        investigation_id=investigation_id,
                        title=search_result.get("title", "Search Result"),
                        content=search_result.get("snippet", ""),
                        url=search_result.get("url", ""),
                        source_name=f"Premium Search - {search_result.get('engine', 'unknown')}",
                        source_type="web_search",
                        relevance_score=search_result.get("relevance_score", 0.5),
                        collection_method="premium_scraping",
                        metadata={
                            "engine": search_result.get("engine"),
                            "rank": search_result.get("rank"),
                            "quality_score": search_result.get("quality_score"),
                            "content_type": search_result.get("content_type"),
                            "extracted_entities": search_result.get("extracted_entities", []),
                            "query_hash": search_result.get("query_hash"),
                            "collection_method": search_result.get("collection_method")
                        },
                        tags=["premium_search", search_result.get("engine", "unknown")]
                    )
                    
                    evidence_db[evidence_id] = evidence
                    evidence_items.append({
                        "id": evidence_id,
                        "title": evidence.title,
                        "url": evidence.url,
                        "source": evidence.source_name,
                        "relevance_score": evidence.relevance_score,
                        "quality_score": search_result.get("quality_score"),
                        "engine": search_result.get("engine"),
                        "content_type": search_result.get("content_type")
                    })
            
            # Update investigation
            investigation = investigations_db[investigation_id]
            investigation.collected_evidence.extend(evidence_items)
            investigation.updated_at = datetime.utcnow()
            
            # Send WebSocket notification
            await enhanced_connection_manager.broadcast_to_group(
                f"investigation_{investigation_id}",
                {
                    "type": "premium_search_completed",
                    "investigation_id": investigation_id,
                    "query": query,
                    "results_count": len(results),
                    "evidence_added": len(evidence_items),
                    "engines_used": data.get("summary", {}).get("engines_used", []),
                    "average_relevance": data.get("summary", {}).get("average_relevance", 0),
                    "quality_distribution": data.get("summary", {}).get("quality_distribution", {}),
                    "search_method": data.get("summary", {}).get("search_method", "http_requests"),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "query": query,
                "investigation_id": investigation_id,
                "results": results,
                "summary": data.get("summary", {}),
                "evidence_added": len(evidence_items),
                "evidence_items": evidence_items,
                "total_results": len(results),
                "execution_time": result.execution_time,
                "confidence": result.confidence
            }
        else:
            raise HTTPException(status_code=500, detail=f"Premium search failed: {result.error_message}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Investigation premium search error: {e}")
        raise HTTPException(status_code=500, detail=f"Investigation premium search failed: {str(e)}")


@router.get("/premium-search/engines")
async def get_premium_search_engines():
    """Get list of supported premium search engines."""
    try:
        premium_agent = PremiumSearchAgent()
        engines = await premium_agent.get_supported_engines()
        
        return {
            "success": True,
            "engines": engines,
            "total_engines": len(engines),
            "features": [
                "No API keys required",
                "Advanced anti-detection",
                "Proxy rotation support",
                "Browser automation",
                "Rate limiting",
                "Result quality assessment",
                "Entity extraction",
                "Content classification"
            ]
        }
        
    except Exception as e:
        logger.error(f"Get engines error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get supported engines: {str(e)}")


@router.post("/premium-search/test-connectivity")
async def test_premium_connectivity():
    """Test connectivity to premium search engines."""
    try:
        premium_agent = PremiumSearchAgent()
        connectivity_results = await premium_agent.test_connectivity()
        
        return {
            "success": True,
            "connectivity": connectivity_results,
            "working_engines": [engine for engine, status in connectivity_results.items() if status],
            "failed_engines": [engine for engine, status in connectivity_results.items() if not status],
            "total_engines": len(connectivity_results),
            "success_rate": sum(connectivity_results.values()) / len(connectivity_results) if connectivity_results else 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Test connectivity error: {e}")
        raise HTTPException(status_code=500, detail=f"Connectivity test failed: {str(e)}")