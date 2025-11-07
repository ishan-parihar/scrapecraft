"""
Configuration Validator for ScrapeCraft OSINT Platform
Validates required API configurations on startup.
"""

from pydantic import BaseModel, field_validator
from typing import List, Dict, Any, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

class APIConfigurationValidator(BaseModel):
    """Validates required API configurations."""
    
    OPENROUTER_API_KEY: str
    GOOGLE_SEARCH_API_KEY: Optional[str] = None
    GOOGLE_SEARCH_ENGINE_ID: Optional[str] = None
    BING_SEARCH_API_KEY: Optional[str] = None
    DUCKDUCKGO_ENABLED: bool = True
    
    @field_validator('OPENROUTER_API_KEY')
    @classmethod
    def validate_openrouter_api(cls, v):
        if not v or len(v) < 10:
            raise ValueError("OpenRouter API key is required and must be valid")
        if not v.startswith('sk-or-') and not v.startswith('sk-'):
            logger.warning("OpenRouter API key should start with 'sk-or-' or 'sk-'")
        return v
    
    @field_validator('DUCKDUCKGO_ENABLED')
    @classmethod
    def validate_duckduckgo(cls, v):
        # DuckDuckGo should always be enabled as fallback
        return True if v is None else v

class CriticalConfigurationValidator(BaseModel):
    """Validates critical configurations that must be present."""
    
    openrouter_key: str
    duckduckgo_enabled: bool = True
    
    @field_validator('openrouter_key')
    @classmethod
    def validate_openrouter_critical(cls, v):
        if not v or len(v) < 10:
            raise ValueError("OpenRouter API key is critical for OSINT functionality")
        return v

def validate_configuration() -> Dict[str, Any]:
    """
    Validate all required configurations on startup.
    
    Returns:
        Dictionary with validation results
    """
    validation_result = {
        "status": "success",
        "errors": [],
        "warnings": [],
        "configured_services": [],
        "missing_services": []
    }
    
    try:
        # Check critical configurations
        try:
            critical_config = CriticalConfigurationValidator(
                openrouter_key=settings.OPENROUTER_API_KEY,
                duckduckgo_enabled=settings.DUCKDUCKGO_ENABLED
            )
            validation_result["configured_services"].append("openrouter")
            logger.info("OpenRouter API key validated")
        except Exception as e:
            validation_result["status"] = "error"
            validation_result["errors"].append(f"Critical configuration error: {e}")
            logger.error(f"Critical configuration validation failed: {e}")
        
        # Check optional search configurations
        if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_SEARCH_ENGINE_ID:
            validation_result["configured_services"].append("google_search")
            logger.info("Google Search API configured")
        else:
            validation_result["missing_services"].append("google_search")
            validation_result["warnings"].append("Google Search API not configured - will use DuckDuckGo fallback")
        
        if settings.BING_SEARCH_API_KEY:
            validation_result["configured_services"].append("bing_search")
            logger.info("Bing Search API configured")
        else:
            validation_result["missing_services"].append("bing_search")
            validation_result["warnings"].append("Bing Search API not configured - will use DuckDuckGo fallback")
        
        # DuckDuckGo is always available as fallback
        if settings.DUCKDUCKGO_ENABLED:
            validation_result["configured_services"].append("duckduckgo_search")
            logger.info("DuckDuckGo search enabled")
        
        # Check social media configurations (optional)
        if settings.TWITTER_BEARER_TOKEN:
            validation_result["configured_services"].append("twitter_api")
        else:
            validation_result["missing_services"].append("twitter_api")
        
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            validation_result["configured_services"].append("reddit_api")
        else:
            validation_result["missing_services"].append("reddit_api")
        
        # Check scraping configuration
        if settings.ENABLE_REAL_SCRAPING:
            validation_result["configured_services"].append("web_scraping")
            logger.info("Real web scraping enabled")
        
        # Log summary
        if validation_result["status"] == "success":
            logger.info(f"Configuration validation passed. Configured services: {validation_result['configured_services']}")
            if validation_result["warnings"]:
                logger.warning(f"Configuration warnings: {validation_result['warnings']}")
        else:
            logger.error(f"Configuration validation failed: {validation_result['errors']}")
        
        return validation_result
        
    except Exception as e:
        error_msg = f"Configuration validation failed with exception: {e}"
        logger.error(error_msg)
        validation_result["status"] = "error"
        validation_result["errors"].append(error_msg)
        return validation_result

def validate_production_mode() -> Dict[str, Any]:
    """
    Validate configurations for production mode.
    
    Returns:
        Dictionary with production validation results
    """
    validation_result = {
        "status": "success",
        "errors": [],
        "warnings": [],
        "production_ready": False
    }
    
    # In production mode, we should have at least one working search service
    search_services = 0
    if settings.GOOGLE_SEARCH_API_KEY and settings.GOOGLE_SEARCH_ENGINE_ID:
        search_services += 1
    if settings.BING_SEARCH_API_KEY:
        search_services += 1
    if settings.DUCKDUCKGO_ENABLED:
        search_services += 1
    
    if search_services == 0:
        validation_result["status"] = "error"
        validation_result["errors"].append("No search services configured")
    elif search_services == 1 and settings.DUCKDUCKGO_ENABLED:
        validation_result["warnings"].append("Only DuckDuckGo configured - consider adding API-based search for reliability")
    
    # Check for secure JWT secret
    if settings.JWT_SECRET == "default-secret-change-in-production":
        validation_result["warnings"].append("Using default JWT secret - change in production")
    
    # Check database configuration
    if settings.DATABASE_URL.startswith("sqlite"):
        validation_result["warnings"].append("Using SQLite in production - consider PostgreSQL")
    
    validation_result["production_ready"] = (
        validation_result["status"] == "success" and 
        len(validation_result["errors"]) == 0 and
        search_services > 0
    )
    
    return validation_result

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass

def ensure_configuration():
    """
    Ensure configuration is valid, raise exception if not.
    
    Raises:
        ConfigurationError: If configuration is invalid
    """
    result = validate_configuration()
    if result["status"] == "error":
        raise ConfigurationError(f"Invalid configuration: {'; '.join(result['errors'])}")
    return result