"""
Unit Tests for API Endpoints

Tests individual API endpoints in isolation.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from tests.conftest import (
    test_client, async_test_client, sample_user_data, 
    sample_investigation_data, sample_osint_data,
    assert_valid_response, assert_error_response, create_test_headers
)

class TestAuthAPI:
    """Test authentication API endpoints."""
    
    def test_register_user_success(self, test_client):
        """Test successful user registration."""
        response = test_client.post("/api/auth/register", json=sample_user_data())
        assert_valid_response(response, 201, ["id", "username", "email"])
        
        data = response.json()
        assert data["username"] == sample_user_data()["username"]
        assert data["email"] == sample_user_data()["email"]
        assert "id" in data
    
    def test_register_user_duplicate_email(self, test_client):
        """Test registration with duplicate email."""
        # First registration
        test_client.post("/api/auth/register", json=sample_user_data())
        
        # Duplicate registration
        response = test_client.post("/api/auth/register", json=sample_user_data())
        assert_error_response(response, 400, "already exists")
    
    def test_register_user_invalid_data(self, test_client):
        """Test registration with invalid data."""
        invalid_data = {"username": "test", "email": "invalid-email"}
        response = test_client.post("/api/auth/register", json=invalid_data)
        assert_error_response(response, 422)
    
    def test_login_success(self, test_client):
        """Test successful user login."""
        # Register user first
        test_client.post("/api/auth/register", json=sample_user_data())
        
        # Login
        login_data = {
            "username": sample_user_data()["username"],
            "password": sample_user_data()["password"]
        }
        response = test_client.post("/api/auth/login", data=login_data)
        assert_valid_response(response, 200, ["access_token", "refresh_token", "token_type"])
        
        data = response.json()
        assert data["token_type"] == "bearer"
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, test_client):
        """Test login with invalid credentials."""
        login_data = {"username": "nonexistent", "password": "wrong"}
        response = test_client.post("/api/auth/login", data=login_data)
        assert_error_response(response, 401, "invalid")
    
    @pytest.mark.asyncio
    async def test_refresh_token(self, async_test_client):
        """Test token refresh."""
        # This would require setting up proper authentication
        # For now, test the endpoint structure
        response = await async_test_client.post("/api/auth/refresh", json={
            "refresh_token": "mock_token"
        })
        # Expected to fail with invalid token, but endpoint should exist
        assert response.status_code in [401, 422]
    
    def test_logout(self, test_client):
        """Test user logout."""
        # This would require proper authentication setup
        response = test_client.post("/api/auth/logout", headers={
            "Authorization": "Bearer mock_token"
        })
        # Expected to fail with invalid token, but endpoint should exist
        assert response.status_code in [401, 422]

class TestInvestigationsAPI:
    """Test investigations API endpoints."""
    
    def test_create_investigation_unauthorized(self, test_client):
        """Test creating investigation without authentication."""
        response = test_client.post("/api/investigations", json=sample_investigation_data())
        assert_error_response(response, 401)
    
    def test_create_investigation_authorized(self, test_client):
        """Test creating investigation with authentication."""
        # Mock authentication
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.post(
                "/api/investigations",
                json=sample_investigation_data(),
                headers=headers
            )
            assert_valid_response(response, 201, ["id", "title", "target"])
    
    def test_get_investigations(self, test_client):
        """Test getting investigations list."""
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/investigations", headers=headers)
            assert_valid_response(response, 200)
            
            data = response.json()
            assert isinstance(data, list)
    
    def test_get_investigation_by_id(self, test_client):
        """Test getting investigation by ID."""
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/investigations/1", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]
    
    def test_update_investigation(self, test_client):
        """Test updating investigation."""
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            update_data = {"title": "Updated Investigation"}
            response = test_client.put(
                "/api/investigations/1",
                json=update_data,
                headers=headers
            )
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]
    
    def test_delete_investigation(self, test_client):
        """Test deleting investigation."""
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.delete("/api/investigations/1", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 204, 404]

class TestAIInvestigationAPI:
    """Test AI investigation API endpoints."""
    
    def test_start_ai_investigation(self, test_client):
        """Test starting AI investigation."""
        with patch('app.api.ai_investigation.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            investigation_data = {
                "target": "test.example.com",
                "objective": "Test investigation",
                "priority": "medium"
            }
            response = test_client.post(
                "/api/ai-investigation/start",
                json=investigation_data,
                headers=headers
            )
            assert_valid_response(response, 200, ["investigation_id", "status"])
    
    def test_get_investigation_status(self, test_client):
        """Test getting investigation status."""
        with patch('app.api.ai_investigation.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/ai-investigation/status/123", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]
    
    def test_stop_investigation(self, test_client):
        """Test stopping investigation."""
        with patch('app.api.ai_investigation.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.post("/api/ai-investigation/stop/123", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]

class TestOSINTAPI:
    """Test OSINT API endpoints."""
    
    def test_start_osint_collection(self, test_client):
        """Test starting OSINT collection."""
        with patch('app.api.osint.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.post(
                "/api/osint/collect",
                json=sample_osint_data(),
                headers=headers
            )
            assert_valid_response(response, 200, ["collection_id", "status"])
    
    def test_get_osint_results(self, test_client):
        """Test getting OSINT results."""
        with patch('app.api.osint.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/osint/results/123", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]
    
    def test_get_osint_sources(self, test_client):
        """Test getting available OSINT sources."""
        with patch('app.api.osint.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/osint/sources", headers=headers)
            assert_valid_response(response, 200)
            
            data = response.json()
            assert isinstance(data, list)

class TestPipelinesAPI:
    """Test pipelines API endpoints."""
    
    def test_get_pipelines(self, test_client):
        """Test getting pipelines list."""
        with patch('app.api.pipelines.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/pipelines", headers=headers)
            assert_valid_response(response, 200)
            
            data = response.json()
            assert isinstance(data, list)
    
    def test_create_pipeline(self, test_client):
        """Test creating pipeline."""
        with patch('app.api.pipelines.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            pipeline_data = {
                "name": "Test Pipeline",
                "description": "A test pipeline",
                "config": {"steps": []}
            }
            response = test_client.post(
                "/api/pipelines",
                json=pipeline_data,
                headers=headers
            )
            assert_valid_response(response, 201, ["id", "name"])
    
    def test_execute_pipeline(self, test_client):
        """Test executing pipeline."""
        with patch('app.api.pipelines.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.post("/api/pipelines/123/execute", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]
    
    def test_get_pipeline_status(self, test_client):
        """Test getting pipeline execution status."""
        with patch('app.api.pipelines.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/pipelines/123/status", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]

class TestScrapingAPI:
    """Test scraping API endpoints."""
    
    def test_start_scraping(self, test_client):
        """Test starting scraping task."""
        with patch('app.api.scraping.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            scraping_data = {
                "urls": ["https://example.com"],
                "options": {"depth": 1}
            }
            response = test_client.post(
                "/api/scraping/start",
                json=scraping_data,
                headers=headers
            )
            assert_valid_response(response, 200, ["task_id", "status"])
    
    def test_get_scraping_status(self, test_client):
        """Test getting scraping task status."""
        with patch('app.api.scraping.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/scraping/status/123", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]
    
    def test_get_scraping_results(self, test_client):
        """Test getting scraping results."""
        with patch('app.api.scraping.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/scraping/results/123", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]

class TestHealthAPI:
    """Test health check API endpoints."""
    
    def test_health_check(self, test_client):
        """Test basic health check."""
        response = test_client.get("/api/health")
        assert_valid_response(response, 200, ["status", "timestamp"])
        
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
    
    def test_detailed_health_check(self, test_client):
        """Test detailed health check."""
        response = test_client.get("/api/health/detailed")
        assert_valid_response(response, 200)
        
        data = response.json()
        assert "services" in data
        assert "database" in data["services"]
        assert "redis" in data["services"]

class TestChatAPI:
    """Test chat API endpoints."""
    
    def test_send_message(self, test_client):
        """Test sending chat message."""
        with patch('app.api.chat.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            message_data = {
                "message": "Hello, AI assistant",
                "context": "investigation"
            }
            response = test_client.post(
                "/api/chat/send",
                json=message_data,
                headers=headers
            )
            assert_valid_response(response, 200, ["response", "timestamp"])
    
    def test_get_chat_history(self, test_client):
        """Test getting chat history."""
        with patch('app.api.chat.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/chat/history", headers=headers)
            assert_valid_response(response, 200)
            
            data = response.json()
            assert isinstance(data, list)

class TestWorkflowAPI:
    """Test workflow API endpoints."""
    
    def test_create_workflow(self, test_client):
        """Test creating workflow."""
        with patch('app.api.workflow.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            workflow_data = {
                "name": "Test Workflow",
                "description": "A test workflow",
                "steps": [
                    {"name": "step1", "type": "data_collection"},
                    {"name": "step2", "type": "analysis"}
                ]
            }
            response = test_client.post(
                "/api/workflows",
                json=workflow_data,
                headers=headers
            )
            assert_valid_response(response, 201, ["id", "name"])
    
    def test_get_workflows(self, test_client):
        """Test getting workflows list."""
        with patch('app.api.workflow.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/workflows", headers=headers)
            assert_valid_response(response, 200)
            
            data = response.json()
            assert isinstance(data, list)

class TestExecutionAPI:
    """Test execution API endpoints."""
    
    def test_execute_task(self, test_client):
        """Test task execution."""
        with patch('app.api.execution.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            task_data = {
                "type": "scraping",
                "config": {"urls": ["https://example.com"]}
            }
            response = test_client.post(
                "/api/execution/start",
                json=task_data,
                headers=headers
            )
            assert_valid_response(response, 200, ["execution_id", "status"])
    
    def test_get_execution_status(self, test_client):
        """Test getting execution status."""
        with patch('app.api.execution.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            
            headers = create_test_headers("mock_token")
            response = test_client.get("/api/execution/status/123", headers=headers)
            # May return 404 if not found, but should not be 401/403
            assert response.status_code in [200, 404]

if __name__ == "__main__":
    print("API Unit Tests")
    print("=" * 50)
    print("Testing individual API endpoints in isolation...")
    print("Run with: pytest tests/unit/test_api.py -v")