"""
Test fixtures and data management utilities for ScrapeCraft testing framework.

This module provides:
- Mock data generators
- Test fixtures setup
- Database test utilities
- API response mocks
- Test data factories
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass, asdict
import random
import string


@dataclass
class MockUser:
    """Mock user data for testing."""
    id: str
    username: str
    email: str
    password_hash: str
    role: str
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class MockInvestigation:
    """Mock investigation data for testing."""
    id: str
    title: str
    description: str
    status: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()


@dataclass
class MockPipeline:
    """Mock pipeline data for testing."""
    id: str
    name: str
    description: str
    code: str
    user_id: str
    status: str = "draft"
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class MockOSINTResult:
    """Mock OSINT result data for testing."""
    id: str
    investigation_id: str
    source: str
    data: Dict[str, Any]
    confidence_score: float
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class TestDataFactory:
    """Factory for generating test data."""
    
    @staticmethod
    def random_string(length: int = 10) -> str:
        """Generate random string."""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    
    @staticmethod
    def random_email() -> str:
        """Generate random email address."""
        return f"{TestDataFactory.random_string(8)}@example.com"
    
    @staticmethod
    def create_user(
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
        role: str = "user"
    ) -> MockUser:
        """Create mock user data."""
        return MockUser(
            id=user_id or str(uuid.uuid4()),
            username=username or TestDataFactory.random_string(8),
            email=email or TestDataFactory.random_email(),
            password_hash="hashed_password_" + TestDataFactory.random_string(20),
            role=role
        )
    
    @staticmethod
    def create_investigation(
        investigation_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        status: str = "active",
        user_id: Optional[str] = None
    ) -> MockInvestigation:
        """Create mock investigation data."""
        return MockInvestigation(
            id=investigation_id or str(uuid.uuid4()),
            title=title or f"Test Investigation {TestDataFactory.random_string(5)}",
            description=description or "Test investigation description",
            status=status,
            user_id=user_id or str(uuid.uuid4())
        )
    
    @staticmethod
    def create_pipeline(
        pipeline_id: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
        code: Optional[str] = None,
        status: str = "draft",
        user_id: Optional[str] = None
    ) -> MockPipeline:
        """Create mock pipeline data."""
        return MockPipeline(
            id=pipeline_id or str(uuid.uuid4()),
            name=name or f"Test Pipeline {TestDataFactory.random_string(5)}",
            description=description or "Test pipeline description",
            code=code or "def test_pipeline():\n    return 'test_result'",
            status=status,
            user_id=user_id or str(uuid.uuid4())
        )
    
    @staticmethod
    def create_osint_result(
        result_id: Optional[str] = None,
        investigation_id: Optional[str] = None,
        source: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        confidence_score: float = 0.8
    ) -> MockOSINTResult:
        """Create mock OSINT result data."""
        return MockOSINTResult(
            id=result_id or str(uuid.uuid4()),
            investigation_id=investigation_id or str(uuid.uuid4()),
            source=source or "test_source",
            data=data or {"test": "data", "value": TestDataFactory.random_string()},
            confidence_score=confidence_score
        )
    
    @staticmethod
    def create_multiple_users(count: int = 5) -> List[MockUser]:
        """Create multiple mock users."""
        return [TestDataFactory.create_user() for _ in range(count)]
    
    @staticmethod
    def create_multiple_investigations(count: int = 5, user_id: Optional[str] = None) -> List[MockInvestigation]:
        """Create multiple mock investigations."""
        return [TestDataFactory.create_investigation(user_id=user_id) for _ in range(count)]


class APIResponseFactory:
    """Factory for creating API response mocks."""
    
    @staticmethod
    def success_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
        """Create success API response."""
        return {
            "status": "success",
            "status_code": status_code,
            "data": data,
            "message": "Operation completed successfully"
        }
    
    @staticmethod
    def error_response(message: str, status_code: int = 400, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Create error API response."""
        response = {
            "status": "error",
            "status_code": status_code,
            "message": message
        }
        if error_code:
            response["error_code"] = error_code
        return response
    
    @staticmethod
    def paginated_response(
        data: List[Any],
        page: int = 1,
        per_page: int = 10,
        total: Optional[int] = None
    ) -> Dict[str, Any]:
        """Create paginated API response."""
        if total is None:
            total = len(data)
        
        return {
            "status": "success",
            "data": data,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "pages": (total + per_page - 1) // per_page if total > 0 else 0
            }
        }
    
    @staticmethod
    def auth_response(user: MockUser, token: Optional[str] = None) -> Dict[str, Any]:
        """Create authentication response."""
        return {
            "status": "success",
            "data": {
                "user": asdict(user),
                "access_token": token or TestDataFactory.random_string(40),
                "token_type": "bearer",
                "expires_in": 3600
            }
        }


class DatabaseFixture:
    """Database test fixture utilities."""
    
    @staticmethod
    def create_test_database_url() -> str:
        """Create test database URL."""
        return "sqlite+aiosqlite:///:memory:"
    
    @staticmethod
    async def create_test_tables(async_engine):
        """Create test database tables."""
        # This would typically import your SQLAlchemy models and create tables
        # For now, it's a placeholder that would be implemented based on your models
        pass
    
    @staticmethod
    async def cleanup_test_database(async_engine):
        """Clean up test database."""
        # Drop all tables after tests
        pass


class WebSocketFixture:
    """WebSocket test fixture utilities."""
    
    @staticmethod
    def create_mock_websocket_message(message_type: str, data: Any) -> Dict[str, Any]:
        """Create mock WebSocket message."""
        return {
            "type": message_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "id": str(uuid.uuid4())
        }
    
    @staticmethod
    def create_investigation_update_message(investigation_id: str, status: str) -> Dict[str, Any]:
        """Create investigation status update message."""
        return WebSocketFixture.create_mock_websocket_message(
            "investigation_update",
            {
                "investigation_id": investigation_id,
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def create_pipeline_status_message(pipeline_id: str, status: str, result: Any = None) -> Dict[str, Any]:
        """Create pipeline status update message."""
        return WebSocketFixture.create_mock_websocket_message(
            "pipeline_status",
            {
                "pipeline_id": pipeline_id,
                "status": status,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )


class TestEnvironment:
    """Test environment setup utilities."""
    
    @staticmethod
    def setup_test_config() -> Dict[str, Any]:
        """Setup test configuration."""
        return {
            "database": {
                "url": DatabaseFixture.create_test_database_url(),
                "echo": False
            },
            "redis": {
                "url": "redis://localhost:6379/1",
                "decode_responses": True
            },
            "auth": {
                "jwt_secret_key": "test_secret_key",
                "jwt_algorithm": "HS256",
                "access_token_expire_minutes": 30
            },
            "logging": {
                "level": "DEBUG",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
    
    @staticmethod
    def get_test_headers(access_token: Optional[str] = None) -> Dict[str, str]:
        """Get test HTTP headers."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        return headers


# Mock data constants
MOCK_USERS = [
    MockUser(
        id="user-1",
        username="testuser1",
        email="user1@example.com",
        password_hash="hash1",
        role="user"
    ),
    MockUser(
        id="user-2",
        username="admin",
        email="admin@example.com",
        password_hash="admin_hash",
        role="admin"
    )
]

MOCK_INVESTIGATIONS = [
    MockInvestigation(
        id="inv-1",
        title="Test Investigation 1",
        description="First test investigation",
        status="active",
        user_id="user-1"
    ),
    MockInvestigation(
        id="inv-2",
        title="Test Investigation 2",
        description="Second test investigation",
        status="completed",
        user_id="user-2"
    )
]

# Export commonly used test data
__all__ = [
    'TestDataFactory',
    'APIResponseFactory',
    'DatabaseFixture',
    'WebSocketFixture',
    'TestEnvironment',
    'MockUser',
    'MockInvestigation',
    'MockPipeline',
    'MockOSINTResult',
    'MOCK_USERS',
    'MOCK_INVESTIGATIONS'
]