#!/usr/bin/env python3
"""
Debug script to test the planning phase and see what objectives are generated.
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow
from ai_agent.src.workflow.state import create_initial_state
from ai_agent.src.agents.planning.objective_definition import ObjectiveDefinitionAgent

async def debug_objectives():
    """Debug planning phase to see what objectives are generated."""
    print("=== DEBUGGING PLANNING PHASE ===")
    
    # Create initial state
    state = create_initial_state(
        user_request="Comprehensive OSINT investigation on cybersecurity threats",
        investigation_id="debug-objectives-001"
    )
    
    print(f"Initial state created: {state['investigation_id']}")
    print(f"User request: {state['user_request']}")
    print(f"Initial objectives: {state.get('objectives', 'Not set yet')}")
    
    # Run objective definition agent directly
    agent = ObjectiveDefinitionAgent()
    
    input_data = {
        "user_request": state["user_request"]
    }
    
    print(f"\nInput data to agent: {input_data}")
    
    result = await agent.execute(input_data)
    
    print(f"Agent execution result: success={result.success}")
    print(f"Agent result data: {result.data}")
    print(f"Agent result error: {result.error_message}")
    
    # Now run the full planning phase
    workflow = create_osint_workflow()
    state = await workflow._run_planning_phase(state)
    
    print(f"\nAfter full planning phase:")
    print(f"Objectives: {state.get('objectives', 'Still not set')}")
    print(f"Strategy: {state.get('strategy', 'Not set')}")
    
    return state

if __name__ == "__main__":
    print("Starting debug objectives test...")
    state = asyncio.run(debug_objectives())
    print(f"\nFinal objectives: {state.get('objectives', 'Not set')}")