"""
Research Loop Engine Implementation

This module implements the Research Loop Engine which manages the iterative
research process, adaptive learning, and continuous refinement within the
AI-Driven Adaptive Research System.
"""

import os
import json
from typing import Dict, Any, List, Optional, Callable, Union, Tuple
from pathlib import Path
import logging
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from uuid import uuid4
from asyncio import sleep

from pydantic import BaseModel, Field

from ..base.osint_agent import LLMOSINTAgent, AgentConfig, AgentResult
from .project_orchestrator_agent import ProjectOrchestratorAgent, OrchestratorConfig


class LoopStatus(str, Enum):
    """Enumeration for research loop statuses"""
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    EVALUATING = "evaluating"
    ADAPTING = "adapting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ResearchIteration(BaseModel):
    """Model for representing a research iteration"""
    iteration_id: str = Field(default_factory=lambda: str(uuid4()))
    iteration_number: int
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    status: LoopStatus = LoopStatus.EXECUTING
    input_data: Dict[str, Any]
    results: Dict[str, Any] = Field(default_factory=dict)
    feedback: Dict[str, Any] = Field(default_factory=dict)
    adaptation_needed: bool = False
    adaptation_plan: Optional[Dict[str, Any]] = None
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)


class EvaluationResult(BaseModel):
    """Model for representing evaluation results"""
    evaluation_id: str = Field(default_factory=lambda: str(uuid4()))
    criteria_evaluated: List[str]
    scores: Dict[str, float]  # Criteria name to score (0.0-1.0)
    overall_score: float = Field(ge=0.0, le=1.0, default=0.0)
    feedback: str
    recommendations: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    needs_adaptation: bool = False


class AdaptationPlan(BaseModel):
    """Model for representing adaptation plans"""
    plan_id: str = Field(default_factory=lambda: str(uuid4()))
    current_issues: List[str]
    proposed_changes: List[Dict[str, Any]]  # e.g., {"component": "agent", "change": "modify_strategy", "details": "..."}
    priority: int = 1  # Higher number = higher priority
    expected_impact: float = Field(ge=0.0, le=1.0, default=0.0)
    implementation_complexity: int = Field(ge=1, le=5, default=3)  # 1-5 scale
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class LoopConfig:
    """Configuration for the Research Loop Engine"""
    max_iterations: int = 10
    target_confidence_score: float = 0.8
    evaluation_threshold: float = 0.7
    adaptation_threshold: float = 0.6
    enable_adaptive_learning: bool = True
    enable_quality_control: bool = True
    enable_feedback_integration: bool = True
    iteration_delay: float = 0.0  # seconds between iterations (for rate limiting)


