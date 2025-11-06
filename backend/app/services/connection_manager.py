"""
Enhanced Caching and Connection Pooling Service

This service provides:
- Redis-based caching with intelligent cache invalidation
- Database connection pooling with health monitoring
- HTTP client connection pooling
- Cache warming strategies
- Performance monitoring and metrics
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import pickle
from contextlib import asynccontextmanager
from functools import wraps

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import QueuePool
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    """Cache invalidation strategies."""
    TTL = "ttl"                    # Time-based expiration
    LRU = "lru"                    # Least recently used
    LFU = "lfu"                    # Least frequently used
    MANUAL = "manual"              # Manual invalidation

@dataclass
class CacheConfig:
    """Configuration for cache settings."""
    default_ttl: int = 3600  # 1 hour
    max_size: int = 10000    # Maximum number of cached items
    strategy: CacheStrategy = CacheStrategy.TTL
    compression_enabled: bool = True
    serialization_method: str = "json"  # json, pickle, msgpack

@dataclass
class ConnectionPoolConfig:
    """Configuration for connection pools."""
    db_pool_size: int = 20
    db_max_overflow: int = 30
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600
    
    http_pool_size: int = 100
    http_max_connections: int = 200
    http_timeout: float = 30.0

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    expires_at: Optional[datetime]
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    size_bytes: int = 0

class CacheManager:
    """Enhanced cache manager with multiple strategies."""
    
    def __init__(self, config: CacheConfig):
        self.config = config
        self.redis_client: Optional[redis.Redis] = None
        self.local_cache: Dict[str, CacheEntry] = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "evictions": 0
        }
        self._lock = asyncio.Lock()
    
    async def initialize(self, redis_url: Optional[str] = None):
        """Initialize cache manager with Redis connection."""
        try:
            if redis_url:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=False
                )
                # Test connection
                await self.redis_client.ping()
                logger.info("Cache manager initialized with Redis")
            else:
                logger.warning("Cache manager initialized without Redis (local cache only)")
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {e}")
            self.redis_client = None
    
    async def close(self):
        """Close cache manager connections."""
        if self.redis_client:
            await self.redis_client.close()
    
    def _generate_cache_key(self, prefix: str, key_parts: List[Any]) -> str:
        """Generate consistent cache key."""
        key_str = ":".join(str(part) for part in key_parts)
        full_key = f"{prefix}:{key_str}"
        
        # Hash long keys to avoid Redis key length limits
        if len(full_key) > 250:
            full_key = f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"
        
        return full_key
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        if self.config.serialization_method == "json":
            return json.dumps(value, default=str).encode('utf-8')
        elif self.config.serialization_method == "pickle":
            return pickle.dumps(value)
        else:
            raise ValueError(f"Unsupported serialization method: {self.config.serialization_method}")
    
    def _deserialize_value(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        if self.config.serialization_method == "json":
            return json.loads(data.decode('utf-8'))
        elif self.config.serialization_method == "pickle":
            return pickle.loads(data)
        else:
            raise ValueError(f"Unsupported serialization method: {self.config.serialization_method}")
    
    async def get(self, prefix: str, key_parts: List[Any]) -> Optional[Any]:
        """Get value from cache."""
        cache_key = self._generate_cache_key(prefix, key_parts)
        
        try:
            # Try Redis first
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    self.cache_stats["hits"] += 1
                    return self._deserialize_value(cached_data)
            
            # Fallback to local cache
            if cache_key in self.local_cache:
                entry = self.local_cache[cache_key]
                
                # Check expiration
                if entry.expires_at and datetime.utcnow() > entry.expires_at:
                    del self.local_cache[cache_key]
                    self.cache_stats["evictions"] += 1
                else:
                    # Update access stats
                    entry.access_count += 1
                    entry.last_accessed = datetime.utcnow()
                    self.cache_stats["hits"] += 1
                    return entry.value
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for key {cache_key}: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(
        self,
        prefix: str,
        key_parts: List[Any],
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        cache_key = self._generate_cache_key(prefix, key_parts)
        ttl = ttl or self.config.default_ttl
        
        try:
            # Serialize value
            serialized_value = self._serialize_value(value)
            size_bytes = len(serialized_value)
            
            # Set in Redis
            if self.redis_client:
                await self.redis_client.setex(cache_key, ttl, serialized_value)
            
            # Set in local cache
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
            entry = CacheEntry(
                key=cache_key,
                value=value,
                created_at=datetime.utcnow(),
                expires_at=expires_at,
                size_bytes=size_bytes,
                last_accessed=datetime.utcnow()
            )
            
            async with self._lock:
                self.local_cache[cache_key] = entry
                
                # Enforce cache size limit
                await self._enforce_size_limit()
            
            self.cache_stats["sets"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    async def delete(self, prefix: str, key_parts: List[Any]) -> bool:
        """Delete value from cache."""
        cache_key = self._generate_cache_key(prefix, key_parts)
        
        try:
            # Delete from Redis
            if self.redis_client:
                await self.redis_client.delete(cache_key)
            
            # Delete from local cache
            async with self._lock:
                if cache_key in self.local_cache:
                    del self.local_cache[cache_key]
            
            self.cache_stats["deletes"] += 1
            return True
            
        except Exception as e:
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    async def clear_prefix(self, prefix: str) -> int:
        """Clear all cache entries with given prefix."""
        try:
            deleted_count = 0
            
            # Clear from Redis
            if self.redis_client:
                pattern = f"{prefix}:*"
                keys = await self.redis_client.keys(pattern)
                if keys:
                    deleted_count += await self.redis_client.delete(*keys)
            
            # Clear from local cache
            async with self._lock:
                keys_to_delete = [
                    key for key in self.local_cache.keys()
                    if key.startswith(f"{prefix}:")
                ]
                for key in keys_to_delete:
                    del self.local_cache[key]
                    deleted_count += 1
            
            logger.info(f"Cleared {deleted_count} cache entries with prefix '{prefix}'")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache clear prefix error for '{prefix}': {e}")
            return 0
    
    async def _enforce_size_limit(self):
        """Enforce cache size limit based on strategy."""
        if len(self.local_cache) <= self.config.max_size:
            return
        
        if self.config.strategy == CacheStrategy.LRU:
            # Remove least recently used items
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: x[1].last_accessed or datetime.min
            )
            
            items_to_remove = len(self.local_cache) - self.config.max_size + 100  # Remove extra
            for key, _ in sorted_items[:items_to_remove]:
                del self.local_cache[key]
                self.cache_stats["evictions"] += 1
        
        elif self.config.strategy == CacheStrategy.LFU:
            # Remove least frequently used items
            sorted_items = sorted(
                self.local_cache.items(),
                key=lambda x: (x[1].access_count, x[1].last_accessed or datetime.min)
            )
            
            items_to_remove = len(self.local_cache) - self.config.max_size + 100
            for key, _ in sorted_items[:items_to_remove]:
                del self.local_cache[key]
                self.cache_stats["evictions"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = self.cache_stats["hits"] / max(1, total_requests)
        
        return {
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "local_cache_size": len(self.local_cache),
            "redis_connected": self.redis_client is not None,
            **self.cache_stats
        }

class DatabaseConnectionManager:
    """Enhanced database connection pool manager."""
    
    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.engine = None
        self.session_factory = None
        self.pool_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "pool_hits": 0,
            "pool_misses": 0
        }
    
    async def initialize(self, database_url: str):
        """Initialize database connection pool."""
        try:
            self.engine = create_async_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=self.config.db_pool_size,
                max_overflow=self.config.db_max_overflow,
                pool_timeout=self.config.db_pool_timeout,
                pool_recycle=self.config.db_pool_recycle,
                pool_pre_ping=True,  # Validate connections
                echo=False
            )
            
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info(f"Database connection pool initialized (size: {self.config.db_pool_size})")
            
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    async def close(self):
        """Close database connection pool."""
        if self.engine:
            await self.engine.dispose()
    
    @asynccontextmanager
    async def get_session(self) -> AsyncSession:
        """Get database session from pool."""
        if not self.session_factory:
            raise RuntimeError("Database pool not initialized")
        
        session = self.session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """Check database pool health."""
        if not self.engine:
            return {"status": "unhealthy", "error": "Pool not initialized"}
        
        try:
            pool = self.engine.pool
            return {
                "status": "healthy",
                "size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

class HTTPConnectionManager:
    """Enhanced HTTP client connection pool manager."""
    
    def __init__(self, config: ConnectionPoolConfig):
        self.config = config
        self.client = None
        self.request_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_response_time": 0.0
        }
    
    async def initialize(self):
        """Initialize HTTP connection pool."""
        try:
            self.client = httpx.AsyncClient(
                limits=httpx.Limits(
                    max_keepalive_connections=self.config.http_pool_size,
                    max_connections=self.config.http_max_connections
                ),
                timeout=httpx.Timeout(self.config.http_timeout),
                http2=True,  # Enable HTTP/2 for better performance
                verify=False  # For testing, set to True in production
            )
            
            logger.info(f"HTTP connection pool initialized (max: {self.config.http_max_connections})")
            
        except Exception as e:
            logger.error(f"Failed to initialize HTTP pool: {e}")
            raise
    
    async def close(self):
        """Close HTTP connection pool."""
        if self.client:
            await self.client.aclose()
    
    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make HTTP request with connection pooling."""
        if not self.client:
            raise RuntimeError("HTTP pool not initialized")
        
        start_time = time.time()
        
        try:
            response = await self.client.request(method, url, **kwargs)
            
            # Update stats
            response_time = time.time() - start_time
            self.request_stats["total_requests"] += 1
            self.request_stats["successful_requests"] += 1
            self.request_stats["total_response_time"] += response_time
            
            return response
            
        except Exception as e:
            self.request_stats["total_requests"] += 1
            self.request_stats["failed_requests"] += 1
            logger.error(f"HTTP request failed: {e}")
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Get HTTP pool statistics."""
        total_requests = self.request_stats["total_requests"]
        success_rate = (
            self.request_stats["successful_requests"] / max(1, total_requests)
        )
        avg_response_time = (
            self.request_stats["total_response_time"] / 
            max(1, self.request_stats["successful_requests"])
        )
        
        return {
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "total_requests": total_requests,
            **self.request_stats
        }

class ConnectionManager:
    """Main connection and caching manager."""
    
    def __init__(self):
        self.cache_config = CacheConfig()
        self.pool_config = ConnectionPoolConfig()
        
        self.cache_manager = CacheManager(self.cache_config)
        self.db_manager = DatabaseConnectionManager(self.pool_config)
        self.http_manager = HTTPConnectionManager(self.pool_config)
        
        self._initialized = False
    
    async def initialize(
        self,
        redis_url: Optional[str] = None,
        database_url: Optional[str] = None
    ):
        """Initialize all connection managers."""
        if self._initialized:
            return
        
        logger.info("Initializing connection manager...")
        
        # Initialize cache
        await self.cache_manager.initialize(redis_url)
        
        # Initialize database pool
        if database_url:
            await self.db_manager.initialize(database_url)
        
        # Initialize HTTP pool
        await self.http_manager.initialize()
        
        self._initialized = True
        logger.info("Connection manager initialized successfully")
    
    async def close(self):
        """Close all connection managers."""
        logger.info("Closing connection manager...")
        
        await self.cache_manager.close()
        await self.db_manager.close()
        await self.http_manager.close()
        
        self._initialized = False
        logger.info("Connection manager closed")
    
    async def health_check(self) -> Dict[str, Any]:
        """Get health status of all connection managers."""
        health = {
            "overall_status": "healthy",
            "cache": self.cache_manager.get_stats(),
            "database": await self.db_manager.health_check(),
            "http": self.http_manager.get_stats()
        }
        
        # Determine overall status
        if health["database"]["status"] != "healthy":
            health["overall_status"] = "degraded"
        
        return health

# Decorators for easy caching
def cache_result(prefix: str, ttl: int = 3600):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key_parts = [func.__name__] + list(args) + list(kwargs.items())
            
            # Try to get from cache
            cache_manager = get_connection_manager().cache_manager
            cached_result = await cache_manager.get(prefix, cache_key_parts)
            
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(prefix, cache_key_parts, result, ttl)
            
            return result
        
        return wrapper
    return decorator

# Global connection manager instance
_connection_manager: Optional[ConnectionManager] = None

def get_connection_manager() -> ConnectionManager:
    """Get global connection manager instance."""
    global _connection_manager
    
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    
    return _connection_manager

async def initialize_connections(
    redis_url: Optional[str] = None,
    database_url: Optional[str] = None
):
    """Initialize global connection manager."""
    manager = get_connection_manager()
    await manager.initialize(redis_url, database_url)

async def close_connections():
    """Close global connection manager."""
    global _connection_manager
    
    if _connection_manager:
        await _connection_manager.close()
        _connection_manager = None

@asynccontextmanager
async def connection_context(
    redis_url: Optional[str] = None,
    database_url: Optional[str] = None
):
    """Context manager for connections."""
    await initialize_connections(redis_url, database_url)
    try:
        yield get_connection_manager()
    finally:
        await close_connections()