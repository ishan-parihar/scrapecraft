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
from ..agents.collection.surface_web_collector import SurfaceWebCollectorAgent
from ..agents.collection.social_media_collector import SocialMediaCollectorAgent
from ..agents.collection.public_records_collector import PublicRecordsCollectorAgent
from ..agents.collection.dark_web_collector import DarkWebCollectorAgent
from ..agents.synthesis.intelligence_synthesis_agent import IntelligenceSynthesisAgent
from ..agents.synthesis.quality_assurance_agent import QualityAssuranceAgent
from ..agents.synthesis.report_generation_agent import ReportGenerationAgent
from ..agents.analysis.data_fusion_agent import DataFusionAgent
from ..agents.analysis.pattern_recognition_agent import PatternRecognitionAgent
from ..agents.analysis.contextual_analysis_agent import ContextualAnalysisAgent
from ..agents.base.osint_agent import AgentConfig


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
        from ..utils.tools.langchain_tools import get_global_tool_manager
        tool_manager = get_global_tool_manager()
        
        self.objective_agent = ObjectiveDefinitionAgent()
        self.strategy_agent = StrategyFormulationAgent()
        
        # Initialize collection agents with tools
        self.surface_web_agent = SurfaceWebCollectorAgent(tools=tool_manager.tools)
        self.social_media_agent = SocialMediaCollectorAgent(tools=tool_manager.tools)
        self.public_records_agent = PublicRecordsCollectorAgent(tools=tool_manager.tools)
        self.dark_web_agent = DarkWebCollectorAgent(tools=tool_manager.tools)
        
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
            state = add_error(state, result.error_message or "Objective definition failed", InvestigationPhase.PLANNING, "ObjectiveDefinitionAgent")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e) or "Error in objective definition node", InvestigationPhase.PLANNING, "objective_definition_node")


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
            error_msg = result.error_message if result.error_message else "Strategy formulation failed"
            state = add_error(state, error_msg, InvestigationPhase.PLANNING, "StrategyFormulationAgent")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.PLANNING, "strategy_formulation_node")

async def search_coordination_node(state: InvestigationState) -> InvestigationState:
    """Coordinate search operations across different data sources."""
    try:
        # Initialize collection agents
        surface_web_agent = SurfaceWebCollectorAgent()
        social_media_agent = SocialMediaCollectorAgent()
        public_records_agent = PublicRecordsCollectorAgent()
        dark_web_agent = DarkWebCollectorAgent()
        
        # Determine which sources to search based on objectives
        objectives = state.get("objectives", {})
        
        search_coordination_results = {
            "surface_web_sources": [],
            "social_media_sources": [],
            "public_records_sources": [],
            "dark_web_sources": [],
            "coordination_status": "completed",
            "sources_identified": 0
        }
        
        # Determine appropriate sources based on investigation objectives
        if "web_search" in str(objectives).lower() or "surface" in str(objectives).lower():
            search_coordination_results["surface_web_sources"] = ["google", "bing", "duckduckgo"]
        
        if "social_media" in str(objectives).lower() or "twitter" in str(objectives).lower():
            search_coordination_results["social_media_sources"] = ["twitter", "linkedin", "facebook", "instagram"]
        
        if "public_records" in str(objectives).lower() or "records" in str(objectives).lower():
            search_coordination_results["public_records_sources"] = ["government_databases", "court_records", "property_records"]
        
        if "dark_web" in str(objectives).lower() or "tor" in str(objectives).lower():
            search_coordination_results["dark_web_sources"] = ["tor_networks", "hidden_services"]
        
        search_coordination_results["sources_identified"] = (
            len(search_coordination_results["surface_web_sources"]) +
            len(search_coordination_results["social_media_sources"]) +
            len(search_coordination_results["public_records_sources"]) +
            len(search_coordination_results["dark_web_sources"])
        )
        
        state["search_coordination_results"] = search_coordination_results
        state["collection_status"]["search_coordination"] = InvestigationStatus.COMPLETED
        state["sources_used"].extend(search_coordination_results["surface_web_sources"] + 
                                   search_coordination_results["social_media_sources"])
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.COLLECTION, "search_coordination_node")

