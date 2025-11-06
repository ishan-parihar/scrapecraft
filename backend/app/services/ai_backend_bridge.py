"""
AI Backend Bridge for OSINT Collection Agents

This module provides a bridge between AI agents and backend scraping services,
enabling state synchronization and task coordination between AI agents and
backend services.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Using dynamic import to avoid circular import issues
import importlib.util
import os

# Import the state module dynamically
state_module_path = os.path.join(os.path.dirname(__file__), 'state.py')
spec = importlib.util.spec_from_file_location("state", state_module_path)
if spec is not None and spec.loader is not None:
    state_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(state_module)
    InvestigationState = state_module.InvestigationState
    InvestigationPhase = state_module.InvestigationPhase
    InvestigationStatus = state_module.InvestigationStatus
else:
    raise ImportError("Could not load state module")

# Dynamically import the BackendScrapingClient to avoid import issues
import importlib.util
import os

# Import the client module dynamically
client_module_path = os.path.join(os.path.dirname(__file__), 'backend_scraping_client.py')
spec = importlib.util.spec_from_file_location("backend_scraping_client", client_module_path)
if spec is not None and spec.loader is not None:
    backend_scraping_client_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backend_scraping_client_module)
    BackendScrapingClient = backend_scraping_client_module.BackendScrapingClient
else:
    raise ImportError("Could not load backend scraping client module")


logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Types of tasks that can be coordinated through the bridge"""
    SCRAPING = "scraping"
    SEARCH = "search"
    CRAWLING = "crawling"
    DATA_EXTRACTION = "data_extraction"
    VALIDATION = "validation"


