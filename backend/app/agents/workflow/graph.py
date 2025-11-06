"""
Workflow orchestration system for OSINT investigations.
Replaces the missing ai_agent.src.workflow.graph module.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import json

import sys
import os
# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), '../../../..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)
# Also add the app directory
app_path = os.path.join(os.path.dirname(__file__), '../../..')
if app_path not in sys.path:
    sys.path.insert(0, app_path)

from app.agents.registry import agent_registry
from app.agents.base.osint_agent import AgentResult


class InvestigationPhase(Enum):
    """Investigation phases."""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    REPORTING = "reporting"
    COMPLETED = "completed"


class InvestigationStatus(Enum):
    """Investigation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class InvestigationState:
    """Investigation state management."""
    investigation_id: str
    user_request: str
    phase: InvestigationPhase = InvestigationPhase.INITIALIZATION
    status: InvestigationStatus = InvestigationStatus.PENDING
    initiated_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Investigation data
    objectives: Dict[str, Any] = field(default_factory=dict)
    strategy: Dict[str, Any] = field(default_factory=dict)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    intelligence: Dict[str, Any] = field(default_factory=dict)
    patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    sources_used: List[str] = field(default_factory=list)
    agents_executed: List[str] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    confidence_level: float = 0.0
    progress_percentage: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "investigation_id": self.investigation_id,
            "user_request": self.user_request,
            "phase": self.phase.value,
            "status": self.status.value,
            "initiated_at": self.initiated_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "objectives": self.objectives,
            "strategy": self.strategy,
            "collected_data": self.collected_data,
            "analysis_results": self.analysis_results,
            "intelligence": self.intelligence,
            "patterns": self.patterns,
            "sources_used": self.sources_used,
            "agents_executed": self.agents_executed,
            "errors": self.errors,
            "confidence_level": self.confidence_level,
            "progress_percentage": self.progress_percentage
        }