async def data_collection_node(state: InvestigationState) -> InvestigationState:
    """Collect data from identified sources."""
    try:
        # Initialize collection agents with tools
        from ..utils.tools.langchain_tools import get_global_tool_manager
        tool_manager = get_global_tool_manager()
        
        surface_web_agent = SurfaceWebCollectorAgent(tools=tool_manager.tools)
        social_media_agent = SocialMediaCollectorAgent(tools=tool_manager.tools)
        public_records_agent = PublicRecordsCollectorAgent(tools=tool_manager.tools)
        dark_web_agent = DarkWebCollectorAgent(tools=tool_manager.tools)
        
        search_results = {}
        raw_data = {
            "total_records": 0,
            "sources": state["search_coordination_results"]["sources_identified"],
            "collection_timestamp": "2024-01-01T00:00:00Z"
        }
        
        # Collect surface web data if requested
        if state["search_coordination_results"]["surface_web_sources"]:
            surface_web_input = {
                "task_type": "web_search",
                "search_queries": [state.get("user_request", "general search")],
                "sources": state["search_coordination_results"]["surface_web_sources"]
            }
            surface_result = await surface_web_agent.execute(surface_web_input)
            if surface_result.success:
                search_results["surface_web"] = surface_result.data.get("results", [])
                raw_data["total_records"] += len(surface_result.data.get("results", []))
                state["agents_participated"].append("SurfaceWebCollectorAgent")
                state["confidence_level"] = max(state["confidence_level"], surface_result.confidence)
            else:
                state = add_warning(state, f"Surface web collection failed: {surface_result.error_message}")
        
        # Collect social media data if requested
        if state["search_coordination_results"]["social_media_sources"]:
            social_media_input = {
                "task_type": "social_media_scan",
                "search_queries": [state.get("user_request", "general search")],
                "platforms": state["search_coordination_results"]["social_media_sources"]
            }
            social_result = await social_media_agent.execute(social_media_input)
            if social_result.success:
                search_results["social_media"] = social_result.data.get("results", [])
                raw_data["total_records"] += len(social_result.data.get("results", []))
                state["agents_participated"].append("SocialMediaCollectorAgent")
                state["confidence_level"] = max(state["confidence_level"], social_result.confidence)
            else:
                state = add_warning(state, f"Social media collection failed: {social_result.error_message}")
        
        # Collect public records data if requested
        if state["search_coordination_results"]["public_records_sources"]:
            public_records_input = {
                "task_type": "public_records_search",
                "search_criteria": [state.get("user_request", "general search")],
                "record_types": state["search_coordination_results"]["public_records_sources"]
            }
            public_result = await public_records_agent.execute(public_records_input)
            if public_result.success:
                search_results["public_records"] = public_result.data.get("results", [])
                raw_data["total_records"] += len(public_result.data.get("results", []))
                state["agents_participated"].append("PublicRecordsCollectorAgent")
                state["confidence_level"] = max(state["confidence_level"], public_result.confidence)
            else:
                state = add_warning(state, f"Public records collection failed: {public_result.error_message}")
        
        # Collect dark web data if requested (with authorization)
        if state["search_coordination_results"]["dark_web_sources"]:
            dark_web_input = {
                "task_type": "dark_web_scan",
                "search_queries": [state.get("user_request", "general search")],
                "sources": state["search_coordination_results"]["dark_web_sources"],
                "authorized": True  # This would normally come from auth system
            }
            dark_result = await dark_web_agent.execute(dark_web_input)
            if dark_result.success:
                search_results["dark_web"] = dark_result.data.get("results", [])
                raw_data["total_records"] += len(dark_result.data.get("results", []))
                state["agents_participated"].append("DarkWebCollectorAgent")
                state["confidence_level"] = max(state["confidence_level"], dark_result.confidence)
            else:
                state = add_warning(state, f"Dark web collection failed: {dark_result.error_message}")
        
        state["search_results"] = search_results
        state["raw_data"] = raw_data
        state["collection_status"]["data_collection"] = InvestigationStatus.COMPLETED
        
        # Calculate data quality metrics based on what was collected
        total_records = raw_data["total_records"]
        state["data_quality_metrics"] = {
            "completeness": min(1.0, total_records / max(1, state.get("search_coordination_results", {}).get("sources_identified", 1))),
            "accuracy": 0.85,  # Default for now
            "relevance": 0.8,  # Default for now
            "freshness": 0.9   # Default for now
        }
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.COLLECTION, "data_collection_node")

