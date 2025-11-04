from pydantic_settings import BaseSettings
from typing import Optional, Literal

class Settings(BaseSettings):
    # API Keys
    OPENROUTER_API_KEY: str
    # Make SCRAPEGRAPH_API_KEY optional for local usage
    SCRAPEGRAPH_API_KEY: Optional[str] = None
    
    # Local scraping flag
    USE_LOCAL_SCRAPING: bool = False
    
    # Database
    DATABASE_URL: str
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:80"]
    
    # OpenRouter Config
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
    
    # LLM Settings
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4-turbo"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4000
    
    # ScrapeGraphAI Settings
    SCRAPEGRAPH_LOCAL_MODE: bool = True
    SCRAPEGRAPH_REASONING_ENABLED: bool = True
    SCRAPEGRAPH_MAX_DEPTH: int = 3
    SCRAPEGRAPH_ENGINE: str = "smart_scraper"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
