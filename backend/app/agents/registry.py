"""
Agent Registry and Lifecycle Management

This module provides centralized agent management, registration, and
lifecycle coordination for the specialized agent architecture.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from app.agents.base.osint_agent import OSINTAgent, AgentConfig, AgentResult


class AgentStatus(Enum):
    """Agent lifecycle status."""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


@dataclass
class AgentRegistration:
    """Agent registration information."""
    agent_class: Type[OSINTAgent]
    agent_id: str
    role: str
    description: str
    capabilities: List[str]
    status: AgentStatus = AgentStatus.INITIALIZING
    instance: Optional[OSINTAgent] = None
    last_health_check: Optional[datetime] = None
    execution_count: int = 0
    error_count: int = 0
    metadata: Optional[Dict[str, Any]] = None


class AgentRegistry:
    """
    Centralized registry for managing specialized agents.
    
    This class handles agent registration, lifecycle management,
    health monitoring, and inter-agent communication coordination.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._agents: Dict[str, AgentRegistration] = {}
        self._agent_roles: Dict[str, str] = {}  # role -> agent_id mapping
        self._health_check_interval = 60  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
    
    async def initialize(self):
        """Initialize the agent registry."""
        self.logger.info("Initializing Agent Registry")
        
        # Register built-in specialized agents
        await self._register_builtin_agents()
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor())
        
        self.logger.info(f"Agent Registry initialized with {len(self._agents)} agents")
    
    async def _register_builtin_agents(self):
        """Register built-in specialized agents."""
        # Import agent classes
        try:
            # Coordination agents
            from app.agents.specialized.coordination.conversational_coordinator import ConversationalCoordinatorAgent
            
            # Collection agents  
            from app.agents.specialized.collection.url_discovery_agent import URLDiscoveryAgent
            from app.agents.specialized.collection.simple_search_agent import SimpleSearchAgent
            # Temporarily disabled due to missing dependencies
            # from app.agents.specialized.collection.surface_web_collector import SurfaceWebCollectorAgent
            # from app.agents.specialized.collection.social_media_collector import SocialMediaCollectorAgent
            # from app.agents.specialized.collection.public_records_collector import PublicRecordsCollectorAgent
            # from app.agents.specialized.collection.dark_web_collector import DarkWebCollectorAgent
            
            # Planning agents
            from app.agents.specialized.planning.objective_definition import ObjectiveDefinitionAgent
            from app.agents.specialized.planning.strategy_formulation import StrategyFormulationAgent
            
            # Analysis agents
            from app.agents.specialized.analysis.contextual_analysis_agent import ContextualAnalysisAgent
            from app.agents.specialized.analysis.data_fusion_agent import DataFusionAgent
            from app.agents.specialized.analysis.pattern_recognition_agent import PatternRecognitionAgent
            
            # Collection agents
            from app.agents.specialized.collection.surface_web_collector import SurfaceWebCollectorAgent
            from app.agents.specialized.collection.social_media_collector import SocialMediaCollectorAgent
            from app.agents.specialized.collection.public_records_collector import PublicRecordsCollectorAgent
            from app.agents.specialized.collection.dark_web_collector import DarkWebCollectorAgent
            
            # Generation agents
            from app.agents.specialized.generation.pipeline_generation_agent import PipelineGenerationAgent
            
            # Synthesis agents - only register the ones that work with OSINTAgent base
            # from .specialized.synthesis.enhanced_intelligence_synthesis_agent_v2 import EnhancedIntelligenceSynthesisAgentV2
            # from .specialized.synthesis.enhanced_report_generation_agent_v2 import EnhancedReportGenerationAgentV2
            # from .specialized.synthesis.quality_assurance_agent_v2 import QualityAssuranceAgentV2
            
            # Register coordination agents
            await self.register_agent(
                ConversationalCoordinatorAgent,
                "conversational_coordinator",
                "Conversational Coordinator",
                "Manages conversation flow and coordinates specialized agents",
                ["intent_analysis", "conversation_management", "context_coordination"]
            )
            
