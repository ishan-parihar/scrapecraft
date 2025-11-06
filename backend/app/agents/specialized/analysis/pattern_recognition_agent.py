"""
Pattern Recognition Agent for OSINT investigations.
"""

import asyncio
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
import json
import logging

from ...base.osint_agent import OSINTAgent, LLMOSINTAgent, AgentConfig, AgentResult


class PatternRecognitionAgent(LLMOSINTAgent):
    """
    Agent responsible for recognizing patterns in OSINT data.
    Handles behavioral patterns, communication patterns, network patterns, and anomaly detection.
    """
    
    def __init__(self, config: AgentConfig, tools: Optional[List[Any]] = None, memory: Optional[Any] = None, logger: Optional[logging.Logger] = None):
        # Initialize with default config if not provided
        if not config:
            config = AgentConfig(
                agent_id="pattern_recognition_agent",
                role="Pattern Recognition Agent",
                description="Agent responsible for recognizing patterns in OSINT data"
            )
        
        super().__init__(config=config, tools=tools, memory=memory, logger=logger)
        
        self.supported_pattern_types = [
            "behavioral", "communication", "network", "temporal", 
            "linguistic", "geographical", "financial", "technical"
        ]
        self.pattern_confidence_threshold = 0.6
        self.anomaly_threshold = 2.0  # Standard deviations
        
    async def detect_behavioral_patterns(
        self, 
        entities: List[Dict[str, Any]],
        pattern_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect behavioral patterns in entity activities.
        
        Args:
            entities: List of entities with activity data
            pattern_types: Types of behavioral patterns to detect
            
        Returns:
            Dictionary containing detected behavioral patterns
        """
        if pattern_types is None:
            pattern_types = ["routine", "anomalous", "coordinated", "escalating"]
            
        self.logger.info(f"Detecting behavioral patterns for {len(entities)} entities")
        
        try:
            detected_patterns = []
            
            for pattern_type in pattern_types:
                patterns = await self._detect_specific_behavioral_pattern(entities, pattern_type)
                detected_patterns.extend(patterns)
            
            # Analyze pattern significance
            significant_patterns = await self._analyze_pattern_significance(detected_patterns)
            
            # Generate pattern insights
            insights = await self._generate_pattern_insights(significant_patterns)
            
            analysis_data = {
                "source": "behavioral_pattern_detection",
                "timestamp": time.time(),
                "entities_analyzed": len(entities),
                "pattern_types": pattern_types,
                "detected_patterns": detected_patterns,
                "significant_patterns": significant_patterns,
                "insights": insights,
                "analysis_success": True
            }
            
            self.logger.info(f"Behavioral pattern analysis completed, {len(detected_patterns)} patterns found")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Error in behavioral pattern detection: {str(e)}")
            return {
                "error": str(e),
                "source": "behavioral_pattern_detection",
                "analysis_success": False
            }
    
    async def detect_communication_patterns(
        self, 
        communications: List[Dict[str, Any]],
        analysis_scope: str = "comprehensive"
    ) -> Dict[str, Any]:
        """
        Detect patterns in communication data.
        
        Args:
            communications: List of communication records
            analysis_scope: Scope of analysis ("basic", "comprehensive", "deep")
            
        Returns:
            Dictionary containing communication pattern analysis
        """
        self.logger.info(f"Analyzing communication patterns for {len(communications)} communications")
        
        try:
            # Temporal patterns
            temporal_patterns = await self._analyze_temporal_communication_patterns(communications)
            
            # Content patterns
            content_patterns = await self._analyze_content_patterns(communications)
            
            # Network patterns
            network_patterns = await self._analyze_communication_network_patterns(communications)
            
            # Stylistic patterns
            stylistic_patterns = await self._analyze_stylistic_patterns(communications)
            
            if analysis_scope == "deep":
                # Advanced analysis
                semantic_patterns = await self._analyze_semantic_patterns(communications)
                sentiment_patterns = await self._analyze_sentiment_patterns(communications)
            else:
                semantic_patterns = []
                sentiment_patterns = []
            
            # Combine and prioritize patterns
            combined_patterns = await self._combine_communication_patterns(
                temporal_patterns, content_patterns, network_patterns, 
                stylistic_patterns, semantic_patterns, sentiment_patterns
            )
            
            analysis_data = {
                "source": "communication_pattern_detection",
                "analysis_scope": analysis_scope,
                "timestamp": time.time(),
                "communications_analyzed": len(communications),
                "temporal_patterns": temporal_patterns,
                "content_patterns": content_patterns,
                "network_patterns": network_patterns,
                "stylistic_patterns": stylistic_patterns,
                "semantic_patterns": semantic_patterns,
                "sentiment_patterns": sentiment_patterns,
                "combined_patterns": combined_patterns,
                "analysis_success": True
            }
            
            self.logger.info(f"Communication pattern analysis completed, {len(combined_patterns)} patterns identified")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Error in communication pattern detection: {str(e)}")
            return {
                "error": str(e),
                "source": "communication_pattern_detection",
                "analysis_success": False
            }
    
    async def detect_network_patterns(
        self, 
        network_data: Dict[str, Any],
        pattern_categories: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Detect patterns in network structure and dynamics.
        
        Args:
            network_data: Network graph and connectivity data
            pattern_categories: Categories of network patterns to detect
            
        Returns:
            Dictionary containing network pattern analysis
        """
        if pattern_categories is None:
            pattern_categories = ["structural", "temporal", "influence", "community"]
            
        self.logger.info(f"Analyzing network patterns for {pattern_categories}")
        
        try:
            detected_patterns = []
            
            # Structural patterns
            if "structural" in pattern_categories:
                structural_patterns = await self._detect_structural_patterns(network_data)
                detected_patterns.extend(structural_patterns)
            
            # Temporal patterns
            if "temporal" in pattern_categories:
                temporal_patterns = await self._detect_temporal_network_patterns(network_data)
                detected_patterns.extend(temporal_patterns)
            
            # Influence patterns
            if "influence" in pattern_categories:
                influence_patterns = await self._detect_influence_patterns(network_data)
                detected_patterns.extend(influence_patterns)
            
            # Community patterns
            if "community" in pattern_categories:
                community_patterns = await self._detect_community_patterns(network_data)
                detected_patterns.extend(community_patterns)
            
            # Anomaly detection
            anomalies = await self._detect_network_anomalies(network_data)
            
            # Generate network insights
            insights = await self._generate_network_insights(detected_patterns, anomalies)
            
            analysis_data = {
                "source": "network_pattern_detection",
                "timestamp": time.time(),
                "pattern_categories": pattern_categories,
                "detected_patterns": detected_patterns,
                "anomalies": anomalies,
                "insights": insights,
                "network_metrics": await self._calculate_pattern_network_metrics(network_data),
                "analysis_success": True
            }
            
            self.logger.info(f"Network pattern analysis completed, {len(detected_patterns)} patterns found")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Error in network pattern detection: {str(e)}")
            return {
                "error": str(e),
                "source": "network_pattern_detection",
                "analysis_success": False
            }
    
    async def detect_anomalies(
        self, 
        data: List[Dict[str, Any]],
        anomaly_types: Optional[List[str]] = None,
        sensitivity: float = 0.05
    ) -> Dict[str, Any]:
        """
        Detect anomalies in OSINT data.
        
        Args:
            data: Data to analyze for anomalies
            anomaly_types: Types of anomalies to detect
            sensitivity: Sensitivity threshold for anomaly detection
            
        Returns:
            Dictionary containing anomaly detection results
        """
        if anomaly_types is None:
            anomaly_types = ["statistical", "temporal", "structural", "behavioral"]
            
        self.logger.info(f"Detecting anomalies with sensitivity {sensitivity}")
        
        try:
            detected_anomalies = []
            
            for anomaly_type in anomaly_types:
                anomalies = await self._detect_specific_anomalies(data, anomaly_type, sensitivity)
                detected_anomalies.extend(anomalies)
            
            # Classify anomalies by severity
            classified_anomalies = await self._classify_anomaly_severity(detected_anomalies)
            
            # Generate anomaly explanations
            explanations = await self._generate_anomaly_explanations(classified_anomalies)
            
            # Recommend investigation priorities
            priorities = await self._prioritize_anomaly_investigation(classified_anomalies)
            
            analysis_data = {
                "source": "anomaly_detection",
                "timestamp": time.time(),
                "data_points_analyzed": len(data),
                "anomaly_types": anomaly_types,
                "sensitivity": sensitivity,
                "detected_anomalies": detected_anomalies,
                "classified_anomalies": classified_anomalies,
                "explanations": explanations,
                "investigation_priorities": priorities,
                "analysis_success": True
            }
            
            self.logger.info(f"Anomaly detection completed, {len(detected_anomalies)} anomalies found")
            return analysis_data
            
        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {str(e)}")
            return {
                "error": str(e),
                "source": "anomaly_detection",
                "analysis_success": False
            }
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a pattern recognition task.
        
        Args:
            task: Task dictionary containing pattern recognition parameters
            
        Returns:
            Dictionary containing pattern recognition results
        """
        task_type = task.get("task_type", "behavioral_patterns")
        results = []
        
        if task_type == "behavioral_patterns":
            # Behavioral pattern detection
            entities = task.get("entities", [])
            pattern_types = task.get("pattern_types")
            
            if entities:
                result = await self.detect_behavioral_patterns(entities, pattern_types)
                results.append(result)
        
        elif task_type == "communication_patterns":
            # Communication pattern detection
            communications = task.get("communications", [])
            analysis_scope = task.get("analysis_scope", "comprehensive")
            
            if communications:
                result = await self.detect_communication_patterns(communications, analysis_scope)
                results.append(result)
        
        elif task_type == "network_patterns":
            # Network pattern detection
            network_data = task.get("network_data", {})
            pattern_categories = task.get("pattern_categories")
            
            if network_data:
                result = await self.detect_network_patterns(network_data, pattern_categories)
                results.append(result)
        
        elif task_type == "anomaly_detection":
            # Anomaly detection
            data = task.get("data", [])
            anomaly_types = task.get("anomaly_types")
            sensitivity = task.get("sensitivity", 0.05)
            
            if data:
                result = await self.detect_anomalies(data, anomaly_types, sensitivity)
                results.append(result)
        
        return {
            "agent_id": self.config.agent_id,
            "task_type": task_type,
            "timestamp": time.time(),
            "results": results,
            "total_analyses": len(results),
            "status": "completed"
        }
    
    async def _detect_specific_behavioral_pattern(self, entities: List[Dict[str, Any]], pattern_type: str) -> List[Dict[str, Any]]:
        """Detect specific behavioral patterns."""
        patterns = []
        
        if pattern_type == "routine":
            # Detect routine patterns
            for entity in entities:
                routine_score = self._calculate_routine_score(entity)
                if routine_score > 0.7:
                    patterns.append({
                        "type": "routine",
                        "entity_id": entity.get("id"),
                        "confidence": routine_score,
                        "description": "Strong routine behavior detected",
                        "details": await self._analyze_routine_details(entity)
                    })
        
        elif pattern_type == "anomalous":
            # Detect anomalous behavior
            for entity in entities:
                anomaly_score = self._calculate_behavioral_anomaly_score(entity)
                if anomaly_score > 0.8:
                    patterns.append({
                        "type": "anomalous",
                        "entity_id": entity.get("id"),
                        "confidence": anomaly_score,
                        "description": "Anomalous behavior detected",
                        "details": await self._analyze_anomaly_details(entity)
                    })
        
        elif pattern_type == "coordinated":
            # Detect coordinated behavior
            coordination_patterns = await self._detect_coordination_patterns(entities)
            patterns.extend(coordination_patterns)
        
        elif pattern_type == "escalating":
            # Detect escalating behavior
            for entity in entities:
                escalation_score = self._calculate_escalation_score(entity)
                if escalation_score > 0.6:
                    patterns.append({
                        "type": "escalating",
                        "entity_id": entity.get("id"),
                        "confidence": escalation_score,
                        "description": "Escalating behavior pattern detected",
                        "details": await self._analyze_escalation_details(entity)
                    })
        
        return patterns
    
    def _calculate_routine_score(self, entity: Dict[str, Any]) -> float:
        """Calculate routine behavior score."""
        # Simulate routine calculation based on temporal regularity
        return 0.75 + (hash(entity.get("id", "")) % 100) / 400  # 0.75-1.0 range
    
    def _calculate_behavioral_anomaly_score(self, entity: Dict[str, Any]) -> float:
        """Calculate behavioral anomaly score."""
        # Simulate anomaly calculation
        return 0.6 + (hash(entity.get("id", "")) % 100) / 250  # 0.6-1.0 range
    
    def _calculate_escalation_score(self, entity: Dict[str, Any]) -> float:
        """Calculate escalation behavior score."""
        # Simulate escalation calculation
        return 0.5 + (hash(entity.get("id", "")) % 100) / 200  # 0.5-1.0 range
    
    async def _detect_coordination_patterns(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect coordinated behavior patterns."""
        patterns = []
        
        # Simulate coordination detection
        if len(entities) >= 2:
            patterns.append({
                "type": "coordinated",
                "entity_ids": [e.get("id") for e in entities[:3]],
                "confidence": 0.8,
                "description": "Coordinated activity detected between entities",
                "details": {
                    "coordination_type": "temporal_synchronization",
                    "evidence_strength": "strong",
                    "coordination_duration": "7_days"
                }
            })
        
        return patterns
    
    async def _analyze_routine_details(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze routine behavior details."""
        return {
            "daily_patterns": True,
            "weekly_patterns": True,
            "activity_consistency": 0.85,
            "peak_hours": ["09:00-11:00", "14:00-16:00"],
            "routine_strength": "strong"
        }
    
    async def _analyze_anomaly_details(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze anomalous behavior details."""
        return {
            "deviation_areas": ["activity_timing", "communication_patterns"],
            "anomaly_magnitude": "high",
            "first_observed": "2024-01-15T10:30:00Z",
            "frequency": "sporadic",
            "potential_triggers": ["external_event", "behavioral_change"]
        }
    
    async def _analyze_escalation_details(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze escalation behavior details."""
        return {
            "escalation_rate": 0.3,
            "escalation_type": "frequency_increase",
            "timeframe": "14_days",
            "current_level": "moderate",
            "projected_trajectory": "continuing"
        }
    
    async def _analyze_pattern_significance(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze significance of detected patterns."""
        significant_patterns = []
        
        for pattern in patterns:
            significance_score = pattern.get("confidence", 0) * 1.2  # Weight confidence
            if significance_score > self.pattern_confidence_threshold:
                pattern["significance"] = significance_score
                pattern["priority"] = "high" if significance_score > 0.8 else "medium"
                significant_patterns.append(pattern)
        
        return sorted(significant_patterns, key=lambda x: x["significance"], reverse=True)
    
    async def _generate_pattern_insights(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights from detected patterns."""
        insights = []
        
        # Pattern frequency analysis
        pattern_types = [p["type"] for p in patterns]
        type_counts = {ptype: pattern_types.count(ptype) for ptype in set(pattern_types)}
        
        if type_counts:
            # Find the pattern type with the highest count
            most_common_type = max(type_counts.keys(), key=lambda k: type_counts[k])
            insights.append({
                "type": "frequency_analysis",
                "description": f"Most common pattern type: {most_common_type}",
                "details": type_counts
            })
        else:
            insights.append({
                "type": "frequency_analysis",
                "description": "No pattern types detected",
                "details": type_counts
            })
        
        # Confidence distribution
        high_confidence = len([p for p in patterns if p.get("confidence", 0) > 0.8])
        insights.append({
            "type": "confidence_distribution",
            "description": f"{high_confidence} patterns with high confidence (>0.8)",
            "details": {"high_confidence_count": high_confidence, "total_patterns": len(patterns)}
        })
        
        return insights
    
    async def _analyze_temporal_communication_patterns(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze temporal communication patterns."""
        patterns = []
        
        # Simulate temporal pattern detection
        patterns.append({
            "type": "temporal",
            "subtype": "daily_rhythm",
            "confidence": 0.75,
            "description": "Strong daily communication rhythm detected",
            "details": {
                "peak_hours": ["09:00-11:00", "14:00-16:00"],
                "quiet_hours": ["22:00-06:00"],
                "pattern_strength": 0.8
            }
        })
        
        patterns.append({
            "type": "temporal",
            "subtype": "weekly_pattern",
            "confidence": 0.65,
            "description": "Weekly communication pattern identified",
            "details": {
                "active_days": ["Monday", "Tuesday", "Wednesday", "Thursday"],
                "quiet_days": ["Saturday", "Sunday"],
                "pattern_consistency": 0.7
            }
        })
        
        return patterns
    
    async def _analyze_content_patterns(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze content patterns in communications."""
        patterns = []
        
        # Simulate content pattern detection
        patterns.append({
            "type": "content",
            "subtype": "topic_consistency",
            "confidence": 0.70,
            "description": "Consistent topic patterns detected",
            "details": {
                "dominant_topics": ["project_discussion", "logistics", "planning"],
                "topic_diversity": 0.4,
                "topic_stability": 0.8
            }
        })
        
        return patterns
    
    async def _analyze_communication_network_patterns(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze communication network patterns."""
        patterns = []
        
        # Simulate network pattern detection
        patterns.append({
            "type": "network",
            "subtype": "hub_spoke",
            "confidence": 0.80,
            "description": "Hub-and-spoke communication pattern detected",
            "details": {
                "central_entities": ["entity_1"],
                "spoke_entities": ["entity_2", "entity_3", "entity_4"],
                "centrality_score": 0.85
            }
        })
        
        return patterns
    
    async def _analyze_stylistic_patterns(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze stylistic patterns in communications."""
        patterns = []
        
        # Simulate stylistic pattern detection
        patterns.append({
            "type": "stylistic",
            "subtype": "formality_consistency",
            "confidence": 0.72,
            "description": "Consistent formality level in communications",
            "details": {
                "formality_level": "semi_formal",
                "consistency_score": 0.85,
                "style_variance": 0.15
            }
        })
        
        return patterns
    
    async def _analyze_semantic_patterns(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze semantic patterns in communications."""
        patterns = []
        
        # Simulate semantic pattern detection
        patterns.append({
            "type": "semantic",
            "subtype": "sentiment_consistency",
            "confidence": 0.68,
            "description": "Consistent sentiment patterns detected",
            "details": {
                "dominant_sentiment": "neutral_positive",
                "sentiment_stability": 0.75,
                "emotional_range": "limited"
            }
        })
        
        return patterns
    
    async def _analyze_sentiment_patterns(self, communications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sentiment patterns in communications."""
        patterns = []
        
        # Simulate sentiment pattern detection
        patterns.append({
            "type": "sentiment",
            "subtype": "temporal_sentiment",
            "confidence": 0.71,
            "description": "Temporal sentiment variation detected",
            "details": {
                "morning_sentiment": "positive",
                "afternoon_sentiment": "neutral",
                "evening_sentiment": "slightly_negative",
                "sentiment_volatility": 0.3
            }
        })
        
        return patterns
    
    async def _combine_communication_patterns(self, *pattern_lists) -> List[Dict[str, Any]]:
        """Combine and prioritize communication patterns."""
        all_patterns = []
        for pattern_list in pattern_lists:
            all_patterns.extend(pattern_list)
        
        # Sort by confidence and remove duplicates
        unique_patterns = []
        seen_patterns = set()
        
        for pattern in sorted(all_patterns, key=lambda x: x.get("confidence", 0), reverse=True):
            pattern_key = (pattern["type"], pattern.get("subtype", ""))
            if pattern_key not in seen_patterns:
                seen_patterns.add(pattern_key)
                unique_patterns.append(pattern)
        
        return unique_patterns[:10]  # Return top 10 patterns
    
    async def _detect_structural_patterns(self, network_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect structural network patterns."""
        patterns = []
        
        # Simulate structural pattern detection
        patterns.append({
            "type": "structural",
            "subtype": "small_world",
            "confidence": 0.78,
            "description": "Small-world network structure detected",
            "details": {
                "clustering_coefficient": 0.45,
                "average_path_length": 3.2,
                "small_world_index": 0.82
            }
        })
        
        return patterns
    
    async def _detect_temporal_network_patterns(self, network_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect temporal network patterns."""
        patterns = []
        
        # Simulate temporal pattern detection
        patterns.append({
            "type": "temporal",
            "subtype": "burst_dynamics",
            "confidence": 0.72,
            "description": "Bursty communication dynamics detected",
            "details": {
                "burst_frequency": "weekly",
                "burst_intensity": "high",
                "inter_burst_interval": "5-7_days"
            }
        })
        
        return patterns
    
    async def _detect_influence_patterns(self, network_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect influence patterns in network."""
        patterns = []
        
        # Simulate influence pattern detection
        patterns.append({
            "type": "influence",
            "subtype": "centralized_influence",
            "confidence": 0.85,
            "description": "Centralized influence structure identified",
            "details": {
                "key_influencers": ["entity_1", "entity_3"],
                "influence_concentration": 0.75,
                "cascade_depth": 3
            }
        })
        
        return patterns
    
    async def _detect_community_patterns(self, network_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect community patterns in network."""
        patterns = []
        
        # Simulate community pattern detection
        patterns.append({
            "type": "community",
            "subtype": "modular_structure",
            "confidence": 0.80,
            "description": "Modular community structure detected",
            "details": {
                "community_count": 3,
                "modularity_score": 0.65,
                "community_sizes": [5, 4, 3]
            }
        })
        
        return patterns
    
    async def _detect_network_anomalies(self, network_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect anomalies in network structure."""
        anomalies = []
        
        # Simulate anomaly detection
        anomalies.append({
            "type": "structural_anomaly",
            "description": "Unusually high degree centrality detected",
            "entity": "entity_2",
            "anomaly_score": 2.3,
            "severity": "medium"
        })
        
        return anomalies
    
    async def _generate_network_insights(self, patterns: List[Dict[str, Any]], anomalies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate insights from network patterns and anomalies."""
        insights = []
        
        # Pattern summary
        pattern_types = [p["type"] for p in patterns]
        insights.append({
            "type": "pattern_summary",
            "description": f"Network exhibits {len(set(pattern_types))} different pattern types",
            "details": {"pattern_distribution": {ptype: pattern_types.count(ptype) for ptype in set(pattern_types)}}
        })
        
        # Anomaly assessment
        if anomalies:
            insights.append({
                "type": "anomaly_assessment",
                "description": f"{len(anomalies)} structural anomalies detected",
                "details": {"anomaly_types": [a["type"] for a in anomalies]}
            })
        
        return insights
    
    async def _calculate_pattern_network_metrics(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate network metrics for pattern analysis."""
        return {
            "node_count": 12,  # Simulated
            "edge_count": 18,  # Simulated
            "density": 0.27,   # Simulated
            "average_clustering": 0.42,  # Simulated
            "assortativity": -0.15  # Simulated
        }
    
    async def _detect_specific_anomalies(self, data: List[Dict[str, Any]], anomaly_type: str, sensitivity: float) -> List[Dict[str, Any]]:
        """Detect specific types of anomalies."""
        anomalies = []
        
        if anomaly_type == "statistical":
            # Statistical anomalies
            anomalies.append({
                "type": "statistical",
                "description": "Statistical outlier detected",
                "data_point": "item_5",
                "anomaly_score": 2.8,
                "p_value": 0.003,
                "severity": "high"
            })
        
        elif anomaly_type == "temporal":
            # Temporal anomalies
            anomalies.append({
                "type": "temporal",
                "description": "Unusual temporal pattern detected",
                "timeframe": "2024-01-20T15:30:00Z",
                "anomaly_score": 2.1,
                "severity": "medium"
            })
        
        elif anomaly_type == "structural":
            # Structural anomalies
            anomalies.append({
                "type": "structural",
                "description": "Structural anomaly in data organization",
                "location": "data_segment_3",
                "anomaly_score": 1.9,
                "severity": "low"
            })
        
        elif anomaly_type == "behavioral":
            # Behavioral anomalies
            anomalies.append({
                "type": "behavioral",
                "description": "Behavioral anomaly detected",
                "entity": "entity_7",
                "anomaly_score": 2.5,
                "severity": "high"
            })
        
        return anomalies
    
    async def _classify_anomaly_severity(self, anomalies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Classify anomalies by severity."""
        classified = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": []
        }
        
        for anomaly in anomalies:
            severity = anomaly.get("severity", "medium")
            if severity in classified:
                classified[severity].append(anomaly)
        
        return classified
    
    async def _generate_anomaly_explanations(self, classified_anomalies: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Generate explanations for detected anomalies."""
        explanations = []
        
        for severity, anomalies in classified_anomalies.items():
            if anomalies:
                explanations.append({
                    "severity": severity,
                    "count": len(anomalies),
                    "explanation": f"{len(anomalies)} {severity} severity anomalies detected requiring attention",
                    "recommended_action": self._get_recommended_action(severity),
                    "anomaly_ids": [a.get("data_point", a.get("entity", f"anomaly_{i}")) for i, a in enumerate(anomalies)]
                })
        
        return explanations
    
    def _get_recommended_action(self, severity: str) -> str:
        """Get recommended action for anomaly severity."""
        actions = {
            "critical": "Immediate investigation required",
            "high": "Priority investigation within 24 hours",
            "medium": "Investigation within 72 hours",
            "low": "Monitor and investigate as resources allow"
        }
        return actions.get(severity, "Further analysis needed")
    
    async def _prioritize_anomaly_investigation(self, classified_anomalies: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Prioritize anomaly investigation based on severity and impact."""
        priorities = []
        
        severity_order = ["critical", "high", "medium", "low"]
        
        for severity in severity_order:
            anomalies = classified_anomalies.get(severity, [])
            for anomaly in anomalies:
                priority_score = self._calculate_priority_score(anomaly, severity)
                priorities.append({
                    "anomaly": anomaly,
                    "priority_score": priority_score,
                    "recommended_timeline": self._get_timeline(severity),
                    "investigation_complexity": self._estimate_complexity(anomaly)
                })
        
        return sorted(priorities, key=lambda x: x["priority_score"], reverse=True)
    
    def _calculate_priority_score(self, anomaly: Dict[str, Any], severity: str) -> float:
        """Calculate priority score for anomaly investigation."""
        severity_scores = {"critical": 4.0, "high": 3.0, "medium": 2.0, "low": 1.0}
        base_score = severity_scores.get(severity, 2.0)
        
        # Adjust based on anomaly score
        anomaly_score = anomaly.get("anomaly_score", 2.0)
        return base_score + (anomaly_score - 2.0) * 0.5
    
    def _get_timeline(self, severity: str) -> str:
        """Get recommended investigation timeline."""
        timelines = {
            "critical": "immediate",
            "high": "24_hours",
            "medium": "72_hours",
            "low": "1_week"
        }
        return timelines.get(severity, "72_hours")
    
    def _estimate_complexity(self, anomaly: Dict[str, Any]) -> str:
        """Estimate investigation complexity."""
        # Simulate complexity estimation
        return "medium"  # Could be "low", "medium", or "high"

    def _get_system_prompt(self) -> str:
        """
        Get the system prompt for this agent.
        """
        return f"""
        You are a {self.config.role}, specialized in identifying patterns in OSINT data.
        Your role is to analyze data and detect behavioral patterns, communication patterns,
        network patterns, and anomalies in the provided information.
        Use statistical analysis, trend identification, and correlation detection to find meaningful patterns.
        Always provide confidence scores and explain the significance of detected patterns.
        """

    def _process_output(self, raw_output: str, intermediate_steps: Optional[List] = None) -> Dict[str, Any]:
        """
        Process the raw output from the agent into structured data.
        """
        try:
            # Clean the raw output - remove markdown formatting, extra whitespace, etc.
            cleaned_output = self._clean_raw_output(raw_output)
            
            # Try to parse JSON output
            if cleaned_output.strip().startswith('{'):
                structured_data = json.loads(cleaned_output)
            else:
                # Extract JSON from text if embedded
                json_match = re.search(r'\{.*\}', cleaned_output, re.DOTALL)
                if json_match:
                    structured_data = json.loads(json_match.group())
                else:
                    # Fallback: parse text manually
                    structured_data = self._parse_text_output(cleaned_output)
            
            # Validate and enhance the structured data
            return self._validate_and_enhance_patterns(structured_data)
            
        except Exception as e:
            self.logger.error(f"Error processing output: {e}")
            try:
                cleaned_output = self._clean_raw_output(raw_output)
            except:
                cleaned_output = raw_output  # fallback if cleaning fails
            return {
                "error": "Failed to process output",
                "raw_output": raw_output,
                "cleaned_output": cleaned_output,
                "fallback_patterns": self._generate_fallback_patterns()
            }

    def _clean_raw_output(self, raw_output: str) -> str:
        """Clean raw output to extract valid JSON."""
        cleaned = raw_output.strip()
        
        # Remove markdown code block formatting
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]  # Remove ```json
        elif cleaned.startswith('```'):
            cleaned = cleaned[3:]   # Remove ```
        
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]  # Remove trailing ```
        
        # Remove any leading/trailing text that might be around the JSON
        # Find the first { and last }
        first_brace = cleaned.find('{')
        last_brace = cleaned.rfind('}')
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            cleaned = cleaned[first_brace:last_brace+1]
        
        return cleaned

    def _validate_and_enhance_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance the pattern recognition results."""
        enhanced = patterns.copy()
        
        # Add metadata
        enhanced["metadata"] = {
            "agent_id": self.config.agent_id,
            "processing_timestamp": datetime.utcnow().isoformat(),
            "confidence_score": self._calculate_pattern_confidence(enhanced),
            "pattern_quality": self._assess_pattern_quality(enhanced)
        }
        
        return enhanced

    def _parse_text_output(self, text: str) -> Dict[str, Any]:
        """Parse non-JSON text output into structured data."""
        # This is a fallback parser for when JSON parsing fails
        patterns = {
            "detected_patterns": [],
            "analysis_success": True,
            "source": "pattern_recognition",
            "timestamp": datetime.utcnow().timestamp()
        }
        
        # Simple text parsing logic
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Add basic parsing logic here
            if "pattern" in line.lower() or "anomaly" in line.lower():
                patterns["detected_patterns"].append({"description": line, "confidence": 0.5})
        
        return patterns

    def _generate_fallback_patterns(self) -> Dict[str, Any]:
        """Generate basic patterns when parsing fails."""
        return {
            "detected_patterns": [],
            "analysis_success": True,
            "source": "pattern_recognition",
            "timestamp": datetime.utcnow().timestamp(),
            "error": "Generated fallback patterns due to processing error"
        }

    def _calculate_pattern_confidence(self, patterns: Dict[str, Any]) -> float:
        """Calculate confidence score for the pattern recognition results."""
        score = 0.0
        total_checks = 0
        
        # Check for detected patterns
        if patterns.get("detected_patterns"):
            score += min(len(patterns["detected_patterns"]) / 5, 1.0)  # Up to 1.0 for 5+ patterns
        total_checks += 1
        
        # Check for analysis success
        if patterns.get("analysis_success"):
            score += 0.5  # Half point for successful analysis
        total_checks += 1
        
        return score / total_checks if total_checks > 0 else 0.0

    def _assess_pattern_quality(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Assess pattern quality metrics."""
        quality_metrics = {
            "completeness": 0.0,
            "relevance": 0.0,
            "accuracy": 0.0,
            "significance": 0.0
        }
        
        # Basic assessment based on pattern content
        if patterns.get("detected_patterns"):
            quality_metrics["completeness"] = min(len(patterns["detected_patterns"]) * 0.2, 1.0)
        
        return quality_metrics

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before execution.
        """
        required_fields = ["task_type"]
        return all(field in input_data for field in required_fields)