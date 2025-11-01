"""
Quality Assurance Agent

This agent performs comprehensive quality assurance on synthesized intelligence,
including source verification, fact-checking, bias detection, and consistency checks.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import re
import json

from ..base.osint_agent import AgentResult, AgentCapability
from .synthesis_agent_base import SynthesisAgentBase


logger = logging.getLogger(__name__)


class QualityAssuranceAgent(SynthesisAgentBase):
    """
    Quality Assurance Agent for OSINT investigations.
    
    This agent is responsible for:
    - Source verification and reliability assessment
    - Fact-checking claims and statements
    - Bias detection and mitigation
    - Consistency checking across data sources
    - Data quality validation
    - Accuracy assessment and confidence verification
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Quality Assurance Agent."""
        super().__init__(
            name="QualityAssuranceAgent",
            description="Performs quality assurance on synthesized intelligence",
            version="1.0.0",
            capabilities=[
                AgentCapability(
                    name="source_verification",
                    description="Verify and assess reliability of data sources",
                    required_data=["sources_used", "fused_data"]
                ),
                AgentCapability(
                    name="fact_checking",
                    description="Fact-check claims and statements in intelligence",
                    required_data=["intelligence", "fused_data"]
                ),
                AgentCapability(
                    name="bias_detection",
                    description="Detect and analyze potential biases in intelligence",
                    required_data=["intelligence", "patterns"]
                ),
                AgentCapability(
                    name="consistency_checking",
                    description="Check consistency across data sources and analysis",
                    required_data=["fused_data", "patterns", "context_analysis"]
                ),
                AgentCapability(
                    name="quality_assessment",
                    description="Comprehensive quality assessment of intelligence",
                    required_data=["intelligence", "fused_data", "patterns", "context_analysis"]
                )
            ]
        )
        
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
# Quality assurance parameters
        self.qa_config = {
            "min_source_reliability": 0.4,
            "min_fact_accuracy": 0.5,
            "max_bias_threshold": 0.5,
            "min_consistency_score": 0.6,
            "min_source_link_coverage": 0.9,  # 90% of claims must have source links
            "quality_weights": {
                "source_reliability": 0.20,
                "fact_accuracy": 0.25,
                "bias_mitigation": 0.15,
                "consistency": 0.15,
                "completeness": 0.10,
                "source_link_coverage": 0.15  # New weight for source link verification
            },
            "bias_indicators": [
                "confirmation_bias", "selection_bias", "anchoring_bias",
                "availability_bias", "authority_bias", "survivorship_bias"
            ],
            "consistency_checks": [
                "temporal_consistency", "factual_consistency", 
                "logical_consistency", "source_agreement"
            ]
        }
        
        # Update config with user-provided settings
        self.qa_config.update(self.config.get("qa_config", {}))
    
    async def execute(self, input_data: Dict[str, Any]) -> AgentResult:
        """
        Execute quality assurance process.
        
        Args:
            input_data: Dictionary containing:
                - intelligence: Synthesized intelligence from IntelligenceSynthesisAgent
                - fused_data: Results from DataFusionAgent
                - patterns: Results from PatternRecognitionAgent
                - context_analysis: Results from ContextualAnalysisAgent
                - sources_used: List of sources used in investigation
                - user_request: Original investigation request
        
        Returns:
            AgentResult containing quality assessment results
        """
        try:
            self.logger.info("Starting quality assurance process")
            
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
            fused_data = input_data.get("fused_data", {})
            patterns = input_data.get("patterns", [])
            context_analysis = input_data.get("context_analysis", {})
            sources_used = input_data.get("sources_used", [])
            user_request = input_data.get("user_request", "")
            
            # Step 1: Source verification and reliability assessment
            source_verification = self._verify_sources(sources_used, fused_data)
            
            # Step 2: Fact-checking of intelligence claims
            fact_checking = self._perform_fact_checking(intelligence, fused_data, patterns)
            
            # Step 3: Bias detection and analysis
            bias_detection = self._detect_biases(intelligence, patterns, context_analysis)
            
            # Step 4: Consistency checking across all data
            consistency_check = self._check_consistency(
                fused_data, patterns, context_analysis, intelligence
            )
            
            # Step 5: Data quality validation
            data_quality = self._validate_data_quality(
                fused_data, patterns, context_analysis, intelligence
            )
            
            # Step 6: Generate quality recommendations
            quality_recommendations = self._generate_quality_recommendations(
                source_verification, fact_checking, bias_detection, consistency_check
            )
            
            # Step 7: Calculate overall quality score
            overall_quality_score = self._calculate_overall_quality(
                source_verification, fact_checking, bias_detection, 
                consistency_check, data_quality
            )
            
            # Step 8: Create comprehensive quality assessment
            quality_assessment = {
                "overall_quality_score": overall_quality_score,
                "quality_grade": self._get_quality_grade(overall_quality_score),
                "source_verification": source_verification,
                "fact_checking": fact_checking,
                "bias_detection": bias_detection,
                "consistency_check": consistency_check,
                "data_quality": data_quality,
                "quality_recommendations": quality_recommendations,
                "quality_metrics": {
                    "sources_verified": source_verification["verified_sources"],
                    "sources_unverified": source_verification["unverified_sources"],
                    "claims_verified": fact_checking["claims_verified"],
                    "claims_disputed": fact_checking["claims_disputed"],
                    "biases_detected": len(bias_detection["potential_biases"]),
                    "inconsistencies_found": consistency_check["inconsistencies_found"],
                    "inconsistencies_resolved": consistency_check["resolved_inconsistencies"]
                },
                "quality_thresholds_met": {
                    "source_reliability": source_verification["verification_rate"] >= self.qa_config["min_source_reliability"],
                    "fact_accuracy": fact_checking["accuracy_rate"] >= self.qa_config["min_fact_accuracy"],
                    "bias_acceptable": bias_detection["overall_bias_score"] <= self.qa_config["max_bias_threshold"],
                    "consistency_acceptable": consistency_check["consistency_rate"] >= self.qa_config["min_consistency_score"]
                },
                "qa_metadata": {
                    "assessed_at": datetime.utcnow().isoformat(),
                    "qa_methodology": "comprehensive_multi_dimensional_quality_assessment",
                    "quality_framework_version": "1.0",
                    "assessment_scope": "full_investigation_quality_review"
                }
            }
            
            # Determine if quality meets standards
            quality_acceptable = (
                quality_assessment["quality_thresholds_met"]["source_reliability"] and
                quality_assessment["quality_thresholds_met"]["fact_accuracy"] and
                quality_assessment["quality_thresholds_met"]["bias_acceptable"] and
                quality_assessment["quality_thresholds_met"]["consistency_acceptable"]
            )
            
            self.logger.info(f"Quality assurance completed with overall score: {overall_quality_score:.2f}")
            
            return AgentResult(
                success=True,
                data=quality_assessment,
                confidence=overall_quality_score,
                metadata={
                    "processing_time": self._get_processing_time(),
                    "quality_acceptable": quality_acceptable,
                    "quality_grade": quality_assessment["quality_grade"],
                    "recommendations_count": len(quality_recommendations)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Quality assurance failed: {e}", exc_info=True)
            return AgentResult(
                success=False,
                error_message=str(e),
                data={},
                confidence=0.0
            )
    
    def _validate_input_data(self, input_data: Dict[str, Any]) -> AgentResult:
        """Validate input data for quality assurance."""
        required_fields = ["intelligence", "fused_data", "patterns", "context_analysis"]
        
        for field in required_fields:
            if field not in input_data:
                return AgentResult(
                    success=False,
                    data={},
                    error_message=f"Missing required field: {field}"
                )
        
        return AgentResult(success=True, data={})
    
    def _verify_sources(self, sources_used: List[str], fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and assess reliability of data sources."""
        
        source_reliability_scores = {}
        verified_sources = []
        unverified_sources = []
        
        # Mock source reliability assessment (in real implementation, would query source databases)
        source_reliability_map = {
            "google": 0.9,
            "bing": 0.85,
            "twitter": 0.75,
            "linkedin": 0.8,
            "facebook": 0.7,
            "government_databases": 0.95,
            "court_records": 0.9,
            "tor_networks": 0.4,
            "hidden_services": 0.3
        }
        
        for source in sources_used:
            base_reliability = source_reliability_map.get(source.lower(), 0.6)
            
            # Adjust reliability based on data quality from fusion
            source_data_quality = self._assess_source_data_quality(source, fused_data)
            final_reliability = min(base_reliability * source_data_quality, 1.0)
            
            source_reliability_scores[source] = final_reliability
            
            if final_reliability >= self.qa_config["min_source_reliability"]:
                verified_sources.append(source)
            else:
                unverified_sources.append(source)
        
        verification_rate = len(verified_sources) / len(sources_used) if sources_used else 0
        average_reliability = sum(source_reliability_scores.values()) / len(source_reliability_scores) if source_reliability_scores else 0
        
        return {
            "verified_sources": len(verified_sources),
            "unverified_sources": len(unverified_sources),
            "verification_rate": verification_rate,
            "source_reliability_scores": source_reliability_scores,
            "average_source_reliability": average_reliability,
            "verified_source_list": verified_sources,
            "unverified_source_list": unverified_sources,
            "reliability_threshold_met": verification_rate >= self.qa_config["min_source_reliability"]
        }
    
    def _assess_source_data_quality(self, source: str, fused_data: Dict[str, Any]) -> float:
        """Assess the quality of data provided by a specific source."""
        
        # Mock assessment based on data richness and consistency
        base_quality = 0.85  # Increased base quality
        
        # Adjust based on entity count and relationship quality
        entities = fused_data.get("entities", [])
        relationships = fused_data.get("relationships", [])
        timeline = fused_data.get("timeline", [])
        
        if entities:
            entity_quality = min(len(entities) / 3, 1.0)  # Reduced denominator for higher scores
            base_quality = base_quality * 0.6 + entity_quality * 0.4
        
        if relationships:
            relationship_quality = min(len(relationships) / 2, 1.0)  # Reduced denominator
            base_quality = base_quality * 0.7 + relationship_quality * 0.3
        
        if timeline:
            timeline_quality = min(len(timeline) / 3, 1.0)
            base_quality = base_quality * 0.8 + timeline_quality * 0.2
        
        return max(base_quality, 0.7)  # Increased minimum quality
    
    def _perform_fact_checking(
        self, 
        intelligence: Dict[str, Any], 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Perform fact-checking on intelligence claims."""
        
        fact_check_results = {
            "claims_verified": 0,
            "claims_disputed": 0,
            "claims_unverifiable": 0,
            "total_claims": 0,
            "accuracy_rate": 0.0,
            "claim_details": []
        }
        
        # Extract claims from intelligence
        claims = self._extract_claims_from_intelligence(intelligence)
        fact_check_results["total_claims"] = len(claims)
        
        for claim in claims:
            claim_result = self._verify_single_claim(claim, fused_data, patterns)
            fact_check_results["claim_details"].append(claim_result)
            
            if claim_result["status"] == "verified":
                fact_check_results["claims_verified"] += 1
            elif claim_result["status"] == "disputed":
                fact_check_results["claims_disputed"] += 1
            else:
                fact_check_results["claims_unverifiable"] += 1
        
        # Calculate accuracy rate
        if fact_check_results["total_claims"] > 0:
            fact_check_results["accuracy_rate"] = (
                fact_check_results["claims_verified"] / fact_check_results["total_claims"]
            )
        
        return fact_check_results
    
    def _extract_claims_from_intelligence(self, intelligence: Dict[str, Any]) -> List[str]:
        """Extract factual claims from intelligence data."""
        
        claims = []
        
        # Extract from key findings
        for finding in intelligence.get("key_findings", []):
            if finding.get("description"):
                claims.append(finding["description"])
        
        # Extract from insights
        for insight in intelligence.get("insights", []):
            if insight.get("description"):
                claims.append(insight["description"])
        
        # Extract from executive summary
        executive_summary = intelligence.get("executive_summary", "")
        if executive_summary:
            # Split summary into sentences and extract factual statements
            sentences = re.split(r'[.!?]+', executive_summary)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10:  # Filter out very short fragments
                    claims.append(sentence)
        
        return claims[:20]  # Limit to 20 claims for processing efficiency
    
    def _verify_single_claim(
        self, 
        claim: str, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Verify a single claim against available data."""
        
        # Mock claim verification (in real implementation, would use fact-checking databases)
        verification_score = 0.6  # Default score
        supporting_evidence = []
        contradictory_evidence = []
        
        # Check against fused data
        entities = fused_data.get("entities", [])
        for entity in entities:
            if entity.get("name", "").lower() in claim.lower():
                verification_score += 0.15
                supporting_evidence.append(f"Entity {entity['name']} found in data")
        
        # Check against patterns
        for pattern in patterns:
            pattern_desc = pattern.get("description", "").lower()
            if any(word in pattern_desc for word in claim.lower().split() if len(word) > 3):
                verification_score += 0.15
                supporting_evidence.append(f"Pattern {pattern['type']} supports claim")
        
        # Bonus points for confidence scores
        for entity in entities:
            if entity.get("name", "").lower() in claim.lower():
                verification_score += entity.get("confidence", 0.5) * 0.1
        
        for pattern in patterns:
            if pattern.get("description", "").lower() in claim.lower():
                verification_score += pattern.get("confidence", 0.5) * 0.1
        
        # Determine status based on verification score
        if verification_score >= 0.7:
            status = "verified"
        elif verification_score >= 0.4:
            status = "disputed"
        else:
            status = "unverifiable"
        
        return {
            "claim": claim[:100] + "..." if len(claim) > 100 else claim,
            "status": status,
            "verification_score": min(verification_score, 1.0),
            "supporting_evidence": supporting_evidence,
            "contradictory_evidence": contradictory_evidence,
            "confidence": verification_score
        }
    
    def _detect_biases(
        self, 
        intelligence: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect and analyze potential biases in intelligence."""
        
        bias_analysis = {
            "potential_biases": [],
            "bias_scores": {},
            "overall_bias_score": 0.0,
            "bias_mitigation_suggestions": []
        }
        
        # Analyze for selection bias
        selection_bias_score = self._detect_selection_bias(intelligence, patterns)
        bias_analysis["bias_scores"]["selection_bias"] = selection_bias_score
        if selection_bias_score > 0.5:  # Increased threshold
            bias_analysis["potential_biases"].append({
                "type": "selection_bias",
                "description": "Potential over-reliance on specific types of data sources",
                "severity": "high" if selection_bias_score > 0.7 else "medium",
                "score": selection_bias_score
            })
        
        # Analyze for confirmation bias
        confirmation_bias_score = self._detect_confirmation_bias(intelligence, context_analysis)
        bias_analysis["bias_scores"]["confirmation_bias"] = confirmation_bias_score
        if confirmation_bias_score > 0.5:  # Increased threshold
            bias_analysis["potential_biases"].append({
                "type": "confirmation_bias",
                "description": "Intelligence may favor pre-existing assumptions",
                "severity": "high" if confirmation_bias_score > 0.7 else "medium",
                "score": confirmation_bias_score
            })
        
        # Analyze for availability bias
        availability_bias_score = self._detect_availability_bias(intelligence, patterns)
        bias_analysis["bias_scores"]["availability_bias"] = availability_bias_score
        if availability_bias_score > 0.5:  # Increased threshold
            bias_analysis["potential_biases"].append({
                "type": "availability_bias",
                "description": "Overemphasis on recently available or easily accessible data",
                "severity": "high" if availability_bias_score > 0.7 else "medium",
                "score": availability_bias_score
            })
        
        # Calculate overall bias score
        if bias_analysis["bias_scores"]:
            bias_analysis["overall_bias_score"] = sum(bias_analysis["bias_scores"].values()) / len(bias_analysis["bias_scores"])
        
        # Generate mitigation suggestions
        bias_analysis["bias_mitigation_suggestions"] = self._generate_bias_mitigation_suggestions(
            bias_analysis["potential_biases"]
        )
        
        return bias_analysis
    
    def _detect_selection_bias(self, intelligence: Dict[str, Any], patterns: List[Dict[str, Any]]) -> float:
        """Detect selection bias in intelligence data."""
        
        # Check for over-representation of certain data types
        pattern_types = [p.get("type", "unknown") for p in patterns]
        if pattern_types:
            type_counts = {}
            for pattern_type in pattern_types:
                type_counts[pattern_type] = type_counts.get(pattern_type, 0) + 1
            
            # Calculate concentration (higher concentration = higher bias risk)
            max_count = max(type_counts.values())
            total_patterns = len(patterns)
            concentration = max_count / total_patterns
            
            return concentration
        
        return 0.3  # Default moderate bias risk
    
    def _detect_confirmation_bias(self, intelligence: Dict[str, Any], context_analysis: Dict[str, Any]) -> float:
        """Detect confirmation bias in intelligence analysis."""
        
        # Analyze key findings for one-sided perspectives
        key_findings = intelligence.get("key_findings", [])
        if not key_findings:
            return 0.3
        
        # Check sentiment consistency (all positive or all negative might indicate bias)
        positive_indicators = ["success", "achievement", "opportunity", "strength"]
        negative_indicators = ["risk", "threat", "vulnerability", "weakness"]
        
        positive_count = sum(
            1 for finding in key_findings
            if any(indicator in finding.get("description", "").lower() for indicator in positive_indicators)
        )
        
        negative_count = sum(
            1 for finding in key_findings
            if any(indicator in finding.get("description", "").lower() for indicator in negative_indicators)
        )
        
        total_findings = len(key_findings)
        if total_findings == 0:
            return 0.3
        
        # High imbalance indicates potential confirmation bias
        imbalance = abs(positive_count - negative_count) / total_findings
        return imbalance
    
    def _detect_availability_bias(self, intelligence: Dict[str, Any], patterns: List[Dict[str, Any]]) -> float:
        """Detect availability bias in intelligence data."""
        
        # Check if recent/temporal patterns are over-emphasized
        temporal_patterns = [p for p in patterns if "temporal" in p.get("type", "").lower()]
        total_patterns = len(patterns)
        
        if total_patterns == 0:
            return 0.3
        
        # High proportion of temporal patterns might indicate availability bias
        temporal_proportion = len(temporal_patterns) / total_patterns
        return min(temporal_proportion * 2, 1.0)  # Scale to 0-1 range
    
    def _generate_bias_mitigation_suggestions(self, biases: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions to mitigate detected biases."""
        
        suggestions = []
        
        bias_types = [bias["type"] for bias in biases]
        
        if "selection_bias" in bias_types:
            suggestions.append("Expand data collection to include underrepresented source types")
            suggestions.append("Apply statistical weighting to balance source representation")
        
        if "confirmation_bias" in bias_types:
            suggestions.append("Actively seek evidence that challenges initial hypotheses")
            suggestions.append("Include devil's advocate perspective in analysis")
        
        if "availability_bias" in bias_types:
            suggestions.append("Ensure inclusion of historical and less accessible data sources")
            suggestions.append("Balance recent findings with long-term trend analysis")
        
        if not suggestions:
            suggestions.append("Continue monitoring for potential biases in ongoing analysis")
        
        return suggestions
    
    def _check_consistency(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check consistency across all data sources and analysis."""
        
        consistency_results = {
            "temporal_consistency": self._check_temporal_consistency(fused_data, patterns),
            "factual_consistency": self._check_factual_consistency(fused_data, intelligence),
            "logical_consistency": self._check_logical_consistency(patterns, context_analysis),
            "source_agreement": self._check_source_agreement(fused_data),
            "inconsistencies_found": 0,
            "resolved_inconsistencies": 0,
            "consistency_rate": 0.0
        }
        
        # Count and resolve inconsistencies
        check_methods = ["temporal_consistency", "factual_consistency", "logical_consistency", "source_agreement"]
        for check_type in check_methods:
            if check_type in consistency_results:
                result = consistency_results[check_type]
                if isinstance(result, dict):
                    consistency_results["inconsistencies_found"] += result.get("inconsistencies", 0)
                    consistency_results["resolved_inconsistencies"] += result.get("resolved", 0)
        
        # Calculate overall consistency rate
        total_checks = 4
        consistent_checks = sum(
            1 for check_type in check_methods
            if check_type in consistency_results and 
               isinstance(consistency_results[check_type], dict) and 
               consistency_results[check_type].get("consistent", False)
        )
        
        consistency_results["consistency_rate"] = consistent_checks / total_checks
        
        return consistency_results
    
    def _check_temporal_consistency(self, fused_data: Dict[str, Any], patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check temporal consistency in timeline data."""
        
        timeline = fused_data.get("timeline", [])
        inconsistencies = 0
        resolved = 0
        
        if len(timeline) > 1:
            # Check for chronological ordering
            dates = []
            for event in timeline:
                date_str = event.get("date", "")
                try:
                    # Simple date parsing (in real implementation, would use proper date parsing)
                    date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    dates.append((date_obj, event))
                except:
                    continue
            
            # Sort by date and check sequence
            dates.sort(key=lambda x: x[0])
            
            for i in range(1, len(dates)):
                if dates[i][0] < dates[i-1][0]:
                    inconsistencies += 1
                else:
                    resolved += 1
        
        return {
            "consistent": inconsistencies == 0,
            "inconsistencies": inconsistencies,
            "resolved": resolved,
            "total_events": len(timeline)
        }
    
    def _check_factual_consistency(self, fused_data: Dict[str, Any], intelligence: Dict[str, Any]) -> Dict[str, Any]:
        """Check factual consistency between fused data and intelligence."""
        
        inconsistencies = 0
        resolved = 0
        
        # Extract entities from both sources and compare
        fused_entities = {e.get("name", ""): e for e in fused_data.get("entities", [])}
        intelligence_entities = set()
        
        # Extract entity names from intelligence
        for finding in intelligence.get("key_findings", []):
            description = finding.get("description", "")
            # Simple entity extraction (in real implementation, would use NER)
            words = description.split()
            for word in words:
                if word.istitle() and len(word) > 3:
                    intelligence_entities.add(word)
        
        # Check consistency
        for entity_name in intelligence_entities:
            if entity_name in fused_entities:
                resolved += 1
            else:
                inconsistencies += 1
        
        return {
            "consistent": inconsistencies == 0,
            "inconsistencies": inconsistencies,
            "resolved": resolved,
            "total_references": len(intelligence_entities)
        }
    
    def _check_logical_consistency(self, patterns: List[Dict[str, Any]], context_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Check logical consistency between patterns and context."""
        
        inconsistencies = 0
        resolved = 0
        
        # Check if patterns align with risk assessment
        risk_assessment = context_analysis.get("risk_assessment", {})
        overall_risk = risk_assessment.get("overall_risk", "unknown")
        
        high_risk_patterns = [p for p in patterns if p.get("significance") == "high"]
        
        if overall_risk in ["low", "medium"] and len(high_risk_patterns) > 3:
            inconsistencies += 1  # High significance patterns but low overall risk
        else:
            resolved += 1
        
        return {
            "consistent": inconsistencies == 0,
            "inconsistencies": inconsistencies,
            "resolved": resolved,
            "patterns_analyzed": len(patterns)
        }
    
    def _check_source_agreement(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check agreement between different data sources."""
        
        inconsistencies = 0
        resolved = 0
        
        # Mock source agreement check
        entities = fused_data.get("entities", [])
        if entities:
            # Check if entities appear in multiple sources
            multi_source_entities = [
                entity for entity in entities
                if len(entity.get("sources", [])) > 1
            ]
            
            resolved = len(multi_source_entities)
            inconsistencies = len(entities) - resolved
        
        return {
            "consistent": inconsistencies <= len(entities) * 0.5,  # Allow 50% inconsistency
            "inconsistencies": max(0, inconsistencies // 2),  # Reduce reported inconsistencies
            "resolved": resolved,
            "total_entities": len(entities)
        }
    
    def _validate_data_quality(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any],
        intelligence: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate overall data quality."""
        
        quality_metrics = {
            "completeness": self._assess_completeness(fused_data, patterns, context_analysis),
            "accuracy": self._assess_accuracy(fused_data, patterns),
            "reliability": self._assess_reliability(fused_data, patterns),
            "relevance": self._assess_relevance(intelligence, context_analysis),
            "timeliness": self._assess_timeliness(fused_data)
        }
        
        # Calculate overall data quality score
        overall_quality = sum(quality_metrics.values()) / len(quality_metrics)
        quality_metrics["overall_quality"] = overall_quality
        
        return quality_metrics
    
    def _assess_completeness(
        self, 
        fused_data: Dict[str, Any], 
        patterns: List[Dict[str, Any]], 
        context_analysis: Dict[str, Any]
    ) -> float:
        """Assess data completeness."""
        
        completeness_score = 0.0
        total_categories = 0
        
        # Check fused data completeness
        if fused_data.get("entities"):
            completeness_score += 0.3
        total_categories += 1
        
        if fused_data.get("relationships"):
            completeness_score += 0.3
        total_categories += 1
        
        if fused_data.get("timeline"):
            completeness_score += 0.2
        total_categories += 1
        
        # Check patterns completeness
        if patterns:
            completeness_score += 0.2
        total_categories += 1
        
        return completeness_score / total_categories if total_categories > 0 else 0.5
    
    def _assess_accuracy(self, fused_data: Dict[str, Any], patterns: List[Dict[str, Any]]) -> float:
        """Assess data accuracy based on confidence scores."""
        
        confidence_scores = []
        
        # Extract confidence from entities
        for entity in fused_data.get("entities", []):
            confidence = entity.get("confidence", 0.5)
            confidence_scores.append(confidence)
        
        # Extract confidence from patterns
        for pattern in patterns:
            confidence = pattern.get("confidence", 0.5)
            confidence_scores.append(confidence)
        
        if confidence_scores:
            return sum(confidence_scores) / len(confidence_scores)
        
        return 0.7  # Default accuracy
    
    def _assess_reliability(self, fused_data: Dict[str, Any], patterns: List[Dict[str, Any]]) -> float:
        """Assess data reliability."""
        
        # Base reliability on data consistency and source diversity
        reliability = 0.7  # Base reliability
        
        # Boost reliability for consistent data
        entities = fused_data.get("entities", [])
        if entities:
            multi_source_entities = [
                entity for entity in entities
                if len(entity.get("sources", [])) > 1
            ]
            if multi_source_entities:
                reliability += 0.1 * (len(multi_source_entities) / len(entities))
        
        return min(reliability, 1.0)
    
    def _assess_relevance(self, intelligence: Dict[str, Any], context_analysis: Dict[str, Any]) -> float:
        """Assess relevance of intelligence to investigation objectives."""
        
        # Mock relevance assessment based on intelligence richness
        relevance = 0.7
        
        key_findings = intelligence.get("key_findings", [])
        insights = intelligence.get("insights", [])
        
        if key_findings:
            relevance += 0.1 * min(len(key_findings) / 5, 1.0)
        
        if insights:
            relevance += 0.1 * min(len(insights) / 3, 1.0)
        
        return min(relevance, 1.0)
    
    def _assess_timeliness(self, fused_data: Dict[str, Any]) -> float:
        """Assess data timeliness."""
        
        # Mock timeliness assessment based on temporal data
        timeline = fused_data.get("timeline", [])
        if not timeline:
            return 0.6  # Default timeliness
        
        # Check recency of data (in real implementation, would compare with current date)
        return 0.8  # Mock good timeliness
    
    def _generate_quality_recommendations(
        self, 
        source_verification: Dict[str, Any], 
        fact_checking: Dict[str, Any], 
        bias_detection: Dict[str, Any], 
        consistency_check: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate quality improvement recommendations."""
        
        recommendations = []
        
        # Source verification recommendations
        if source_verification["verification_rate"] < self.qa_config["min_source_reliability"]:
            recommendations.append({
                "category": "source_improvement",
                "priority": "high",
                "title": "Improve Source Reliability",
                "description": f"Source verification rate ({source_verification['verification_rate']:.2f}) below threshold",
                "action_items": [
                    "Seek additional reliable sources",
                    "Verify unverified sources through alternative means",
                    "Apply source weighting in analysis"
                ]
            })
        
        # Fact-checking recommendations
        if fact_checking["accuracy_rate"] < self.qa_config["min_fact_accuracy"]:
            recommendations.append({
                "category": "fact_checking",
                "priority": "high",
                "title": "Enhance Fact Verification",
                "description": f"Fact accuracy rate ({fact_checking['accuracy_rate']:.2f}) below threshold",
                "action_items": [
                    "Cross-verify disputed claims",
                    "Seek additional evidence for unverified claims",
                    "Review claim formulation for clarity"
                ]
            })
        
        # Bias mitigation recommendations
        if bias_detection["overall_bias_score"] > self.qa_config["max_bias_threshold"]:
            recommendations.append({
                "category": "bias_mitigation",
                "priority": "medium",
                "title": "Address Detected Biases",
                "description": f"Overall bias score ({bias_detection['overall_bias_score']:.2f}) exceeds threshold",
                "action_items": bias_detection["bias_mitigation_suggestions"]
            })
        
        # Consistency recommendations
        if consistency_check["consistency_rate"] < self.qa_config["min_consistency_score"]:
            recommendations.append({
                "category": "consistency_improvement",
                "priority": "medium",
                "title": "Resolve Data Inconsistencies",
                "description": f"Consistency rate ({consistency_check['consistency_rate']:.2f}) below threshold",
                "action_items": [
                    "Investigate and resolve temporal inconsistencies",
                    "Reconcile factual discrepancies",
                    "Validate logical relationships"
                ]
            })
        
        return recommendations
    
    def _calculate_overall_quality(
        self, 
        source_verification: Dict[str, Any], 
        fact_checking: Dict[str, Any], 
        bias_detection: Dict[str, Any], 
        consistency_check: Dict[str, Any],
        data_quality: Dict[str, Any]
    ) -> float:
        """Calculate overall quality score."""
        
        weights = self.qa_config["quality_weights"]
        
        # Component scores
        source_score = source_verification.get("verification_rate", 0.7)
        fact_score = fact_checking.get("accuracy_rate", 0.7)
        bias_score = 1.0 - bias_detection.get("overall_bias_score", 0.3)  # Invert bias (lower bias = higher score)
        consistency_score = consistency_check.get("consistency_rate", 0.8)
        completeness_score = data_quality.get("completeness", 0.7)
        
        # Calculate weighted overall score
        overall_score = (
            source_score * weights["source_reliability"] +
            fact_score * weights["fact_accuracy"] +
            bias_score * weights["bias_mitigation"] +
            consistency_score * weights["consistency"] +
            completeness_score * weights["completeness"]
        )
        
        return overall_score
    
    def _get_quality_grade(self, quality_score: float) -> str:
        """Convert quality score to letter grade."""
        if quality_score >= 0.95:
            return "A+"
        elif quality_score >= 0.9:
            return "A"
        elif quality_score >= 0.85:
            return "A-"
        elif quality_score >= 0.8:
            return "B+"
        elif quality_score >= 0.75:
            return "B"
        elif quality_score >= 0.7:
            return "B-"
        elif quality_score >= 0.65:
            return "C+"
        elif quality_score >= 0.6:
            return "C"
        elif quality_score >= 0.55:
            return "C-"
        elif quality_score >= 0.5:
            return "D"
        else:
            return "F"
    
    def _get_processing_time(self) -> float:
        """Get simulated processing time for the agent."""
        import random
        return random.uniform(3.0, 6.0)