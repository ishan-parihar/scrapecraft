# AI Agent OSINT/SOCMINT Development Guide

## 🎯 Overview

This guide provides comprehensive documentation for developing and working with the AI Agent system for Open Source Intelligence (OSINT) and Social Media Intelligence (SOCMINT) operations.

## 📁 Project Structure

```
ai_agent/
├── src/                          # Source code
│   ├── agents/                   # Agent implementations
│   │   ├── base/                 # Base agent classes
│   │   ├── planning/             # Planning phase agents
│   │   ├── collection/           # Data collection agents
│   │   ├── analysis/             # Data analysis agents
│   │   └── synthesis/            # Report synthesis agents
│   ├── workflow/                 # LangGraph workflow orchestration
│   ├── crews/                    # CrewAI specialized teams
│   ├── tools/                    # Agent tools and utilities
│   ├── storage/                  # Data storage implementations
│   ├── monitoring/               # Monitoring and metrics
│   └── api/                      # REST API endpoints
├── tests/                        # Test suites
├── config/                       # Configuration files
├── scripts/                      # Setup and utility scripts
├── docs/                         # Documentation
└── requirements.txt              # Python dependencies
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Run the setup script
cd ai_agent
python scripts/setup_environment.py

# Activate virtual environment
source ../venv/bin/activate  # Linux/macOS
# or
../venv/Scripts/activate     # Windows

# Configure environment variables
cp config/.env.example config/.env
# Edit config/.env with your API keys
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Start PostgreSQL and Redis
docker-compose up -d postgres redis

# Run database migrations
python scripts/setup_database.py
```

### 4. Run Tests

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/performance/
```

### 5. Start Development Server

```bash
# Start the API server
python src/api/main.py

# Or start with specific configuration
python src/api/main.py --config config/development.yaml
```

## 🏗️ Architecture Overview

### Core Components

1. **Base Agent Framework** (`src/agents/base/`)
   - `OSINTAgent`: Base class for all agents
   - `AgentCommunication`: Inter-agent communication system
   - `AgentConfig`: Configuration management

2. **Planning Phase** (`src/agents/planning/`)
   - `ObjectiveDefinitionAgent`: Defines investigation objectives
   - `StrategyFormulationAgent`: Creates investigation strategies

3. **Workflow Orchestration** (`src/workflow/`)
   - `InvestigationState`: State management with LangGraph
   - `OSINTWorkflow`: Complete investigation workflow
   - Node functions for each investigation phase

4. **Storage Layer** (`src/storage/`)
   - PostgreSQL for structured data
   - Redis for caching and messaging
   - ChromaDB for vector embeddings

### Technology Stack

- **Framework**: LangChain + LangGraph
- **Multi-Agent**: CrewAI for specialized teams
- **API**: FastAPI
- **Database**: PostgreSQL + Redis + ChromaDB
- **Monitoring**: Prometheus + Grafana
- **Testing**: pytest + pytest-asyncio

## 🔧 Development Workflow

### 1. Creating New Agents

```python
# Create new agent in appropriate directory
# Example: src/agents/collection/custom_agent.py

from ..base.osint_agent import OSINTAgent, AgentConfig

class CustomAgent(OSINTAgent):
    def __init__(self, config: Optional[AgentConfig] = None, **kwargs):
        if config is None:
            config = AgentConfig(
                role="Custom Specialist",
                description="Custom agent description",
                max_iterations=5,
                timeout=180
            )
        
        super().__init__(config=config, tools=[], **kwargs)
    
    def _create_agent(self):
        # Implement LangChain agent creation
        pass
    
    def _get_system_prompt(self) -> str:
        return "Your system prompt here"
    
    def _process_output(self, raw_output: str, intermediate_steps: List = None) -> Dict[str, Any]:
        # Process and structure output
        return {"result": "processed_output"}
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        # Validate input data
        return True
```

### 2. Adding Workflow Nodes

```python
# Add node function to src/workflow/nodes.py

async def custom_node(state: InvestigationState) -> InvestigationState:
    """Custom workflow node"""
    try:
        # Process state
        # Update state with results
        state["custom_results"] = {"data": "processed"}
        return state
    except Exception as e:
        # Handle errors
        state = add_error(state, str(e))
        return state

# Add to workflow graph in src/workflow/graph.py
workflow.add_node("custom_node", custom_node)
```

### 3. Configuration Management

```yaml
# config/agent_config.yaml
agent_settings:
  default_timeout: 300
  max_iterations: 10
  retry_attempts: 3

