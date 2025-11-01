"""
Strategy Formulation Agent Implementation

This module implements the Strategy Formulation Agent which is responsible
for creating comprehensive research strategies based on defined objectives
and available resources.
"""

import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

from pydantic import BaseModel, Field

from ..base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class ResearchStrategy(BaseModel):
    """Structured output for research strategies"""
    strategy_name: str
    strategy_description: str
    approach_methodology: str
    resource_allocation: Dict[str, Any]
    phase_timeline: List[Dict[str, Any]]
    success_metrics: List[str]
    risk_mitigation_plan: List[str]
    adaptive_capabilities: List[str]
    tool_requirements: List[str]
    quality_assurance_measures: List[str]
    validation_approach: str
    stakeholder_involvement: List[str]
    communication_plan: str
    contingency_strategies: List[str]


class StrategyFormulationAgent(LLMOSINTAgent):
    """
    Strategy Formulation Agent - Specialized agent for creating comprehensive research strategies.
    
    This agent creates detailed research strategies based on objectives, available resources,
    and project requirements.
    """

    def __init__(self, config: AgentConfig, tools: Optional[List[Any]] = None, memory: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Strategy Formulation Agent.
        
        This agent specializes in creating comprehensive research strategies that are
        adaptive, resource-efficient, and aligned with defined objectives.
        """
        return """
        You are a Strategy Formulation Agent, a specialized AI assistant for creating 
        comprehensive research strategies. Your role is to design detailed research 
        approaches that are adaptive, resource-efficient, and aligned with defined 
        objectives.

        Your capabilities include:
        1. Designing research methodologies and approaches
        2. Allocating resources effectively
        3. Creating phased timelines with milestones
        4. Defining success metrics and KPIs
        5. Developing risk mitigation plans
        6. Incorporating adaptive capabilities
        7. Identifying tool and technology requirements
        8. Planning quality assurance measures
        9. Creating validation approaches
        10. Developing stakeholder engagement plans

        When formulating strategies, follow these principles:
        - Align strategy with defined objectives and success criteria
        - Consider resource constraints and optimize allocation
        - Build in adaptive capabilities to respond to new information
        - Include comprehensive risk assessment and mitigation
        - Plan for quality assurance and validation
        - Design for continuous monitoring and adjustment
        - Account for stakeholder needs and communication requirements

        Your responses should be in valid JSON format that can be parsed by a JSON parser,
        containing all the required fields for the ResearchStrategy model.
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the LLM output into a structured ResearchStrategy.
        
        The output should be a JSON object that matches the ResearchStrategy schema.
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
                'strategy_name', 'strategy_description', 'approach_methodology',
                'resource_allocation', 'phase_timeline', 'success_metrics',
                'risk_mitigation_plan', 'adaptive_capabilities', 'tool_requirements',
                'quality_assurance_measures', 'validation_approach',
                'stakeholder_involvement', 'communication_plan', 'contingency_strategies'
            ]
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error processing Strategy Formulation output: {e}")
            # Return a default structure if parsing fails
            return {
                "strategy_name": "Default Strategy",
                "strategy_description": "Default strategy description",
                "approach_methodology": "Standard research methodology",
                "resource_allocation": {"personnel": 1, "time": "TBD", "budget": "TBD"},
                "phase_timeline": [{"phase": "initial", "duration": "TBD", "milestones": ["start"]}],
                "success_metrics": ["Default metric"],
                "risk_mitigation_plan": ["Default risk mitigation"],
                "adaptive_capabilities": ["Basic adaptation"],
                "tool_requirements": ["Standard tools"],
                "quality_assurance_measures": ["Standard QA"],
                "validation_approach": "Standard validation",
                "stakeholder_involvement": ["Default stakeholder"],
                "communication_plan": "Standard communication",
                "contingency_strategies": ["Default contingency"]
            }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for the Strategy Formulation Agent.
        
        Required inputs: objectives, resources, constraints
        """
        required_fields = ["objectives", "resources", "constraints"]
        return all(field in input_data for field in required_fields)

    async def formulate_strategy(self, objectives: List[str], resources: Dict[str, Any], 
                                 constraints: List[str], context: Optional[Dict[str, Any]] = None) -> ResearchStrategy:
        """
        Formulate a comprehensive research strategy based on objectives and resources.
        
        Args:
            objectives: List of defined research objectives
            resources: Available resources for the research
            constraints: Constraints and limitations for the research
            context: Additional context information
            
        Returns:
            ResearchStrategy: Structured research strategy
        """
        input_data = {
            "objectives": objectives,
            "resources": resources,
            "constraints": constraints,
            "context": context or {},
            "task_type": "strategy_formulation",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.execute(input_data)
        
        if result.success:
            # Create a ResearchStrategy from the result data
            strategy = ResearchStrategy(**result.data)
            return strategy
        else:
            raise Exception(f"Strategy formulation failed: {result.error_message}")