class OSINTWorkflow:
    """OSINT investigation workflow orchestrator."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.registry = agent_registry
        
    async def run_investigation(
        self, 
        user_request: str,
        investigation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run a complete OSINT investigation."""
        
        # Create investigation state
        if not investigation_id:
            investigation_id = f"inv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
        state = InvestigationState(
            investigation_id=investigation_id,
            user_request=user_request,
            phase=InvestigationPhase.INITIALIZATION,
            status=InvestigationStatus.IN_PROGRESS
        )
        
        self.logger.info(f"Starting investigation {investigation_id}: {user_request}")
        
        try:
            # Phase 1: Planning
            state = await self._planning_phase(state)
            
            # Phase 2: Collection
            state = await self._collection_phase(state)
            
            # Phase 3: Analysis
            state = await self._analysis_phase(state)
            
            # Phase 4: Synthesis
            state = await self._synthesis_phase(state)
            
            # Phase 5: Reporting
            state = await self._reporting_phase(state)
            
            # Mark as completed
            state.status = InvestigationStatus.COMPLETED
            state.phase = InvestigationPhase.COMPLETED
            state.completed_at = datetime.utcnow()
            state.progress_percentage = 100.0
            
            self.logger.info(f"Investigation {investigation_id} completed successfully")
            
        except Exception as e:
            self.logger.error(f"Investigation {investigation_id} failed: {e}")
            state.status = InvestigationStatus.FAILED
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "phase": state.phase.value
            })
            
        finally:
            state.updated_at = datetime.utcnow()
            
        return state.to_dict()
    
    async def _planning_phase(self, state: InvestigationState) -> InvestigationState:
        """Planning phase: define objectives and strategy."""
        self.logger.info(f"Planning phase for {state.investigation_id}")
        
        state.phase = InvestigationPhase.PLANNING
        state.progress_percentage = 10.0
        
        # Execute objective definition agent
        try:
            result = await self.registry.execute_agent(
                "objective_definition",
                {"user_request": state.user_request}
            )
            
            if result.success:
                state.objectives = result.data
                state.agents_executed.append("objective_definition")
                state.confidence_level += 0.2
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "objective_definition",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Objective definition failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        # Execute strategy formulation agent
        try:
            result = await self.registry.execute_agent(
                "strategy_formulation",
                {
                    "user_request": state.user_request,
                    "objectives": state.objectives
                }
            )
            
            if result.success:
                state.strategy = result.data
                state.agents_executed.append("strategy_formulation")
                state.confidence_level += 0.1
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "strategy_formulation", 
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Strategy formulation failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        state.progress_percentage = 25.0
        return state
    
    async def _collection_phase(self, state: InvestigationState) -> InvestigationState:
        """Collection phase: gather data from multiple sources."""
        self.logger.info(f"Collection phase for {state.investigation_id}")
        
        state.phase = InvestigationPhase.COLLECTION
        state.progress_percentage = 30.0
        
        # Execute URL discovery
        try:
            result = await self.registry.execute_agent(
                "url_discovery",
                {
                    "user_request": state.user_request,
                    "objectives": state.objectives,
                    "strategy": state.strategy
                }
            )
            
            if result.success:
                state.collected_data["urls"] = result.data
                state.agents_executed.append("url_discovery")
                state.sources_used.extend(result.data.get("sources", []))
                state.confidence_level += 0.1
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "url_discovery",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"URL discovery failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        # Execute simple search
        try:
            result = await self.registry.execute_agent(
                "simple_search",
                {
                    "user_request": state.user_request,
                    "objectives": state.objectives,
                    "strategy": state.strategy,
                    "query": state.user_request
                }
            )
            
            if result.success:
                state.collected_data["search_results"] = result.data
                state.agents_executed.append("simple_search")
                state.sources_used.extend(result.data.get("engines_used", []))
                state.confidence_level += 0.2
                state.progress_percentage += 10.0
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "simple_search",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Simple search failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        state.progress_percentage = 50.0
        return state
    
    async def _analysis_phase(self, state: InvestigationState) -> InvestigationState:
        """Analysis phase: analyze collected data."""
        self.logger.info(f"Analysis phase for {state.investigation_id}")
        
        state.phase = InvestigationPhase.ANALYSIS
        state.progress_percentage = 55.0
        
        # Execute contextual analysis
        try:
            result = await self.registry.execute_agent(
                "contextual_analysis",
                {
                    "collected_data": state.collected_data,
                    "objectives": state.objectives,
                    "user_request": state.user_request
                }
            )
            
            if result.success:
                state.analysis_results["contextual"] = result.data
                state.agents_executed.append("contextual_analysis")
                state.confidence_level += 0.1
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "contextual_analysis",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Contextual analysis failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        # Execute pattern recognition
        try:
            result = await self.registry.execute_agent(
                "pattern_recognition",
                {
                    "collected_data": state.collected_data,
                    "context_analysis": state.analysis_results.get("contextual", {})
                }
            )
            
            if result.success:
                state.patterns = result.data.get("patterns", [])
                state.analysis_results["patterns"] = result.data
                state.agents_executed.append("pattern_recognition")
                state.confidence_level += 0.1
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "pattern_recognition",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Pattern recognition failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        state.progress_percentage = 70.0
        return state
    
    async def _synthesis_phase(self, state: InvestigationState) -> InvestigationState:
        """Synthesis phase: fuse data and generate intelligence."""
        self.logger.info(f"Synthesis phase for {state.investigation_id}")
        
        state.phase = InvestigationPhase.SYNTHESIS
        state.progress_percentage = 75.0
        
        # Execute data fusion
        try:
            result = await self.registry.execute_agent(
                "data_fusion",
                {
                    "collected_data": state.collected_data,
                    "analysis_results": state.analysis_results,
                    "patterns": state.patterns
                }
            )
            
            if result.success:
                state.intelligence["fused_data"] = result.data
                state.agents_executed.append("data_fusion")
                state.confidence_level += 0.1
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "data_fusion",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Data fusion failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        state.progress_percentage = 85.0
        return state
    
    async def _reporting_phase(self, state: InvestigationState) -> InvestigationState:
        """Reporting phase: generate final reports."""
        self.logger.info(f"Reporting phase for {state.investigation_id}")
        
        state.phase = InvestigationPhase.REPORTING
        state.progress_percentage = 90.0
        
        # Execute pipeline generation for reports
        try:
            result = await self.registry.execute_agent(
                "pipeline_generation",
                {
                    "intelligence": state.intelligence,
                    "analysis_results": state.analysis_results,
                    "objectives": state.objectives,
                    "user_request": state.user_request
                }
            )
            
            if result.success:
                state.intelligence["reports"] = result.data
                state.agents_executed.append("pipeline_generation")
                state.confidence_level += 0.1
            else:
                state.errors.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "agent": "pipeline_generation",
                    "error": result.error_message
                })
                
        except Exception as e:
            self.logger.error(f"Pipeline generation failed: {e}")
            state.errors.append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            })
        
        state.progress_percentage = 95.0
        return state
    
    def get_investigation_progress(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Get investigation progress information."""
        return {
            "investigation_id": state.get("investigation_id"),
            "phase": state.get("phase"),
            "status": state.get("status"),
            "progress_percentage": state.get("progress_percentage", 0.0),
            "confidence_level": state.get("confidence_level", 0.0),
            "agents_executed": state.get("agents_executed", []),
            "sources_used": state.get("sources_used", []),
            "errors_count": len(state.get("errors", [])),
            "last_updated": state.get("updated_at"),
            "initiated_at": state.get("initiated_at")
        }


def create_osint_workflow(config: Optional[Dict[str, Any]] = None) -> OSINTWorkflow:
    """Create and initialize an OSINT workflow."""
    return OSINTWorkflow(config)