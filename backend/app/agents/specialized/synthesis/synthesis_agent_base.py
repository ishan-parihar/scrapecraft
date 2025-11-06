"""
Base class for synthesis agents that provides a simpler interface
without the abstract method requirements of the main OSINTAgent class.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ...base.osint_agent import AgentResult, AgentCapability


class SynthesisAgentBase:
    """
    Base class for synthesis agents.
    
    Provides a simpler interface for agents that don't need the full
    LangChain integration of the main OSINTAgent class.
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        version: str = "1.0.0",
        capabilities: Optional[List[AgentCapability]] = None
    ):
        """Initialize the synthesis agent."""
        self.name = name
        self.description = description
        self.version = version
        self.capabilities = capabilities or []
        self.logger = logging.getLogger(f"{__name__}.{name}")
        
        # Agent state
        self.is_active = False
        self.current_task = None
        self.execution_history: List[AgentResult] = []
        
        self.logger.info(f"Initialized {name} agent")
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute the agent's main functionality.
        
        Must be implemented by each synthesis agent.
        """
        raise NotImplementedError("Each synthesis agent must implement the execute method")
    
    def _get_processing_time(self) -> float:
        """Get processing time based on data complexity."""
        # Base processing time adjusted by actual data complexity
        base_time = 1.0
        
        # Adjust based on execution history (more complex data = longer processing)
        if self.execution_history:
            avg_complexity = sum(r.data_complexity for r in self.execution_history) / len(self.execution_history)
            return base_time + (avg_complexity * 2.0)
        
        return base_time
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "agent_name": self.name,
            "is_active": self.is_active,
            "current_task": self.current_task,
            "execution_count": len(self.execution_history),
            "last_execution": self.execution_history[-1].timestamp if self.execution_history else None,
            "success_rate": sum(1 for r in self.execution_history if r.success) / len(self.execution_history) if self.execution_history else 0
        }