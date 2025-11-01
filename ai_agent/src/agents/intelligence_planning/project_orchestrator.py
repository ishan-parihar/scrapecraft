"""
Project Orchestrator Implementation

This module implements the Project Orchestrator which manages the lifecycle
of AI-driven research projects, coordinating between different agents and
managing the research workflow.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import logging
from datetime import datetime
import importlib

from pydantic import BaseModel, Field

from ..base.osint_agent import AgentConfig, AgentResult
from .ai_planner_agent import AIPlannerAgent, ProjectPlan


class ResearchTask(BaseModel):
    """Definition of a research task"""
    task_id: str
    task_name: str
    description: str
    required_agents: List[str]
    dependencies: List[str]  # task_ids this task depends on
    input_data: Dict[str, Any]
    priority: int = 1
    deadline: Optional[datetime] = None
    success_criteria: List[str] = Field(default_factory=list)


class ProjectState(BaseModel):
    """Current state of the research project"""
    project_plan: ProjectPlan
    current_phase: str
    completed_tasks: List[str]
    active_tasks: List[str]
    failed_tasks: List[str]
    task_results: Dict[str, AgentResult]
    research_progress: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    project_metrics: Dict[str, Any] = Field(default_factory=dict)


class ProjectOrchestrator:
    """
    Project Orchestrator - Manages the lifecycle of AI-driven research projects.
    
    This component coordinates between different agents, manages the research workflow,
    and maintains the state of the research project throughout its lifecycle.
    """
    
    def __init__(self, project_root: str, logger: Optional[logging.Logger] = None):
        self.project_root = Path(project_root)
        self.logger = logger or logging.getLogger(__name__)
        self.agents: Dict[str, Any] = {}
        self.tasks: Dict[str, ResearchTask] = {}
        self.config = self._load_project_config()
        
        # Initialize project state
        self._initialize_state()
    
    def _load_project_config(self) -> Dict[str, Any]:
        """Load project configuration from config.json"""
        config_path = self.project_root / "config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        else:
            raise FileNotFoundError(f"Project configuration not found at {config_path}")
    
    def _initialize_state(self):
        """Initialize the project state from saved state or defaults"""
        try:
            state_path = self.project_root / "state.json"
            if state_path.exists():
                with open(state_path, 'r') as f:
                    state_data = json.load(f)
                    # Load the project plan separately
                    plan_path = self.project_root / "plan.json"
                    if plan_path.exists():
                        with open(plan_path, 'r') as pf:
                            plan_data = json.load(pf)
                            project_plan = ProjectPlan(**plan_data)
                            state_data['project_plan'] = project_plan
                    self.state = ProjectState(**state_data)
            else:
                # Create initial state with an empty project plan
                project_plan = ProjectPlan(
                    project_name=self.config.get("project_name", "Unknown Project"),
                    project_description=self.config.get("description", "No description"),
                    research_objectives=self.config.get("research_objectives", []),
                    research_steps=[],
                    estimated_duration="TBD",
                    required_agents=self.config.get("required_agents", []),
                    project_directory=str(self.project_root),
                    success_criteria=self.config.get("success_criteria", []),
                    potential_challenges=[],
                    initial_data_collection_strategy="Standard approach"
                )
                self.state = ProjectState(
                    project_plan=project_plan,
                    current_phase="initial",
                    completed_tasks=[],
                    active_tasks=[],
                    failed_tasks=[],
                    task_results={},
                    research_progress=0.0
                )
        except Exception as e:
            self.logger.error(f"Error initializing state: {e}")
            # Create a default state if initialization fails
            project_plan = ProjectPlan(
                project_name=self.config.get("project_name", "Unknown Project"),
                project_description=self.config.get("description", "No description"),
                research_objectives=self.config.get("research_objectives", []),
                research_steps=[],
                estimated_duration="TBD",
                required_agents=self.config.get("required_agents", []),
                project_directory=str(self.project_root),
                success_criteria=self.config.get("success_criteria", []),
                potential_challenges=[],
                initial_data_collection_strategy="Standard approach"
            )
            self.state = ProjectState(
                project_plan=project_plan,
                current_phase="initial",
                completed_tasks=[],
                active_tasks=[],
                failed_tasks=[],
                task_results={},
                research_progress=0.0
            )
    
    def save_state(self):
        """Save current project state to file"""
        if self.state:
            # Prepare state data for serialization
            state_data = self.state.dict()
            # Extract project plan separately to handle serialization
            plan_data = self.state.project_plan.dict()
            
            # Save project plan
            plan_path = self.project_root / "plan.json"
            with open(plan_path, 'w') as f:
                json.dump(plan_data, f, indent=2, default=str)
            
            # Remove project_plan from state data to avoid duplication
            del state_data['project_plan']
            
            # Save state data
            state_path = self.project_root / "state.json"
            with open(state_path, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
    
    def register_agent(self, agent_id: str, agent_instance: Any):
        """Register an agent with the orchestrator"""
        self.agents[agent_id] = agent_instance
        self.logger.info(f"Registered agent: {agent_id}")
    
    def add_task(self, task: ResearchTask):
        """Add a research task to the orchestrator"""
        self.tasks[task.task_id] = task
        self.logger.info(f"Added task: {task.task_id}")
    
    def get_ready_tasks(self) -> List[ResearchTask]:
        """Get tasks that are ready to be executed (dependencies satisfied)"""
        ready_tasks = []
        
        for task_id, task in self.tasks.items():
            # Skip if task is already completed or active
            if task_id in self.state.completed_tasks or task_id in self.state.active_tasks:
                continue
            
            # Check if all dependencies are completed
            all_deps_completed = all(dep in self.state.completed_tasks for dep in task.dependencies)
            
            if all_deps_completed:
                ready_tasks.append(task)
        
        return ready_tasks
    
    async def execute_task(self, task_id: str) -> Optional[AgentResult]:
        """Execute a specific research task"""
        if task_id not in self.tasks:
            self.logger.error(f"Task {task_id} not found")
            return None
        
        task = self.tasks[task_id]
        
        # Mark task as active
        self.state.active_tasks.append(task_id)
        self.save_state()
        
        try:
            self.logger.info(f"Starting execution of task: {task_id}")
            
            # Determine which agent to use based on task requirements
            agent_id = task.required_agents[0] if task.required_agents else None
            if not agent_id or agent_id not in self.agents:
                self.logger.error(f"No suitable agent found for task {task_id}")
                return None
            
            agent = self.agents[agent_id]
            
            # Execute the task with the appropriate agent
            result = await agent.execute(task.input_data)
            
            # Update state based on result
            self.state.task_results[task_id] = result
            
            if result.success:
                self.state.completed_tasks.append(task_id)
                self.state.active_tasks.remove(task_id)
                
                # Calculate progress
                total_tasks = len(self.tasks)
                completed_tasks = len(self.state.completed_tasks)
                self.state.research_progress = completed_tasks / total_tasks if total_tasks > 0 else 0.0
                
                self.logger.info(f"Successfully completed task: {task_id}")
            else:
                self.state.failed_tasks.append(task_id)
                self.state.active_tasks.remove(task_id)
                self.logger.error(f"Failed task: {task_id}, Error: {result.error_message}")
            
            # Update last updated time
            self.state.last_updated = datetime.utcnow()
            
            # Save state
            self.save_state()
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing task {task_id}: {str(e)}")
            
            # Mark as failed
            self.state.failed_tasks.append(task_id)
            self.state.active_tasks.remove(task_id)
            
            # Create error result
            error_result = AgentResult(
                success=False,
                data={},
                error_message=str(e),
                execution_time=0.0
            )
            self.state.task_results[task_id] = error_result
            
            # Save state
            self.save_state()
            
            return error_result
    
    async def execute_project(self, max_concurrent_tasks: int = 3):
        """Execute the entire project by processing tasks"""
        self.logger.info("Starting project execution")
        
        # Continue until all tasks are completed
        while len(self.state.completed_tasks) + len(self.state.failed_tasks) < len(self.tasks):
            # Get available tasks that can be executed
            ready_tasks = self.get_ready_tasks()
            
            if not ready_tasks:
                # If no tasks are ready but we have active tasks, wait for them
                if self.state.active_tasks:
                    await asyncio.sleep(1)  # Wait briefly before checking again
                    continue
                else:
                    # No tasks can be executed (possible circular dependency)
                    self.logger.error("No tasks can be executed - possible circular dependency")
                    break
            
            # Execute up to max_concurrent_tasks ready tasks
            tasks_to_execute = ready_tasks[:max_concurrent_tasks]
            
            # Execute tasks concurrently
            execution_tasks = []
            for task in tasks_to_execute:
                execution_tasks.append(self.execute_task(task.task_id))
            
            # Wait for all current executions to complete
            await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        self.logger.info(f"Project execution completed. Completed: {len(self.state.completed_tasks)}, Failed: {len(self.state.failed_tasks)}")
    
    def generate_progress_report(self) -> Dict[str, Any]:
        """Generate a progress report for the current project"""
        return {
            "project_name": self.state.project_plan.project_name,
            "status": self._get_project_status(),
            "progress_percentage": self.state.research_progress * 100,
            "completed_tasks_count": len(self.state.completed_tasks),
            "failed_tasks_count": len(self.state.failed_tasks),
            "active_tasks_count": len(self.state.active_tasks),
            "total_tasks_count": len(self.tasks),
            "last_updated": self.state.last_updated.isoformat(),
            "current_phase": self.state.current_phase,
            "completed_tasks": self.state.completed_tasks,
            "failed_tasks": self.state.failed_tasks,
            "project_metrics": self.state.project_metrics
        }
    
    def _get_project_status(self) -> str:
        """Determine the overall project status"""
        if not self.tasks:
            return "initialized"
        
        total_tasks = len(self.tasks)
        completed_tasks = len(self.state.completed_tasks)
        
        if completed_tasks == total_tasks:
            return "completed"
        elif len(self.state.failed_tasks) > 0 and completed_tasks / total_tasks < 0.1:
            return "failed"
        elif completed_tasks / total_tasks < 0.25:
            return "initial"
        elif completed_tasks / total_tasks < 0.5:
            return "early_progress"
        elif completed_tasks / total_tasks < 0.75:
            return "mid_progress"
        else:
            return "late_progress"
    
    async def adaptive_replan(self, feedback: Dict[str, Any]):
        """Adaptively replan based on feedback and current state"""
        self.logger.info("Starting adaptive replanning process")
        
        # Create an AI Planner Agent to generate a new plan
        config = AgentConfig(
            role="AI Planner Agent",
            description="Agent responsible for adaptive replanning based on research progress and feedback",
            llm_model="gpt-4-turbo"
        )
        
        planner_agent = AIPlannerAgent(config=config)
        
        # Prepare input data for replanning
        input_data = {
            "research_topic": self.state.project_plan.project_name,
            "initial_objectives": self.state.project_plan.research_objectives,
            "project_scope": "Adaptive replanning based on current progress",
            "current_progress": self.generate_progress_report(),
            "feedback": feedback,
            "completed_tasks": self.state.completed_tasks,
            "failed_tasks": self.state.failed_tasks,
            "task_results": {task_id: result.dict() for task_id, result in self.state.task_results.items()}
        }
        
        # Generate new project plan
        new_plan = await planner_agent.create_project(
            research_topic=self.state.project_plan.project_name,
            initial_objectives=self.state.project_plan.research_objectives,
            project_scope="Adaptive replanning based on current progress and feedback"
        )
        
        # Update the project state with the new plan
        self.state.project_plan = new_plan
        
        self.logger.info("Adaptive replanning completed")
        return new_plan