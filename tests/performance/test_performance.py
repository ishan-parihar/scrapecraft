"""
Performance and Load Testing Suite

Tests system performance under various load conditions.
"""

import pytest
import asyncio
import time
import psutil
import gc
from typing import Dict, List, Any
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
from datetime import datetime

from tests.conftest import (
    test_client, async_test_client, performance_helper,
    sample_user_data, sample_investigation_data
)

class TestAPIPerformance:
    """Test API endpoint performance."""
    
    @pytest.mark.performance
    def test_api_response_times(self, test_client):
        """Test API response times are within acceptable limits."""
        
        # Test endpoints that should be fast
        fast_endpoints = [
            ("GET", "/api/health"),
            ("GET", "/api/health/detailed"),
        ]
        
        for method, endpoint in fast_endpoints:
            start_time = time.time()
            
            if method == "GET":
                response = test_client.get(endpoint)
            else:
                response = test_client.post(endpoint, json={})
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # API responses should be under 2 seconds
            assert response_time < 2000, f"{method} {endpoint} took {response_time:.2f}ms"
            print(f"✅ {method} {endpoint}: {response_time:.2f}ms")
    
    @pytest.mark.performance
    async def test_concurrent_api_requests(self, async_test_client, performance_helper):
        """Test API performance under concurrent load."""
        
        async def make_api_request(endpoint_info):
            """Make API request and measure performance."""
            method, endpoint, data = endpoint_info
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = await async_test_client.get(endpoint)
                elif method == "POST":
                    response = await async_test_client.post(endpoint, json=data)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                end_time = time.time()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000,
                    "endpoint": endpoint
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": (end_time - start_time) * 1000,
                    "endpoint": endpoint
                }
        
        # Define API endpoints to test
        api_endpoints = [
            ("GET", "/api/health", None),
            ("GET", "/api/health/detailed", None),
            ("GET", "/api/investigations", None),
            ("POST", "/api/investigations", sample_investigation_data()),
        ]
        
        # Create test arguments for concurrent execution
        args_list = [(endpoint,) for endpoint in api_endpoints]
        
        # Run concurrent API requests
        metrics = await performance_helper.run_concurrent_requests(
            make_api_request,
            args_list,
            concurrency=5
        )
        
        # Analyze performance metrics
        assert metrics["success_rate"] >= 0.8, f"Success rate too low: {metrics['success_rate']}"
        assert metrics["avg_response_time"] < 5000, f"Average response time too high: {metrics['avg_response_time']}ms"
        assert metrics["p95_response_time"] < 10000, f"P95 response time too high: {metrics['p95_response_time']}ms"
        
        print(f"✅ Concurrent API Performance:")
        print(f"   Success Rate: {metrics['success_rate']:.2%}")
        print(f"   Avg Response Time: {metrics['avg_response_time']:.2f}ms")
        print(f"   P95 Response Time: {metrics['p95_response_time']:.2f}ms")
        print(f"   Requests/Second: {metrics['requests_per_second']:.2f}")
    
    @pytest.mark.performance
    def test_memory_usage_during_requests(self, test_client):
        """Test memory usage during API requests."""
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make multiple requests
        for _ in range(100):
            response = test_client.get("/api/health")
            assert response.status_code in [200, 401]  # Accept both for test
        
        # Check memory usage after requests
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50, f"Memory increased by {memory_increase:.2f}MB"
        
        # Force garbage collection
        gc.collect()
        
        # Check memory after garbage collection
        post_gc_memory = process.memory_info().rss / 1024 / 1024  # MB
        post_gc_increase = post_gc_memory - initial_memory
        
        assert post_gc_increase < 30, f"Memory after GC still high: {post_gc_increase:.2f}MB"
        
        print(f"✅ Memory Usage Test:")
        print(f"   Initial: {initial_memory:.2f}MB")
        print(f"   Final: {final_memory:.2f}MB")
        print(f"   Increase: {memory_increase:.2f}MB")
        print(f"   After GC: {post_gc_memory:.2f}MB")

