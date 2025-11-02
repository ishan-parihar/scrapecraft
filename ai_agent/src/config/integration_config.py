from typing import Dict, Any, Optional
from dataclasses import dataclass
import os

@dataclass
class IntegrationConfig:
    """
    Configuration for AI agent to backend scraping service integration
    """
    # Backend scraping service configuration
    backend_scraping_base_url: str = os.getenv("BACKEND_SCRAPING_URL", "http://localhost:8000")
    backend_api_key: Optional[str] = os.getenv("BACKEND_API_KEY")
    backend_timeout: int = int(os.getenv("BACKEND_TIMEOUT", "30"))
    
    # Feature flags
    use_backend_scraping: bool = os.getenv("USE_BACKEND_SCRAPING", "true").lower() == "true"
    fallback_to_local_scraping: bool = os.getenv("FALLBACK_TO_LOCAL", "true").lower() == "true"
    max_concurrent_tasks: int = int(os.getenv("MAX_CONCURRENT_BACKEND_TASKS", "5"))
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'IntegrationConfig':
        """Create config from dictionary"""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})