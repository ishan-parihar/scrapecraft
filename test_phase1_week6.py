"""
Comprehensive test suite for Week 6: Advanced Web Intelligence
Tests deep web scraping, content intelligence, entity recognition, and relationship mapping.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.deep_web_scraping_service import DeepWebScrapingService, perform_deep_scraping
from app.services.content_intelligence_service import ContentIntelligenceService, Entity, Relationship, analyze_content_intelligence
from app.services.llm_integration import LLMIntegrationService
from app.config import settings


class TestDeepWebScrapingService:
    """Test the deep web scraping service capabilities."""
    
    @pytest.fixture
    def deep_scraper(self):
        """Create deep web scraping service instance."""
        return DeepWebScrapingService()
    
    @pytest.mark.asyncio
    async def test_dynamic_content_scraping_fallback(self, deep_scraper):
        """Test dynamic content scraping with fallback to basic scraping."""
        # Test when Selenium is not available
        with patch.object(deep_scraper, '_initialize_driver') as mock_init:
            mock_init.return_value = None
            
            with patch('app.services.deep_web_scraping_service.EnhancedWebScrapingService') as mock_service:
                mock_instance = AsyncMock()
                mock_service.return_value = mock_instance
                mock_instance.scrape_content.return_value = {
                    'url': 'https://example.com',
                    'title': 'Test Page',
                    'text_content': 'Test content',
                    'scraped_at': datetime.utcnow().isoformat()
                }
                
                result = await deep_scraper.scrape_dynamic_content('https://example.com')
                
                assert result['url'] == 'https://example.com'
                assert result['title'] == 'Test Page'
                assert 'text_content' in result
    
    @pytest.mark.asyncio
    async def test_stealth_mode_setup(self, deep_scraper):
        """Test stealth mode setup for anti-bot detection."""
        with patch('selenium.webdriver.Chrome') as mock_driver:
            mock_instance = Mock()
            mock_driver.return_value = mock_instance
            
            # Mock CDP command execution
            mock_instance.execute_cdp_cmd = Mock()
            
            await deep_scraper._initialize_driver()
            
            # Should have added stealth scripts
            assert mock_instance.execute_cdp_cmd.call_count > 0
    
    @pytest.mark.asyncio
    async def test_human_like_delay(self, deep_scraper):
        """Test human-like delay functionality."""
        start_time = asyncio.get_event_loop().time()
        await deep_scraper._human_like_delay(1.0, 2.0)
        end_time = asyncio.get_event_loop().time()
        
        # Should have delayed between 1-2 seconds
        delay = end_time - start_time
        assert 1.0 <= delay <= 2.5  # Allow some tolerance
    
    def test_safe_extract(self, deep_scraper):
        """Test safe text extraction from elements."""
        # Mock element with text
        mock_element = Mock()
        mock_element.get_text.return_value = "Test Text"
        
        result = deep_scraper._safe_extract(mock_element)
        assert result == "Test Text"
        
        # Test with None element
        result = deep_scraper._safe_extract(None)
        assert result == ""
        
        # Test with element without get_text
        mock_element_no_text = Mock()
        del mock_element_no_text.get_text
        
        result = deep_scraper._safe_extract(mock_element_no_text, "default")
        assert result == "default"
    
    def test_extract_main_text(self, deep_scraper):
        """Test main text extraction from HTML."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <head><title>Test</title></head>
            <body>
                <nav>Navigation</nav>
                <header>Header</header>
                <main>
                    <h1>Main Title</h1>
                    <p>This is the main content.</p>
                    <article>
                        <p>Article content here.</p>
                    </article>
                </main>
                <footer>Footer</footer>
                <script>console.log('test');</script>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        main_text = deep_scraper._extract_main_text(soup)
        
        assert "Main Title" in main_text
        assert "main content" in main_text
        assert "Article content" in main_text
        assert "Navigation" not in main_text
        assert "Footer" not in main_text
        assert "console.log" not in main_text
    
    def test_extract_structured_data(self, deep_scraper):
        """Test structured data extraction."""
        from bs4 import BeautifulSoup
        
        html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Person",
                    "name": "John Doe",
                    "jobTitle": "Software Engineer"
                }
                </script>
            </head>
            <body>
                <div itemscope itemtype="https://schema.org/Organization">
                    <span itemprop="name">Tech Corp</span>
                    <span itemprop="employee">John Doe</span>
                </div>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        structured_data = deep_scraper._extract_structured_data(soup)
        
        assert len(structured_data) == 2
        
        # Check JSON-LD data
        json_ld = next((item for item in structured_data if item['type'] == 'json-ld'), None)
        assert json_ld is not None
        assert json_ld['data']['name'] == "John Doe"
        
        # Check microdata
        microdata = next((item for item in structured_data if item['type'] == 'microdata'), None)
        assert microdata is not None
        assert microdata['properties']['name'] == "Tech Corp"
    
    def test_classify_link(self, deep_scraper):
        """Test link classification."""
        assert deep_scraper._classify_link("https://twitter.com/user") == "social_media"
        assert deep_scraper._classify_link("https://www.whitehouse.gov") == "government"
        assert deep_scraper._classify_link("https://mit.edu/research") == "academic"
        assert deep_scraper._classify_link("https://cnn.com/article") == "news"
        assert deep_scraper._classify_link("https://example.com/document.pdf") == "document"
        assert deep_scraper._classify_link("https://youtube.com/watch") == "video"
        assert deep_scraper._classify_link("https://example.com/image.jpg") == "image"
        assert deep_scraper._classify_link("https://example.com/page") == "general"
    
    @pytest.mark.asyncio
    async def test_scrape_multiple_pages(self, deep_scraper):
        """Test multi-page scraping."""
        # Mock the scrape_dynamic_content method
        with patch.object(deep_scraper, 'scrape_dynamic_content') as mock_scrape:
            mock_scrape.side_effect = [
                {
                    'url': 'https://example.com',
                    'links': [
                        {'url': 'https://example.com?page=2', 'text': 'Next'},
                        {'url': 'https://example.com?page=3', 'text': 'Next'}
                    ]
                },
                {
                    'url': 'https://example.com?page=2',
                    'links': []
                }
            ]
            
            results = await deep_scraper.scrape_multiple_pages(
                'https://example.com', 
                max_pages=2
            )
            
            assert len(results) == 2
            assert results[0]['url'] == 'https://example.com'
            assert results[1]['url'] == 'https://example.com?page=2'