class TaskStatus(Enum):
    """Status of backend tasks"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AIBackendBridge:
    """
    Bridge class that synchronizes AI agent state with backend scraping services.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.client = BackendScrapingClient(base_url)
        self.logger = logging.getLogger(f"{__name__}.AIBackendBridge")
        
    async def __aenter__(self):
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)
    
    async def sync_investigation_state(
        self, 
        investigation_id: str, 
        state: InvestigationState
    ) -> Dict[str, Any]:
        """
        Synchronize investigation state with backend services.
        
        Args:
            investigation_id: Unique ID of the investigation
            state: Current investigation state
            
        Returns:
            Synchronization result
        """
        url = f"{self.client.base_url}/api/investigation/{investigation_id}/state"
        
        # Prepare state data for sync
        sync_data = {
            "investigation_id": investigation_id,
            "current_phase": state["current_phase"].value,
            "overall_status": state["overall_status"].value,
            "progress_percentage": state["progress_percentage"],
            "sources_used": state["sources_used"],
            "agents_participated": state["agents_participated"],
            "confidence_level": state["confidence_level"],
            "errors_count": len(state["errors"]),
            "warnings_count": len(state["warnings"]),
            "total_execution_time": state["total_execution_time"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with self.client.session.post(url, json=sync_data) as response:
                if response.status == 200:
                    result = await response.json()
                    self.logger.info(f"Investigation state synced for {investigation_id}")
                    return result
                else:
                    error_text = await response.text()
                    self.logger.error(f"State sync failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except Exception as e:
            self.logger.error(f"State sync error: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def submit_scraping_task(
        self, 
        investigation_id: str, 
        urls: List[str], 
        prompt: str,
        schema: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Submit a scraping task to backend services and track it.
        
        Args:
            investigation_id: Investigation ID this task belongs to
            urls: URLs to scrape
            prompt: Natural language prompt for extraction
            schema: Optional schema for structured extraction
            
        Returns:
            Task submission result with task ID
        """
        # First submit the scraping task
        submission_result = await self.client.execute_scraping(urls, prompt, schema)
        
        if not submission_result.get("success"):
            return submission_result
        
        task_id = submission_result.get("task_id")
        if not task_id:
            return {
                "success": False,
                "error": "No task ID returned from backend"
            }
        
        # Create task tracking entry
        tracking_data = {
            "task_id": task_id,
            "investigation_id": investigation_id,
            "task_type": TaskType.SCRAPING.value,
            "urls": urls,
            "prompt": prompt,
            "created_at": datetime.utcnow().isoformat(),
            "status": TaskStatus.PENDING.value
        }
        
        # Register the task in the backend task tracking system
        tracking_url = f"{self.client.base_url}/api/tasks/register"
        try:
            async with self.client.session.post(tracking_url, json=tracking_data) as response:
                if response.status == 200:
                    tracking_result = await response.json()
                    return {
                        "success": True,
                        "task_id": task_id,
                        "tracking_result": tracking_result
                    }
                else:
                    error_text = await response.text()
                    self.logger.error(f"Task tracking registration failed: {response.status} - {error_text}")
                    # Still return the original task ID since backend task was created
                    return {
                        "success": True,
                        "task_id": task_id,
                        "warning": f"Task created but tracking registration failed: {error_text}"
                    }
        except Exception as e:
            self.logger.error(f"Task tracking error: {str(e)}")
            # Still return the original task ID since backend task was created
            return {
                "success": True,
                "task_id": task_id,
                "warning": f"Task created but tracking registration failed: {str(e)}"
            }
    
    async def wait_for_task_completion(
        self, 
        task_id: str, 
        max_retries: int = 20,
        poll_interval: int = 3
    ) -> Dict[str, Any]:
        """
        Wait for a backend task to complete.
        
        Args:
            task_id: Backend task ID to wait for
            max_retries: Maximum number of polling attempts
            poll_interval: Seconds between polling attempts
            
        Returns:
            Task completion result with data
        """
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                status_result = await self.client.get_task_status(task_id)
                
                if status_result.get("status") == "completed":
                    # Get results
                    results = await self.client.get_task_results(task_id)
                    return {
                        "success": True,
                        "task_id": task_id,
                        "status": "completed",
                        "results": results,
                        "data": results
                    }
                elif status_result.get("status") in ["failed", "error"]:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "status": status_result.get("status"),
                        "error": status_result.get("error", "Task failed"),
                        "data": None
                    }
                
                # Wait before next check
                await asyncio.sleep(poll_interval)
                retry_count += 1
                
            except Exception as e:
                self.logger.error(f"Error checking task status: {str(e)}")
                retry_count += 1
                await asyncio.sleep(poll_interval)
        
        return {
            "success": False,
            "task_id": task_id,
            "status": "timeout",
            "error": "Task timeout - still running after maximum wait time",
            "data": None
        }
    
    async def submit_search_task(
        self, 
        investigation_id: str, 
        query: str, 
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Submit a search task to backend services.
        
        Args:
            investigation_id: Investigation ID this task belongs to
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            Task submission result with task ID
        """
        url = f"{self.client.base_url}/api/tasks/search"
        payload = {
            "investigation_id": investigation_id,
            "query": query,
            "max_results": max_results,
            "task_type": TaskType.SEARCH.value
        }
        
        try:
            async with self.client.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Search task submission failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except Exception as e:
            logger.error(f"Search task submission error: {str(e)}")
            return {"error": str(e), "success": False}
    
    async def get_task_results_with_cache(
        self, 
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get task results with caching to avoid repeated backend calls.
        
        Args:
            task_id: Backend task ID to get results for
            
        Returns:
            Task results
        """
        # For now, just return the results from backend
        # In a real implementation, we would cache results
        return await self.client.get_task_results(task_id)
    
    async def update_task_status(
        self, 
        task_id: str, 
        status: TaskStatus,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Update the status of a backend task.
        
        Args:
            task_id: Backend task ID to update
            status: New status
            details: Additional status details
            
        Returns:
            Update result
        """
        url = f"{self.client.base_url}/api/tasks/{task_id}/status"
        payload = {
            "status": status.value,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        try:
            async with self.client.session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"Task status update failed: {response.status} - {error_text}")
                    return {"error": f"HTTP {response.status}: {error_text}", "success": False}
        except Exception as e:
            logger.error(f"Task status update error: {str(e)}")
            return {"error": str(e), "success": False}


# Global bridge instance
_bridge_instance = None


async def get_global_ai_bridge() -> AIBackendBridge:
    """
    Get the global AI backend bridge instance.
    Note: This returns a new instance each time, as proper async singleton handling
    would require more complex implementation with connection management.
    """
    global _bridge_instance
    if _bridge_instance is None:
        # Dynamically import the IntegrationConfig to avoid import issues
        import importlib.util
        import os
        
        # Import the config module dynamically
        config_module_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'config', 'integration_config.py')
        spec = importlib.util.spec_from_file_location("integration_config", config_module_path)
        if spec is not None and spec.loader is not None:
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            IntegrationConfig = config_module.IntegrationConfig
        else:
            raise ImportError("Could not load integration config module")
        
        config = IntegrationConfig()
        _bridge_instance = AIBackendBridge(base_url=config.backend_scraping_base_url)
    return _bridge_instance


async def close_global_ai_bridge():
    """
    Close the global AI backend bridge instance.
    """
    global _bridge_instance
    if _bridge_instance:
        await _bridge_instance.__aexit__(None, None, None)
        _bridge_instance = None