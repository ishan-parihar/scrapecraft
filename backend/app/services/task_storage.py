"""
Redis-based task storage service for ScrapeCraft
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings
import asyncio

logger = logging.getLogger(__name__)

class TaskStorageService:
    """Redis-based task storage service with connection retry logic."""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client = None
        self.task_ttl = 3600  # Tasks expire after 1 hour
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        self.connection_pool = None
    
    async def connect(self):
        """Initialize Redis connection with retry logic."""
        for attempt in range(self.max_retries):
            try:
                # Create connection pool for better performance
                self.connection_pool = redis.ConnectionPool.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                    max_connections=10,
                    retry_on_timeout=True
                )
                
                self.redis_client = redis.Redis(connection_pool=self.connection_pool)
                
                # Test connection - use async operations for compatibility
                try:
                    # Try a simple set/get operation to test connection
                    await self.redis_client.set("test_key", "test_value", ex=10)
                    await self.redis_client.delete("test_key")
                    logger.info(f"Connected to Redis for task storage (attempt {attempt + 1})")
                    return True
                except Exception as test_error:
                    raise Exception(f"Redis connection test failed: {test_error}")
                    
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    logger.error("All Redis connection attempts failed")
                    self.redis_client = None
                    self.connection_pool = None
                    return False
        
        return False
    
    async def disconnect(self):
        """Close Redis connection."""
        try:
            if self.redis_client:
                await self.redis_client.aclose()
            if self.connection_pool:
                await self.connection_pool.aclose()
            logger.info("Redis disconnected successfully")
        except Exception as e:
            logger.error(f"Error disconnecting Redis: {e}")
    
    async def ensure_connection(self) -> bool:
        """Ensure Redis connection is active, reconnect if needed."""
        if not self.redis_client:
            logger.info("Redis not connected, attempting to connect...")
            return await self.connect()
        
        try:
            # Test existing connection with a simple operation
            if self.redis_client:
                redis_client = self.redis_client  # Type assertion
                await redis_client.set("test_key", "test_value", ex=10)
                await redis_client.delete("test_key")
                return True
        except Exception as e:
            logger.warning(f"Redis connection check failed: {e}, attempting to reconnect...")
        
        return await self.connect()
    
    def _get_task_key(self, task_id: str) -> str:
        """Generate Redis key for task."""
        return f"scraping_task:{task_id}"
    
    async def create_task(
        self,
        task_id: str,
        urls: List[str],
        prompt: str,
        schema: Optional[Dict] = None
    ) -> bool:
        """Create a new task in Redis."""
        if not await self.ensure_connection() or not self.redis_client:
            logger.warning("Redis not available for task creation")
            return False
            
        try:
            task_data = {
                "task_id": task_id,
                "status": "pending",
                "urls": urls,
                "prompt": prompt,
                "schema": schema or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "results": None,
                "error": None
            }
            
            key = self._get_task_key(task_id)
            redis_client = self.redis_client  # Type assertion
            await redis_client.setex(
                key,
                self.task_ttl,
                json.dumps(task_data)
            )
            
            logger.info(f"Created task {task_id} in Redis")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create task {task_id}: {e}")
            return False
    
    async def update_task_status(
        self,
        task_id: str,
        status: str,
        results: Optional[List[Dict]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Update task status in Redis."""
        if not await self.ensure_connection() or not self.redis_client:
            logger.warning("Redis not available for task update")
            return False
            
        try:
            key = self._get_task_key(task_id)
            redis_client = self.redis_client  # Type assertion
            existing_data = await redis_client.get(key)
            
            if not existing_data:
                logger.warning(f"Task {task_id} not found for update")
                return False
            
            task_data = json.loads(existing_data)
            task_data["status"] = status
            task_data["updated_at"] = datetime.utcnow().isoformat()
            
            if results is not None:
                task_data["results"] = results
            if error is not None:
                task_data["error"] = error
            
            await redis_client.setex(
                key,
                self.task_ttl,
                json.dumps(task_data)
            )
            
            logger.info(f"Updated task {task_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task data from Redis."""
        if not await self.ensure_connection() or not self.redis_client:
            logger.warning("Redis not available for task retrieval")
            return None
            
        try:
            key = self._get_task_key(task_id)
            redis_client = self.redis_client  # Type assertion
            data = await redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task from Redis."""
        if not await self.ensure_connection() or not self.redis_client:
            logger.warning("Redis not available for task deletion")
            return False
            
        try:
            key = self._get_task_key(task_id)
            redis_client = self.redis_client  # Type assertion
            result = await redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    async def list_tasks(self, limit: int = 50) -> List[Dict]:
        """List all tasks (for debugging/admin)."""
        if not await self.ensure_connection() or not self.redis_client:
            logger.warning("Redis not available for task listing")
            return []
            
        try:
            pattern = "scraping_task:*"
            redis_client = self.redis_client  # Type assertion
            keys = await redis_client.keys(pattern)
            
            tasks = []
            for key in keys[:limit]:
                data = await redis_client.get(key)
                if data:
                    tasks.append(json.loads(data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

# Global instance
task_storage = TaskStorageService()