class TestContentIntelligenceService:
    """Test the content intelligence service capabilities."""
    
    @pytest.fixture
    def intel_service(self):
        """Create content intelligence service instance."""
        return ContentIntelligenceService()
    
    @pytest.fixture
    def sample_content(self):
        """Sample content for testing."""
        return """
        John Smith, the CEO of TechCorp Inc., announced today that the company has acquired 
        Software Solutions LLC for $50 million. The deal was finalized on January 15, 2024. 
        Smith stated that this acquisition will help TechCorp expand its presence in the 
        technology sector. The company is headquartered in San Francisco, California. 
        Contact John at john.smith@techcorp.com or call +1-555-0123 for more information.
        """
    
    def test_entity_creation(self):
        """Test entity creation and properties."""
        entity = Entity("John Smith", "PERSON", 0.9)
        
        assert entity.text == "John Smith"
        assert entity.entity_type == "PERSON"
        assert entity.confidence == 0.9
        assert entity.mention_count == 1
        
        # Test adding mentions
        entity.add_mention("https://example.com")
        assert entity.mention_count == 2
        assert "https://example.com" in entity.source_urls
        
        # Test adding aliases
        entity.add_alias("J. Smith")
        assert "J. Smith" in entity.aliases
        
        # Test adding relationships
        entity.add_relationship("WORKS_AT", "TechCorp")
        assert len(entity.relationships) == 1
        assert entity.relationships[0]['target'] == "TechCorp"
    
    def test_relationship_creation(self):
        """Test relationship creation and properties."""
        rel = Relationship("John Smith", "TechCorp", "WORKS_AT", 0.8)
        
        assert rel.source == "John Smith"
        assert rel.target == "TechCorp"
        assert rel.relationship_type == "WORKS_AT"
        assert rel.confidence == 0.8
        assert rel.mention_count == 1
        
        # Test adding mentions
        rel.add_mention("John works at TechCorp")
        assert rel.mention_count == 2
        assert "John works at TechCorp" in rel.contexts
    
    @pytest.mark.asyncio
    async def test_extract_entities(self, intel_service, sample_content):
        """Test entity extraction from content."""
        entities = await intel_service.extract_entities(sample_content, "https://example.com")
        
        # Should extract various entity types
        entity_types = {entity.entity_type for entity in entities}
        assert 'PERSON' in entity_types
        assert 'ORGANIZATION' in entity_types
        assert 'LOCATION' in entity_types
        assert 'EMAIL' in entity_types
        assert 'PHONE' in entity_types
        assert 'MONEY' in entity_types
        assert 'DATE' in entity_types
        
        # Check specific entities
        entity_texts = {entity.text for entity in entities}
        assert "John Smith" in entity_texts
        assert "TechCorp Inc." in entity_texts
        assert "San Francisco" in entity_texts
        assert "john.smith@techcorp.com" in entity_texts
    
    @pytest.mark.asyncio
    async def test_extract_relationships(self, intel_service, sample_content):
        """Test relationship extraction from content."""
        # First extract entities
        entities = await intel_service.extract_entities(sample_content)
        
        # Then extract relationships
        relationships = await intel_service.extract_relationships(sample_content, entities)
        
        # Should find relationships
        relationship_types = {rel.relationship_type for rel in relationships}
        assert 'LEADS_ORGANIZATION' in relationship_types or 'WORKS_AT' in relationship_types
        
        # Check relationship structure
        for rel in relationships:
            assert rel.source in [entity.text for entity in entities]
            assert rel.target in [entity.text for entity in entities]
            assert 0.0 <= rel.confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns(self, intel_service, sample_content):
        """Test temporal pattern analysis."""
        entities = await intel_service.extract_entities(sample_content)
        temporal_analysis = await intel_service.analyze_temporal_patterns(sample_content, entities)
        
        assert 'dates_mentioned' in temporal_analysis
        assert 'time_periods' in temporal_analysis
        assert 'entity_timeline' in temporal_analysis
        assert 'frequency_patterns' in temporal_analysis
        assert 'trend_indicators' in temporal_analysis
        
        # Should find the date mentioned in content
        dates = temporal_analysis['dates_mentioned']
        assert len(dates) > 0
        assert any('January' in date['text'] for date in dates)
    
    @pytest.mark.asyncio
    async def test_extract_intelligence_summary(self, intel_service, sample_content):
        """Test comprehensive intelligence summary extraction."""
        summary = await intel_service.extract_intelligence_summary(sample_content, "https://example.com")
        
        # Check all required sections
        assert 'source_url' in summary
        assert 'processed_at' in summary
        assert 'content_summary' in summary
        assert 'entities' in summary
        assert 'relationships' in summary
        assert 'temporal_analysis' in summary
        assert 'intelligence_scores' in summary
        assert 'key_insights' in summary
        assert 'content_hash' in summary
        
        # Check content summary
        content_summary = summary['content_summary']
        assert content_summary['word_count'] > 0
        assert content_summary['sentence_count'] > 0
        assert 'readability_score' in content_summary
        assert 'topics' in content_summary
        assert 'sentiment' in content_summary
        
        # Check intelligence scores
        scores = summary['intelligence_scores']
        assert 'entity_density' in scores
        assert 'relationship_complexity' in scores
        assert 'entity_diversity' in scores
        assert 'content_richness' in scores
        assert 'overall' in scores
        
        # Check key insights
        insights = summary['key_insights']
        assert len(insights) > 0
        assert all(isinstance(insight, str) for insight in insights)
    
    def test_calculate_entity_confidence(self, intel_service):
        """Test entity confidence calculation."""
        # Test person confidence
        confidence = intel_service._calculate_entity_confidence("Dr. John Smith", "PERSON")
        assert confidence > 0.7  # Should be high for "Dr. John Smith"
        
        # Test organization confidence
        confidence = intel_service._calculate_entity_confidence("TechCorp Inc.", "ORGANIZATION")
        assert confidence > 0.7  # Should be high for "Inc."
        
        # Test email confidence
        confidence = intel_service._calculate_entity_confidence("test@example.com", "EMAIL")
        assert confidence > 0.8  # Should be high for emails
        
        # Test URL confidence
        confidence = intel_service._calculate_entity_confidence("https://example.com", "URL")
        assert confidence > 0.9  # Should be very high for URLs
    
    def test_calculate_relationship_confidence(self, intel_service):
        """Test relationship confidence calculation."""
        content = "John Smith is the CEO of TechCorp Inc., confirmed today."
        
        # Create a mock match object
        class MockMatch:
            def __init__(self):
                self.start_pos = 0
                self.end_pos = 20
            
            def start(self):
                return self.start_pos
            
            def end(self):
                return self.end_pos
        
        mock_match = MockMatch()
        confidence = intel_service._calculate_relationship_confidence(mock_match, content)
        
        assert 0.0 <= confidence <= 1.0
        # Should be boosted by "confirmed" in context
        assert confidence > 0.5
    
    def test_parse_date(self, intel_service):
        """Test date parsing."""
        # Test various date formats
        assert intel_service._parse_date("January 15, 2024") is not None
        assert intel_service._parse_date("01/15/2024") is not None
        assert intel_service._parse_date("2024-01-15") is not None
        assert intel_service._parse_date("invalid date") is None
    
    def test_generate_content_summary(self, intel_service):
        """Test content summary generation."""
        content = "This is a test sentence. This is another test sentence. One more sentence for testing."
        
        summary = intel_service._generate_content_summary(content)
        
        assert summary['word_count'] == 16
        assert summary['sentence_count'] == 3
        assert summary['character_count'] == len(content)
        assert 'readability_score' in summary
        assert 'topics' in summary
        assert 'sentiment' in summary
        assert 0.0 <= summary['readability_score'] <= 100.0
        assert summary['sentiment'] in ['positive', 'negative', 'neutral']
    
    def test_extract_topics(self, intel_service):
        """Test topic extraction."""
        content = """
        The latest technology news shows that software companies are growing rapidly.
        Computer science research has made significant breakthroughs in artificial intelligence.
        Business analysts predict continued growth in the tech sector.
        """
        
        topics = intel_service._extract_topics(content)
        
        assert 'technology' in topics
        assert 'business' in topics
        assert 'science' in topics
    
    def test_calculate_intelligence_scores(self, intel_service):
        """Test intelligence score calculation."""
        content = "Sample content for testing."
        entities = [Entity("John Doe", "PERSON", 0.9), Entity("TechCorp", "ORGANIZATION", 0.8)]
        relationships = [Relationship("John Doe", "TechCorp", "WORKS_AT", 0.8)]
        
        scores = intel_service._calculate_intelligence_scores(content, entities, relationships)
        
        assert 'entity_density' in scores
        assert 'relationship_complexity' in scores
        assert 'entity_diversity' in scores
        assert 'content_richness' in scores
        assert 'overall' in scores
        
        # All scores should be between 0 and 10
        for score in scores.values():
            assert 0.0 <= score <= 10.0


