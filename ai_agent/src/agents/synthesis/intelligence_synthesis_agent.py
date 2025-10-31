"""
Intelligence Synthesis Agent

This agent combines analysis results from the DataFusionAgent, PatternRecognitionAgent,
and ContextualAnalysisAgent to generate actionable intelligence and insights.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from ..base.osint_agent import AgentResult, AgentCapability
from .synthesis_agent_base import SynthesisAgentBase


logger = logging.getLogger(__name__)


class IntelligenceSynthesisAgent(SynthesisAgentBase):
    """
    Intelligence Synthesis Agent for OSINT investigations.
    
    This agent is responsible for:
    - Combining fused data, patterns, and contextual analysis
    - Generating actionable intelligence and insights
    - Assessing confidence levels and reliability
    - Identifying key findings and strategic implications
    - Formulating recommendations based on comprehensive analysis
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Intelligence Synthesis Agent."""
        super().__init__(
            name="IntelligenceSynthesisAgent",
            description="Synthesizes analysis results into actionable intelligence",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="intelligence_synthesis",
                    description="Combine analysis results into actionable intelligence",
                    required_data=["fused_data", "patterns", "context_analysis"]
                ),
                AgentCapability(
                    name="insight_generation",
                    description="Generate strategic insights from analysis data",
                    required_data=["fused_data", "patterns"]
                ),
                AgentCapability(
                    name="confidence_assessment",
                    description="Assess confidence levels of synthesized intelligence",
                    required_data=["fused_data", "patterns", "context_analysis"]
                ),
                AgentCapability(
                    name="recommendation_formulation",
                    description="Formulate actionable recommendations",
                    required_data=["intelligence", "insights"]
                )
            ]
        )
        
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # Intelligence synthesis parameters
        self.synthesis_config = {
            "min_confidence_threshold": 0.6,
            "max_key_findings": 10,
            "max_recommendations": 8,
            "insight_categories": [
                "strategic", "tactical", "operational", 
                "threat", "opportunity", "risk"
            ],
            "confidence_weights": {
                "data_quality": 0.3,
                "source_reliability": 0.25,
                "analysis_depth": 0.25,
                "pattern_strength": 0.2
            }
        }
        
        # Update config with user-provided settings
        self.synthesis_config.update(self.config.get("synthesis_config", {}))
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute intelligence synthesis process.
        
        Args:
            input_data: Dictionary containing:
                - fused_data: Results from DataFusionAgent
                - patterns: Results from PatternRecognitionAgent  
                - context_analysis: Results from ContextualAnalysisAgent
                - user_request: Original investigation request
                - objectives: Investigation objectives
        
        Returns:
            AgentResult containing synthesized intelligence
        """
        try:
            self.logger.info("Starting intelligence synthesis")
            
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
            fused_data = input_data.get("fused_data", {})
            patterns = input_data.get("patterns", [])
            context_analysis = input_data.get("context_analysis", {})
            user_request = input_data.get("user_request", "")
            objectives = input_data.get("objectives", {})
            
            # Step 1: Analyze data quality and completeness
            quality_assessment = self._assess_data_quality(
                fused_data, patterns, context_analysis
            )
            
            # Step 2: Extract key findings from all analysis sources
            key_findings = self._extract_key_findings(
                fused_data, patterns, context_analysis, objectives
            )
            
            # Step 3: Generate strategic insights
            insights = self._generate_insights(
                fused_data, patterns, context_analysis, key_findings
            )
            
            # Step 4: Assess confidence levels
            confidence_assessment = self._assess_confidence(
                fused_data, patterns, context_analysis, quality_assessment
            )
            
            # Step 5: Formulate actionable recommendations
            recommendations = self._formulate_recommendations(
                insights, key_findings, context_analysis, objectives
            )
            
            # Step 6: Create intelligence synthesis
            intelligence = {
                "executive_summary": self._create_executive_summary(
                    key_findings, insights, user_request
                ),
                "key_findings": key_findings,
                "insights": insights,
                "recommendations": recommendations,
                "confidence_assessment": confidence_assessment,
                "quality_assessment": quality_assessment,
                "strategic_implications": self._identify_strategic_implications(
                    insights, key_findings
                ),
                "intelligence_gaps": self._identify_intelligence_gaps(
                    fused_data, patterns, context_analysis
                ),
                "synthesis_metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "data_sources_analyzed": len(fused_data.get("sources", [])),
                    "patterns_processed": len(patterns),
                    "confidence_threshold": self.synthesis_config["min_confidence_threshold"],
                    "synthesis_methodology": "multi_source_intelligence_fusion"
                }
            }
            
            # Calculate overall confidence
            overall_confidence = confidence_assessment.get("overall_confidence", 0.7)
            
            self.logger.info(f"Intelligence synthesis completed with confidence: {overall_confidence}")
            
            return AgentResult(
                success=True,
                data=intelligence,
                confidence=overall_confidence,
                metadata={
                    "processing_time": self._get_processing_time(),
                    "findings_count": len(key_findings),
                    "insights_count": len(insights),
                    "recommendations_count": len(recommendations)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Intelligence synthesis failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error_message=str(e),
                data={},
                confidence=0.0
            )
    
    def _validate_input_data(self, input_data: Dict[str, Any]) -> AgentResult:
        """Validate input data for intelligence synthesis."""
        required_fields = ["fused_data", "patterns", "context_analysis"]
        
        for field in required_fields:
            if field not in input_data:
                return AgentResult(
                    success=False,
                    data={},
                    error_message=f"Missing required field: {field}"
                )
        
        # Validate data structure
        fused_data = input_data.get("fused_data", {})
        patterns = input_data.get("patterns", [])
        context_analysis = input_data.get("context_analysis", {})
        
        if not isinstance(fused_data, dict):
            return AgentResult(
                success=False,
                data={},
                error_message="fused_data must be a dictionary"
            )
        
        if not isinstance(patterns, list):
            return AgentResult(
                success=False,
                data={},
                error_message="patterns must be a list"
            )
        
        if not isinstance(context_analysis, dict):
            return AgentResult(
                success=False,
                data={},
                error_message="context_analysis must be a dictionary"
            )
        
        return AgentResult(success=True, data={})
    
    def _assess_data_quality(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the quality and completeness of analysis data."""
        
        quality_scores = {}
        
        # Assess fused data quality
        fused_quality = 0.0
        if fused_data:
            entity_count = len(fused_data.get("entities", []))
            relationship_count = len(fused_data.get("relationships", []))
            timeline_count = len(fused_data.get("timeline", []))
            
            # Quality based on data richness
            if entity_count > 0:
                fused_quality += 0.4
            if relationship_count > 0:
                fused_quality += 0.3
            if timeline_count > 0:
                fused_quality += 0.3
        
        quality_scores["fused_data_quality"] = min(fused_quality, 1.0)
        
        # Assess patterns quality
        patterns_quality = 0.0
        if patterns:
            high_confidence_patterns = [
                p for p in patterns 
                if p.get("confidence", 0) >= 0.7
            ]
            
            if high_confidence_patterns:
                patterns_quality = len(high_confidence_patterns) / len(patterns)
            else:
                patterns_quality = 0.5  # Minimum for having any patterns
        
        quality_scores["patterns_quality"] = min(patterns_quality, 1.0)
        
        # Assess context analysis quality
        context_quality = 0.0
        if context_analysis:
            context_sections = [
                "historical_context", "cultural_context", 
                "geopolitical_context", "technical_context", "risk_assessment"
            ]
            
            present_sections = [
                section for section in context_sections 
                if section in context_analysis and context_analysis[section]
            ]
            
            if present_sections:
                context_quality = len(present_sections) / len(context_sections)
        
        quality_scores["context_analysis_quality"] = min(context_quality, 1.0)
        
        # Calculate overall quality
        weights = {"fused": 0.4, "patterns": 0.3, "context": 0.3}
        overall_quality = (
            quality_scores["fused_data_quality"] * weights["fused"] +
            quality_scores["patterns_quality"] * weights["patterns"] +
            quality_scores["context_analysis_quality"] * weights["context"]
        )
        
        return {
            "overall_quality": overall_quality,
            "fused_data_quality": quality_scores["fused_data_quality"],
            "patterns_quality": quality_scores["patterns_quality"],
            "context_analysis_quality": quality_scores["context_analysis_quality"],
            "quality_threshold_met": overall_quality >= self.synthesis_config["min_confidence_threshold"],
            "data_completeness": self._assess_data_completeness(fused_data, patterns, context_analysis)
        }
    
    def _assess_data_completeness(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess completeness of different data types."""
        
        completeness: Dict[str, Any] = {
            "entities": len(fused_data.get("entities", [])) > 0,
            "relationships": len(fused_data.get("relationships", [])) > 0,
            "temporal_data": len(fused_data.get("timeline", [])) > 0,
            "geospatial_data": len(fused_data.get("geospatial", [])) > 0,
            "patterns_detected": len(patterns) > 0,
            "risk_assessment": "risk_assessment" in context_analysis,
            "threat_analysis": "threat_analysis" in context_analysis,
            "historical_context": "historical_context" in context_analysis
        }
        
        total_categories = len(completeness)
        complete_categories = sum(completeness.values())
        
        result = completeness.copy()
        result["overall_completeness"] = complete_categories / total_categories
        result["missing_categories"] = [
            category for category, present in completeness.items() 
            if not present and category != "overall_completeness"
        ]
        
        return result
    
    def _extract_key_findings(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        objectives: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Extract key findings from analysis results."""
        
        findings = []
        
        # Extract findings from fused data
        entities = fused_data.get("entities", [])
        if entities:
            high_confidence_entities = [
                entity for entity in entities 
                if entity.get("confidence", 0) >= 0.7
            ]
            
            for entity in high_confidence_entities[:3]:  # Top 3 entities
                findings.append({
                    "type": "entity_finding",
                    "title": f"Key Entity Identified: {entity.get('name', 'Unknown')}",
                    "description": f"Significant {entity.get('type', 'entity')} with confidence {entity.get('confidence', 0):.2f}",
                    "confidence": entity.get("confidence", 0.7),
                    "significance": "high" if entity.get("confidence", 0) >= 0.8 else "medium",
                    "source": "data_fusion",
                    "supporting_data": {"entity": entity}
                })
        
        # Extract findings from patterns
        significant_patterns = [
            pattern for pattern in patterns 
            if pattern.get("significance") in ["high", "medium"] and 
               pattern.get("confidence", 0) >= 0.6
        ]
        
        for pattern in significant_patterns[:3]:  # Top 3 patterns
            findings.append({
                "type": "pattern_finding",
                "title": f"Significant Pattern: {pattern.get('type', 'Unknown Pattern')}",
                "description": pattern.get("description", "Pattern detected"),
                "confidence": pattern.get("confidence", 0.6),
                "significance": pattern.get("significance", "medium"),
                "source": "pattern_recognition",
                "supporting_data": {"pattern": pattern}
            })
        
        # Extract findings from context analysis
        risk_assessment = context_analysis.get("risk_assessment", {})
        if risk_assessment:
            overall_risk = risk_assessment.get("overall_risk", "unknown")
            findings.append({
                "type": "risk_finding",
                "title": f"Risk Assessment: {overall_risk.upper()} Risk Level",
                "description": f"Overall risk evaluated as {overall_risk} based on comprehensive analysis",
                "confidence": 0.8,
                "significance": "high" if overall_risk in ["high", "critical"] else "medium",
                "source": "contextual_analysis",
                "supporting_data": {"risk_assessment": risk_assessment}
            })
        
        # Sort by significance and confidence, then limit
        findings.sort(key=lambda x: (
            0 if x["significance"] == "high" else 1 if x["significance"] == "medium" else 2,
            -x["confidence"]
        ))
        
        return findings[:self.synthesis_config["max_key_findings"]]
    
    def _generate_insights(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        key_findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate strategic insights from analysis data."""
        
        insights = []
        
        # Generate insights from entity relationships
        relationships = fused_data.get("relationships", [])
        if relationships:
            high_value_relationships = [
                rel for rel in relationships 
                if rel.get("confidence", 0) >= 0.7
            ]
            
            if high_value_relationships:
                insights.append({
                    "category": "network",
                    "title": "Network Relationships Identified",
                    "description": f"Analysis revealed {len(high_value_relationships)} significant relationships between entities",
                    "confidence": sum(rel.get("confidence", 0) for rel in high_value_relationships) / len(high_value_relationships),
                    "strategic_value": "high",
                    "supporting_findings": [f["title"] for f in key_findings if f["type"] == "entity_finding"]
                })
        
        # Generate insights from temporal patterns
        timeline = fused_data.get("timeline", [])
        if timeline:
            insights.append({
                "category": "temporal",
                "title": "Temporal Activity Patterns",
                "description": f"Timeline analysis of {len(timeline)} events reveals activity patterns and sequences",
                "confidence": 0.75,
                "strategic_value": "medium",
                "supporting_findings": [f["title"] for f in key_findings if "pattern" in f["type"]]
            })
        
        # Generate insights from detected patterns
        if patterns:
            pattern_types = set(p.get("type", "unknown") for p in patterns)
            insights.append({
                "category": "behavioral",
                "title": "Behavioral Patterns Analysis",
                "description": f"Analysis identified patterns in {', '.join(pattern_types)} indicating structured behavior",
                "confidence": sum(p.get("confidence", 0) for p in patterns) / len(patterns),
                "strategic_value": "high" if len(patterns) > 2 else "medium",
                "supporting_findings": [f["title"] for f in key_findings if f["type"] == "pattern_finding"]
            })
        
        # Generate insights from context
        if context_analysis.get("geopolitical_context"):
            insights.append({
                "category": "strategic",
                "title": "Geopolitical Context Implications",
                "description": "Analysis reveals significant geopolitical factors influencing the investigation",
                "confidence": 0.8,
                "strategic_value": "high",
                "supporting_findings": []
            })
        
        # Generate threat insights
        if context_analysis.get("risk_assessment", {}).get("risk_factors"):
            risk_factors = context_analysis["risk_assessment"]["risk_factors"]
            insights.append({
                "category": "threat",
                "title": "Threat Landscape Analysis",
                "description": f"Identified {len(risk_factors)} key risk factors requiring attention",
                "confidence": 0.85,
                "strategic_value": "high",
                "supporting_findings": [f["title"] for f in key_findings if "risk" in f["type"]]
            })
        
        # Sort by strategic value and confidence
        insights.sort(key=lambda x: (
            0 if x["strategic_value"] == "high" else 1 if x["strategic_value"] == "medium" else 2,
            -x["confidence"]
        ))
        
        return insights
    
    def _assess_confidence(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        quality_assessment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess confidence levels for synthesized intelligence."""
        
        weights = self.synthesis_config["confidence_weights"]
        
        # Data quality confidence
        data_quality_confidence = quality_assessment.get("overall_quality", 0.7)
        
        # Source reliability confidence (based on data fusion results)
        source_reliability_confidence = 0.8  # Default, would be calculated from actual sources
        if fused_data.get("entities"):
            entity_confidences = [e.get("confidence", 0.5) for e in fused_data["entities"]]
            if entity_confidences:
                source_reliability_confidence = sum(entity_confidences) / len(entity_confidences)
        
        # Analysis depth confidence
        analysis_depth_confidence = 0.0
        if fused_data:
            analysis_depth_confidence += 0.3
        if patterns:
            analysis_depth_confidence += 0.4
        if context_analysis:
            analysis_depth_confidence += 0.3
        
        # Pattern strength confidence
        pattern_strength_confidence = 0.5  # Default
        if patterns:
            pattern_confidences = [p.get("confidence", 0.5) for p in patterns]
            if pattern_confidences:
                pattern_strength_confidence = sum(pattern_confidences) / len(pattern_confidences)
        
        # Calculate overall confidence
        overall_confidence = (
            data_quality_confidence * weights["data_quality"] +
            source_reliability_confidence * weights["source_reliability"] +
            analysis_depth_confidence * weights["analysis_depth"] +
            pattern_strength_confidence * weights["pattern_strength"]
        )
        
        return {
            "overall_confidence": overall_confidence,
            "confidence_breakdown": {
                "data_quality": data_quality_confidence,
                "source_reliability": source_reliability_confidence,
                "analysis_depth": analysis_depth_confidence,
                "pattern_strength": pattern_strength_confidence
            },
            "confidence_level": self._get_confidence_level(overall_confidence),
            "reliability_assessment": "high" if overall_confidence >= 0.8 else "medium" if overall_confidence >= 0.6 else "low"
        }
    
    def _get_confidence_level(self, confidence_score: float) -> str:
        """Convert confidence score to confidence level."""
        if confidence_score >= 0.9:
            return "very_high"
        elif confidence_score >= 0.8:
            return "high"
        elif confidence_score >= 0.7:
            return "medium_high"
        elif confidence_score >= 0.6:
            return "medium"
        elif confidence_score >= 0.5:
            return "low_medium"
        else:
            return "low"
    
    def _formulate_recommendations(
        self, 
        insights: List[Dict[str, Any]], 
        key_findings: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        objectives: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Formulate actionable recommendations based on intelligence."""
        
        recommendations = []
        
        # Risk-based recommendations
        risk_assessment = context_analysis.get("risk_assessment", {})
        if risk_assessment.get("risk_factors"):
            recommendations.append({
                "type": "risk_mitigation",
                "priority": "high",
                "title": "Implement Risk Mitigation Strategies",
                "description": "Address identified risk factors through targeted mitigation measures",
                "action_items": [
                    "Develop comprehensive risk management plan",
                    "Implement monitoring for high-risk factors",
                    "Establish response protocols for identified threats"
                ],
                "supporting_intelligence": [insight["title"] for insight in insights if insight["category"] == "threat"],
                "estimated_impact": "high",
                "implementation_complexity": "medium"
            })
        
        # Investigation continuation recommendations
        if context_analysis.get("risk_assessment", {}).get("overall_risk") in ["high", "critical"]:
            recommendations.append({
                "type": "investigation",
                "priority": "high",
                "title": "Expand Investigation Scope",
                "description": "High risk level indicates need for expanded investigation",
                "action_items": [
                    "Deep dive into high-confidence patterns",
                    "Expand data collection to additional sources",
                    "Conduct specialized analysis for critical areas"
                ],
                "supporting_intelligence": [finding["title"] for finding in key_findings if finding["significance"] == "high"],
                "estimated_impact": "high",
                "implementation_complexity": "high"
            })
        
        # Monitoring recommendations
        significant_patterns = [p for p in key_findings if p["type"] == "pattern_finding"]
        if significant_patterns:
            recommendations.append({
                "type": "monitoring",
                "priority": "medium",
                "title": "Establish Ongoing Monitoring",
                "description": "Implement continuous monitoring for detected patterns",
                "action_items": [
                    "Set up automated pattern monitoring",
                    "Establish alert thresholds for significant changes",
                    "Create regular review schedule for pattern evolution"
                ],
                "supporting_intelligence": [pattern["title"] for pattern in significant_patterns],
                "estimated_impact": "medium",
                "implementation_complexity": "low"
            })
        
        # Intelligence gathering recommendations
        intelligence_gaps = self._identify_intelligence_gaps({}, [], context_analysis)
        if intelligence_gaps.get("critical_gaps"):
            recommendations.append({
                "type": "intelligence_gathering",
                "priority": "medium",
                "title": "Address Intelligence Gaps",
                "description": "Fill critical intelligence gaps through targeted collection",
                "action_items": [
                    f"Prioritize collection for: {', '.join(intelligence_gaps['critical_gaps'][:3])}",
                    "Develop specialized collection strategies for gaps",
                    "Validate findings through alternative sources"
                ],
                "supporting_intelligence": [],
                "estimated_impact": "medium",
                "implementation_complexity": "medium"
            })
        
        # Strategic recommendations based on insights
        strategic_insights = [insight for insight in insights if insight["strategic_value"] == "high"]
        if strategic_insights:
            recommendations.append({
                "type": "strategic",
                "priority": "high",
                "title": "Strategic Response Planning",
                "description": "Develop strategic response based on high-value insights",
                "action_items": [
                    "Create strategic action plan based on key insights",
                    "Align response with organizational objectives",
                    "Establish metrics for strategic outcome measurement"
                ],
                "supporting_intelligence": [insight["title"] for insight in strategic_insights],
                "estimated_impact": "high",
                "implementation_complexity": "high"
            })
        
        # Sort by priority and impact
        recommendations.sort(key=lambda x: (
            0 if x["priority"] == "high" else 1 if x["priority"] == "medium" else 2,
            0 if x["estimated_impact"] == "high" else 1 if x["estimated_impact"] == "medium" else 2
        ))
        
        return recommendations[:self.synthesis_config["max_recommendations"]]
    
    def _identify_strategic_implications(
        self, 
        insights: List[Dict[str, Any]], 
        key_findings: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify strategic implications of the intelligence."""
        
        implications = []
        
        # High-risk implications
        high_risk_findings = [f for f in key_findings if "risk" in f["type"] and f["significance"] == "high"]
        if high_risk_findings:
            implications.append({
                "category": "risk",
                "level": "strategic",
                "description": "High-risk factors identified require immediate strategic attention",
                "potential_impact": "Significant operational and strategic implications",
                "timeframe": "immediate"
            })
        
        # Network implications
        network_insights = [insight for insight in insights if insight["category"] == "network"]
        if network_insights:
            implications.append({
                "category": "network",
                "level": "operational",
                "description": "Network relationships indicate coordinated activity patterns",
                "potential_impact": "Operational planning should account for network dynamics",
                "timeframe": "short-term"
            })
        
        # Pattern implications
        pattern_insights = [insight for insight in insights if insight["category"] == "behavioral"]
        if pattern_insights:
            implications.append({
                "category": "behavioral",
                "level": "tactical",
                "description": "Behavioral patterns suggest predictable activity cycles",
                "potential_impact": "Tactical operations can leverage pattern predictability",
                "timeframe": "medium-term"
            })
        
        return implications
    
    def _identify_intelligence_gaps(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Identify gaps in intelligence that need addressing."""
        
        gaps = {
            "critical_gaps": [],
            "moderate_gaps": [],
            "minor_gaps": [],
            "recommended_collection": []
        }
        
        # Check for missing entity types
        entities = fused_data.get("entities", [])
        entity_types = set(entity.get("type", "unknown") for entity in entities)
        
        if "person" not in entity_types:
            gaps["moderate_gaps"].append("person_entities")
        if "organization" not in entity_types:
            gaps["moderate_gaps"].append("organization_entities")
        
        # Check for temporal data gaps
        timeline = fused_data.get("timeline", [])
        if not timeline:
            gaps["critical_gaps"].append("temporal_analysis")
        
        # Check for geospatial data gaps
        geospatial = fused_data.get("geospatial", [])
        if not geospatial:
            gaps["moderate_gaps"].append("geospatial_analysis")
        
        # Check for context analysis gaps
        context_sections = [
            "historical_context", "cultural_context", 
            "geopolitical_context", "technical_context"
        ]
        
        missing_context = [
            section for section in context_sections 
            if section not in context_analysis or not context_analysis[section]
        ]
        
        for missing in missing_context:
            gaps["minor_gaps"].append(missing)
        
        # Generate collection recommendations
        if gaps["critical_gaps"]:
            gaps["recommended_collection"].append("Prioritize critical gap filling through targeted collection")
        if gaps["moderate_gaps"]:
            gaps["recommended_collection"].append("Expand collection to cover moderate intelligence gaps")
        if gaps["minor_gaps"]:
            gaps["recommended_collection"].append("Consider minor gap filling in subsequent collection phases")
        
        return gaps
    
    def _create_executive_summary(
        self, 
        key_findings: List[Dict[str, Any]], 
        insights: List[Dict[str, Any]], 
        user_request: str
    ) -> str:
        """Create executive summary of the intelligence synthesis."""
        
        high_significance_findings = [
            finding for finding in key_findings 
            if finding["significance"] == "high"
        ]
        
        high_value_insights = [
            insight for insight in insights 
            if insight["strategic_value"] == "high"
        ]
        
        summary = f"Intelligence synthesis for investigation: {user_request[:100]}...\n\n"
        
        summary += f"Analysis identified {len(key_findings)} key findings, "
        summary += f"with {len(high_significance_findings)} assessed as high significance. "
        
        if high_value_insights:
            summary += f"Generated {len(insights)} strategic insights, "
            summary += f"including {len(high_value_insights)} high-value strategic implications. "
        
        summary += "The synthesis reveals actionable intelligence for informed decision-making."
        
        return summary
    
    def _get_processing_time(self) -> float:
        """Get simulated processing time for the agent."""
        import random
        return random.uniform(2.0, 5.0)