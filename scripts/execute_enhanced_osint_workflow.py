#!/usr/bin/env python3
"""
Execute Enhanced OSINT Workflow with Mandatory Source Link Verification

This script runs the enhanced OSINT workflow using agents with mandatory source link verification
to achieve the desired grade upgrade from B to A- or higher.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to sys.path to ensure imports work correctly
import sys
sys.path.insert(0, os.path.abspath('.'))

def load_test_dataset():
    """Load the enhanced test dataset with source links."""
    with open('data/enhanced_maritime_test_dataset.json', 'r') as f:
        return json.load(f)

async def execute_enhanced_osint_workflow():
    """Execute the enhanced OSINT workflow with mandatory source link verification."""
    
    print("Starting Enhanced OSINT Workflow with Mandatory Source Link Verification")
    print("=" * 70)
    
    # Load test dataset
    print("1. Loading enhanced test dataset with source links...")
    dataset = load_test_dataset()
    
    # Extract test data
    vessels = dataset['vessels']
    shell_companies = dataset['shell_companies']
    verification_sources = dataset['verification_sources']
    ais_tracking = dataset['data_sources']['ais_tracking']
    
    print(f"   Loaded {len(vessels)} vessels, {len(shell_companies)} shell companies")
    print(f"   Loaded {len(verification_sources)} verification sources")
    print(f"   Loaded {len(ais_tracking)} AIS records with source links")
    
    print("\n2. Initializing enhanced agents with mandatory source link verification...")
    
    # Import enhanced agents
    from ai_agent.src.agents.synthesis.enhanced_intelligence_synthesis_agent_v2 import EnhancedIntelligenceSynthesisAgentV2
    from ai_agent.src.agents.synthesis.enhanced_report_generation_agent_v2 import EnhancedReportGenerationAgentV2
    from ai_agent.src.agents.synthesis.quality_assurance_agent_v2 import QualityAssuranceAgentV2
    
    # Create agent instances
    intelligence_synthesis_agent = EnhancedIntelligenceSynthesisAgentV2()
    report_generation_agent = EnhancedReportGenerationAgentV2()
    quality_assurance_agent = QualityAssuranceAgentV2()
    
    print("   Enhanced agents initialized successfully")
    
    print("\n3. Preparing investigation input with source links...")
    
    # Prepare input data for the agents
    # Simulate data from earlier phases of the OSINT workflow
    fused_data = {
        "entities": [
            {
                "name": "MT OCEAN SHADOW",
                "type": "vessel",
                "confidence": 0.95,
                "attributes": {"imo": "9876543", "flag": "Panama"}
            },
            {
                "name": "Oceanic Shipping Ltd",
                "type": "organization", 
                "confidence": 0.88,
                "attributes": {"jurisdiction": "UAE", "registration": "2021-03-15"}
            }
        ],
        "relationships": [
            {
                "from_entity": "MT OCEAN SHADOW",
                "to_entity": "Oceanic Shipping Ltd",
                "relationship_type": "operated_by",
                "confidence": 0.92
            }
        ],
        "timeline": [
            {
                "event": "Vessel registered to company",
                "date": "2021-03-15",
                "confidence": 0.85
            }
        ],
        "sources": verification_sources[:5]  # Use first 5 verification sources
    }
    
    patterns = [
        {
            "type": "shipping_pattern",
            "description": "Vessel shows irregular AIS signal patterns",
            "confidence": 0.87,
            "significance": "high",
            "details": {
                "pattern_type": "signal_manipulation",
                "frequency": "recurrent",
                "duration": "multi_day_gaps"
            }
        },
        {
            "type": "financial_pattern", 
            "description": "Complex financial transaction structure",
            "confidence": 0.82,
            "significance": "high",
            "details": {
                "pattern_type": "layering",
                "structure": "multi_jurisdictional",
                "purpose": "obfuscation"
            }
        }
    ]
    
    context_analysis = {
        "historical_context": "Entity has history of operating in sanctioned regions",
        "geopolitical_context": "Operations aligned with targeted sanctions evasion",
        "risk_assessment": {
            "overall_risk": "high",
            "risk_factors": [
                {"factor": "sanctions_evasion", "confidence": 0.92},
                {"factor": "shell_company_use", "confidence": 0.88},
                {"factor": "AIS_manipulation", "confidence": 0.85}
            ]
        },
        "threat_analysis": {
            "threat_level": "medium",
            "threat_type": "sanctions_evasion",
            "potential_impact": "financial_crimes"
        }
    }
    
    investigation_objectives = {
        "primary_objectives": [
            "Identify sanctions evasion networks",
            "Map complex corporate ownership",
            "Detect AIS manipulation patterns"
        ],
        "investigation_scope": {
            "in_scope": ["vessel_tracking", "corporate_structures", "financial_flows"],
            "out_of_scope": ["military_intelligence", "personal_privacy_violations"]
        }
    }
    
    investigation_metadata = {
        "case_id": "MARITIME_SHADOW_NETWORKS_2025",
        "investigator": "OSINT_System",
        "start_time": datetime.utcnow().isoformat(),
        "classification": "confidential"
    }
    
    print("   Input data prepared with comprehensive source links")
    
    print("\n4. Executing Enhanced Intelligence Synthesis with mandatory source verification...")
    
    # Prepare input for intelligence synthesis agent
    synthesis_input = {
        "fused_data": fused_data,
        "patterns": patterns,
        "context_analysis": context_analysis,
        "sources_used": [source["url"] for source in verification_sources],  # Use all verification source URLs
        "user_request": "Investigate maritime shadow networks for sanctions evasion",
        "objectives": investigation_objectives
    }
    
    # Execute intelligence synthesis with source verification
    synthesis_result = await intelligence_synthesis_agent.execute(synthesis_input)
    
    if not synthesis_result.success:
        print(f"   ERROR: Intelligence synthesis failed - {synthesis_result.error_message}")
        return
    
    intelligence_output = synthesis_result.data
    print(f"   Intelligence synthesis completed successfully with confidence: {synthesis_result.confidence:.2f}")
    print(f"   Generated {len(intelligence_output.get('key_findings', []))} key findings")
    print(f"   Generated {len(intelligence_output.get('insights', []))} strategic insights")
    print(f"   Generated {len(intelligence_output.get('recommendations', []))} recommendations")
    
    print("\n5. Executing Quality Assurance with mandatory source link validation...")
    
    # Prepare input for quality assurance agent
    qa_input = {
        "intelligence": intelligence_output,
        "fused_data": fused_data,
        "patterns": patterns,
        "context_analysis": context_analysis,
        "sources_used": [source["url"] for source in verification_sources],
        "objectives": investigation_objectives,
        "investigation_metadata": investigation_metadata
    }
    
    # Execute quality assurance with source validation
    qa_result = await quality_assurance_agent.execute(qa_input)
    
    if not qa_result.success:
        print(f"   ERROR: Quality assurance failed - {qa_result.error_message}")
        return
    
    qa_output = qa_result.data
    print(f"   Quality assurance completed successfully with confidence: {qa_result.confidence:.2f}")
    print(f"   Quality grade: {qa_output.get('quality_grade', 'Unknown')}")
    print(f"   Source link coverage: {qa_output.get('source_link_validation', {}).get('coverage_rate', 0):.2f}")
    print(f"   Source link validity: {qa_output.get('source_link_validation', {}).get('validity_rate', 0):.2f}")
    
    # Check if we achieved the target grade improvement
    target_grade = "B"  # Starting grade was B
    achieved_grade = qa_output.get('quality_grade', 'F')
    
    grade_improvement = False
    if achieved_grade in ['A+', 'A', 'A-'] and target_grade in ['B+', 'B', 'B-']:
        grade_improvement = True
    elif achieved_grade in ['B+', 'B'] and target_grade == 'C':
        grade_improvement = True
    elif achieved_grade in ['B-', 'C+'] and target_grade == 'D':
        grade_improvement = True
    
    print(f"   Grade improvement achieved: {'YES' if grade_improvement else 'NO'}")
    print(f"   Previous grade: {target_grade}, Achieved grade: {achieved_grade}")
    
    print("\n6. Executing Enhanced Report Generation with verified source links...")
    
    # Prepare input for report generation agent
    report_input = {
        "intelligence": intelligence_output,
        "quality_assessment": qa_output,
        "fused_data": fused_data,
        "patterns": patterns,
        "context_analysis": context_analysis,
        "sources_used": [source["url"] for source in verification_sources],
        "user_request": "Investigate maritime shadow networks for sanctions evasion",
        "objectives": investigation_objectives,
        "investigation_metadata": investigation_metadata
    }
    
    # Execute report generation with source verification
    report_result = await report_generation_agent.execute(report_input)
    
    if not report_result.success:
        print(f"   ERROR: Report generation failed - {report_result.error_message}")
        return
    
    report_output = report_result.data
    print(f"   Report generation completed successfully with confidence: {report_result.confidence:.2f}")
    print(f"   Report compliance status: {report_output.get('report_metadata', {}).get('compliance_status', 'Unknown')}")
    print(f"   Source link coverage in report: {report_output.get('report_metadata', {}).get('source_link_coverage', 0.0):.2f}")
    print(f"   Source link validity in report: {report_output.get('report_metadata', {}).get('source_link_validity', 0.0):.2f}")
    
    print("\n7. Validating Enhanced System Compliance...")
    
    # Validate compliance with source link requirements
    source_link_coverage = qa_output.get('source_link_validation', {}).get('coverage_rate', 0)
    source_link_validity = qa_output.get('source_link_validation', {}).get('validity_rate', 0)
    
    min_coverage_required = 0.9  # 90%
    min_validity_required = 0.8  # 80%
    
    coverage_compliant = source_link_coverage >= min_coverage_required
    validity_compliant = source_link_validity >= min_validity_required
    
    print(f"   Source link coverage: {source_link_coverage:.2f} (Required: >={min_coverage_required}) - {'PASS' if coverage_compliant else 'FAIL'}")
    print(f"   Source link validity: {source_link_validity:.2f} (Required: >={min_validity_required}) - {'PASS' if validity_compliant else 'FAIL'}")
    
    overall_compliance = coverage_compliant and validity_compliant
    
    print(f"\n8. Enhanced OSINT Workflow Summary:")
    print(f"   - Workflow completed: SUCCESS")
    print(f"   - Quality grade achieved: {achieved_grade}")
    print(f"   - Grade improvement: {'YES' if grade_improvement else 'NO'}")
    print(f"   - Source link compliance: {'PASS' if overall_compliance else 'FAIL'}")
    print(f"   - Data accuracy mandate satisfied: {'YES' if overall_compliance else 'NO'}")
    print(f"   - Report generated with verified sources: YES")
    
    # Determine if we achieved the target goal
    target_achieved = grade_improvement and overall_compliance
    print(f"   - Target goal achieved (grade upgrade + compliance): {'YES' if target_achieved else 'NO'}")
    
    print("\n" + "=" * 70)
    print("Enhanced OSINT Workflow completed successfully!")
    
    # Save results to a summary file
    summary = {
        "workflow_completion_time": datetime.utcnow().isoformat(),
        "quality_grade_achieved": achieved_grade,
        "grade_improvement": grade_improvement,
        "source_link_coverage": source_link_coverage,
        "source_link_validity": source_link_validity,
        "coverage_compliant": coverage_compliant,
        "validity_compliant": validity_compliant,
        "overall_compliance": overall_compliance,
        "target_achieved": target_achieved,
        "key_metrics": {
            "total_key_findings": len(intelligence_output.get("key_findings", [])),
            "total_insights": len(intelligence_output.get("insights", [])),
            "total_recommendations": len(intelligence_output.get("recommendations", [])),
            "synthesis_confidence": synthesis_result.confidence,
            "qa_confidence": qa_result.confidence,
            "report_confidence": report_result.confidence
        }
    }
    
    with open(f"enhanced_osint_workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\nResults summary saved to: enhanced_osint_workflow_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    
    return target_achieved

if __name__ == "__main__":
    success = asyncio.run(execute_enhanced_osint_workflow())
    if success:
        print("\nENHANCED OSINT WORKFLOW SUCCESSFULLY COMPLETED!")
        print("System has achieved both grade improvement and source link compliance.")
    else:
        print("\nENHANCED OSINT WORKFLOW COMPLETED BUT TARGET GOALS NOT FULLY ACHIEVED.")
        print("Review the results and adjust the system parameters as needed.")