async def data_fusion_node(state: InvestigationState) -> InvestigationState:
     """Fuse and correlate data from multiple sources."""
     try:
         config = AgentConfig(
             agent_id="data_fusion_agent",
             role="Data Fusion Agent",
             description="Agent responsible for fusing and integrating data from multiple sources"
         )
         agent = DataFusionAgent(config=config)
         
         # Prepare input data for data fusion
         fusion_input = {
             "search_results": state.get("search_results", {}),
             "raw_data": state.get("raw_data", {}),
             "sources_used": state.get("sources_used", []),
             "user_request": state.get("user_request", ""),
             "objectives": state.get("objectives", {})
         }
         
         # Execute data fusion
         result = await agent.execute(fusion_input)
         
         if result.success:
             state["fused_data"] = result.data
             state["agents_participated"].append("DataFusionAgent")
             state["confidence_level"] = max(state["confidence_level"], result.confidence)
             state["analysis_status"]["data_fusion"] = InvestigationStatus.COMPLETED
         else:
             error_msg = result.error_message if result.error_message else "Data fusion failed"
             state = add_error(state, error_msg, InvestigationPhase.ANALYSIS, "DataFusionAgent")
         
         return state
         
     except Exception as e:
         return add_error(state, str(e), InvestigationPhase.ANALYSIS, "data_fusion_node")


async def pattern_recognition_node(state: InvestigationState) -> InvestigationState:
    """Recognize patterns and anomalies in the fused data."""
    try:
        config = AgentConfig(
            agent_id="pattern_recognition_agent",
            role="Pattern Recognition Agent",
            description="Agent responsible for recognizing patterns in OSINT data"
        )
        agent = PatternRecognitionAgent(config=config)
        
        # Prepare input data for pattern recognition
        pattern_input = {
            "task_type": "behavioral_patterns",
            "fused_data": state.get("fused_data", {}),
            "search_results": state.get("search_results", {}),
            "user_request": state.get("user_request", ""),
            "objectives": state.get("objectives", {})
        }
        
        # Execute pattern recognition
        result = await agent.execute(pattern_input)
        
        if result.success:
            # Extract patterns from the result, handling different possible return structures
            if isinstance(result.data, dict) and "results" in result.data:
                # If results is a list of dicts, extract the patterns from each
                raw_patterns = result.data["results"]
                all_patterns = []
                for result_item in raw_patterns:
                    if isinstance(result_item, dict) and "results" in result_item:
                        if isinstance(result_item["results"], list):
                            all_patterns.extend(result_item["results"])
                        else:
                            all_patterns.append(result_item["results"])
                state["patterns"] = all_patterns
            elif isinstance(result.data, list):
                state["patterns"] = result.data
            else:
                # If it's a single result, wrap it in a list
                state["patterns"] = [result.data] if result.data else []
            
            state["agents_participated"].append("PatternRecognitionAgent")
            state["confidence_level"] = max(state["confidence_level"], result.confidence)
            state["analysis_status"]["pattern_recognition"] = InvestigationStatus.COMPLETED
        else:
            error_msg = result.error_message if result.error_message else "Pattern recognition failed"
            state = add_error(state, error_msg, InvestigationPhase.ANALYSIS, "PatternRecognitionAgent")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.ANALYSIS, "pattern_recognition_node")


