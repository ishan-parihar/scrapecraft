#!/usr/bin/env python3
"""
Test script to verify source link compliance in the enhanced OSINT workflow.
This script specifically tests that all intelligence items have mandatory source links.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow
from ai_agent.src.workflow.state import create_initial_state

async def test_source_compliance():
    """Test that all intelligence items have source links."""
    print("Testing source link compliance...")
    
    # Create initial state
    state = create_initial_state(
        user_request="Research OSINT best practices",
        investigation_id="compliance-test-001"
    )
    
    print(f"Initial state created: {state['investigation_id']}")
    
    # Create workflow instance
    workflow = create_osint_workflow()
    
    print("Running investigation for source compliance test...")
    
    try:
        # Run the investigation
        final_state = await workflow.run_investigation(
            user_request="Research OSINT best practices",
            investigation_id="compliance-test-001"
        )
        
        print(f"Investigation completed with status: {final_state['overall_status']}")
        print(f"Sources used: {len(final_state['sources_used'])}")
        print(f"Errors: {len(final_state['errors'])}")
        
        # Check intelligence data for source link compliance
        if 'intelligence' in final_state:
            intelligence = final_state['intelligence']
            print(f"\nIntelligence structure: {type(intelligence)}")
            
            if isinstance(intelligence, dict):
                print("\nAnalyzing intelligence components:")
                
                # Check key_findings for source links
                if 'key_findings' in intelligence:
                    key_findings = intelligence['key_findings']
                    print(f"Key findings count: {len(key_findings) if isinstance(key_findings, list) else 'N/A'}")
                    if isinstance(key_findings, list):
                        for i, finding in enumerate(key_findings):
                            if isinstance(finding, dict):
                                has_source = 'source_links' in finding or 'source' in finding
                                print(f"  Key finding {i}: {'✓' if has_source else '✗'} (has source: {has_source})")
                
                # Check insights for source links
                if 'insights' in intelligence:
                    insights = intelligence['insights']
                    print(f"Insights count: {len(insights) if isinstance(insights, list) else 'N/A'}")
                    if isinstance(insights, list):
                        for i, insight in enumerate(insights):
                            if isinstance(insight, dict):
                                has_source = 'source_links' in insight or 'source' in insight
                                print(f"  Insight {i}: {'✓' if has_source else '✗'} (has source: {has_source})")
                
                # Check recommendations for source links
                if 'recommendations' in intelligence:
                    recommendations = intelligence['recommendations']
                    print(f"Recommendations count: {len(recommendations) if isinstance(recommendations, list) else 'N/A'}")
                    if isinstance(recommendations, list):
                        for i, recommendation in enumerate(recommendations):
                            if isinstance(recommendation, dict):
                                has_source = 'source_links' in recommendation or 'source' in recommendation
                                print(f"  Recommendation {i}: {'✓' if has_source else '✗'} (has source: {has_source})")
                
                # Check strategic_implications for source links
                if 'strategic_implications' in intelligence:
                    strategic_implications = intelligence['strategic_implications']
                    print(f"Strategic implications count: {len(strategic_implications) if isinstance(strategic_implications, list) else 'N/A'}")
                    if isinstance(strategic_implications, list):
                        for i, implication in enumerate(strategic_implications):
                            if isinstance(implication, dict):
                                has_source = 'source_links' in implication or 'source' in implication
                                print(f"  Strategic implication {i}: {'✓' if has_source else '✗'} (has source: {has_source})")
                
                # Calculate source link compliance percentage
                total_items = 0
                items_with_sources = 0
                
                for category in ['key_findings', 'insights', 'recommendations', 'strategic_implications']:
                    if category in intelligence and isinstance(intelligence[category], list):
                        category_items = intelligence[category]
                        for item in category_items:
                            if isinstance(item, dict):
                                total_items += 1
                                has_source = 'source_links' in item or 'source' in item
                                if has_source:
                                    items_with_sources += 1
                
                compliance_rate = (items_with_sources / total_items * 100) if total_items > 0 else 0
                print(f"\nSource link compliance: {items_with_sources}/{total_items} items ({compliance_rate:.1f}%)")
                
                if compliance_rate >= 90:
                    print("✅ Source link compliance achieved (90%+ requirement met)")
                else:
                    print(f"❌ Source link compliance NOT met (requirement: 90%, actual: {compliance_rate:.1f}%)")
                
                return compliance_rate >= 90
        
        return False
        
    except Exception as e:
        print(f"Error during investigation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting source link compliance test...")
    success = asyncio.run(test_source_compliance())
    if success:
        print("\n✅ Source compliance test passed!")
    else:
        print("\n❌ Source compliance test failed!")
        sys.exit(1)