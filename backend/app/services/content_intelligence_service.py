"""
Content Intelligence Service
Provides entity recognition, relationship mapping, and temporal analysis for OSINT content.
"""

import re
import json
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import hashlib

from app.services.llm_integration import LLMIntegrationService
from app.config import settings

logger = logging.getLogger(__name__)

class Entity:
    """Represents an extracted entity with metadata."""
    
    def __init__(self, text: str, entity_type: str, confidence: float = 0.0):
        self.text = text
        self.entity_type = entity_type  # PERSON, ORGANIZATION, LOCATION, etc.
        self.confidence = confidence
        self.aliases = set()
        self.attributes = {}
        self.relationships = []
        self.first_seen = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.mention_count = 1
        self.source_urls = set()
        
    def add_mention(self, source_url: str = None):
        """Record a new mention of this entity."""
        self.mention_count += 1
        self.last_seen = datetime.utcnow()
        if source_url:
            self.source_urls.add(source_url)
    
    def add_alias(self, alias: str):
        """Add an alias for this entity."""
        self.aliases.add(alias)
    
    def add_relationship(self, relationship: str, target_entity: str):
        """Add a relationship to another entity."""
        self.relationships.append({
            'type': relationship,
            'target': target_entity,
            'confidence': 0.5,
            'first_seen': datetime.utcnow().isoformat()
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        return {
            'text': self.text,
            'entity_type': self.entity_type,
            'confidence': self.confidence,
            'aliases': list(self.aliases),
            'attributes': self.attributes,
            'relationships': self.relationships,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'mention_count': self.mention_count,
            'source_urls': list(self.source_urls)
        }


class Relationship:
    """Represents a relationship between two entities."""
    
    def __init__(self, source: str, target: str, relationship_type: str, confidence: float = 0.5):
        self.source = source
        self.target = target
        self.relationship_type = relationship_type
        self.confidence = confidence
        self.first_seen = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.mention_count = 1
        self.contexts = []
        
    def add_mention(self, context: str = None):
        """Record a new mention of this relationship."""
        self.mention_count += 1
        self.last_seen = datetime.utcnow()
        if context:
            self.contexts.append(context)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary representation."""
        return {
            'source': self.source,
            'target': self.target,
            'relationship_type': self.relationship_type,
            'confidence': self.confidence,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'mention_count': self.mention_count,
            'contexts': self.contexts[-5:]  # Keep last 5 contexts
        }


class ContentIntelligenceService:
    """
    Service for extracting intelligence from content including entities, relationships, and temporal patterns.
    """
    
    def __init__(self):
        self.llm_service = LLMIntegrationService()
        self.entities = {}  # text -> Entity
        self.relationships = []  # List of Relationship objects
        self.temporal_patterns = defaultdict(list)
        
        # Entity extraction patterns
        self._setup_entity_patterns()
        
    def _setup_entity_patterns(self):
        """Setup regex patterns for entity extraction."""
        self.patterns = {
            'PERSON': [
                r'\b([A-Z][a-z]+ [A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',  # John Smith, John Michael Smith
                r'\b(Mr|Mrs|Ms|Dr|Prof|Sir|Madam)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b',
                r'\b([A-Z]\.\s*[A-Z][a-z]+)\b',  # J. Smith
            ],
            'ORGANIZATION': [
                r'\b([A-Z][a-z]*(?:\s+[A-Z][a-z]+)*(?:\s+(?:Inc|LLC|Corp|Corporation|Company|Co|Ltd|Limited|Group|Enterprises|International|Institute|Foundation|Association|Agency|Department|Ministry|Office)))\b',
                r'\b((?:The\s+)?[A-Z][a-z]*(?:\s+[A-Z][a-z]+)*(?:\s+(?:University|College|Hospital|School|Bank|Insurance|Media|News|Times|Post|Journal)))\b',
            ],
            'LOCATION': [
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][A-Z])\b',  # City, State
                r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*,\s*[A-Z][a-z]+)\b',  # City, Country
                r'\b((?:United\s+States|United\s+Kingdom|New\s+York|Los\s+Angeles|San\s+Francisco|Washington\s+DC|London|Paris|Tokyo|Berlin|Moscow|Beijing|Sydney))\b',
            ],
            'EMAIL': [
                r'\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            ],
            'PHONE': [
                r'\b(\+?1[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4})\b',
                r'\b(\+?[0-9]{1,3}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9})\b',
            ],
            'DATE': [
                r'\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b',
                r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b',
                r'\b(\d{4}-\d{2}-\d{2})\b',
            ],
            'MONEY': [
                r'\$([0-9,]+(?:\.[0-9]{2})?)\b',
                r'\b([0-9,]+(?:\.[0-9]{2})?\s+(?:USD|dollars|million|billion|thousand))\b',
            ],
            'URL': [
                r'\b(https?://[^\s<>"{}|\\^`\[\]]+)\b',
            ]
        }
        
        # Relationship patterns
        self.relationship_patterns = [
            (r'(\w+(?:\s+\w+)*)\s+(?:is|was|are|were)\s+(?:the|a|an)?\s*(CEO|president|director|manager|founder|owner|chair|chairperson|head|chief|leader)\s+of\s+(\w+(?:\s+\w+)*)', 'LEADS_ORGANIZATION'),
            (r'(\w+(?:\s+\w+)*)\s+(?:works?|worked?)\s+(?:at|for|in)\s+(\w+(?:\s+\w+)*)', 'WORKS_AT'),
            (r'(\w+(?:\s+\w+)*)\s+(?:is|was)\s+(?:born|located|based)\s+in\s+(\w+(?:\s+\w+)*)', 'LOCATED_IN'),
            (r'(\w+(?:\s+\w+)*)\s+(?:owns?|owned?)\s+(\w+(?:\s+\w+)*)', 'OWNS'),
            (r'(\w+(?:\s+\w+)*)\s+(?:partners?|partnered?)\s+with\s+(\w+(?:\s+\w+)*)', 'PARTNERS_WITH'),
            (r'(\w+(?:\s+\w+)*)\s+(?:acquires?|acquired?)\s+(\w+(?:\s+\w+)*)', 'ACQUIRES'),
            (r'(\w+(?:\s+\w+)*)\s+(?:invests?|invested?)\s+in\s+(\w+(?:\s+\w+)*)', 'INVESTS_IN'),
        ]
    
    async def extract_entities(self, content: str, source_url: str = None) -> List[Entity]:
        """
        Extract entities from text content.
        
        Args:
            content: Text content to analyze
            source_url: Source URL for tracking
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Extract entities using regex patterns
        for entity_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    entity_text = match.group(1) if match.groups() else match.group(0)
                    entity_text = entity_text.strip()
                    
                    if len(entity_text) < 2:  # Skip very short matches
                        continue
                    
                    # Calculate confidence based on pattern strength
                    confidence = self._calculate_entity_confidence(entity_text, entity_type)
                    
                    # Create or update entity
                    entity_key = f"{entity_type}:{entity_text.lower()}"
                    if entity_key in self.entities:
                        self.entities[entity_key].add_mention(source_url)
                    else:
                        entity = Entity(entity_text, entity_type, confidence)
                        entity.add_mention(source_url)
                        self.entities[entity_key] = entity
                        entities.append(entity)
        
        # Use LLM for advanced entity extraction if available
        if settings.OPENROUTER_API_KEY:
            try:
                llm_entities = await self._extract_entities_with_llm(content, source_url)
                entities.extend(llm_entities)
            except Exception as e:
                logger.warning(f"LLM entity extraction failed: {e}")
        
        logger.info(f"Extracted {len(entities)} entities from content")
        return entities
    
    async def extract_relationships(self, content: str, entities: List[Entity]) -> List[Relationship]:
        """
        Extract relationships between entities from text content.
        
        Args:
            content: Text content to analyze
            entities: List of entities found in the content
            
        Returns:
            List of extracted relationships
        """
        relationships = []
        entity_texts = {entity.text.lower() for entity in entities}
        
        # Extract relationships using pattern matching
        for pattern, rel_type in self.relationship_patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE)
            for match in matches:
                source_text = match.group(1).strip()
                target_text = match.group(2).strip()
                
                # Check if both entities exist in our entity list
                if (source_text.lower() in entity_texts and 
                    target_text.lower() in entity_texts):
                    
                    # Calculate confidence
                    confidence = self._calculate_relationship_confidence(match, content)
                    
                    # Create relationship
                    relationship = Relationship(source_text, target_text, rel_type, confidence)
                    relationship.add_mention(content[:200])  # Add context snippet
                    
                    self.relationships.append(relationship)
                    relationships.append(relationship)
        
        # Use LLM for advanced relationship extraction
        if settings.OPENROUTER_API_KEY:
            try:
                llm_relationships = await self._extract_relationships_with_llm(content, entities)
                relationships.extend(llm_relationships)
            except Exception as e:
                logger.warning(f"LLM relationship extraction failed: {e}")
        
        logger.info(f"Extracted {len(relationships)} relationships from content")
        return relationships
    
    async def analyze_temporal_patterns(self, content: str, entities: List[Entity]) -> Dict[str, Any]:
        """
        Analyze temporal patterns in content.
        
        Args:
            content: Text content to analyze
            entities: List of entities found in the content
            
        Returns:
            Dictionary with temporal analysis results
        """
        temporal_analysis = {
            'dates_mentioned': [],
            'time_periods': [],
            'entity_timeline': defaultdict(list),
            'frequency_patterns': {},
            'trend_indicators': []
        }
        
        # Extract dates
        date_pattern = self.patterns['DATE'][0]  # Use first date pattern
        dates = re.findall(date_pattern, content, re.IGNORECASE)
        
        for date_str in dates:
            try:
                parsed_date = self._parse_date(date_str)
                if parsed_date:
                    temporal_analysis['dates_mentioned'].append({
                        'text': date_str,
                        'parsed': parsed_date.isoformat(),
                        'days_ago': (datetime.utcnow() - parsed_date).days
                    })
            except Exception as e:
                logger.debug(f"Failed to parse date '{date_str}': {e}")
        
        # Analyze entity mentions over time
        for entity in entities:
            if entity.entity_type in ['PERSON', 'ORGANIZATION']:
                temporal_analysis['entity_timeline'][entity.text].append({
                    'date': datetime.utcnow().isoformat(),
                    'confidence': entity.confidence,
                    'context': 'recent_mention'
                })
        
        # Detect frequency patterns
        words = content.lower().split()
        word_freq = Counter(words)
        
        # Look for trending terms (high frequency, recent)
        trending_threshold = max(3, len(words) // 1000)  # Adaptive threshold
        temporal_analysis['frequency_patterns'] = {
            word: count for word, count in word_freq.items() 
            if count >= trending_threshold and len(word) > 3
        }
        
        # Detect trend indicators
        trend_words = ['new', 'recent', 'latest', 'upcoming', 'breaking', 'developing', 'emerging']
        for trend_word in trend_words:
            if trend_word in content.lower():
                temporal_analysis['trend_indicators'].append(trend_word)
        
        return dict(temporal_analysis)
    
    async def extract_intelligence_summary(self, content: str, source_url: str = None) -> Dict[str, Any]:
        """
        Extract comprehensive intelligence summary from content.
        
        Args:
            content: Text content to analyze
            source_url: Source URL for tracking
            
        Returns:
            Comprehensive intelligence summary
        """
        logger.info(f"Extracting intelligence summary from {source_url or 'unknown source'}")
        
        # Extract entities
        entities = await self.extract_entities(content, source_url)
        
        # Extract relationships
        relationships = await self.extract_relationships(content, entities)
        
        # Analyze temporal patterns
        temporal_analysis = await self.analyze_temporal_patterns(content, entities)
        
        # Generate content summary
        content_summary = self._generate_content_summary(content)
        
        # Calculate intelligence scores
        intelligence_scores = self._calculate_intelligence_scores(content, entities, relationships)
        
        # Extract key insights
        key_insights = await self._extract_key_insights(content, entities, relationships)
        
        summary = {
            'source_url': source_url,
            'processed_at': datetime.utcnow().isoformat(),
            'content_summary': content_summary,
            'entities': [entity.to_dict() for entity in entities],
            'relationships': [rel.to_dict() for rel in relationships],
            'temporal_analysis': temporal_analysis,
            'intelligence_scores': intelligence_scores,
            'key_insights': key_insights,
            'content_hash': hashlib.md5(content.encode()).hexdigest()[:16]
        }
        
        logger.info(f"Generated intelligence summary with {len(entities)} entities and {len(relationships)} relationships")
        return summary
    
    def _calculate_entity_confidence(self, entity_text: str, entity_type: str) -> float:
        """Calculate confidence score for an entity."""
        base_confidence = 0.5
        
        # Boost confidence based on entity characteristics
        if entity_type == 'PERSON':
            if len(entity_text.split()) >= 2:  # Multiple words suggest full name
                base_confidence += 0.3
            if any(title in entity_text for title in ['Dr', 'Prof', 'Mr', 'Mrs', 'Ms']):
                base_confidence += 0.2
                
        elif entity_type == 'ORGANIZATION':
            org_indicators = ['Inc', 'LLC', 'Corp', 'Company', 'University', 'Institute', 'Foundation']
            if any(indicator in entity_text for indicator in org_indicators):
                base_confidence += 0.3
                
        elif entity_type == 'LOCATION':
            if ',' in entity_text:  # City, State format
                base_confidence += 0.2
                
        elif entity_type == 'EMAIL':
            base_confidence = 0.9  # Email patterns are quite reliable
            
        elif entity_type == 'URL':
            base_confidence = 0.95  # URL patterns are very reliable
        
        return min(1.0, base_confidence)
    
    def _calculate_relationship_confidence(self, match, content: str) -> float:
        """Calculate confidence score for a relationship."""
        base_confidence = 0.6
        
        # Boost confidence based on context
        context_window = 50
        start = max(0, match.start() - context_window)
        end = min(len(content), match.end() + context_window)
        context = content[start:end].lower()
        
        # Look for confidence boosters
        confidence_boosters = ['confirmed', 'announced', 'official', 'reported', 'stated']
        for booster in confidence_boosters:
            if booster in context:
                base_confidence += 0.2
                break
        
        # Look for confidence reducers
        confidence_reducers = ['allegedly', 'reportedly', 'supposedly', 'rumored']
        for reducer in confidence_reducers:
            if reducer in context:
                base_confidence -= 0.2
                break
        
        return max(0.1, min(1.0, base_confidence))
    
    async def _extract_entities_with_llm(self, content: str, source_url: str = None) -> List[Entity]:
        """Use LLM to extract entities that regex patterns might miss."""
        try:
            prompt = f"""
            Extract important entities from the following text. Focus on:
            - People (full names, titles)
            - Organizations (companies, institutions, agencies)
            - Locations (cities, countries, addresses)
            - Technologies, products, or services mentioned
            - Key dates, amounts, or other significant data points
            
            Text: {content[:2000]}  # Limit content length
            
            Return in JSON format:
            {{
                "entities": [
                    {{"text": "Entity Name", "type": "PERSON|ORGANIZATION|LOCATION|OTHER", "confidence": 0.8}}
                ]
            }}
            """
            
            response = await self.llm_service.analyze_content(prompt, max_tokens=1000)
            
            if response and 'entities' in response:
                entities = []
                for entity_data in response['entities']:
                    entity = Entity(
                        entity_data['text'],
                        entity_data['type'],
                        entity_data.get('confidence', 0.5)
                    )
                    entity.add_mention(source_url)
                    entities.append(entity)
                return entities
                
        except Exception as e:
            logger.error(f"LLM entity extraction error: {e}")
        
        return []
    
    async def _extract_relationships_with_llm(self, content: str, entities: List[Entity]) -> List[Relationship]:
        """Use LLM to extract complex relationships."""
        try:
            entity_names = [entity.text for entity in entities]
            prompt = f"""
            Analyze relationships between the following entities in the text:
            
            Entities: {', '.join(entity_names)}
            
            Text: {content[:2000]}
            
            Look for relationships like:
            - Employment/leadership (CEO, works at, leads)
            - Ownership (owns, acquired by)
            - Partnerships (partners with, collaborates with)
            - Location (based in, located in)
            - Family/personal connections
            
            Return in JSON format:
            {{
                "relationships": [
                    {{"source": "Entity A", "target": "Entity B", "type": "RELATIONSHIP_TYPE", "confidence": 0.7}}
                ]
            }}
            """
            
            response = await self.llm_service.analyze_content(prompt, max_tokens=1000)
            
            if response and 'relationships' in response:
                relationships = []
                for rel_data in response['relationships']:
                    relationship = Relationship(
                        rel_data['source'],
                        rel_data['target'],
                        rel_data['type'],
                        rel_data.get('confidence', 0.5)
                    )
                    relationships.append(relationship)
                return relationships
                
        except Exception as e:
            logger.error(f"LLM relationship extraction error: {e}")
        
        return []
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats."""
        try:
            # Try different date formats
            formats = [
                '%B %d, %Y',  # January 15, 2024
                '%m/%d/%Y',   # 01/15/2024
                '%m/%d/%y',   # 01/15/24
                '%Y-%m-%d',   # 2024-01-15
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
                    
        except Exception:
            pass
        
        return None
    
    def _generate_content_summary(self, content: str) -> Dict[str, Any]:
        """Generate a summary of the content."""
        # Basic content statistics
        words = content.split()
        sentences = re.split(r'[.!?]+', content)
        
        return {
            'word_count': len(words),
            'sentence_count': len([s for s in sentences if s.strip()]),
            'character_count': len(content),
            'readability_score': self._calculate_readability_score(content),
            'language': 'en',  # Could be enhanced with language detection
            'topics': self._extract_topics(content),
            'sentiment': self._analyze_sentiment(content)
        }
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate basic readability score."""
        sentences = re.split(r'[.!?]+', content)
        words = content.split()
        
        if not sentences or not words:
            return 0.0
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simple readability score (higher = more readable)
        readability = 100 - (1.015 * avg_sentence_length) - (84.6 * (avg_word_length / 100))
        return max(0.0, min(100.0, readability))
    
    def _extract_topics(self, content: str) -> List[str]:
        """Extract main topics from content."""
        # Simple keyword-based topic extraction
        topic_keywords = {
            'technology': ['software', 'computer', 'digital', 'technology', 'internet', 'data'],
            'business': ['company', 'business', 'market', 'financial', 'economy', 'revenue'],
            'politics': ['government', 'policy', 'political', 'election', 'democracy', 'congress'],
            'health': ['health', 'medical', 'hospital', 'disease', 'treatment', 'patient'],
            'science': ['research', 'study', 'scientific', 'experiment', 'analysis', 'discovery'],
            'security': ['security', 'cyber', 'attack', 'breach', 'vulnerability', 'threat']
        }
        
        content_lower = content.lower()
        topics = []
        
        for topic, keywords in topic_keywords.items():
            keyword_count = sum(1 for keyword in keywords if keyword in content_lower)
            if keyword_count >= 2:  # At least 2 mentions
                topics.append(topic)
        
        return topics
    
    def _analyze_sentiment(self, content: str) -> str:
        """Basic sentiment analysis."""
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'achievement', 'growth']
        negative_words = ['bad', 'terrible', 'negative', 'failure', 'decline', 'loss', 'problem']
        
        content_lower = content.lower()
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _calculate_intelligence_scores(self, content: str, entities: List[Entity], relationships: List[Relationship]) -> Dict[str, float]:
        """Calculate various intelligence scores."""
        scores = {}
        
        # Entity density score
        word_count = len(content.split())
        entity_density = len(entities) / max(word_count, 1) * 100
        scores['entity_density'] = min(10.0, entity_density)
        
        # Relationship complexity score
        scores['relationship_complexity'] = min(10.0, len(relationships) * 2)
        
        # Entity diversity score
        entity_types = set(entity.entity_type for entity in entities)
        scores['entity_diversity'] = min(10.0, len(entity_types) * 2)
        
        # Content richness score
        unique_words = len(set(content.lower().split()))
        content_richness = unique_words / max(word_count, 1) * 10
        scores['content_richness'] = min(10.0, content_richness)
        
        # Overall intelligence score
        scores['overall'] = sum(scores.values()) / len(scores)
        
        return scores
    
    async def _extract_key_insights(self, content: str, entities: List[Entity], relationships: List[Relationship]) -> List[str]:
        """Extract key insights from the analyzed content."""
        insights = []
        
        # High-confidence entities
        high_conf_entities = [e for e in entities if e.confidence > 0.8]
        if high_conf_entities:
            insights.append(f"High-confidence entities identified: {', '.join([e.text for e in high_conf_entities[:3]])}")
        
        # Strong relationships
        strong_relationships = [r for r in relationships if r.confidence > 0.7]
        if strong_relationships:
            insights.append(f"Strong relationships found: {len(strong_relationships)} connections identified")
        
        # Organization clusters
        org_entities = [e for e in entities if e.entity_type == 'ORGANIZATION']
        if len(org_entities) > 1:
            insights.append(f"Multiple organizations mentioned: {', '.join([e.text for e in org_entities[:3]])}")
        
        # Location patterns
        location_entities = [e for e in entities if e.entity_type == 'LOCATION']
        if len(location_entities) > 1:
            insights.append(f"Geographic scope: {len(location_entities)} locations referenced")
        
        # Use LLM for advanced insights if available
        if settings.OPENROUTER_API_KEY and len(content) > 200:
            try:
                prompt = f"""
                Based on the following analyzed content, provide 2-3 key intelligence insights:
                
                Entities: {', '.join([e.text for e in entities[:5]])}
                Relationships: {len(relationships)} relationships found
                
                Content excerpt: {content[:1000]}
                
                Provide concise, actionable insights for OSINT analysis.
                """
                
                response = await self.llm_service.analyze_content(prompt, max_tokens=500)
                if response:
                    insights.extend(response.split('\n')[:2])
                    
            except Exception as e:
                logger.warning(f"LLM insight extraction failed: {e}")
        
        return insights[:5]  # Limit to top 5 insights


async def analyze_content_intelligence(content: str, source_url: str = None) -> Dict[str, Any]:
    """
    Convenience function for content intelligence analysis.
    
    Args:
        content: Text content to analyze
        source_url: Source URL for tracking
        
    Returns:
        Comprehensive intelligence analysis
    """
    service = ContentIntelligenceService()
    return await service.extract_intelligence_summary(content, source_url)