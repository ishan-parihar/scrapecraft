#!/usr/bin/env python3
"""
Debug script to test the data collection flow and see where URLs are being collected.
"""
import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow
from ai_agent.src.workflow.state import create_initial_state

async def debug_collection():
    """Debug collection phase to see what's happening with URL collection."""
    print("=== DEBUGGING COLLECTION PHASE ===")
    
    # Create initial state
    state = create_initial_state(
        user_request="Comprehensive OSINT investigation on cybersecurity threats",
        investigation_id="debug-test-001"
    )
    
    print(f"Initial state created: {state['investigation_id']}")
    print(f"Initial confidence level: {state['confidence_level']}")
    print(f"Initial sources used: {len(state['sources_used'])}")
    
    # Create workflow instance
    workflow = create_osint_workflow()
    
    print("\nRunning planning phase...")
    # Run planning phase
    state = await workflow._run_planning_phase(state)
    print(f"After planning - sources used: {len(state['sources_used'])}")
    
    print("\nRunning search coordination...")
    # Run search coordination node directly
    from ai_agent.src.workflow.graph import search_coordination_node
    state = await search_coordination_node(state)
    print(f"After search coordination - sources used: {len(state['sources_used'])}")
    print(f"Search coordination results: {state.get('search_coordination_results', {})}")
    
    print("\nRunning data collection...")
    # Run data collection node directly
    from ai_agent.src.workflow.graph import data_collection_node
    state = await data_collection_node(state)
    print(f"After data collection - sources used: {len(state['sources_used'])}")
    print(f"Raw data: {state.get('raw_data', {})}")
    print(f"Search results: {state.get('search_results', {})}")
    print(f"Sources used: {state['sources_used']}")
    
    return state

if __name__ == "__main__":
    print("Starting debug collection test...")
    state = asyncio.run(debug_collection())
    print(f"\nFinal sources used: {len(state['sources_used'])}")
    print(f"Sources: {state['sources_used']}")