class TestDatabasePerformance:
    """Test database performance under load."""
    
    @pytest.mark.performance
    async def test_concurrent_database_operations(self, setup_test_environment, performance_helper):
        """Test database performance with concurrent operations."""
        
        db = setup_test_environment["database"]
        
        async def database_operation(operation_info):
            """Perform database operation and measure performance."""
            operation_type, data = operation_info
            start_time = time.time()
            
            try:
                async for session in db.get_async_session():
                    if operation_type == "create":
                        # Mock create operation
                        await asyncio.sleep(0.01)  # Simulate DB operation
                        result = {"id": f"test_{time.time()}", "status": "created"}
                    elif operation_type == "read":
                        # Mock read operation
                        await asyncio.sleep(0.005)  # Simulate DB read
                        result = {"id": data, "status": "read"}
                    elif operation_type == "update":
                        # Mock update operation
                        await asyncio.sleep(0.01)  # Simulate DB update
                        result = {"id": data, "status": "updated"}
                    else:
                        raise ValueError(f"Unknown operation: {operation_type}")
                    
                    end_time = time.time()
                    return {
                        "success": True,
                        "operation": operation_type,
                        "response_time": (end_time - start_time) * 1000,
                        "result": result
                    }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "operation": operation_type,
                    "error": str(e),
                    "response_time": (end_time - start_time) * 1000
                }
        
        # Define database operations to test
        db_operations = [
            ("create", None),
            ("read", "test_1"),
            ("update", "test_1"),
            ("create", None),
            ("read", "test_2"),
            ("update", "test_2"),
        ] * 10  # Repeat for more load
        
        # Create test arguments
        args_list = [(op,) for op in db_operations]
        
        # Run concurrent database operations
        metrics = await performance_helper.run_concurrent_requests(
            database_operation,
            args_list,
            concurrency=5
        )
        
        # Database operations should be reasonably fast
        assert metrics["success_rate"] >= 0.9, f"DB success rate too low: {metrics['success_rate']}"
        assert metrics["avg_response_time"] < 100, f"DB avg response time too high: {metrics['avg_response_time']}ms"
        
        print(f"✅ Database Performance:")
        print(f"   Success Rate: {metrics['success_rate']:.2%}")
        print(f"   Avg Response Time: {metrics['avg_response_time']:.2f}ms")
        print(f"   Operations/Second: {metrics['requests_per_second']:.2f}")
    
    @pytest.mark.performance
    async def test_database_connection_pool(self, setup_test_environment):
        """Test database connection pool performance."""
        
        db = setup_test_environment["database"]
        
        # Test multiple concurrent sessions
        async def create_session():
            start_time = time.time()
            try:
                async for session in db.get_async_session():
                    # Simulate some work
                    await asyncio.sleep(0.01)
                    break  # Just test connection acquisition
                
                end_time = time.time()
                return {
                    "success": True,
                    "response_time": (end_time - start_time) * 1000
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": (end_time - start_time) * 1000
                }
        
        # Create multiple concurrent sessions
        tasks = [create_session() for _ in range(20)]
        results = await asyncio.gather(*tasks)
        
        # Analyze results
        successful_sessions = [r for r in results if r["success"]]
        response_times = [r["response_time"] for r in successful_sessions]
        
        assert len(successful_sessions) >= 18, f"Too many failed sessions: {len(successful_sessions)}/20"
        assert sum(response_times) / len(response_times) < 50, "Connection acquisition too slow"
        
        print(f"✅ Connection Pool Performance:")
        print(f"   Successful Sessions: {len(successful_sessions)}/20")
        print(f"   Avg Connection Time: {sum(response_times) / len(response_times):.2f}ms")

class TestLLMServicePerformance:
    """Test LLM service performance and resource usage."""
    
    @pytest.mark.performance
    async def test_llm_concurrent_requests(self, mock_llm_service, performance_helper):
        """Test LLM service performance with concurrent requests."""
        
        async def llm_request(request_data):
            """Make LLM request and measure performance."""
            prompt, expected_response = request_data
            start_time = time.time()
            
            try:
                # Set expected response
                mock_llm_service.set_response(prompt, expected_response)
                
                # Make request
                messages = [{"role": "user", "content": prompt}]
                response = await mock_llm_service.ainvoke(messages)
                
                end_time = time.time()
                return {
                    "success": True,
                    "response_time": (end_time - start_time) * 1000,
                    "response": response.content,
                    "prompt": prompt
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "error": str(e),
                    "response_time": (end_time - start_time) * 1000,
                    "prompt": prompt
                }
        
        # Define LLM requests to test
        llm_requests = [
            ("Analyze this security threat", "Threat analysis completed"),
            ("Generate investigation plan", "Investigation plan generated"),
            ("Summarize findings", "Findings summarized"),
            ("Recommend next steps", "Next steps recommended"),
            ("Assess risk level", "Risk level assessed"),
        ] * 5  # Repeat for load testing
        
        # Create test arguments
        args_list = [(request,) for request in llm_requests]
        
        # Run concurrent LLM requests
        metrics = await performance_helper.run_concurrent_requests(
            llm_request,
            args_list,
            concurrency=3
        )
        
        # LLM requests should complete successfully
        assert metrics["success_rate"] >= 0.9, f"LLM success rate too low: {metrics['success_rate']}"
        assert metrics["avg_response_time"] < 500, f"LLM avg response time too high: {metrics['avg_response_time']}ms"
        
        print(f"✅ LLM Service Performance:")
        print(f"   Success Rate: {metrics['success_rate']:.2%}")
        print(f"   Avg Response Time: {metrics['avg_response_time']:.2f}ms")
        print(f"   Requests/Second: {metrics['requests_per_second']:.2f}")
    
    @pytest.mark.performance
    def test_llm_memory_usage(self, mock_llm_service):
        """Test LLM service memory usage."""
        
        # Get initial memory usage
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many LLM requests
        async def make_many_requests():
            for i in range(50):
                prompt = f"Test prompt {i}"
                mock_llm_service.set_response(prompt, f"Response {i}")
                
                messages = [{"role": "user", "content": prompt}]
                await mock_llm_service.ainvoke(messages)
        
        # Run the requests
        asyncio.run(make_many_requests())
        
        # Check memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable
        assert memory_increase < 20, f"LLM service memory increased by {memory_increase:.2f}MB"
        
        print(f"✅ LLM Memory Usage:")
        print(f"   Initial: {initial_memory:.2f}MB")
        print(f"   Final: {final_memory:.2f}MB")
        print(f"   Increase: {memory_increase:.2f}MB")

