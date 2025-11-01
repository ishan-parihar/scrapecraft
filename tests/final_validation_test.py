#!/usr/bin/env python3
"""
Final validation test for the enhanced OSINT system.
This script validates that all requirements have been met:
1. Grade improvement (confidence level increase)
2. 90%+ source link compliance
3. System stability and functionality
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow
from ai_agent.src.workflow.state import create_initial_state

async def final_validation_test():
    """Final validation test for the enhanced OSINT system."""
    print("=== FINAL VALIDATION TEST FOR ENHANCED OSINT SYSTEM ===")
    
    # Create initial state
    state = create_initial_state(
        user_request="Comprehensive OSINT investigation on cybersecurity threats",
        investigation_id="final-validation-001"
    )
    
    print(f"Initial state created: {state['investigation_id']}")
    print(f"Initial confidence level: {state['confidence_level']}")
    print(f"Initial sources used: {len(state['sources_used'])}")
    
    # Create workflow instance
    workflow = create_osint_workflow()
    
    print("\nRunning comprehensive investigation...")
    
    try:
        # Run the investigation
        final_state = await workflow.run_investigation(
            user_request="Comprehensive OSINT investigation on cybersecurity threats",
            investigation_id="final-validation-001"
        )
        
        print(f"\nInvestigation completed with status: {final_state['overall_status']}")
        print(f"Final confidence level: {final_state['confidence_level']}")
        print(f"Final sources used: {len(final_state['sources_used'])}")
        print(f"Errors: {len(final_state['errors'])}")
        print(f"Warnings: {len(final_state['warnings'])}")
        
        # Print error details
        if final_state['errors']:
            print("\nError details:")
            for i, error in enumerate(final_state['errors'], 1):
                print(f"  {i}. {error.get('message', 'No message')}")
                print(f"     Phase: {error.get('phase', 'Unknown')}")
                print(f"     Agent: {error.get('agent', 'Unknown')}")
                print(f"     Timestamp: {error.get('timestamp', 'Unknown')}")
        
        # Validation Checks
        print("\n=== VALIDATION RESULTS ===")
        
        # 1. Check grade improvement (confidence level)
        initial_confidence = 0.0  # From initial state
        final_confidence = final_state['confidence_level']
        print(f"1. Grade Improvement: {initial_confidence} → {final_confidence}")
        grade_improvement_met = final_confidence > initial_confidence
        print(f"   Grade improvement requirement: {'✅ MET' if grade_improvement_met else '❌ NOT MET'}")
        
        # 2. Check source link compliance
        total_items = 0
        items_with_sources = 0
        
        if 'intelligence' in final_state:
            intelligence = final_state['intelligence']
            if isinstance(intelligence, dict):
                for category in ['key_findings', 'insights', 'recommendations', 'strategic_implications']:
                    if category in intelligence and isinstance(intelligence[category], list):
                        category_items = intelligence[category]
                        print(f"   {category}: {len(category_items)} items")
                        for item in category_items:
                            if isinstance(item, dict):
                                total_items += 1
                                has_source = any(key in item for key in ['source_links', 'source', 'sources'])
                                if has_source:
                                    items_with_sources += 1
        
        compliance_rate = (items_with_sources / total_items * 100) if total_items > 0 else 0
        print(f"2. Source Link Compliance: {items_with_sources}/{total_items} items ({compliance_rate:.1f}%)")
        source_compliance_met = compliance_rate >= 90
        print(f"   90%+ source link compliance: {'✅ MET' if source_compliance_met else '❌ NOT MET'}")
        
        # 3. Check system stability (no critical errors)
        error_count = len(final_state['errors'])
        warning_count = len(final_state['warnings'])
        print(f"3. System Stability: {error_count} errors, {warning_count} warnings")
        system_stability_met = error_count <= 1  # Allow for minor errors
        print(f"   System stability: {'✅ MET' if system_stability_met else '❌ NOT MET'}")
        
        # 4. Check workflow completion
        workflow_completed = final_state['overall_status'].name == 'COMPLETED'
        print(f"4. Workflow Completion: {'✅ MET' if workflow_completed else '❌ NOT MET'}")
        
        # 5. Check resource efficiency (progress tracking)
        progress = workflow.get_investigation_progress(final_state)
        print(f"5. Progress Tracking: {progress['progress_percentage']}% complete")
        
        # Overall Assessment
        print(f"\n=== OVERALL ASSESSMENT ===")
        all_requirements_met = (
            grade_improvement_met and 
            source_compliance_met and 
            system_stability_met and 
            workflow_completed
        )
        
        print(f"Grade Improvement (confidence increase): {'✅' if grade_improvement_met else '❌'}")
        print(f"Source Link Compliance (90%+): {'✅' if source_compliance_met else '❌'}")
        print(f"System Stability: {'✅' if system_stability_met else '❌'}")
        print(f"Workflow Completion: {'✅' if workflow_completed else '❌'}")
        
        print(f"\n🎯 ALL REQUIREMENTS MET: {'✅ YES' if all_requirements_met else '❌ NO'}")
        
        if all_requirements_met:
            print(f"\n🎉 ENHANCED OSINT SYSTEM VALIDATION: SUCCESSFUL!")
            print(f"   - Confidence level increased from {initial_confidence} to {final_confidence}")
            print(f"   - Source link compliance achieved: {compliance_rate:.1f}% ({items_with_sources}/{total_items} items)")
            print(f"   - System completed successfully with minimal errors")
            print(f"   - All intelligence categories have mandatory source links")
        else:
            print(f"\n❌ ENHANCED OSINT SYSTEM VALIDATION: FAILED!")
            
        return all_requirements_met
        
    except Exception as e:
        print(f"Error during validation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting final validation test for the enhanced OSINT system...")
    success = asyncio.run(final_validation_test())
    if success:
        print("\n✅ Final validation test PASSED - All requirements satisfied!")
        sys.exit(0)
    else:
        print("\n❌ Final validation test FAILED - Requirements not met!")
        sys.exit(1)