class TestIntegrationWeek6:
    """Integration tests for Week 6 functionality."""
    
    @pytest.mark.asyncio
    async def test_deep_scraping_with_content_intelligence(self):
        """Test integration between deep scraping and content intelligence."""
        # Mock deep scraping result
        mock_scraping_result = {
            'url': 'https://example.com',
            'title': 'Company News',
            'text_content': """
            TechCorp announced today that CEO Jane Smith has secured a $10 million investment 
            from Global Ventures. The company, based in New York, plans to expand operations 
            to San Francisco. Contact: jane.smith@techcorp.com or +1-555-0123.
            """,
            'scraped_at': datetime.utcnow().isoformat()
        }
        
        # Analyze with content intelligence
        analysis = await analyze_content_intelligence(
            mock_scraping_result['text_content'],
            mock_scraping_result['url']
        )
        
        assert 'entities' in analysis
        assert 'relationships' in analysis
        assert len(analysis['entities']) > 0
        
        # Check for expected entities
        entity_texts = [entity['text'] for entity in analysis['entities']]
        assert "Jane Smith" in entity_texts or "TechCorp" in entity_texts
        assert "New York" in entity_texts or "San Francisco" in entity_texts
    
    @pytest.mark.asyncio
    async def test_perform_deep_scraping_convenience(self):
        """Test convenience function for deep scraping."""
        with patch('app.services.deep_web_scraping_service.DeepWebScrapingService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value.__aenter__.return_value = mock_instance
            mock_instance.scrape_dynamic_content.return_value = {
                'url': 'https://example.com',
                'title': 'Test Page',
                'text_content': 'Test content'
            }
            
            result = await perform_deep_scraping(
                'https://example.com',
                scroll_down=True,
                max_scrolls=2
            )
            
            assert result['url'] == 'https://example.com'
            assert result['title'] == 'Test Page'
    
    @pytest.mark.asyncio
    async def test_end_to_end_intelligence_pipeline(self):
        """Test end-to-end intelligence extraction pipeline."""
        # Create a realistic scenario
        sample_content = """
        Breaking News: Global Technology Holdings announced the acquisition of AI Solutions 
        Inc. for $75 million on December 1, 2023. The deal was led by CEO Michael Johnson 
        and CTO Sarah Williams. AI Solutions, a Boston-based startup specializing in machine 
        learning, will become a subsidiary of Global Tech. Johnson stated that this acquisition 
        strengthens their position in the AI market. Contact: investors@globaltech.com or 
        call +1-800-555-0198.
        """
        
        # Extract intelligence
        analysis = await analyze_content_intelligence(sample_content, "https://news.example.com/article")
        
        # Verify comprehensive analysis
        assert analysis['source_url'] == "https://news.example.com/article"
        assert len(analysis['entities']) >= 5  # Should find multiple entities
        assert len(analysis['relationships']) >= 1  # Should find relationships
        assert analysis['intelligence_scores']['overall'] > 0
        assert len(analysis['key_insights']) >= 2  # Should generate insights
        
        # Check for specific entity types
        entity_types = {entity['entity_type'] for entity in analysis['entities']}
        assert 'PERSON' in entity_types
        assert 'ORGANIZATION' in entity_types
        assert 'LOCATION' in entity_types
        assert 'MONEY' in entity_types
        assert 'EMAIL' in entity_types
        assert 'PHONE' in entity_types
        assert 'DATE' in entity_types


class TestErrorHandlingWeek6:
    """Test error handling for Week 6 functionality."""
    
    @pytest.mark.asyncio
    async def test_deep_scraping_selenium_unavailable(self):
        """Test fallback when Selenium is not available."""
        service = DeepWebScrapingService()
        
        with patch('selenium.webdriver.Chrome') as mock_chrome:
            mock_chrome.side_effect = Exception("Selenium not available")
            
            # Should handle gracefully and fall back to basic scraping
            result = await service.scrape_dynamic_content('https://example.com')
            
            # Should still return some result due to fallback
            assert isinstance(result, dict)
    
    @pytest.mark.asyncio
    async def test_content_intelligence_llm_fallback(self):
        """Test content intelligence when LLM is not available."""
        service = ContentIntelligenceService()
        
        with patch.object(settings, 'OPENROUTER_API_KEY', ''):
            # Should work without LLM using regex patterns
            entities = await service.extract_entities("John Smith works at TechCorp")
            
            assert len(entities) > 0
            assert any(entity.text == "John Smith" for entity in entities)
            assert any(entity.entity_type == "PERSON" for entity in entities)
    
    @pytest.mark.asyncio
    async def test_malformed_content_handling(self):
        """Test handling of malformed or empty content."""
        service = ContentIntelligenceService()
        
        # Test with empty content
        summary = await service.extract_intelligence_summary("")
        assert summary['content_summary']['word_count'] == 0
        assert summary['entities'] == []
        assert summary['relationships'] == []
        
        # Test with malformed content
        malformed_content = "!!! ??? \n\n\t\t   "
        summary = await service.extract_intelligence_summary(malformed_content)
        assert isinstance(summary, dict)
        assert 'entities' in summary
        assert 'relationships' in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])