"""
LangGraph Workflow Graph Implementation

This module contains the main workflow graph for OSINT investigations
using LangGraph for state management and agent coordination.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

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
         # Load environment variables from .env file
         load_dotenv()
         
         self.config = config or {}
         self.logger = logging.getLogger(f"{__name__}.OSINTWorkflow")
         
         # Initialize agents
         # Using dynamic import to avoid import issues
         import importlib.util
         import os
         tool_module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'tools', 'langchain_tools.py')
         spec = importlib.util.spec_from_file_location("langchain_tools", tool_module_path)
         if spec is not None and spec.loader is not None:
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            get_global_tool_manager = tool_module.get_global_tool_manager
         else:
            raise ImportError("Could not load scraping tools module")
         tool_manager = get_global_tool_manager()
         
         # Initialize AI backend bridge for state synchronization
         # Using dynamic import to avoid import issues
         import importlib.util
         import os
         bridge_module_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils', 'bridge', 'ai_backend_bridge.py')
         spec = importlib.util.spec_from_file_location("ai_backend_bridge", bridge_module_path)
         if spec is not None and spec.loader is not None:
            bridge_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bridge_module)
            get_global_ai_bridge = bridge_module.get_global_ai_bridge
         else:
            raise ImportError("Could not load AI backend bridge module")
         
         # Get the bridge instance (this will be awaited when used)
         self.ai_backend_bridge = get_global_ai_bridge()
         
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
        
        # Sync initial state with backend
        try:
           ai_backend_bridge = await self.ai_backend_bridge
           sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
           if not sync_result.get("success", True):
               self.logger.warning(f"State sync failed: {sync_result.get('error')}")
        except Exception as e:
           self.logger.warning(f"Could not sync investigation state with backend: {str(e)}")
        
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
           
           # Sync final state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Final state sync failed: {sync_result.get('error')}")
           except Exception as sync_e:
               self.logger.warning(f"Could not sync final investigation state with backend: {str(sync_e)}")
           
        except Exception as e:
           self.logger.error(f"Investigation failed: {e}", exc_info=True)
           state = add_error(state, str(e))
           state = update_phase_status(
               state,
               InvestigationPhase.FAILED,
               InvestigationStatus.FAILED
           )
           
           # Sync failed state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Failed state sync failed: {sync_result.get('error')}")
           except Exception as sync_e:
               self.logger.warning(f"Could not sync failed investigation state with backend: {str(sync_e)}")
        
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
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Planning phase state sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync planning phase state with backend: {str(e)}")
           
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
           
           # Update progress percentage
           state["progress_percentage"] = calculate_progress(state)
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Planning phase completion sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync planning phase completion with backend: {str(e)}")
           
           self.logger.info("Planning phase completed")
           
        except Exception as e:
           self.logger.error(f"Planning phase failed: {e}")
           state = add_error(state, str(e), InvestigationPhase.PLANNING)
           state = update_phase_status(
               state,
               InvestigationPhase.PLANNING,
               InvestigationStatus.FAILED
           )
           
           # Sync failed state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Planning phase failure sync failed: {sync_result.get('error')}")
           except Exception as sync_e:
               self.logger.warning(f"Could not sync planning phase failure with backend: {str(sync_e)}")
           
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
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Collection phase state sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync collection phase state with backend: {str(e)}")
           
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
           
           # Update progress percentage
           state["progress_percentage"] = calculate_progress(state)
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Collection phase completion sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync collection phase completion with backend: {str(e)}")
           
           self.logger.info("Collection phase completed")
           
        except Exception as e:
           self.logger.error(f"Collection phase failed: {e}")
           state = add_error(state, str(e), InvestigationPhase.COLLECTION)
           state = update_phase_status(
               state,
               InvestigationPhase.COLLECTION,
               InvestigationStatus.FAILED
           )
           
           # Sync failed state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Collection phase failure sync failed: {sync_result.get('error')}")
           except Exception as sync_e:
               self.logger.warning(f"Could not sync collection phase failure with backend: {str(sync_e)}")
           
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
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Analysis phase state sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync analysis phase state with backend: {str(e)}")
           
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
           
           # Update progress percentage
           state["progress_percentage"] = calculate_progress(state)
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Analysis phase completion sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync analysis phase completion with backend: {str(e)}")
           
           self.logger.info("Analysis phase completed")
           
        except Exception as e:
           self.logger.error(f"Analysis phase failed: {e}")
           state = add_error(state, str(e), InvestigationPhase.ANALYSIS)
           state = update_phase_status(
               state,
               InvestigationPhase.ANALYSIS,
               InvestigationStatus.FAILED
           )
           
           # Sync failed state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Analysis phase failure sync failed: {sync_result.get('error')}")
           except Exception as sync_e:
               self.logger.warning(f"Could not sync analysis phase failure with backend: {str(sync_e)}")
           
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
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Synthesis phase state sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync synthesis phase state with backend: {str(e)}")
           
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
           
           # Update progress percentage
           state["progress_percentage"] = calculate_progress(state)
           
           # Sync state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Synthesis phase completion sync failed: {sync_result.get('error')}")
           except Exception as e:
               self.logger.warning(f"Could not sync synthesis phase completion with backend: {str(e)}")
           
           self.logger.info("Synthesis phase completed")
           
        except Exception as e:
           self.logger.error(f"Synthesis phase failed: {e}")
           state = add_error(state, str(e), InvestigationPhase.SYNTHESIS)
           state = update_phase_status(
               state,
               InvestigationPhase.SYNTHESIS,
               InvestigationStatus.FAILED
           )
           
           # Sync failed state with backend
           try:
               ai_backend_bridge = await self.ai_backend_bridge
               sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
               if not sync_result.get("success", True):
                   self.logger.warning(f"Synthesis phase failure sync failed: {sync_result.get('error')}")
           except Exception as sync_e:
               self.logger.warning(f"Could not sync synthesis phase failure with backend: {str(sync_e)}")
           
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
        
        # Determine which sources to search based on both objectives and strategy
        objectives = state.get("objectives", {})
        strategy = state.get("strategy", {})
        
        search_coordination_results = {
           "surface_web_sources": [],
           "social_media_sources": [],
           "public_records_sources": [],
           "dark_web_sources": [],
           "coordination_status": "completed",
           "sources_identified": 0
        }
        
        # Determine appropriate sources based on investigation objectives (backward compatibility)
        if "web_search" in str(objectives).lower() or "surface" in str(objectives).lower():
           search_coordination_results["surface_web_sources"] = ["google", "bing", "duckduckgo"]
        
        if "social_media" in str(objectives).lower() or "twitter" in str(objectives).lower():
           search_coordination_results["social_media_sources"] = ["twitter", "linkedin", "facebook", "instagram"]
        
        if "public_records" in str(objectives).lower() or "records" in str(objectives).lower():
           search_coordination_results["public_records_sources"] = ["government_databases", "court_records", "property_records"]
        
        if "dark_web" in str(objectives).lower() or "tor" in str(objectives).lower():
           search_coordination_results["dark_web_sources"] = ["tor_networks", "hidden_services"]
        
        # Determine sources based on strategy (primary method)
        strategy_data_sources = strategy.get("data_sources", {})
        primary_sources = strategy_data_sources.get("primary_sources", [])
        secondary_sources = strategy_data_sources.get("secondary_sources", [])
        
        # Process all data sources to identify search targets
        all_sources = primary_sources + secondary_sources
        for source in all_sources:
           source_type = source.get("type", "").lower()
           if source_type == "surface_web":
               if not search_coordination_results["surface_web_sources"]:  # Only add if not already set
                   search_coordination_results["surface_web_sources"] = ["google", "bing", "duckduckgo"]
           elif source_type == "social_media":
               if not search_coordination_results["social_media_sources"]:  # Only add if not already set
                   search_coordination_results["social_media_sources"] = ["twitter", "linkedin", "facebook", "instagram"]
           elif source_type == "public_records":
               if not search_coordination_results["public_records_sources"]:  # Only add if not already set
                   search_coordination_results["public_records_sources"] = ["government_databases", "court_records", "property_records"]
           elif source_type == "dark_web":
               if not search_coordination_results["dark_web_sources"]:  # Only add if not already set
                   search_coordination_results["dark_web_sources"] = ["tor_networks", "hidden_services"]
        
        # Also check for specific sources in strategy
        for source in all_sources:
           specific_sources = source.get("specific_sources", [])
           for specific_source in specific_sources:
               specific_source_lower = specific_source.lower()
               if "search engine" in specific_source_lower or "public website" in specific_source_lower:
                   if not search_coordination_results["surface_web_sources"]:
                       search_coordination_results["surface_web_sources"] = ["google", "bing", "duckduckgo"]
               elif "social" in specific_source_lower:
                   if not search_coordination_results["social_media_sources"]:
                       search_coordination_results["social_media_sources"] = ["twitter", "linkedin", "facebook", "instagram"]
               elif "public records" in specific_source_lower or "records" in specific_source_lower:
                   if not search_coordination_results["public_records_sources"]:
                       search_coordination_results["public_records_sources"] = ["government_databases", "court_records", "property_records"]
        
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
         # Using dynamic import to avoid import issues
         import importlib.util
         import os
         tool_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils', 'tools', 'langchain_tools.py')
         spec = importlib.util.spec_from_file_location("langchain_tools", tool_module_path)
         if spec is not None and spec.loader is not None:
            tool_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(tool_module)
            get_global_tool_manager = tool_module.get_global_tool_manager
         else:
            raise ImportError("Could not load scraping tools module")
         tool_manager = get_global_tool_manager()
         
         # Initialize AI backend bridge for state synchronization during collection
         # Using dynamic import to avoid import issues
         import importlib.util
         import os
         bridge_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'utils', 'bridge', 'ai_backend_bridge.py')
         spec = importlib.util.spec_from_file_location("ai_backend_bridge", bridge_module_path)
         if spec is not None and spec.loader is not None:
            bridge_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(bridge_module)
            get_global_ai_bridge = bridge_module.get_global_ai_bridge
         else:
            raise ImportError("Could not load AI backend bridge module")
         
         ai_backend_bridge = await get_global_ai_bridge()
         
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
                "task_type": "search",
                "queries": [state.get("user_request", "general search")],
                "engines": state["search_coordination_results"]["surface_web_sources"],
                "max_results": 5
            }
            surface_result = await surface_web_agent.execute(surface_web_input)
            if surface_result.success:
                search_results["surface_web"] = surface_result.data.get("results", [])
                raw_data["total_records"] += len(surface_result.data.get("results", []))
                state["agents_participated"].append("SurfaceWebCollectorAgent")
                state["confidence_level"] = max(state["confidence_level"], surface_result.confidence)
                
                # Enhanced URL extraction from surface web results and add to sources_used
                extracted_urls = []
                
                # Handle different possible result structures
                result_data = surface_result.data
                
                # Check if there are results at the top level
                if "results" in result_data:
                    all_results = result_data["results"]
                else:
                    all_results = [result_data]  # If single result object, wrap in list
                
                # Process all results to extract URLs
                for result_item in all_results:
                    if isinstance(result_item, dict):
                        # Check for direct URLs in common fields
                        if "url" in result_item and result_item["url"]:
                            extracted_urls.append(result_item["url"])
                        elif "urls" in result_item and isinstance(result_item["urls"], list):
                            extracted_urls.extend(result_item["urls"])
                        elif "links" in result_item and isinstance(result_item["links"], list):
                            for link in result_item["links"]:
                                if isinstance(link, str) and link.startswith("http"):
                                    extracted_urls.append(link)
                                elif isinstance(link, dict) and "url" in link:
                                    extracted_urls.append(link["url"])
                                elif isinstance(link, dict) and "link" in link:
                                    extracted_urls.append(link["link"])
                        
                        # Check for nested search results
                        if "results" in result_item:
                            nested_results = result_item["results"]
                            if isinstance(nested_results, list):
                                for nested_result in nested_results:
                                    if isinstance(nested_result, dict):
                                        # Extract URLs from nested results
                                        if "url" in nested_result and nested_result["url"]:
                                            extracted_urls.append(nested_result["url"])
                                        elif "link" in nested_result and nested_result["link"]:
                                            extracted_urls.append(nested_result["link"])
                                        elif "links" in nested_result and isinstance(nested_result["links"], list):
                                            for link in nested_result["links"]:
                                                if isinstance(link, str) and link.startswith("http"):
                                                    extracted_urls.append(link)
                                                elif isinstance(link, dict) and "url" in link:
                                                    extracted_urls.append(link["url"])
                                
                # Also check for direct sources in the result data
                if "sources" in result_data and isinstance(result_data["sources"], list):
                    extracted_urls.extend(result_data["sources"])
                
                # Check if result data contains source links or references
                if "source_links" in result_data and isinstance(result_data["source_links"], list):
                    extracted_urls.extend(result_data["source_links"])
                if "references" in result_data and isinstance(result_data["references"], list):
                    extracted_urls.extend(result_data["references"])
                if "citations" in result_data and isinstance(result_data["citations"], list):
                    extracted_urls.extend(result_data["citations"])
                
                # Extract URLs from any string content that might contain them
                def extract_urls_from_content(content):
                    if isinstance(content, str):
                        # Simple URL extraction from string content
                        import re
                        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                        found_urls = re.findall(url_pattern, content)
                        return found_urls
                    elif isinstance(content, dict):
                        urls = []
                        for key, value in content.items():
                            if isinstance(value, (str, dict, list)):
                                urls.extend(extract_urls_from_content(value))
                        return urls
                    elif isinstance(content, list):
                        urls = []
                        for item in content:
                            if isinstance(item, (str, dict, list)):
                                urls.extend(extract_urls_from_content(item))
                        return urls
                    return []
                
                # Extract additional URLs from string content in the result data
                extracted_urls.extend(extract_urls_from_content(result_data))
                
                # Add extracted URLs to sources_used (only unique HTTPS URLs)
                for url in extracted_urls:
                    if url and url.startswith("https://") and url not in state["sources_used"]:
                        state["sources_used"].append(url)
                        
                # Also add any HTTP URLs if we don't have enough HTTPS URLs yet
                for url in extracted_urls:
                    if url and url.startswith("http://") and url not in state["sources_used"] and len([u for u in state["sources_used"] if u.startswith("https://")]) < 3:
                        state["sources_used"].append(url)
                
                # Log how many URLs were added
                unique_https_urls = [url for url in extracted_urls if url and url.startswith("https://")]
                unique_http_urls = [url for url in extracted_urls if url and url.startswith("http://")]
                logger.info(f"Extracted {len(unique_https_urls)} unique HTTPS URLs and {len(unique_http_urls)} HTTP URLs from surface web collection")
                logger.info(f"Total sources in state now: {len(state['sources_used'])}")
                
                # Sync with backend after surface web collection
                try:
                    sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
                    if not sync_result.get("success", True):
                        logger.warning(f"Surface web collection state sync failed: {sync_result.get('error')}")
                except Exception as sync_e:
                    logger.warning(f"Could not sync surface web collection state with backend: {str(sync_e)}")
            else:
                state = add_warning(state, f"Surface web collection failed: {surface_result.error_message}")
                logger.warning(f"Surface web collection error: {surface_result.error_message}")

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
                
                # Sync with backend after social media collection
                try:
                    sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
                    if not sync_result.get("success", True):
                        logger.warning(f"Social media collection state sync failed: {sync_result.get('error')}")
                except Exception as sync_e:
                    logger.warning(f"Could not sync social media collection state with backend: {str(sync_e)}")
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
                
                # Sync with backend after public records collection
                try:
                    sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
                    if not sync_result.get("success", True):
                        logger.warning(f"Public records collection state sync failed: {sync_result.get('error')}")
                except Exception as sync_e:
                    logger.warning(f"Could not sync public records collection state with backend: {str(sync_e)}")
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
                
                # Sync with backend after dark web collection
                try:
                    sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
                    if not sync_result.get("success", True):
                        logger.warning(f"Dark web collection state sync failed: {sync_result.get('error')}")
                except Exception as sync_e:
                    logger.warning(f"Could not sync dark web collection state with backend: {str(sync_e)}")
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

         # Final sync with backend after all collection is complete
         try:
            sync_result = await ai_backend_bridge.sync_investigation_state(state['investigation_id'], state)
            if not sync_result.get("success", True):
                logger.warning(f"Final collection state sync failed: {sync_result.get('error')}")
         except Exception as sync_e:
            logger.warning(f"Could not sync final collection state with backend: {str(sync_e)}")

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
           "task_type": "data_fusion",
           "collection_results": state.get("search_results", {}),
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