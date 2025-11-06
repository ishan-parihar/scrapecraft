import os
import logging
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.language_models.base import BaseLanguageModel
from pydantic import SecretStr
from app.config import settings

logger = logging.getLogger(__name__)

class LLMProviderError(Exception):
    """Custom exception for LLM provider configuration errors."""
    pass

def validate_llm_config() -> None:
    """Validate LLM configuration based on the selected provider."""
    provider = settings.LLM_PROVIDER.lower()
    
    if provider == "openrouter":
        if not settings.OPENROUTER_API_KEY:
            raise LLMProviderError(
                "OPENROUTER_API_KEY is required when using OpenRouter provider. "
                "Set the environment variable or change LLM_PROVIDER."
            )
    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise LLMProviderError(
                "OPENAI_API_KEY is required when using OpenAI provider. "
                "Set the environment variable or change LLM_PROVIDER."
            )
    elif provider == "custom":
        if not settings.CUSTOM_LLM_ENABLED:
            raise LLMProviderError(
                "CUSTOM_LLM_ENABLED must be True when using custom provider. "
                "Set CUSTOM_LLM_ENABLED=true or change LLM_PROVIDER."
            )
        if not settings.CUSTOM_LLM_BASE_URL:
            raise LLMProviderError(
                "CUSTOM_LLM_BASE_URL is required when using custom provider. "
                "Set the environment variable with your custom endpoint URL."
            )
        if not settings.CUSTOM_LLM_MODEL:
            raise LLMProviderError(
                "CUSTOM_LLM_MODEL is required when using custom provider. "
                "Set the environment variable with your model name."
            )
        
        # Additional validation for OpenAI-compatible providers
        if settings.CUSTOM_LLM_PROVIDER_TYPE == "openai-compatible":
            if not settings.CUSTOM_LLM_API_KEY:
                raise LLMProviderError(
                    "CUSTOM_LLM_API_KEY is required for OpenAI-compatible providers. "
                    "Set the environment variable with your API key."
                )
            
            # Validate base URL format
            if not settings.CUSTOM_LLM_BASE_URL.startswith(("http://", "https://")):
                raise LLMProviderError(
                    "CUSTOM_LLM_BASE_URL must start with http:// or https:// for OpenAI-compatible providers."
                )
        
        # Model-specific validation
        if "glm-4.6" in settings.CUSTOM_LLM_MODEL.lower():
            logger.info("Detected GLM-4.6 model configuration")
            if settings.CUSTOM_LLM_PROVIDER_TYPE != "openai-compatible":
                logger.warning(
                    f"GLM-4.6 model typically works best with 'openai-compatible' provider type, "
                    f"but current type is '{settings.CUSTOM_LLM_PROVIDER_TYPE}'"
                )
    else:
        raise LLMProviderError(
            f"Unknown LLM provider: {provider}. "
            "Supported providers: openrouter, openai, custom"
        )

def get_openrouter_llm() -> ChatOpenAI:
    """Get OpenRouter LLM instance with proper configuration."""
    logger.info(f"Initializing OpenRouter LLM with model: {settings.OPENROUTER_MODEL}")
    
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=SecretStr(settings.OPENROUTER_API_KEY) if settings.OPENROUTER_API_KEY else None,
        model=settings.OPENROUTER_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        streaming=True,
        default_headers={
            "HTTP-Referer": "https://scrapecraft.app",
            "X-Title": "ScrapeCraft"
        }
    )

