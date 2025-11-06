"""
Real Social Media Integration Service
Provides actual social media data collection using APIs and web scraping.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, List, Any, Optional
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta
import re

from app.config import settings

logger = logging.getLogger(__name__)

class RealSocialMediaService:
    """
    Service for performing actual social media data collection.
    """
    
    def __init__(self):
        self.session = None
        self.rate_limiters = {
            'twitter': {'last_request': 0, 'min_delay': 2.0},
            'reddit': {'last_request': 0, 'min_delay': 1.0},
            'instagram': {'last_request': 0, 'min_delay': 3.0},
            'linkedin': {'last_request': 0, 'min_delay': 2.0},
            'facebook': {'last_request': 0, 'min_delay': 2.0}
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
    
    async def search_twitter_profile(self, username: str) -> Dict[str, Any]:
        """
        Search for Twitter profile data using web scraping.
        
        Args:
            username: Twitter username to search for
            
        Returns:
            Dictionary containing Twitter profile information
        """
        await self._rate_limit('twitter')
        
        try:
            # Use Twitter's web interface for scraping
            url = f"https://twitter.com/{username}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self._parse_twitter_profile(html, username)
                else:
                    logger.error(f"Twitter profile not found: {response.status}")
                    return {"error": f"Profile not found (status: {response.status})", "username": username}
                    
        except Exception as e:
            logger.error(f"Error fetching Twitter profile for {username}: {e}")
            return {"error": str(e), "username": username}
    
    async def _parse_twitter_profile(self, html: str, username: str) -> Dict[str, Any]:
        """Parse Twitter profile HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract profile data using CSS selectors and patterns
            profile_data = {
                "username": username,
                "platform": "twitter",
                "profile_found": True,
                "data_source": "web_scraping"
            }
            
            # Extract display name
            name_tag = soup.find('h1') or soup.find('span', {'data-testid': 'UserName'})
            if name_tag:
                profile_data["display_name"] = name_tag.get_text().strip()
            
            # Extract bio
            bio_tag = soup.find('div', {'data-testid': 'UserDescription'})
            if bio_tag:
                profile_data["bio"] = bio_tag.get_text().strip()
            
            # Extract follower counts (using regex patterns)
            followers_match = re.search(r'([\d,]+)\s*Followers', html)
            if followers_match:
                profile_data["followers_count"] = int(followers_match.group(1).replace(',', ''))
            
            following_match = re.search(r'([\d,]+)\s*Following', html)
            if following_match:
                profile_data["following_count"] = int(following_match.group(1).replace(',', ''))
            
            # Extract location
            location_match = re.search(r'([\w\s,]+)\s*·', html)
            if location_match:
                profile_data["location"] = location_match.group(1).strip()
            
            # Extract website URL
            website_tag = soup.find('a', {'data-testid': 'UserUrl'})
            if website_tag and website_tag.get('href'):
                profile_data["website"] = website_tag.get('href')
            
            # Extract profile image
            img_tag = soup.find('img', {'data-testid': 'UserAvatar-Container-' + username})
            if img_tag and img_tag.get('src'):
                profile_data["profile_image"] = img_tag.get('src')
            
            profile_data["scraped_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Successfully scraped Twitter profile for {username}")
            return profile_data
            
        except ImportError:
            logger.warning("BeautifulSoup not available for Twitter parsing")
            return {"error": "Parsing library not available", "username": username}
        except Exception as e:
            logger.error(f"Failed to parse Twitter profile: {e}")
            return {"error": f"Parsing failed: {str(e)}", "username": username}
    
    async def search_reddit_user(self, username: str) -> Dict[str, Any]:
        """
        Search for Reddit user data using web scraping.
        
        Args:
            username: Reddit username to search for
            
        Returns:
            Dictionary containing Reddit user information
        """
        await self._rate_limit('reddit')
        
        try:
            # Use Reddit's user profile page
            url = f"https://www.reddit.com/user/{username}/"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self._parse_reddit_profile(html, username)
                else:
                    logger.error(f"Reddit user not found: {response.status}")
                    return {"error": f"User not found (status: {response.status})", "username": username}
                    
        except Exception as e:
            logger.error(f"Error fetching Reddit user {username}: {e}")
            return {"error": str(e), "username": username}
    
    async def _parse_reddit_profile(self, html: str, username: str) -> Dict[str, Any]:
        """Parse Reddit profile HTML."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            profile_data = {
                "username": username,
                "platform": "reddit",
                "profile_found": True,
                "data_source": "web_scraping"
            }
            
            # Extract karma using regex
            karma_match = re.search(r'([\d,]+)\s*karma', html, re.IGNORECASE)
            if karma_match:
                profile_data["karma"] = int(karma_match.group(1).replace(',', ''))
            
            # Extract cake day
            cake_day_match = re.search(r'(\w+\s+\d{1,2},\s+\d{4})', html)
            if cake_day_match:
                profile_data["cake_day"] = cake_day_match.group(1)
            
            # Extract post/comment karma breakdown
            post_karma_match = re.search(r'([\d,]+)\s*Post Karma', html)
            if post_karma_match:
                profile_data["post_karma"] = int(post_karma_match.group(1).replace(',', ''))
            
            comment_karma_match = re.search(r'([\d,]+)\s*Comment Karma', html)
            if comment_karma_match:
                profile_data["comment_karma"] = int(comment_karma_match.group(1).replace(',', ''))
            
            profile_data["scraped_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Successfully scraped Reddit profile for {username}")
            return profile_data
            
        except Exception as e:
            logger.error(f"Failed to parse Reddit profile: {e}")
            return {"error": f"Parsing failed: {str(e)}", "username": username}
    
    async def search_social_media_posts(self, query: str, platform: str = "twitter", max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for social media posts containing specific keywords.
        
        Args:
            query: Search query/keyword
            platform: Social media platform
            max_results: Maximum number of results
            
        Returns:
            List of posts containing the keyword
        """
        await self._rate_limit(platform)
        
        try:
            if platform == "twitter":
                return await self._search_twitter_posts(query, max_results)
            elif platform == "reddit":
                return await self._search_reddit_posts(query, max_results)
            else:
                logger.warning(f"Platform {platform} not yet implemented for post search")
                return []
                
        except Exception as e:
            logger.error(f"Error searching {platform} posts for '{query}': {e}")
            return []
    
    async def _search_twitter_posts(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Twitter posts using web scraping."""
        try:
            # Shorten the query to avoid header length issues
            shortened_query = query[:100] if len(query) > 100 else query
            
            # Use Twitter search URL with shortened query
            url = "https://twitter.com/search"
            params = {
                'q': shortened_query,
                'f': 'live',
                'lang': 'en'
            }
            
            # Use minimal headers to avoid header length issues
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            async with self.session.get(url, params=params, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self._parse_twitter_search_results(html, shortened_query, max_results)
                else:
                    logger.error(f"Twitter search error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Twitter search error: {e}")
            return []
    
    async def _parse_twitter_search_results(self, html: str, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse Twitter search results."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            posts = []
            tweet_elements = soup.find_all('article', {'data-testid': 'tweet'})[:max_results]
            
            for i, tweet in enumerate(tweet_elements):
                post_data = {
                    "platform": "twitter",
                    "query": query,
                    "position": i + 1,
                    "data_source": "web_scraping"
                }
                
                # Extract author
                author_tag = tweet.find('span', {'data-testid': 'User-Name'})
                if author_tag:
                    post_data["author"] = author_tag.get_text().strip()
                
                # Extract content
                content_tag = tweet.find('div', {'data-testid': 'tweetText'})
                if content_tag:
                    post_data["content"] = content_tag.get_text().strip()
                
                # Extract engagement metrics
                likes_match = re.search(r'([\d,]+)\s*Likes', tweet.get_text())
                if likes_match:
                    post_data["likes"] = int(likes_match.group(1).replace(',', ''))
                
                shares_match = re.search(r'([\d,]+)\s*Retweets', tweet.get_text())
                if shares_match:
                    post_data["shares"] = int(shares_match.group(1).replace(',', ''))
                
                # Extract timestamp
                time_tag = tweet.find('time')
                if time_tag and time_tag.get('datetime'):
                    post_data["timestamp"] = time_tag.get('datetime')
                
                post_data["scraped_at"] = datetime.utcnow().isoformat()
                posts.append(post_data)
            
            logger.info(f"Found {len(posts)} Twitter posts for query: {query}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to parse Twitter search results: {e}")
            return []
    
    async def _search_reddit_posts(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Search Reddit posts using web scraping."""
        try:
            # Use Reddit search URL
            url = "https://www.reddit.com/search"
            params = {
                'q': query,
                'type': 'link',
                'sort': 'relevance',
                't': 'all'
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self._parse_reddit_search_results(html, query, max_results)
                else:
                    logger.error(f"Reddit search failed: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Reddit search error: {e}")
            return []
    
    async def _parse_reddit_search_results(self, html: str, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Parse Reddit search results."""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            
            posts = []
            post_elements = soup.find_all('div', {'data-testid': 'post-container'})[:max_results]
            
            for i, post in enumerate(post_elements):
                post_data = {
                    "platform": "reddit",
                    "query": query,
                    "position": i + 1,
                    "data_source": "web_scraping"
                }
                
                # Extract title
                title_tag = post.find('h3')
                if title_tag:
                    post_data["title"] = title_tag.get_text().strip()
                
                # Extract subreddit
                subreddit_tag = post.find('a', {'data-testid': 'subreddit-link'})
                if subreddit_tag:
                    post_data["subreddit"] = subreddit_tag.get_text().strip()
                
                # Extract author
                author_tag = post.find('span', {'data-testid': 'post-author'})
                if author_tag:
                    post_data["author"] = author_tag.get_text().strip()
                
                # Extract score
                score_tag = post.find('div', {'data-testid': 'post-score'})
                if score_tag:
                    score_text = score_tag.get_text().strip()
                    if score_text.isdigit():
                        post_data["score"] = int(score_text)
                
                # Extract comments count
                comments_match = re.search(r'([\d,]+)\s*Comments', post.get_text())
                if comments_match:
                    post_data["comments"] = int(comments_match.group(1).replace(',', ''))
                
                post_data["scraped_at"] = datetime.utcnow().isoformat()
                posts.append(post_data)
            
            logger.info(f"Found {len(posts)} Reddit posts for query: {query}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to parse Reddit search results: {e}")
            return []
    
    async def analyze_social_media_network(self, username: str, platform: str) -> Dict[str, Any]:
        """
        Analyze social media network connections.
        
        Args:
            username: Username to analyze
            platform: Social media platform
            
        Returns:
            Dictionary containing network analysis
        """
        # This is a simplified implementation - real network analysis would require
        # more sophisticated scraping and potentially API access
        try:
            if platform == "twitter":
                profile_data = await self.search_twitter_profile(username)
                if "error" not in profile_data:
                    # Extract network insights from profile data
                    network_analysis = {
                        "username": username,
                        "platform": platform,
                        "followers_count": profile_data.get("followers_count", 0),
                        "following_count": profile_data.get("following_count", 0),
                        "follower_following_ratio": (
                            profile_data.get("followers_count", 1) / max(profile_data.get("following_count", 1), 1)
                        ),
                        "influence_score": min(profile_data.get("followers_count", 0) / 1000, 100),
                        "data_source": "profile_analysis"
                    }
                    return network_analysis
            
            return {"error": f"Network analysis not implemented for {platform}", "username": username}
            
        except Exception as e:
            logger.error(f"Error in network analysis for {username} on {platform}: {e}")
            return {"error": str(e), "username": username, "platform": platform}


async def perform_social_media_search(platform: str, search_type: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to perform social media searches.
    
    Args:
        platform: Social media platform (twitter, reddit, etc.)
        search_type: Type of search (profile, posts, network)
        **kwargs: Additional search parameters
        
    Returns:
        Dictionary containing search results
    """
    async with RealSocialMediaService() as social_service:
        if search_type == "profile":
            username = kwargs.get("username")
            if not username:
                return {"error": "Username required for profile search"}
            
            if platform == "twitter":
                return await social_service.search_twitter_profile(username)
            elif platform == "reddit":
                return await social_service.search_reddit_user(username)
            else:
                return {"error": f"Profile search not implemented for {platform}"}
        
        elif search_type == "posts":
            query = kwargs.get("query")
            if not query:
                return {"error": "Query required for post search"}
            
            max_results = kwargs.get("max_results", 20)
            posts = await social_service.search_social_media_posts(query, platform, max_results)
            return {
                "platform": platform,
                "query": query,
                "posts": posts,
                "total_results": len(posts)
            }
        
        elif search_type == "network":
            username = kwargs.get("username")
            if not username:
                return {"error": "Username required for network analysis"}
            
            return await social_service.analyze_social_media_network(username, platform)
        
        else:
            return {"error": f"Search type '{search_type}' not supported"}