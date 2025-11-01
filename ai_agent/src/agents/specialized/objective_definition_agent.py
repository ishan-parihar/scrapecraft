"""
Objective Definition Agent Implementation

This module implements the Objective Definition Agent which is responsible
for analyzing research requirements and defining clear, measurable objectives
for the AI-driven research system.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

from pydantic import BaseModel, Field

from ..base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class ObjectiveDefinition(BaseModel):
    """Structured output for objective definitions"""
    primary_objective: str
    secondary_objectives: List[str]
    success_criteria: List[str]
    key_performance_indicators: List[str]
    timeline_estimates: Dict[str, str]
    resource_requirements: List[str]
    potential_roadblocks: List[str]
    objective_priority: str  # high, medium, low
    objective_complexity: str  # simple, moderate, complex
    dependencies: List[str]
    measurable_outcomes: List[str]


class ObjectiveDefinitionAgent(LLMOSINTAgent):
    """
    Objective Definition Agent - Specialized agent for defining clear research objectives.
    
    This agent analyzes research requirements and creates well-defined, measurable objectives
    that guide the entire research process.
    """

    def __init__(self, config: AgentConfig, tools: Optional[List[Any]] = None, memory: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Objective Definition Agent.
        
        This agent specializes in creating clear, measurable, and achievable research objectives
        with defined success criteria and resource requirements.
        """
        return """
        You are an Objective Definition Agent, a specialized AI assistant for creating 
        clear, measurable, and achievable research objectives. Your role is to analyze 
        research requirements and define specific objectives with success criteria, 
        resource needs, and measurable outcomes.

        Your capabilities include:
        1. Analyzing research topics and requirements
        2. Defining primary and secondary objectives
        3. Establishing success criteria and KPIs
        4. Estimating timelines and resource requirements
        5. Identifying potential roadblocks
        6. Determining objective priorities and dependencies
        7. Creating measurable outcomes

        When defining objectives, follow these principles:
        - Objectives must be Specific, Measurable, Achievable, Relevant, and Time-bound (SMART)
        - Consider the research scope and available resources
        - Identify dependencies between objectives
        - Estimate realistic timelines for each objective
        - Define clear success criteria that can be objectively measured
        - Identify potential challenges that may impede objective achievement

        Your responses should be in valid JSON format that can be parsed by a JSON parser,
        containing all the required fields for the ObjectiveDefinition model.
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the LLM output into a structured ObjectiveDefinition.
        
        The output should be a JSON object that matches the ObjectiveDefinition schema.
        """
        try:
            # Try to extract JSON from the response if it's wrapped in markdown
            if "```json" in raw_output:
                start = raw_output.find("```json") + len("```json")
                end = raw_output.find("```", start)
                json_str = raw_output[start:end].strip()
            elif raw_output.strip().startswith("{") and raw_output.strip().endswith("}"):
                json_str = raw_output.strip()
            else:
                # Find the first { and the last } to extract JSON
                start = raw_output.find("{")
                end = raw_output.rfind("}") + 1
                if start != -1 and end != -1:
                    json_str = raw_output[start:end].strip()
                else:
                    raise ValueError("No JSON object found in the response")

            data = json.loads(json_str)
            
            # Validate that the required fields are present
            required_fields = [
                'primary_objective', 'secondary_objectives', 'success_criteria',
                'key_performance_indicators', 'timeline_estimates', 'resource_requirements',
                'potential_roadblocks', 'objective_priority', 'objective_complexity',
                'dependencies', 'measurable_outcomes'
            ]
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error processing Objective Definition output: {e}")
            # Return a default structure if parsing fails
            return {
                "primary_objective": "Default primary objective",
                "secondary_objectives": ["Default secondary objective"],
                "success_criteria": ["Default success criterion"],
                "key_performance_indicators": ["Default KPI"],
                "timeline_estimates": {"default": "TBD"},
                "resource_requirements": ["Default resources"],
                "potential_roadblocks": ["Potential roadblock"],
                "objective_priority": "medium",
                "objective_complexity": "moderate",
                "dependencies": [],
                "measurable_outcomes": ["Default outcome"]
            }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for the Objective Definition Agent.
        
        Required inputs: research_topic, research_scope, initial_requirements
        """
        required_fields = ["research_topic", "research_scope", "initial_requirements"]
        return all(field in input_data for field in required_fields)

    async def define_objectives(self, research_topic: str, research_scope: str, 
                                initial_requirements: List[str], context: Optional[Dict[str, Any]] = None) -> ObjectiveDefinition:
        """
        Define clear research objectives based on the provided information.
        
        Args:
            research_topic: The main topic of the research
            research_scope: Scope and constraints of the research
            initial_requirements: Initial requirements for the research
            context: Additional context information
            
        Returns:
            ObjectiveDefinition: Structured objective definitions
        """
        input_data = {
            "research_topic": research_topic,
            "research_scope": research_scope,
            "initial_requirements": initial_requirements,
            "context": context or {},
            "task_type": "objective_definition",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.execute(input_data)
        
        if result.success:
            # Create an ObjectiveDefinition from the result data
            objective_def = ObjectiveDefinition(**result.data)
            return objective_def
        else:
            raise Exception(f"Objective definition failed: {result.error_message}")