class TestWebSocketPerformance:
    """Test WebSocket performance under load."""
    
    @pytest.mark.performance
    async def test_websocket_concurrent_connections(self, async_test_client, performance_helper):
        """Test WebSocket performance with multiple concurrent connections."""
        
        async def websocket_connection(connection_info):
            """Simulate WebSocket connection and measure performance."""
            connection_id, message_count = connection_info
            start_time = time.time()
            
            try:
                # Mock WebSocket connection
                with patch('app.services.websocket.ConnectionManager') as mock_manager:
                    mock_manager_instance = AsyncMock()
                    mock_manager_instance.connect = AsyncMock()
                    mock_manager_instance.broadcast = AsyncMock()
                    mock_manager.return_value = mock_manager_instance
                    
                    # Simulate sending messages
                    for i in range(message_count):
                        await mock_manager_instance.broadcast({
                            "type": "test_message",
                            "connection_id": connection_id,
                            "message": f"Message {i}",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        await asyncio.sleep(0.001)  # Small delay
                
                end_time = time.time()
                return {
                    "success": True,
                    "connection_id": connection_id,
                    "messages_sent": message_count,
                    "response_time": (end_time - start_time) * 1000
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "connection_id": connection_id,
                    "error": str(e),
                    "response_time": (end_time - start_time) * 1000
                }
        
        # Define WebSocket connections to test
        websocket_connections = [
            (f"conn_{i}", 10) for i in range(15)  # 15 connections, 10 messages each
        ]
        
        # Create test arguments
        args_list = [(conn,) for conn in websocket_connections]
        
        # Run concurrent WebSocket connections
        metrics = await performance_helper.run_concurrent_requests(
            websocket_connection,
            args_list,
            concurrency=5
        )
        
        # WebSocket connections should perform well
        assert metrics["success_rate"] >= 0.9, f"WebSocket success rate too low: {metrics['success_rate']}"
        
        print(f"✅ WebSocket Performance:")
        print(f"   Success Rate: {metrics['success_rate']:.2%}")
        print(f"   Avg Connection Time: {metrics['avg_response_time']:.2f}ms")
        print(f"   Total Messages: {sum(r.get('messages_sent', 0) for r in metrics.get('tests', []))}")

class TestStressTesting:
    """Stress testing for system limits."""
    
    @pytest.mark.performance
    @pytest.mark.slow
    async def test_high_load_scenario(self, async_test_client, performance_helper):
        """Test system under high load scenario."""
        
        async def mixed_request(request_info):
            """Handle mixed request types under stress."""
            request_type, data = request_info
            start_time = time.time()
            
            try:
                if request_type == "health_check":
                    response = await async_test_client.get("/api/health")
                elif request_type == "create_investigation":
                    with patch('app.api.investigations.get_current_user') as mock_user:
                        mock_user.return_value = {"id": 1, "username": "testuser"}
                        response = await async_test_client.post("/api/investigations", json=data)
                elif request_type == "get_investigations":
                    with patch('app.api.investigations.get_current_user') as mock_user:
                        mock_user.return_value = {"id": 1, "username": "testuser"}
                        response = await async_test_client.get("/api/investigations")
                else:
                    raise ValueError(f"Unknown request type: {request_type}")
                
                end_time = time.time()
                return {
                    "success": True,
                    "request_type": request_type,
                    "status_code": response.status_code,
                    "response_time": (end_time - start_time) * 1000
                }
            except Exception as e:
                end_time = time.time()
                return {
                    "success": False,
                    "request_type": request_type,
                    "error": str(e),
                    "response_time": (end_time - start_time) * 1000
                }
        
        # Create high load scenario with mixed requests
        stress_requests = []
        
        # Add health checks (lightweight)
        for _ in range(30):
            stress_requests.append(("health_check", None))
        
        # Add investigation operations (heavier)
        for _ in range(20):
            stress_requests.append(("create_investigation", sample_investigation_data()))
            stress_requests.append(("get_investigations", None))
        
        # Create test arguments
        args_list = [(req,) for req in stress_requests]
        
        # Run stress test with higher concurrency
        metrics = await performance_helper.run_concurrent_requests(
            mixed_request,
            args_list,
            concurrency=10
        )
        
        # System should handle stress reasonably well
        assert metrics["success_rate"] >= 0.7, f"Stress test success rate too low: {metrics['success_rate']}"
        assert metrics["avg_response_time"] < 10000, f"Stress test avg response time too high: {metrics['avg_response_time']}ms"
        
        print(f"✅ Stress Test Results:")
        print(f"   Total Requests: {metrics['total_requests']}")
        print(f"   Success Rate: {metrics['success_rate']:.2%}")
        print(f"   Avg Response Time: {metrics['avg_response_time']:.2f}ms")
        print(f"   P95 Response Time: {metrics['p95_response_time']:.2f}ms")
        print(f"   Requests/Second: {metrics['requests_per_second']:.2f}")
    
    @pytest.mark.performance
    def test_memory_leak_detection(self, test_client):
        """Test for memory leaks during extended usage."""
        
        process = psutil.Process()
        memory_readings = []
        
        # Perform multiple rounds of requests
        for round_num in range(10):
            # Make requests
            for _ in range(20):
                test_client.get("/api/health")
            
            # Force garbage collection
            gc.collect()
            
            # Record memory usage
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_readings.append(memory_mb)
            
            print(f"Round {round_num + 1}: {memory_mb:.2f}MB")
        
        # Check for memory leaks
        initial_memory = memory_readings[0]
        final_memory = memory_readings[-1]
        memory_increase = final_memory - initial_memory
        
        # Memory should not grow continuously
        max_memory = max(memory_readings)
        min_memory = min(memory_readings[1:])  # Exclude initial reading
        
        # Memory growth should be minimal
        assert memory_increase < 10, f"Potential memory leak: {memory_increase:.2f}MB increase"
        assert (max_memory - min_memory) < 15, f"Memory variance too high: {max_memory - min_memory:.2f}MB"
        
        print(f"✅ Memory Leak Test:")
        print(f"   Initial: {initial_memory:.2f}MB")
        print(f"   Final: {final_memory:.2f}MB")
        print(f"   Increase: {memory_increase:.2f}MB")
        print(f"   Variance: {max_memory - min_memory:.2f}MB")

class TestPerformanceRegression:
    """Test for performance regressions."""
    
    @pytest.mark.performance
    def test_api_regression_baseline(self, test_client):
        """Establish baseline performance metrics for regression testing."""
        
        # Define baseline expectations (in milliseconds)
        baseline_expectations = {
            "/api/health": {"max_response_time": 100, "avg_response_time": 50},
            "/api/health/detailed": {"max_response_time": 200, "avg_response_time": 100},
            "/api/investigations": {"max_response_time": 500, "avg_response_time": 250},
        }
        
        results = {}
        
        for endpoint, expectations in baseline_expectations.items():
            response_times = []
            
            # Make multiple requests to get average
            for _ in range(10):
                start_time = time.time()
                response = test_client.get(endpoint)
                end_time = time.time()
                
                response_times.append((end_time - start_time) * 1000)
            
            avg_time = sum(response_times) / len(response_times)
            max_time = max(response_times)
            
            results[endpoint] = {
                "avg_response_time": avg_time,
                "max_response_time": max_time,
                "expected_avg": expectations["avg_response_time"],
                "expected_max": expectations["max_response_time"]
            }
            
            # Check against baseline
            assert avg_time <= expectations["avg_response_time"] * 1.5, f"{endpoint} avg time regression: {avg_time:.2f}ms"
            assert max_time <= expectations["max_response_time"] * 2, f"{endpoint} max time regression: {max_time:.2f}ms"
        
        print(f"✅ Performance Baseline Results:")
        for endpoint, metrics in results.items():
            print(f"   {endpoint}:")
            print(f"     Avg: {metrics['avg_response_time']:.2f}ms (expected: {metrics['expected_avg']}ms)")
            print(f"     Max: {metrics['max_response_time']:.2f}ms (expected: {metrics['expected_max']}ms)")

if __name__ == "__main__":
    print("Performance and Load Testing Suite")
    print("=" * 50)
    print("Testing system performance under load...")
    print("Run with: pytest tests/performance/test_performance.py -v -m performance")