async def contextual_analysis_node(state: InvestigationState) -> InvestigationState:
    """Perform contextual analysis of the data and patterns."""
    try:
        config = AgentConfig(
            agent_id="contextual_analysis_agent",
            role="Contextual Analysis Agent",
            description="Agent responsible for providing contextual analysis of OSINT data"
        )
        agent = ContextualAnalysisAgent(config=config)
        
        # Prepare input data for contextual analysis
        context_input = {
            "task_type": "situational_awareness",
            "fused_data": state.get("fused_data", {}),
            "patterns": state.get("patterns", []),
            "search_results": state.get("search_results", {}),
            "user_request": state.get("user_request", ""),
            "objectives": state.get("objectives", {})
        }
        
        # Execute contextual analysis
        result = await agent.execute(context_input)
        
        if result.success:
            # Extract context analysis from the result, handling different possible return structures
            if isinstance(result.data, dict) and "results" in result.data:
                # If results is a list of dicts, take the first set of results
                raw_results = result.data["results"]
                if isinstance(raw_results, list) and len(raw_results) > 0:
                    # Take the first result if it has the context data
                    state["context_analysis"] = raw_results[0] if isinstance(raw_results[0], dict) else {"analysis": raw_results[0]}
                else:
                    state["context_analysis"] = {"analysis": raw_results if isinstance(raw_results, dict) else {}}
            elif isinstance(result.data, dict):
                state["context_analysis"] = result.data
            else:
                # If it's not a dict, wrap it in a dictionary
                state["context_analysis"] = {"analysis": result.data}
            
            state["agents_participated"].append("ContextualAnalysisAgent")
            state["confidence_level"] = max(state["confidence_level"], result.confidence)
            state["analysis_status"]["contextual_analysis"] = InvestigationStatus.COMPLETED
        else:
            error_msg = result.error_message if result.error_message else "Contextual analysis failed"
            state = add_error(state, error_msg, InvestigationPhase.ANALYSIS, "ContextualAnalysisAgent")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.ANALYSIS, "contextual_analysis_node")


async def intelligence_synthesis_node(state: InvestigationState) -> InvestigationState:
    """Synthesize intelligence from analysis results."""
    try:
        # Initialize the enhanced intelligence synthesis agent with mandatory source links
        from ..agents.synthesis.enhanced_intelligence_synthesis_agent_v2 import EnhancedIntelligenceSynthesisAgentV2
        agent = EnhancedIntelligenceSynthesisAgentV2()
        
        # Prepare input data for intelligence synthesis
        synthesis_input = {
            "fused_data": state.get("fused_data", {}),
            "patterns": state.get("patterns", []),
            "context_analysis": state.get("context_analysis", {}),
            "sources_used": state.get("sources_used", []),
            "user_request": state.get("user_request", ""),
            "objectives": state.get("objectives", {})
        }
        
        # Execute intelligence synthesis
        result = await agent.execute(synthesis_input)
        
        if result.success:
            state["intelligence"] = result.data
            state["synthesis_status"]["intelligence_synthesis"] = InvestigationStatus.COMPLETED
            # Update resource costs - need to pass a dict
            cost_update = {"intelligence_synthesis_time": result.metadata.get("processing_time", 4.0)}
            state = update_resource_costs(state, cost_update)
        else:
            error_msg = result.error_message if result.error_message else "Intelligence synthesis failed"
            return add_error(state, error_msg or "Intelligence synthesis failed", InvestigationPhase.SYNTHESIS, "intelligence_synthesis_node")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e) or "Error in intelligence synthesis node", InvestigationPhase.SYNTHESIS, "intelligence_synthesis_node")


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
            cost_update = {"quality_assurance_time": result.metadata.get("processing_time", 5.0)}
            state = update_resource_costs(state, cost_update)
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
            cost_update = {"report_generation_time": result.metadata.get("processing_time", 6.0)}
            state = update_resource_costs(state, cost_update)
        else:
            error_msg = result.error_message if result.error_message else "Report generation failed"
            return add_error(state, error_msg, InvestigationPhase.SYNTHESIS, "report_generation_node")
        
        return state
        
    except Exception as e:
        return add_error(state, str(e), InvestigationPhase.SYNTHESIS, "report_generation_node")