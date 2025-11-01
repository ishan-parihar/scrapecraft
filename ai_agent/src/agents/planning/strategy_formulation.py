"""
Strategy Formulation Agent

This agent is responsible for developing investigation strategies and methodologies
based on defined objectives and requirements.
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


class StrategyFormulationAgent(LLMOSINTAgent):
    """
    Agent responsible for formulating investigation strategies.
    
    This agent develops comprehensive investigation methodologies,
    identifies data sources, plans resource allocation, and defines coordination protocols.
    """
    
    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                role="Investigation Strategy Specialist",
                description="Develops comprehensive OSINT investigation strategies",
                max_iterations=5,
                timeout=240
            )
        
        # Initialize with basic tools
        tools = []
        
        super().__init__(config=config, tools=tools, **kwargs)
        
        # Strategy formulation specific attributes
        self.investigation_methodologies = {
            "passive_intelligence": {
                "description": "Information gathering without direct interaction",
                "techniques": ["open source research", "social media monitoring", "public records analysis"],
                "risk_level": "low"
            },
            "active_intelligence": {
                "description": "Information gathering with direct interaction",
                "techniques": ["human intelligence", "technical reconnaissance", "social engineering"],
                "risk_level": "high"
            },
            "technical_intelligence": {
                "description": "Technical analysis and digital forensics",
                "techniques": ["network analysis", "malware analysis", "digital footprint analysis"],
                "risk_level": "medium"
            }
        }
        
        self.data_sources = {
            "surface_web": {
                "sources": ["search engines", "websites", "blogs", "news articles"],
                "accessibility": "public",
                "reliability": "variable"
            },
            "social_media": {
                "sources": ["twitter", "linkedin", "facebook", "instagram", "reddit"],
                "accessibility": "public/semi-public",
                "reliability": "variable"
            },
            "public_records": {
                "sources": ["government databases", "court records", "business registries"],
                "accessibility": "public",
                "reliability": "high"
            },
            "dark_web": {
                "sources": ["tor networks", "hidden services", "underground forums"],
                "accessibility": "restricted",
                "reliability": "low"
            }
        }
    
    def _create_agent(self):
        """
        Create the LangChain agent for strategy formulation.
        
        Placeholder implementation - will be implemented with LangChain.
        """
        return self
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for strategy formulation"""
        return """
        You are an Investigation Strategy Specialist for OSINT operations.
        
        Based on the defined objectives, create a comprehensive investigation strategy:
        
        1. Select appropriate investigation methodologies
        2. Identify primary and secondary data sources
        3. Plan agent specialization allocation
        4. Define coordination protocols
        5. Establish timeline and milestones
        6. Allocate resources effectively
        7. Identify potential risks and mitigation strategies
        
        Consider the following factors:
        - Information availability and accessibility
        - Source reliability and credibility
        - Technical capabilities and limitations
        - Time constraints and urgency
        - Resource requirements and availability
        - Legal and ethical boundaries
        - Risk tolerance and mitigation
        
        Structure your response as valid JSON with the following format:
        {
            "investigation_methodology": {
                "primary_approach": "passive_intelligence|active_intelligence|technical_intelligence",
                "secondary_approaches": ["approach1", "approach2"],
                "rationale": "Explanation of methodology selection"
            },
            "data_sources": {
                "primary_sources": [
                    {
                        "type": "surface_web|social_media|public_records|dark_web",
                        "specific_sources": ["source1", "source2"],
                        "priority": "high|medium|low",
                        "access_method": "api|scraping|manual|automated"
                    }
                ],
                "secondary_sources": [...]
            },
            "agent_allocation": {
                "coordination_agent": "agent_type",
                "collection_agents": [
                    {
                        "agent_type": "SurfaceWebAgent|SocialMediaAgent|PublicRecordsAgent|DarkWebAgent",
                        "responsibilities": ["task1", "task2"],
                        "priority": "high|medium|low"
                    }
                ],
                "analysis_agents": [...],
                "synthesis_agents": [...]
            },
            "coordination_protocols": {
                "communication_channels": ["channel1", "channel2"],
                "data_sharing_methods": ["method1", "method2"],
                "decision_making_process": "centralized|decentralized|hybrid",
                "escalation_procedures": ["procedure1", "procedure2"]
            },
            "timeline": {
                "total_duration_days": 30,
                "phases": [
                    {
                        "phase": "planning|collection|analysis|synthesis",
                        "duration_days": 7,
                        "key_milestones": ["milestone1", "milestone2"],
                        "dependencies": ["dependency1", "dependency2"]
                    }
                ]
            },
            "resource_requirements": {
                "computational_resources": {
                    "cpu_cores": 8,
                    "memory_gb": 32,
                    "storage_gb": 500
                },
                "human_resources": {
                    "analysts": 2,
                    "technical_specialists": 1,
                    "subject_matter_experts": 1
                },
                "external_services": ["service1", "service2"],
                "tools_and_technologies": ["tool1", "tool2"]
            },
            "risk_assessment": {
                "operational_risks": ["risk1", "risk2"],
                "legal_risks": ["risk1", "risk2"],
                "technical_risks": ["risk1", "risk2"],
                "mitigation_strategies": ["strategy1", "strategy2"]
            },
            "success_metrics": {
                "quantitative_metrics": ["metric1", "metric2"],
                "qualitative_metrics": ["metric1", "metric2"],
                "progress_indicators": ["indicator1", "indicator2"]
            }
        }
        """
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the raw output from the agent into structured data.
        """
        try:
            # Check if this is a fallback response from _execute_local_fallback
            if "[This response was generated using local analysis" in raw_output:
                # This is a fallback response, generate proper structured strategy
                return self._generate_fallback_strategy()
            
            # Try to parse JSON output
            if raw_output.strip().startswith('{'):
                structured_data = json.loads(raw_output)
            else:
                # Extract JSON from text if embedded
                json_match = re.search(r'\{.*\}', raw_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback: parse text manually
                    structured_data = self._parse_text_output(raw_output)
            
            # Validate and enhance the strategy
            return self._validate_and_enhance_strategy(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing strategy output: {e}")
            return self._generate_fallback_strategy()
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate input data for strategy formulation"""
        # Check if objectives are provided
        if "objectives" not in input_data:
            self.logger.warning("Missing objectives in input data, will use fallback")
            return True  # Allow execution with fallback data
        
        objectives = input_data["objectives"]
        
        # Check for required objective components, but be more lenient with fallbacks
        required_objective_fields = ["primary_objectives", "key_intelligence_requirements"]
        missing_fields = []
        
        for field in required_objective_fields:
            if field not in objectives or not objectives[field]:
                missing_fields.append(field)
                self.logger.warning(f"Missing required objective field: {field}, will use fallback")
        
        # If both primary objectives and KIRs are missing, we can't proceed meaningfully
        if len(missing_fields) == len(required_objective_fields):
            self.logger.warning("Both primary_objectives and key_intelligence_requirements are missing, using fallback strategy")
            return True  # Still allow execution with complete fallback
        
        return True
    
    def _validate_and_enhance_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the strategy data"""
        enhanced = strategy.copy()
        
        # Ensure required sections exist
        required_sections = [
            "investigation_methodology", "data_sources", "agent_allocation",
            "coordination_protocols", "timeline", "resource_requirements",
            "risk_assessment", "success_metrics"
        ]
        
        for section in required_sections:
            if section not in enhanced:
                enhanced[section] = self._generate_default_section(section)
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "processing_timestamp": "2024-01-01T00:00:00Z",  # Will be dynamic
            "strategy_complexity": self._calculate_strategy_complexity(enhanced),
            "estimated_cost": self._estimate_strategy_cost(enhanced),
            "risk_level": self._calculate_overall_risk(enhanced)
        }
        
        # Validate timeline consistency
        enhanced = self._validate_timeline_consistency(enhanced)
        
        return enhanced
    
    def _parse_text_output(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text output into structured data"""
        strategy = {
            "investigation_methodology": {
                "primary_approach": "passive_intelligence",
                "secondary_approaches": [],
                "rationale": "Default strategy based on text parsing"
            },
            "data_sources": {
                "primary_sources": [],
                "secondary_sources": []
            },
            "agent_allocation": {
                "coordination_agent": "SearchCoordinationAgent",
                "collection_agents": [],
                "analysis_agents": [],
                "synthesis_agents": []
            },
            "coordination_protocols": {
                "communication_channels": ["message_queue"],
                "data_sharing_methods": ["shared_database"],
                "decision_making_process": "hybrid",
                "escalation_procedures": []
            },
            "timeline": {
                "total_duration_days": 30,
                "phases": []
            },
            "resource_requirements": {
                "computational_resources": {"cpu_cores": 4, "memory_gb": 16, "storage_gb": 250},
                "human_resources": {"analysts": 1, "technical_specialists": 1},
                "external_services": [],
                "tools_and_technologies": []
            },
            "risk_assessment": {
                "operational_risks": [],
                "legal_risks": [],
                "technical_risks": [],
                "mitigation_strategies": []
            },
            "success_metrics": {
                "quantitative_metrics": [],
                "qualitative_metrics": [],
                "progress_indicators": []
            }
        }
        
        # Simple text parsing logic
        lines = text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Identify sections and extract information
            if "methodology" in line.lower():
                current_section = "methodology"
            elif "data source" in line.lower():
                current_section = "data_sources"
            elif "agent" in line.lower():
                current_section = "agent_allocation"
            elif "timeline" in line.lower() or "schedule" in line.lower():
                current_section = "timeline"
            elif "resource" in line.lower():
                current_section = "resource_requirements"
            elif "risk" in line.lower():
                current_section = "risk_assessment"
            elif current_section and line.startswith(('-', '•', '*')):
                # Extract bullet points
                item = line.lstrip('-•* ').strip()
                self._add_item_to_section(strategy, current_section, item)
        
        return strategy
    
    def _add_item_to_section(self, strategy: Dict[str, Any], section: str, item: str):
        """Add parsed item to appropriate strategy section"""
        # Simple logic to add items to sections
        if section == "data_sources" and "primary_sources" in strategy["data_sources"]:
            strategy["data_sources"]["primary_sources"].append({"type": "surface_web", "specific_sources": [item], "priority": "medium"})
        elif section == "agent_allocation" and "collection_agents" in strategy["agent_allocation"]:
            strategy["agent_allocation"]["collection_agents"].append({"agent_type": "SurfaceWebAgent", "responsibilities": [item], "priority": "medium"})
        elif section == "risk_assessment" and "operational_risks" in strategy["risk_assessment"]:
            strategy["risk_assessment"]["operational_risks"].append(item)
    
    def _generate_default_section(self, section: str) -> Dict[str, Any]:
        """Generate default content for missing sections"""
        defaults = {
            "investigation_methodology": {
                "primary_approach": "passive_intelligence",
                "secondary_approaches": [],
                "rationale": "Default passive intelligence approach"
            },
            "data_sources": {
                "primary_sources": [],
                "secondary_sources": []
            },
            "agent_allocation": {
                "coordination_agent": "SearchCoordinationAgent",
                "collection_agents": [],
                "analysis_agents": [],
                "synthesis_agents": []
            },
            "coordination_protocols": {
                "communication_channels": ["message_queue"],
                "data_sharing_methods": ["shared_database"],
                "decision_making_process": "hybrid",
                "escalation_procedures": []
            },
            "timeline": {
                "total_duration_days": 30,
                "phases": []
            },
            "resource_requirements": {
                "computational_resources": {"cpu_cores": 4, "memory_gb": 16, "storage_gb": 250},
                "human_resources": {"analysts": 1, "technical_specialists": 1},
                "external_services": [],
                "tools_and_technologies": []
            },
            "risk_assessment": {
                "operational_risks": [],
                "legal_risks": [],
                "technical_risks": [],
                "mitigation_strategies": []
            },
            "success_metrics": {
                "quantitative_metrics": [],
                "qualitative_metrics": [],
                "progress_indicators": []
            }
        }
        
        return defaults.get(section, {})
    
    def _generate_fallback_strategy(self) -> Dict[str, Any]:
        """Generate basic strategy when parsing fails"""
        return {
            "investigation_methodology": {
                "primary_approach": "passive_intelligence",
                "secondary_approaches": ["technical_intelligence"],
                "rationale": "Conservative approach using publicly available information"
            },
            "data_sources": {
                "primary_sources": [
                    {
                        "type": "surface_web",
                        "specific_sources": ["search engines", "public websites"],
                        "priority": "high",
                        "access_method": "scraping"
                    }
                ],
                "secondary_sources": []
            },
            "agent_allocation": {
                "coordination_agent": "SearchCoordinationAgent",
                "collection_agents": [
                    {
                        "agent_type": "SurfaceWebAgent",
                        "responsibilities": ["Web scraping", "Content analysis"],
                        "priority": "high"
                    }
                ],
                "analysis_agents": [],
                "synthesis_agents": []
            },
            "coordination_protocols": {
                "communication_channels": ["message_queue"],
                "data_sharing_methods": ["shared_database"],
                "decision_making_process": "centralized",
                "escalation_procedures": ["manual_review"]
            },
            "timeline": {
                "total_duration_days": 14,
                "phases": [
                    {
                        "phase": "planning",
                        "duration_days": 2,
                        "key_milestones": ["Strategy finalized"],
                        "dependencies": []
                    },
                    {
                        "phase": "collection",
                        "duration_days": 7,
                        "key_milestones": ["Data collection completed"],
                        "dependencies": ["planning"]
                    }
                ]
            },
            "resource_requirements": {
                "computational_resources": {"cpu_cores": 4, "memory_gb": 16, "storage_gb": 250},
                "human_resources": {"analysts": 1, "technical_specialists": 1},
                "external_services": [],
                "tools_and_technologies": ["web_scraping_tools", "analysis_frameworks"]
            },
            "risk_assessment": {
                "operational_risks": ["Data availability issues"],
                "legal_risks": ["Terms of service compliance"],
                "technical_risks": ["Website blocking"],
                "mitigation_strategies": ["Multiple data sources", "Rate limiting"]
            },
            "success_metrics": {
                "quantitative_metrics": ["Data points collected", "Sources covered"],
                "qualitative_metrics": ["Data relevance", "Source reliability"],
                "progress_indicators": ["Collection progress", "Analysis completion"]
            },
            "error": "Generated fallback strategy due to processing error"
        }
    
    def _calculate_strategy_complexity(self, strategy: Dict[str, Any]) -> str:
        """Calculate overall strategy complexity"""
        complexity_score = 0
        
        # Count data sources
        primary_sources = len(strategy.get("data_sources", {}).get("primary_sources", []))
        secondary_sources = len(strategy.get("data_sources", {}).get("secondary_sources", []))
        
        if primary_sources + secondary_sources > 10:
            complexity_score += 1
        
        # Count agent types
        collection_agents = len(strategy.get("agent_allocation", {}).get("collection_agents", []))
        analysis_agents = len(strategy.get("agent_allocation", {}).get("analysis_agents", []))
        
        if collection_agents + analysis_agents > 5:
            complexity_score += 1
        
        # Check timeline
        total_duration = strategy.get("timeline", {}).get("total_duration_days", 0)
        if total_duration > 30:
            complexity_score += 1
        
        # Check resource requirements
        cpu_cores = strategy.get("resource_requirements", {}).get("computational_resources", {}).get("cpu_cores", 0)
        if cpu_cores > 8:
            complexity_score += 1
        
        if complexity_score >= 3:
            return "high"
        elif complexity_score >= 1:
            return "medium"
        else:
            return "low"
    
    def _estimate_strategy_cost(self, strategy: Dict[str, Any]) -> Dict[str, float]:
        """Estimate resource costs for the strategy"""
        # Simple cost estimation based on resources
        cpu_hours = (
            strategy.get("resource_requirements", {})
            .get("computational_resources", {})
            .get("cpu_cores", 4) * 
            strategy.get("timeline", {}).get("total_duration_days", 30) * 24
        )
        
        human_hours = (
            sum(strategy.get("resource_requirements", {}).get("human_resources", {}).values()) *
            strategy.get("timeline", {}).get("total_duration_days", 30) * 8
        )
        
        return {
            "computational_cost": cpu_hours * 0.10,  # $0.10 per CPU hour
            "human_cost": human_hours * 50,  # $50 per hour
            "external_services_cost": 100,  # Fixed estimate
            "total_estimated_cost": cpu_hours * 0.10 + human_hours * 50 + 100
        }
    
    def _calculate_overall_risk(self, strategy: Dict[str, Any]) -> str:
        """Calculate overall risk level"""
        risk_counts = 0
        
        for risk_category in ["operational_risks", "legal_risks", "technical_risks"]:
            risk_count = len(strategy.get("risk_assessment", {}).get(risk_category, []))
            if risk_count > 3:
                risk_counts += 1
        
        # Check methodology risk
        methodology = strategy.get("investigation_methodology", {}).get("primary_approach", "")
        if methodology == "active_intelligence":
            risk_counts += 2
        elif methodology == "technical_intelligence":
            risk_counts += 1
        
        if risk_counts >= 4:
            return "high"
        elif risk_counts >= 2:
            return "medium"
        else:
            return "low"
    
    def _validate_timeline_consistency(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Validate timeline consistency and adjust if needed"""
        timeline = strategy.get("timeline", {})
        phases = timeline.get("phases", [])
        
        # Calculate total phase duration
        total_phase_duration = sum(phase.get("duration_days", 0) for phase in phases)
        total_duration = timeline.get("total_duration_days", 30)
        
        # Adjust if inconsistent
        if total_phase_duration != total_duration:
            if not phases:
                # Create default phases
                phases = [
                    {
                        "phase": "planning",
                        "duration_days": max(1, total_duration // 10),
                        "key_milestones": ["Strategy defined"],
                        "dependencies": []
                    },
                    {
                        "phase": "collection",
                        "duration_days": max(1, total_duration // 2),
                        "key_milestones": ["Data collection completed"],
                        "dependencies": ["planning"]
                    },
                    {
                        "phase": "analysis",
                        "duration_days": max(1, total_duration // 3),
                        "key_milestones": ["Analysis completed"],
                        "dependencies": ["collection"]
                    },
                    {
                        "phase": "synthesis",
                        "duration_days": max(1, total_duration // 6),
                        "key_milestones": ["Report generated"],
                        "dependencies": ["analysis"]
                    }
                ]
                
                # Adjust to match total duration
                current_total = sum(phase.get("duration_days", 0) for phase in phases)
                if current_total != total_duration:
                    phases[2]["duration_days"] += total_duration - current_total
            
            strategy["timeline"]["phases"] = phases
        
        return strategy
    
    def _get_required_output_fields(self) -> List[str]:
        """Get required output fields for this agent"""
        return [
            "investigation_methodology",
            "data_sources",
            "agent_allocation",
            "coordination_protocols",
            "timeline"
        ]