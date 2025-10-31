"""
Base OSINT Agent Class

This module contains the foundational OSINTAgent class that all specialized
OSINT agents will inherit from.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import asyncio
import uuid
import json
import logging

from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for OSINT agents"""
    agent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    description: str
    max_iterations: int = 10
    verbose: bool = True
    timeout: int = 300
    retry_attempts: int = 3


class AgentResult(BaseModel):
    """Standardized result format for agent operations"""
    success: bool
    data: Dict[str, Any]
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)
    sources: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None
    execution_time: float = 0.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentCapability(BaseModel):
    """Capability definition for OSINT agents"""
    name: str
    description: str
    required_data: List[str] = Field(default_factory=list)
    output_data: List[str] = Field(default_factory=list)
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class OSINTAgent(ABC):
    """
    Base class for all OSINT agents.
    
    Provides common functionality for agent lifecycle management,
    communication, and execution.
    """
    
    def __init__(
        self,
        config: AgentConfig,
        tools: List[Any] = None,
        memory: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.config = config
        self.tools = tools or []
        self.memory = memory
        self.logger = logger or logging.getLogger(f"{__name__}.{config.role}")
        
        # Agent state
        self.is_active = False
        self.current_task = None
        self.execution_history: List[AgentResult] = []
        
        self.logger.info(f"Initialized {self.config.role} agent with ID: {self.config.agent_id}")
    
    @abstractmethod
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        
        Must be implemented by each specialized agent.
        """
        pass
    
    @abstractmethod
    def _process_output(self, raw_output: str, intermediate_steps: List = None) -> Dict[str, Any]:
        """
        Process and structure the raw output from the agent.
        
        Must be implemented by each specialized agent to convert
        raw text into structured data.
        """
        pass
    
    @abstractmethod
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        
        Must be implemented by each specialized agent.
        """
        pass
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute agent task with error handling and logging.
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate input
            if not self.validate_input(input_data):
                return AgentResult(
                    success=False,
                    data={},
                    error_message="Input validation failed",
                    execution_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            self.is_active = True
            self.current_task = input_data
            
            self.logger.info(f"Starting execution for {self.config.role} agent")
            
            # Execute the agent
            result = await asyncio.wait_for(
                self._execute_with_retry(input_data),
                timeout=self.config.timeout
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create standardized result
            agent_result = AgentResult(
                success=True,
                data=result,
                confidence=self._calculate_confidence(result, input_data),
                sources=self._extract_sources(result),
                metadata={
                    "agent_id": self.config.agent_id,
                    "agent_role": self.config.role,
                    "intermediate_steps": len(self.memory.chat_memory.messages) if self.memory else 0
                },
                execution_time=execution_time
            )
            
            self.execution_history.append(agent_result)
            self.logger.info(f"Successfully completed execution in {execution_time:.2f}s")
            
            return agent_result
            
        except asyncio.TimeoutError:
            error_msg = f"Execution timed out after {self.config.timeout} seconds"
            self.logger.error(error_msg)
            return AgentResult(
                success=False,
                data={},
                error_message=error_msg,
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
        except Exception as e:
            error_msg = f"Execution failed: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return AgentResult(
                success=False,
                data={},
                error_message=error_msg,
                execution_time=(datetime.utcnow() - start_time).total_seconds()
            )
            
        finally:
            self.is_active = False
            self.current_task = None
    
    async def _execute_with_retry(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute with retry logic for transient failures.
        """
        last_exception = None
        
        for attempt in range(self.config.retry_attempts):
            try:
                # Simulate agent execution (replace with actual LLM call)
                result = await self._simulate_agent_execution(input_data)
                
                # Process the output
                structured_result = self._process_output(result, [])
                
                return structured_result
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                
                if attempt < self.config.retry_attempts - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise last_exception
    
    async def _simulate_agent_execution(self, input_data: Dict[str, Any]) -> str:
        """
        Simulate agent execution with LLM.
        In a real implementation, this would call an actual LLM.
        """
        # For now, return a mock response based on the agent type
        if "objective" in self.config.role.lower():
            return json.dumps({
                "primary_objectives": ["Analyze provided request"],
                "secondary_objectives": ["Extract key requirements"],
                "key_intelligence_requirements": ["Information relevant to investigation"],
                "success_criteria": ["Clear objectives defined"],
                "constraints": ["Legal and ethical boundaries"],
                "ethical_considerations": ["Maintain privacy compliance"],
                "investigation_scope": {
                    "in_scope": ["Publicly available information"],
                    "out_of_scope": ["Private data"]
                },
                "urgency_level": "medium",
                "estimated_complexity": "medium"
            })
        else:
            return f"Processed input: {input_data} with {self.config.role}"
    
    def _calculate_confidence(self, result: Dict[str, Any], input_data: Dict[str, Any]) -> float:
        """
        Calculate confidence score for the result.
        
        Base implementation - can be overridden by specialized agents.
        """
        # Simple confidence calculation based on result completeness
        required_fields = self._get_required_output_fields()
        if not required_fields:
            return 0.8  # Default confidence
        
        present_fields = sum(1 for field in required_fields if field in result and result[field])
        return present_fields / len(required_fields)
    
    def _extract_sources(self, result: Dict[str, Any]) -> List[str]:
        """
        Extract source information from the result.
        
        Base implementation - can be overridden by specialized agents.
        """
        sources = []
        
        # Look for common source fields
        for source_field in ['sources', 'references', 'citations', 'urls']:
            if source_field in result:
                if isinstance(result[source_field], list):
                    sources.extend(result[source_field])
                elif isinstance(result[source_field], str):
                    sources.append(result[source_field])
        
        return list(set(sources))  # Remove duplicates
    
    def _get_required_output_fields(self) -> List[str]:
        """
        Get list of required output fields for this agent.
        
        Base implementation - can be overridden by specialized agents.
        """
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status.
        """
        return {
            "agent_id": self.config.agent_id,
            "role": self.config.role,
            "is_active": self.is_active,
            "current_task": self.current_task,
            "execution_count": len(self.execution_history),
            "last_execution": self.execution_history[-1].timestamp if self.execution_history else None,
            "average_execution_time": sum(r.execution_time for r in self.execution_history) / len(self.execution_history) if self.execution_history else 0,
            "success_rate": sum(1 for r in self.execution_history if r.success) / len(self.execution_history) if self.execution_history else 0
        }
    
    def reset_memory(self):
        """Clear the agent's memory"""
        if self.memory:
            self.memory.clear()
        self.logger.info(f"Memory cleared for {self.config.role} agent")
    
    def get_execution_history(self, limit: int = 10) -> List[AgentResult]:
        """Get recent execution history"""
        return self.execution_history[-limit:] if self.execution_history else []