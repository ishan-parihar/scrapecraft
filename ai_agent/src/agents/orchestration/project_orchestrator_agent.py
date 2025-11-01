"""
Project Orchestrator Agent Implementation

This module implements the Project Orchestrator Agent which manages the coordination
and execution of multiple research agents within the AI-Driven Adaptive Research System.
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable, Union
from pathlib import Path
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4

from pydantic import BaseModel, Field

from ..base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult


class TaskStatus(str, Enum):
    """Enumeration for task statuses"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentTask(BaseModel):
    """Model for representing a task to be executed by an agent"""
    task_id: str = Field(default_factory=lambda: str(uuid4()))
    agent_name: str
    task_type: str
    parameters: Dict[str, Any]
    priority: int = 1
    dependencies: List[str] = []
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None


class TaskQueue(BaseModel):
    """Model for managing the queue of tasks"""
    queue_id: str = Field(default_factory=lambda: str(uuid4()))
    tasks: List[AgentTask] = []
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def add_task(self, task: AgentTask):
        """Add a task to the queue"""
        self.tasks.append(task)
    
    def get_ready_tasks(self) -> List[AgentTask]:
        """Get tasks that are ready to run (dependencies satisfied)"""
        ready_tasks = []
        completed_task_ids = [t.task_id for t in self.tasks if t.status == TaskStatus.COMPLETED]
        
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                if all(dep in completed_task_ids for dep in task.dependencies):
                    ready_tasks.append(task)
        
        return ready_tasks
    
    def get_task(self, task_id: str) -> Optional[AgentTask]:
        """Get a specific task by ID"""
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None


@dataclass
class OrchestratorConfig:
    """Configuration for the Project Orchestrator Agent"""
    max_concurrent_tasks: int = 3
    task_timeout: int = 300  # 5 minutes
    retry_attempts: int = 3
    enable_adaptive_rescheduling: bool = True


