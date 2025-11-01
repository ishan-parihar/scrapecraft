#!/usr/bin/env python3
"""
Execute Person Research OSINT Workflow with Mandatory Source Link Verification

This script runs the enhanced OSINT workflow using the proper workflow graph 
to research "Ishan Parihar" in "Noida" with mandatory source link verification
to ensure all intelligence outputs have verifiable sources.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to sys.path to ensure imports work correctly
import sys
sys.path.insert(0, os.path.abspath('.'))

async def execute_person_research_workflow():
    """Execute the person research OSINT workflow with mandatory source link verification."""
    
    print("Starting Person Research OSINT Workflow with Mandatory Source Link Verification")
    print("=" * 80)
    
    print("\n1. Initializing proper OSINT workflow graph...")
    
    # Import the proper workflow graph and state management
    from ai_agent.src.workflow.graph import create_osint_workflow
    from ai_agent.src.workflow.state import create_initial_state, InvestigationPhase, InvestigationStatus
    
    # Create the workflow instance
    workflow = create_osint_workflow()
    
    print("   OSINT workflow graph initialized successfully")
    
    print("\n2. Setting up person research parameters...")
    
    # Define the person research request
    user_request = "Research Ishan Parihar who lives in Noida"
    print(f"   Research target: {user_request}")
    
    # Create initial investigation state for person research
    state = create_initial_state(
        user_request=user_request,
        investigation_id=f"PERSON_RESEARCH_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        investigation_type="person_research",
        target_name="Ishan Parihar",
        target_location="Noida",
        privacy_compliance=True,
        data_retention_policy="30_days"
    )
    
    print("   Person research parameters configured")
    
    print("\n3. Executing comprehensive person research workflow...")
    
    try:
        # Execute the complete investigation workflow
        final_state = await workflow.run_investigation(
            user_request=user_request,
            investigation_id=state["investigation_id"]
        )
        
        print(f"   Investigation completed with status: {final_state['overall_status'].value}")
        
        print("\n4. Processing investigation results...")
        
        # Get investigation progress and results
        progress = workflow.get_investigation_progress(final_state)
        
        print(f"   Investigation ID: {progress['investigation_id']}")
        print(f"   Current Phase: {progress['current_phase']}")
        print(f"   Overall Status: {progress['overall_status']}")
        print(f"   Progress: {progress['progress_percentage']:.1f}%")
        print(f"   Errors: {progress['errors_count']}")
        print(f"   Warnings: {progress['warnings_count']}")
        print(f"   Sources Used: {progress['sources_used']}")
        print(f"   Confidence: {progress['confidence_level']:.2f}")
        
        # Extract key results
        final_report = final_state.get("final_report", {})
        intelligence = final_state.get("intelligence", {})
        
        print(f"   Generated {len(intelligence.get('key_findings', []))} key findings")
        print(f"   Generated {len(intelligence.get('insights', []))} strategic insights")
        print(f"   Generated {len(intelligence.get('recommendations', []))} recommendations")
        
        print("\n5. Validating source link compliance...")
        
        # Check source link compliance
        quality_assessment = final_state.get("quality_assessment", {})
        source_validation = quality_assessment.get("source_link_validation", {})
        
        source_link_coverage = source_validation.get("coverage_rate", 0.0)
        source_link_validity = source_validation.get("validity_rate", 0.0)
        
        min_coverage_required = 0.9  # 90%
        min_validity_required = 0.8  # 80%
        
        coverage_compliant = source_link_coverage >= min_coverage_required
        validity_compliant = source_link_validity >= min_validity_required
        overall_compliance = coverage_compliant and validity_compliant
        
        print(f"   Source link coverage: {source_link_coverage:.2f} (Required: >={min_coverage_required}) - {'PASS' if coverage_compliant else 'FAIL'}")
        print(f"   Source link validity: {source_link_validity:.2f} (Required: >={min_validity_required}) - {'PASS' if validity_compliant else 'FAIL'}")
        print(f"   Overall compliance: {'YES' if overall_compliance else 'NO'}")
        
        print("\n6. Person Research Workflow Summary:")
        print(f"   - Workflow completed: {'SUCCESS' if final_state['overall_status'] == InvestigationStatus.COMPLETED else 'FAILED'}")
        print(f"   - Target achieved: {final_state['overall_status'] == InvestigationStatus.COMPLETED}")
        print(f"   - Source link compliance: {'PASS' if overall_compliance else 'FAIL'}")
        print(f"   - Data accuracy mandate satisfied: {'YES' if overall_compliance else 'NO'}")
        
        # Check if report was generated
        report_generated = bool(final_report)
        print(f"   - Report generated: {'YES' if report_generated else 'NO'}")
        
        print("\n" + "=" * 80)
        print("Person Research OSINT Workflow completed!")
        
        # Save results to a summary file
        from ai_agent.src.agents.synthesis.enhanced_report_generation_agent_v2 import EnhancedReportGenerationAgentV2
        report_agent = EnhancedReportGenerationAgentV2()
        
        # Generate a summary of the person research
        summary_data = {
            "workflow_completion_time": datetime.utcnow().isoformat(),
            "investigation_id": progress['investigation_id'],
            "user_request": user_request,
            "target_name": "Ishan Parihar",
            "target_location": "Noida",
            "overall_status": progress['overall_status'],
            "progress_percentage": progress['progress_percentage'],
            "confidence_level": progress['confidence_level'],
            "sources_used_count": progress['sources_used'],
            "key_findings_count": len(intelligence.get('key_findings', [])),
            "insights_count": len(intelligence.get('insights', [])),
            "recommendations_count": len(intelligence.get('recommendations', [])),
            "source_link_coverage": source_link_coverage,
            "source_link_validity": source_link_validity,
            "coverage_compliant": coverage_compliant,
            "validity_compliant": validity_compliant,
            "overall_compliance": overall_compliance,
            "target_achieved": final_state['overall_status'] == InvestigationStatus.COMPLETED
        }
        
        summary_filename = f"person_research_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_filename, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"\nResults summary saved to: {summary_filename}")
        
        # Also save the detailed report if available
        if final_report:
            report_filename = f"person_research_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_filename, 'w') as f:
                json.dump(final_report, f, indent=2)
            print(f"Detailed report saved to: {report_filename}")
        
        return overall_compliance and final_state['overall_status'] == InvestigationStatus.COMPLETED
        
    except Exception as e:
        print(f"   ERROR: Person research workflow failed - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(execute_person_research_workflow())
    if success:
        print("\nPERSON RESEARCH OSINT WORKFLOW SUCCESSFULLY COMPLETED!")
        print("System has achieved both target research and source link compliance.")
    else:
        print("\nPERSON RESEARCH OSINT WORKFLOW COMPLETED BUT TARGET GOALS NOT FULLY ACHIEVED.")
        print("Review the results and adjust the system parameters as needed.")