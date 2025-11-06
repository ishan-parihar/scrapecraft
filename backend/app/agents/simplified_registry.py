"""
Simplified Agent Registry for Phase 2.1 Testing

This module provides a basic registry for the core specialized agents
that are working correctly.
"""

import logging
from typing import Dict, List, Optional, Any, Type
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass

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


class SimplifiedAgentRegistry:
    """
    Simplified registry for managing core specialized agents.
    
    This class handles agent registration, lifecycle management,
    and basic coordination for the agents that are working correctly.
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
        self.logger.info("Initializing Simplified Agent Registry")
        
        # Register core working agents
        await self._register_core_agents()
        
        # Start health monitoring
        self._health_check_task = asyncio.create_task(self._health_monitor())
        
        self.logger.info(f"Simplified Agent Registry initialized with {len(self._agents)} agents")
    
    async def _register_core_agents(self):
        """Register core working agents."""
        try:
            # Coordination agents
            from app.agents.specialized.coordination.conversational_coordinator import ConversationalCoordinatorAgent
            
            # Collection agents  
            from app.agents.specialized.collection.url_discovery_agent import URLDiscoveryAgent
            
            # Generation agents
            from app.agents.specialized.generation.pipeline_generation_agent import PipelineGenerationAgent
            
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
                URLDiscoveryAgent,
                "url_discovery",
                "URL Discovery Specialist", 
                "Finds and analyzes relevant URLs for scraping tasks",
                ["url_search", "relevance_analysis", "source_discovery"]
            )
            
            # Register generation agents
            await self.register_agent(
                PipelineGenerationAgent,
                "pipeline_generation",
                "Pipeline Generation Specialist",
                "Generates optimized scraping pipelines and code",
                ["code_generation", "pipeline_optimization", "automation"]
            )
            
        except ImportError as e:
            self.logger.warning(f"Could not import some agent classes: {e}")
    
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
            metadata: Optional metadata
            
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
        self.logger.info("Shutting down Simplified Agent Registry")
        
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
        
        self.logger.info("Simplified Agent Registry shutdown complete")
    
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
simplified_agent_registry = SimplifiedAgentRegistry()