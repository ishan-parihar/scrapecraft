"""
Comprehensive Security Test Suite for ScrapeCraft OSINT Platform

This module provides security testing for:
- Authentication and authorization
- Rate limiting and DDoS protection
- Input validation and XSS prevention
- SQL injection protection
- Security headers and CORS
- JWT token security
- Session management
"""

import pytest
import asyncio
import time
from typing import Dict, Any, List
import json
import hashlib
import secrets

from fastapi.testclient import TestClient
from httpx import AsyncClient

# Security test configuration
SECURITY_TEST_CONFIG = {
    "max_login_attempts": 5,
    "rate_limit_window": 300,  # 5 minutes
    "password_min_length": 12,
    "jwt_secret_length": 64,
    "max_concurrent_sessions": 3
}

class SecurityTestSuite:
    """Comprehensive security testing suite."""
    
    def __init__(self, client: TestClient):
        self.client = client
        self.base_url = "http://testserver"
        self.test_results: List[Dict[str, Any]] = []
    
    def log_test_result(self, test_name: str, passed: bool, details: str = "", risk_level: str = "MEDIUM"):
        """Log test result with risk assessment."""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details,
            "risk_level": risk_level,
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {test_name} - {details} (Risk: {risk_level})")
    
    async def test_authentication_security(self) -> Dict[str, Any]:
        """Test authentication security mechanisms."""
        results = {
            "category": "Authentication Security",
            "tests": []
        }
        
        # Test 1: Password strength validation
        try:
            weak_passwords = [
                "password", "12345678", "qwerty", "admin123",
                "short", "nouppercase1!", "NOLOWERCASE1!", "NoNumbers!",
                "NoSymbols123", "ValidPassword123!"
            ]
            
            weak_password_count = 0
            for password in weak_passwords:
                response = self.client.post("/api/auth/register", json={
                    "username": f"testuser_{password[:8]}",
                    "email": f"test_{password[:8]}@example.com",
                    "password": password,
                    "confirm_password": password
                })
                
                if response.status_code != 200 and password != "ValidPassword123!":
                    weak_password_count += 1
            
            password_security_passed = weak_password_count >= len(weak_passwords) - 1
            self.log_test_result(
                "Password Strength Validation",
                password_security_passed,
                f"Rejected {weak_password_count} weak passwords",
                "HIGH" if not password_security_passed else "LOW"
            )
            
            results["tests"].append({
                "name": "Password Strength Validation",
                "passed": password_security_passed,
                "details": f"Rejected {weak_password_count} weak passwords"
            })
            
        except Exception as e:
            self.log_test_result("Password Strength Validation", False, str(e), "HIGH")
        
        # Test 2: Account lockout after failed attempts
        try:
            username = "lockout_test_user"
            # First register a user
            self.client.post("/api/auth/register", json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!"
            })
            
            # Try multiple failed logins
            lockout_triggered = False
            for i in range(SECURITY_TEST_CONFIG["max_login_attempts"] + 2):
                response = self.client.post("/api/auth/login", data={
                    "username": username,
                    "password": "wrongpassword"
                })
                
                if response.status_code == 423:  # Locked
                    lockout_triggered = True
                    break
            
            self.log_test_result(
                "Account Lockout",
                lockout_triggered,
                f"Account locked after {i+1} failed attempts",
                "HIGH" if not lockout_triggered else "LOW"
            )
            
            results["tests"].append({
                "name": "Account Lockout",
                "passed": lockout_triggered,
                "details": f"Account locked after {i+1} failed attempts"
            })
            
        except Exception as e:
            self.log_test_result("Account Lockout", False, str(e), "HIGH")
        
        # Test 3: JWT token security
        try:
            # Login to get token
            login_response = self.client.post("/api/auth/login", data={
                "username": "lockout_test_user",
                "password": "StrongPassword123!"
            })
            
            if login_response.status_code == 200:
                token_data = login_response.json()["data"]
                access_token = token_data["access_token"]
                
                # Test token structure
                token_parts = access_token.split(".")
                jwt_structure_valid = len(token_parts) == 3
                
                # Test token expiration
                import jwt
                try:
                    payload = jwt.decode(access_token, options={"verify_signature": False})
                    has_exp = "exp" in payload
                    has_jti = "jti" in payload
                    has_iat = "iat" in payload
                    token_claims_valid = has_exp and has_jti and has_iat
                except:
                    token_claims_valid = False
                
                jwt_security_passed = jwt_structure_valid and token_claims_valid
                
                self.log_test_result(
                    "JWT Token Security",
                    jwt_security_passed,
                    f"Structure: {jwt_structure_valid}, Claims: {token_claims_valid}",
                    "HIGH" if not jwt_security_passed else "LOW"
                )
                
                results["tests"].append({
                    "name": "JWT Token Security",
                    "passed": jwt_security_passed,
                    "details": f"Structure: {jwt_structure_valid}, Claims: {token_claims_valid}"
                })
            
        except Exception as e:
            self.log_test_result("JWT Token Security", False, str(e), "HIGH")
        
        return results
    
    async def test_rate_limiting(self) -> Dict[str, Any]:
        """Test rate limiting protection."""
        results = {
            "category": "Rate Limiting",
            "tests": []
        }
        
        # Test 1: Login rate limiting
        try:
            username = "ratelimit_test_user"
            # Register user first
            self.client.post("/api/auth/register", json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!"
            })
            
            # Rapid login attempts
            rate_limited = False
            for i in range(10):  # More than typical rate limit
                response = self.client.post("/api/auth/login", data={
                    "username": username,
                    "password": "wrongpassword"
                })
                
                if response.status_code == 429:  # Too Many Requests
                    rate_limited = True
                    break
            
            self.log_test_result(
                "Login Rate Limiting",
                rate_limited,
                f"Rate limiting triggered after {i+1} attempts",
                "MEDIUM" if not rate_limited else "LOW"
            )
            
            results["tests"].append({
                "name": "Login Rate Limiting",
                "passed": rate_limited,
                "details": f"Rate limiting triggered after {i+1} attempts"
            })
            
        except Exception as e:
            self.log_test_result("Login Rate Limiting", False, str(e), "MEDIUM")
        
        # Test 2: Registration rate limiting
        try:
            rate_limited = False
            for i in range(5):  # More than typical registration rate limit
                response = self.client.post("/api/auth/register", json={
                    "username": f"ratelimit_user_{i}",
                    "email": f"ratelimit_user_{i}@example.com",
                    "password": "StrongPassword123!",
                    "confirm_password": "StrongPassword123!"
                })
                
                if response.status_code == 429:
                    rate_limited = True
                    break
            
            self.log_test_result(
                "Registration Rate Limiting",
                rate_limited,
                f"Registration rate limiting triggered after {i+1} attempts",
                "MEDIUM" if not rate_limited else "LOW"
            )
            
            results["tests"].append({
                "name": "Registration Rate Limiting",
                "passed": rate_limited,
                "details": f"Registration rate limiting triggered after {i+1} attempts"
            })
            
        except Exception as e:
            self.log_test_result("Registration Rate Limiting", False, str(e), "MEDIUM")
        
        return results
    
    async def test_input_validation(self) -> Dict[str, Any]:
        """Test input validation and XSS prevention."""
        results = {
            "category": "Input Validation",
            "tests": []
        }
        
        # Test 1: XSS injection attempts
        try:
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "<svg onload=alert('xss')>",
                "';alert('xss');//"
            ]
            
            xss_blocked = 0
            for payload in xss_payloads:
                response = self.client.post("/api/auth/register", json={
                    "username": f"xss_test_{hashlib.md5(payload.encode()).hexdigest()[:8]}",
                    "email": f"xss_test_{hashlib.md5(payload.encode()).hexdigest()[:8]}@example.com",
                    "password": "StrongPassword123!",
                    "confirm_password": "StrongPassword123!",
                    "full_name": payload  # Try to inject XSS in full name
                })
                
                # Check if XSS payload was sanitized/rejected
                if response.status_code != 200:
                    xss_blocked += 1
            
            xss_protection_passed = xss_blocked >= len(xss_payloads) // 2
            self.log_test_result(
                "XSS Protection",
                xss_protection_passed,
                f"Blocked {xss_blocked}/{len(xss_payloads)} XSS attempts",
                "HIGH" if not xss_protection_passed else "MEDIUM"
            )
            
            results["tests"].append({
                "name": "XSS Protection",
                "passed": xss_protection_passed,
                "details": f"Blocked {xss_blocked}/{len(xss_payloads)} XSS attempts"
            })
            
        except Exception as e:
            self.log_test_result("XSS Protection", False, str(e), "HIGH")
        
        # Test 2: SQL injection attempts
        try:
            sql_payloads = [
                "admin'--",
                "admin' OR '1'='1",
                "'; DROP TABLE users; --",
                "1' UNION SELECT * FROM users--",
                "admin'; INSERT INTO users VALUES('hacker','pass'); --"
            ]
            
            sql_blocked = 0
            for payload in sql_payloads:
                response = self.client.post("/api/auth/login", data={
                    "username": payload,
                    "password": "anypassword"
                })
                
                # SQL injection should not succeed
                if response.status_code != 200:
                    sql_blocked += 1
            
            sql_protection_passed = sql_blocked >= len(sql_payloads) // 2
            self.log_test_result(
                "SQL Injection Protection",
                sql_protection_passed,
                f"Blocked {sql_blocked}/{len(sql_payloads)} SQL injection attempts",
                "HIGH" if not sql_protection_passed else "MEDIUM"
            )
            
            results["tests"].append({
                "name": "SQL Injection Protection",
                "passed": sql_protection_passed,
                "details": f"Blocked {sql_blocked}/{len(sql_payloads)} SQL injection attempts"
            })
            
        except Exception as e:
            self.log_test_result("SQL Injection Protection", False, str(e), "HIGH")
        
        return results
    
    async def test_security_headers(self) -> Dict[str, Any]:
        """Test security headers implementation."""
        results = {
            "category": "Security Headers",
            "tests": []
        }
        
        # Test 1: Essential security headers
        try:
            response = self.client.get("/")
            headers = response.headers
            
            required_headers = [
                "x-content-type-options",
                "x-frame-options",
                "x-xss-protection",
                "referrer-policy"
            ]
            
            headers_present = 0
            missing_headers = []
            
            for header in required_headers:
                if header in headers:
                    headers_present += 1
                    # Validate header values
                    if header == "x-content-type-options" and headers[header].lower() != "nosniff":
                        missing_headers.append(f"{header} (invalid value: {headers[header]})")
                    elif header == "x-frame-options" and headers[header].upper() not in ["DENY", "SAMEORIGIN"]:
                        missing_headers.append(f"{header} (invalid value: {headers[header]})")
                else:
                    missing_headers.append(header)
            
            security_headers_passed = headers_present >= len(required_headers) - 1
            self.log_test_result(
                "Security Headers",
                security_headers_passed,
                f"Present: {headers_present}/{len(required_headers)}, Missing: {missing_headers}",
                "MEDIUM" if not security_headers_passed else "LOW"
            )
            
            results["tests"].append({
                "name": "Security Headers",
                "passed": security_headers_passed,
                "details": f"Present: {headers_present}/{len(required_headers)}, Missing: {missing_headers}"
            })
            
        except Exception as e:
            self.log_test_result("Security Headers", False, str(e), "MEDIUM")
        
        # Test 2: CORS configuration
        try:
            response = self.client.options("/", headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            })
            
            cors_headers = response.headers
            allowed_origin = cors_headers.get("access-control-allow-origin", "")
            
            # Check if wildcard CORS is not used in production-like scenarios
            cors_secure = allowed_origin != "*" or "localhost" in allowed_origin
            
            self.log_test_result(
                "CORS Configuration",
                cors_secure,
                f"Allowed origin: {allowed_origin}",
                "MEDIUM" if not cors_secure else "LOW"
            )
            
            results["tests"].append({
                "name": "CORS Configuration",
                "passed": cors_secure,
                "details": f"Allowed origin: {allowed_origin}"
            })
            
        except Exception as e:
            self.log_test_result("CORS Configuration", False, str(e), "MEDIUM")
        
        return results
    
    async def test_authorization(self) -> Dict[str, Any]:
        """Test role-based access control."""
        results = {
            "category": "Authorization",
            "tests": []
        }
        
        # Test 1: Protected endpoint access without token
        try:
            response = self.client.get("/api/auth/me")
            unauthorized_access = response.status_code == 401
            
            self.log_test_result(
                "Unauthorized Access Protection",
                unauthorized_access,
                f"Status code: {response.status_code}",
                "HIGH" if not unauthorized_access else "LOW"
            )
            
            results["tests"].append({
                "name": "Unauthorized Access Protection",
                "passed": unauthorized_access,
                "details": f"Status code: {response.status_code}"
            })
            
        except Exception as e:
            self.log_test_result("Unauthorized Access Protection", False, str(e), "HIGH")
        
        # Test 2: Admin endpoint protection
        try:
            # Register and login as regular user
            username = "regular_user"
            self.client.post("/api/auth/register", json={
                "username": username,
                "email": f"{username}@example.com",
                "password": "StrongPassword123!",
                "confirm_password": "StrongPassword123!"
            })
            
            login_response = self.client.post("/api/auth/login", data={
                "username": username,
                "password": "StrongPassword123!"
            })
            
            if login_response.status_code == 200:
                token = login_response.json()["data"]["access_token"]
                headers = {"Authorization": f"Bearer {token}"}
                
                # Try to access admin endpoint
                response = self.client.get("/api/auth/admin/users", headers=headers)
                admin_protected = response.status_code == 403
                
                self.log_test_result(
                    "Admin Endpoint Protection",
                    admin_protected,
                    f"Regular user access to admin endpoint: {response.status_code}",
                    "HIGH" if not admin_protected else "LOW"
                )
                
                results["tests"].append({
                    "name": "Admin Endpoint Protection",
                    "passed": admin_protected,
                    "details": f"Regular user access to admin endpoint: {response.status_code}"
                })
            
        except Exception as e:
            self.log_test_result("Admin Endpoint Protection", False, str(e), "HIGH")
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all security tests and return comprehensive report."""
        print("🔒 Starting Comprehensive Security Test Suite")
        print("=" * 60)
        
        # Run all test categories
        auth_results = await self.test_authentication_security()
        rate_limit_results = await self.test_rate_limiting()
        input_validation_results = await self.test_input_validation()
        headers_results = await self.test_security_headers()
        authz_results = await self.test_authorization()
        
        # Calculate overall security score
        all_tests = (
            auth_results["tests"] + 
            rate_limit_results["tests"] + 
            input_validation_results["tests"] + 
            headers_results["tests"] + 
            authz_results["tests"]
        )
        
        passed_tests = sum(1 for test in all_tests if test["passed"])
        total_tests = len(all_tests)
        security_score = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Generate risk assessment
        high_risk_failures = sum(1 for result in self.test_results 
                               if not result["passed"] and result["risk_level"] == "HIGH")
        medium_risk_failures = sum(1 for result in self.test_results 
                                  if not result["passed"] and result["risk_level"] == "MEDIUM")
        
        # Determine overall risk level
        if high_risk_failures > 0:
            overall_risk = "CRITICAL"
        elif medium_risk_failures > 2:
            overall_risk = "HIGH"
        elif medium_risk_failures > 0:
            overall_risk = "MEDIUM"
        else:
            overall_risk = "LOW"
        
        # Compile final report
        security_report = {
            "scan_timestamp": time.time(),
            "security_score": round(security_score, 1),
            "overall_risk": overall_risk,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "high_risk_failures": high_risk_failures,
                "medium_risk_failures": medium_risk_failures
            },
            "categories": {
                "authentication": auth_results,
                "rate_limiting": rate_limit_results,
                "input_validation": input_validation_results,
                "security_headers": headers_results,
                "authorization": authz_results
            },
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        # Print summary
        print(f"\n📊 Security Test Summary")
        print("=" * 60)
        print(f"Security Score: {security_score:.1f}%")
        print(f"Overall Risk: {overall_risk}")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"High Risk Failures: {high_risk_failures}")
        print(f"Medium Risk Failures: {medium_risk_failures}")
        
        return security_report
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations based on test results."""
        recommendations = []
        
        for result in self.test_results:
            if not result["passed"]:
                if "Password" in result["test_name"]:
                    recommendations.append(
                        "Implement stronger password validation with length, complexity, and common password checks"
                    )
                elif "Account Lockout" in result["test_name"]:
                    recommendations.append(
                        "Implement account lockout mechanism after failed login attempts to prevent brute force attacks"
                    )
                elif "JWT" in result["test_name"]:
                    recommendations.append(
                        "Ensure JWT tokens include proper claims (exp, iat, jti) and use strong signing secrets"
                    )
                elif "Rate Limiting" in result["test_name"]:
                    recommendations.append(
                        "Implement rate limiting on authentication endpoints to prevent credential stuffing attacks"
                    )
                elif "XSS" in result["test_name"]:
                    recommendations.append(
                        "Implement input sanitization and output encoding to prevent XSS attacks"
                    )
                elif "SQL Injection" in result["test_name"]:
                    recommendations.append(
                        "Use parameterized queries and input validation to prevent SQL injection attacks"
                    )
                elif "Security Headers" in result["test_name"]:
                    recommendations.append(
                        "Implement comprehensive security headers including CSP, HSTS, and X-Frame-Options"
                    )
                elif "Authorization" in result["test_name"]:
                    recommendations.append(
                        "Strengthen role-based access control and ensure proper endpoint protection"
                    )
        
        return list(set(recommendations))  # Remove duplicates

# Utility function to run security tests
async def run_security_audit(client: TestClient) -> Dict[str, Any]:
    """
    Run comprehensive security audit on the application.
    
    Args:
        client: TestClient instance
        
    Returns:
        Comprehensive security report
    """
    security_suite = SecurityTestSuite(client)
    return await security_suite.run_all_tests()

# Example usage
if __name__ == "__main__":
    from app.main_enhanced import app
    
    with TestClient(app) as client:
        report = asyncio.run(run_security_audit(client))
        
        # Save report to file
        with open("security_audit_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📋 Security audit report saved to security_audit_report.json")