class ResearchLoopEngine:
    """
    Research Loop Engine - Manages the iterative research process, adaptive learning,
    and continuous refinement of research objectives and strategies.
    
    This engine is responsible for:
    1. Managing the research cycle: Plan -> Execute -> Evaluate -> Adapt
    2. Tracking iteration progress and quality
    3. Implementing adaptive mechanisms when objectives aren't met
    4. Maintaining state across iterations
    5. Learning from past iterations to improve future ones
    """
    
    def __init__(self, orchestrator: ProjectOrchestratorAgent, loop_config: Optional[LoopConfig] = None,
                 logger: Optional[logging.Logger] = None):
        self.orchestrator = orchestrator
        self.loop_config = loop_config or LoopConfig()
        self.logger = logger or logging.getLogger(f"{__name__}.ResearchLoopEngine")
        
        # Internal state management
        self.current_research_topic: Optional[str] = None
        self.current_objectives: List[str] = []
        self.current_iteration: Optional[ResearchIteration] = None
        self.iteration_history: List[ResearchIteration] = []
        self.evaluation_history: List[EvaluationResult] = []
        self.adaptation_history: List[AdaptationPlan] = []
        self.loop_status: LoopStatus = LoopStatus.IDLE
        self.current_iteration_number: int = 0
        
        self.logger.info("Research Loop Engine initialized")
    
    async def start_research_loop(self, research_topic: str, initial_objectives: List[str],
                                 research_plan: Dict[str, Any], quality_criteria: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Start the adaptive research loop.
        
        Args:
            research_topic: Main topic of the research
            initial_objectives: Initial set of research objectives
            research_plan: Initial plan for the research
            quality_criteria: List of criteria to evaluate research quality
            
        Returns:
            Dict[str, Any]: Final results of the research loop
        """
        self.logger.info(f"Starting research loop for topic: {research_topic}")
        
        self.current_research_topic = research_topic
        self.current_objectives = initial_objectives
        self.loop_status = LoopStatus.PLANNING
        self.current_iteration_number = 0
        
        # Initialize quality criteria if not provided
        self.quality_criteria = quality_criteria or [
            "relevance_to_topic",
            "completeness_of_data", 
            "accuracy_of_information",
            "timeliness_of_data",
            "source_reliability"
        ]
        
        # Initialize with the first plan
        initial_input = {
            "research_topic": research_topic,
            "objectives": initial_objectives,
            "initial_plan": research_plan,
            "iteration_number": 0
        }
        
        # Start the iterative loop
        final_results = {"iterations": [], "evaluations": [], "adaptations": [], "final_summary": {}}
        
        try:
            for iteration_num in range(self.loop_config.max_iterations):
                self.current_iteration_number = iteration_num
                self.logger.info(f"Starting iteration {iteration_num + 1}")
                
                # Plan the iteration
                iteration_plan = await self._plan_iteration(initial_input if iteration_num == 0 else self._get_adaptation_input())
                self.loop_status = LoopStatus.EXECUTING
                
                # Execute the iteration
                iteration_result = await self._execute_iteration(iteration_plan, iteration_num)
                
                # Evaluate the iteration
                self.loop_status = LoopStatus.EVALUATING
                evaluation_result = await self._evaluate_iteration(iteration_result)
                
                # Add to histories
                self.iteration_history.append(iteration_result)
                self.evaluation_history.append(evaluation_result)
                
                # Check if we've met our objectives or if adaptation is needed
                if self._check_completion_criteria(evaluation_result, iteration_result):
                    self.logger.info(f"Research objectives met at iteration {iteration_num + 1}")
                    break
                elif evaluation_result.needs_adaptation:
                    self.logger.info(f"Adaptation needed at iteration {iteration_num + 1}")
                    self.loop_status = LoopStatus.ADAPTING
                    adaptation_plan = await self._generate_adaptation_plan(evaluation_result, iteration_result)
                    self.adaptation_history.append(adaptation_plan)
                    
                    # Apply adaptation
                    await self._apply_adaptation(adaptation_plan)
                
                # Add delay between iterations if configured
                if self.loop_config.iteration_delay > 0:
                    await sleep(self.loop_config.iteration_delay)
            
            # Compile final results
            final_results = self._compile_final_results()
            self.loop_status = LoopStatus.COMPLETED
            
        except Exception as e:
            self.logger.error(f"Research loop failed: {e}", exc_info=True)
            self.loop_status = LoopStatus.FAILED
            final_results = {
                "iterations": self.iteration_history,
                "evaluations": self.evaluation_history,
                "adaptations": self.adaptation_history,
                "final_summary": {"status": "failed", "error": str(e)}
            }
        
        return final_results
    
    async def _plan_iteration(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Plan the next iteration based on current state and previous results.
        """
        self.logger.info(f"Planning iteration {self.current_iteration_number + 1}")
        
        # This would normally call an AI agent to generate a plan
        # For now, we'll return a basic plan
        plan = {
            "iteration_number": self.current_iteration_number,
            "tasks": [
                {
                    "task_id": str(uuid4()),
                    "agent_name": "Data Collection Agent",
                    "task_type": "data_collection",
                    "parameters": {
                        "query": self.current_research_topic,
                        "objectives": self.current_objectives
                    }
                }
            ],
            "expected_outcomes": f"Iteration {self.current_iteration_number + 1} outcomes",
            "quality_checkpoints": self.quality_criteria
        }
        
        return plan
    
    async def _execute_iteration(self, iteration_plan: Dict[str, Any], iteration_num: int) -> ResearchIteration:
        """
        Execute a single iteration of the research process.
        """
        self.logger.info(f"Executing iteration {iteration_num + 1}")
        
        # Create research iteration record
        iteration = ResearchIteration(
            iteration_number=iteration_num,
            input_data=iteration_plan,
            status=LoopStatus.EXECUTING
        )
        
        try:
            # Execute the plan using the orchestrator
            # For now, we'll simulate execution
            # In a real implementation, we would use the orchestrator to execute the tasks
            results = {}
            
            # Simulate execution of each task in the plan
            for task_data in iteration_plan.get("tasks", []):
                task_id = self.orchestrator.schedule_task(
                    agent_name=task_data.get("agent_name", "default_agent"),
                    task_type=task_data.get("task_type", "default_task"),
                    parameters=task_data.get("parameters", {}),
                    priority=1,
                    dependencies=[]
                )
                
                # In a real implementation, we would wait for the task to complete
                # For now, we'll simulate a result
                results[task_id] = {"result": f"Simulated result for task {task_id}"}
            
            # Process the queue of tasks
            if iteration_plan.get("tasks"):
                execution_summary = await self.orchestrator.process_queue()
                results["execution_summary"] = execution_summary
            
            # Calculate a confidence score based on results
            confidence_score = await self._calculate_iteration_confidence(results)
            
            # Update iteration record
            iteration.results = results
            iteration.confidence_score = confidence_score
            iteration.status = LoopStatus.COMPLETED
            
        except Exception as e:
            iteration.status = LoopStatus.FAILED
            iteration.results = {"error": str(e)}
            iteration.confidence_score = 0.0
            self.logger.error(f"Iteration {iteration_num + 1} failed: {e}")
        
        iteration.end_time = datetime.utcnow()
        self.current_iteration = iteration
        
        return iteration
    
    async def _evaluate_iteration(self, iteration_result: ResearchIteration) -> EvaluationResult:
        """
        Evaluate the results of an iteration against quality criteria.
        """
        self.logger.info(f"Evaluating iteration {iteration_result.iteration_number + 1}")
        
        # Calculate scores for each quality criterion
        scores = {}
        total_score = 0
        
        for criterion in self.quality_criteria:
            # Simulate scoring based on iteration results
            score = await self._score_criterion(criterion, iteration_result)
            scores[criterion] = score
            total_score += score
        
        overall_score = total_score / len(self.quality_criteria) if self.quality_criteria else 0.0
        
        # Determine if adaptation is needed
        needs_adaptation = overall_score < self.loop_config.adaptation_threshold
        
        # Generate recommendations
        recommendations = await self._generate_recommendations(scores, iteration_result)
        
        evaluation_result = EvaluationResult(
            criteria_evaluated=self.quality_criteria,
            scores=scores,
            overall_score=overall_score,
            feedback=f"Evaluation of iteration {iteration_result.iteration_number + 1}",
            recommendations=recommendations,
            needs_adaptation=needs_adaptation
        )
        
        return evaluation_result
    
    async def _score_criterion(self, criterion: str, iteration_result: ResearchIteration) -> float:
        """
        Score a specific criterion for the iteration.
        """
        # This would normally use AI evaluation or specialized scoring
        # For now, we'll use simple heuristics
        
        if criterion == "relevance_to_topic":
            # Score based on whether the results seem relevant to the research topic
            if self.current_research_topic and self.current_research_topic.lower() in str(iteration_result.results).lower():
                return 0.8
            else:
                return 0.3
        
        elif criterion == "completeness_of_data":
            # Score based on the amount and variety of data collected
            result_keys = list(iteration_result.results.keys())
            if len(result_keys) > 3:  # Arbitrary threshold
                return 0.7
            else:
                return 0.4
        
        elif criterion == "accuracy_of_information":
            # Score based on confidence score from the iteration
            return iteration_result.confidence_score
        
        elif criterion == "timeliness_of_data":
            # Score based on how recent the data is (simulated)
            return 0.7  # Assuming reasonably current data
        
        elif criterion == "source_reliability":
            # Score based on number of sources (simulated)
            if "execution_summary" in iteration_result.results:
                sources_count = iteration_result.results.get("execution_summary", {}).get("completed_tasks", 1)
                return min(1.0, sources_count * 0.2)  # Scale based on number of completed tasks
            else:
                return 0.5
        
        else:
            # Default score for unrecognized criteria
            return 0.6
    
    async def _generate_recommendations(self, scores: Dict[str, float], iteration_result: ResearchIteration) -> List[str]:
        """
        Generate recommendations based on evaluation scores.
        """
        recommendations = []
        
        for criterion, score in scores.items():
            if score < 0.5:  # Below threshold
                if criterion == "relevance_to_topic":
                    recommendations.append("Improve search terms to better match research topic")
                elif criterion == "completeness_of_data":
                    recommendations.append("Expand data sources or extend search scope")
                elif criterion == "accuracy_of_information":
                    recommendations.append("Verify information through additional sources")
                elif criterion == "timeliness_of_data":
                    recommendations.append("Focus on more recent data sources")
                elif criterion == "source_reliability":
                    recommendations.append("Use more authoritative or verified sources")
        
        if not recommendations:
            recommendations.append("Current results meet quality standards")
        
        return recommendations
    
    async def _calculate_iteration_confidence(self, results: Dict[str, Any]) -> float:
        """
        Calculate a confidence score for the iteration results.
        """
        # This would normally perform detailed analysis of result quality
        # For now, we'll use a simple heuristic
        if not results or "error" in results:
            return 0.1
        
        # Base confidence on number of successful results
        if "execution_summary" in results:
            success_rate = results["execution_summary"].get("completed_tasks", 0) / max(
                results["execution_summary"].get("total_tasks", 1), 1
            )
            return min(1.0, success_rate + 0.2)  # Add base confidence
        else:
            return 0.6  # Default confidence for simple results
    
    def _check_completion_criteria(self, evaluation_result: EvaluationResult, iteration_result: ResearchIteration) -> bool:
        """
        Check if the research objectives have been met.
        """
        # Check if we've met the target confidence score
        if iteration_result.confidence_score >= self.loop_config.target_confidence_score:
            return True
        
        # Check if overall evaluation score is sufficient
        if evaluation_result.overall_score >= self.loop_config.evaluation_threshold:
            return True
        
        # Check if max iterations reached
        if self.current_iteration_number >= self.loop_config.max_iterations - 1:
            return True
        
        return False
    
    async def _generate_adaptation_plan(self, evaluation_result: EvaluationResult, 
                                      iteration_result: ResearchIteration) -> AdaptationPlan:
        """
        Generate an adaptation plan based on evaluation results.
        """
        self.logger.info("Generating adaptation plan")
        
        # Identify issues from low scores
        current_issues = []
        for criterion, score in evaluation_result.scores.items():
            if score < 0.5:  # Below acceptable threshold
                current_issues.append(f"Low {criterion} score: {score}")
        
        # Identify potential changes based on recommendations
        proposed_changes = []
        for recommendation in evaluation_result.recommendations:
            change = {
                "component": "data_collection",  # Default component
                "change": recommendation,
                "details": f"Implement recommendation: {recommendation}"
            }
            proposed_changes.append(change)
        
        # Calculate expected impact (higher for lower scores)
        expected_impact = 1.0 - evaluation_result.overall_score  # Inverse relationship
        
        adaptation_plan = AdaptationPlan(
            current_issues=current_issues,
            proposed_changes=proposed_changes,
            priority=3,  # Default priority
            expected_impact=expected_impact,
            implementation_complexity=3  # Default complexity
        )
        
        return adaptation_plan
    
    async def _apply_adaptation(self, adaptation_plan: AdaptationPlan):
        """
        Apply the adaptation plan to adjust the research approach.
        """
        self.logger.info(f"Applying adaptation plan: {adaptation_plan.plan_id}")
        
        # Update research strategy based on adaptation plan
        for change in adaptation_plan.proposed_changes:
            component = change.get("component", "general")
            change_desc = change.get("change", "")
            
            if component == "data_collection":
                # Modify data collection strategy
                self.logger.info(f"Adapting data collection: {change_desc}")
            elif component == "analysis":
                # Modify analysis approach
                self.logger.info(f"Adapting analysis: {change_desc}")
            else:
                # General adaptation
                self.logger.info(f"Applying general adaptation: {change_desc}")
        
        # Apply changes to orchestrator or other components as needed
        # This would involve updating agent configurations, search parameters, etc.
    
    def _get_adaptation_input(self) -> Dict[str, Any]:
        """
        Prepare input for the next iteration based on adaptations.
        """
        return {
            "research_topic": self.current_research_topic,
            "objectives": self.current_objectives,
            "previous_iterations": self.iteration_history[-3:],  # Last 3 iterations
            "evaluation_feedback": self.evaluation_history[-1] if self.evaluation_history else {},
            "adaptations_applied": self.adaptation_history[-1] if self.adaptation_history else {},
            "iteration_number": self.current_iteration_number
        }
    
    def _compile_final_results(self) -> Dict[str, Any]:
        """
        Compile the final results of the research loop.
        """
        total_iterations = len(self.iteration_history)
        avg_confidence = sum(iter.confidence_score for iter in self.iteration_history) / total_iterations if total_iterations > 0 else 0.0
        final_score = self.evaluation_history[-1].overall_score if self.evaluation_history else 0.0
        
        final_results = {
            "research_topic": self.current_research_topic,
            "objectives": self.current_objectives,
            "total_iterations": total_iterations,
            "average_confidence": avg_confidence,
            "final_evaluation_score": final_score,
            "loop_status": self.loop_status.value,
            "iterations": [iter.model_dump() if hasattr(iter, 'model_dump') else iter.dict() for iter in self.iteration_history],
            "evaluations": [eval_res.model_dump() if hasattr(eval_res, 'model_dump') else eval_res.dict() for eval_res in self.evaluation_history],
            "adaptations": [adapt.model_dump() if hasattr(adapt, 'model_dump') else adapt.dict() for adapt in self.adaptation_history],
            "final_summary": {
                "status": "completed" if self.loop_status == LoopStatus.COMPLETED else "failed",
                "total_iterations": total_iterations,
                "average_confidence": avg_confidence,
                "final_score": final_score,
                "completion_reason": self._get_completion_reason()
            }
        }
        
        return final_results
    
    def _get_completion_reason(self) -> str:
        """
        Determine the reason for loop completion.
        """
        if self.loop_status == LoopStatus.COMPLETED:
            if self.evaluation_history and self.evaluation_history[-1].overall_score >= self.loop_config.evaluation_threshold:
                return "Quality threshold met"
            elif self.current_iteration_number >= self.loop_config.max_iterations - 1:
                return "Maximum iterations reached"
            else:
                return "Objectives met"
        else:
            return "Loop failed"
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the research loop.
        """
        return {
            "status": self.loop_status.value,
            "current_iteration": self.current_iteration_number,
            "total_iterations": len(self.iteration_history),
            "current_research_topic": self.current_research_topic,
            "current_objectives": self.current_objectives,
            "completed_iterations": len([i for i in self.iteration_history if i.status == LoopStatus.COMPLETED]),
            "failed_iterations": len([i for i in self.iteration_history if i.status == LoopStatus.FAILED]),
            "total_adaptations": len(self.adaptation_history),
            "average_confidence": sum(iter.confidence_score for iter in self.iteration_history) / len(self.iteration_history) if self.iteration_history else 0.0,
            "last_evaluation_score": self.evaluation_history[-1].overall_score if self.evaluation_history else 0.0
        }