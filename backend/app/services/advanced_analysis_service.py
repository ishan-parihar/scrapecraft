"""
Advanced Analysis Service
Provides pattern recognition, behavioral analysis, threat assessment, and link analysis capabilities
"""

import asyncio
import aiohttp
import json
import re
import networkx as nx
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple, Set
from dataclasses import dataclass, asdict
from datetime import datetime, date, timedelta
from collections import Counter, defaultdict
from urllib.parse import urljoin, urlparse
import logging

from bs4 import BeautifulSoup
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairity import cosine_similarity

from app.services.error_handling import handle_errors, RetryConfig
from app.services.llm_integration import LLMIntegrationService

logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Detected pattern in data"""
    pattern_type: str
    description: str
    confidence: float
    frequency: int
    time_period: str
    entities: List[str]
    context: Dict[str, Any]
    indicators: List[str]
    severity: str = "medium"  # low, medium, high, critical
    source: str = ""
    timestamp: Optional[datetime] = None


@dataclass
class BehavioralProfile:
    """Behavioral analysis profile"""
    entity_name: str
    entity_type: str  # person, organization, ip, domain
    behavioral_patterns: List[str]
    risk_score: float
    activity_timeline: List[Dict[str, Any]]
    communication_patterns: Dict[str, Any]
    temporal_patterns: Dict[str, Any]
    network_behavior: Dict[str, Any]
    anomaly_indicators: List[str]
    confidence: float
    source: str = ""
    last_updated: Optional[datetime] = None


@dataclass
class ThreatAssessment:
    """Threat assessment results"""
    target: str
    threat_level: str  # low, medium, high, critical
    threat_vectors: List[str]
    vulnerability_indicators: List[str]
    attack_patterns: List[str]
    risk_factors: List[Dict[str, Any]]
    mitigation_recommendations: List[str]
    confidence: float
    assessment_date: datetime
    time_horizon: str  # immediate, short_term, long_term
    sources: List[str]


@dataclass
class LinkAnalysisResult:
    """Link analysis results"""
    central_entities: List[str]
    relationship_strength: Dict[Tuple[str, str], float]
    clusters: List[Set[str]]
    key_influencers: List[str]
    hidden_connections: List[Tuple[str, str, str]]
    network_metrics: Dict[str, float]
    visualization_data: Dict[str, Any]
    confidence: float
    analysis_timestamp: datetime


@dataclass
class AnomalyDetection:
    """Anomaly detection results"""
    anomaly_type: str
    description: str
    severity: str
    confidence: float
    affected_entities: List[str]
    baseline_deviation: float
    time_detected: datetime
    context: Dict[str, Any]
    recommended_actions: List[str]


class AdvancedAnalysisService:
    """Service for advanced OSINT analysis"""
    
    def __init__(self):
        self.llm_service = LLMIntegrationService()
        self.session = None
        self.retry_config = RetryConfig(max_retries=3, base_delay=2.0)
        
        # Analysis configuration
        self.min_pattern_frequency = 3
        self.similarity_threshold = 0.7
        self.anomaly_threshold = 2.0  # Standard deviations
        self.network_centrality_threshold = 0.5
        
        # Threat intelligence patterns
        self.threat_patterns = {
            'data_breach': ['breach', 'leak', 'exposed', 'compromised', 'stolen'],
            'malware': ['malware', 'virus', 'trojan', 'ransomware', 'backdoor'],
            'phishing': ['phishing', 'credential', 'login', 'password', 'harvest'],
            'social_engineering': ['social engineering', 'pretext', 'impersonation', 'deception'],
            'ddos': ['ddos', 'flood', 'overload', 'amplification', 'botnet'],
            'insider_threat': ['insider', 'employee', 'privileged', 'access abuse'],
            'apt': ['apt', 'advanced persistent', 'sophisticated', 'state-sponsored']
        }
        
        # Behavioral indicators
        self.behavioral_indicators = {
            'high_frequency': {'threshold': 100, 'period': '24h'},
            'unusual_timing': {'hours': [22, 23, 0, 1, 2, 3, 4, 5]},
            ' geographic_anomaly': {'threshold': 3},  # Number of distinct locations
            'communication_burst': {'threshold': 50, 'window': '1h'},
            'access_pattern': {'deviation_threshold': 2.0}
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={'User-Agent': 'Mozilla/5.0 (compatible; OSINT-Analyzer/1.0)'}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @handle_errors("advanced_analysis", "pattern_recognition", RetryConfig(max_retries=3, base_delay=2.0))
    async def recognize_patterns(self, data_sources: List[Dict[str, Any]], pattern_types: List[str] = None) -> List[Pattern]:
        """Recognize patterns across multiple data sources"""
        
        if pattern_types is None:
            pattern_types = ['temporal', 'communication', 'behavioral', 'network', 'content']
            
        patterns = []
        combined_data = self._combine_data_sources(data_sources)
        
        for pattern_type in pattern_types:
            try:
                if pattern_type == 'temporal':
                    temporal_patterns = await self._detect_temporal_patterns(combined_data)
                    patterns.extend(temporal_patterns)
                elif pattern_type == 'communication':
                    comm_patterns = await self._detect_communication_patterns(combined_data)
                    patterns.extend(comm_patterns)
                elif pattern_type == 'behavioral':
                    behavioral_patterns = await self._detect_behavioral_patterns(combined_data)
                    patterns.extend(behavioral_patterns)
                elif pattern_type == 'network':
                    network_patterns = await self._detect_network_patterns(combined_data)
                    patterns.extend(network_patterns)
                elif pattern_type == 'content':
                    content_patterns = await self._detect_content_patterns(combined_data)
                    patterns.extend(content_patterns)
                    
            except Exception as e:
                logger.debug(f"Pattern detection failed for {pattern_type}: {str(e)}")
                continue
                
        # Enhance patterns with LLM analysis
        enhanced_patterns = await self._enhance_patterns_with_llm(patterns)
        
        # Filter and rank patterns
        filtered_patterns = self._filter_patterns(enhanced_patterns)
        
        return sorted(filtered_patterns, key=lambda x: (x.severity_score, x.confidence), reverse=True)

    @handle_errors("advanced_analysis", "behavioral_analysis", RetryConfig(max_retries=3, base_delay=2.0))
    async def analyze_behavior(self, entity_data: Dict[str, Any], time_window: int = 30) -> BehavioralProfile:
        """Analyze behavioral patterns for an entity"""
        
        entity_name = entity_data.get('name', 'unknown')
        entity_type = entity_data.get('type', 'unknown')
        
        # Extract behavioral data
        activities = entity_data.get('activities', [])
        communications = entity_data.get('communications', [])
        network_activity = entity_data.get('network_activity', [])
        
        # Analyze behavioral patterns
        behavioral_patterns = await self._extract_behavioral_patterns(activities)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_behavior(activities, time_window)
        
        # Analyze communication patterns
        comm_patterns = self._analyze_communication_behavior(communications)
        
        # Analyze network behavior
        net_behavior = self._analyze_network_behavior(network_activity)
        
        # Detect anomalies
        anomaly_indicators = await self._detect_behavioral_anomalies(
            activities, communications, network_activity
        )
        
        # Calculate risk score
        risk_score = self._calculate_behavioral_risk_score(
            behavioral_patterns, anomaly_indicators, temporal_patterns
        )
        
        # Create activity timeline
        activity_timeline = self._create_activity_timeline(activities, time_window)
        
        profile = BehavioralProfile(
            entity_name=entity_name,
            entity_type=entity_type,
            behavioral_patterns=behavioral_patterns,
            risk_score=risk_score,
            activity_timeline=activity_timeline,
            communication_patterns=comm_patterns,
            temporal_patterns=temporal_patterns,
            network_behavior=net_behavior,
            anomaly_indicators=anomaly_indicators,
            confidence=self._calculate_behavioral_confidence(entity_data),
            source="Advanced Analysis Service",
            last_updated=datetime.now()
        )
        
        return profile

    @handle_errors("advanced_analysis", "threat_assessment", RetryConfig(max_retries=3, base_delay=2.0))
    async def assess_threats(self, target_data: Dict[str, Any], context_data: List[Dict[str, Any]] = None) -> ThreatAssessment:
        """Comprehensive threat assessment"""
        
        target = target_data.get('target', 'unknown')
        
        # Analyze threat vectors
        threat_vectors = await self._identify_threat_vectors(target_data)
        
        # Identify vulnerability indicators
        vulnerabilities = await self._identify_vulnerabilities(target_data)
        
        # Analyze attack patterns
        attack_patterns = await self._analyze_attack_patterns(target_data, context_data)
        
        # Assess risk factors
        risk_factors = await self._assess_risk_factors(target_data, context_data)
        
        # Calculate overall threat level
        threat_level = self._calculate_threat_level(threat_vectors, vulnerabilities, attack_patterns)
        
        # Generate mitigation recommendations
        recommendations = await self._generate_mitigation_recommendations(
            threat_level, threat_vectors, vulnerabilities
        )
        
        # Determine time horizon
        time_horizon = self._determine_threat_time_horizon(threat_vectors, attack_patterns)
        
        assessment = ThreatAssessment(
            target=target,
            threat_level=threat_level,
            threat_vectors=threat_vectors,
            vulnerability_indicators=vulnerabilities,
            attack_patterns=attack_patterns,
            risk_factors=risk_factors,
            mitigation_recommendations=recommendations,
            confidence=self._calculate_threat_confidence(target_data, context_data),
            assessment_date=datetime.now(),
            time_horizon=time_horizon,
            sources=["Advanced Analysis Service", "Threat Intelligence"]
        )
        
        return assessment

    @handle_errors("advanced_analysis", "link_analysis", RetryConfig(max_retries=3, base_delay=2.0))
    async def analyze_links(self, entities: List[Dict[str, Any]], relationships: List[Dict[str, Any]] = None) -> LinkAnalysisResult:
        """Perform link analysis between entities"""
        
        if relationships is None:
            relationships = []
            
        # Build network graph
        G = self._build_network_graph(entities, relationships)
        
        # Calculate centrality measures
        centrality_metrics = self._calculate_centrality_metrics(G)
        
        # Identify central entities
        central_entities = self._identify_central_entities(centrality_metrics)
        
        # Calculate relationship strength
        relationship_strength = self._calculate_relationship_strength(G)
        
        # Detect clusters
        clusters = self._detect_network_clusters(G)
        
        # Identify key influencers
        key_influencers = self._identify_key_influencers(G, centrality_metrics)
        
        # Find hidden connections
        hidden_connections = self._find_hidden_connections(G)
        
        # Calculate network metrics
        network_metrics = self._calculate_network_metrics(G)
        
        # Generate visualization data
        viz_data = self._generate_visualization_data(G, centrality_metrics, clusters)
        
        result = LinkAnalysisResult(
            central_entities=central_entities,
            relationship_strength=relationship_strength,
            clusters=clusters,
            key_influencers=key_influencers,
            hidden_connections=hidden_connections,
            network_metrics=network_metrics,
            visualization_data=viz_data,
            confidence=self._calculate_link_analysis_confidence(G),
            analysis_timestamp=datetime.now()
        )
        
        return result

    @handle_errors("advanced_analysis", "anomaly_detection", RetryConfig(max_retries=3, base_delay=2.0))
    async def detect_anomalies(self, baseline_data: Dict[str, Any], current_data: Dict[str, Any]) -> List[AnomalyDetection]:
        """Detect anomalies in current data compared to baseline"""
        
        anomalies = []
        
        # Analyze different data dimensions
        anomaly_types = ['frequency', 'temporal', 'behavioral', 'network', 'content']
        
        for anomaly_type in anomaly_types:
            try:
                if anomaly_type == 'frequency':
                    freq_anomalies = self._detect_frequency_anomalies(baseline_data, current_data)
                    anomalies.extend(freq_anomalies)
                elif anomaly_type == 'temporal':
                    temporal_anomalies = self._detect_temporal_anomalies(baseline_data, current_data)
                    anomalies.extend(temporal_anomalies)
                elif anomaly_type == 'behavioral':
                    behavioral_anomalies = self._detect_behavioral_anomalies(baseline_data, current_data)
                    anomalies.extend(behavioral_anomalies)
                elif anomaly_type == 'network':
                    network_anomalies = self._detect_network_anomalies(baseline_data, current_data)
                    anomalies.extend(network_anomalies)
                elif anomaly_type == 'content':
                    content_anomalies = self._detect_content_anomalies(baseline_data, current_data)
                    anomalies.extend(content_anomalies)
                    
            except Exception as e:
                logger.debug(f"Anomaly detection failed for {anomaly_type}: {str(e)}")
                continue
        
        # Enhance with LLM analysis
        enhanced_anomalies = await self._enhance_anomalies_with_llm(anomalies)
        
        # Rank by severity and confidence
        ranked_anomalies = sorted(
            enhanced_anomalies,
            key=lambda x: (x.severity_score, x.confidence),
            reverse=True
        )
        
        return ranked_anomalies

    async def _detect_temporal_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Detect temporal patterns in data"""
        
        patterns = []
        events = data.get('events', [])
        
        if not events:
            return patterns
            
        # Extract timestamps and create time series
        timestamps = [event.get('timestamp') for event in events if event.get('timestamp')]
        
        if len(timestamps) < self.min_pattern_frequency:
            return patterns
            
        # Analyze time intervals
        intervals = []
        for i in range(1, len(timestamps)):
            if timestamps[i] and timestamps[i-1]:
                interval = (timestamps[i] - timestamps[i-1]).total_seconds()
                intervals.append(interval)
        
        if intervals:
            # Detect regular intervals
            interval_counter = Counter(intervals)
            common_intervals = interval_counter.most_common(5)
            
            for interval, count in common_intervals:
                if count >= self.min_pattern_frequency:
                    pattern = Pattern(
                        pattern_type="temporal",
                        description=f"Regular activity pattern every {interval/3600:.1f} hours",
                        confidence=min(count / len(intervals), 1.0),
                        frequency=count,
                        time_period=f"Last {max(timestamps) - min(timestamps)}",
                        entities=[event.get('entity') for event in events[:count]],
                        context={'interval_seconds': interval, 'total_events': len(events)},
                        indicators=['regular_timing', 'predictable_schedule'],
                        severity="medium"
                    )
                    patterns.append(pattern)
        
        return patterns

    async def _detect_communication_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Detect communication patterns"""
        
        patterns = []
        communications = data.get('communications', [])
        
        if not communications:
            return patterns
            
        # Analyze communication frequency
        comm_counter = Counter()
        entity_pairs = []
        
        for comm in communications:
            sender = comm.get('sender')
            receiver = comm.get('receiver')
            if sender and receiver:
                pair = tuple(sorted([sender, receiver]))
                comm_counter[pair] += 1
                entity_pairs.append(pair)
        
        # Detect high-frequency communications
        for pair, count in comm_counter.most_common(10):
            if count >= self.min_pattern_frequency:
                pattern = Pattern(
                    pattern_type="communication",
                    description=f"High-frequency communication between {pair[0]} and {pair[1]}",
                    confidence=min(count / len(communications), 1.0),
                    frequency=count,
                    time_period="Analysis period",
                    entities=list(pair),
                    context={'communication_count': count, 'total_communications': len(communications)},
                    indicators=['high_frequency', 'established_relationship'],
                    severity="low"
                )
                patterns.append(pattern)
        
        return patterns

    async def _detect_behavioral_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Detect behavioral patterns"""
        
        patterns = []
        activities = data.get('activities', [])
        
        if not activities:
            return patterns
            
        # Analyze activity types
        activity_types = [activity.get('type') for activity in activities if activity.get('type')]
        type_counter = Counter(activity_types)
        
        # Detect dominant behavior patterns
        for activity_type, count in type_counter.most_common(10):
            if count >= self.min_pattern_frequency:
                pattern = Pattern(
                    pattern_type="behavioral",
                    description=f"Dominant behavioral pattern: {activity_type}",
                    confidence=min(count / len(activities), 1.0),
                    frequency=count,
                    time_period="Analysis period",
                    entities=[activity.get('entity') for activity in activities if activity.get('type') == activity_type],
                    context={'activity_type': activity_type, 'total_activities': len(activities)},
                    indicators=['repeated_behavior', 'activity_preference'],
                    severity="low"
                )
                patterns.append(pattern)
        
        return patterns

    async def _detect_network_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Detect network patterns"""
        
        patterns = []
        network_events = data.get('network_events', [])
        
        if not network_events:
            return patterns
            
        # Analyze IP addresses and ports
        ip_counter = Counter()
        port_counter = Counter()
        
        for event in network_events:
            ip = event.get('ip_address')
            port = event.get('port')
            if ip:
                ip_counter[ip] += 1
            if port:
                port_counter[port] += 1
        
        # Detect frequent IP connections
        for ip, count in ip_counter.most_common(10):
            if count >= self.min_pattern_frequency:
                pattern = Pattern(
                    pattern_type="network",
                    description=f"Frequent connection to IP {ip}",
                    confidence=min(count / len(network_events), 1.0),
                    frequency=count,
                    time_period="Analysis period",
                    entities=[ip],
                    context={'connection_count': count, 'total_events': len(network_events)},
                    indicators=['frequent_connection', 'established_endpoint'],
                    severity="low"
                )
                patterns.append(pattern)
        
        return patterns

    async def _detect_content_patterns(self, data: Dict[str, Any]) -> List[Pattern]:
        """Detect content patterns using text analysis"""
        
        patterns = []
        content_items = data.get('content', [])
        
        if not content_items:
            return patterns
            
        # Extract text content
        texts = [item.get('text', '') for item in content_items if item.get('text')]
        
        if len(texts) < self.min_pattern_frequency:
            return patterns
            
        # Use TF-IDF for pattern detection
        try:
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
            tfidf_matrix = vectorizer.fit_transform(texts)
            
            # Find important terms
            feature_names = vectorizer.get_feature_names_out()
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Get top terms
            top_indices = np.argsort(mean_scores)[-10:][::-1]
            
            for idx in top_indices:
                if mean_scores[idx] > 0.1:  # Threshold for significance
                    term = feature_names[idx]
                    pattern = Pattern(
                        pattern_type="content",
                        description=f"Recurring content theme: {term}",
                        confidence=mean_scores[idx],
                        frequency=sum(1 for text in texts if term in text.lower()),
                        time_period="Analysis period",
                        entities=[item.get('source') for item in content_items if term in item.get('text', '').lower()],
                        context={'term': term, 'tfidf_score': mean_scores[idx]},
                        indicators=['content_theme', 'repeated_topic'],
                        severity="low"
                    )
                    patterns.append(pattern)
                    
        except Exception as e:
            logger.debug(f"Content pattern detection failed: {str(e)}")
        
        return patterns

    async def _enhance_patterns_with_llm(self, patterns: List[Pattern]) -> List[Pattern]:
        """Enhance patterns with LLM analysis"""
        
        enhanced_patterns = []
        
        for pattern in patterns:
            try:
                # Prepare context for LLM
                context = {
                    'pattern_type': pattern.pattern_type,
                    'description': pattern.description,
                    'frequency': pattern.frequency,
                    'entities': pattern.entities,
                    'indicators': pattern.indicators
                }
                
                # Generate LLM enhancement
                prompt = f"""
                Analyze this OSINT pattern and provide enhanced assessment:
                
                Pattern Type: {pattern.pattern_type}
                Description: {pattern.description}
                Frequency: {pattern.frequency}
                Entities: {', '.join(pattern.entities)}
                Indicators: {', '.join(pattern.indicators)}
                
                Provide:
                1. Enhanced severity assessment (low/medium/high/critical)
                2. Additional context or implications
                3. Potential security relevance
                """
                
                llm_response = await self.llm_service.generate_response(prompt, max_tokens=300)
                
                if llm_response:
                    # Parse LLM response to enhance pattern
                    enhanced_pattern = Pattern(
                        pattern_type=pattern.pattern_type,
                        description=pattern.description,
                        confidence=pattern.confidence,
                        frequency=pattern.frequency,
                        time_period=pattern.time_period,
                        entities=pattern.entities,
                        context={**pattern.context, 'llm_analysis': llm_response},
                        indicators=pattern.indicators,
                        severity=self._extract_severity_from_llm(llm_response) or pattern.severity,
                        source=f"{pattern.source} + LLM Enhanced",
                        timestamp=pattern.timestamp
                    )
                    enhanced_patterns.append(enhanced_pattern)
                else:
                    enhanced_patterns.append(pattern)
                    
            except Exception as e:
                logger.debug(f"LLM enhancement failed for pattern: {str(e)}")
                enhanced_patterns.append(pattern)
        
        return enhanced_patterns

    def _filter_patterns(self, patterns: List[Pattern]) -> List[Pattern]:
        """Filter and rank patterns"""
        
        # Filter by minimum frequency and confidence
        filtered = [
            pattern for pattern in patterns
            if pattern.frequency >= self.min_pattern_frequency and pattern.confidence >= 0.5
        ]
        
        # Remove duplicates
        unique_patterns = []
        seen_descriptions = set()
        
        for pattern in filtered:
            desc_key = f"{pattern.pattern_type}:{pattern.description[:100]}"
            if desc_key not in seen_descriptions:
                seen_descriptions.add(desc_key)
                unique_patterns.append(pattern)
        
        return unique_patterns

    def _extract_severity_from_llm(self, llm_response: str) -> Optional[str]:
        """Extract severity level from LLM response"""
        
        response_lower = llm_response.lower()
        
        if any(keyword in response_lower for keyword in ['critical', 'severe', 'urgent']):
            return 'critical'
        elif any(keyword in response_lower for keyword in ['high', 'significant', 'major']):
            return 'high'
        elif any(keyword in response_lower for keyword in ['medium', 'moderate', 'notable']):
            return 'medium'
        else:
            return 'low'

    def _calculate_behavioral_confidence(self, entity_data: Dict[str, Any]) -> float:
        """Calculate confidence score for behavioral analysis"""
        
        data_points = 0
        total_possible = 0
        
        # Check data availability
        if entity_data.get('activities'):
            data_points += len(entity_data['activities'])
            total_possible += 50
            
        if entity_data.get('communications'):
            data_points += len(entity_data['communications'])
            total_possible += 30
            
        if entity_data.get('network_activity'):
            data_points += len(entity_data['network_activity'])
            total_possible += 20
        
        return min(data_points / max(total_possible, 1), 1.0)

    def _calculate_threat_confidence(self, target_data: Dict[str, Any], context_data: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for threat assessment"""
        
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data availability
        if target_data.get('vulnerabilities'):
            confidence += 0.1
            
        if target_data.get('threat_indicators'):
            confidence += 0.1
            
        if context_data and len(context_data) > 0:
            confidence += 0.2
            
        if target_data.get('historical_incidents'):
            confidence += 0.1
            
        return min(confidence, 1.0)

    def _calculate_link_analysis_confidence(self, G: nx.Graph) -> float:
        """Calculate confidence score for link analysis"""
        
        if G.number_of_nodes() == 0:
            return 0.0
            
        # Confidence based on network density and data completeness
        density = nx.density(G)
        
        # More complete networks have higher confidence
        confidence = min(density * 2, 1.0)
        
        # Adjust for network size
        if G.number_of_nodes() > 50:
            confidence = min(confidence + 0.1, 1.0)
        elif G.number_of_nodes() < 10:
            confidence = max(confidence - 0.2, 0.1)
            
        return confidence

    async def generate_comprehensive_analysis(self, target_data: Dict[str, Any], related_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate comprehensive analysis combining all advanced analysis capabilities"""
        
        if related_data is None:
            related_data = []
            
        analysis_result = {
            'target': target_data.get('target', 'unknown'),
            'analysis_timestamp': datetime.now().isoformat(),
            'patterns': [],
            'behavioral_profiles': [],
            'threat_assessments': [],
            'link_analysis': None,
            'anomaly_detections': [],
            'overall_risk_score': 0.0,
            'key_findings': [],
            'recommendations': []
        }
        
        try:
            async with self:
                # Pattern Recognition
                all_data = [target_data] + related_data
                patterns = await self.recognize_patterns(all_data)
                analysis_result['patterns'] = [asdict(pattern) for pattern in patterns]
                
                # Behavioral Analysis
                if target_data.get('entities'):
                    for entity in target_data['entities'][:5]:  # Limit to prevent overwhelming
                        behavioral_profile = await self.analyze_behavior(entity)
                        analysis_result['behavioral_profiles'].append(asdict(behavioral_profile))
                
                # Threat Assessment
                threat_assessment = await self.assess_threats(target_data, related_data)
                analysis_result['threat_assessments'].append(asdict(threat_assessment))
                
                # Link Analysis
                if target_data.get('entities') and len(target_data['entities']) > 1:
                    entities = target_data['entities']
                    relationships = target_data.get('relationships', [])
                    link_analysis = await self.analyze_links(entities, relationships)
                    analysis_result['link_analysis'] = asdict(link_analysis)
                
                # Anomaly Detection
                if target_data.get('baseline_data'):
                    anomalies = await self.detect_anomalies(
                        target_data['baseline_data'], 
                        target_data.get('current_data', {})
                    )
                    analysis_result['anomaly_detections'] = [asdict(anomaly) for anomaly in anomalies]
                
                # Calculate overall risk score
                analysis_result['overall_risk_score'] = self._calculate_overall_risk_score(analysis_result)
                
                # Generate key findings
                analysis_result['key_findings'] = await self._generate_key_findings(analysis_result)
                
                # Generate recommendations
                analysis_result['recommendations'] = await self._generate_overall_recommendations(analysis_result)
                
        except Exception as e:
            logger.error(f"Comprehensive analysis failed: {str(e)}")
            analysis_result['error'] = str(e)
        
        return analysis_result


# Convenience function for comprehensive analysis
async def perform_advanced_analysis(target_data: Dict[str, Any], related_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Perform comprehensive advanced analysis"""
    
    async with AdvancedAnalysisService() as service:
        return await service.generate_comprehensive_analysis(target_data, related_data)