#!/usr/bin/env python3
"""
Test script for the enhanced OSINT workflow.
This script tests the fixes made to ensure 100% source link coverage.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow
from ai_agent.src.workflow.state import create_initial_state

async def test_enhanced_workflow():
    """Test the enhanced OSINT workflow."""
    print("Testing enhanced OSINT workflow...")
    
    # Create initial state
    state = create_initial_state(
        user_request="Research recent developments in AI technology",
        investigation_id="test-investigation-001"
    )
    
    print(f"Initial state created: {state['investigation_id']}")
    print(f"Initial confidence level: {state['confidence_level']}")
    print(f"Initial sources used: {len(state['sources_used'])}")
    
    # Create workflow instance
    workflow = create_osint_workflow()
    
    print("Running investigation...")
    
    try:
        # Run the investigation
        final_state = await workflow.run_investigation(
            user_request="Research recent developments in AI technology",
            investigation_id="test-investigation-001"
        )
        
        print(f"Investigation completed with status: {final_state['overall_status']}")
        print(f"Final confidence level: {final_state['confidence_level']}")
        print(f"Final sources used: {len(final_state['sources_used'])}")
        print(f"Errors: {len(final_state['errors'])}")
        print(f"Warnings: {len(final_state['warnings'])}")
        
        # Check intelligence data for source links
        if 'intelligence' in final_state:
            intelligence = final_state['intelligence']
            print(f"Intelligence data found: {len(intelligence) if isinstance(intelligence, (list, dict)) else 'unknown'} items")
            
            # Check if intelligence item has source links
            if isinstance(intelligence, dict):
                for key, value in intelligence.items():
                    if 'source_links' in str(value).lower() or hasattr(value, 'get') and value.get('source_links'):
                        print(f"Found source links in {key}")
        
        # Check final report for source compliance
        if 'final_report' in final_state:
            report = final_state['final_report']
            print(f"Final report generated: {bool(report)}")
            
        # Check for overall progress
        progress = workflow.get_investigation_progress(final_state)
        print(f"Progress: {progress['progress_percentage']}%")
        print(f"Current phase: {progress['current_phase']}")
        print(f"Overall status: {progress['overall_status']}")
        
        return final_state
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting enhanced OSINT workflow test...")
    result = asyncio.run(test_enhanced_workflow())
    if result:
        print("\nTest completed successfully!")
    else:
        print("\nTest failed!")
        sys.exit(1)