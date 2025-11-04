# ScrapeCraft OSINT Platform - Development Guidelines

## Build / Lint / Test Commands

### Backend (FastAPI)
```bash
cd backend
python dev_server.py                    # Start development server
pytest -v                              # Run all tests
pytest tests/test_specific.py -v       # Run single test file
pytest tests/test_specific.py::test_method -v  # Run single test method
```

### Frontend (React/TypeScript)
```bash
cd frontend
npm start                               # Start development server
npm test                                # Run all tests
npm test -- --testPathPattern=specific.test  # Run single test file
npm run build                           # Production build
```

### Python CLI & AI Agent
```bash
python -m pytest -v                    # Run all tests
python -m pytest tests/test_specific.py -v  # Run single test
python osint_cli.py --help             # Test CLI functionality
```

## Code Style Guidelines

### Python
- **Formatting**: `black .` (line length 88)
- **Linting**: `ruff check .` then `ruff format .`
- **Imports**: `isort .` (stdlib → third-party → local)
- **Type Checking**: `mypy .` with strict mode
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes

### TypeScript/React
- **Components**: Functional components with hooks
- **Types**: Strict TypeScript, interface over type
- **Naming**: `PascalCase` for components/types, `camelCase` for variables
- **Imports**: React imports first, then third-party, then local

### Error Handling
- Use structured logging with timestamps
- Implement comprehensive try/catch blocks
- Async/await patterns with proper error propagation
- Validate inputs at API boundaries

### Testing
- Unit tests with pytest (Python) and Jest (React)
- Integration tests for API endpoints
- Minimum 80% code coverage required
- Test files named `test_*.py` or `*.test.ts`