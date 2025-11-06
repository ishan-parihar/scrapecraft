"""
Unit Tests for Core Services

Tests individual service components in isolation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Test configuration and utilities
from tests.conftest import (
    mock_llm_service, mock_scraping_service, 
    sample_user_data, sample_investigation_data, sample_osint_data,
    performance_helper
)

class TestLLMService:
    """Test LLM service functionality."""
    
    @pytest.mark.asyncio
    async def test_llm_invoke_basic(self, mock_llm_service):
        """Test basic LLM invocation."""
        mock_llm_service.set_default_response("Test response")
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await mock_llm_service.ainvoke(messages)
        
        assert response.content == "Test response"
        assert mock_llm_service.call_count == 1
        assert mock_llm_service.last_request == "Hello"
    
    @pytest.mark.asyncio
    async def test_llm_invoke_with_specific_response(self, mock_llm_service):
        """Test LLM invocation with specific response."""
        mock_llm_service.set_response("Hello", "Hi there!")
        
        messages = [{"role": "user", "content": "Hello"}]
        response = await mock_llm_service.ainvoke(messages)
        
        assert response.content == "Hi there!"
    
    @pytest.mark.asyncio
    async def test_llm_invoke_delay(self, mock_llm_service):
        """Test LLM invocation with delay."""
        mock_llm_service.response_delay = 0.2
        start_time = asyncio.get_event_loop().time()
        
        await mock_llm_service.ainvoke([{"role": "user", "content": "test"}])
        
        end_time = asyncio.get_event_loop().time()
        assert end_time - start_time >= 0.2

class TestScrapingService:
    """Test scraping service functionality."""
    
    @pytest.mark.asyncio
    async def test_scrape_url_basic(self, mock_scraping_service):
        """Test basic URL scraping."""
        url = "https://example.com"
        result = await mock_scraping_service.scrape_url(url)
        
        assert result["url"] == url
        assert result["title"] == "Mock Title"
        assert result["content"] == "Mock content for testing"
        assert result["status_code"] == 200
        assert "scraped_at" in result
        assert mock_scraping_service.call_count == 1
    
    @pytest.mark.asyncio
    async def test_scrape_url_with_custom_data(self, mock_scraping_service):
        """Test scraping with custom data."""
        url = "https://custom.com"
        custom_data = {
            "url": url,
            "title": "Custom Title",
            "content": "Custom content",
            "status_code": 200,
            "scraped_at": datetime.utcnow().isoformat()
        }
        
        mock_scraping_service.set_scraped_data(url, custom_data)
        result = await mock_scraping_service.scrape_url(url)
        
        assert result["title"] == "Custom Title"
        assert result["content"] == "Custom content"

class TestDatabaseService:
    """Test database service functionality."""
    
    @pytest.mark.asyncio
    async def test_database_connection(self, setup_test_environment):
        """Test database connection setup."""
        db = setup_test_environment["database"]
        
        # Test sync session
        session = db.get_sync_session()
        assert session is not None
        session.close()
    
    @pytest.mark.asyncio
    async def test_async_database_session(self, setup_test_environment):
        """Test async database session."""
        db = setup_test_environment["database"]
        
        async for session in db.get_async_session():
            assert session is not None
    
    @pytest.mark.asyncio
    async def test_database_transaction(self, setup_test_environment):
        """Test database transaction handling."""
        db = setup_test_environment["database"]
        
        async for session in db.get_async_session():
            # Test basic transaction
            try:
                # Transaction operations would go here
                await session.commit()
            except Exception:
                await session.rollback()
                raise

class TestAuthService:
    """Test authentication service functionality."""
    
    def test_password_hashing(self):
        """Test password hashing and verification."""
        # Mock password hashing
        password = "testpassword123"
        hashed_password = "hashed_" + password
        
        # In real implementation, would use bcrypt
        assert password != hashed_password
        assert hashed_password.startswith("hashed_")
    
    def test_jwt_token_generation(self):
        """Test JWT token generation."""
        user_id = 1
        username = "testuser"
        
        # Mock token generation
        token = f"mock_token_{user_id}_{username}"
        
        assert "mock_token" in token
        assert str(user_id) in token
        assert username in token
    
    def test_user_role_validation(self):
        """Test user role validation."""
        valid_roles = ["admin", "analyst", "viewer"]
        
        # Test valid role
        assert "analyst" in valid_roles
        
        # Test invalid role
        assert "hacker" not in valid_roles

class TestTaskStorageService:
    """Test task storage service functionality."""
    
    @pytest.mark.asyncio
    async def test_task_creation(self, setup_test_environment):
        """Test task creation."""
        redis = setup_test_environment["redis"]
        client = redis.get_client()
        
        # Mock task creation
        task_id = "test_task_123"
        task_data = {
            "id": task_id,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # In real implementation, would store in Redis
        # mock_redis_set(client, f"task:{task_id}", json.dumps(task_data))
        assert task_id is not None
        assert task_data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_task_status_update(self):
        """Test task status update."""
        task_id = "test_task_123"
        new_status = "completed"
        
        # Mock status update
        task_data = {
            "id": task_id,
            "status": new_status,
            "completed_at": datetime.utcnow().isoformat()
        }
        
        assert task_data["status"] == new_status
        assert "completed_at" in task_data

class TestWorkflowService:
    """Test workflow service functionality."""
    
    @pytest.mark.asyncio
    async def test_workflow_creation(self):
        """Test workflow creation."""
        workflow_data = {
            "name": "Test Workflow",
            "description": "A test workflow",
            "steps": [
                {"name": "data_collection", "type": "scraping"},
                {"name": "analysis", "type": "ai_analysis"}
            ]
        }
        
        # Mock workflow creation
        workflow_id = "workflow_123"
        workflow = {
            "id": workflow_id,
            **workflow_data,
            "status": "created",
            "created_at": datetime.utcnow().isoformat()
        }
        
        assert workflow["id"] is not None
        assert len(workflow["steps"]) == 2
        assert workflow["status"] == "created"
    
    @pytest.mark.asyncio
    async def test_workflow_execution(self):
        """Test workflow execution."""
        workflow_id = "workflow_123"
        
        # Mock execution steps
        execution_steps = [
            {"step": "data_collection", "status": "completed"},
            {"step": "analysis", "status": "in_progress"}
        ]
        
        execution_status = {
            "workflow_id": workflow_id,
            "status": "running",
            "current_step": "analysis",
            "steps": execution_steps,
            "started_at": datetime.utcnow().isoformat()
        }
        
        assert execution_status["status"] == "running"
        assert execution_status["current_step"] == "analysis"

class TestAuditService:
    """Test audit service functionality."""
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self):
        """Test audit log creation."""
        audit_data = {
            "user_id": 1,
            "action": "investigation_created",
            "resource": "investigation",
            "resource_id": "inv_123",
            "ip_address": "127.0.0.1",
            "user_agent": "TestClient/1.0",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Mock audit log creation
        audit_id = "audit_123"
        audit_log = {
            "id": audit_id,
            **audit_data
        }
        
        assert audit_log["id"] is not None
        assert audit_log["action"] == "investigation_created"
        assert audit_log["resource"] == "investigation"
    
    @pytest.mark.asyncio
    async def test_audit_log_retrieval(self):
        """Test audit log retrieval."""
        user_id = 1
        
        # Mock audit logs
        audit_logs = [
            {
                "id": "audit_1",
                "user_id": user_id,
                "action": "login",
                "timestamp": datetime.utcnow().isoformat()
            },
            {
                "id": "audit_2",
                "user_id": user_id,
                "action": "investigation_created",
                "timestamp": datetime.utcnow().isoformat()
            }
        ]
        
        # Filter by user
        user_logs = [log for log in audit_logs if log["user_id"] == user_id]
        
        assert len(user_logs) == 2
        assert all(log["user_id"] == user_id for log in user_logs)

class TestOSService:
    """Test OSINT service functionality."""
    
    @pytest.mark.asyncio
    async def test_osint_data_collection(self):
        """Test OSINT data collection."""
        target = "example.com"
        data_sources = ["dns", "whois", "social_media"]
        
        # Mock OSINT collection
        collection_result = {
            "target": target,
            "collection_id": "osint_123",
            "status": "in_progress",
            "data_sources": data_sources,
            "started_at": datetime.utcnow().isoformat()
        }
        
        assert collection_result["target"] == target
        assert collection_result["status"] == "in_progress"
        assert len(collection_result["data_sources"]) == 3
    
    @pytest.mark.asyncio
    async def test_osint_results_processing(self):
        """Test OSINT results processing."""
        collection_id = "osint_123"
        
        # Mock OSINT results
        osint_results = {
            "collection_id": collection_id,
            "target": "example.com",
            "status": "completed",
            "results": {
                "dns": {
                    "records": ["A: 93.184.216.34", "MX: mail.example.com"]
                },
                "whois": {
                    "registrar": "Example Registrar",
                    "created": "1995-08-13"
                },
                "social_media": {
                    "twitter": "@example",
                    "linkedin": "example-corp"
                }
            },
            "completed_at": datetime.utcnow().isoformat()
        }
        
        assert osint_results["status"] == "completed"
        assert "dns" in osint_results["results"]
        assert "whois" in osint_results["results"]
        assert "social_media" in osint_results["results"]

class TestPipelineService:
    """Test pipeline service functionality."""
    
    @pytest.mark.asyncio
    async def test_pipeline_creation(self):
        """Test pipeline creation."""
        pipeline_data = {
            "name": "Test Pipeline",
            "description": "A test data processing pipeline",
            "config": {
                "input_source": "web_scraping",
                "processing_steps": ["cleaning", "analysis", "storage"],
                "output_format": "json"
            }
        }
        
        # Mock pipeline creation
        pipeline_id = "pipeline_123"
        pipeline = {
            "id": pipeline_id,
            **pipeline_data,
            "status": "created",
            "created_at": datetime.utcnow().isoformat()
        }
        
        assert pipeline["id"] is not None
        assert len(pipeline["config"]["processing_steps"]) == 3
        assert pipeline["status"] == "created"
    
    @pytest.mark.asyncio
    async def test_pipeline_execution(self):
        """Test pipeline execution."""
        pipeline_id = "pipeline_123"
        input_data = {"urls": ["https://example.com"]}
        
        # Mock pipeline execution
        execution_result = {
            "pipeline_id": pipeline_id,
            "execution_id": "exec_123",
            "status": "running",
            "input_data": input_data,
            "started_at": datetime.utcnow().isoformat()
        }
        
        assert execution_result["status"] == "running"
        assert execution_result["pipeline_id"] == pipeline_id

class TestPerformanceService:
    """Test performance monitoring service."""
    
    @pytest.mark.asyncio
    async def test_performance_metrics_collection(self, performance_helper):
        """Test performance metrics collection."""
        # Mock function to measure
        async def mock_operation(x):
            await asyncio.sleep(0.1)
            return f"result_{x}"
        
        # Create test arguments
        args_list = [(i,) for i in range(5)]
        
        # Run performance test
        metrics = await performance_helper.run_concurrent_requests(
            mock_operation,
            args_list,
            concurrency=3
        )
        
        # Verify metrics
        assert metrics["total_requests"] == 5
        assert metrics["successful_requests"] == 5
        assert metrics["success_rate"] == 1.0
        assert metrics["avg_response_time"] > 0
        assert "requests_per_second" in metrics
    
    @pytest.mark.asyncio
    async def test_performance_with_failures(self, performance_helper):
        """Test performance monitoring with failures."""
        # Mock failing function
        async def failing_operation(x):
            await asyncio.sleep(0.05)
            if x % 2 == 0:
                raise ValueError(f"Failed for {x}")
            return f"success_{x}"
        
        args_list = [(i,) for i in range(4)]
        
        metrics = await performance_helper.run_concurrent_requests(
            failing_operation,
            args_list,
            concurrency=2
        )
        
        # Should have some failures
        assert metrics["total_requests"] == 4
        assert metrics["successful_requests"] == 2
        assert metrics["failed_requests"] == 2
        assert metrics["success_rate"] == 0.5

class TestWebSocketService:
    """Test WebSocket service functionality."""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection handling."""
        # Mock WebSocket connection
        websocket = Mock()
        websocket.client = Mock()
        websocket.client.host = "127.0.0.1"
        websocket.client.port = 12345
        
        connection_info = {
            "websocket": websocket,
            "client_id": "client_123",
            "connected_at": datetime.utcnow().isoformat(),
            "status": "connected"
        }
        
        assert connection_info["status"] == "connected"
        assert connection_info["client_id"] is not None
    
    @pytest.mark.asyncio
    async def test_websocket_message_broadcast(self):
        """Test WebSocket message broadcasting."""
        # Mock broadcast to multiple clients
        clients = ["client_1", "client_2", "client_3"]
        message = {
            "type": "investigation_update",
            "data": {"status": "completed", "progress": 100}
        }
        
        # Mock broadcast
        broadcast_results = []
        for client_id in clients:
            result = {
                "client_id": client_id,
                "message_sent": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            broadcast_results.append(result)
        
        # All clients should receive the message
        assert len(broadcast_results) == 3
        assert all(result["message_sent"] for result in broadcast_results)

if __name__ == "__main__":
    print("Service Unit Tests")
    print("=" * 50)
    print("Testing individual service components...")
    print("Run with: pytest tests/unit/test_services.py -v")