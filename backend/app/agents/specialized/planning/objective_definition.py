"""
Objective Definition Agent

This agent is responsible for clarifying and structuring investigation objectives,
identifying Key Intelligence Requirements (KIRs), and defining success criteria.
"""

import json
import re
from typing import Dict, Any, List, Optional
import logging

# Placeholder imports until dependencies are available
# from langchain.agents import AgentExecutor, load_tools
# from langchain.llms import OpenAI
# from langchain.prompts import PromptTemplate

from ..base.osint_agent import OSINTAgent, LLMOSINTAgent, AgentConfig, AgentResult


class ObjectiveDefinitionAgent(LLMOSINTAgent):
    """
    Agent responsible for defining and clarifying investigation objectives.
    
    This agent parses user requirements, identifies Key Intelligence Requirements (KIRs),
    defines investigation scope and constraints, and establishes success criteria.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                role="Objective Definition Specialist",
                description="Clarifies and structures OSINT investigation objectives",
                max_iterations=5,
                timeout=180
            )
        
        # Initialize with basic tools (will be expanded with LangChain tools)
        tools = []
        
        super().__init__(config=config, tools=tools, **kwargs)
        
        # Objective definition specific attributes
        self.objective_patterns = {
            "investigation_types": [
                "background check", "due diligence", "threat assessment", 
                "competitive intelligence", "security audit", "compliance check"
            ],
            "entity_types": [
                "person", "company", "organization", "product", "service", 
                "location", "event", "concept"
            ],
            "information_types": [
                "financial", "legal", "reputation", "technical", "operational",
                "strategic", "personal", "professional"
            ]
        }
    
    def _create_agent(self):
        """
        Create the LangChain agent for objective definition.
        
        Placeholder implementation - will be implemented with LangChain.
        """
        # This will be implemented when LangChain dependencies are available
        # For now, return a mock agent
        return self
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for objective definition"""
        return """
        You are an Objective Definition Specialist for OSINT investigations.
        
        Your role is to:
        1. Parse and clarify user requirements
        2. Identify Key Intelligence Requirements (KIRs)
        3. Define investigation scope and constraints
        4. Establish success criteria
        5. Identify legal/ethical boundaries
        
        Analyze the user's request and provide:
        - Primary objectives (main goals)
        - Secondary objectives (supporting goals)
        - Key Intelligence Requirements (specific information needed)
        - Success metrics (how to measure completion)
        - Constraints and limitations (what cannot be done)
        - Ethical considerations (legal/moral boundaries)
        - Investigation scope (what is in/out of scope)
        
        Always structure your response as valid JSON with the following format:
        {
            "primary_objectives": ["objective1", "objective2"],
            "secondary_objectives": ["objective1", "objective2"],
            "key_intelligence_requirements": ["KIR1", "KIR2"],
            "success_criteria": ["criteria1", "criteria2"],
            "constraints": ["constraint1", "constraint2"],
            "ethical_considerations": ["consideration1", "consideration2"],
            "investigation_scope": {
                "in_scope": ["item1", "item2"],
                "out_of_scope": ["item1", "item2"]
            },
            "target_entities": ["entity1", "entity2"],
            "information_types": ["type1", "type2"],
            "urgency_level": "low|medium|high|critical",
            "estimated_complexity": "low|medium|high"
        }
        """
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the raw output from the agent into structured data.
        """
        try:
            # Check if this is a fallback response from _execute_local_fallback
            if "[This response was generated using local analysis" in raw_output:
                # This is a fallback response, generate proper structured objectives
                return self._generate_fallback_objectives()
            
            # Clean the raw output - remove markdown formatting, extra whitespace, etc.
            cleaned_output = self._clean_raw_output(raw_output)
            
            # Try to parse JSON output
            if cleaned_output.strip().startswith('{'):
                structured_data = json.loads(cleaned_output)
            else:
                # Extract JSON from text if embedded
                json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback: parse text manually
                    structured_data = self._parse_text_output(cleaned_output)
            
            # Validate and enhance the structured data
            return self._validate_and_enhance_objectives(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing output: {e}")
            return self._generate_fallback_objectives()
    
    def _clean_raw_output(self, raw_output: str) -> str:
        """Clean raw output to extract valid JSON."""
        cleaned = raw_output.strip()
        
        # Remove markdown code block formatting
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]   # Remove ```
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]  # Remove trailing ```
        
        # Remove any leading/trailing text that might be around the JSON
        # Find the first { and last }
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace+1]
        
        return cleaned
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for objective definition"""
        required_fields = ["user_request"]
        
        for field in required_fields:
            if field not in input_data or not input_data[field]:
                self.logger.error(f"Missing required field: {field}")
                return False
        
        # Check if user request is meaningful
        user_request = input_data.get("user_request", "").strip()
        if len(user_request) < 10:
            self.logger.error("User request too short")
            return False
        
        return True
    
    def _validate_and_enhance_objectives(self, objectives: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the objectives data"""
        enhanced = objectives.copy()
        
        # Ensure required fields exist
        required_fields = [
            "primary_objectives", "secondary_objectives", "key_intelligence_requirements",
            "success_criteria", "constraints", "ethical_considerations", "investigation_scope"
        ]
        
        for field in required_fields:
            if field not in enhanced:
                enhanced[field] = [] if field != "investigation_scope" else {"in_scope": [], "out_of_scope": []}
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "processing_timestamp": "2024-01-01T00:00:00Z",  # Will be dynamic
            "confidence_score": self._calculate_objective_confidence(enhanced),
            "complexity_score": self._calculate_complexity_score(enhanced)
        }
        
        return enhanced
    
    def _parse_text_output(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text output into structured data"""
        # This is a fallback parser for when JSON parsing fails
        objectives = {
            "primary_objectives": [],
            "secondary_objectives": [],
            "key_intelligence_requirements": [],
            "success_criteria": [],
            "constraints": [],
            "ethical_considerations": [],
            "investigation_scope": {"in_scope": [], "out_of_scope": []},
            "target_entities": [],
            "information_types": [],
            "urgency_level": "medium",
            "estimated_complexity": "medium"
        }
        
        # Simple text parsing logic
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections
            if any(keyword in line.lower() for keyword in ["primary objective", "main goal"]):
                current_section = "primary_objectives"
            elif any(keyword in line.lower() for keyword in ["secondary objective", "supporting goal"]):
                current_section = "secondary_objectives"
            elif "kir" in line.lower() or "key intelligence" in line.lower():
                current_section = "key_intelligence_requirements"
            elif "success" in line.lower() or "criteria" in line.lower():
                current_section = "success_criteria"
            elif "constraint" in line.lower() or "limitation" in line.lower():
                current_section = "constraints"
            elif "ethical" in line.lower() or "legal" in line.lower():
                current_section = "ethical_considerations"
            elif current_section and line.startswith(('-', '•', '*')):
                # Add item to current section
                item = line.lstrip('-•* ').strip()
                if current_section in objectives:
                    if isinstance(objectives[current_section], list):
                        objectives[current_section].append(item)
        
        return objectives
    
    def _generate_fallback_objectives(self) -> Dict[str, Any]:
        """Generate basic objectives when parsing fails"""
        return {
            "primary_objectives": ["Conduct investigation based on user request"],
            "secondary_objectives": ["Gather relevant information", "Ensure data quality"],
            "key_intelligence_requirements": ["Information related to investigation target"],
            "success_criteria": ["Investigation completed", "Relevant information collected"],
            "constraints": ["Legal and ethical boundaries"],
            "ethical_considerations": ["Maintain privacy", "Follow applicable laws"],
            "investigation_scope": {
                "in_scope": ["Publicly available information"],
                "out_of_scope": ["Private information without authorization"]
            },
            "target_entities": [],
            "information_types": [],
            "urgency_level": "medium",
            "estimated_complexity": "medium",
            "error": "Generated fallback objectives due to processing error"
        }
    
    def _calculate_objective_confidence(self, objectives: Dict[str, Any]) -> float:
        """Calculate confidence score for the defined objectives"""
        score = 0.0
        total_checks = 0
        
        # Check for primary objectives
        if objectives.get("primary_objectives"):
            score += len(objectives["primary_objectives"]) > 0
        total_checks += 1
        
        # Check for KIRs
        if objectives.get("key_intelligence_requirements"):
            score += len(objectives["key_intelligence_requirements"]) > 0
        total_checks += 1
        
        # Check for success criteria
        if objectives.get("success_criteria"):
            score += len(objectives["success_criteria"]) > 0
        total_checks += 1
        
        # Check for constraints
        if objectives.get("constraints"):
            score += len(objectives["constraints"]) > 0
        total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0
    
    def _calculate_complexity_score(self, objectives: Dict[str, Any]) -> str:
        """Calculate investigation complexity"""
        complexity_factors = 0
        
        # Count objectives
        primary_count = len(objectives.get("primary_objectives", []))
        secondary_count = len(objectives.get("secondary_objectives", []))
        
        if primary_count > 3 or secondary_count > 5:
            complexity_factors += 1
        
        # Count KIRs
        kir_count = len(objectives.get("key_intelligence_requirements", []))
        if kir_count > 10:
            complexity_factors += 1
        
        # Check information types
        info_types = len(objectives.get("information_types", []))
        if info_types > 5:
            complexity_factors += 1
        
        # Check urgency
        if objectives.get("urgency_level") == "critical":
            complexity_factors += 1
        
        if complexity_factors >= 3:
            return "high"
        elif complexity_factors >= 1:
            return "medium"
        else:
            return "low"
    
    def _get_required_output_fields(self) -> List[str]:
        """Get required output fields for this agent"""
        return [
            "primary_objectives",
            "key_intelligence_requirements", 
            "success_criteria",
            "constraints",
            "ethical_considerations"
        ]