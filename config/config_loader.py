#!/usr/bin/env python3
"""
Configuration Loader for ScrapeCraft OSINT Platform
Handles environment-specific configuration loading and validation
"""

import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Environment(Enum):
    """Supported deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str
    pool_size: int
    max_overflow: int
    statement_timeout: Optional[int] = None
    query_timeout: Optional[int] = None

@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str
    pool_size: int
    sentinel_enabled: bool = False
    sentinel_service: Optional[str] = None

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: Optional[int] = None
    cors_origins: str = ""
    enable_csrf_protection: bool = False

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enable_metrics: bool
    metrics_port: int
    health_check_interval: int
    sentry_dsn: Optional[str] = None
    enable_apm: bool = False
    apm_service_name: Optional[str] = None

@dataclass
class AppConfig:
    """Complete application configuration"""
    environment: Environment
    backend_host: str
    backend_port: int
    backend_workers: int
    reload: bool
    
    # Frontend
    react_app_api_url: str
    react_app_ws_url: str
    react_app_environment: str
    
    # Components
    database: DatabaseConfig
    redis: RedisConfig
    security: SecurityConfig
    monitoring: MonitoringConfig
    
    # Feature flags
    enable_debug_mode: bool
    enable_sql_debug: bool
    enable_cors_debug: bool
    enable_websocket_debug: bool
    
    # External services
    mock_external_apis: bool
    enable_rate_limiting: bool
    rate_limit_requests: int
    rate_limit_window: int
    
    # Performance
    max_memory_usage: str
    max_cpu_usage: str
    enable_cache: bool
    cache_ttl: int
    enable_compression: bool
    
    # SSL/TLS
    force_https: bool
    ssl_verify: bool
    tls_version: Optional[str] = None
    enable_hsts: bool = False
    
    # External API keys
    shodan_api_key: Optional[str] = None
    virustotal_api_key: Optional[str] = None
    abuseipdb_api_key: Optional[str] = None

class ConfigurationError(Exception):
    """Configuration-related errors"""
    pass

class ConfigLoader:
    """Loads and validates configuration for different environments"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize config loader"""
        if config_dir is None:
            # Default to config/environments directory
            config_dir = Path(__file__).parent / "environments"
        
        self.config_dir = Path(config_dir)
        self.environment = self._detect_environment()
        self.config = self._load_config()
        
    def _detect_environment(self) -> Environment:
        """Detect current environment from NODE_ENV or default to development"""
        node_env = os.getenv("NODE_ENV", "development").lower()
        
        try:
            return Environment(node_env)
        except ValueError:
            logger.warning(f"Unknown environment '{node_env}', defaulting to development")
            return Environment.DEVELOPMENT
    
    def _load_config(self) -> AppConfig:
        """Load configuration for the current environment"""
        config_file = self.config_dir / f"{self.environment.value}.yaml"
        
        if not config_file.exists():
            raise ConfigurationError(f"Configuration file not found: {config_file}")
        
        logger.info(f"Loading configuration for environment: {self.environment.value}")
        
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML config: {e}")
        
        # Process environment variable substitution
        config_data = self._substitute_env_vars(config_data)
        
        # Validate configuration
        self._validate_config(config_data)
        
        # Create configuration objects
        return self._create_app_config(config_data)
    
    def _substitute_env_vars(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute environment variables in configuration values"""
        def substitute_recursive(obj):
            if isinstance(obj, dict):
                return {k: substitute_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute_recursive(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                default_value = None
                
                if ":" in env_var:
                    env_var, default_value = env_var.split(":", 1)
                
                return os.getenv(env_var, default_value)
            else:
                return obj
        
        return substitute_recursive(config_data)  # type: ignore
    
    def _validate_config(self, config_data: Dict[str, Any]) -> None:
        """Validate configuration data"""
        required_fields = [
            "BACKEND_HOST",
            "BACKEND_PORT",
            "DATABASE_URL",
            "REDIS_URL",
            "SECRET_KEY"
        ]
        
        missing_fields = []
        for field in required_fields:
            if field not in config_data or not config_data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ConfigurationError(f"Missing required configuration fields: {missing_fields}")
        
        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            production_required = [
                "PRODUCTION_SECRET_KEY",
                "PRODUCTION_SENTRY_DSN"
            ]
            
            for field in production_required:
                if os.getenv(field) is None:
                    logger.warning(f"Production environment variable {field} not set")
        
        # Validate URLs
        if not config_data["DATABASE_URL"].startswith(("postgresql://", "sqlite://")):
            raise ConfigurationError("DATABASE_URL must start with postgresql:// or sqlite://")
        
        if not config_data["REDIS_URL"].startswith("redis://"):
            raise ConfigurationError("REDIS_URL must start with redis://")
    
    def _create_app_config(self, config_data: Dict[str, Any]) -> AppConfig:
        """Create AppConfig object from configuration data"""
        try:
            # Database configuration
            database = DatabaseConfig(
                url=config_data["DATABASE_URL"],
                pool_size=int(config_data.get("DATABASE_POOL_SIZE", "10")),
                max_overflow=int(config_data.get("DATABASE_MAX_OVERFLOW", "20")),
                statement_timeout=int(config_data.get("DATABASE_STATEMENT_TIMEOUT", "0")) or None,
                query_timeout=int(config_data.get("DATABASE_QUERY_TIMEOUT", "0")) or None
            )
            
            # Redis configuration
            redis = RedisConfig(
                url=config_data["REDIS_URL"],
                pool_size=int(config_data.get("REDIS_POOL_SIZE", "10")),
                sentinel_enabled=config_data.get("REDIS_SENTINEL_ENABLED", "false").lower() == "true",
                sentinel_service=config_data.get("REDIS_SENTINEL_SERVICE")
            )
            
            # Security configuration
            security = SecurityConfig(
                secret_key=config_data["SECRET_KEY"],
                algorithm=config_data.get("ALGORITHM", "HS256"),
                access_token_expire_minutes=int(config_data.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
                refresh_token_expire_days=int(config_data.get("REFRESH_TOKEN_EXPIRE_DAYS", "0")) or None,
                cors_origins=config_data.get("CORS_ORIGINS", ""),
                enable_csrf_protection=config_data.get("ENABLE_CSRF_PROTECTION", "false").lower() == "true"
            )
            
            # Monitoring configuration
            monitoring = MonitoringConfig(
                enable_metrics=config_data.get("ENABLE_METRICS", "true").lower() == "true",
                metrics_port=int(config_data.get("METRICS_PORT", "9090")),
                health_check_interval=int(config_data.get("HEALTH_CHECK_INTERVAL", "30")),
                sentry_dsn=config_data.get("SENTRY_DSN"),
                enable_apm=config_data.get("ENABLE_APM", "false").lower() == "true",
                apm_service_name=config_data.get("APM_SERVICE_NAME")
            )
            
            return AppConfig(
                environment=self.environment,
                backend_host=config_data["BACKEND_HOST"],
                backend_port=int(config_data["BACKEND_PORT"]),
                backend_workers=int(config_data.get("BACKEND_WORKERS", "1")),
                reload=config_data.get("RELOAD", "false").lower() == "true",
                
                react_app_api_url=config_data.get("REACT_APP_API_URL", ""),
                react_app_ws_url=config_data.get("REACT_APP_WS_URL", ""),
                react_app_environment=config_data.get("REACT_APP_ENVIRONMENT", "development"),
                
                database=database,
                redis=redis,
                security=security,
                monitoring=monitoring,
                
                enable_debug_mode=config_data.get("ENABLE_DEBUG_MODE", "false").lower() == "true",
                enable_sql_debug=config_data.get("ENABLE_SQL_DEBUG", "false").lower() == "true",
                enable_cors_debug=config_data.get("ENABLE_CORS_DEBUG", "false").lower() == "true",
                enable_websocket_debug=config_data.get("ENABLE_WEBSOCKET_DEBUG", "false").lower() == "true",
                
                mock_external_apis=config_data.get("MOCK_EXTERNAL_APIS", "false").lower() == "true",
                enable_rate_limiting=config_data.get("ENABLE_RATE_LIMITING", "false").lower() == "true",
                rate_limit_requests=int(config_data.get("RATE_LIMIT_REQUESTS", "100")),
                rate_limit_window=int(config_data.get("RATE_LIMIT_WINDOW", "3600")),
                
                max_memory_usage=config_data.get("MAX_MEMORY_USAGE", "1Gi"),
                max_cpu_usage=config_data.get("MAX_CPU_USAGE", "500m"),
                enable_cache=config_data.get("ENABLE_CACHE", "true").lower() == "true",
                cache_ttl=int(config_data.get("CACHE_TTL", "300")),
                enable_compression=config_data.get("ENABLE_COMPRESSION", "true").lower() == "true",
                
                force_https=config_data.get("FORCE_HTTPS", "false").lower() == "true",
                ssl_verify=config_data.get("SSL_VERIFY", "true").lower() == "true",
                tls_version=config_data.get("TLS_VERSION"),
                enable_hsts=config_data.get("ENABLE_HSTS", "false").lower() == "true",
                
                shodan_api_key=config_data.get("SHODAN_API_KEY"),
                virustotal_api_key=config_data.get("VIRUSTOTAL_API_KEY"),
                abuseipdb_api_key=config_data.get("ABUSEIPDB_API_KEY")
            )
            
        except (KeyError, ValueError) as e:
            raise ConfigurationError(f"Error creating configuration: {e}")
    
    def get_config(self) -> AppConfig:
        """Get the loaded configuration"""
        return self.config
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get configuration as environment variables for containers"""
        config_dict = {}
        
        # Flatten configuration into environment variables
        for key, value in self.config.__dict__.items():
            if isinstance(value, (str, int, bool)):
                config_dict[key.upper()] = str(value)
            elif hasattr(value, '__dict__'):
                # Handle nested config objects
                for nested_key, nested_value in value.__dict__.items():
                    if isinstance(nested_value, (str, int, bool)):
                        config_dict[f"{key.upper()}_{nested_key.upper()}"] = str(nested_value)
        
        return config_dict

# Global configuration instance
_config_loader = None

def get_config() -> AppConfig:
    """Get global configuration instance"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.get_config()

def load_config(config_dir: Optional[Path] = None) -> AppConfig:
    """Load configuration from specified directory"""
    loader = ConfigLoader(config_dir)
    return loader.get_config()

if __name__ == "__main__":
    # Test configuration loading
    try:
        config = get_config()
        print(f"✅ Configuration loaded successfully for environment: {config.environment.value}")
        print(f"📊 Backend: {config.backend_host}:{config.backend_port}")
        print(f"🗄️  Database: {config.database.url}")
        print(f"🔴 Redis: {config.redis.url}")
        print(f"🔐 Security: {config.security.algorithm}")
        print(f"📈 Monitoring: {config.monitoring.enable_metrics}")
        
    except ConfigurationError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)