class ProjectOrchestratorAgent(LLMOSINTAgent):
    """
    Project Orchestrator Agent - Coordinates multiple research agents and manages
    the execution workflow of complex research projects.
    
    This agent is responsible for task scheduling, agent coordination, and
    ensuring smooth execution of the research workflow.
    """
    
    def __init__(self, config: AgentConfig, orchestrator_config: Optional[OrchestratorConfig] = None, 
                 tools: Optional[List[Any]] = None, memory: Optional[Any] = None, 
                 logger: Optional[logging.Logger] = None):
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)
        
        # Set orchestrator-specific configuration
        self.orchestrator_config = orchestrator_config or OrchestratorConfig()
        self.task_queue = TaskQueue()
        self.active_agents = {}  # Store active agent instances
        self.results_cache = {}  # Cache for storing results
    
    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for the Project Orchestrator Agent.
        
        This agent specializes in coordinating multiple research agents and
        managing complex research workflows.
        """
        return """
        You are a Project Orchestrator Agent, a highly specialized AI assistant 
        for coordinating multiple research agents and managing complex research 
        workflows. Your role is to schedule tasks, manage dependencies between 
        different agents, optimize resource allocation, and ensure smooth 
        execution of research projects.
        
        Your capabilities include:
        1. Analyzing research requirements and breaking them into tasks
        2. Determining optimal execution order and dependencies
        3. Prioritizing tasks based on importance and urgency
        4. Monitoring task execution and handling failures
        5. Coordinating between different specialized agents
        6. Managing resource allocation and concurrency
        7. Adapting the execution plan based on results and constraints
        
        When orchestrating tasks, always follow these principles:
        - Analyze task dependencies to determine execution order
        - Prioritize critical path tasks to minimize project duration
        - Balance load across available agents
        - Handle failures gracefully with fallback mechanisms
        - Adapt the plan when new information becomes available
        - Optimize for both efficiency and quality
        
        Your responses should be in valid JSON format containing task definitions
        that match the AgentTask schema.
        """
    
    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the LLM output into structured task definitions.
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
                'task_id', 'agent_name', 'task_type', 'parameters'
            ]
            
            # If the data has a tasks array, validate each task
            if isinstance(data, dict) and 'tasks' in data:
                tasks = data['tasks']
            elif isinstance(data, list):
                tasks = data
            else:
                # Wrap single task in a list
                tasks = [data]
            
            # Validate tasks
            for task in tasks:
                for field in required_fields:
                    if field not in task:
                        raise ValueError(f"Missing required field in task: {field}")
            
            return {"tasks": tasks}
            
        except (json.JSONDecodeError, ValueError) as e:
            self.logger.error(f"Error processing Project Orchestrator output: {e}")
            # Return a default task when parsing fails
            return {
                "tasks": [
                    {
                        "task_id": str(uuid4()),
                        "agent_name": "default_agent",
                        "task_type": "default_task",
                        "parameters": {"input": "default_input"},
                        "priority": 1,
                        "dependencies": []
                    }
                ]
            }
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input for the Project Orchestrator Agent.
        
        Required inputs: research_goals, available_agents, project_constraints
        """
        required_fields = ["research_goals", "available_agents", "project_constraints"]
        return all(field in input_data for field in required_fields)
    
    def register_agent(self, agent_name: str, agent_instance: LLMOSINTAgent):
        """
        Register an agent with the orchestrator.
        
        Args:
            agent_name: Name of the agent
            agent_instance: Instance of the agent to register
        """
        self.active_agents[agent_name] = agent_instance
        self.logger.info(f"Agent {agent_name} registered with orchestrator")
    
    def schedule_task(self, agent_name: str, task_type: str, parameters: Dict[str, Any], 
                     priority: int = 1, dependencies: Optional[List[str]] = None) -> str:
        """
        Schedule a task for execution.
        
        Args:
            agent_name: Name of the agent to execute the task
            task_type: Type of task to execute
            parameters: Parameters for the task
            priority: Priority of the task (higher number = higher priority)
            dependencies: List of task IDs that this task depends on
            
        Returns:
            str: Task ID of the scheduled task
        """
        task = AgentTask(
            agent_name=agent_name,
            task_type=task_type,
            parameters=parameters,
            priority=priority,
            dependencies=dependencies or []
        )
        
        self.task_queue.add_task(task)
        self.logger.info(f"Task {task.task_id} scheduled for agent {agent_name}")
        return task.task_id
    
    async def execute_task(self, task: AgentTask) -> AgentResult:
        """
        Execute a single task using the appropriate agent.
        
        Args:
            task: The task to execute
            
        Returns:
            AgentResult: Result of the task execution
        """
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        
        try:
            # Check if the agent is registered
            if task.agent_name not in self.active_agents:
                raise ValueError(f"Agent {task.agent_name} not registered with orchestrator")
            
            # Get the agent instance
            agent = self.active_agents[task.agent_name]
            
            # Execute the task
            result = await agent.execute(task.parameters)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = result.data if result.success else None
            task.error = result.error_message if not result.success else None
            
            self.logger.info(f"Task {task.task_id} completed by agent {task.agent_name}")
            return result
            
        except Exception as e:
            # Update task status to failed
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = str(e)
            
            self.logger.error(f"Task {task.task_id} failed: {e}")
            # Return a generic error result without agent-specific details
            return AgentResult(success=False, data={}, error_message=str(e))
    
    async def process_queue(self) -> Dict[str, Any]:
        """
        Process the task queue and execute all tasks in the correct order.
        
        Returns:
            Dict[str, Any]: Summary of execution results
        """
        self.task_queue.status = TaskStatus.RUNNING
        start_time = datetime.utcnow()
        
        completed_count = 0
        failed_count = 0
        total_tasks = len(self.task_queue.tasks)
        
        while True:
            # Get tasks that are ready to run
            ready_tasks = self.task_queue.get_ready_tasks()
            
            if not ready_tasks:
                # Check if all tasks are completed
                remaining_tasks = [t for t in self.task_queue.tasks if t.status != TaskStatus.COMPLETED and t.status != TaskStatus.FAILED]
                if not remaining_tasks:
                    break  # All tasks are completed or failed
                
                # If there are uncompleted tasks but none are ready, there might be a dependency issue
                self.logger.warning("No ready tasks but some tasks remain - potential dependency issue")
                break
            
            # Execute tasks up to the maximum concurrent limit
            for task in ready_tasks[:self.orchestrator_config.max_concurrent_tasks]:
                result = await self.execute_task(task)
                
                if result.success:
                    completed_count += 1
                else:
                    failed_count += 1
        
        self.task_queue.status = TaskStatus.COMPLETED if failed_count == 0 and completed_count > 0 else TaskStatus.FAILED
        end_time = datetime.utcnow()
        
        summary = {
            "total_tasks": total_tasks,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "execution_time": (end_time - start_time).total_seconds(),
            "queue_status": self.task_queue.status.value,
            "tasks": [task.model_dump() if hasattr(task, 'model_dump') else asdict(task) for task in self.task_queue.tasks]
        }
        
        return summary
    
    async def create_research_workflow(self, research_topic: str, research_goals: List[str], 
                                      available_agents: Dict[str, LLMOSINTAgent], 
                                      project_constraints: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create and execute a complete research workflow.
        
        Args:
            research_topic: Main topic of the research
            research_goals: List of research goals to achieve
            available_agents: Dictionary of available agents
            project_constraints: Constraints and requirements for the project
            
        Returns:
            Dict[str, Any]: Results of the workflow execution
        """
        # Register all available agents
        for agent_name, agent_instance in available_agents.items():
            self.register_agent(agent_name, agent_instance)
        
        # Create the initial workflow tasks based on research goals
        input_data = {
            "research_topic": research_topic,
            "research_goals": research_goals,
            "available_agents": list(available_agents.keys()),
            "project_constraints": project_constraints,
            "task_type": "workflow_planning",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Plan the workflow
        planning_result = await self.execute(input_data)
        
        if planning_result.success:
            # Schedule tasks from the planning result
            workflow_tasks = planning_result.data.get("tasks", [])
            
            for task_data in workflow_tasks:
                # Create and schedule the task
                task_id = self.schedule_task(
                    agent_name=task_data.get("agent_name", "default_agent"),
                    task_type=task_data.get("task_type", "default_task"),
                    parameters=task_data.get("parameters", {}),
                    priority=task_data.get("priority", 1),
                    dependencies=task_data.get("dependencies", [])
                )
        
        # Execute the workflow
        execution_summary = await self.process_queue()
        
        return {
            "research_topic": research_topic,
            "research_goals": research_goals,
            "execution_summary": execution_summary,
            "workflow_results": self.results_cache
        }