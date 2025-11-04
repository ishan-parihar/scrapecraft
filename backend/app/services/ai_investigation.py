"""
AI Investigation Service

Service for managing AI-powered OSINT investigations.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import uuid
import logging

logger = logging.getLogger(__name__)

class InvestigationRequest:
    """Request model for starting investigations"""
    
    def __init__(self, target: str, objective: str, scope: List[str] = None, 
                 priority: str = "medium", requirements: Dict[str, Any] = None):
        self.target = target
        self.objective = objective
        self.scope = scope or []
        self.priority = priority
        self.requirements = requirements or {}

class InvestigationResponse:
    """Response model for investigations"""
    
    def __init__(self, investigation_id: str, status: str, current_phase: str,
                 progress_percentage: float, estimated_completion: Optional[datetime] = None,
                 message: str = ""):
        self.investigation_id = investigation_id
        self.status = status
        self.current_phase = current_phase
        self.progress_percentage = progress_percentage
        self.estimated_completion = estimated_completion
        self.message = message

class AIInvestigationService:
    """Service for managing AI-powered OSINT investigations"""
    
    def __init__(self):
        self.active_investigations: Dict[str, Dict[str, Any]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Import workflow components dynamically to avoid circular imports
        try:
            import importlib.util
            import os
            
            # Import OSINTWorkflow
            workflow_path = os.path.join(os.path.dirname(__file__), 'graph.py')
            spec = importlib.util.spec_from_file_location("osint_workflow", workflow_path)
            if spec is not None and spec.loader is not None:
                workflow_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(workflow_module)
                self.workflow_class = getattr(workflow_module, 'OSINTWorkflow', None)
            else:
                self.logger.warning("Could not load OSINTWorkflow, using placeholder")
                self.workflow_class = None
                
        except Exception as e:
            self.logger.error(f"Failed to import workflow components: {e}")
            self.workflow_class = None
    
    async def start_investigation(self, request: InvestigationRequest) -> Dict[str, Any]:
        """Start a new OSINT investigation"""
        try:
            # Generate unique investigation ID
            investigation_id = str(uuid.uuid4())
            
            # Initialize investigation state
            investigation_state = {
                "investigation_id": investigation_id,
                "target": request.target,
                "objective": request.objective,
                "scope": request.scope,
                "priority": request.priority,
                "requirements": request.requirements,
                "status": "initializing",
                "current_phase": "planning",
                "progress_percentage": 0.0,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "phases_completed": [],
                "results": {},
                "errors": []
            }
            
            # Store investigation
            self.active_investigations[investigation_id] = investigation_state
            
            # Initialize workflow if available
            if self.workflow_class:
                try:
                    workflow = self.workflow_class()
                    # Start workflow in background
                    asyncio.create_task(self._run_workflow(investigation_id, workflow, request))
                    investigation_state["status"] = "running"
                    self.logger.info(f"Started investigation {investigation_id} for target: {request.target}")
                except Exception as e:
                    self.logger.error(f"Failed to start workflow for investigation {investigation_id}: {e}")
                    investigation_state["status"] = "failed"
                    investigation_state["errors"].append(str(e))
            else:
                # Placeholder workflow
                investigation_state["status"] = "running"
                asyncio.create_task(self._placeholder_workflow(investigation_id))
            
            return {
                "investigation_id": investigation_id,
                "status": investigation_state["status"],
                "current_phase": investigation_state["current_phase"],
                "progress_percentage": investigation_state["progress_percentage"],
                "message": f"Investigation started for target: {request.target}"
            }
            
        except Exception as e:
            self.logger.error(f"Failed to start investigation: {e}")
            return {
                "error": str(e),
                "status": "failed"
            }
    
    async def get_investigation_status(self, investigation_id: str) -> Dict[str, Any]:
        """Get investigation status"""
        if investigation_id not in self.active_investigations:
            return {
                "error": "Investigation not found",
                "status": "not_found"
            }
        
        investigation = self.active_investigations[investigation_id]
        
        return {
            "investigation_id": investigation_id,
            "status": investigation["status"],
            "current_phase": investigation["current_phase"],
            "progress_percentage": investigation["progress_percentage"],
            "created_at": investigation["created_at"],
            "updated_at": investigation["updated_at"],
            "phases_completed": investigation["phases_completed"],
            "errors": investigation["errors"],
            "results": investigation.get("results", {})
        }
    
    async def approve_phase(self, investigation_id: str, phase: str) -> Dict[str, Any]:
        """Approve investigation phase"""
        if investigation_id not in self.active_investigations:
            return {
                "error": "Investigation not found",
                "status": "not_found"
            }
        
        investigation = self.active_investigations[investigation_id]
        
        # Add phase approval logic here
        investigation["phases_completed"].append(phase)
        investigation["updated_at"] = datetime.utcnow()
        
        return {
            "investigation_id": investigation_id,
            "status": "approved",
            "phase": phase,
            "message": f"Phase {phase} approved"
        }
    
    async def _run_workflow(self, investigation_id: str, workflow, request: InvestigationRequest):
        """Run the OSINT workflow for an investigation"""
        try:
            # This would integrate with the actual OSINT workflow
            # For now, simulate workflow execution
            investigation = self.active_investigations[investigation_id]
            
            phases = ["planning", "collection", "analysis", "synthesis"]
            
            for i, phase in enumerate(phases):
                # Update phase
                investigation["current_phase"] = phase
                investigation["progress_percentage"] = (i + 1) / len(phases) * 100
                investigation["updated_at"] = datetime.utcnow()
                
                # Simulate phase execution
                await asyncio.sleep(2)  # Simulate work
                
                # Mark phase as completed
                investigation["phases_completed"].append(phase)
            
            # Mark as completed
            investigation["status"] = "completed"
            investigation["progress_percentage"] = 100.0
            investigation["updated_at"] = datetime.utcnow()
            investigation["results"] = {
                "summary": f"Completed investigation for {request.target}",
                "findings": ["Sample finding 1", "Sample finding 2"],
                "confidence": 0.85
            }
            
            self.logger.info(f"Completed investigation {investigation_id}")
            
        except Exception as e:
            self.logger.error(f"Workflow failed for investigation {investigation_id}: {e}")
            if investigation_id in self.active_investigations:
                self.active_investigations[investigation_id]["status"] = "failed"
                self.active_investigations[investigation_id]["errors"].append(str(e))
    
    async def _placeholder_workflow(self, investigation_id: str):
        """Placeholder workflow when OSINTWorkflow is not available"""
        try:
            investigation = self.active_investigations[investigation_id]
            
            # Simulate investigation progress
            for i in range(1, 101):
                if investigation_id not in self.active_investigations:
                    break
                    
                investigation["progress_percentage"] = i
                investigation["updated_at"] = datetime.utcnow()
                
                if i % 25 == 0:  # Update phase every 25%
                    phases = ["planning", "collection", "analysis", "synthesis"]
                    phase_index = min(i // 25, len(phases) - 1)
                    investigation["current_phase"] = phases[phase_index]
                
                await asyncio.sleep(0.1)  # Small delay to simulate progress
            
            # Mark as completed
            investigation["status"] = "completed"
            investigation["results"] = {
                "summary": "Placeholder investigation completed",
                "findings": ["Placeholder finding"],
                "confidence": 0.5
            }
            
        except Exception as e:
            self.logger.error(f"Placeholder workflow failed: {e}")
            if investigation_id in self.active_investigations:
                self.active_investigations[investigation_id]["status"] = "failed"
                self.active_investigations[investigation_id]["errors"].append(str(e))