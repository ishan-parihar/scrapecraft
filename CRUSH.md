# ScrapeCraft OSINT Platform - Development Guide

## Project Overview

ScrapeCraft is a comprehensive OSINT (Open Source Intelligence) platform that combines automated web scraping, AI-powered analysis, and real-time investigation workflows. The system consists of a FastAPI backend with specialized agents, a React/TypeScript frontend, and supporting infrastructure for scalable deployments.

## Architecture

### Backend (FastAPI + Python 3.11)
- **Framework**: FastAPI with async/await patterns
- **Database**: PostgreSQL with SQLAlchemy ORM, SQLite for development
- **Caching**: Redis for task storage and real-time data
- **AI/LLM**: Multiple providers (OpenRouter, OpenAI, Custom), LangChain integration
- **Web Scraping**: ScrapeGraphAI, BeautifulSoup4, custom scraping services
- **Authentication**: JWT-based with role-based access control (RBAC)
- **Real-time**: WebSocket connections for live investigation updates

### Frontend (React 18 + TypeScript)
- **Framework**: React with functional components and hooks
- **State Management**: Zustand stores for investigation, chat, workflow states
- **UI**: Tailwind CSS with custom components
- **Real-time**: WebSocket integration with fallback polling
- **Routing**: React Router v7.9.5

### Agent System
- **Base Classes**: `OSINTAgent` with standardized configuration and results
- **Specialized Agents**: Collection, Analysis, Synthesis, Planning, Coordination
- **Registry**: Dynamic agent discovery and management
- **Legacy Support**: Backward compatibility with existing agent implementations

## Essential Commands

### Development Environment
```bash
# Start full stack
docker-compose up -d

# Backend only
cd backend
python dev_server.py                    # Development server (uvicorn with reload)
python simple_main.py                   # Minimal server for testing

# Frontend only
cd frontend
npm start                               # Development server on port 3000
npm run build                           # Production build
```

### Backend Commands
```bash
cd backend

# Testing
pytest -v                              # Run all tests
pytest tests/unit/ -v                   # Unit tests only
pytest tests/integration/ -v            # Integration tests
pytest tests/security/ -v               # Security tests
pytest tests/e2e/ -v                    # End-to-end tests
pytest tests/test_specific.py::test_method -v  # Single test method

# Code Quality
black .                                 # Format code (line length 88)
ruff check .                            # Lint code
ruff format .                           # Format with ruff
isort .                                 # Sort imports
mypy .                                  # Type checking (strict mode)
bandit -r app/                          # Security linting

# Database
alembic upgrade head                    # Apply migrations
alembic revision --autogenerate -m "message"  # Create migration
```

### Frontend Commands
```bash
cd frontend

# Testing
npm test                                # Run all tests
npm test -- --testPathPattern=specific.test  # Single test file
npm run test:coverage                   # Coverage report
npm run test:ci                         # CI testing

# Code Quality
npm run lint                            # ESLint
npm run lint:fix                        # Auto-fix linting
npm run format                          # Prettier formatting
npm run format:check                    # Check formatting
npm run type-check                      # TypeScript checking

# Build
npm run build                           # Production build
```

### CLI Tools
```bash
python osint_cli.py --help             # Test CLI functionality
python -m pytest -v                    # Run tests from project root
```

## Code Style & Conventions

### Python
- **Formatting**: Black (line length 88)
- **Linting**: Ruff (comprehensive linting)
- **Imports**: isort (stdlib → third-party → local)
- **Type Checking**: mypy with strict mode
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Async Patterns**: Use `async/await`, proper error propagation
- **Error Handling**: Structured logging with timestamps, comprehensive try/catch

### TypeScript/React
- **Components**: Functional components with hooks only
- **Types**: Strict TypeScript, prefer `interface` over `type`
- **Naming**: `PascalCase` for components/types, `camelCase` for variables
- **Imports**: React imports first, then third-party, then local
- **State**: Zustand for global state, local state for component-specific data

### File Organization
```
backend/
├── app/
│   ├── api/           # API route handlers
│   ├── models/        # Pydantic models + SQLAlchemy models
│   ├── services/      # Business logic and external integrations
│   ├── agents/        # OSINT agent system
│   ├── middleware/    # FastAPI middleware
│   └── security/      # Authentication and authorization
├── tests/             # Test suite (unit, integration, e2e)
└── migrations/        # Database migrations

frontend/
├── src/
│   ├── components/    # React components organized by feature
│   ├── services/      # API clients and external services
│   ├── store/         # Zustand state management
│   ├── hooks/         # Custom React hooks
│   └── types/         # TypeScript type definitions
```

## Key Patterns & Gotchas

### LLM Integration
- **Service Location**: `app/services/llm_integration.py`
- **Providers**: OpenRouter (default), OpenAI, Custom LLM
- **Response Parsing**: Robust JSON parsing with structured text fallback
- **Timeouts**: 30s for complex analysis, 1000 token limit for speed
- **Error Handling**: Graceful degradation to mock responses when needed

### WebSocket Architecture
- **Backend Endpoint**: `/api/osint/ws/{investigation_id}`
- **Frontend Connection**: Through `websocketStore.ts`
- **Fallback**: HTTP polling when WebSocket fails
- **Real-time Updates**: Investigation progress, agent status, task completion

