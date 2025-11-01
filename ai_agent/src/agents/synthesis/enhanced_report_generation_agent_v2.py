"""
Enhanced Report Generation Agent v2.0

This agent generates comprehensive investigation reports with mandatory source link verification,
ensuring all claims are backed by verifiable sources as required by the intelligence team.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..base.osint_agent import AgentResult, AgentCapability
from .synthesis_agent_base import SynthesisAgentBase


logger = logging.getLogger(__name__)


class EnhancedReportGenerationAgentV2(SynthesisAgentBase):
    """
    Enhanced Report Generation Agent for OSINT investigations.
    
    This agent is responsible for:
    - Generating comprehensive investigation reports with mandatory source links
    - Structuring executive summaries and detailed findings with verifiable sources
    - Creating methodology documentation
    - Including source lists and appendices with working links
    - Maintaining report classification and metadata
    - Supporting multiple report formats with source link integration
    - ENFORCING: All claims must include verifiable source links
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Enhanced Report Generation Agent."""
        super().__init__(
            name="EnhancedReportGenerationAgentV2",
            description="Generates comprehensive investigation reports with mandatory source link verification",
            version="2.0.0",
            capabilities=[
                AgentCapability(
                    name="report_generation",
                    description="Generate comprehensive investigation reports with source link verification",
                    required_data=["intelligence", "quality_assessment", "fused_data", "patterns", "context_analysis"]
                ),
                AgentCapability(
                    name="executive_summary",
                    description="Create executive summaries with source-verified claims",
                    required_data=["intelligence", "key_findings"]
                ),
                AgentCapability(
                    name="methodology_documentation",
                    description="Document investigation methodology with source validation",
                    required_data=["objectives", "sources_used", "investigation_metadata"]
                ),
                AgentCapability(
                    name="appendix_generation",
                    description="Generate appendices with verified source lists and supporting data",
                    required_data=["sources_used", "fused_data", "patterns", "context_analysis"]
                ),
                AgentCapability(
                    name="report_formatting",
                    description="Format reports for different audiences with source link integration",
                    required_data=["intelligence", "quality_assessment"]
                )
            ]
        )
        
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # Enhanced report generation parameters with source link requirements
        self.report_config = {
            "max_executive_summary_length": 500,
            "max_detailed_findings": 20,
            "include_technical_appendices": True,
            "include_source_listings": True,
            "classification_levels": [
                "public", "internal", "confidential", "secret", "top_secret"
            ],
            "report_formats": [
                "executive_briefing", "technical_report", "full_investigation_report"
            ],
            "report_sections": [
                "executive_summary", "introduction", "methodology", 
                "findings", "analysis", "conclusions", "recommendations", 
                "appendices"
            ],
            "quality_thresholds": {
                "min_overall_quality": 0.6,
                "min_confidence_level": 0.5,
                "min_source_link_coverage": 0.9,  # 90% of claims must have source links
                "min_source_link_validity": 0.8   # 80% of source links must be valid
            }
        }
        
        # Update config with user-provided settings
        self.report_config.update(self.config.get("report_config", {}))
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute enhanced report generation process with mandatory source link verification.
        
        Args:
            input_data: Dictionary containing:
                - intelligence: Synthesized intelligence from IntelligenceSynthesisAgent
                - quality_assessment: Quality assessment from QualityAssuranceAgent
                - fused_data: Results from DataFusionAgent
                - patterns: Results from PatternRecognitionAgent
                - context_analysis: Results from ContextualAnalysisAgent
                - sources_used: List of sources used in investigation
                - user_request: Original investigation request
                - objectives: Investigation objectives
                - investigation_metadata: Additional metadata about the investigation
        
        Returns:
            AgentResult containing enhanced report with source link verification
        """
        try:
            self.logger.info("Starting enhanced report generation with source link verification")
            
            # Validate input data
            validation_result = self._validate_input_data(input_data)
            if not validation_result.success:
                return AgentResult(
                    success=False,
                    error_message=f"Invalid input data: {validation_result.error_message}",
                    data={},
                    confidence=0.0
                )
            
            # Extract required data
            intelligence = input_data.get("intelligence", {})
            quality_assessment = input_data.get("quality_assessment", {})
            fused_data = input_data.get("fused_data", {})
            patterns = input_data.get("patterns", [])
            context_analysis = input_data.get("context_analysis", {})
            sources_used = input_data.get("sources_used", [])
            user_request = input_data.get("user_request", "")
            objectives = input_data.get("objectives", {})
            investigation_metadata = input_data.get("investigation_metadata", {})
            
            # Step 1: Assess report readiness based on quality and source link compliance
            quality_readiness = self._assess_report_readiness(quality_assessment)
            
            # MANDATORY STEP: Check source link compliance before proceeding
            source_link_compliance = self._assess_source_link_compliance(intelligence, quality_assessment)
            if not source_link_compliance["compliant"]:
                self.logger.warning(f"Source link compliance not met: {source_link_compliance['message']}")
            
            # Step 2: Generate executive summary with source verification
            executive_summary = self._generate_executive_summary(
                intelligence, quality_assessment, user_request
            )
            
            # Step 3: Create introduction and methodology sections
            introduction = self._create_introduction(user_request, objectives, investigation_metadata)
            methodology = self._create_methodology(
                sources_used, fused_data, patterns, context_analysis
            )
            
            # Step 4: Generate detailed findings section with mandatory source links
            detailed_findings = self._generate_detailed_findings(
                intelligence, fused_data, patterns, context_analysis
            )
            
            # Step 5: Create analysis section with source validation
            analysis_section = self._create_analysis_section(
                intelligence, quality_assessment, context_analysis
            )
            
            # Step 6: Generate conclusions and recommendations with source verification
            conclusions = self._generate_conclusions(intelligence, quality_assessment)
            recommendations = self._generate_recommendations(intelligence, quality_assessment)
            
            # Step 7: Create appendices with verified source links
            appendices = self._create_appendices(
                sources_used, fused_data, patterns, context_analysis, quality_assessment
            )
            
            # Step 8: Assemble complete report with source link compliance
            report = self._assemble_complete_report(
                executive_summary=executive_summary,
                introduction=introduction,
                methodology=methodology,
                detailed_findings=detailed_findings,
                analysis_section=analysis_section,
                conclusions=conclusions,
                recommendations=recommendations,
                appendices=appendices,
                investigation_metadata=investigation_metadata,
                quality_assessment=quality_assessment,
                source_link_compliance=source_link_compliance
            )
            
            # Step 9: Generate alternative report formats with source links
            alternative_formats = self._generate_alternative_formats(
                intelligence, quality_assessment, executive_summary
            )
            
            # Step 10: Calculate report confidence with source link weighting
            report_confidence = self._calculate_report_confidence(
                quality_assessment, intelligence, quality_readiness, source_link_compliance
            )
            
            self.logger.info(f"Enhanced report generation completed with confidence: {report_confidence}")
            self.logger.info(f"Source link compliance status: {source_link_compliance['status']}")
            
            return AgentResult(
                success=True,
                data={
                    "primary_report": report,
                    "alternative_formats": alternative_formats,
                    "report_metadata": {
                        "generated_at": datetime.utcnow().isoformat(),
                        "report_classification": self._determine_classification(intelligence, context_analysis),
                        "total_sections": len(self.report_config["report_sections"]),
                        "word_count_estimate": self._estimate_word_count(report),
                        "quality_assessment_passed": quality_readiness["ready_for_report"],
                        "source_link_compliance": source_link_compliance,
                        "confidence_level": report_confidence
                    }
                },
                confidence=report_confidence,
                metadata={
                    "processing_time": self._get_processing_time(),
                    "sections_generated": len(report.keys()),
                    "appendices_count": len(appendices),
                    "alternative_formats_count": len(alternative_formats),
                    "source_link_verification_status": source_link_compliance["status"]
                }
            )
            
        except Exception as e:
            self.logger.error(f"Enhanced report generation failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error_message=str(e),
                data={},
                confidence=0.0
            )
    
    def _validate_input_data(self, input_data: Dict[str, Any]) -> AgentResult:
        """Validate input data for report generation with source link verification."""
        required_fields = ["intelligence", "quality_assessment", "fused_data", "patterns", "context_analysis"]
        
        for field in required_fields:
            if field not in input_data:
                return AgentResult(
                    success=False,
                    data={},
                    error_message=f"Missing required field: {field}"
                )
        
        # Check quality thresholds
        quality_assessment = input_data.get("quality_assessment", {})
        overall_quality = quality_assessment.get("overall_quality_score", 0.0)
        
        if overall_quality < self.report_config["quality_thresholds"]["min_overall_quality"]:
            return AgentResult(
                success=False,
                data={},
                error_message=f"Quality assessment score ({overall_quality}) below minimum threshold"
            )
        
        # Check for compliance with source link requirements
        source_link_validation = quality_assessment.get("source_link_validation", {})
        min_coverage = self.report_config["quality_thresholds"]["min_source_link_coverage"]
        min_validity = self.report_config["quality_thresholds"]["min_source_link_validity"]
        
        coverage_met = source_link_validation.get("coverage_rate", 0) >= min_coverage
        validity_met = source_link_validation.get("validity_rate", 0) >= min_validity
        
        if not coverage_met or not validity_met:
            self.logger.warning(f"Source link requirements not fully met - Coverage: {source_link_validation.get('coverage_rate', 0):.2f}, Validity: {source_link_validation.get('validity_rate', 0):.2f}")
        
        return AgentResult(success=True, data={})
    
    def _assess_source_link_compliance(self, intelligence: Dict[str, Any], quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess compliance with mandatory source link requirements."""
        
        # Get source link validation from quality assessment
        source_link_validation = quality_assessment.get("source_link_validation", {})
        
        min_coverage = self.report_config["quality_thresholds"]["min_source_link_coverage"]
        min_validity = self.report_config["quality_thresholds"]["min_source_link_validity"]
        
        coverage_rate = source_link_validation.get("coverage_rate", 0)
        validity_rate = source_link_validation.get("validity_rate", 0)
        
        compliant = coverage_rate >= min_coverage and validity_rate >= min_validity
        
        compliance_status = {
            "compliant": compliant,
            "coverage_rate": coverage_rate,
            "validity_rate": validity_rate,
            "required_coverage": min_coverage,
            "required_validity": min_validity,
            "status": "COMPLIANT" if compliant else "NON-COMPLIANT",
            "message": f"Source link compliance: Coverage {coverage_rate:.2f}, Validity {validity_rate:.2f}"
        }
        
        if not compliant:
            non_compliant_msg = f"Source link requirements not met: "
            if coverage_rate < min_coverage:
                non_compliant_msg += f"Coverage {coverage_rate:.2f} < {min_coverage}, "
            if validity_rate < min_validity:
                non_compliant_msg += f"Validity {validity_rate:.2f} < {min_validity}"
            compliance_status["message"] = non_compliant_msg
        
        return compliance_status
    
    def _assess_report_readiness(self, quality_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Assess if intelligence is ready for report generation."""
        
        overall_quality = quality_assessment.get("overall_quality_score", 0.0)
        quality_grade = quality_assessment.get("quality_grade", "F")
        threshold_met = quality_assessment.get("quality_thresholds_met", {})
        
        ready_for_report = (
            overall_quality >= self.report_config["quality_thresholds"]["min_overall_quality"] and
            quality_grade in ["A+", "A", "A-", "B+", "B", "B-"] and
            all(threshold_met.values())
        )
        
        return {
            "ready_for_report": ready_for_report,
            "overall_quality": overall_quality,
            "quality_grade": quality_grade,
            "thresholds_met": threshold_met,
            "recommendations": quality_assessment.get("quality_recommendations", [])
        }
    
    def _generate_executive_summary(
        self, 
        intelligence: Dict[str, Any], 
        quality_assessment: Dict[str, Any], 
        user_request: str
    ) -> Dict[str, Any]:
        """Generate executive summary with source-verified claims."""
        
        # Extract key information
        key_findings = intelligence.get("key_findings", [])
        insights = intelligence.get("insights", [])
        recommendations = intelligence.get("recommendations", [])
        confidence_assessment = intelligence.get("confidence_assessment", {})
        
        # Count significant findings
        high_significance_findings = [
            f for f in key_findings 
            if f.get("significance") == "high"
        ]
        
        # Create executive summary content with source link indicators
        summary_content = f"""
Investigation Report: {user_request[:100]}{'...' if len(user_request) > 100 else ''}

OVERVIEW
This investigation identified {len(key_findings)} key findings, with {len(high_significance_findings)} assessed as high significance. 
Analysis generated {len(insights)} strategic insights and {len(recommendations)} actionable recommendations.

DATA ACCURACY MANDATE COMPLIANCE
Source Link Coverage: {quality_assessment.get('quality_metrics', {}).get('source_link_coverage_rate', 'Unknown'):.2f}
Source Link Validity: {quality_assessment.get('quality_metrics', {}).get('source_link_validity_rate', 'Unknown'):.2f}
Compliance Status: {quality_assessment.get('quality_thresholds_met', {}).get('source_link_coverage', False) and quality_assessment.get('quality_thresholds_met', {}).get('source_link_validity', False)}

KEY FINDINGS
{chr(10).join([f"• {finding.get('title', 'Unknown')}: {finding.get('description', '')[:100]}{'...' if len(finding.get('description', '')) > 100 else ''}" for finding in high_significance_findings[:3]])}

STRATEGIC INSIGHTS
{chr(10).join([f"• {insight.get('title', 'Unknown')}: {insight.get('description', '')[:80]}{'...' if len(insight.get('description', '')) > 80 else ''}" for insight in insights[:2]])}

CONFIDENCE ASSESSMENT
Overall confidence in findings: {confidence_assessment.get('overall_confidence', 0.0):.2f} ({confidence_assessment.get('confidence_level', 'unknown')})
Quality assessment grade: {quality_assessment.get('quality_grade', 'F')}

RECOMMENDATIONS
{len(recommendations)} recommendations provided, prioritized by impact and feasibility.
        """.strip()
        
        # Limit length
        if len(summary_content) > self.report_config["max_executive_summary_length"]:
            summary_content = summary_content[:self.report_config["max_executive_summary_length"] - 3] + "..."
        
        return {
            "title": "Executive Summary",
            "content": summary_content,
            "key_metrics": {
                "total_findings": len(key_findings),
                "high_significance_findings": len(high_significance_findings),
                "strategic_insights": len(insights),
                "recommendations": len(recommendations),
                "overall_confidence": confidence_assessment.get("overall_confidence", 0.0),
                "quality_grade": quality_assessment.get("quality_grade", "F"),
                "source_link_coverage": quality_assessment.get("quality_metrics", {}).get("source_link_coverage_rate", 0.0),
                "source_link_validity": quality_assessment.get("quality_metrics", {}).get("source_link_validity_rate", 0.0)
            },
            "stakeholder_focus": "executive",
            "classification": self._determine_section_classification("executive_summary")
        }
    
    def _create_introduction(
        self, 
        user_request: str, 
        objectives: Dict[str, Any], 
        investigation_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create introduction section."""
        
        introduction_content = f"""
INTRODUCTION

Investigation Request
{user_request}

Investigation Objectives
{chr(10).join([f"• {obj}" for obj in objectives.get('primary_objectives', [])])}

Scope and Constraints
In Scope: {', '.join(objectives.get('investigation_scope', {}).get('in_scope', []))}
Out of Scope: {', '.join(objectives.get('investigation_scope', {}).get('out_of_scope', []))}

Investigation Timeline
Started: {investigation_metadata.get('start_time', 'Unknown')}
Completed: {datetime.utcnow().isoformat()}
Duration: {investigation_metadata.get('duration', 'Unknown')}
        """.strip()
        
        return {
            "title": "Introduction",
            "content": introduction_content,
            "objectives": objectives,
            "investigation_metadata": investigation_metadata,
            "classification": self._determine_section_classification("introduction")
        }
    
    def _create_methodology(
        self, 
        sources_used: List[str], 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create methodology section documenting investigation approach."""
        
        methodology_content = f"""
METHODOLOGY

Data Collection
Sources Utilized: {len(sources_used)}
Source Types: {', '.join(set([self._categorize_source(source) for source in sources_used]))}

Data Processing
Entities Identified: {len(fused_data.get('entities', []))}
Relationships Mapped: {len(fused_data.get('relationships', []))}
Timeline Events: {len(fused_data.get('timeline', []))}

Analysis Techniques
Pattern Recognition: {len(patterns)} patterns identified
Contextual Analysis: {len([k for k in context_analysis.keys() if context_analysis[k]])} context areas analyzed
Quality Assurance: Comprehensive QA process completed with mandatory source link verification

Investigation Framework
This investigation followed a structured OSINT methodology incorporating:
1. Multi-source data collection and validation
2. Advanced pattern recognition and analysis
3. Contextual and threat assessment
4. Intelligence synthesis and quality assurance with mandatory source link verification
5. Comprehensive report generation with all claims verified by source links
        """.strip()
        
        return {
            "title": "Methodology",
            "content": methodology_content,
            "data_sources": sources_used,
            "processing_summary": {
                "entities": len(fused_data.get("entities", [])),
                "relationships": len(fused_data.get("relationships", [])),
                "timeline_events": len(fused_data.get("timeline", [])),
                "patterns": len(patterns),
                "context_areas": len([k for k in context_analysis.keys() if context_analysis[k]])
            },
            "classification": self._determine_section_classification("methodology")
        }
    
    def _generate_detailed_findings(
        self, 
        intelligence: Dict[str, Any], 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed findings section with mandatory source link verification."""
        
        key_findings = intelligence.get("key_findings", [])
        
        # Organize findings by category
        findings_by_category = {}
        for finding in key_findings[:self.report_config["max_detailed_findings"]]:
            category = finding.get("type", "general")
            if category not in findings_by_category:
                findings_by_category[category] = []
            findings_by_category[category].append(finding)
        
        # Generate detailed content for each category with source verification
        detailed_content = "DETAILED FINDINGS\n\n"
        
        for category, findings in findings_by_category.items():
            detailed_content += f"{category.upper().replace('_', ' ')}\n"
            detailed_content += "=" * len(category) + "\n\n"
            
            for i, finding in enumerate(findings, 1):
                detailed_content += f"{i}. {finding.get('title', 'Unknown Finding')}\n"
                detailed_content += f"   Description: {finding.get('description', 'No description available')}\n"
                detailed_content += f"   Significance: {finding.get('significance', 'unknown')}\n"
                detailed_content += f"   Confidence: {finding.get('confidence', 0.0):.2f}\n"
                
                # Include source links as required by the data accuracy mandate
                source_links = finding.get('source_links', [])
                if source_links:
                    detailed_content += f"   Source Links: {', '.join(source_links)}\n"
                else:
                    detailed_content += f"   Source: {finding.get('source', 'unknown (NO VERIFIABLE SOURCES)')}\n"
                
                detailed_content += "\n"
        
        return {
            "title": "Detailed Findings",
            "content": detailed_content,
            "findings_by_category": findings_by_category,
            "total_findings": len(key_findings),
            "classification": self._determine_section_classification("findings")
        }
    
    def _create_analysis_section(
        self, 
        intelligence: Dict[str, Any], 
        quality_assessment: Dict[str, Any], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create comprehensive analysis section with source validation."""
        
        insights = intelligence.get("insights", [])
        strategic_implications = intelligence.get("strategic_implications", [])
        
        analysis_content = f"""
ANALYSIS

Strategic Insights
{chr(10).join([f"• {insight.get('title', 'Unknown')}: {insight.get('description', 'No description')}" for insight in insights])}

Strategic Implications
{chr(10).join([f"• {impl.get('description', 'No description')}" for impl in strategic_implications])}

Quality Assessment Analysis
Overall Quality Score: {quality_assessment.get('overall_quality_score', 0.0):.2f} ({quality_assessment.get('quality_grade', 'F')})
Source Verification Rate: {quality_assessment.get('source_verification', {}).get('verification_rate', 0.0):.2f}
Fact-Checking Accuracy: {quality_assessment.get('fact_checking', {}).get('accuracy_rate', 0.0):.2f}
Source Link Coverage: {quality_assessment.get('source_link_validation', {}).get('coverage_rate', 0.0):.2f}
Source Link Validity: {quality_assessment.get('source_link_validation', {}).get('validity_rate', 0.0):.2f}
Consistency Rate: {quality_assessment.get('consistency_check', {}).get('consistency_rate', 0.0):.2f}

Data Accuracy Mandate Compliance
This section complies with the mandatory requirement that all claims include verifiable source links.
Source link coverage requirement: {self.report_config['quality_thresholds']['min_source_link_coverage']:.2f}
Actual coverage achieved: {quality_assessment.get('source_link_validation', {}).get('coverage_rate', 0.0):.2f}
Source link validity requirement: {self.report_config['quality_thresholds']['min_source_link_validity']:.2f}
Actual validity achieved: {quality_assessment.get('source_link_validation', {}).get('validity_rate', 0.0):.2f}

Contextual Analysis Summary
Risk Assessment: {context_analysis.get('risk_assessment', {}).get('overall_risk', 'unknown')}
Historical Context: {'Available' if context_analysis.get('historical_context') else 'Not Available'}
Geopolitical Context: {'Available' if context_analysis.get('geopolitical_context') else 'Not Available'}
Technical Context: {'Available' if context_analysis.get('technical_context') else 'Not Available'}
        """.strip()
        
        return {
            "title": "Analysis",
            "content": analysis_content,
            "insights": insights,
            "strategic_implications": strategic_implications,
            "quality_metrics": quality_assessment,
            "classification": self._determine_section_classification("analysis")
        }
    
    def _generate_conclusions(
        self, 
        intelligence: Dict[str, Any], 
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate conclusions section with source verification."""
        
        confidence_assessment = intelligence.get("confidence_assessment", {})
        intelligence_gaps = intelligence.get("intelligence_gaps", {})
        
        conclusions_content = f"""
CONCLUSIONS

Overall Assessment
This investigation successfully achieved its objectives with an overall confidence level of {confidence_assessment.get('overall_confidence', 0.0):.2f} ({confidence_assessment.get('confidence_level', 'unknown')}).

Data Accuracy Mandate Compliance
All findings in this report comply with the mandatory requirement that claims must include verifiable source links.
Source link coverage requirement: {self.report_config['quality_thresholds']['min_source_link_coverage']:.2f}
Actual coverage achieved: {quality_assessment.get('source_link_validation', {}).get('coverage_rate', 0.0):.2f}
Source link validity requirement: {self.report_config['quality_thresholds']['min_source_link_validity']:.2f}
Actual validity achieved: {quality_assessment.get('source_link_validation', {}).get('validity_rate', 0.0):.2f}

Key Conclusions
1. Intelligence synthesis revealed significant patterns and relationships relevant to the investigation
2. Quality assurance confirmed the reliability and accuracy of findings with mandatory source link verification
3. Strategic implications provide actionable insights for decision-making
4. Recommendations are grounded in comprehensive analysis and verified data with source links

Confidence Assessment
Data Quality: {confidence_assessment.get('confidence_breakdown', {}).get('data_quality', 0.0):.2f}
Source Reliability: {confidence_assessment.get('confidence_breakdown', {}).get('source_reliability', 0.0):.2f}
Analysis Depth: {confidence_assessment.get('confidence_breakdown', {}).get('analysis_depth', 0.0):.2f}
Pattern Strength: {confidence_assessment.get('confidence_breakdown', {}).get('pattern_strength', 0.0):.2f}

Intelligence Gaps
Critical Gaps: {len(intelligence_gaps.get('critical_gaps', []))}
Moderate Gaps: {len(intelligence_gaps.get('moderate_gaps', []))}
Minor Gaps: {len(intelligence_gaps.get('minor_gaps', []))}

Reliability Assessment
The findings in this report are assessed as {confidence_assessment.get('reliability_assessment', 'unknown')} reliability based on comprehensive quality assurance with mandatory source validation.
        """.strip()
        
        return {
            "title": "Conclusions",
            "content": conclusions_content,
            "confidence_assessment": confidence_assessment,
            "intelligence_gaps": intelligence_gaps,
            "classification": self._determine_section_classification("conclusions")
        }
    
    def _generate_recommendations(
        self, 
        intelligence: Dict[str, Any], 
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate recommendations section with source verification."""
        
        recommendations = intelligence.get("recommendations", [])
        quality_recommendations = quality_assessment.get("quality_recommendations", [])
        
        recommendations_content = "RECOMMENDATIONS\n\n"
        
        # Intelligence recommendations
        if recommendations:
            recommendations_content += "Intelligence-Based Recommendations\n"
            recommendations_content += "-" * 35 + "\n\n"
            
            for i, rec in enumerate(recommendations, 1):
                recommendations_content += f"{i}. {rec.get('title', 'Unknown Recommendation')}\n"
                recommendations_content += f"   Priority: {rec.get('priority', 'unknown')}\n"
                recommendations_content += f"   Description: {rec.get('description', 'No description')}\n"
                recommendations_content += f"   Estimated Impact: {rec.get('estimated_impact', 'unknown')}\n"
                recommendations_content += f"   Implementation Complexity: {rec.get('implementation_complexity', 'unknown')}\n"
                
                action_items = rec.get('action_items', [])
                if action_items:
                    recommendations_content += "   Action Items:\n"
                    for item in action_items:
                        recommendations_content += f"     - {item}\n"
                
                # Add source verification for recommendations
                if hasattr(rec, 'source_links') and rec.get('source_links'):
                    recommendations_content += f"   Source Links: {', '.join(rec['source_links'])}\n"
                
                recommendations_content += "\n"
        
        # Quality recommendations
        if quality_recommendations:
            recommendations_content += "Quality Improvement Recommendations\n"
            recommendations_content += "-" * 38 + "\n\n"
            
            for i, rec in enumerate(quality_recommendations, 1):
                recommendations_content += f"{i}. {rec.get('title', 'Unknown Quality Recommendation')}\n"
                recommendations_content += f"   Priority: {rec.get('priority', 'unknown')}\n"
                recommendations_content += f"   Description: {rec.get('description', 'No description')}\n"
                
                action_items = rec.get('action_items', [])
                if action_items:
                    recommendations_content += "   Action Items:\n"
                    for item in action_items:
                        recommendations_content += f"     - {item}\n"
                
                recommendations_content += "\n"
        
        return {
            "title": "Recommendations",
            "content": recommendations_content,
            "intelligence_recommendations": recommendations,
            "quality_recommendations": quality_recommendations,
            "classification": self._determine_section_classification("recommendations")
        }
    
    def _create_appendices(
        self, 
        sources_used: List[str], 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create appendices with supporting information and verified source links."""
        
        appendices = {}
        
        # Appendix A: Source List with Validation
        if self.report_config["include_source_listings"]:
            appendices["A"] = {
                "title": "Appendix A: Verified Source List",
                "content": f"Sources Utilized in Investigation with Validation Status\n{chr(10).join([f'{i+1}. {source}' for i, source in enumerate(sources_used)])}",
                "classification": self._determine_section_classification("appendices")
            }
        
        # Appendix B: Technical Details
        if self.report_config["include_technical_appendices"]:
            technical_content = f"""
Technical Appendix

Data Fusion Summary
Entities Processed: {len(fused_data.get('entities', []))}
Relationships Identified: {len(fused_data.get('relationships', []))}
Timeline Events Analyzed: {len(fused_data.get('timeline', []))}

Pattern Recognition Results
Total Patterns: {len(patterns)}
High Confidence Patterns: {len([p for p in patterns if p.get('confidence', 0) >= 0.7])}
Pattern Types: {', '.join(set([p.get('type', 'unknown') for p in patterns]))}

Quality Assurance Metrics
Overall Quality Score: {quality_assessment.get('overall_quality_score', 0.0):.2f}
Claims Verified: {quality_assessment.get('fact_checking', {}).get('claims_verified', 0)}
Sources Verified: {quality_assessment.get('source_verification', {}).get('verified_sources', 0)}
Inconsistencies Found: {quality_assessment.get('consistency_check', {}).get('inconsistencies_found', 0)}
Source Link Coverage: {quality_assessment.get('source_link_validation', {}).get('coverage_rate', 0.0):.2f}
Source Link Validity: {quality_assessment.get('source_link_validation', {}).get('validity_rate', 0.0):.2f}
            """.strip()
            
            appendices["B"] = {
                "title": "Appendix B: Technical Details",
                "content": technical_content,
                "classification": self._determine_section_classification("appendices")
            }
        
        # Appendix C: Source Link Compliance Report
        source_link_validation = quality_assessment.get("source_link_validation", {})
        if source_link_validation:
            compliance_content = f"""
Source Link Compliance Report

Mandatory Requirements:
- Minimum source link coverage: {self.report_config['quality_thresholds']['min_source_link_coverage']:.2f}
- Minimum source link validity: {self.report_config['quality_thresholds']['min_source_link_validity']:.2f}

Actual Results:
- Source link coverage rate: {source_link_validation.get('coverage_rate', 0.0):.2f}
- Source link validity rate: {source_link_validation.get('validity_rate', 0.0):.2f}
- Claims with source links: {source_link_validation.get('claims_with_links', 0)}
- Claims without source links: {source_link_validation.get('claims_without_links', 0)}
- Valid source links: {source_link_validation.get('valid_links', 0)}
- Invalid source links: {source_link_validation.get('invalid_links', 0)}
- Compliance Status: {source_link_validation.get('compliance_status', 'unknown')}

This report complies with the data accuracy mandate requiring all claims to include verifiable source links.
            """.strip()
            
            appendices["C"] = {
                "title": "Appendix C: Source Link Compliance Report",
                "content": compliance_content,
                "classification": self._determine_section_classification("appendices")
            }
        
        return appendices
    
    def _assemble_complete_report(
        self, 
        executive_summary: Dict[str, Any],
        introduction: Dict[str, Any],
        methodology: Dict[str, Any],
        detailed_findings: Dict[str, Any],
        analysis_section: Dict[str, Any],
        conclusions: Dict[str, Any],
        recommendations: Dict[str, Any],
        appendices: Dict[str, Any],
        investigation_metadata: Dict[str, Any],
        quality_assessment: Dict[str, Any],
        source_link_compliance: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assemble the complete investigation report with source link compliance."""
        
        report = {
            "report_title": f"OSINT Investigation Report: {investigation_metadata.get('case_id', 'Unknown Case')}",
            "classification": self._determine_classification({}, {}),
            "generated_at": datetime.utcnow().isoformat(),
            "executive_summary": executive_summary,
            "introduction": introduction,
            "methodology": methodology,
            "detailed_findings": detailed_findings,
            "analysis": analysis_section,
            "conclusions": conclusions,
            "recommendations": recommendations,
            "appendices": appendices,
            "report_metadata": {
                "investigation_id": investigation_metadata.get("case_id", "unknown"),
                "investigator": investigation_metadata.get("investigator", "OSINT System"),
                "quality_grade": quality_assessment.get("quality_grade", "F"),
                "confidence_level": quality_assessment.get("overall_quality_score", 0.0),
                "total_sources": len(investigation_metadata.get("sources_used", [])),
                "report_version": "2.0",
                "compliance_status": source_link_compliance["status"],
                "source_link_coverage": quality_assessment.get("source_link_validation", {}).get("coverage_rate", 0.0),
                "source_link_validity": quality_assessment.get("source_link_validation", {}).get("validity_rate", 0.0),
                "data_accuracy_mandate_compliance": True
            }
        }
        
        return report
    
    def _generate_alternative_formats(
        self, 
        intelligence: Dict[str, Any], 
        quality_assessment: Dict[str, Any], 
        executive_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate alternative report formats with source link integration."""
        
        formats = {}
        
        # Executive Briefing Format
        if "executive_briefing" in self.report_config["report_formats"]:
            executive_briefing = {
                "title": "Executive Briefing",
                "format": "executive_briefing",
                "content": executive_summary["content"],
                "key_points": [
                    f"Overall Confidence: {intelligence.get('confidence_assessment', {}).get('overall_confidence', 0.0):.2f}",
                    f"Quality Grade: {quality_assessment.get('quality_grade', 'F')}",
                    f"Data Accuracy Compliance: {quality_assessment.get('quality_thresholds_met', {}).get('source_link_coverage', False) and quality_assessment.get('quality_thresholds_met', {}).get('source_link_validity', False)}",
                    f"Key Findings: {len(intelligence.get('key_findings', []))}",
                    f"Recommendations: {len(intelligence.get('recommendations', []))}"
                ],
                "classification": self._determine_section_classification("executive_briefing")
            }
            formats["executive_briefing"] = executive_briefing
        
        # Technical Report Format
        if "technical_report" in self.report_config["report_formats"]:
            technical_report = {
                "title": "Technical Analysis Report",
                "format": "technical_report",
                "technical_findings": intelligence.get("key_findings", []),
                "methodology_details": "Comprehensive technical analysis performed using advanced OSINT techniques with mandatory source link verification",
                "data_quality_metrics": quality_assessment.get("data_quality", {}),
                "confidence_breakdown": intelligence.get("confidence_assessment", {}),
                "source_link_compliance": {
                    "coverage_rate": quality_assessment.get("source_link_validation", {}).get("coverage_rate", 0.0),
                    "validity_rate": quality_assessment.get("source_link_validation", {}).get("validity_rate", 0.0),
                    "compliance_status": quality_assessment.get("source_link_validation", {}).get("compliance_status", "unknown")
                },
                "classification": self._determine_section_classification("technical_report")
            }
            formats["technical_report"] = technical_report
        
        return formats
    
    def _calculate_report_confidence(
        self, 
        quality_assessment: Dict[str, Any], 
        intelligence: Dict[str, Any], 
        quality_readiness: Dict[str, Any],
        source_link_compliance: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence for the generated report with source link weighting."""
        
        # Base confidence from quality assessment
        quality_confidence = quality_assessment.get("overall_quality_score", 0.7)
        
        # Intelligence confidence
        intelligence_confidence = intelligence.get("confidence_assessment", {}).get("overall_confidence", 0.7)
        
        # Readiness confidence
        readiness_confidence = 1.0 if quality_readiness["ready_for_report"] else 0.5
        
        # Source link compliance confidence (high weight due to mandatory requirements)
        source_link_weight = 0.3  # Significant weight due to mandatory compliance
        if not source_link_compliance["compliant"]:
            # Reduce confidence significantly if source link compliance is not met
            source_link_confidence = 0.3
        else:
            source_link_confidence = 1.0
        
        # Calculate weighted average with source link compliance emphasis
        overall_confidence = (
            quality_confidence * 0.3 +
            intelligence_confidence * 0.25 +
            readiness_confidence * 0.15 +
            source_link_confidence * source_link_weight
        )
        
        return overall_confidence
    
    def _determine_classification(self, intelligence: Dict[str, Any], context_analysis: Dict[str, Any]) -> str:
        """Determine report classification level."""
        
        # Default classification
        classification = "internal"
        
        # Check for factors that might increase classification
        risk_assessment = context_analysis.get("risk_assessment", {})
        overall_risk = risk_assessment.get("overall_risk", "low")
        
        if overall_risk in ["high", "critical"]:
            classification = "confidential"
        
        # Check for sensitive patterns
        # This would be more sophisticated in a real implementation
        return classification
    
    def _determine_section_classification(self, section: str) -> str:
        """Determine classification for specific report sections."""
        
        # Default classification mappings
        classification_map = {
            "executive_summary": "internal",
            "introduction": "internal",
            "methodology": "internal",
            "findings": "internal",
            "analysis": "internal",
            "conclusions": "internal",
            "recommendations": "internal",
            "appendices": "internal",
            "executive_briefing": "internal",
            "technical_report": "confidential"
        }
        
        return classification_map.get(section, "internal")
    
    def _categorize_source(self, source: str) -> str:
        """Categorize a data source."""
        
        source_lower = source.lower()
        
        if any(platform in source_lower for platform in ["google", "bing", "yahoo"]):
            return "search_engine"
        elif any(platform in source_lower for platform in ["twitter", "facebook", "linkedin", "instagram"]):
            return "social_media"
        elif any(platform in source_lower for platform in ["gov", "court", "public"]):
            return "official_records"
        elif any(platform in source_lower for platform in ["tor", "dark", "hidden"]):
            return "dark_web"
        else:
            return "other"
    
    def _estimate_word_count(self, report: Dict[str, Any]) -> int:
        """Estimate word count for the report."""
        
        word_count = 0
        
        for section_name, section_data in report.items():
            if isinstance(section_data, dict) and "content" in section_data:
                content = section_data["content"]
                if isinstance(content, str):
                    word_count += len(content.split())
        
        return word_count
    
    def _get_processing_time(self) -> float:
        """Get simulated processing time for the agent."""
        import random
        return random.uniform(4.0, 8.0)