llm_settings:
  provider: openai
  model: gpt-4
  temperature: 0.1

database_settings:
  postgres_url: postgresql://user:pass@localhost/db
  redis_url: redis://localhost:6379/0
```

### 4. Testing

```python
# tests/unit/test_custom_agent.py
import pytest
from src.agents.collection.custom_agent import CustomAgent

@pytest.mark.asyncio
async def test_custom_agent_execution():
    agent = CustomAgent()
    
    input_data = {"test_input": "value"}
    result = await agent.execute(input_data)
    
    assert result.success is True
    assert "custom_results" in result.data
```

## 📊 Monitoring and Debugging

### 1. Logging

```python
import logging

logger = logging.getLogger(__name__)

# Use structured logging
logger.info("Agent execution started", extra={
    "agent_id": agent.config.agent_id,
    "input_data": input_data
})
```

### 2. Metrics

```python
from src.monitoring.metrics import OSINTMetrics

metrics = OSINTMetrics()
await metrics.track_investigation_metrics(
    investigation_id="inv_123",
    phase="planning",
    metrics={"duration": 45.2, "items_processed": 100}
)
```

### 3. Health Checks

```python
# src/monitoring/health.py

async def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "llm": await check_llm_health()
        }
    }
```

## 🔒 Security Considerations

### 1. API Security

```python
# API key authentication
from src.api.middleware.auth import verify_api_key

@app.post("/investigate")
@verify_api_key
async def start_investigation(request: InvestigationRequest):
    # Process request
    pass
```

### 2. Data Protection

```python
# Encrypt sensitive data
from src.tools.security.encryption import encrypt_data

encrypted_data = encrypt_data(sensitive_data, encryption_key)
```

### 3. Compliance

```python
# Check compliance before processing
from src.tools.security.compliance import ComplianceManager

compliance = ComplianceManager()
validation = await compliance.validate_request(request)
if not validation["approved"]:
    raise ComplianceError(validation["violations"])
```

## 🚀 Deployment

### 1. Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

CMD ["python", "src/api/main.py"]
```

### 2. Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-agent-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ai-agent-system
  template:
    metadata:
      labels:
        app: ai-agent-system
    spec:
      containers:
      - name: ai-agent
        image: ai-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### 3. Environment Configuration

```yaml
# config/production.yaml
debug: false
log_level: WARNING

database:
  pool_size: 20
  max_overflow: 40

monitoring:
  prometheus_enabled: true
  sentry_enabled: true
  sentry_dsn: ${SENTRY_DSN}
```

## 🧪 Testing Strategy

### 1. Unit Tests

- Test individual agent functionality
- Mock external dependencies
- Focus on business logic

### 2. Integration Tests

- Test agent interactions
- Test workflow execution
- Use test databases

### 3. Performance Tests

- Load testing for API endpoints
- Agent performance benchmarks
- Memory and CPU profiling

### 4. End-to-End Tests

- Complete investigation workflows
- Real data scenarios
- User acceptance testing

## 📈 Performance Optimization

### 1. Agent Optimization

```python
# Use connection pooling
database_pool = create_engine(database_url, pool_size=20)

# Implement caching
@lru_cache(maxsize=1000)
def expensive_operation(input_data):
    # Expensive computation
    return result
```

### 2. Workflow Optimization

```python
# Parallel execution
async def parallel_data_collection():
    tasks = [
        collect_surface_web_data(),
        collect_social_media_data(),
        collect_public_records_data()
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. Resource Management

```python
# Resource monitoring
import psutil

def monitor_resources():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    
    if cpu_percent > 80 or memory_percent > 80:
        # Scale or optimize
        pass
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**: Ensure virtual environment is activated
2. **Database Connection**: Check database configuration and connectivity
3. **API Keys**: Verify environment variables are set correctly
4. **Memory Issues**: Monitor resource usage and optimize queries
5. **Agent Timeouts**: Adjust timeout configurations

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
export DEBUG=true

# Run with debugger
python -m pdb src/api/main.py
```

### Log Analysis

```bash
# View error logs
tail -f logs/ai_agent_error.log

# Search for specific errors
grep "ERROR" logs/ai_agent.log | tail -20
```

## 📚 Additional Resources

- [LangChain Documentation](https://python.langchain.com/)
- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [CrewAI Documentation](https://crewai.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Redis Documentation](https://redis.io/documentation)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit pull request with description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.