### Agent System
- **Base Class**: `OSINTAgent` in `app/agents/base/osint_agent.py`
- **Configuration**: `AgentConfig` with standardized settings
- **Results**: `AgentResult` with confidence scores and metadata
- **Registry**: Dynamic agent discovery in `app/agents/registry.py`
- **Specialization**: Collection → Analysis → Synthesis workflow

### Database Patterns
- **ORM**: SQLAlchemy 2.0 with async support
- **Models**: Pydantic for API, SQLAlchemy for persistence
- **Migrations**: Alembic with version control
- **Testing**: Separate test databases, fixtures in `tests/fixtures/`

### Security Considerations
- **Authentication**: JWT tokens with configurable expiration
- **Authorization**: RBAC with role-based permissions
- **Input Validation**: Pydantic models at API boundaries
- **Environment**: Secrets in `.env` files, never in code
- **CORS**: Configured for development origins

## Testing Strategy

### Test Organization
- **Unit Tests**: Individual functions and classes (`tests/unit/`)
- **Integration Tests**: API endpoints and service interactions (`tests/integration/`)
- **E2E Tests**: Complete user workflows (`tests/e2e/`)
- **Security Tests**: Authentication and authorization (`tests/security/`)
- **Performance Tests**: Load and timing (`tests/performance/`)

### Coverage Requirements
- **Minimum**: 80% code coverage across all modules
- **Backend**: pytest with coverage reporting
- **Frontend**: Jest with coverage thresholds
- **CI/CD**: Automated testing on all PRs and pushes

### Test Data
- **Fixtures**: Standardized test data in `tests/fixtures/`
- **Mocks**: External services mocked for reliability
- **Database**: In-memory or test databases isolated from production

## Configuration Management

### Environment Variables
- **Development**: `.env` files in project root and service directories
- **Production**: Environment variables or secret management
- **Docker**: Environment variables in `docker-compose.yml`

### Key Settings
- **Database**: `DATABASE_URL` (PostgreSQL for production, SQLite for dev)
- **LLM**: `OPENROUTER_API_KEY`, `OPENAI_API_KEY`, `LLM_PROVIDER`
- **Security**: `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRATION_HOURS`
- **Scraping**: `ENABLE_REAL_SCRAPING`, `SCRAPE_DELAY_SECONDS`, `MAX_CONCURRENT_REQUESTS`

## Deployment & Infrastructure

### Docker Setup
- **Multi-service**: Backend, frontend, PostgreSQL, Redis
- **Development**: Volume mounts for code reloading
- **Production**: Optimized builds without development dependencies
- **Optional**: Ollama service for local LLM inference

### Kubernetes
- **Deployments**: Separate deployments for backend and frontend
- **Services**: Load balancers and internal service communication
- **ConfigMaps**: Configuration management
- **Secrets**: Sensitive data management

### Monitoring & Logging
- **Health Checks**: `/health` endpoints for all services
- **Structured Logging**: JSON format with timestamps and correlation IDs
- **Error Tracking**: Comprehensive error logging and reporting
- **Performance**: Metrics collection and monitoring

## Common Issues & Solutions

### LLM Integration Issues
- **Timeout Errors**: Increase timeout in `llm_integration.py` or reduce prompt complexity
- **Parsing Failures**: Check response format, fallback to structured text parsing
- **API Limits**: Implement rate limiting and token counting

### WebSocket Connection Problems
- **URL Mismatch**: Ensure frontend connects to `/api/osint/ws/{investigation_id}`
- **CORS Issues**: Check `CORS_ORIGINS` configuration
- **Connection Drops**: Implement reconnection logic with exponential backoff

### Agent System Errors
- **Import Issues**: Check circular imports, use lazy imports where needed
- **Configuration**: Ensure `AgentConfig` is properly initialized
- **Registry**: Verify agents are properly registered before use

### Database Connection Issues
- **Migration Lag**: Run `alembic upgrade head` after schema changes
- **Connection Pooling**: Adjust pool size for high-load scenarios
- **Test Isolation**: Use separate test databases to avoid conflicts

## Development Workflow

### Getting Started
1. Clone repository and install dependencies
2. Copy `.env.example` to `.env` and configure variables
3. Run `docker-compose up -d` for full stack or start services individually
4. Run migrations: `cd backend && alembic upgrade head`
5. Access frontend at `http://localhost:3000`, backend at `http://localhost:8000`

### Making Changes
1. Create feature branch from `main` or `develop`
2. Make changes with proper test coverage
3. Run linting and formatting tools
4. Test manually and with automated test suite
5. Submit PR with comprehensive description

### Code Review Checklist
- [ ] Tests pass with adequate coverage
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Security considerations addressed
- [ ] Performance impact assessed
- [ ] Breaking changes documented

## Resources & Documentation

### Internal Documentation
- **API Documentation**: Auto-generated at `/docs` endpoint
- **Agent Architecture**: See `app/agents/` directory and base classes
- **Migration Guides**: In `docs/` directory for major changes

### External Dependencies
- **FastAPI**: https://fastapi.tiangolo.com/
- **LangChain**: https://python.langchain.com/
- **React**: https://react.dev/
- **Tailwind CSS**: https://tailwindcss.com/

### Troubleshooting
- **Logs**: Check backend logs and browser console
- **Health Status**: Use `/health` and `/api/health` endpoints
- **Database**: Verify connection and migration status
- **Network**: Check Docker networking and port availability