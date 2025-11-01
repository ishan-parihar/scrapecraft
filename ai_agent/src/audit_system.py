"""
OSINT System Audit Tool

Comprehensive audit system that generates structured outputs and logs
for proper system validation and performance assessment.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

from utils.output_manager import get_output_manager
from agents.synthesis.intelligence_synthesis_agent import IntelligenceSynthesisAgent
from agents.synthesis.quality_assurance_agent import QualityAssuranceAgent
from agents.synthesis.report_generation_agent import ReportGenerationAgent


class OSINTSystemAuditor:
    """
    Comprehensive OSINT system auditor with structured output generation.
    """
    
    def __init__(self):
        """Initialize the auditor."""
        self.output_manager = get_output_manager()
        self.logger = self.output_manager.logger
        self.audit_results = {}
        
    async def run_comprehensive_audit(self, case_id: str = "maritime_shadow_networks") -> Dict[str, Any]:
        """
        Run comprehensive audit with full output generation and logging.
        
        Args:
            case_id: Case ID for the audit
            
        Returns:
            Complete audit results with all outputs saved
        """
        
        self.logger.info(f"Starting comprehensive OSINT system audit - Case: {case_id}")
        
        # Initialize audit tracking
        audit_start_time = time.time()
        self.audit_results = {
            "case_id": case_id,
            "audit_start_time": datetime.utcnow().isoformat(),
            "test_scenario": "Maritime Shadow Networks - Complex制裁 evasion investigation",
            "phases": {},
            "overall_results": {},
            "output_files": {}
        }
        
        # Create complex test data
        investigation_data = self.create_complex_test_data()
        
        try:
            # Phase 1: Intelligence Synthesis
            intel_result = await self.execute_intelligence_synthesis(investigation_data)
            if not intel_result["success"]:
                raise Exception(f"Intelligence synthesis failed: {intel_result.get('error')}")
            
            # Phase 2: Quality Assurance
            qa_result = await self.execute_quality_assurance(intel_result, investigation_data)
            if not qa_result["success"]:
                raise Exception(f"Quality assurance failed: {qa_result.get('error')}")
            
            # Phase 3: Report Generation
            report_result = await self.execute_report_generation(
                intel_result, qa_result, investigation_data
            )
            if not report_result["success"]:
                raise Exception(f"Report generation failed: {report_result.get('error')}")
            
            # Compile complete investigation results
            complete_results = self.compile_investigation_results(
                investigation_data, intel_result, qa_result, report_result
            )
            
            # Save complete investigation report
            report_file = self.output_manager.save_investigation_report(
                complete_results, case_id
            )
            
            # Calculate final metrics
            audit_end_time = time.time()
            total_execution_time = audit_end_time - audit_start_time
            
            final_metrics = self.calculate_final_metrics(
                intel_result, qa_result, report_result, total_execution_time
            )
            
            # Save audit summary
            audit_summary = self.create_audit_summary(final_metrics, complete_results)
            self.save_audit_summary(audit_summary, case_id)
            
            self.logger.info(f"Comprehensive audit completed successfully - Case: {case_id}")
            
            return {
                "success": True,
                "case_id": case_id,
                "final_metrics": final_metrics,
                "report_file": report_file,
                "complete_results": complete_results,
                "audit_summary": audit_summary
            }
            
        except Exception as e:
            self.logger.error(f"Audit failed: {str(e)}")
            return {
                "success": False,
                "case_id": case_id,
                "error": str(e),
                "partial_results": self.audit_results
            }
    
    async def execute_intelligence_synthesis(self, investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute intelligence synthesis phase with full logging."""
        self.logger.info("Executing Intelligence Synthesis phase")
        phase_start_time = time.time()
        
        try:
            agent = IntelligenceSynthesisAgent()
            
            input_data = {
                'fused_data': investigation_data['fused_data'],
                'patterns': investigation_data['patterns'],
                'context_analysis': investigation_data['context_analysis'],
                'user_request': investigation_data['user_request'],
                'objectives': investigation_data['objectives']
            }
            
            result = await agent.execute(input_data)
            execution_time = time.time() - phase_start_time
            
            # Log execution
            self.output_manager.log_agent_execution(
                agent_name="IntelligenceSynthesisAgent",
                input_data=input_data,
                output_data=result.data if result.success else {},
                execution_time=execution_time,
                success=result.success,
                error_message=result.error_message if not result.success else None
            )
            
            phase_result = {
                "success": result.success,
                "confidence": result.confidence,
                "execution_time": execution_time,
                "data": result.data if result.success else None,
                "error": result.error_message if not result.success else None
            }
            
            self.audit_results["phases"]["intelligence_synthesis"] = phase_result
            
            return phase_result
            
        except Exception as e:
            execution_time = time.time() - phase_start_time
            self.output_manager.log_agent_execution(
                agent_name="IntelligenceSynthesisAgent",
                input_data={},
                output_data={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def execute_quality_assurance(self, intel_result: Dict[str, Any], investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute quality assurance phase with full logging."""
        self.logger.info("Executing Quality Assurance phase")
        phase_start_time = time.time()
        
        try:
            agent = QualityAssuranceAgent()
            
            input_data = {
                'intelligence': intel_result["data"],
                'fused_data': investigation_data['fused_data'],
                'patterns': investigation_data['patterns'],
                'context_analysis': investigation_data['context_analysis'],
                'sources_used': investigation_data['sources_used'],
                'user_request': investigation_data['user_request']
            }
            
            result = await agent.execute(input_data)
            execution_time = time.time() - phase_start_time
            
            # Log execution
            self.output_manager.log_agent_execution(
                agent_name="QualityAssuranceAgent",
                input_data=input_data,
                output_data=result.data if result.success else {},
                execution_time=execution_time,
                success=result.success,
                error_message=result.error_message if not result.success else None
            )
            
            phase_result = {
                "success": result.success,
                "confidence": result.confidence,
                "execution_time": execution_time,
                "data": result.data if result.success else None,
                "error": result.error_message if not result.success else None
            }
            
            self.audit_results["phases"]["quality_assurance"] = phase_result
            
            return phase_result
            
        except Exception as e:
            execution_time = time.time() - phase_start_time
            self.output_manager.log_agent_execution(
                agent_name="QualityAssuranceAgent",
                input_data={},
                output_data={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    async def execute_report_generation(
        self, 
        intel_result: Dict[str, Any], 
        qa_result: Dict[str, Any], 
        investigation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute report generation phase with full logging."""
        self.logger.info("Executing Report Generation phase")
        phase_start_time = time.time()
        
        try:
            agent = ReportGenerationAgent()
            
            input_data = {
                'intelligence': intel_result["data"],
                'quality_assessment': qa_result["data"],
                'fused_data': investigation_data['fused_data'],
                'patterns': investigation_data['patterns'],
                'context_analysis': investigation_data['context_analysis'],
                'sources_used': investigation_data['sources_used'],
                'user_request': investigation_data['user_request'],
                'objectives': investigation_data['objectives'],
                'investigation_metadata': investigation_data['investigation_metadata']
            }
            
            result = await agent.execute(input_data)
            execution_time = time.time() - phase_start_time
            
            # Log execution
            self.output_manager.log_agent_execution(
                agent_name="ReportGenerationAgent",
                input_data=input_data,
                output_data=result.data if result.success else {},
                execution_time=execution_time,
                success=result.success,
                error_message=result.error_message if not result.success else None
            )
            
            phase_result = {
                "success": result.success,
                "confidence": result.confidence,
                "execution_time": execution_time,
                "data": result.data if result.success else None,
                "error": result.error_message if not result.success else None
            }
            
            self.audit_results["phases"]["report_generation"] = phase_result
            
            return phase_result
            
        except Exception as e:
            execution_time = time.time() - phase_start_time
            self.output_manager.log_agent_execution(
                agent_name="ReportGenerationAgent",
                input_data={},
                output_data={},
                execution_time=execution_time,
                success=False,
                error_message=str(e)
            )
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time
            }
    
    def create_complex_test_data(self) -> Dict[str, Any]:
        """Create complex test data for audit."""
        return {
            'user_request': '''Investigate potential制裁 evasion network involving vessels operating in the Indo-Pacific region. Focus on identifying:
            1. Vessels engaged in suspicious AIS manipulation patterns
            2. Shell companies and ownership structures
            3. Key personnel and network connections
            4. Financial flows and money laundering patterns
            5. Geopolitical implications and risk assessment
            Timeline: January 2022 - December 2024''',
            
            'objectives': {
                'primary_objective': 'Identify and map制裁 evasion maritime network',
                'secondary_objectives': [
                    'Trace financial flows and money laundering patterns',
                    'Identify key personnel and beneficial owners',
                    'Assess geopolitical implications',
                    'Provide actionable intelligence for interdiction'
                ]
            },
            
            'fused_data': {
                'entities': [
                    {
                        'name': 'MV Ocean Spirit',
                        'type': 'vessel',
                        'confidence': 0.95,
                        'sources': ['ais_data', 'port_records', 'satellite_imagery'],
                        'attributes': {
                            'imo_number': '9876543',
                            'flag': 'Panama',
                            'owner': 'Global Shipping LLC',
                            'suspicious_patterns': ['ais_gaps', 'flag_hopping']
                        }
                    },
                    {
                        'name': 'Global Shipping LLC',
                        'type': 'company',
                        'confidence': 0.92,
                        'sources': ['corporate_registry', 'financial_records'],
                        'attributes': {
                            'jurisdiction': 'Marshall Islands',
                            'incorporation_date': '2021-03-15'
                        }
                    },
                    {
                        'name': 'Chen Wei',
                        'type': 'person',
                        'confidence': 0.88,
                        'sources': ['social_media', 'corporate_records'],
                        'attributes': {
                            'nationality': 'Singaporean',
                            'role': 'Shipping Manager'
                        }
                    }
                ],
                'relationships': [
                    {
                        'source': 'MV Ocean Spirit',
                        'target': 'Global Shipping LLC',
                        'type': 'owned_by',
                        'confidence': 0.94,
                        'evidence': ['registration_documents']
                    },
                    {
                        'source': 'Chen Wei',
                        'target': 'Global Shipping LLC',
                        'type': 'employed_by',
                        'confidence': 0.87,
                        'evidence': ['corporate_records']
                    }
                ],
                'timeline': [
                    {
                        'date': '2022-01-15',
                        'event': 'Global Shipping LLC incorporated',
                        'sources': ['corporate_registry'],
                        'significance': 'high'
                    }
                ]
            },
            
            'patterns': [
                {
                    'type': 'ais_manipulation_pattern',
                    'description': 'Systematic AIS signal gaps detected',
                    'confidence': 0.93,
                    'significance': 'high'
                },
                {
                    'type': 'shell_company_chain_pattern',
                    'description': 'Multi-layered corporate structure',
                    'confidence': 0.89,
                    'significance': 'high'
                }
            ],
            
            'context_analysis': {
                'historical_context': 'Increased制裁 enforcement since 2021',
                'geopolitical_context': 'Great power competition in Indo-Pacific',
                'risk_assessment': {
                    'overall_risk': 'critical',
                    'threat_level': 9.2,
                    'confidence': 0.94
                }
            },
            
            'sources_used': [
                'ais_data_providers', 'satellite_imagery', 'corporate_registries',
                'financial_intelligence_units', 'sanctions_databases'
            ],
            
            'investigation_metadata': {
                'case_id': 'MSN-2024-001',
                'start_time': '2024-01-01T00:00:00Z',
                'investigator': 'OSINT System Audit Team',
                'classification': 'secret',
                'priority': 'high'
            }
        }
    
    def compile_investigation_results(
        self, 
        investigation_data: Dict[str, Any],
        intel_result: Dict[str, Any],
        qa_result: Dict[str, Any],
        report_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compile complete investigation results."""
        
        return {
            "case_id": investigation_data['investigation_metadata']['case_id'],
            "user_request": investigation_data['user_request'],
            "objectives": investigation_data['objectives'],
            "investigation_metadata": investigation_data['investigation_metadata'],
            "sources_used": investigation_data['sources_used'],
            "fused_data": investigation_data['fused_data'],
            "patterns": investigation_data['patterns'],
            "context_analysis": investigation_data['context_analysis'],
            "intelligence": intel_result["data"],
            "quality_assessment": qa_result["data"],
            "final_report": report_result["data"]["primary_report"],
            "alternative_formats": report_result["data"]["alternative_formats"],
            "report_metadata": report_result["data"]["report_metadata"],
            "overall_status": "completed",
            "phase_results": {
                "intelligence_synthesis": {
                    "success": intel_result["success"],
                    "confidence": intel_result["confidence"],
                    "execution_time": intel_result["execution_time"]
                },
                "quality_assurance": {
                    "success": qa_result["success"],
                    "confidence": qa_result["confidence"],
                    "execution_time": qa_result["execution_time"]
                },
                "report_generation": {
                    "success": report_result["success"],
                    "confidence": report_result["confidence"],
                    "execution_time": report_result["execution_time"]
                }
            }
        }
    
    def calculate_final_metrics(
        self, 
        intel_result: Dict[str, Any],
        qa_result: Dict[str, Any],
        report_result: Dict[str, Any],
        total_execution_time: float
    ) -> Dict[str, Any]:
        """Calculate final performance metrics."""
        
        avg_confidence = (intel_result["confidence"] + qa_result["confidence"] + report_result["confidence"]) / 3
        
        # Determine grade
        if avg_confidence >= 0.9:
            grade = 'A+ (Exceptional)'
        elif avg_confidence >= 0.85:
            grade = 'A (Excellent)'
        elif avg_confidence >= 0.8:
            grade = 'B+ (Very Good)'
        elif avg_confidence >= 0.75:
            grade = 'B (Good)'
        elif avg_confidence >= 0.7:
            grade = 'C+ (Satisfactory)'
        elif avg_confidence >= 0.6:
            grade = 'C (Acceptable)'
        else:
            grade = 'D (Needs Improvement)'
        
        return {
            "average_confidence": avg_confidence,
            "grade": grade,
            "total_execution_time": total_execution_time,
            "phase_confidence_scores": {
                "intelligence_synthesis": intel_result["confidence"],
                "quality_assurance": qa_result["confidence"],
                "report_generation": report_result["confidence"]
            },
            "phase_execution_times": {
                "intelligence_synthesis": intel_result["execution_time"],
                "quality_assurance": qa_result["execution_time"],
                "report_generation": report_result["execution_time"]
            },
            "all_phases_successful": all([
                intel_result["success"], 
                qa_result["success"], 
                report_result["success"]
            ])
        }
    
    def create_audit_summary(self, metrics: Dict[str, Any], results: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive audit summary."""
        
        return {
            "audit_summary": {
                "case_id": results["case_id"],
                "audit_timestamp": datetime.utcnow().isoformat(),
                "test_scenario": "Maritime Shadow Networks - Complex制裁 evasion investigation",
                "overall_performance": {
                    "score": metrics["average_confidence"],
                    "grade": metrics["grade"],
                    "execution_time": metrics["total_execution_time"],
                    "all_phases_successful": metrics["all_phases_successful"]
                },
                "key_findings": {
                    "entities_identified": len(results["fused_data"]["entities"]),
                    "relationships_found": len(results["fused_data"]["relationships"]),
                    "patterns_detected": len(results["patterns"]),
                    "sources_analyzed": len(results["sources_used"]),
                    "report_sections_generated": len(results["final_report"])
                },
                "quality_assessment": {
                    "overall_quality_score": results["quality_assessment"]["overall_quality_score"],
                    "quality_grade": results["quality_assessment"]["quality_grade"],
                    "source_verification_rate": results["quality_assessment"]["source_verification"]["verification_rate"],
                    "fact_accuracy_rate": results["quality_assessment"]["fact_checking"]["accuracy_rate"]
                },
                "intelligence_output": {
                    "executive_summary_length": len(results["intelligence"]["executive_summary"]),
                    "key_findings_count": len(results["intelligence"]["key_findings"]),
                    "insights_count": len(results["intelligence"]["insights"])
                },
                "production_readiness": {
                    "ready_for_production": metrics["average_confidence"] >= 0.75,
                    "recommended_improvements": self.get_improvement_recommendations(metrics, results)
                }
            }
        }
    
    def get_improvement_recommendations(self, metrics: Dict[str, Any], results: Dict[str, Any]) -> list:
        """Get improvement recommendations based on results."""
        recommendations = []
        
        if metrics["phase_confidence_scores"]["quality_assurance"] < 0.8:
            recommendations.append("Enhance quality assurance processes and threshold calibration")
        
        if results["quality_assessment"]["fact_checking"]["accuracy_rate"] < 0.7:
            recommendations.append("Improve fact accuracy verification algorithms")
        
        if metrics["phase_confidence_scores"]["report_generation"] < 0.8:
            recommendations.append("Optimize report generation confidence and quality")
        
        if metrics["total_execution_time"] > 60:
            recommendations.append("Optimize processing time for better performance")
        
        return recommendations if recommendations else ["System performing well, continue monitoring"]
    
    def save_audit_summary(self, audit_summary: Dict[str, Any], case_id: str):
        """Save audit summary to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        audit_file = self.output_manager.audit_dir / f"{case_id}_audit_summary_{timestamp}.json"
        
        with open(audit_file, 'w', encoding='utf-8') as f:
            json.dump(audit_summary, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Audit summary saved: {audit_file}")


async def main():
    """Main audit execution function."""
    auditor = OSINTSystemAuditor()
    
    print("🔍 Starting Comprehensive OSINT System Audit")
    print("=" * 60)
    
    result = await auditor.run_comprehensive_audit("maritime_shadow_networks_audit")
    
    if result["success"]:
        print("\n✅ AUDIT COMPLETED SUCCESSFULLY")
        print(f"📊 Final Performance Score: {result['final_metrics']['average_confidence']:.2f}")
        print(f"🏅 Performance Grade: {result['final_metrics']['grade']}")
        print(f"📄 Report File: {result['report_file']}")
        print(f"⏱️  Total Execution Time: {result['final_metrics']['total_execution_time']:.2f}s")
        
        # Show output locations
        print(f"\n📁 Output Files Generated:")
        print(f"   Reports: {auditor.output_manager.reports_dir}")
        print(f"   Logs: {auditor.output_manager.logs_dir}")
        print(f"   Audit Trail: {auditor.output_manager.audit_dir}")
        
        # Show latest reports
        latest_reports = auditor.output_manager.get_latest_reports(3)
        if latest_reports:
            print(f"\n📋 Latest Reports:")
            for report in latest_reports:
                print(f"   - {report['name']} ({report['size']} bytes, {report['modified']})")
    else:
        print(f"\n❌ AUDIT FAILED: {result['error']}")


if __name__ == "__main__":
    asyncio.run(main())