# Register collection agents
            await self.register_agent(
                SimpleSearchAgent,
                "simple_search",
                "Simple Search Specialist",
                "Performs basic multi-engine web searches",
                ["web_search", "multi_engine", "content_discovery", "basic_research"]
            )
            
            await self.register_agent(
                URLDiscoveryAgent,
                "url_discovery",
                "URL Discovery Specialist", 
                "Finds and analyzes relevant URLs for scraping tasks",
                ["url_search", "relevance_analysis", "source_discovery"]
            )
            
            await self.register_agent(
                SurfaceWebCollectorAgent,
                "surface_web_collector",
                "Surface Web Collector",
                "Collects data from surface web sources",
                ["web_scraping", "content_extraction", "surface_data"]
            )
            
            await self.register_agent(
                SocialMediaCollectorAgent,
                "social_media_collector", 
                "Social Media Collector",
                "Collects data from social media platforms",
                ["social_scraping", "profile_analysis", "social_monitoring"]
            )
            
            await self.register_agent(
                PublicRecordsCollectorAgent,
                "public_records_collector",
                "Public Records Collector", 
                "Collects public records and official data",
                ["records_search", "official_data", "public_information"]
            )
            
            await self.register_agent(
                DarkWebCollectorAgent,
                "dark_web_collector",
                "Dark Web Collector",
                "Collects data from dark web sources",
                ["dark_web_monitoring", "anonymous_sources", "hidden_services"]
            )
            
            # Planning agents - temporarily disabled
            # await self.register_agent(
            #     ObjectiveDefinitionAgent,
            #     "objective_definition",
            #     "Objective Definition Specialist",
            #     "Defines and clarifies investigation objectives", 
            #     ["objective_analysis", "kir_definition", "scope_planning"]
            # )
            
            # await self.register_agent(
            #     StrategyFormulationAgent,
            #     "strategy_formulation",
            #     "Strategy Formulation Specialist",
            #     "Formulates investigation strategies and methodologies",
            #     ["strategy_planning", "methodology_design", "resource_allocation"]
            # )
            
            # Analysis agents - temporarily disabled
            # await self.register_agent(
            #     ContextualAnalysisAgent,
            #     "contextual_analysis",
            #     "Contextual Analysis Specialist",
            #     "Provides contextual analysis and situational awareness",
            #     ["context_analysis", "situational_awareness", "environment_assessment"]
            # )
            
            # await self.register_agent(
            #     DataFusionAgent,
            #     "data_fusion",
            #     "Data Fusion Specialist",
            #     "Fuses data from multiple sources and formats",
            #     ["data_integration", "fusion_algorithms", "multi_source_analysis"]
            # )
            
            # await self.register_agent(
            #     PatternRecognitionAgent,
            #     "pattern_recognition",
            #     "Pattern Recognition Specialist",
            #     "Identifies patterns and anomalies in data",
            #     ["pattern_detection", "anomaly_analysis", "trend_identification"]
            # )
            
            # Temporarily disabled due to missing dependencies
            # await self.register_agent(
            #     SurfaceWebCollectorAgent,
            #     "surface_web_collector",
            #     "Surface Web Collector",
            #     "Collects data from surface web sources",
            #     ["web_scraping", "content_extraction", "surface_data"]
            # )
            
            # await self.register_agent(
            #     SocialMediaCollectorAgent,
            #     "social_media_collector", 
            #     "Social Media Collector",
            #     "Collects data from social media platforms",
            #     ["social_scraping", "profile_analysis", "social_monitoring"]
            # )
            
            # await self.register_agent(
            #     PublicRecordsCollectorAgent,
            #     "public_records_collector",
            #     "Public Records Collector", 
            #     "Collects public records and official data",
            #     ["records_search", "official_data", "public_information"]
            # )
            
            # await self.register_agent(
            #     DarkWebCollectorAgent,
            #     "dark_web_collector",
            #     "Dark Web Collector",
            #     "Collects data from dark web sources",
            #     ["dark_web_monitoring", "anonymous_sources", "hidden_services"]
            # )
            
            # Register planning agents
            await self.register_agent(
                ObjectiveDefinitionAgent,
                "objective_definition",
                "Objective Definition Specialist",
                "Defines and clarifies investigation objectives", 
                ["objective_analysis", "kir_definition", "scope_planning"]
            )
            
            await self.register_agent(
                StrategyFormulationAgent,
                "strategy_formulation",
                "Strategy Formulation Specialist",
                "Formulates investigation strategies and methodologies",
                ["strategy_planning", "methodology_design", "resource_allocation"]
            )
            
            # Register analysis agents
            await self.register_agent(
                ContextualAnalysisAgent,
                "contextual_analysis",
                "Contextual Analysis Specialist",
                "Provides contextual analysis and situational awareness",
                ["context_analysis", "situational_awareness", "environment_assessment"]
            )
            
            await self.register_agent(
                DataFusionAgent,
                "data_fusion",
                "Data Fusion Specialist",
                "Fuses data from multiple sources and formats",
                ["data_integration", "fusion_algorithms", "multi_source_analysis"]
            )
            
            await self.register_agent(
                PatternRecognitionAgent,
                "pattern_recognition",
                "Pattern Recognition Specialist",
                "Identifies patterns and anomalies in data",
                ["pattern_detection", "anomaly_analysis", "trend_identification"]
            )
            
            # Register generation agents
            await self.register_agent(
                PipelineGenerationAgent,
                "pipeline_generation",
                "Pipeline Generation Specialist",
                "Generates optimized scraping pipelines and code",
                ["code_generation", "pipeline_optimization", "automation"]
            )
            
            # Register synthesis agents - commented out for now due to base class compatibility
            # await self.register_agent(
            #     EnhancedIntelligenceSynthesisAgentV2,
            #     "intelligence_synthesis",
            #     "Intelligence Synthesis Specialist",
            #     "Synthesizes intelligence from collected data",
            #     ["intelligence_synthesis", "data_integration", "analysis"]
            # )
            
            # await self.register_agent(
            #     EnhancedReportGenerationAgentV2,
            #     "report_generation",
            #     "Report Generation Specialist",
            #     "Generates comprehensive reports and documentation",
            #     ["report_creation", "documentation", "presentation"]
            # )
            
            # await self.register_agent(
            #     QualityAssuranceAgentV2,
            #     "quality_assurance",
            #     "Quality Assurance Specialist",
            #     "Ensures data quality and validates results",
            #     ["quality_control", "validation", "accuracy_assessment"]
            # )
            
        except ImportError as e:
            self.logger.warning(f"Could not import some agent classes: {e}")
            
        # Always ensure basic functionality even if some agents fail
        try:
            # Register a basic search agent as fallback
            from backend.app.services.multi_search_service import MultiSearchEngine
            
            class BasicSearchAgent(OSINTAgent):
                """Basic search agent using multi-search service."""
                
                def __init__(self, config: Optional[AgentConfig] = None):
                    if config is None:
                        config = AgentConfig(
                            role="Basic Search Agent",
                            description="Performs multi-engine web searches",
                            timeout=30
                        )
                    super().__init__(config)
                
                async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
                    """Execute multi-engine search."""
                    query = input_data.get("query", input_data.get("user_request", ""))
                    
                    if not query:
                        return AgentResult(
                            success=False,
                            data={},
                            error_message="No query provided"
                        )
                    
                    try:
                        async with MultiSearchEngine() as search_engine:
                            search_results = await search_engine.search(
                                query=query,
                                max_results=20
                            )
                        
                        return AgentResult(
                            success=True,
                            data=search_results,
                            metadata={
                                "agent_type": "basic_search",
                                "sources_used": search_results.get("engines_used", [])
                            }
                        )
                        
                    except Exception as e:
                        return AgentResult(
                            success=False,
                            data={},
                            error_message=f"Search failed: {str(e)}"
                        )
            
            # Register the basic search agent
            await self.register_agent(
                BasicSearchAgent,
                "basic_search",
                "Basic Search Agent",
                "Performs multi-engine web searches as fallback",
                ["web_search", "multi_engine", "content_discovery"]
            )
            
        except Exception as e:
            self.logger.error(f"Failed to register basic search agent: {e}")
    
    async def register_agent(
        self,
        agent_class: Type[OSINTAgent],
        agent_id: str,
        role: str,
        description: str,
        capabilities: List[str],
        config: Optional[AgentConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Register an agent with the registry.
        
        Args:
            agent_class: The agent class to register
            agent_id: Unique identifier for the agent
            role: Human-readable role name
            description: Description of agent capabilities
            capabilities: List of agent capabilities
            config: Optional agent configuration
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            # Check for existing registration
            if agent_id in self._agents:
                self.logger.warning(f"Agent {agent_id} already registered")
                return False
            
            # Create agent instance
            try:
                if config:
                    instance = agent_class(config=config)
                else:
                    instance = agent_class()
            except TypeError:
                # Agent class requires config parameter
                default_config = AgentConfig(
                    role=role,
                    description=description
                )
                instance = agent_class(config=default_config)
            
            # Create registration
            registration = AgentRegistration(
                agent_class=agent_class,
                agent_id=agent_id,
                role=role,
                description=description,
                capabilities=capabilities,
                status=AgentStatus.ACTIVE,
                instance=instance,
                last_health_check=datetime.utcnow(),
                metadata=metadata or {}
            )
            
            # Register agent
            self._agents[agent_id] = registration
            self._agent_roles[role] = agent_id
            
            self.logger.info(f"Registered agent: {agent_id} ({role})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to register agent {agent_id}: {e}")
            return False
    
    def get_agent(self, agent_id: str) -> Optional[OSINTAgent]:
        """Get agent instance by ID."""
        registration = self._agents.get(agent_id)
        return registration.instance if registration else None
    
    def get_agent_by_role(self, role: str) -> Optional[OSINTAgent]:
        """Get agent instance by role."""
        agent_id = self._agent_roles.get(role)
        return self.get_agent(agent_id) if agent_id else None
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents with their status."""
        agents = []
        for agent_id, registration in self._agents.items():
            agents.append({
                "agent_id": agent_id,
                "role": registration.role,
                "description": registration.description,
                "status": registration.status.value,
                "capabilities": registration.capabilities,
                "execution_count": registration.execution_count,
                "error_count": registration.error_count,
                "last_health_check": registration.last_health_check.isoformat() if registration.last_health_check else None
            })
        return agents
    
    def get_agents_by_capability(self, capability: str) -> List[OSINTAgent]:
        """Get all agents that have a specific capability."""
        agents = []
        for registration in self._agents.values():
            if capability in registration.capabilities and registration.status == AgentStatus.ACTIVE:
                agents.append(registration.instance)
        return agents
    
    async def execute_agent(
        self,
        agent_id: str,
        input_data: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> AgentResult:
        """
        Execute an agent with input data.
        
        Args:
            agent_id: ID of agent to execute
            input_data: Input data for the agent
            timeout: Optional timeout override
            
        Returns:
            Agent execution result
        """
        registration = self._agents.get(agent_id)
        if not registration:
            return AgentResult(
                success=False,
                data={},
                error_message=f"Agent {agent_id} not found"
            )
        
        if registration.status != AgentStatus.ACTIVE:
            return AgentResult(
                success=False,
                data={},
                error_message=f"Agent {agent_id} is not active (status: {registration.status.value})"
            )
        
        try:
            # Update status
            registration.status = AgentStatus.BUSY
            registration.execution_count += 1
            
            # Execute agent
            if registration.instance:
                if timeout:
                    original_timeout = registration.instance.config.timeout
                    registration.instance.config.timeout = timeout
                    result = await registration.instance.execute(input_data)
                    registration.instance.config.timeout = original_timeout
                else:
                    result = await registration.instance.execute(input_data)
            else:
                result = AgentResult(
                    success=False,
                    data={},
                    error_message=f"Agent {agent_id} instance not available"
                )
            
            # Update status based on result
            if result.success:
                registration.status = AgentStatus.ACTIVE
            else:
                registration.status = AgentStatus.ERROR
                registration.error_count += 1
            
            return result
            
        except Exception as e:
            registration.status = AgentStatus.ERROR
            registration.error_count += 1
            self.logger.error(f"Agent {agent_id} execution failed: {e}")
            
            return AgentResult(
                success=False,
                data={},
                error_message=f"Agent execution failed: {str(e)}"
            )
    
    async def coordinate_agents(
        self,
        workflow: List[Dict[str, Any]],
        global_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate multiple agents in a workflow.
        
        Args:
            workflow: List of agent execution steps
            global_context: Shared context across agents
            
        Returns:
            Workflow execution results
        """
        results = {}
        context = global_context or {}
        
        for step in workflow:
            agent_id = step.get("agent_id")
            step_input = step.get("input", {})
            
            # Merge with global context
            step_input.update(context)
            
            # Execute agent
            if agent_id:
                result = await self.execute_agent(agent_id, step_input)
            else:
                result = AgentResult(
                    success=False,
                    data={},
                    error_message="Agent ID not provided in workflow step"
                )
            results[agent_id] = result
            
            # Update context with agent output
            if result.success:
                context.update(result.data)
            
            # Stop workflow on failure
            if not result.success and step.get("required", True):
                self.logger.error(f"Workflow stopped at step {agent_id}: {result.error_message}")
                break
        
        return {
            "results": results,
            "final_context": context,
            "success": all(r.success for r in results.values())
        }
    
    async def _health_monitor(self):
        """Monitor agent health and status."""
        while not self._shutdown_event.is_set():
            try:
                for agent_id, registration in self._agents.items():
                    if registration.status == AgentStatus.ACTIVE:
                        # Perform health check
                        try:
                            # Simple health check - can be enhanced
                            if registration.instance and hasattr(registration.instance, 'get_status'):
                                status = registration.instance.get_status()
                                if registration.metadata:
                                    registration.metadata["status"] = status
                            
                            registration.last_health_check = datetime.utcnow()
                            
                        except Exception as e:
                            self.logger.warning(f"Health check failed for {agent_id}: {e}")
                            registration.status = AgentStatus.ERROR
                            registration.error_count += 1
                
                # Wait for next check
                await asyncio.sleep(self._health_check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(10)  # Brief pause on error
    
    async def shutdown(self):
        """Shutdown the agent registry."""
        self.logger.info("Shutting down Agent Registry")
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel health monitor
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        # Shutdown all agents
        for agent_id, registration in self._agents.items():
            try:
                if registration.instance and hasattr(registration.instance, 'cleanup'):
                    await registration.instance.cleanup()
                registration.status = AgentStatus.SHUTDOWN
            except Exception as e:
                self.logger.warning(f"Error shutting down agent {agent_id}: {e}")
        
        self.logger.info("Agent Registry shutdown complete")
    
    def get_registry_status(self) -> Dict[str, Any]:
        """Get overall registry status."""
        active_agents = sum(1 for r in self._agents.values() if r.status == AgentStatus.ACTIVE)
        total_executions = sum(r.execution_count for r in self._agents.values())
        total_errors = sum(r.error_count for r in self._agents.values())
        
        return {
            "total_agents": len(self._agents),
            "active_agents": active_agents,
            "total_executions": total_executions,
            "total_errors": total_errors,
            "health_monitor_running": self._health_check_task and not self._health_check_task.done(),
            "last_health_check": max(
                (r.last_health_check for r in self._agents.values() if r.last_health_check),
                default=None
            )
        }


# Global registry instance
agent_registry = AgentRegistry()