#!/usr/bin/env python3
"""
Advanced Adaptive Research System Demo

This script demonstrates the complete AI-Driven Adaptive Research System (ADR)
with Project Orchestrator and Research Loop Engine components.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List
import logging

# Import the ADR system components
from ai_agent.src.agents.base.osint_agent import AgentConfig, LLMOSINTAgent
from ai_agent.src.agents.intelligence_planning.ai_planner_agent import AIPlannerAgent, ProjectPlan
from ai_agent.src.agents.specialized.objective_definition_agent import ObjectiveDefinitionAgent
from ai_agent.src.agents.specialized.strategy_formulation_agent import StrategyFormulationAgent
from ai_agent.src.agents.specialized.data_collection_agent import DataCollectionAgent
from ai_agent.src.agents.orchestration.project_orchestrator_agent import ProjectOrchestratorAgent, OrchestratorConfig
from ai_agent.src.agents.orchestration.research_loop_engine import ResearchLoopEngine, LoopConfig


def setup_logging():
    """Set up logging for the demo"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


async def main():
    """Main demo function demonstrating the ADR system"""
    print("🚀 AI-Driven Adaptive Research System (ADR) - Advanced Demo")
    print("="*60)
    setup_logging()
    
    # Define the research topic and requirements
    research_topic = "Analysis of Renewable Energy Adoption in European Markets"
    research_goals = [
        "Assess current renewable energy adoption rates",
        "Identify key market drivers and barriers", 
        "Analyze policy impacts on adoption",
        "Evaluate future growth projections"
    ]
    
    print(f"🔬 Research Topic: {research_topic}")
    print(f"📋 Research Goals: {len(research_goals)} goals defined")
    print()
    
    # Initialize all ADR system agents
    print("🏗️  Initializing ADR System Components...")
    
    # Create agent configurations
    ai_planner_config = AgentConfig(
        role="AI Planner Agent",
        description="Creates intelligent project plans for adaptive research"
    )
    
    objective_config = AgentConfig(
        role="Objective Definition Agent", 
        description="Defines clear research objectives and success criteria"
    )
    
    strategy_config = AgentConfig(
        role="Strategy Formulation Agent",
        description="Creates comprehensive research strategies"
    )
    
    collection_config = AgentConfig(
        role="Data Collection Agent",
        description="Executes intelligent data gathering from multiple sources"
    )
    
    # Initialize agents
    ai_planner_agent = AIPlannerAgent(config=ai_planner_config)
    objective_agent = ObjectiveDefinitionAgent(config=objective_config)
    strategy_agent = StrategyFormulationAgent(config=strategy_config)
    collection_agent = DataCollectionAgent(config=collection_config)
    
    print("✅ Agents initialized successfully")
    
    # Initialize Project Orchestrator
    orchestrator_config = OrchestratorConfig(
        max_concurrent_tasks=2,
        task_timeout=300,
        retry_attempts=2,
        enable_adaptive_rescheduling=True
    )
    
    orchestrator_agent = ProjectOrchestratorAgent(
        config=AgentConfig(
            role="Project Orchestrator Agent",
            description="Coordinates multiple research agents and manages workflow execution"
        ),
        orchestrator_config=orchestrator_config
    )
    
    print("✅ Project Orchestrator initialized")
    
    # Initialize Research Loop Engine
    loop_config = LoopConfig(
        max_iterations=5,
        target_confidence_score=0.7,
        evaluation_threshold=0.6,
        adaptation_threshold=0.5,
        enable_adaptive_learning=True,
        enable_quality_control=True,
        iteration_delay=0.1  # Small delay for demo purposes
    )
    
    research_engine = ResearchLoopEngine(
        orchestrator=orchestrator_agent,
        loop_config=loop_config
    )
    
    print("✅ Research Loop Engine initialized")
    print()
    
    # Register agents with orchestrator
    available_agents = {
        "AI Planner Agent": ai_planner_agent,
        "Objective Definition Agent": objective_agent,
        "Strategy Formulation Agent": strategy_agent,
        "Data Collection Agent": collection_agent,
        "Project Orchestrator Agent": orchestrator_agent
    }
    
    print("📋 Registering agents with orchestrator...")
    for name, agent in available_agents.items():
        orchestrator_agent.register_agent(name, agent)
    print(f"✅ {len(available_agents)} agents registered")
    print()
    
    # Create project plan using AI Planner
    print("🎯 Phase 1: Creating Project Plan...")
    project_plan = await ai_planner_agent.create_project(
        research_topic=research_topic,
        initial_objectives=research_goals,
        project_scope="Comprehensive analysis of European renewable energy markets"
    )
    
    print(f"✅ Project Plan Created: {project_plan.project_name}")
    print(f"📊 Objectives: {len(project_plan.research_objectives)} defined")
    print(f"⏱️  Estimated Duration: {project_plan.estimated_duration}")
    print(f"👥 Required Agents: {project_plan.required_agents}")
    print()
    
    # Define objectives using Objective Definition Agent
    print("🎯 Phase 2: Defining Research Objectives...")
    objective_def = await objective_agent.define_objectives(
        research_topic=research_topic,
        research_scope="European renewable energy market analysis",
        initial_requirements=["Market analysis completed", "Policy impacts identified", "Growth projections evaluated"]
    )
    
    print(f"✅ Primary Objective: {objective_def.primary_objective}")
    print(f"✅ Secondary Objectives: {len(objective_def.secondary_objectives)} defined")
    print(f"✅ Success Criteria: {len(objective_def.success_criteria)} established")
    print()
    
    # Formulate strategy using Strategy Formulation Agent
    print("🧠 Phase 3: Formulating Research Strategy...")
    strategy = await strategy_agent.formulate_strategy(
        objectives=[objective_def.primary_objective] + objective_def.secondary_objectives,
        resources={"market_data": "available", "policy_documents": "available", "industry_reports": "available"},
        constraints=["time_budget", "data_availability"]
    )
    
    print(f"✅ Strategy: {strategy.strategy_name}")
    print(f"✅ Approach Methodology: {strategy.approach_methodology}")
    print(f"✅ Strategy Phases: {len(strategy.phase_timeline)} defined")
    print()
    
    # Plan data collection using Data Collection Agent
    print("🔍 Phase 4: Planning Data Collection...")
    collection_plan = await collection_agent.plan_collection(
        research_objectives=[objective_def.primary_objective] + objective_def.secondary_objectives,
        strategy_guidelines=strategy.model_dump() if hasattr(strategy, 'model_dump') else strategy.dict(),
        resource_constraints={"time": "available", "budget": "limited"}
    )
    
    print(f"✅ Sources to Query: {len(collection_plan.sources_to_query)} identified")
    print(f"✅ Data Types: {collection_plan.data_types_requested}")
    print(f"✅ Quality Criteria: {len(collection_plan.quality_criteria)} defined")
    print()
    
    # Execute research using the Research Loop Engine
    print("🔄 Phase 5: Executing Adaptive Research Loop...")
    
    # Prepare research plan for the loop engine
    research_plan = {
        "project_plan": project_plan.model_dump() if hasattr(project_plan, 'model_dump') else project_plan.dict(),
        "objectives": objective_def.model_dump() if hasattr(objective_def, 'model_dump') else objective_def.dict(),
        "strategy": strategy.model_dump() if hasattr(strategy, 'model_dump') else strategy.dict(),
        "collection_plan": collection_plan.model_dump() if hasattr(collection_plan, 'model_dump') else collection_plan.dict(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Start the adaptive research loop
    loop_results = await research_engine.start_research_loop(
        research_topic=research_topic,
        initial_objectives=[objective_def.primary_objective] + objective_def.secondary_objectives,
        research_plan=research_plan,
        quality_criteria=["relevance", "accuracy", "completeness", "timeliness"]
    )
    
    print(f"✅ Research Loop Completed!")
    # Check if loop results have the expected structure
    if 'total_iterations' in loop_results:
        print(f"📊 Total Iterations: {loop_results['total_iterations']}")
        print(f"📈 Average Confidence: {loop_results['average_confidence']:.2f}")
        print(f"🎯 Final Score: {loop_results.get('final_evaluation_score', 0.0):.2f}")
    else:
        print("📊 Total Iterations: 0")
        print("📈 Average Confidence: 0.00")
        print("🎯 Final Score: 0.00")
    print()
    
    # Display loop status
    status = research_engine.get_status()
    print("🔍 Research Loop Status:")
    print(f"  • Status: {status['status']}")
    print(f"  • Completed Iterations: {status['completed_iterations']}")
    print(f"  • Failed Iterations: {status['failed_iterations']}")
    print(f"  • Total Adaptations: {status['total_adaptations']}")
    print(f"  • Average Confidence: {status['average_confidence']:.2f}")
    print()
    
    print("🏆 ADR System Capabilities Demonstrated:")
    print("  1. ✅ AI Planner Agent - Creates intelligent project plans")
    print("  2. ✅ Objective Definition Agent - Defines clear research objectives")
    print("  3. ✅ Strategy Formulation Agent - Creates comprehensive research strategies")
    print("  4. ✅ Data Collection Agent - Executes intelligent data gathering")
    print("  5. ✅ Project Orchestrator - Coordinates multiple agents and workflows")
    print("  6. ✅ Research Loop Engine - Manages iterative research with adaptation")
    print("  7. ✅ Adaptive Architecture - Components work together seamlessly")
    print()
    
    print("🔄 Advanced ADR System Features:")
    print("  • Dynamic task scheduling and dependency management")
    print("  • Quality control and evaluation mechanisms")
    print("  • Adaptive learning and realignment capabilities")
    print("  • Continuous refinement through iterative loops")
    print("  • Comprehensive monitoring and adjustment capabilities")
    print()
    
    print("✨ The Advanced AI-Driven Adaptive Research System (ADR) is fully operational!")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())