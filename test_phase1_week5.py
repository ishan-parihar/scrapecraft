"""
Comprehensive test suite for Week 5: Enhanced Search & Collection
Tests specialized search, multi-engine deduplication, and social media integration.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.services.enhanced_search_service import EnhancedSearchService, perform_enhanced_search
from app.services.social_media_service import SocialMediaService, perform_social_media_search
from app.services.real_search_service import RealSearchService
from app.config import settings


class TestEnhancedSearchService:
    """Test the enhanced search service capabilities."""
    
    @pytest.fixture
    def enhanced_service(self):
        """Create enhanced search service instance."""
        return EnhancedSearchService()
    
    @pytest.fixture
    def mock_search_results(self):
        """Mock search results for testing."""
        return {
            'google': [
                {
                    'title': 'Artificial Intelligence News - Latest Updates',
                    'url': 'https://example.com/ai-news',
                    'snippet': 'Latest developments in artificial intelligence',
                    'domain': 'example.com',
                    'source': 'google',
                    'position': 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ],
            'duckduckgo': [
                {
                    'title': 'AI Research Breakthrough',
                    'url': 'https://example.com/ai-research',
                    'snippet': 'New breakthrough in AI research',
                    'domain': 'example.com',
                    'source': 'duckduckgo',
                    'position': 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_search_news(self, enhanced_service):
        """Test news-specific search functionality."""
        with patch.object(RealSearchService, 'search_google') as mock_search:
            mock_search.return_value = [
                {
                    'title': 'Breaking News: AI Development',
                    'url': 'https://cnn.com/ai-news',
                    'snippet': 'Latest AI developments announced today',
                    'domain': 'cnn.com',
                    'source': 'google',
                    'position': 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
            
            results = await enhanced_service.search_news("artificial intelligence", 5)
            
            assert len(results) > 0
            assert results[0]['content_type'] == 'news'
            assert 'freshness_score' in results[0]
            assert 'news_source' in results[0]
            assert results[0]['news_source'] == 'Cnn'
    
    @pytest.mark.asyncio
    async def test_search_academic(self, enhanced_service):
        """Test academic search functionality."""
        with patch.object(RealSearchService, 'multi_search') as mock_search:
            mock_search.return_value = {
                'google': [
                    {
                        'title': 'Machine Learning Research Paper',
                        'url': 'https://arxiv.org/ml-paper',
                        'snippet': 'New research in machine learning algorithms',
                        'domain': 'arxiv.org',
                        'source': 'google',
                        'position': 1,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                'duckduckgo': []
            }
            
            results = await enhanced_service.search_academic("machine learning", 5)
            
            assert len(results) > 0
            assert results[0]['content_type'] == 'academic'
            assert 'academic_score' in results[0]
            assert 'citation_count' in results[0]
            assert results[0]['academic_score'] > 5.0  # Should be high for academic content
    
    @pytest.mark.asyncio
    async def test_search_images(self, enhanced_service):
        """Test image search functionality."""
        with patch.object(RealSearchService, 'search_google') as mock_search:
            mock_search.return_value = [
                {
                    'title': 'AI Image Gallery',
                    'url': 'https://example.com/ai-images',
                    'snippet': 'Collection of AI-generated images',
                    'domain': 'example.com',
                    'source': 'google',
                    'position': 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
            
            results = await enhanced_service.search_images("artificial intelligence", 5)
            
            assert len(results) > 0
            assert results[0]['content_type'] == 'images'
            assert 'image_score' in results[0]
            assert results[0]['likely_images'] is True
    
    @pytest.mark.asyncio
    async def test_deduplicate_and_rank(self, enhanced_service, mock_search_results):
        """Test result deduplication and ranking."""
        query = "artificial intelligence"
        
        results = await enhanced_service.deduplicate_and_rank(mock_search_results, query)
        
        assert len(results) == 2  # Should have 2 unique results
        assert all('composite_score' in result for result in results)
        assert all('relevance_score' in result for result in results)
        assert all('authority_score' in result for result in results)
        assert all('quality_score' in result for result in results)
        
        # Results should be sorted by composite score
        assert results[0]['composite_score'] >= results[1]['composite_score']
    
    def test_normalize_url(self, enhanced_service):
        """Test URL normalization for deduplication."""
        url1 = "https://www.example.com/page/"
        url2 = "https://example.com/page"
        url3 = "HTTP://EXAMPLE.COM/PAGE"
        
        normalized1 = enhanced_service._normalize_url(url1)
        normalized2 = enhanced_service._normalize_url(url2)
        normalized3 = enhanced_service._normalize_url(url3)
        
        assert normalized1 == normalized2 == normalized3
    
    def test_calculate_relevance_score(self, enhanced_service):
        """Test relevance score calculation."""
        result = {
            'title': 'Artificial Intelligence Research',
            'snippet': 'Latest AI research developments',
            'url': 'https://example.com/ai-research'
        }
        query = "artificial intelligence"
        
        score = enhanced_service._calculate_relevance_score(result, query)
        
        assert 0 <= score <= 1.0
        assert score > 0.3  # Should be high for matching content
    
    def test_calculate_domain_authority(self, enhanced_service):
        """Test domain authority calculation."""
        # Test high authority domains
        assert enhanced_service._calculate_domain_authority('wikipedia.org') > 9.0
        assert enhanced_service._calculate_domain_authority('nasa.gov') > 8.5
        assert enhanced_service._calculate_domain_authority('arxiv.org') > 8.0
        
        # Test lower authority domains
        assert enhanced_service._calculate_domain_authority('example.com') <= 6.0
    
    def test_is_news_source(self, enhanced_service):
        """Test news source detection."""
        assert enhanced_service._is_news_source('https://cnn.com/article') is True
        assert enhanced_service._is_news_source('https://bbc.com/news') is True
        assert enhanced_service._is_news_source('https://example.com') is False
    
    def test_is_academic_source(self, enhanced_service):
        """Test academic source detection."""
        assert enhanced_service._is_academic_source('https://arxiv.org/abs/1234') is True
        assert enhanced_service._is_academic_source('https://scholar.google.com') is True
        assert enhanced_service._is_academic_source('https://example.com') is False


class TestSocialMediaService:
    """Test the social media service capabilities."""
    
    @pytest.fixture
    def social_service(self):
        """Create social media service instance."""
        return SocialMediaService()
    
    @pytest.fixture
    def mock_twitter_response(self):
        """Mock Twitter API response."""
        return {
            'data': [
                {
                    'id': '123456789',
                    'text': 'Latest developments in AI are exciting! #AI #MachineLearning',
                    'created_at': '2024-01-15T10:30:00Z',
                    'author_id': '987654321',
                    'public_metrics': {
                        'like_count': 150,
                        'retweet_count': 25,
                        'reply_count': 12,
                        'quote_count': 5
                    },
                    'lang': 'en'
                }
            ],
            'includes': {
                'users': [
                    {
                        'id': '987654321',
                        'username': 'airesearcher',
                        'name': 'AI Researcher',
                        'verified': True,
                        'public_metrics': {
                            'followers_count': 10000,
                            'following_count': 500
                        }
                    }
                ]
            }
        }
    
    @pytest.fixture
    def mock_reddit_response(self):
        """Mock Reddit API response."""
        return {
            'data': {
                'children': [
                    {
                        'data': {
                            'id': 'abcdef',
                            'title': 'New AI breakthrough announced',
                            'selftext': 'Researchers have made significant progress...',
                            'author': 'tech_enthusiast',
                            'score': 1250,
                            'ups': 1250,
                            'downs': 0,
                            'num_comments': 89,
                            'upvote_ratio': 0.95,
                            'subreddit': 'technology',
                            'created_utc': 1705123456,
                            'permalink': '/r/technology/comments/abcdef/new_ai_breakthrough/'
                        }
                    }
                ]
            }
        }
    
    @pytest.mark.asyncio
    async def test_search_twitter_success(self, social_service, mock_twitter_response):
        """Test successful Twitter search."""
        with patch.object(settings, 'TWITTER_BEARER_TOKEN', 'test_token'):
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.json = AsyncMock(return_value=mock_twitter_response)
                mock_get.return_value.__aenter__.return_value = mock_response
                
                results = await social_service.search_twitter("artificial intelligence", 5)
                
                assert len(results) == 1
                tweet = results[0]
                assert tweet['platform'] == 'twitter'
                assert tweet['id'] == '123456789'
                assert tweet['author']['username'] == 'airesearcher'
                assert tweet['author']['verified'] is True
                assert tweet['metrics']['likes'] == 150
                assert 'engagement_score' in tweet
    
    @pytest.mark.asyncio
    async def test_search_twitter_no_token(self, social_service):
        """Test Twitter search without API token."""
        with patch.object(settings, 'TWITTER_BEARER_TOKEN', ''):
            results = await social_service.search_twitter("test", 5)
            assert results == []
    
    @pytest.mark.asyncio
    async def test_search_reddit_success(self, social_service, mock_reddit_response):
        """Test successful Reddit search."""
        with patch.object(settings, 'REDDIT_CLIENT_ID', 'test_id'):
            with patch.object(settings, 'REDDIT_CLIENT_SECRET', 'test_secret'):
                with patch.object(social_service, '_get_reddit_access_token') as mock_token:
                    mock_token.return_value = 'test_access_token'
                    
                    with patch('aiohttp.ClientSession.get') as mock_get:
                        mock_response = AsyncMock()
                        mock_response.status = 200
                        mock_response.json = AsyncMock(return_value=mock_reddit_response)
                        mock_get.return_value.__aenter__.return_value = mock_response
                        
                        results = await social_service.search_reddit("artificial intelligence", 5)
                        
                        assert len(results) == 1
                        post = results[0]
                        assert post['platform'] == 'reddit'
                        assert post['id'] == 'abcdef'
                        assert post['title'] == 'New AI breakthrough announced'
                        assert post['subreddit'] == 'technology'
                        assert post['metrics']['score'] == 1250
                        assert 'engagement_score' in post
    
    @pytest.mark.asyncio
    async def test_search_reddit_no_credentials(self, social_service):
        """Test Reddit search without API credentials."""
        with patch.object(settings, 'REDDIT_CLIENT_ID', ''):
            results = await social_service.search_reddit("test", 5)
            assert results == []
    
    def test_build_twitter_query(self, social_service):
        """Test Twitter query building."""
        query = social_service._build_twitter_query("artificial intelligence")
        assert "artificial intelligence" in query
        assert "-is:retweet" in query
        assert "lang:en" in query
    
    def test_build_reddit_query(self, social_service):
        """Test Reddit query building."""
        # Test without subreddits
        query = social_service._build_reddit_query("AI research")
        assert query == "AI research"
        
        # Test with subreddits
        query = social_service._build_reddit_query("AI research", ["technology", "MachineLearning"])
        assert "AI research" in query
        assert "subreddit:technology" in query
        assert "subreddit:MachineLearning" in query
    
    def test_calculate_twitter_engagement(self, social_service):
        """Test Twitter engagement score calculation."""
        tweet = {
            'metrics': {
                'likes': 100,
                'retweets': 20,
                'replies': 10,
                'quotes': 5
            },
            'author': {
                'followers': 1000
            }
        }
        
        score = social_service._calculate_twitter_engagement(tweet)
        assert 0 <= score <= 10.0
        assert score > 0  # Should have some engagement
    
    def test_calculate_reddit_engagement(self, social_service):
        """Test Reddit engagement score calculation."""
        post = {
            'metrics': {
                'score': 500,
                'upvotes': 500,
                'comments': 50,
                'ratio': 0.9
            }
        }
        
        score = social_service._calculate_reddit_engagement(post)
        assert 0 <= score <= 10.0
        assert score > 0  # Should have some engagement


class TestIntegrationWeek5:
    """Integration tests for Week 5 functionality."""
    
    @pytest.mark.asyncio
    async def test_perform_enhanced_search_news(self):
        """Test enhanced news search convenience function."""
        with patch('app.services.enhanced_search_service.RealSearchService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value.__aenter__.return_value = mock_instance
            mock_instance.search_google.return_value = [
                {
                    'title': 'AI Breaking News',
                    'url': 'https://cnn.com/ai-breaking',
                    'snippet': 'Breaking AI news today',
                    'domain': 'cnn.com',
                    'source': 'google',
                    'position': 1,
                    'timestamp': datetime.utcnow().isoformat()
                }
            ]
            
            results = await perform_enhanced_search("AI", search_type="news", max_results=5)
            
            assert len(results) > 0
            assert results[0]['content_type'] == 'news'
    
    @pytest.mark.asyncio
    async def test_perform_social_media_search(self):
        """Test social media search convenience function."""
        with patch('app.services.social_media_service.SocialMediaService') as mock_service:
            mock_instance = AsyncMock()
            mock_service.return_value.__aenter__.return_value = mock_instance
            mock_instance.search_twitter.return_value = [
                {
                    'id': '123',
                    'platform': 'twitter',
                    'content': 'AI is amazing!',
                    'author': {'username': 'user1'},
                    'metrics': {'likes': 10},
                    'engagement_score': 2.5,
                    'collected_at': datetime.utcnow().isoformat()
                }
            ]
            
            results = await perform_social_media_search("AI", platforms=['twitter'], max_results=5)
            
            assert 'twitter' in results
            assert len(results['twitter']) > 0
            assert results['twitter'][0]['platform'] == 'twitter'
    
    @pytest.mark.asyncio
    async def test_multi_platform_search_integration(self):
        """Test integrated multi-platform search."""
        enhanced_service = EnhancedSearchService()
        
        # Mock all the required services
        with patch.object(RealSearchService, 'multi_search') as mock_search, \
             patch.object(enhanced_service, '_search_twitter') as mock_twitter, \
             patch.object(enhanced_service, '_search_reddit') as mock_reddit:
            
            mock_search.return_value = {
                'google': [
                    {
                        'title': 'AI Research',
                        'url': 'https://example.com/ai',
                        'snippet': 'AI research news',
                        'domain': 'example.com',
                        'source': 'google',
                        'position': 1,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ]
            }
            
            mock_twitter.return_value = [
                {
                    'id': '123',
                    'platform': 'twitter',
                    'content': 'AI developments',
                    'author': {'username': 'researcher'},
                    'metrics': {'likes': 50},
                    'engagement_score': 5.0,
                    'collected_at': datetime.utcnow().isoformat()
                }
            ]
            
            mock_reddit.return_value = [
                {
                    'id': '456',
                    'platform': 'reddit',
                    'title': 'AI Discussion',
                    'author': {'username': 'tech_user'},
                    'metrics': {'score': 100},
                    'engagement_score': 3.0,
                    'collected_at': datetime.utcnow().isoformat()
                }
            ]
            
            # Test general search with deduplication
            general_results = await enhanced_service.deduplicate_and_rank(mock_search.return_value, "AI")
            assert len(general_results) > 0
            assert general_results[0]['composite_score'] > 0
            
            # Test social media search
            social_results = await enhanced_service.search_social_media("AI", ['twitter', 'reddit'], 5)
            assert 'twitter' in social_results
            assert 'reddit' in social_results
            assert len(social_results['twitter']) > 0
            assert len(social_results['reddit']) > 0


class TestErrorHandlingWeek5:
    """Test error handling for Week 5 functionality."""
    
    @pytest.mark.asyncio
    async def test_search_service_unavailable(self):
        """Test behavior when search services are unavailable."""
        enhanced_service = EnhancedSearchService()
        
        with patch.object(RealSearchService, 'search_google') as mock_search:
            mock_search.side_effect = Exception("Service unavailable")
            
            results = await enhanced_service.search_news("test", 5)
            
            # Should return empty list, not crash
            assert isinstance(results, list)
    
    @pytest.mark.asyncio
    async def test_social_media_rate_limit(self):
        """Test rate limit handling for social media."""
        social_service = SocialMediaService()
        
        with patch.object(settings, 'TWITTER_BEARER_TOKEN', 'test_token'):
            with patch('aiohttp.ClientSession.get') as mock_get:
                mock_response = AsyncMock()
                mock_response.status = 429  # Rate limit
                mock_get.return_value.__aenter__.return_value = mock_response
                
                results = await social_service.search_twitter("test", 5)
                
                # Should return empty list, not crash
                assert results == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])