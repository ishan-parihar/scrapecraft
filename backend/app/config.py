from pydantic_settings import BaseSettings
from typing import Optional, Literal

class Settings(BaseSettings):
    # API Keys
    OPENROUTER_API_KEY: str = ""
    # Make SCRAPEGRAPH_API_KEY optional for local usage
    SCRAPEGRAPH_API_KEY: Optional[str] = None
    
    # Search Engine APIs
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""
    BING_SEARCH_API_KEY: str = ""
    DUCKDUCKGO_ENABLED: bool = True
    
    # Social Media APIs
    TWITTER_BEARER_TOKEN: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "ScrapeCraft/1.0"
    
    # Web Scraping
    ENABLE_REAL_SCRAPING: bool = True
    SCRAPE_DELAY_SECONDS: float = 1.0
    MAX_CONCURRENT_REQUESTS: int = 5
    USER_AGENT: str = "ScrapeCraft-OSINT/1.0 (Research Tool)"
    
    # Local scraping flag
    USE_LOCAL_SCRAPING: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./scrapecraft.db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security
    JWT_SECRET: str = "default-secret-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:80"]
    
    # LLM Provider Configuration
    LLM_PROVIDER: Literal["openrouter", "openai", "custom"] = "openrouter"
    
    # OpenRouter Configuration
    OPENROUTER_MODEL: str = "moonshotai/kimi-k2"
    
    # App Config
    APP_NAME: str = "ScrapeCraft"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # AI Agent Settings
    AI_AGENTS_ENABLED: bool = True
    OSINT_WORKFLOW_ENABLED: bool = True
    INVESTIGATION_TIMEOUT: int = 3600
    AGENT_MAX_RETRIES: int = 3
    AGENT_RETRY_DELAY: float = 1.0
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4-turbo"
    
    # Custom LLM Provider Configuration
    CUSTOM_LLM_ENABLED: bool = False
    CUSTOM_LLM_BASE_URL: str = "https://api.your-provider.com/v1"
    CUSTOM_LLM_API_KEY: str = ""
    CUSTOM_LLM_MODEL: str = "your-custom-model"
    
    # Custom LLM Provider Type Detection
    CUSTOM_LLM_PROVIDER_TYPE: Literal["ollama", "localai", "vllm", "openai-compatible", "custom"] = "openai-compatible"
    
    # Custom LLM Connection Settings
    CUSTOM_LLM_TIMEOUT: int = 120
    CUSTOM_LLM_MAX_RETRIES: int = 3
    CUSTOM_LLM_RETRY_DELAY: float = 1.0
    CUSTOM_LLM_CONNECTION_POOL_SIZE: int = 10
    CUSTOM_LLM_KEEP_ALIVE: bool = True
    
    # Custom LLM Performance Settings
    CUSTOM_LLM_TEMPERATURE: Optional[float] = None  # Inherits from LLM_TEMPERATURE if None
    CUSTOM_LLM_MAX_TOKENS: Optional[int] = None     # Inherits from LLM_MAX_TOKENS if None
    CUSTOM_LLM_TOP_P: Optional[float] = None        # Nucleus sampling (0.0 to 1.0)
    CUSTOM_LLM_FREQUENCY_PENALTY: Optional[float] = None  # -2.0 to 2.0
    CUSTOM_LLM_PRESENCE_PENALTY: Optional[float] = None   # -2.0 to 2.0
    CUSTOM_LLM_SEED: Optional[int] = None          # For reproducible outputs
    
    # Custom LLM Streaming Settings
    CUSTOM_LLM_STREAMING: bool = True
    CUSTOM_LLM_STREAM_BUFFER_SIZE: int = 1024
    CUSTOM_LLM_STREAM_TIMEOUT: int = 30
    
    # Custom LLM Model Validation
    CUSTOM_LLM_VALIDATE_MODEL: bool = True
    CUSTOM_LLM_AUTO_DISCOVER_MODELS: bool = False
    CUSTOM_LLM_MODEL_LIST_ENDPOINT: Optional[str] = None  # e.g., "/v1/models"
    CUSTOM_LLM_SUPPORTED_MODELS: list[str] = []  # Empty means allow any model
    
    # Custom LLM Security Settings
    CUSTOM_LLM_VERIFY_SSL: bool = True
    CUSTOM_LLM_ALLOW_SELF_SIGNED: bool = False
    CUSTOM_LLM_API_KEY_HEADER: str = "Authorization"  # Custom header name if needed
    CUSTOM_LLM_API_KEY_PREFIX: str = "Bearer "        # Custom prefix if needed
    
    # Custom LLM Caching Settings
    CUSTOM_LLM_ENABLE_CACHE: bool = False
    CUSTOM_LLM_CACHE_TTL: int = 3600  # seconds
    CUSTOM_LLM_CACHE_SIZE: int = 1000
    
    # Provider-Specific Settings
    # Ollama Settings
    OLLAMA_DEFAULT_MODEL: str = "llama3.2:instruct"
    OLLAMA_PULL_MODELS: bool = False
    OLLAMA_GPU_LAYERS: Optional[int] = None  # For GPU acceleration
    
    # LocalAI Settings
    LOCALAI_DEFAULT_MODEL: str = "ggml-gpt4all-j"
    LOCALAI_CONTEXT_SIZE: int = 2048
    LOCALAI_THREADS: int = 4
    
    # vLLM Settings
    VLLM_DEFAULT_MODEL: str = "your-model"
    VLLM_TENSOR_PARALLEL_SIZE: int = 1
    VLLM_MAX_MODEL_LENGTH: Optional[int] = None
    
    # LLM Settings
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4000
    
    # Custom LLM Advanced Features
    CUSTOM_LLM_ENABLE_FALLBACK: bool = False
    CUSTOM_LLM_FALLBACK_PROVIDERS: list[str] = []  # List of fallback base URLs
    CUSTOM_LLM_HEALTH_CHECK_INTERVAL: int = 300  # seconds
    CUSTOM_LLM_PERFORMANCE_MONITORING: bool = True
    
    # ScrapeGraphAI Settings
    SCRAPEGRAPH_LOCAL_MODE: bool = True
    SCRAPEGRAPH_REASONING_ENABLED: bool = True
    SCRAPEGRAPH_MAX_DEPTH: int = 3
    SCRAPEGRAPH_ENGINE: str = "smart_scraper"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra environment variables

settings = Settings()
