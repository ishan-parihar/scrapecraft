"""
Redis-based task storage service for ScrapeCraft
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis.asyncio as redis
from app.config import settings

logger = logging.getLogger(__name__)

class TaskStorageService:
    """Redis-based task storage service."""
    
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.redis_client = None
        self.task_ttl = 3600  # Tasks expire after 1 hour
    
    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("Connected to Redis for task storage")
        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            # Don't raise - continue without Redis for development
            self.redis_client = None
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
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
            await self.redis_client.setex(
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
        try:
            key = self._get_task_key(task_id)
            existing_data = await self.redis_client.get(key)
            
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
            
            await self.redis_client.setex(
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
        try:
            key = self._get_task_key(task_id)
            data = await self.redis_client.get(key)
            
            if data:
                return json.loads(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    async def delete_task(self, task_id: str) -> bool:
        """Delete task from Redis."""
        try:
            key = self._get_task_key(task_id)
            result = await self.redis_client.delete(key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            return False
    
    async def list_tasks(self, limit: int = 50) -> List[Dict]:
        """List all tasks (for debugging/admin)."""
        try:
            pattern = "scraping_task:*"
            keys = await self.redis_client.keys(pattern)
            
            tasks = []
            for key in keys[:limit]:
                data = await self.redis_client.get(key)
                if data:
                    tasks.append(json.loads(data))
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to list tasks: {e}")
            return []

# Global instance
task_storage = TaskStorageService()