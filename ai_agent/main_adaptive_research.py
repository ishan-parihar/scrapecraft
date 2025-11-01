"""
AI-Driven Adaptive Research System (ADR) - Main Integration Module

This module demonstrates the complete AI-Driven Adaptive Research System
that integrates all components as outlined in the upgrade plan.
"""

import asyncio
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging
from datetime import datetime

from ai_agent.src.agents.base.osint_agent import AgentConfig
from ai_agent.src.agents.intelligence_planning.ai_planner_agent import AIPlannerAgent, ProjectPlan
from ai_agent.src.agents.specialized.objective_definition_agent import ObjectiveDefinitionAgent, ObjectiveDefinition
from ai_agent.src.agents.specialized.strategy_formulation_agent import StrategyFormulationAgent, ResearchStrategy
from ai_agent.src.agents.specialized.data_collection_agent import DataCollectionAgent, CollectionPlan


class AdaptiveResearchSystem:
    """
    AI-Driven Adaptive Research System (ADR) - Main Integration Class
    
    This class orchestrates the complete adaptive research process by integrating
    all specialized components of the system.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.project_plan: Optional[ProjectPlan] = None
        self.objective_definition: Optional[ObjectiveDefinition] = None
        self.research_strategy: Optional[ResearchStrategy] = None
        self.collection_plan: Optional[CollectionPlan] = None
        
        # Initialize all agent components
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize all specialized agents for the research system"""
        # Initialize AI Planner Agent
        planner_config = AgentConfig(
            role="AI Planner Agent",
            description="Specialized agent for creating intelligent research project plans",
            llm_model="gpt-4-turbo",
            temperature=0.2
        )
        self.planner_agent = AIPlannerAgent(config=planner_config)
        
        # Initialize Objective Definition Agent
        objective_config = AgentConfig(
            role="Objective Definition Agent", 
            description="Specialized agent for defining clear research objectives",
            llm_model="gpt-4-turbo",
            temperature=0.1
        )
        self.objective_agent = ObjectiveDefinitionAgent(config=objective_config)
        
        # Initialize Strategy Formulation Agent
        strategy_config = AgentConfig(
            role="Strategy Formulation Agent",
            description="Specialized agent for creating comprehensive research strategies",
            llm_model="gpt-4-turbo", 
            temperature=0.3
        )
        self.strategy_agent = StrategyFormulationAgent(config=strategy_config)
        
        # Initialize Data Collection Agent
        collection_config = AgentConfig(
            role="Data Collection Agent",
            description="Specialized agent for intelligent data gathering",
            llm_model="gpt-4-turbo",
            temperature=0.4
        )
        self.collection_agent = DataCollectionAgent(config=collection_config)
        
        self.logger.info("All specialized agents initialized successfully")
    
    async def execute_adaptive_research(self, research_topic: str, initial_requirements: List[str]) -> Dict[str, Any]:
        """
        Execute the complete adaptive research workflow.
        
        Args:
            research_topic: The main topic for research
            initial_requirements: Initial requirements for the research
            
        Returns:
            Dict containing the complete research results and metadata
        """
        self.logger.info(f"Starting adaptive research for topic: {research_topic}")
        
        # Phase 1: Project Planning
        self.logger.info("Phase 1: Project Planning")
        await self._execute_project_planning(research_topic, initial_requirements)
        
        # Phase 2: Objective Definition
        self.logger.info("Phase 2: Objective Definition")
        await self._execute_objective_definition(research_topic)
        
        # Phase 3: Strategy Formulation
        self.logger.info("Phase 3: Strategy Formulation")
        await self._execute_strategy_formulation()
        
        # Phase 4: Data Collection Planning
        self.logger.info("Phase 4: Data Collection Planning")
        await self._execute_collection_planning()
        
        # Phase 5: Data Collection
        self.logger.info("Phase 5: Data Collection Execution")
        collected_data = await self._execute_data_collection()
        
        # Compile results
        results = {
            "project_plan": self.project_plan.dict() if self.project_plan else {},
            "objectives": self.objective_definition.dict() if self.objective_definition else {},
            "strategy": self.research_strategy.dict() if self.research_strategy else {},
            "collection_plan": self.collection_plan.dict() if self.collection_plan else {},
            "collected_data": collected_data,
            "execution_timestamp": datetime.utcnow().isoformat(),
            "research_topic": research_topic,
            "initial_requirements": initial_requirements
        }
        
        self.logger.info("Adaptive research execution completed successfully")
        
        return results
    
    async def _execute_project_planning(self, research_topic: str, initial_requirements: List[str]):
        """Execute the project planning phase"""
        self.project_plan = await self.planner_agent.create_project(
            research_topic=research_topic,
            initial_objectives=initial_requirements,
            project_scope="Comprehensive adaptive research project"
        )
        self.logger.info(f"Project plan created: {self.project_plan.project_name}")
    
    async def _execute_objective_definition(self, research_topic: str):
        """Execute the objective definition phase"""
        self.objective_definition = await self.objective_agent.define_objectives(
            research_topic=research_topic,
            research_scope=self.project_plan.project_description if self.project_plan else "General research",
            initial_requirements=self.project_plan.research_objectives if self.project_plan else ["General research objective"]
        )
        self.logger.info(f"Objectives defined: {self.objective_definition.primary_objective}")
    
    async def _execute_strategy_formulation(self):
        """Execute the strategy formulation phase"""
        if not self.objective_definition:
            raise ValueError("Objectives must be defined before strategy formulation")
        
        self.research_strategy = await self.strategy_agent.formulate_strategy(
            objectives=[self.objective_definition.primary_objective] + self.objective_definition.secondary_objectives,
            resources={"personnel": 1, "time": "30 days", "budget": "TBD"},
            constraints=["time", "data_availability", "access_restrictions"]
        )
        self.logger.info(f"Research strategy formulated: {self.research_strategy.strategy_name}")
    
    async def _execute_collection_planning(self):
        """Execute the data collection planning phase"""
        if not self.objective_definition or not self.research_strategy:
            raise ValueError("Objectives and strategy must be defined before collection planning")
        
        self.collection_plan = await self.collection_agent.plan_collection(
            research_objectives=[self.objective_definition.primary_objective],
            strategy_guidelines=self.research_strategy.dict(),
            resource_constraints={"bandwidth": "standard", "time": "ongoing", "tools": ["default"]}
        )
        self.logger.info(f"Collection plan created for {len(self.collection_plan.sources_to_query)} sources")
    
    async def _execute_data_collection(self) -> Dict[str, Any]:
        """Execute the data collection phase"""
        if not self.collection_plan:
            raise ValueError("Collection plan must be created before executing collection")
        
        collected_data = await self.collection_agent.collect_data(self.collection_plan)
        self.logger.info(f"Data collection completed with {len(collected_data.get('data_samples', []))} samples")
        
        return collected_data


