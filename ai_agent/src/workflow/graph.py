"""
LangGraph Workflow Graph Implementation

This module contains the main workflow graph for OSINT investigations
using LangGraph for state management and agent coordination.
"""

import asyncio
import logging
from typing import Dict, Any, Optional

from .state import (
    InvestigationState, 
    InvestigationPhase, 
    InvestigationStatus,
    create_initial_state,
    update_phase_status,
    calculate_progress,
    add_error,
    add_warning,
    update_resource_costs
)
from ..agents.planning.objective_definition import ObjectiveDefinitionAgent
from ..agents.planning.strategy_formulation import StrategyFormulationAgent
from ..agents.synthesis.intelligence_synthesis_agent import IntelligenceSynthesisAgent
from ..agents.synthesis.quality_assurance_agent import QualityAssuranceAgent
from ..agents.synthesis.report_generation_agent import ReportGenerationAgent


logger = logging.getLogger(__name__)


class OSINTWorkflow:
    """
    Main workflow orchestrator for OSINT investigations.
    
    Manages the complete investigation lifecycle from planning to synthesis.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.OSINTWorkflow")
        
        # Initialize agents
        self.objective_agent = ObjectiveDefinitionAgent()
        self.strategy_agent = StrategyFormulationAgent()
        
        # Initialize synthesis agents
        self.intelligence_synthesis_agent = IntelligenceSynthesisAgent()
        self.quality_assurance_agent = QualityAssuranceAgent()
        self.report_generation_agent = ReportGenerationAgent()
        
        self.logger.info("OSINT Workflow initialized")
    
    async def run_investigation(
        self, 
        user_request: str,
        investigation_id: Optional[str] = None,
        **kwargs
    ) -> InvestigationState:
        """
        Run a complete OSINT investigation.
        
        Args:
            user_request: The user's investigation request
            investigation_id: Optional investigation ID
            **kwargs: Additional investigation parameters
            
        Returns:
            Completed investigation state
        """
        # Create initial state
        state = create_initial_state(
            user_request=user_request,
            investigation_id=investigation_id,
            **kwargs
        )
        
        self.logger.info(f"Starting investigation: {state['investigation_id']}")
        
        try:
            # Phase 1: Planning
            state = await self._run_planning_phase(state)
            
            # Phase 2: Collection
            state = await self._run_collection_phase(state)
            
            # Phase 3: Analysis
            state = await self._run_analysis_phase(state)
            
            # Phase 4: Synthesis
            state = await self._run_synthesis_phase(state)
            
            # Mark as completed
            state = update_phase_status(
                state, 
                InvestigationPhase.COMPLETED, 
                InvestigationStatus.COMPLETED
            )
            
            self.logger.info(f"Investigation completed: {state['investigation_id']}")
            
        except Exception as e:
            self.logger.error(f"Investigation failed: {e}", exc_info=True)
            state = add_error(state, str(e))
            state = update_phase_status(
                state,
                InvestigationPhase.FAILED,
                InvestigationStatus.FAILED
            )
        
        return state
    
    async def _run_planning_phase(self, state: InvestigationState) -> InvestigationState:
        """Execute the planning phase of the investigation."""
        self.logger.info("Starting planning phase")
        
        try:
            # Update phase status
            state = update_phase_status(
                state,
                InvestigationPhase.PLANNING,
                InvestigationStatus.IN_PROGRESS
            )
            
            # Step 1: Define objectives
            state = await objective_definition_node(state)
            
            # Step 2: Formulate strategy
            state = await strategy_formulation_node(state)
            
            # Mark planning phase as completed
            state = update_phase_status(
                state,
                InvestigationPhase.PLANNING,
                InvestigationStatus.COMPLETED,
                {"duration": 5.0, "agents_used": ["ObjectiveDefinitionAgent", "StrategyFormulationAgent"]}
            )
            
            self.logger.info("Planning phase completed")
            
        except Exception as e:
            self.logger.error(f"Planning phase failed: {e}")
            state = add_error(state, str(e), InvestigationPhase.PLANNING)
            state = update_phase_status(
                state,
                InvestigationPhase.PLANNING,
                InvestigationStatus.FAILED
            )
            raise
        
        return state
    
    async def _run_collection_phase(self, state: InvestigationState) -> InvestigationState:
        """Execute the collection phase of the investigation."""
        self.logger.info("Starting collection phase")
        
        try:
            # Update phase status
            state = update_phase_status(
                state,
                InvestigationPhase.COLLECTION,
                InvestigationStatus.IN_PROGRESS
            )
            
            # Step 1: Coordinate search
            state = await search_coordination_node(state)
            
            # Step 2: Collect data
            state = await data_collection_node(state)
            
            # Mark collection phase as completed
            state = update_phase_status(
                state,
                InvestigationPhase.COLLECTION,
                InvestigationStatus.COMPLETED,
                {"duration": 10.0, "data_sources_count": 5}
            )
            
            self.logger.info("Collection phase completed")
            
        except Exception as e:
            self.logger.error(f"Collection phase failed: {e}")
            state = add_error(state, str(e), InvestigationPhase.COLLECTION)
            state = update_phase_status(
                state,
                InvestigationPhase.COLLECTION,
                InvestigationStatus.FAILED
            )
            raise
        
        return state
    
    async def _run_analysis_phase(self, state: InvestigationState) -> InvestigationState:
        """Execute the analysis phase of the investigation."""
        self.logger.info("Starting analysis phase")
        
        try:
            # Update phase status
            state = update_phase_status(
                state,
                InvestigationPhase.ANALYSIS,
                InvestigationStatus.IN_PROGRESS
            )
            
            # Step 1: Fuse data
            state = await data_fusion_node(state)
            
            # Step 2: Recognize patterns
            state = await pattern_recognition_node(state)
            
            # Step 3: Analyze context
            state = await contextual_analysis_node(state)
            
            # Mark analysis phase as completed
            state = update_phase_status(
                state,
                InvestigationPhase.ANALYSIS,
                InvestigationStatus.COMPLETED,
                {"duration": 15.0, "patterns_found": 3}
            )
            
            self.logger.info("Analysis phase completed")
            
        except Exception as e:
            self.logger.error(f"Analysis phase failed: {e}")
            state = add_error(state, str(e), InvestigationPhase.ANALYSIS)
            state = update_phase_status(
                state,
                InvestigationPhase.ANALYSIS,
                InvestigationStatus.FAILED
            )
            raise
        
        return state
    
    async def _run_synthesis_phase(self, state: InvestigationState) -> InvestigationState:
        """Execute the synthesis phase of the investigation."""
        self.logger.info("Starting synthesis phase")
        
        try:
            # Update phase status
            state = update_phase_status(
                state,
                InvestigationPhase.SYNTHESIS,
                InvestigationStatus.IN_PROGRESS
            )
            
            # Step 1: Synthesize intelligence
            state = await intelligence_synthesis_node(state)
            
            # Step 2: Quality assurance
            state = await quality_assurance_node(state)
            
            # Step 3: Generate report
            state = await report_generation_node(state)
            
            # Mark synthesis phase as completed
            state = update_phase_status(
                state,
                InvestigationPhase.SYNTHESIS,
                InvestigationStatus.COMPLETED,
                {"duration": 8.0, "report_sections": 5}
            )
            
            self.logger.info("Synthesis phase completed")
            
        except Exception as e:
            self.logger.error(f"Synthesis phase failed: {e}")
            state = add_error(state, str(e), InvestigationPhase.SYNTHESIS)
            state = update_phase_status(
                state,
                InvestigationPhase.SYNTHESIS,
                InvestigationStatus.FAILED
            )
            raise
        
        return state
    
    def get_investigation_progress(self, state: InvestigationState) -> Dict[str, Any]:
        """Get current progress of the investigation."""
        progress = calculate_progress(state)
        
        return {
            "investigation_id": state["investigation_id"],
            "current_phase": state["current_phase"].value,
            "overall_status": state["overall_status"].value,
            "progress_percentage": progress,
            "errors_count": len(state["errors"]),
            "warnings_count": len(state["warnings"]),
            "sources_used": len(state["sources_used"]),
            "confidence_level": state["confidence_level"]
        }


def create_osint_workflow(config: Optional[Dict[str, Any]] = None) -> OSINTWorkflow:
    """
    Create and return an OSINT workflow instance.
    
    Args:
        config: Optional configuration for the workflow
        
    Returns:
        OSINTWorkflow instance
    """
    return OSINTWorkflow(config)


# Workflow Node Functions
async def objective_definition_node(state: InvestigationState) -> InvestigationState:
    """Define investigation objectives using the ObjectiveDefinitionAgent."""
    try:
        agent = ObjectiveDefinitionAgent()
        
        input_data = {
            "user_request": state["user_request"]
        }
        
        result = await agent.execute(input_data)
        
        if result.success:
            state["objectives"] = result.data
            state["agents_participated"].append("ObjectiveDefinitionAgent")
            state["confidence_level"] = max(state["confidence_level"], result.confidence)
        else:
            state = add_error(state, result.error_message, InvestigationPhase.PLANNING, "ObjectiveDefinitionAgent")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.PLANNING, "objective_definition_node")


async def strategy_formulation_node(state: InvestigationState) -> InvestigationState:
    """Formulate investigation strategy using the StrategyFormulationAgent."""
    try:
        from ..agents.planning.strategy_formulation import StrategyFormulationAgent
        
        agent = StrategyFormulationAgent()
        
        input_data = {
            "user_request": state["user_request"],
            "objectives": state["objectives"]
        }
        
        result = await agent.execute(input_data)
        
        if result.success:
            state["strategy"] = result.data
            state["agents_participated"].append("StrategyFormulationAgent")
            state["confidence_level"] = max(state["confidence_level"], result.confidence)
        else:
            state = add_error(state, result.error_message, InvestigationPhase.PLANNING, "StrategyFormulationAgent")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.PLANNING, "strategy_formulation_node")


async def search_coordination_node(state: InvestigationState) -> InvestigationState:
    """Coordinate search operations across different data sources."""
    try:
        # Mock search coordination results
        state["search_coordination_results"] = {
            "surface_web_sources": ["google", "bing", "duckduckgo"],
            "social_media_sources": ["twitter", "linkedin", "facebook"],
            "public_records_sources": ["government_databases", "court_records"],
            "dark_web_sources": ["tor_networks", "hidden_services"],
            "coordination_status": "completed",
            "sources_identified": 10
        }
        
        state["collection_status"]["search_coordination"] = InvestigationStatus.COMPLETED
        state["sources_used"].extend(["google", "bing", "twitter", "linkedin"])
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.COLLECTION, "search_coordination_node")


async def data_collection_node(state: InvestigationState) -> InvestigationState:
    """Collect data from identified sources."""
    try:
        # Mock data collection results
        state["search_results"] = {
            "surface_web": [
                {"url": "example.com", "content": "Sample content 1", "relevance": 0.8},
                {"url": "test.com", "content": "Sample content 2", "relevance": 0.7}
            ],
            "social_media": [
                {"platform": "twitter", "content": "Tweet content", "relevance": 0.9},
                {"platform": "linkedin", "content": "LinkedIn content", "relevance": 0.8}
            ],
            "public_records": [
                {"source": "court_records", "content": "Legal document", "relevance": 0.6}
            ]
        }
        
        state["raw_data"] = {
            "total_records": 5,
            "sources": state["search_coordination_results"]["sources_identified"],
            "collection_timestamp": "2024-01-01T00:00:00Z"
        }
        
        state["collection_status"]["data_collection"] = InvestigationStatus.COMPLETED
        state["data_quality_metrics"] = {
            "completeness": 0.8,
            "accuracy": 0.9,
            "relevance": 0.75,
            "freshness": 0.85
        }
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.COLLECTION, "data_collection_node")


async def data_fusion_node(state: InvestigationState) -> InvestigationState:
    """Fuse and correlate data from multiple sources."""
    try:
        # Mock data fusion results
        state["fused_data"] = {
            "entities": [
                {"name": "Test Entity", "type": "organization", "confidence": 0.9}
            ],
            "relationships": [
                {"source": "Entity A", "target": "Entity B", "type": "association", "confidence": 0.8}
            ],
            "timeline": [
                {"date": "2024-01-01", "event": "Event 1", "sources": ["web", "social"]}
            ],
            "geospatial": [
                {"location": "Test Location", "coordinates": [0, 0], "relevance": 0.7}
            ]
        }
        
        state["analysis_status"]["data_fusion"] = InvestigationStatus.COMPLETED
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.ANALYSIS, "data_fusion_node")


async def pattern_recognition_node(state: InvestigationState) -> InvestigationState:
    """Recognize patterns and anomalies in the fused data."""
    try:
        # Mock pattern recognition results
        state["patterns"] = [
            {
                "type": "temporal_pattern",
                "description": "Recurring activity pattern detected",
                "confidence": 0.8,
                "significance": "medium"
            },
            {
                "type": "network_pattern",
                "description": "Connection cluster identified",
                "confidence": 0.9,
                "significance": "high"
            }
        ]
        
        state["analysis_status"]["pattern_recognition"] = InvestigationStatus.COMPLETED
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.ANALYSIS, "pattern_recognition_node")


async def contextual_analysis_node(state: InvestigationState) -> InvestigationState:
    """Perform contextual analysis of the data and patterns."""
    try:
        # Mock contextual analysis results
        state["context_analysis"] = {
            "historical_context": "Historical background information",
            "cultural_context": "Cultural factors and considerations",
            "geopolitical_context": "Geopolitical implications",
            "technical_context": "Technical domain analysis",
            "risk_assessment": {
                "overall_risk": "medium",
                "risk_factors": ["factor1", "factor2"],
                "mitigation_strategies": ["strategy1", "strategy2"]
            }
        }
        
        state["analysis_status"]["contextual_analysis"] = InvestigationStatus.COMPLETED
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.ANALYSIS, "contextual_analysis_node")


async def intelligence_synthesis_node(state: InvestigationState) -> InvestigationState:
    """Synthesize intelligence from analysis results."""
    try:
        # Initialize the intelligence synthesis agent
        agent = IntelligenceSynthesisAgent()
        
        # Prepare input data for intelligence synthesis
        synthesis_input = {
            "fused_data": state.get("fused_data", {}),
            "patterns": state.get("patterns", []),
            "context_analysis": state.get("context_analysis", {}),
            "user_request": state.get("user_request", ""),
            "objectives": state.get("objectives", {})
        }
        
        # Execute intelligence synthesis
        result = await agent.execute(synthesis_input)
        
        if result.success:
            state["intelligence"] = result.data
            state["synthesis_status"]["intelligence_synthesis"] = InvestigationStatus.COMPLETED
            update_resource_costs(state, "intelligence_synthesis", result.metadata.get("processing_time", 4.0))
        else:
            error_msg = result.error_message if result.error_message else "Intelligence synthesis failed"
            return add_error(state, error_msg, InvestigationPhase.SYNTHESIS, "intelligence_synthesis_node")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.SYNTHESIS, "intelligence_synthesis_node")


async def quality_assurance_node(state: InvestigationState) -> InvestigationState:
    """Perform quality assurance on the synthesized intelligence."""
    try:
        # Initialize the quality assurance agent
        agent = QualityAssuranceAgent()
        
        # Prepare input data for quality assurance
        qa_input = {
            "intelligence": state.get("intelligence", {}),
            "fused_data": state.get("fused_data", {}),
            "patterns": state.get("patterns", []),
            "context_analysis": state.get("context_analysis", {}),
            "sources_used": state.get("sources_used", []),
            "user_request": state.get("user_request", "")
        }
        
        # Execute quality assurance
        result = await agent.execute(qa_input)
        
        if result.success:
            state["quality_assessment"] = result.data
            state["synthesis_status"]["quality_assurance"] = InvestigationStatus.COMPLETED
            update_resource_costs(state, "quality_assurance", result.metadata.get("processing_time", 5.0))
        else:
            error_msg = result.error_message if result.error_message else "Quality assurance failed"
            return add_error(state, error_msg, InvestigationPhase.SYNTHESIS, "quality_assurance_node")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.SYNTHESIS, "quality_assurance_node")


async def report_generation_node(state: InvestigationState) -> InvestigationState:
    """Generate the final investigation report."""
    try:
        # Initialize the report generation agent
        agent = ReportGenerationAgent()
        
        # Prepare input data for report generation
        report_input = {
            "intelligence": state.get("intelligence", {}),
            "quality_assessment": state.get("quality_assessment", {}),
            "fused_data": state.get("fused_data", {}),
            "patterns": state.get("patterns", []),
            "context_analysis": state.get("context_analysis", {}),
            "sources_used": state.get("sources_used", []),
            "user_request": state.get("user_request", ""),
            "objectives": state.get("objectives", {}),
            "investigation_metadata": {
                "case_id": state.get("investigation_id", "unknown"),
                "start_time": state.get("start_time", "unknown"),
                "investigator": "OSINT System"
            }
        }
        
        # Execute report generation
        result = await agent.execute(report_input)
        
        if result.success:
            report_data = result.data
            state["final_report"] = report_data.get("primary_report", {})
            state["alternative_formats"] = report_data.get("alternative_formats", {})
            state["report_metadata"] = report_data.get("report_metadata", {})
            state["synthesis_status"]["report_generation"] = InvestigationStatus.COMPLETED
            update_resource_costs(state, "report_generation", result.metadata.get("processing_time", 6.0))
        else:
            error_msg = result.error_message if result.error_message else "Report generation failed"
            return add_error(state, error_msg, InvestigationPhase.SYNTHESIS, "report_generation_node")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.SYNTHESIS, "report_generation_node")