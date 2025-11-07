"""
Data Validation Framework
Validates search results quality, source reliability, and content relevance.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from urllib.parse import urlparse
from datetime import datetime, timedelta
from enum import Enum

from app.services.enhanced_web_scraping_service import ScrapedContent

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    """Levels of validation strictness."""
    LENIENT = "lenient"
    MODERATE = "moderate"
    STRICT = "strict"

class ContentCategory(Enum):
    """Categories of content for validation."""
    ARTICLE = "article"
    BLOG = "blog"
    NEWS = "news"
    DOCUMENTATION = "documentation"
    FORUM = "forum"
    COMMERCIAL = "commercial"
    SOCIAL_MEDIA = "social_media"
    ACADEMIC = "academic"
    UNKNOWN = "unknown"

@dataclass
class ValidationRule:
    """Individual validation rule."""
    name: str
    description: str
    validator_func: callable
    weight: float = 1.0
    level: ValidationLevel = ValidationLevel.MODERATE

@dataclass
class ValidationResult:
    """Result of validation."""
    is_valid: bool
    overall_score: float
    rule_results: Dict[str, bool]
    violations: List[str]
    warnings: List[str]
    category: ContentCategory = ContentCategory.UNKNOWN
    reliability_score: float = 0.0
    freshness_score: float = 0.0

@dataclass
class SourceReliability:
    """Information about source reliability."""
    domain: str
    trust_score: float
    category: str
    last_updated: datetime
    citation_count: int = 0
    fact_check_rating: Optional[str] = None

class SourceReliabilityAssessment:
    """Assesses source reliability based on various factors."""
    
    def __init__(self):
        # Known reliable sources
        self.reliable_domains = {
            # Academic/Government
            'edu': 0.9, 'gov': 0.95, 'mil': 0.95,
            # Major news organizations
            'reuters.com': 0.85, 'ap.org': 0.85, 'bbc.com': 0.8,
            'cnn.com': 0.75, 'npr.org': 0.8, 'wsj.com': 0.8,
            'nytimes.com': 0.75, 'washingtonpost.com': 0.75,
            # Technical sources
            'github.com': 0.8, 'stackoverflow.com': 0.75,
            'python.org': 0.9, 'w3.org': 0.9,
            # Reference sites
            'wikipedia.org': 0.7, 'wikidata.org': 0.75,
            # Research
            'arxiv.org': 0.9, 'pubmed.ncbi.nlm.nih.gov': 0.9,
            'scholar.google.com': 0.85
        }
        
        # Known problematic domains
        self.unreliable_domains = {
            'fake-news-site.com': 0.1,
            'conspiracy-theory.org': 0.1,
            # Add more as needed
        }
        
        # Domain patterns for categorization
        self.category_patterns = {
            ContentCategory.NEWS: [
                r'.*news.*', r'.*cnn.*', r'.*bbc.*', r'.*reuters.*',
                r'.*ap.*', r'.*npr.*', r'.*wsj.*', r'.*times.*'
            ],
            ContentCategory.ACADEMIC: [
                r'.*edu.*', r'.*ac\..*', r'.*scholar.*', r'.*arxiv.*',
                r'.*research.*', r'.*journal.*'
            ],
            ContentCategory.COMMERCIAL: [
                r'.*shop.*', r'.*store.*', r'.*buy.*', r'.*sale.*',
                r'.*amazon.*', r'.*ebay.*'
            ],
            ContentCategory.FORUM: [
                r'.*forum.*', r'.*reddit.*', r'.*discourse.*',
                r'.*board.*', r'.*discussion.*'
            ]
        }
    
    def assess_domain(self, domain: str) -> SourceReliability:
        """Assess the reliability of a domain."""
        domain = domain.lower()
        
        # Check exact matches
        if domain in self.reliable_domains:
            trust_score = self.reliable_domains[domain]
        elif domain in self.unreliable_domains:
            trust_score = self.unreliable_domains[domain]
        else:
            # Check TLD-based scoring
            trust_score = 0.5  # Default neutral score
            if domain.endswith('.edu'):
                trust_score = 0.9
            elif domain.endswith('.gov'):
                trust_score = 0.95
            elif domain.endswith('.mil'):
                trust_score = 0.95
            elif domain.endswith('.org'):
                trust_score = 0.6
        
        # Categorize domain
        category = self._categorize_domain(domain)
        
        return SourceReliability(
            domain=domain,
            trust_score=trust_score,
            category=category,
            last_updated=datetime.now()
        )
    
    def _categorize_domain(self, domain: str) -> str:
        """Categorize domain based on patterns."""
        for category, patterns in self.category_patterns.items():
            for pattern in patterns:
                if re.match(pattern, domain, re.IGNORECASE):
                    return category.value
        return "general"
    
    def update_reliability(self, domain: str, feedback: bool):
        """Update reliability based on user feedback."""
        # Simple feedback mechanism - could be enhanced with ML
        if domain in self.reliable_domains:
            if feedback:
                self.reliable_domains[domain] = min(1.0, self.reliable_domains[domain] + 0.01)
            else:
                self.reliable_domains[domain] = max(0.0, self.reliable_domains[domain] - 0.05)

class ContentValidator:
    """Validates content quality and relevance."""
    
    def __init__(self):
        self.validation_rules = self._initialize_rules()
        self.spam_indicators = [
            r'click here',
            r'buy now',
            r'limited time',
            r'act now',
            r'free.*money',
            r'guarantee.*result',
            r'risk.*free',
            r'winner.*selected',
            r'congratulations.*won'
        ]
        
        self.quality_indicators = [
            r'\b\d{4}\b',  # Years
            r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',  # Proper names
            r'\b\d+,\d+\b',  # Numbers with commas
            r'\b\w+\.\w+',  # Domain names
            r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'  # Dates
        ]
        
        self.min_content_length = 50
        self.max_content_length = 1000000  # 1MB
    
    def _initialize_rules(self) -> List[ValidationRule]:
        """Initialize validation rules."""
        rules = [
            ValidationRule(
                name="content_length",
                description="Content has reasonable length",
                validator_func=self._validate_content_length,
                weight=1.0
            ),
            ValidationRule(
                name="title_quality",
                description="Title is meaningful and not spammy",
                validator_func=self._validate_title_quality,
                weight=1.5
            ),
            ValidationRule(
                name="language_detection",
                description="Content is in recognizable language",
                validator_func=self._validate_language,
                weight=1.0
            ),
            ValidationRule(
                name="structure_quality",
                description="Content has proper structure",
                validator_func=self._validate_structure,
                weight=0.8
            ),
            ValidationRule(
                name="spam_detection",
                description="Content is not spam",
                validator_func=self._validate_no_spam,
                weight=2.0
            ),
            ValidationRule(
                name="readability",
                description="Content is readable and coherent",
                validator_func=self._validate_readability,
                weight=1.2
            )
        ]
        return rules
    
    def validate_search_result(
        self,
        title: str,
        snippet: str,
        url: str,
        content: Optional[ScrapedContent] = None,
        level: ValidationLevel = ValidationLevel.MODERATE
    ) -> ValidationResult:
        """Validate a search result."""
        rule_results = {}
        violations = []
        warnings = []
        total_score = 0.0
        total_weight = 0.0
        
        for rule in self.validation_rules:
            # Skip rules based on validation level
            if rule.level == ValidationLevel.STRICT and level != ValidationLevel.STRICT:
                continue
            if rule.level == ValidationLevel.LENIENT and level == ValidationLevel.STRICT:
                continue
            
            try:
                is_valid = rule.validator_func(title, snippet, url, content)
                rule_results[rule.name] = is_valid
                
                if is_valid:
                    total_score += rule.weight
                else:
                    violations.append(rule.description)
                
                total_weight += rule.weight
                
            except Exception as e:
                logger.warning(f"Validation rule '{rule.name}' failed: {e}")
                rule_results[rule.name] = False
                violations.append(f"Rule '{rule.name}' failed to execute")
                total_weight += rule.weight
        
        # Calculate overall score
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        is_valid = overall_score >= 0.6  # 60% of rules must pass
        
        # Categorize content
        category = self._categorize_content(title, snippet, url, content)
        
        # Calculate reliability and freshness scores
        reliability_score = self._calculate_reliability_score(url, content)
        freshness_score = self._calculate_freshness_score(content)
        
        return ValidationResult(
            is_valid=is_valid,
            overall_score=overall_score,
            rule_results=rule_results,
            violations=violations,
            warnings=warnings,
            category=category,
            reliability_score=reliability_score,
            freshness_score=freshness_score
        )
    
    def _validate_content_length(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> bool:
        """Validate content length."""
        if content:
            length = content.content_length
            return self.min_content_length <= length <= self.max_content_length
        else:
            # Fall back to snippet length
            return len(snippet) >= 10
    
    def _validate_title_quality(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> bool:
        """Validate title quality."""
        if not title or len(title) < 5:
            return False
        
        # Check for spam indicators in title
        title_lower = title.lower()
        spam_matches = sum(1 for pattern in self.spam_indicators if re.search(pattern, title_lower))
        return spam_matches == 0
    
    def _validate_language(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> bool:
        """Validate that content is in recognizable language."""
        # Simple check: ensure there are meaningful characters
        text = f"{title} {snippet}"
        if content:
            text += f" {content.text_content}"
        
        # Check for minimum word count and alphabetic characters
        words = re.findall(r'\b\w+\b', text)
        if len(words) < 3:
            return False
        
        # Check for reasonable proportion of alphabetic characters
        alpha_chars = sum(1 for c in text if c.isalpha())
        total_chars = len(text.replace(' ', ''))
        if total_chars == 0:
            return False
        
        alpha_ratio = alpha_chars / total_chars
        return alpha_ratio > 0.3
    
    def _validate_structure(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> bool:
        """Validate content structure."""
        if not content:
            return True  # Can't validate structure without content
        
        # Check for basic structural elements
        text = content.text_content
        
        # Has sentences (periods, question marks, exclamation marks)
        sentence_enders = re.findall(r'[.!?]', text)
        if len(sentence_enders) < 3:
            return False
        
        # Has paragraphs (multiple newlines)
        paragraphs = text.split('\n\n')
        if len(paragraphs) < 2:
            return False
        
        return True
    
    def _validate_no_spam(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> bool:
        """Validate that content is not spam."""
        text = f"{title} {snippet}"
        if content:
            text += f" {content.text_content}"
        
        text_lower = text.lower()
        spam_matches = sum(1 for pattern in self.spam_indicators if re.search(pattern, text_lower))
        
        # Allow some spam matches but not too many
        return spam_matches <= 2
    
    def _validate_readability(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> bool:
        """Validate content readability."""
        text = f"{title} {snippet}"
        if content:
            text += f" {content.text_content}"
        
        # Simple readability checks
        words = re.findall(r'\b\w+\b', text)
        if len(words) < 10:
            return False
        
        # Average word length (should be reasonable)
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length < 3 or avg_word_length > 10:
            return False
        
        # Sentence count
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) < 2:
            return False
        
        return True
    
    def _categorize_content(self, title: str, snippet: str, url: str, content: Optional[ScrapedContent]) -> ContentCategory:
        """Categorize the content type."""
        text = f"{title} {snippet}".lower()
        url_lower = url.lower()
        
        # Check for news indicators
        news_indicators = ['news', 'breaking', 'report', 'article', 'press']
        if any(indicator in text or indicator in url_lower for indicator in news_indicators):
            return ContentCategory.NEWS
        
        # Check for blog indicators
        blog_indicators = ['blog', 'post', 'opinion', 'editorial']
        if any(indicator in text or indicator in url_lower for indicator in blog_indicators):
            return ContentCategory.BLOG
        
        # Check for documentation
        doc_indicators = ['documentation', 'docs', 'manual', 'guide', 'tutorial', 'api']
        if any(indicator in text or indicator in url_lower for indicator in doc_indicators):
            return ContentCategory.DOCUMENTATION
        
        # Check for forum
        forum_indicators = ['forum', 'thread', 'discussion', 'reddit', 'stack overflow']
        if any(indicator in text or indicator in url_lower for indicator in forum_indicators):
            return ContentCategory.FORUM
        
        # Check for commercial
        commercial_indicators = ['shop', 'buy', 'sale', 'price', 'order', 'cart']
        if any(indicator in text or indicator in url_lower for indicator in commercial_indicators):
            return ContentCategory.COMMERCIAL
        
        # Check for social media
        social_indicators = ['twitter', 'facebook', 'instagram', 'linkedin', 'social']
        if any(indicator in text or indicator in url_lower for indicator in social_indicators):
            return ContentCategory.SOCIAL_MEDIA
        
        return ContentCategory.UNKNOWN
    
    def _calculate_reliability_score(self, url: str, content: Optional[ScrapedContent]) -> float:
        """Calculate reliability score based on URL and content."""
        domain = urlparse(url).netloc.lower()
        
        # Base score from domain
        if domain.endswith('.edu'):
            base_score = 0.9
        elif domain.endswith('.gov'):
            base_score = 0.95
        elif domain.endswith('.org'):
            base_score = 0.7
        else:
            base_score = 0.5
        
        # Boost for HTTPS
        if url.startswith('https://'):
            base_score += 0.1
        
        # Content factors
        if content:
            # Has metadata
            if content.metadata.get('meta_description'):
                base_score += 0.05
            
            # Good structure
            if len(content.links) > 3 and content.word_count > 100:
                base_score += 0.05
        
        return min(1.0, base_score)
    
    def _calculate_freshness_score(self, content: Optional[ScrapedContent]) -> float:
        """Calculate freshness score based on content timestamps."""
        if not content:
            return 0.5  # Default for unknown freshness
        
        # Use scrape time as fallback
        scrape_time = content.scrape_timestamp
        now = datetime.now()
        
        # Calculate age in days
        age_days = (now - scrape_time).days
        
        # Freshness score decreases with age
        if age_days <= 1:
            return 1.0
        elif age_days <= 7:
            return 0.8
        elif age_days <= 30:
            return 0.6
        elif age_days <= 365:
            return 0.4
        else:
            return 0.2

class DataValidationFramework:
    """Main framework for data validation."""
    
    def __init__(self):
        self.source_assessor = SourceReliabilityAssessment()
        self.content_validator = ContentValidator()
    
    def validate_search_results(
        self,
        search_results: List[Dict[str, Any]],
        scraped_contents: Optional[Dict[str, ScrapedContent]] = None,
        level: ValidationLevel = ValidationLevel.MODERATE
    ) -> List[Tuple[Dict, ValidationResult]]:
        """Validate multiple search results."""
        validated_results = []
        
        for result in search_results:
            url = result.get('url', '')
            content = scraped_contents.get(url) if scraped_contents else None
            
            validation_result = self.content_validator.validate_search_result(
                title=result.get('title', ''),
                snippet=result.get('snippet', ''),
                url=url,
                content=content,
                level=level
            )
            
            validated_results.append((result, validation_result))
        
        return validated_results
    
    def filter_valid_results(
        self,
        validated_results: List[Tuple[Dict, ValidationResult]],
        min_score: float = 0.6
    ) -> List[Dict]:
        """Filter results based on validation scores."""
        valid_results = []
        
        for result, validation in validated_results:
            if validation.is_valid and validation.overall_score >= min_score:
                valid_results.append(result)
        
        return valid_results
    
    def get_validation_summary(self, validated_results: List[Tuple[Dict, ValidationResult]]) -> Dict[str, Any]:
        """Get summary of validation results."""
        total_count = len(validated_results)
        valid_count = sum(1 for _, validation in validated_results if validation.is_valid)
        
        # Category distribution
        category_counts = {}
        for _, validation in validated_results:
            category = validation.category.value
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Average scores
        avg_overall = sum(validation.overall_score for _, validation in validated_results) / total_count
        avg_reliability = sum(validation.reliability_score for _, validation in validated_results) / total_count
        avg_freshness = sum(validation.freshness_score for _, validation in validated_results) / total_count
        
        # Common violations
        violation_counts = {}
        for _, validation in validated_results:
            for violation in validation.violations:
                violation_counts[violation] = violation_counts.get(violation, 0) + 1
        
        return {
            'total_results': total_count,
            'valid_results': valid_count,
            'validation_rate': valid_count / total_count if total_count > 0 else 0,
            'average_scores': {
                'overall': avg_overall,
                'reliability': avg_reliability,
                'freshness': avg_freshness
            },
            'category_distribution': category_counts,
            'common_violations': dict(sorted(violation_counts.items(), key=lambda x: x[1], reverse=True)[:5])
        }