async def run_adaptive_research_demo():
    """
    Run a demonstration of the Adaptive Research System
    """
    print("🚀 Starting AI-Driven Adaptive Research System (ADR)")
    print("=" * 70)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create an instance of the adaptive research system
    research_system = AdaptiveResearchSystem()
    
    # Define a sample research topic and requirements
    research_topic = "Impact of AI on Cybersecurity in Financial Services"
    initial_requirements = [
        "Analyze current AI adoption in financial cybersecurity",
        "Identify key challenges and opportunities",
        "Assess regulatory implications",
        "Evaluate competitive landscape"
    ]
    
    print(f"🔬 Research Topic: {research_topic}")
    print(f"📋 Requirements: {len(initial_requirements)} initial requirements defined")
    print()
    
    # Execute the adaptive research workflow
    results = await research_system.execute_adaptive_research(research_topic, initial_requirements)
    
    # Display results
    print("✅ Adaptive Research Completed!")
    print("=" * 70)
    print(f"📊 Project: {results['project_plan'].get('project_name', 'N/A')}")
    print(f"🎯 Primary Objective: {results['objectives'].get('primary_objective', 'N/A')}")
    print(f"🔍 Strategy: {results['strategy'].get('strategy_name', 'N/A')}")
    print(f"🌐 Sources Queried: {len(results['collection_plan'].get('sources_to_query', []))}")
    print(f"📁 Data Samples Collected: {len(results['collected_data'].get('data_samples', []))}")
    print(f"⚡ Execution Time: {results['execution_timestamp']}")
    
    print("\n" + "=" * 70)
    print("AI-Driven Adaptive Research System (ADR) - Key Capabilities:")
    print(" 1. Intelligent project planning and initialization")
    print(" 2. Clear objective definition with success criteria")
    print(" 3. Comprehensive strategy formulation")
    print(" 4. Adaptive data collection planning")
    print(" 5. Quality-assured data gathering")
    print(" 6. Integration of all research components")
    
    print("\n✨ The ADR system is ready for complex, multi-domain OSINT investigations!")
    
    return results


if __name__ == "__main__":
    # Run the adaptive research demonstration
    results = asyncio.run(run_adaptive_research_demo())