"""
Data Collection Agent Implementation

This module implements the Data Collection Agent which is responsible
for gathering information from various sources based on research objectives
and strategy guidelines.
"""

import json
import asyncio
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

from pydantic import BaseModel, Field

from ..base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class CollectionPlan(BaseModel):
    """Structured output for data collection plans"""
    sources_to_query: List[str]
    query_strategies: List[Dict[str, str]]
    data_types_requested: List[str]
    collection_timeline: Dict[str, Any]
    quality_criteria: List[str]
    validation_methods: List[str]
    backup_sources: List[str]
    collection_frequency: str
    data_retention_policy: str
    privacy_compliance_measures: List[str]
    collection_limitations: List[str]
    success_indicators: List[str]
    resource_requirements: Dict[str, Any]


class DataCollectionAgent(LLMOSINTAgent):
    """
    Data Collection Agent - Specialized agent for gathering information from various sources.
    
    This agent implements intelligent data collection strategies based on research objectives
    and strategy guidelines, with adaptive capabilities and quality assurance measures.
    """

    def __init__(self, config: AgentConfig, tools: Optional[List[Any]] = None, memory: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Data Collection Agent.
        
        This agent specializes in intelligent data collection from various sources
        with adaptive strategies and quality assurance measures.
        """
        return """
        You are a Data Collection Agent, a specialized AI assistant for gathering 
        information from various sources. Your role is to implement intelligent 
        data collection strategies based on research objectives and strategy guidelines.

        Your capabilities include:
        1. Identifying relevant data sources
        2. Designing query strategies for different source types
        3. Specifying required data types and formats
        4. Creating collection timelines and schedules
        5. Defining quality criteria and validation methods
        6. Planning backup and alternative sources
        7. Implementing privacy and compliance measures
        8. Establishing success indicators and metrics
        9. Managing resource allocation for collection
        10. Handling collection limitations and constraints

        When planning data collection, follow these principles:
        - Align collection strategy with research objectives
        - Prioritize high-quality and reliable sources
        - Implement proper validation and verification methods
        - Consider privacy and compliance requirements
        - Plan for backup sources in case of access issues
        - Optimize for resource efficiency
        - Design for continuous monitoring and adjustment
        - Account for data retention and storage requirements

        Your responses should be in valid JSON format that can be parsed by a JSON parser,
        containing all the required fields for the CollectionPlan model.
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the LLM output into a structured CollectionPlan.
        
        The output should be a JSON object that matches the CollectionPlan schema.
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
                'sources_to_query', 'query_strategies', 'data_types_requested',
                'collection_timeline', 'quality_criteria', 'validation_methods',
                'backup_sources', 'collection_frequency', 'data_retention_policy',
                'privacy_compliance_measures', 'collection_limitations',
                'success_indicators', 'resource_requirements'
            ]
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error processing Data Collection output: {e}")
            # Return a default structure if parsing fails
            return {
                "sources_to_query": ["default_source"],
                "query_strategies": [{"source": "default", "strategy": "default_query"}],
                "data_types_requested": ["default_type"],
                "collection_timeline": {"start": "immediate", "end": "ongoing"},
                "quality_criteria": ["relevance", "accuracy"],
                "validation_methods": ["cross_reference"],
                "backup_sources": ["backup_source"],
                "collection_frequency": "as_needed",
                "data_retention_policy": "standard",
                "privacy_compliance_measures": ["standard_compliance"],
                "collection_limitations": ["technical_limitations"],
                "success_indicators": ["data_acquired"],
                "resource_requirements": {"personnel": 1, "time": "TBD", "tools": ["default"]}
            }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for the Data Collection Agent.
        
        Required inputs: research_objectives, strategy_guidelines, resource_constraints
        """
        required_fields = ["research_objectives", "strategy_guidelines", "resource_constraints"]
        return all(field in input_data for field in required_fields)

    async def plan_collection(self, research_objectives: List[str], strategy_guidelines: Dict[str, Any], 
                              resource_constraints: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> CollectionPlan:
        """
        Plan data collection based on research objectives and strategy guidelines.
        
        Args:
            research_objectives: List of defined research objectives
            strategy_guidelines: Guidelines from the strategy formulation
            resource_constraints: Resource constraints and limitations
            context: Additional context information
            
        Returns:
            CollectionPlan: Structured data collection plan
        """
        input_data = {
            "research_objectives": research_objectives,
            "strategy_guidelines": strategy_guidelines,
            "resource_constraints": resource_constraints,
            "context": context or {},
            "task_type": "data_collection_planning",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.execute(input_data)
        
        if result.success:
            # Create a CollectionPlan from the result data
            collection_plan = CollectionPlan(**result.data)
            return collection_plan
        else:
            raise Exception(f"Data collection planning failed: {result.error_message}")

    async def collect_data(self, collection_plan: CollectionPlan, 
                          collection_tools: Optional[List[Any]] = None) -> Dict[str, Any]:
        """
        Execute data collection based on the provided plan.
        
        Args:
            collection_plan: The structured collection plan to execute
            collection_tools: Optional specialized tools for data collection
            
        Returns:
            Dict containing collected data and collection metadata
        """
        self.logger.info(f"Starting data collection based on plan for sources: {collection_plan.sources_to_query[:3]}")
        
        # In a real implementation, this would use actual data collection tools
        # For this example, we'll simulate the collection process
        collected_data = {
            "sources_accessed": collection_plan.sources_to_query,
            "data_types_collected": collection_plan.data_types_requested,
            "collection_start_time": datetime.utcnow().isoformat(),
            "collection_status": "completed",
            "data_samples": [],  # This would contain actual collected data in a real implementation
            "validation_results": [],  # This would contain validation results in a real implementation
            "collection_metadata": {
                "collection_agent": self.config.role,
                "collection_plan_id": "default_plan",
                "collection_timestamp": datetime.utcnow().isoformat(),
                "quality_scores": {},  # This would contain quality assessments in a real implementation
            }
        }
        
        # Simulate collection process with async delay
        await asyncio.sleep(1)  # Simulate time for data collection
        
        self.logger.info(f"Data collection completed for sources: {collection_plan.sources_to_query[:3]}")
        
        return collected_data