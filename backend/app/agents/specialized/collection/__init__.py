"""
Collection phase agents for OSINT investigations.
"""

# Only import agents that work without external dependencies
from .url_discovery_agent import URLDiscoveryAgent

# Temporarily disabled due to missing dependencies
# from .surface_web_collector import SurfaceWebCollectorAgent
# from .social_media_collector import SocialMediaCollectorAgent
# from .public_records_collector import PublicRecordsCollectorAgent
# from .dark_web_collector import DarkWebCollectorAgent

__all__ = [
    "URLDiscoveryAgent"
]