def get_openai_llm() -> ChatOpenAI:
    """Get OpenAI LLM instance."""
    logger.info(f"Initializing OpenAI LLM with model: {settings.OPENAI_MODEL}")
    
    return ChatOpenAI(
        base_url=settings.OPENAI_BASE_URL,
        api_key=SecretStr(settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None,
        model=settings.OPENAI_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        streaming=True
    )

def get_custom_llm() -> ChatOpenAI:
    """Get custom OpenAI-compatible LLM instance."""
    logger.info(f"Initializing custom LLM with model: {settings.CUSTOM_LLM_MODEL}")
    logger.info(f"Custom LLM Base URL: {settings.CUSTOM_LLM_BASE_URL}")
    logger.info(f"Custom LLM Provider Type: {settings.CUSTOM_LLM_PROVIDER_TYPE}")
    
    # Custom headers for specific providers
    custom_headers = {}
    
    # Configure API key based on provider type
    if settings.CUSTOM_LLM_PROVIDER_TYPE == "ollama":
        # Ollama typically doesn't need an API key
        api_key = SecretStr(settings.CUSTOM_LLM_API_KEY) if settings.CUSTOM_LLM_API_KEY else SecretStr("ollama")
    elif settings.CUSTOM_LLM_PROVIDER_TYPE == "localai":
        # LocalAI might not need API keys
        api_key = SecretStr(settings.CUSTOM_LLM_API_KEY) if settings.CUSTOM_LLM_API_KEY else SecretStr("local")
    elif settings.CUSTOM_LLM_PROVIDER_TYPE == "openai-compatible":
        # OpenAI-compatible APIs usually need proper API key
        if not settings.CUSTOM_LLM_API_KEY:
            raise LLMProviderError(
                f"CUSTOM_LLM_API_KEY is required for OpenAI-compatible provider. "
                f"Current provider type: {settings.CUSTOM_LLM_PROVIDER_TYPE}"
            )
        api_key = SecretStr(settings.CUSTOM_LLM_API_KEY)
        
        # Add custom headers for specific OpenAI-compatible providers
        if "glm-4.6" in settings.CUSTOM_LLM_MODEL.lower():
            # Add any specific headers needed for GLM models
            custom_headers.update({
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
    else:
        api_key = SecretStr(settings.CUSTOM_LLM_API_KEY) if settings.CUSTOM_LLM_API_KEY else None
    
    # Configure temperature for the specific model
    temperature = settings.LLM_TEMPERATURE
    if settings.CUSTOM_LLM_TEMPERATURE is not None:
        temperature = settings.CUSTOM_LLM_TEMPERATURE
    elif "glm-4.6" in settings.CUSTOM_LLM_MODEL.lower():
        # GLM models often work well with slightly higher temperature
        temperature = max(temperature, 0.3)
    
    # Configure max tokens for the specific model
    max_tokens = settings.LLM_MAX_TOKENS
    if settings.CUSTOM_LLM_MAX_TOKENS is not None:
        max_tokens = settings.CUSTOM_LLM_MAX_TOKENS
    elif "glm-4.6" in settings.CUSTOM_LLM_MODEL.lower():
        # GLM-4.6 typically supports larger context windows
        max_tokens = min(max_tokens, 8192)
    
    llm_config = {
        "base_url": settings.CUSTOM_LLM_BASE_URL,
        "api_key": api_key,
        "model": settings.CUSTOM_LLM_MODEL,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "streaming": settings.CUSTOM_LLM_STREAMING,
        "timeout": settings.CUSTOM_LLM_TIMEOUT,
        "max_retries": settings.CUSTOM_LLM_MAX_RETRIES,
    }
    
    # Add custom headers if any
    if custom_headers:
        llm_config["default_headers"] = custom_headers
    
    # Add model-specific parameters
    if settings.CUSTOM_LLM_TOP_P is not None:
        llm_config["top_p"] = settings.CUSTOM_LLM_TOP_P
    if settings.CUSTOM_LLM_FREQUENCY_PENALTY is not None:
        llm_config["frequency_penalty"] = settings.CUSTOM_LLM_FREQUENCY_PENALTY
    if settings.CUSTOM_LLM_PRESENCE_PENALTY is not None:
        llm_config["presence_penalty"] = settings.CUSTOM_LLM_PRESENCE_PENALTY
    if settings.CUSTOM_LLM_SEED is not None:
        llm_config["seed"] = settings.CUSTOM_LLM_SEED
    
    # Configure SSL verification
    if not settings.CUSTOM_LLM_VERIFY_SSL:
        llm_config["http_client"] = None  # Will be configured below if needed
    
    logger.info(f"Custom LLM Configuration: {llm_config}")
    
    try:
        llm = ChatOpenAI(**llm_config)
        
        # Configure SSL if needed
        if not settings.CUSTOM_LLM_VERIFY_SSL:
            import httpx
            llm.http_client = httpx.Client(verify=False)
        
        return llm
        
    except Exception as e:
        logger.error(f"Failed to initialize custom LLM: {str(e)}")
        raise LLMProviderError(f"Failed to initialize custom LLM: {str(e)}")

def get_llm() -> BaseLanguageModel:
    """
    Get the appropriate LLM instance based on the LLM_PROVIDER setting.
    
    Returns:
        BaseLanguageModel: Configured LLM instance
        
    Raises:
        LLMProviderError: If configuration is invalid
        Exception: For other initialization errors
    """
    try:
        # Validate configuration first
        validate_llm_config()
        
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "openrouter":
            return get_openrouter_llm()
        elif provider == "openai":
            return get_openai_llm()
        elif provider == "custom":
            return get_custom_llm()
        else:
            raise LLMProviderError(f"Unsupported LLM provider: {provider}")
            
    except LLMProviderError:
        # Re-raise configuration errors
        raise
    except Exception as e:
        logger.error(f"Failed to initialize LLM provider '{settings.LLM_PROVIDER}': {str(e)}")
        raise LLMProviderError(
            f"Failed to initialize LLM provider '{settings.LLM_PROVIDER}': {str(e)}. "
            "Please check your configuration and network connectivity."
        )

def get_llm_with_fallback() -> BaseLanguageModel:
    """
    Get LLM instance with fallback to alternative providers if primary fails.
    This provides resilience for production deployments.
    
    Returns:
        BaseLanguageModel: Working LLM instance
        
    Raises:
        LLMProviderError: If all providers fail
    """
    primary_provider = settings.LLM_PROVIDER.lower()
    fallback_providers = ["openrouter", "openai", "custom"]
    
    # Try primary provider first
    try:
        return get_llm()
    except LLMProviderError as e:
        logger.warning(f"Primary LLM provider '{primary_provider}' failed: {str(e)}")
    
    # Try fallback providers by calling their direct functions
    fallback_functions = {
        "openrouter": get_openrouter_llm,
        "openai": get_openai_llm,
        "custom": get_custom_llm
    }
    
    for provider in fallback_providers:
        if provider == primary_provider:
            continue  # Skip the one that already failed
            
        try:
            logger.info(f"Trying fallback provider: {provider}")
            
            # Validate config for this provider
            temp_provider = settings.LLM_PROVIDER
            if provider == "openrouter" and settings.OPENROUTER_API_KEY:
                llm = get_openrouter_llm()
            elif provider == "openai" and settings.OPENAI_API_KEY:
                llm = get_openai_llm()
            elif provider == "custom" and settings.CUSTOM_LLM_ENABLED:
                llm = get_custom_llm()
            else:
                logger.warning(f"Skipping fallback provider '{provider}' - insufficient configuration")
                continue
            
            logger.info(f"Successfully initialized fallback provider: {provider}")
            return llm
        except Exception as e:
            logger.warning(f"Fallback provider '{provider}' also failed: {str(e)}")
            continue
    
    raise LLMProviderError(
        f"All LLM providers failed. Primary: {primary_provider}, "
        f"Tried fallbacks: {[p for p in fallback_providers if p != primary_provider]}"
    )

# Convenience functions for specific providers
def get_openrouter_llm_direct() -> ChatOpenAI:
    """Direct access to OpenRouter LLM (bypasses provider selection)."""
    return get_openrouter_llm()

def get_openai_llm_direct() -> ChatOpenAI:
    """Direct access to OpenAI LLM (bypasses provider selection)."""
    return get_openai_llm()

def get_custom_llm_direct() -> ChatOpenAI:
    """Direct access to custom LLM (bypasses provider selection)."""
    return get_custom_llm()

async def test_connection() -> dict:
    """
    Test connectivity to the configured LLM provider.
    
    Returns:
        dict: Health check result with status and details
    """
    from datetime import datetime
    
    try:
        # Validate configuration first
        validate_llm_config()
        
        # Get LLM instance
        llm = get_llm()
        
        # Test with a simple request
        try:
            # Simple test message
            test_response = await llm.ainvoke("Hello")
            
            return {
                "status": "healthy",
                "provider": settings.LLM_PROVIDER,
                "model": getattr(llm, 'model_name', getattr(llm, 'model', 'unknown')),
                "base_url": getattr(llm, 'base_url', 'default'),
                "timestamp": datetime.utcnow().isoformat(),
                "test_response": str(test_response)[:100] + "..." if len(str(test_response)) > 100 else str(test_response)
            }
            
        except Exception as api_error:
            logger.error(f"LLM API test failed: {api_error}")
            return {
                "status": "unhealthy",
                "provider": settings.LLM_PROVIDER,
                "error": f"API test failed: {str(api_error)}",
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except LLMProviderError as config_error:
        return {
            "status": "unhealthy",
            "provider": settings.LLM_PROVIDER,
            "error": f"Configuration error: {str(config_error)}",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "provider": settings.LLM_PROVIDER,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }