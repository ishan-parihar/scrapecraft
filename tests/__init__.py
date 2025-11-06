"""
Comprehensive Testing Framework for ScrapeCraft OSINT Platform

This framework provides:
- Unit tests for individual components
- Integration tests for component interactions
- End-to-end tests for complete user workflows
- Performance and load testing
- Security testing
- Test fixtures and utilities
- CI/CD integration helpers

Phase 3.2 Implementation: Comprehensive Testing Framework
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))
sys.path.insert(0, str(project_root / "frontend"))

# Test configuration
TEST_CONFIG = {
    "database": {
        "test_url": "sqlite+aiosqlite:///:memory:",
        "migrations_path": "backend/migrations"
    },
    "redis": {
        "test_db": 1,
        "test_url": "redis://localhost:6379/1"
    },
    "llm": {
        "test_provider": "mock",
        "test_model": "test-model",
        "mock_responses": True
    },
    "performance": {
        "load_test_concurrency": 10,
        "load_test_duration": 60,
        "stress_test_multiplier": 2
    },
    "coverage": {
        "minimum_threshold": 80,
        "exclude_paths": ["tests/", "migrations/", "__pycache__/"]
    }
}

# Test categories
TEST_CATEGORIES = {
    "unit": "Tests for individual functions and classes",
    "integration": "Tests for component interactions",
    "e2e": "End-to-end workflow tests",
    "performance": "Load and stress testing",
    "security": "Authentication and authorization testing"
}

# Critical user flows for E2E testing
CRITICAL_FLOWS = {
    "investigation_workflow": {
        "description": "Complete investigation from creation to reporting",
        "steps": [
            "User authentication",
            "Investigation creation", 
            "AI planning with LLM",
            "Data collection",
            "Analysis and reporting"
        ]
    },
    "authentication_flow": {
        "description": "User authentication and session management",
        "steps": [
            "User registration",
            "Email verification",
            "Login with JWT",
            "Token refresh",
            "Logout"
        ]
    },
    "pipeline_execution": {
        "description": "Pipeline creation and execution",
        "steps": [
            "Pipeline creation",
            "Code generation",
            "Execution",
            "Results storage",
            "Error handling"
        ]
    },
    "data_persistence": {
        "description": "Database operations and data integrity",
        "steps": [
            "Database operations",
            "Transaction handling",
            "Backup/restore",
            "Data integrity checks"
        ]
    }
}

# API endpoints to test
API_ENDPOINTS = {
    "auth": [
        "POST /api/auth/register",
        "POST /api/auth/login",
        "POST /api/auth/refresh",
        "POST /api/auth/logout"
    ],
    "investigations": [
        "GET /api/investigations",
        "POST /api/investigations",
        "GET /api/investigations/{id}",
        "PUT /api/investigations/{id}",
        "DELETE /api/investigations/{id}"
    ],
    "ai_investigation": [
        "POST /api/ai-investigation/start",
        "GET /api/ai-investigation/status/{id}",
        "POST /api/ai-investigation/stop/{id}"
    ],
    "osint": [
        "POST /api/osint/collect",
        "GET /api/osint/results/{id}",
        "GET /api/osint/sources"
    ],
    "pipelines": [
        "GET /api/pipelines",
        "POST /api/pipelines",
        "POST /api/pipelines/{id}/execute",
        "GET /api/pipelines/{id}/status"
    ],
    "scraping": [
        "POST /api/scraping/start",
        "GET /api/scraping/status/{id}",
        "GET /api/scraping/results/{id}"
    ]
}

# Frontend components to test
FRONTEND_COMPONENTS = {
    "auth": ["Login", "Register", "PasswordReset"],
    "chat": ["ChatContainer", "MessageBubble", "InputArea"],
    "osint": ["InvestigationPlanner", "AnalysisView", "EvidenceViewer"],
    "workflow": ["AgentCoordinator", "ApprovalDialog", "WorkflowSidebar"],
    "pipeline": ["PipelinePanel", "CodeViewer", "OutputDisplay"],
    "common": ["Button", "Input", "LoadingSpinner", "ClassificationBanner"]
}

if __name__ == "__main__":
    print("ScrapeCraft Testing Framework")
    print("=" * 40)
    print(f"Test Categories: {list(TEST_CATEGORIES.keys())}")
    print(f"Critical Flows: {list(CRITICAL_FLOWS.keys())}")
    print(f"API Endpoints: {sum(len(endpoints) for endpoints in API_ENDPOINTS.values())}")
    print(f"Frontend Components: {sum(len(components) for components in FRONTEND_COMPONENTS.values())}")
    print("Framework initialized successfully! ✅")