"""
Research Loop Engine Implementation

This module implements the Research Loop Engine which manages the iterative
research process, enabling continuous learning and adaptation based on new
information and feedback.
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Tuple
from pathlib import Path
import logging
from datetime import datetime
import json

from pydantic import BaseModel, Field

from ..base.osint_agent import AgentResult
from .ai_planner_agent import ProjectPlan
from .project_orchestrator import ProjectOrchestrator, ResearchTask
from .project_orchestrator import ProjectOrchestrator, ResearchTask


class ResearchIteration(BaseModel):
    """Represents a single iteration of the research loop"""
    iteration_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    iteration_number: int
    research_tasks: List[Dict[str, Any]]
    results: List[Dict[str, Any]] = Field(default_factory=list)
    feedback: Dict[str, Any] = Field(default_factory=dict)
    confidence_score: float = 0.0
    completed_objectives: List[str] = Field(default_factory=list)
    new_information: List[str] = Field(default_factory=list)
    adaptation_needed: bool = False
    adaptation_reason: str = ""


class LoopMetrics(BaseModel):
    """Metrics for the research loop performance"""
    total_iterations: int = 0
    avg_iteration_time: float = 0.0
    total_research_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    avg_confidence_score: float = 0.0
    objectives_completed: int = 0
    objectives_remaining: int = 0
    information_gained: int = 0
    adaptation_events: int = 0
    efficiency_score: float = 0.0  # 0-1 scale


class ResearchLoopEngine:
    """
    Research Loop Engine - Manages the iterative research process.
    
    This component implements the continuous research loop that enables
    the AI-driven system to learn from new information, adapt its approach,
    and continuously refine its understanding of the research domain.
    """
    
    def __init__(self, orchestrator: ProjectOrchestrator, logger: Optional[logging.Logger] = None):
        self.orchestrator = orchestrator
        self.logger = logger or logging.getLogger(__name__)
        self.iterations: List[ResearchIteration] = []
        self.metrics = LoopMetrics()
        self.current_iteration = 0
        self.max_iterations = 50  # Prevent infinite loops
        self.convergence_threshold = 0.95  # When to stop if confidence is high
        self.divergence_threshold = 0.1   # When to trigger adaptation if confidence is low
        self.continuous_mode = True
        self.pause_between_iterations = 1  # seconds
    
    def add_research_task(self, task: ResearchTask):
        """Add a research task to be executed in the loop"""
        self.orchestrator.add_task(task)
    
    async def run_research_loop(self, max_iterations: Optional[int] = None, 
                                convergence_threshold: Optional[float] = None,
                                continuous_mode: bool = True) -> List[ResearchIteration]:
        """
        Run the main research loop with adaptive capabilities.
        
        Args:
            max_iterations: Maximum number of iterations to run
            convergence_threshold: Confidence threshold to stop iteration
            continuous_mode: Whether to continue until convergence or run fixed iterations
            
        Returns:
            List of completed iterations
        """
        self.max_iterations = max_iterations or self.max_iterations
        self.convergence_threshold = convergence_threshold or self.convergence_threshold
        self.continuous_mode = continuous_mode
        
        self.logger.info("Starting research loop execution")
        
        while self.current_iteration < self.max_iterations:
            iteration_start_time = time.time()
            
            # Create a new iteration
            iteration = ResearchIteration(
                iteration_id=f"iteration_{self.current_iteration + 1}",
                start_time=datetime.utcnow(),
                iteration_number=self.current_iteration + 1,
                research_tasks=[],
                results=[]
            )
            
            # Execute research tasks for this iteration
            await self._execute_iteration_tasks(iteration)
            
            # Evaluate the results and determine if adaptation is needed
            await self._evaluate_iteration_outcomes(iteration)
            
            # Check if we should continue based on convergence or other criteria
            should_continue = await self._should_continue(iteration)
            
            # Update metrics
            iteration_duration = time.time() - iteration_start_time
            iteration.end_time = datetime.utcnow()
            
            # Add iteration to history
            self.iterations.append(iteration)
            self._update_metrics(iteration, iteration_duration)
            
            self.logger.info(f"Iteration {iteration.iteration_number} completed. "
                           f"Confidence: {iteration.confidence_score:.2f}, "
                           f"Completed objectives: {len(iteration.completed_objectives)}")
            
            # Save iteration results
            await self._save_iteration_results(iteration)
            
            # Check if adaptation is needed based on feedback
            if iteration.adaptation_needed:
                self.logger.info(f"Adaptation triggered in iteration {iteration.iteration_number}: {iteration.adaptation_reason}")
                await self._perform_adaptation(iteration)
            
            # Pause between iterations if needed
            if self.pause_between_iterations > 0:
                await asyncio.sleep(self.pause_between_iterations)
            
            # Increment iteration counter
            self.current_iteration += 1
            
            # Break if we shouldn't continue
            if not should_continue:
                self.logger.info("Research loop stopped based on termination criteria")
                break
        
        self.logger.info(f"Research loop completed after {self.current_iteration} iterations")
        return self.iterations
    
    async def _execute_iteration_tasks(self, iteration: ResearchIteration):
        """Execute the research tasks for the current iteration"""
        # Get ready tasks from orchestrator
        ready_tasks = self.orchestrator.get_ready_tasks()
        
        if not ready_tasks:
            self.logger.info(f"No ready tasks for iteration {iteration.iteration_number}, "
                           f"checking for new task generation...")
            # If no tasks are ready, try to generate new tasks based on current state
            new_tasks = await self._generate_adaptive_tasks(iteration)
            for task in new_tasks:
                self.orchestrator.add_task(task)
                ready_tasks.append(task)
        
        # Execute all ready tasks
        for task in ready_tasks:
            iteration.research_tasks.append({
                "task_id": task.task_id,
                "task_name": task.task_name,
                "description": task.description
            })
            
            # Execute the task
            result = await self.orchestrator.execute_task(task.task_id)
            
            if result:
                iteration.results.append({
                    "task_id": task.task_id,
                    "result": result.dict(),
                    "timestamp": datetime.utcnow().isoformat()
                })
                
                # Extract new information from the result
                if result.success and 'data' in result.data:
                    # Look for new information in the result
                    new_info = self._extract_new_information(result.data)
                    iteration.new_information.extend(new_info)
        
        # Calculate overall confidence score for this iteration
        iteration.confidence_score = self._calculate_iteration_confidence(iteration)
    
    async def _evaluate_iteration_outcomes(self, iteration: ResearchIteration):
        """Evaluate the outcomes of the current iteration and check for adaptation needs"""
        # Check if objectives were completed
        completed_objectives = self._identify_completed_objectives(iteration)
        iteration.completed_objectives = completed_objectives
        
        # Determine if adaptation is needed
        if iteration.confidence_score < self.divergence_threshold:
            iteration.adaptation_needed = True
            iteration.adaptation_reason = f"Low confidence score: {iteration.confidence_score:.2f} < {self.divergence_threshold}"
        elif self._needs_adaptation_due_to_new_info(iteration):
            iteration.adaptation_needed = True
            iteration.adaptation_reason = "New significant information discovered requiring approach adjustment"
        elif self._needs_adaptation_due_to_failed_tasks(iteration):
            iteration.adaptation_needed = True
            iteration.adaptation_reason = "Multiple task failures detected requiring strategy adjustment"
    
    def _identify_completed_objectives(self, iteration: ResearchIteration) -> List[str]:
        """Identify which research objectives were completed in this iteration"""
        completed = []
        
        # Extract completed objectives from task results
        for result_entry in iteration.results:
            result = result_entry['result']
            if result.get('success', False):
                # Look for objective completion indicators in the result data
                data = result.get('data', {})
                if 'completed_objectives' in data:
                    completed.extend(data['completed_objectives'])
                elif 'objective_completed' in data:
                    completed.append(data['objective_completed'])
        
        return list(set(completed))  # Remove duplicates
    
    def _needs_adaptation_due_to_new_info(self, iteration: ResearchIteration) -> bool:
        """Check if adaptation is needed due to significant new information"""
        # Adapt if we discovered significantly new information that changes understanding
        return len(iteration.new_information) > 0
    
    def _needs_adaptation_due_to_failed_tasks(self, iteration: ResearchIteration) -> bool:
        """Check if adaptation is needed due to task failures"""
        failed_count = sum(1 for result in iteration.results if not result['result'].get('success', False))
        total_count = len(iteration.results)
        
        # Adapt if more than 30% of tasks fail in an iteration
        return total_count > 0 and (failed_count / total_count) > 0.3
    
    async def _should_continue(self, iteration: ResearchIteration) -> bool:
        """Determine if the research loop should continue"""
        # Stop if we've reached max iterations
        if self.current_iteration >= self.max_iterations:
            return False
        
        # Stop if confidence is high enough (converged)
        if iteration.confidence_score >= self.convergence_threshold and self.continuous_mode:
            self.logger.info(f"Stopping: Convergence threshold reached ({iteration.confidence_score:.2f} >= {self.convergence_threshold})")
            return False
        
        # Check if all objectives are completed
        project_plan = self.orchestrator.state.project_plan if self.orchestrator.state else None
        if project_plan:
            all_objectives = set(project_plan.research_objectives)
            completed_objectives = set()
            for past_iteration in self.iterations + [iteration]:
                completed_objectives.update(past_iteration.completed_objectives)
            
            if all_objectives.issubset(completed_objectives):
                self.logger.info("Stopping: All research objectives completed")
                return False
        
        # Continue by default
        return True
    
    def _calculate_iteration_confidence(self, iteration: ResearchIteration) -> float:
        """Calculate the overall confidence score for this iteration"""
        if not iteration.results:
            return 0.0
        
        # Calculate based on successful results
        successful_results = [r for r in iteration.results if r['result'].get('success', False)]
        success_rate = len(successful_results) / len(iteration.results)
        
        # Calculate based on result confidence scores
        confidence_scores = [r['result'].get('confidence', 0.5) for r in iteration.results]
        avg_result_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.5
        
        # Weighted combination of success rate and confidence
        overall_confidence = (success_rate * 0.6) + (avg_result_confidence * 0.4)
        
        return min(overall_confidence, 1.0)  # Ensure it doesn't exceed 1.0
    
    def _extract_new_information(self, result_data: Dict[str, Any]) -> List[str]:
        """Extract new information from a result"""
        new_info = []
        
        # Look for common fields that might contain new information
        for key, value in result_data.items():
            if isinstance(value, (str, list, dict)):
                if 'new_' in key.lower() or 'discovered_' in key.lower() or 'identified_' in key.lower():
                    if isinstance(value, str):
                        new_info.append(value)
                    elif isinstance(value, list):
                        new_info.extend([str(item) for item in value])
                    elif isinstance(value, dict):
                        new_info.append(str(value))
        
        return new_info
    
    async def _generate_adaptive_tasks(self, iteration: ResearchIteration) -> List[ResearchTask]:
        """Generate new tasks based on the results of current iteration"""
        new_tasks = []
        
        # If we have new information that suggests new research directions
        if iteration.new_information:
            # Create follow-up tasks based on new information
            for i, new_info in enumerate(iteration.new_information[:3]):  # Limit to 3 new tasks
                task_id = f"adaptive_followup_{iteration.iteration_number}_{i}"
                new_tasks.append(ResearchTask(
                    task_id=task_id,
                    task_name=f"Follow-up research on: {new_info[:50]}...",
                    description=f"Investigate leads discovered in previous iteration: {new_info}",
                    required_agents=["default_research_agent"],
                    dependencies=[],
                    input_data={"query": new_info, "context": "follow_up"},
                    priority=2
                ))
        
        return new_tasks
    
    def _update_metrics(self, iteration: ResearchIteration, iteration_duration: float):
        """Update loop metrics based on the completed iteration"""
        # Update basic metrics
        self.metrics.total_iterations += 1
        self.metrics.total_research_tasks += len(iteration.research_tasks)
        
        # Update success/failure metrics
        for result in iteration.results:
            if result['result'].get('success', False):
                self.metrics.successful_tasks += 1
            else:
                self.metrics.failed_tasks += 1
        
        # Update confidence metrics
        total_confidence = self.metrics.avg_confidence_score * (self.metrics.total_iterations - 1)
        total_confidence += iteration.confidence_score
        self.metrics.avg_confidence_score = total_confidence / self.metrics.total_iterations
        
        # Update objectives metrics
        all_completed = set()
        for past_iteration in self.iterations:
            all_completed.update(past_iteration.completed_objectives)
        self.metrics.objectives_completed = len(all_completed)
        
        if self.orchestrator.state and self.orchestrator.state.project_plan:
            total_objectives = len(self.orchestrator.state.project_plan.research_objectives)
            self.metrics.objectives_remaining = max(0, total_objectives - self.metrics.objectives_completed)
        
        # Update information metrics
        self.metrics.information_gained += len(iteration.new_information)
        
        # Update adaptation metrics
        if iteration.adaptation_needed:
            self.metrics.adaptation_events += 1
        
        # Update efficiency metrics (simple calculation based on success rate and confidence)
        success_rate = self.metrics.successful_tasks / self.metrics.total_research_tasks if self.metrics.total_research_tasks > 0 else 0
        avg_confidence = self.metrics.avg_confidence_score
        self.metrics.efficiency_score = (success_rate * avg_confidence)
    
    async def _save_iteration_results(self, iteration: ResearchIteration):
        """Save the results of an iteration to the project directory"""
        results_path = Path(self.orchestrator.project_root) / "outputs" / "iterations"
        results_path.mkdir(parents=True, exist_ok=True)
        
        # Save the iteration data
        iteration_path = results_path / f"iteration_{iteration.iteration_number:03d}.json"
        with open(iteration_path, 'w') as f:
            # Convert datetime objects to ISO format for JSON serialization
            iteration_data = iteration.dict()
            if iteration_data['start_time']:
                iteration_data['start_time'] = iteration_data['start_time'].isoformat()
            if iteration_data['end_time']:
                iteration_data['end_time'] = iteration_data['end_time'].isoformat()
            json.dump(iteration_data, f, indent=2, default=str)
        
        # Update the main results summary
        summary_path = results_path / "iteration_summary.json"
        summary = {
            "total_iterations": len(self.iterations),
            "latest_iteration": iteration.iteration_number,
            "latest_confidence": iteration.confidence_score,
            "total_objectives_completed": self.metrics.objectives_completed,
            "total_new_information": self.metrics.information_gained,
            "adaptation_events": self.metrics.adaptation_events
        }
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    async def _perform_adaptation(self, iteration: ResearchIteration):
        """Perform adaptive changes based on iteration feedback"""
        feedback_data = {
            "iteration_results": iteration.results,
            "new_information": iteration.new_information,
            "completed_objectives": iteration.completed_objectives,
            "confidence_score": iteration.confidence_score,
            "adaptation_reason": iteration.adaptation_reason
        }
        
        # Use the orchestrator's adaptive replan method
        try:
            await self.orchestrator.adaptive_replan(feedback_data)
            self.logger.info(f"Adaptation completed for iteration {iteration.iteration_number}")
        except Exception as e:
            self.logger.error(f"Error during adaptation for iteration {iteration.iteration_number}: {str(e)}")
    
    def get_loop_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the research loop"""
        return {
            "current_iteration": self.current_iteration,
            "total_iterations_completed": self.metrics.total_iterations,
            "metrics": self.metrics.dict(),
            "ongoing_tasks": self.orchestrator.state.active_tasks if self.orchestrator.state else [],
            "completed_tasks": self.orchestrator.state.completed_tasks if self.orchestrator.state else [],
            "project_progress": self.orchestrator.state.research_progress if self.orchestrator.state else 0.0,
            "latest_confidence_score": self.iterations[-1].confidence_score if self.iterations else 0.0,
            "total_new_information": sum(len(it.new_information) for it in self.iterations),
            "adaptation_events": len([it for it in self.iterations if it.adaptation_needed])
        }
    
    async def pause_loop(self):
        """Pause the research loop execution"""
        self.continuous_mode = False
        self.logger.info("Research loop paused")
    
    async def resume_loop(self):
        """Resume the research loop execution"""
        self.continuous_mode = True
        self.logger.info("Research loop resumed")
    
    async def terminate_loop(self):
        """Terminate the research loop execution"""
        self.max_iterations = self.current_iteration  # Set max iterations to current to stop the loop
        self.logger.info("Research loop terminated")