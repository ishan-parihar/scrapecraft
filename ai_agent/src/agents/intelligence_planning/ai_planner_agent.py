"""
AI Planner Agent Implementation

This module implements the AI Planner Agent which handles intelligent project
initialization and planning for the AI-Driven Adaptive Research System.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

from pydantic import BaseModel, Field

from ..base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class ProjectPlan(BaseModel):
    """Structured output for project planning"""
    project_name: str
    project_description: str
    research_objectives: List[str]
    research_steps: List[Dict[str, Any]]
    estimated_duration: str
    required_agents: List[str]
    project_directory: str
    success_criteria: List[str]
    potential_challenges: List[str]
    initial_data_collection_strategy: str


class AIPlannerAgent(LLMOSINTAgent):
    """
    AI Planner Agent - Implements intelligent project initialization and planning.
    
    This agent is responsible for creating well-structured research projects,
    defining clear objectives, and establishing the foundational architecture
    for the AI-driven research system.
    """

    def __init__(self, config: AgentConfig, tools: Optional[List[Any]] = None, memory: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)
        
        # Set up project directory and file structure constants
        self.project_directories = [
            "data/raw",
            "data/processed",
            "data/enhanced",
            "outputs/reports",
            "outputs/summaries",
            "outputs/visualizations",
            "logs",
            "docs"
        ]
        
        self.project_files = [
            ".env",
            "README.md",
            "config.json"
        ]

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the AI Planner Agent.
        
        This agent specializes in creating well-structured, adaptive research projects
        with clear objectives and intelligent planning.
        """
        return """
        You are an AI Planner Agent, a highly specialized AI assistant for creating intelligent, 
        adaptive research projects. Your role is to design comprehensive project structures 
        that can support complex OSINT investigations with clear objectives, intelligent 
        workflows, and adaptive capabilities.

        Your capabilities include:
        1. Creating detailed project plans with clear objectives
        2. Designing adaptive workflows that can adjust to new information
        3. Defining required agents and their coordination mechanisms
        4. Establishing success criteria and evaluation metrics
        5. Anticipating potential challenges and mitigation strategies
        6. Designing data collection and processing strategies
        7. Creating structured project architectures

        When creating project plans, always follow these principles:
        - Structure should be modular and extensible
        - Objectives should be specific, measurable, and achievable
        - Consider multiple research paths and adaptive capabilities
        - Account for various data sources and collection methods
        - Plan for iterative refinement and learning
        - Include quality assurance and validation mechanisms

        Your responses should be in valid JSON format that can be parsed by a JSON parser,
        containing all the required fields for the ProjectPlan model.
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the LLM output into a structured ProjectPlan.
        
        The output should be a JSON object that matches the ProjectPlan schema.
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
                'project_name', 'project_description', 'research_objectives',
                'research_steps', 'estimated_duration', 'required_agents',
                'project_directory', 'success_criteria', 'potential_challenges',
                'initial_data_collection_strategy'
            ]
            
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error processing AI Planner output: {e}")
            # Return a valid structure if parsing fails
            import uuid
            project_dir = f"project_{str(uuid.uuid4())[:8]}"
            return {
                "project_name": "Adaptive Research Project",
                "project_description": "AI-Driven adaptive research project created due to API unavailability",
                "research_objectives": ["Primary research objective"],
                "research_steps": [{"step": 1, "description": "Initial research step"}],
                "estimated_duration": "TBD",
                "required_agents": ["default_agent"],
                "project_directory": project_dir,
                "success_criteria": ["Default success criterion"],
                "potential_challenges": ["Potential challenge"],
                "initial_data_collection_strategy": "Standard collection approach"
            }

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for the AI Planner Agent.
        
        Required inputs: research_topic, initial_objectives, project_scope
        """
        required_fields = ["research_topic", "initial_objectives", "project_scope"]
        return all(field in input_data for field in required_fields)

    async def create_project(self, research_topic: str, initial_objectives: List[str], project_scope: str) -> ProjectPlan:
        """
        Create a new research project with intelligent planning.
        
        Args:
            research_topic: The main topic of the research
            initial_objectives: Initial set of research objectives
            project_scope: Scope and constraints of the project
            
        Returns:
            ProjectPlan: A structured project plan
        """
        input_data = {
            "research_topic": research_topic,
            "initial_objectives": initial_objectives,
            "project_scope": project_scope,
            "task_type": "project_planning",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        result = await self.execute(input_data)
        
        if result.success:
            try:
                # Create a ProjectPlan from the result data
                project_plan = ProjectPlan(**result.data)
                # Create the project directory structure
                await self._create_project_structure(project_plan)
                return project_plan
            except Exception as e:
                self.logger.error(f"Error creating ProjectPlan object: {e}")
                # Create a default ProjectPlan when parsing fails
                import uuid
                project_dir = f"project_{str(uuid.uuid4())[:8]}"
                default_plan = ProjectPlan(
                    project_name="Adaptive Research Project",
                    project_description="AI-Driven adaptive research project created due to API unavailability",
                    research_objectives=initial_objectives,
                    research_steps=[{"step": 1, "description": "Initial research step"}],
                    estimated_duration="TBD",
                    required_agents=["default_agent"],
                    project_directory=project_dir,
                    success_criteria=["Default success criterion"],
                    potential_challenges=["Potential challenge"],
                    initial_data_collection_strategy="Standard collection approach"
                )
                await self._create_project_structure(default_plan)
                return default_plan
        else:
            # Create a default ProjectPlan when execution fails
            import uuid
            project_dir = f"project_{str(uuid.uuid4())[:8]}"
            default_plan = ProjectPlan(
                project_name="Adaptive Research Project",
                project_description="AI-Driven adaptive research project created due to execution failure",
                research_objectives=initial_objectives,
                research_steps=[{"step": 1, "description": "Initial research step"}],
                estimated_duration="TBD",
                required_agents=["default_agent"],
                project_directory=project_dir,
                success_criteria=["Default success criterion"],
                potential_challenges=["Potential challenge"],
                initial_data_collection_strategy="Standard collection approach"
            )
            await self._create_project_structure(default_plan)
            return default_plan

    async def _create_project_structure(self, project_plan: ProjectPlan):
        """
        Create the project directory structure based on the plan.
        
        Args:
            project_plan: The planned project structure
        """
        project_root = Path(project_plan.project_directory)
        
        # Ensure the path doesn't conflict with an existing file
        if project_root.exists() and project_root.is_file():
            # If there's a file with the same name, we need to handle it
            self.logger.warning(f"File exists at project path, removing: {project_root}")
            project_root.unlink()
        
        # Create main project directory
        project_root.mkdir(parents=True, exist_ok=True)
        
        # Create all required subdirectories
        for subdirectory in self.project_directories:
            # Ensure each subdirectory is not a file
            sub_path = project_root / subdirectory
            if sub_path.exists():
                if sub_path.is_file():
                    self.logger.warning(f"File exists at subdirectory path, removing: {sub_path}")
                    sub_path.unlink()
                # If it's a directory, we'll use it as is
            sub_path.mkdir(parents=True, exist_ok=True)
        
        # Create initial configuration file - ensure it's not conflicting with a directory
        config_path = project_root / "config.json"
        if config_path.exists() and config_path.is_dir():
            # If config.json exists as a directory, remove it
            self.logger.warning(f"Directory exists at config path, removing: {config_path}")
            import shutil
            shutil.rmtree(config_path)
        
        config_data = {
            "project_name": project_plan.project_name,
            "description": project_plan.project_description,
            "created_at": datetime.utcnow().isoformat(),
            "research_objectives": project_plan.research_objectives,
            "success_criteria": project_plan.success_criteria,
            "required_agents": project_plan.required_agents
        }
        
        with open(config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Create initial README - ensure it's not conflicting with a directory
        readme_path = project_root / "README.md"
        if readme_path.exists() and readme_path.is_dir():
            # If README.md exists as a directory, remove it
            self.logger.warning(f"Directory exists at README path, removing: {readme_path}")
            import shutil
            shutil.rmtree(readme_path)
        
        readme_content = f"""# {project_plan.project_name}

{project_plan.project_description}

## Research Objectives
{chr(10).join([f"- {obj}" for obj in project_plan.research_objectives])}

## Success Criteria
{chr(10).join([f"- {criterion}" for criterion in project_plan.success_criteria])}

## Project Timeline
Estimated Duration: {project_plan.estimated_duration}

## Required Agents
{chr(10).join([f"- {agent}" for agent in project_plan.required_agents])}

## Initial Data Collection Strategy
{project_plan.initial_data_collection_strategy}

Created on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
"""
        
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        self.logger.info(f"Project structure created at: {project_root}")