"""
Social Media Integration Service
Provides real integration with Twitter API v2 and Reddit API for social media OSINT.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode, quote_plus

from app.config import settings
from app.services.error_handling import handle_errors, NetworkException, RateLimitException, RetryConfig

logger = logging.getLogger(__name__)

class SocialMediaService:
    """
    Service for collecting intelligence from social media platforms.
    """
    
    def __init__(self):
        self.session = None
        self.rate_limiters = {
            'twitter': {'last_request': 0, 'min_delay': 1.0},
            'reddit': {'last_request': 0, 'min_delay': 1.0}
        }
    
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': settings.USER_AGENT}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
    async def _rate_limit(self, platform: str):
        """Apply rate limiting for social media platforms."""
        if platform in self.rate_limiters:
            limiter = self.rate_limiters[platform]
            time_since_last = asyncio.get_event_loop().time() - limiter['last_request']
            if time_since_last < limiter['min_delay']:
                await asyncio.sleep(limiter['min_delay'] - time_since_last)
            limiter['last_request'] = asyncio.get_event_loop().time()
    
    @handle_errors(
        service_name="twitter",
        operation_name="search_twitter",
        retry_config=RetryConfig(max_retries=3, base_delay=2.0)
    )
    async def search_twitter(self, query: str, max_results: int = 10, time_range: str = "7d") -> List[Dict[str, Any]]:
        """
        Search Twitter using Twitter API v2.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            time_range: Time range (1d, 7d, 30d)
            
        Returns:
            List of tweets with metadata
        """
        if not settings.TWITTER_BEARER_TOKEN:
            logger.warning("Twitter Bearer Token not configured")
            return []
        
        await self._rate_limit('twitter')
        
        try:
            # Convert time range to Twitter API format
            start_time = self._calculate_start_time(time_range)
            
            # Build Twitter API v2 search URL
            url = "https://api.twitter.com/2/tweets/search/recent"
            
            params = {
                'query': self._build_twitter_query(query),
                'max_results': min(max_results, 100),  # Twitter API limit
                'tweet.fields': 'created_at,author_id,public_metrics,context_annotations,lang,geo',
                'user.fields': 'username,name,verified,public_metrics,location,description',
                'expansions': 'author_id,attachments.media_keys',
                'start_time': start_time
            }
            
            headers = {
                'Authorization': f'Bearer {settings.TWITTER_BEARER_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_twitter_response(data)
                elif response.status == 429:
                    raise RateLimitException("Twitter API rate limit exceeded")
                else:
                    logger.error(f"Twitter API error: {response.status} - {await response.text()}")
                    return []
                    
        except RateLimitException:
            logger.warning("Twitter rate limit hit, backing off")
            return []
        except Exception as e:
            logger.error(f"Twitter search failed: {e}")
            return []
    
    @handle_errors(
        service_name="reddit",
        operation_name="search_reddit",
        retry_config=RetryConfig(max_retries=3, base_delay=2.0)
    )
    async def search_reddit(self, query: str, max_results: int = 10, time_range: str = "7d", subreddits: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search Reddit using Reddit API.
        
        Args:
            query: Search query
            max_results: Maximum number of results
            time_range: Time range (1d, 7d, 30d)
            subreddits: List of specific subreddits to search
            
        Returns:
            List of Reddit posts with metadata
        """
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            logger.warning("Reddit API credentials not configured")
            return []
        
        await self._rate_limit('reddit')
        
        try:
            # Get Reddit access token
            access_token = await self._get_reddit_access_token()
            if not access_token:
                logger.error("Failed to get Reddit access token")
                return []
            
            # Build Reddit search URL
            url = "https://oauth.reddit.com/search"
            
            params = {
                'q': self._build_reddit_query(query, subreddits),
                'limit': min(max_results, 100),  # Reddit API limit
                'sort': 'relevance',
                't': self._convert_time_range(time_range),
                'type': 'link'
            }
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': settings.USER_AGENT
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._process_reddit_response(data)
                elif response.status == 429:
                    raise RateLimitException("Reddit API rate limit exceeded")
                else:
                    logger.error(f"Reddit API error: {response.status} - {await response.text()}")
                    return []
                    
        except RateLimitException:
            logger.warning("Reddit rate limit hit, backing off")
            return []
        except Exception as e:
            logger.error(f"Reddit search failed: {e}")
            return []
    
    async def get_twitter_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a Twitter user.
        
        Args:
            username: Twitter username
            
        Returns:
            User information or None if not found
        """
        if not settings.TWITTER_BEARER_TOKEN:
            return None
        
        await self._rate_limit('twitter')
        
        try:
            url = "https://api.twitter.com/2/users/by/username/" + username
            
            params = {
                'user.fields': 'created_at,description,location,pinned_tweet_id,profile_image_url,protected,public_metrics,url,username,verified,verified_type,withheld'
            }
            
            headers = {
                'Authorization': f'Bearer {settings.TWITTER_BEARER_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data')
                else:
                    logger.error(f"Twitter user API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get Twitter user info: {e}")
            return None
    
    async def get_reddit_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a Reddit user.
        
        Args:
            username: Reddit username
            
        Returns:
            User information or None if not found
        """
        if not settings.REDDIT_CLIENT_ID or not settings.REDDIT_CLIENT_SECRET:
            return None
        
        await self._rate_limit('reddit')
        
        try:
            access_token = await self._get_reddit_access_token()
            if not access_token:
                return None
            
            url = f"https://oauth.reddit.com/user/{username}/about"
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': settings.USER_AGENT
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('data')
                else:
                    logger.error(f"Reddit user API error: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get Reddit user info: {e}")
            return None
    
    def _build_twitter_query(self, query: str) -> str:
        """Build Twitter API query with operators."""
        # Add operators to filter out retweets and get original content
        return f"{query} -is:retweet lang:en"
    
    def _build_reddit_query(self, query: str, subreddits: List[str] = None) -> str:
        """Build Reddit API query with subreddit restrictions."""
        if subreddits:
            subreddit_filter = " OR ".join([f"subreddit:{sub}" for sub in subreddits])
            return f"{query} ({subreddit_filter})"
        return query
    
    def _calculate_start_time(self, time_range: str) -> str:
        """Calculate start time for API queries."""
        now = datetime.utcnow()
        if time_range == "1d":
            start_time = now - timedelta(days=1)
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
        else:
            start_time = now - timedelta(days=7)  # Default to 7 days
        
        return start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    def _convert_time_range(self, time_range: str) -> str:
        """Convert time range to Reddit API format."""
        mapping = {
            "1d": "day",
            "7d": "week", 
            "30d": "month",
            "365d": "year"
        }
        return mapping.get(time_range, "week")
    
    async def _get_reddit_access_token(self) -> Optional[str]:
        """Get Reddit API access token."""
        try:
            url = "https://www.reddit.com/api/v1/access_token"
            
            auth = aiohttp.BasicAuth(settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET)
            
            data = {
                'grant_type': 'client_credentials',
                'duration': 'temporary'
            }
            
            headers = {
                'User-Agent': settings.USER_AGENT
            }
            
            async with self.session.post(url, data=data, auth=auth, headers=headers) as response:
                if response.status == 200:
                    token_data = await response.json()
                    return token_data.get('access_token')
                else:
                    logger.error(f"Reddit auth failed: {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to get Reddit access token: {e}")
            return None
    
    def _process_twitter_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Twitter API response into standardized format."""
        results = []
        
        tweets = data.get('data', [])
        users = {user['id']: user for user in data.get('includes', {}).get('users', [])}
        
        for tweet in tweets:
            user_id = tweet.get('author_id')
            user = users.get(user_id, {})
            
            result = {
                'id': tweet.get('id'),
                'platform': 'twitter',
                'content': tweet.get('text', ''),
                'author': {
                    'id': user_id,
                    'username': user.get('username', ''),
                    'name': user.get('name', ''),
                    'verified': user.get('verified', False),
                    'followers': user.get('public_metrics', {}).get('followers_count', 0),
                    'following': user.get('public_metrics', {}).get('following_count', 0)
                },
                'metrics': {
                    'likes': tweet.get('public_metrics', {}).get('like_count', 0),
                    'retweets': tweet.get('public_metrics', {}).get('retweet_count', 0),
                    'replies': tweet.get('public_metrics', {}).get('reply_count', 0),
                    'quotes': tweet.get('public_metrics', {}).get('quote_count', 0)
                },
                'created_at': tweet.get('created_at', ''),
                'language': tweet.get('lang', ''),
                'url': f"https://twitter.com/{user.get('username', 'user')}/status/{tweet.get('id')}",
                'source': 'twitter_api_v2',
                'collected_at': datetime.utcnow().isoformat()
            }
            
            # Calculate engagement score
            result['engagement_score'] = self._calculate_twitter_engagement(result)
            
            results.append(result)
        
        return results
    
    def _process_reddit_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Reddit API response into standardized format."""
        results = []
        
        posts = data.get('data', {}).get('children', [])
        
        for post_data in posts:
            post = post_data.get('data', {})
            
            result = {
                'id': post.get('id'),
                'platform': 'reddit',
                'title': post.get('title', ''),
                'content': post.get('selftext', ''),
                'author': {
                    'id': post.get('author', ''),
                    'username': post.get('author', ''),
                    'name': post.get('author', ''),
                    'verified': False,  # Reddit doesn't have verification in the same way
                    'karma': post.get('author_fullname', '').replace('t2_', '') if post.get('author_fullname') else '0'
                },
                'metrics': {
                    'score': post.get('score', 0),
                    'upvotes': post.get('ups', 0),
                    'downvotes': post.get('downs', 0),
                    'comments': post.get('num_comments', 0),
                    'ratio': post.get('upvote_ratio', 0.0)
                },
                'subreddit': post.get('subreddit', ''),
                'created_at': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                'url': f"https://reddit.com{post.get('permalink', '')}",
                'external_url': post.get('url', ''),
                'source': 'reddit_api',
                'collected_at': datetime.utcnow().isoformat()
            }
            
            # Calculate engagement score
            result['engagement_score'] = self._calculate_reddit_engagement(result)
            
            results.append(result)
        
        return results
    
    def _calculate_twitter_engagement(self, tweet: Dict[str, Any]) -> float:
        """Calculate engagement score for a tweet."""
        metrics = tweet.get('metrics', {})
        author = tweet.get('author', {})
        
        # Base engagement
        likes = metrics.get('likes', 0)
        retweets = metrics.get('retweets', 0)
        replies = metrics.get('replies', 0)
        quotes = metrics.get('quotes', 0)
        
        # Weight different engagement types
        engagement = (likes * 1.0) + (retweets * 3.0) + (replies * 2.0) + (quotes * 2.5)
        
        # Normalize by author's follower count (to reduce bias toward accounts with huge followings)
        followers = max(1, author.get('followers', 1))
        normalized_engagement = engagement / (followers ** 0.5)  # Square root normalization
        
        # Scale to 0-10
        return min(10.0, normalized_engagement * 100)
    
    def _calculate_reddit_engagement(self, post: Dict[str, Any]) -> float:
        """Calculate engagement score for a Reddit post."""
        metrics = post.get('metrics', {})
        
        # Base engagement
        score = metrics.get('score', 0)
        comments = metrics.get('comments', 0)
        ratio = metrics.get('ratio', 0.0)
        
        # Weight different engagement types
        engagement = (score * 1.0) + (comments * 2.0)
        
        # Bonus for high upvote ratio
        if ratio > 0.9:
            engagement *= 1.5
        
        # Scale to 0-10
        return min(10.0, engagement / 100)
    
    async def search_all_platforms(self, query: str, max_results: int = 10, time_range: str = "7d") -> Dict[str, List[Dict[str, Any]]]:
        """
        Search across all configured social media platforms.
        
        Args:
            query: Search query
            max_results: Maximum results per platform
            time_range: Time range for search
            
        Returns:
            Dictionary with platform names as keys and result lists as values
        """
        results = {}
        
        # Search Twitter
        if settings.TWITTER_BEARER_TOKEN:
            results['twitter'] = await self.search_twitter(query, max_results, time_range)
        else:
            logger.info("Twitter API not configured, skipping")
            results['twitter'] = []
        
        # Search Reddit
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            results['reddit'] = await self.search_reddit(query, max_results, time_range)
        else:
            logger.info("Reddit API not configured, skipping")
            results['reddit'] = []
        
        return results


async def perform_social_media_search(
    query: str, 
    platforms: List[str] = None,
    max_results: int = 10,
    time_range: str = "7d",
    **kwargs
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Convenience function for social media search.
    
    Args:
        query: Search query
        platforms: List of platforms to search (twitter, reddit)
        max_results: Maximum results per platform
        time_range: Time range for search
        **kwargs: Additional parameters
        
    Returns:
        Dictionary with platform names as keys and result lists as values
    """
    async with SocialMediaService() as social_service:
        if platforms and len(platforms) == 1:
            # Single platform search
            platform = platforms[0]
            if platform == 'twitter':
                return {'twitter': await social_service.search_twitter(query, max_results, time_range)}
            elif platform == 'reddit':
                subreddits = kwargs.get('subreddits')
                return {'reddit': await social_service.search_reddit(query, max_results, time_range, subreddits)}
        else:
            # Multi-platform search
            return await social_service.search_all_platforms(query, max_results, time_range)