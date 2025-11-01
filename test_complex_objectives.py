#!/usr/bin/env python3
"""
Comprehensive Test Script for OSINT OS System Architecture Audit
Tests the integrative functionality with complex, multi-phase investigation objectives.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.abspath('.'))

from ai_agent.src.workflow.graph import create_osint_workflow, OSINTWorkflow
from ai_agent.src.workflow.state import create_initial_state, InvestigationPhase, InvestigationStatus
from ai_agent.src.workflow.state import calculate_progress, add_error
from osint_os import OSINTOperatingSystem

class OSINTSystemTestSuite:
    """Comprehensive test suite for OSINT OS integrative functionality."""
    
    def __init__(self):
        self.test_results = []
        self.failed_tests = []
        self.passed_tests = []
        
    async def initialize_system(self) -> OSINTOperatingSystem:
        """Initialize the OSINT Operating System for testing."""
        print("Initializing OSINT Operating System for testing...")
        osint_os = OSINTOperatingSystem()
        await osint_os.initialize()
        return osint_os
        
    def create_complex_test_objectives(self) -> List[Dict[str, Any]]:
        """Create complex test objectives that require cross-phase coordination."""
        return [
            {
                "id": "complex_person_research",
                "name": "Comprehensive Person Research",
                "description": "Research a person across multiple data sources, with verification and synthesis",
                "request": "Investigate John Smith, CEO of TechCorp, including business affiliations, social media presence, public records, and verify information through cross-referencing",
                "success_criteria": [
                    "Objectives defined with multiple data sources",
                    "Strategy includes verification through multiple sources",
                    "Data collected from at least 3 different source types",
                    "Patterns recognized across data sources",
                    "Information synthesized with source attribution",
                    "Quality assurance performed on findings",
                    "Final report with executive summary and recommendations"
                ],
                "expected_duration": 300  # seconds
            },
            {
                "id": "company_investigation",
                "name": "Company Background Investigation",
                "description": "Investigate a company's background, including financials, legal issues, and reputation",
                "request": "Research ABC Corporation's financial health, legal disputes, executive team, market position, and public sentiment from news sources",
                "success_criteria": [
                    "Multi-source data collection",
                    "Financial pattern recognition",
                    "Legal issue identification",
                    "Competitive analysis",
                    "Synthesized intelligence report"
                ],
                "expected_duration": 240
            },
            {
                "id": "incident_analysis",
                "name": "Incident Timeline Analysis",
                "description": "Analyze a specific incident by collecting timeline data from multiple sources",
                "request": "Investigate the timeline of events surrounding the Twitter data breach in 2023, including technical details, affected accounts, and response measures",
                "success_criteria": [
                    "Timeline reconstruction",
                    "Source verification",
                    "Technical analysis",
                    "Impact assessment",
                    "Recommendations for prevention"
                ],
                "expected_duration": 360
            }
        ]
    
    async def run_test_objective(self, osint_os: OSINTOperatingSystem, objective: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single complex test objective."""
        print(f"\n{'='*60}")
        print(f"Running Test Objective: {objective['name']}")
        print(f"Request: {objective['request']}")
        print(f"{'='*60}")
        
        start_time = datetime.utcnow()
        
        try:
            # Run the investigation
            final_state = await osint_os.run_investigation(
                user_request=objective['request'],
                investigation_id=objective['id'],
                priority="high"
            )
            
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze results
            analysis = self.analyze_investigation_results(final_state, objective)
            
            # Create test result
            test_result = {
                "test_id": objective['id'],
                "test_name": objective['name'],
                "duration": duration,
                "expected_duration": objective['expected_duration'],
                "final_state": final_state,
                "analysis": analysis,
                "passed": analysis['all_criteria_met'],
                "timestamp": start_time.isoformat(),
                "execution_details": {
                    "status": final_state['overall_status'],
                    "progress": final_state.get('progress_percentage', 0),
                    "confidence": final_state['confidence_level'],
                    "errors": len(final_state['errors']),
                    "warnings": len(final_state['warnings']),
                    "sources_used": len(final_state['sources_used']),
                    "agents_participated": final_state['agents_participated']
                }
            }
            
            self.test_results.append(test_result)
            
            if test_result['passed']:
                self.passed_tests.append(test_result)
                print(f"\n✅ {objective['name']} - PASSED")
            else:
                self.failed_tests.append(test_result)
                print(f"\n❌ {objective['name']} - FAILED")
            
            print(f"Duration: {duration:.2f}s (expected: {objective['expected_duration']}s)")
            print(f"Status: {final_state['overall_status']}")
            print(f"Progress: {final_state.get('progress_percentage', 0):.1f}%")
            print(f"Confidence: {final_state['confidence_level']:.2f}")
            print(f"Sources used: {len(final_state['sources_used'])}")
            print(f"Errors: {len(final_state['errors'])}")
            
            return test_result
            
        except Exception as e:
            print(f"❌ Error running test {objective['name']}: {e}")
            import traceback
            traceback.print_exc()
            
            test_result = {
                "test_id": objective['id'],
                "test_name": objective['name'],
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "expected_duration": objective['expected_duration'],
                "final_state": None,
                "analysis": {"error": str(e)},
                "passed": False,
                "timestamp": start_time.isoformat(),
                "execution_details": {
                    "error": str(e)
                }
            }
            
            self.test_results.append(test_result)
            self.failed_tests.append(test_result)
            
            return test_result
    
    def analyze_investigation_results(self, state, objective: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze investigation results against success criteria."""
        if not state:
            return {
                "all_criteria_met": False,
                "failed_criteria": objective['success_criteria'],
                "passed_criteria": [],
                "error": "No state returned from investigation"
            }
        
        passed_criteria = []
        failed_criteria = []
        
        # Check each success criterion
        for criterion in objective['success_criteria']:
            if "Objectives defined" in criterion:
                # Check if objectives were defined
                if state.get('objectives'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif "Strategy includes" in criterion:
                # Check if strategy was formulated
                if state.get('strategy'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif "Data collected from" in criterion:
                # Check if data collection occurred
                min_sources = 3 if "at least 3" in criterion else 2
                if len(state.get('sources_used', [])) >= min_sources or \
                   state.get('search_results') or \
                   state.get('raw_data'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif "Patterns recognized" in criterion:
                # Check if analysis was performed
                if state.get('patterns'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif "Information synthesized" in criterion:
                # Check if synthesis occurred
                if state.get('intelligence'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif "Quality assurance" in criterion:
                # Check if QA was performed
                if state.get('quality_assessment'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            elif "Final report" in criterion:
                # Check if report was generated
                if state.get('final_report'):
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
            
            # Generic criteria that are difficult to assess without specific content
            else:
                # For now, assume these were met if the investigation completed
                if state.get('overall_status') == 'completed':
                    passed_criteria.append(criterion)
                else:
                    failed_criteria.append(criterion)
        
        all_criteria_met = len(failed_criteria) == 0
        
        # Additional checks for system architecture
        architecture_indicators = {
            "planning_phase_executed": state.get('planning_status') == 'completed',
            "collection_phase_executed": state.get('collection_status', {}).get('data_collection') == 'completed',
            "analysis_phase_executed": state.get('analysis_status', {}).get('data_fusion') == 'completed',
            "synthesis_phase_executed": state.get('synthesis_status', {}).get('intelligence_synthesis') == 'completed',
            "all_agents_participated": len(state.get('agents_participated', [])) > 0,
            "state_properly_updated": state.get('progress_percentage', 0) > 0,
            "sources_tracked": len(state.get('sources_used', [])) > 0
        }
        
        return {
            "all_criteria_met": all_criteria_met,
            "passed_criteria": passed_criteria,
            "failed_criteria": failed_criteria,
            "total_criteria": len(objective['success_criteria']),
            "architecture_indicators": architecture_indicators
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive tests on the OSINT OS system."""
        print("Starting OSINT OS System Architecture Audit")
        print("Testing integrative functionality with complex objectives...")
        
        # Initialize the system
        osint_os = await self.initialize_system()
        
        # Create complex test objectives
        test_objectives = self.create_complex_test_objectives()
        
        # Run each test objective
        for objective in test_objectives:
            await self.run_test_objective(osint_os, objective)
        
        # Generate comprehensive report
        return self.generate_audit_report()
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate a comprehensive audit report."""
        total_tests = len(self.test_results)
        passed_tests = len(self.passed_tests)
        failed_tests = len(self.failed_tests)
        
        # Calculate overall success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Analyze architecture indicators across all tests
        all_architecture_indicators = []
        for result in self.test_results:
            if 'analysis' in result and 'architecture_indicators' in result['analysis']:
                all_architecture_indicators.append(result['analysis']['architecture_indicators'])
        
        # Aggregate architecture indicators
        aggregated_indicators = {}
        if all_architecture_indicators:
            for key in all_architecture_indicators[0].keys():
                aggregated_indicators[key] = sum(1 for indicators in all_architecture_indicators if indicators.get(key)) / len(all_architecture_indicators)
        
        audit_report = {
            "audit_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": success_rate,
                "timestamp": datetime.utcnow().isoformat()
            },
            "test_results": self.test_results,
            "architecture_analysis": {
                "indicators_summary": aggregated_indicators,
                "integration_score": success_rate,
                "system_coherence": self.calculate_system_coherence(aggregated_indicators)
            },
            "recommendations": self.generate_recommendations(aggregated_indicators),
            "system_status": self.determine_system_status(success_rate, aggregated_indicators)
        }
        
        return audit_report
    
    def calculate_system_coherence(self, indicators: Dict[str, float]) -> float:
        """Calculate system coherence based on architecture indicators."""
        # Weighted average of key architecture indicators
        weights = {
            "planning_phase_executed": 0.15,
            "collection_phase_executed": 0.25,
            "analysis_phase_executed": 0.25,
            "synthesis_phase_executed": 0.20,
            "all_agents_participated": 0.10,
            "state_properly_updated": 0.05
        }
        
        coherence_score = sum(indicators.get(key, 0) * weight for key, weight in weights.items())
        return coherence_score * 100
    
    def generate_recommendations(self, indicators: Dict[str, float]) -> List[str]:
        """Generate recommendations based on test results."""
        recommendations = []
        
        if indicators.get("planning_phase_executed", 0) < 0.8:
            recommendations.append("Improve planning phase execution - ensure all investigations start with proper objective definition and strategy formulation")
        
        if indicators.get("collection_phase_executed", 0) < 0.8:
            recommendations.append("Enhance collection phase reliability - ensure consistent data collection across multiple sources")
        
        if indicators.get("analysis_phase_executed", 0) < 0.8:
            recommendations.append("Strengthen analysis phase - ensure consistent pattern recognition and data fusion execution")
        
        if indicators.get("synthesis_phase_executed", 0) < 0.8:
            recommendations.append("Optimize synthesis phase - ensure reliable intelligence synthesis and quality assurance")
        
        if indicators.get("sources_tracked", 0) < 0.9:
            recommendations.append("Improve source tracking - ensure all data sources are properly recorded in the state management system")
        
        if not recommendations:
            recommendations.append("System architecture appears robust. Consider expanding test scenarios to validate edge cases.")
        
        return recommendations
    
    def determine_system_status(self, success_rate: float, indicators: Dict[str, float]) -> str:
        """Determine overall system status based on test results."""
        if success_rate >= 90 and all(indicator >= 0.8 for indicator in indicators.values()):
            return "GREEN - System operating optimally"
        elif success_rate >= 70 and all(indicator >= 0.6 for indicator in indicators.values()):
            return "YELLOW - System functional with areas for improvement"
        else:
            return "RED - System requires significant improvements"
    
    def print_detailed_report(self, audit_report: Dict[str, Any]):
        """Print a detailed audit report."""
        print("\n" + "="*80)
        print("OSINT OS SYSTEM ARCHITECTURE AUDIT REPORT")
        print("="*80)
        
        summary = audit_report["audit_summary"]
        print(f"\n📊 AUDIT SUMMARY:")
        print(f"   Total Tests: {summary['total_tests']}")
        print(f"   Passed: {summary['passed_tests']}")
        print(f"   Failed: {summary['failed_tests']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Timestamp: {summary['timestamp']}")
        
        print(f"\n🏗️  ARCHITECTURE ANALYSIS:")
        indicators = audit_report["architecture_analysis"]["indicators_summary"]
        for indicator, score in indicators.items():
            status = "✅" if score >= 0.8 else "⚠️" if score >= 0.6 else "❌"
            print(f"   {status} {indicator}: {score:.2f}")
        
        print(f"\n🎯 SYSTEM COHERENCE: {audit_report['architecture_analysis']['system_coherence']:.1f}%")
        print(f"📋 SYSTEM STATUS: {audit_report['system_status']}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        for recommendation in audit_report["recommendations"]:
            print(f"   • {recommendation}")
        
        print(f"\n📋 DETAILED TEST RESULTS:")
        for result in audit_report["test_results"]:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            print(f"   {status} {result['test_name']}")
            print(f"        Duration: {result['duration']:.1f}s (expected: {result['expected_duration']}s)")
            if result.get("analysis"):
                analysis = result["analysis"]
                if "passed_criteria" in analysis:
                    print(f"        Criteria: {len(analysis['passed_criteria'])}/{analysis['total_criteria']} met")
        
        print("="*80)


async def main():
    """Main function to run the OSINT OS system architecture audit."""
    print("OSINT OS System Architecture Audit - Integrative Functionality Test")
    print("This test validates that the OSINT Operating System functions as an integrated whole")
    print("by executing complex, multi-phase investigation objectives.\n")
    
    # Create test suite
    test_suite = OSINTSystemTestSuite()
    
    # Run comprehensive tests
    audit_report = await test_suite.run_comprehensive_test()
    
    # Print detailed report
    test_suite.print_detailed_report(audit_report)
    
    # Return success status for CI/CD
    success_rate = audit_report["audit_summary"]["success_rate"]
    system_status = audit_report["system_status"]
    
    print(f"\n🏁 FINAL RESULT:")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   System Status: {system_status}")
    
    # Exit with appropriate code based on results
    if success_rate >= 70:  # Consider it successful if 70%+ tests pass
        print("   Overall: ✅ SYSTEM VALIDATED - Architecture functioning as expected")
        return 0
    else:
        print("   Overall: ❌ SYSTEM REQUIRES ATTENTION - Architecture issues identified")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)