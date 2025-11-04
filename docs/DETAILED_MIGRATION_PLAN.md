# Step-by-Step Migration Plan: Backend Integration

## 🎯 Overview

This plan provides detailed steps to migrate `ai_agent/` and `Scrapegraph-ai/` functionality into the `backend/` folder, creating a unified two-folder structure (`frontend/` and `backend/`).

## 📋 Migration Checklist

### **Pre-Migration Preparation**
- [ ] Create backup of current state
- [ ] Update gitignore to exclude temporary files
- [ ] Verify all dependencies are documented
- [ ] Create migration branches

---

## 🔄 Phase 1: Foundation Setup (Day 1-2)

### **Step 1.1: Create New Backend Structure**
```bash
# Navigate to backend folder
cd backend/app

# Create new directories
mkdir -p agents/base
mkdir -p agents/specialized/collection
mkdir -p agents/specialized/analysis
mkdir -p agents/specialized/synthesis
mkdir -p agents/specialized/planning
mkdir -p agents/tools
mkdir -p agents/nodes
mkdir -p agents/legacy
mkdir -p utils
```

### **Step 1.2: Move Current Agents to Legacy**
```bash
# Move existing agents to legacy folder
mv agents/kimi_agent.py agents/legacy/
mv agents/langgraph_agent.py agents/legacy/
mv agents/openrouter_agent.py agents/legacy/
mv agents/scraping_agent.py agents/legacy/
mv agents/unified_agent.py agents/legacy/
mv agents/simple_agent.py agents/legacy/
mv agents/langgraph_tools_agent.py agents/legacy/

# Move agent tools to legacy
mv agents/tools/ agents/legacy/
```

### **Step 1.3: Update Configuration**
```python
# backend/app/config.py - Add AI agent settings
class Settings(BaseSettings):
    # Existing settings...
    
    # AI Agent Settings
    AI_AGENTS_ENABLED: bool = True
    OSINT_WORKFLOW_ENABLED: bool = True
    INVESTIGATION_TIMEOUT: int = 3600
    AGENT_MAX_RETRIES: int = 3
    AGENT_RETRY_DELAY: float = 1.0
    
    # LLM Settings
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4-turbo"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 4000
    
    # ScrapeGraphAI Settings
    SCRAPEGRAPH_LOCAL_MODE: bool = True
    SCRAPEGRAPH_REASONING_ENABLED: bool = True
    SCRAPEGRAPH_MAX_DEPTH: int = 3
    SCRAPEGRAPH_ENGINE: str = "smart_scraper"
```

### **Step 1.4: Update Dependencies**
```bash
# backend/requirements.txt - Add AI agent dependencies
langchain-openai>=0.1.22
langchain-core>=0.2.39
langchain>=0.3.0
langchain-community>=0.2.9
httpx>=0.27.0
aiofiles>=23.0.0
python-dateutil>=2.8.0
psutil>=5.9.0
asyncio-throttle>=1.0.2
```

---

## 🔄 Phase 2: Base Agent Framework (Day 3-4)

### **Step 2.1: Move Base Agent Framework**
```bash
# Copy base agents from ai_agent to backend
cp -r ../../ai_agent/src/agents/base/* agents/base/
```

### **Step 2.2: Update Base Agent Imports**
```python
# backend/app/agents/base/osint_agent.py - Update imports
# Change from:
from ai_agent.src.utils.tools.langchain_tools import BackendScrapingTool
# To:
from app.agents.tools.langchain_tools import BackendScrapingTool

# Change from:
from ai_agent.src.utils.bridge.ai_backend_bridge import AIBackendBridge
# To:
from app.services.ai_bridge import AIBackendBridge
```

### **Step 2.3: Create Agent Base Init**
```python
# backend/app/agents/__init__.py
from .base.osint_agent import OSINTAgent, LLMOSINTAgent
from .base.communication import AgentCommunication

__all__ = [
    "OSINTAgent",
    "LLMOSINTAgent", 
    "AgentCommunication"
]
```

---

## 🔄 Phase 3: Specialized Agents Migration (Day 5-7)

### **Step 3.1: Move Collection Agents**
```bash
# Move collection agents
cp ../../ai_agent/src/agents/collection/* agents/specialized/collection/
```

### **Step 3.2: Update Collection Agent Imports**
```python
# For each collection agent, update imports:
# From:
from ai_agent.src.agents.base.osint_agent import LLMOSINTAgent
# To:
from app.agents.base.osint_agent import LLMOSINTAgent

# From:
from ai_agent.src.utils.tools.scrapegraph_integration import BackendScrapingAdapter
# To:
from app.agents.tools.scrapegraph_tools import BackendScrapingAdapter
```

### **Step 3.3: Move Analysis Agents**
```bash
cp ../../ai_agent/src/agents/analysis/* agents/specialized/analysis/
```

### **Step 3.4: Move Synthesis Agents**
```bash
cp ../../ai_agent/src/agents/synthesis/* agents/specialized/synthesis/
```

### **Step 3.5: Move Planning Agents**
```bash
cp ../../ai_agent/src/agents/planning/* agents/specialized/planning/
```

### **Step 3.6: Update All Agent Imports**
```python
# Create a script to update all Python files in agents/specialized/
# Update imports to use new backend paths
```

---

## 🔄 Phase 4: Tools and Utilities Migration (Day 8-10)

### **Step 4.1: Move Agent Tools**
```bash
# Move tools from ai_agent to backend
cp ../../ai_agent/src/utils/tools/* agents/tools/
```

### **Step 4.2: Update Tool Imports**
```python
# backend/app/agents/tools/langchain_tools.py - Update imports
# From:
from ai_agent.src.utils.clients.backend_scraping_client import BackendScrapingClient
# To:
from app.services.backend_scraping_client import BackendScrapingClient

# From:
from ai_agent.src.utils.tools.scrapegraph_integration import BackendScrapingAdapter
# To:
from app.agents.tools.scrapegraph_tools import BackendScrapingAdapter
```

### **Step 4.3: Move Backend Clients**
```bash
# Move client utilities to services
cp ../../ai_agent/src/utils/clients/* services/
```

### **Step 4.4: Move Bridge Components**
```bash
# Move bridge to services
cp ../../ai_agent/src/utils/bridge/* services/
```

---

## 🔄 Phase 5: Workflow Integration (Day 11-12)

### **Step 5.1: Move Workflow System**
```bash
# Move workflow components
cp ../../ai_agent/src/workflow/* services/
```

### **Step 5.2: Create Investigation Service**
```python
# backend/app/services/ai_investigation.py
from typing import Dict, Any, List, Optional
from .osint_workflow import OSINTWorkflow
from .investigation_state import InvestigationState

class AIInvestigationService:
    """Service for managing AI-powered OSINT investigations"""
    
    def __init__(self):
        self.workflow = OSINTWorkflow()
    
    async def start_investigation(self, request: InvestigationRequest) -> Dict[str, Any]:
        """Start a new OSINT investigation"""
        pass
    
    async def get_investigation_status(self, investigation_id: str) -> Dict[str, Any]:
        """Get investigation status"""
        pass
    
    async def approve_phase(self, investigation_id: str, phase: str) -> Dict[str, Any]:
        """Approve investigation phase"""
        pass
```

---

## 🔄 Phase 6: ScrapeGraphAI Integration (Day 13-15)

### **Step 6.1: Extract Core ScrapeGraph Components**
```bash
# Copy essential ScrapeGraph components
cp -r ../Scrapegraph-ai/scrapegraphai/nodes/ agents/nodes/
cp -r ../Scrapegraph-ai/scrapegraphai/graphs/ services/scrapegraph_graphs/
cp -r ../Scrapegraph-ai/scrapegraphai/utils/ services/scrapegraph_utils/
```

### **Step 6.2: Create Enhanced ScrapeGraph Service**
```python
# backend/app/services/scrapegraph_enhanced.py
from typing import Dict, Any, List, Optional
from .scrapegraph_graphs.smart_scraper_graph import SmartScraperGraph
from .scrapegraph_graphs.search_scraper_graph import SearchScraperGraph

class ScrapeGraphEnhanced:
    """Enhanced ScrapeGraphAI service with OSINT capabilities"""
    
    def __init__(self):
        self.graphs = {}
        self._initialize_graphs()
    
    def _initialize_graphs(self):
        """Initialize all available graphs"""
        self.graphs['smart_scraper'] = SmartScraperGraph
        self.graphs['search_scraper'] = SearchScraperGraph
        # Add more graph types as needed
    
    async def execute_scraping(self, graph_type: str, prompt: str, source: str, config: Dict = None) -> Dict[str, Any]:
        """Execute scraping with specified graph type"""
        pass
```

---

## 🔄 Phase 7: API Development (Day 16-18)

### **Step 7.1: Create Investigation API**
```python
# backend/app/api/ai_investigation.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from app.services.ai_investigation import AIInvestigationService
from app.models.ai_investigation import InvestigationRequest, InvestigationResponse

router = APIRouter(prefix="/api/ai-investigation", tags=["AI Investigation"])

@router.post("/start", response_model=InvestigationResponse)
async def start_investigation(
    request: InvestigationRequest,
    service: AIInvestigationService = Depends()
) -> InvestigationResponse:
    """Start a new AI-powered OSINT investigation"""
    try:
        result = await service.start_investigation(request)
        return InvestigationResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{investigation_id}/status")
async def get_investigation_status(
    investigation_id: str,
    service: AIInvestigationService = Depends()
) -> Dict[str, Any]:
    """Get investigation status"""
    return await service.get_investigation_status(investigation_id)
```

### **Step 7.2: Create Investigation Models**
```python
# backend/app/models/ai_investigation.py
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

class InvestigationPhase(str, Enum):
    PLANNING = "planning"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"

class InvestigationRequest(BaseModel):
    target: str = Field(..., description="Investigation target")
    objective: str = Field(..., description="Investigation objective")
    scope: List[str] = Field(default_factory=list, description="Investigation scope")
    priority: str = Field(default="medium", description="Investigation priority")
    requirements: Dict[str, Any] = Field(default_factory=dict)

class InvestigationResponse(BaseModel):
    investigation_id: str
    status: str
    current_phase: InvestigationPhase
    progress_percentage: float
    estimated_completion: Optional[datetime] = None
    message: str
```

---

## 🔄 Phase 8: Integration & Testing (Day 19-21)

### **Step 8.1: Update Main Application**
```python
# backend/app/main.py - Add new router
from app.api.ai_investigation import router as investigation_router

app.include_router(investigation_router)
```

### **Step 8.2: Update Database Models**
```python
# backend/app/models/osint.py - Add investigation tables
# Add tables for AI investigations, agent execution, workflow state
```

### **Step 8.3: Create Database Migration**
```bash
# Generate new migration for AI investigation tables
alembic revision --autogenerate -m "Add AI investigation models"
alembic upgrade head
```

### **Step 8.4: Update Requirements**
```python
# backend/requirements.txt - Final version with all dependencies
# Ensure all new dependencies are included
```

---

## 🔄 Phase 9: Cleanup (Day 22-23)

### **Step 9.1: Remove Old Folders**
```bash
# After confirming everything works, remove old folders
rm -rf ../ai_agent/
rm -rf ../Scrapegraph-ai/
```

### **Step 9.2: Update Documentation**
```markdown
# Update README.md to reflect new structure
# Update API documentation
# Update deployment guides
```

### **Step 9.3: Update Scripts**
```bash
# Update any startup scripts to reference new paths
# Update Docker configurations
# Update CI/CD pipelines
```

---

## 🔄 Phase 10: Final Testing (Day 24-25)

### **Step 10.1: Integration Testing**
```python
# Test complete AI investigation workflow
# Test all agent types
# Test API endpoints
# Test database operations
```

### **Step 10.2: Performance Testing**
```python
# Test agent performance
# Test memory usage
# Test concurrent investigations
# Test API response times
```

### **Step 10.3: Documentation**
```markdown
# Create API documentation
# Create deployment guide
# Create troubleshooting guide
```

---

## 📊 Success Criteria

### **Functional Requirements**
- [ ] All AI agents work correctly in new structure
- [ ] API endpoints function properly
- [ ] Database operations work
- [ ] Frontend can still communicate with backend

### **Technical Requirements**
- [ ] All imports resolve correctly
- [ ] No circular dependencies
- [ ] Tests pass
- [ ] Performance is maintained or improved

### **Documentation Requirements**
- [ ] README updated
- [ ] API documentation complete
- [ ] Migration guide created
- [ ] Troubleshooting guide available

---

## 🚨 Rollback Plan

If migration fails at any point:

1. **Git Reset**: Use git to reset to pre-migration state
2. **Backup Restore**: Restore from backup created in Step 1.1
3. **Partial Rollback**: Rollback specific phases if needed
4. **Documentation**: Document what failed and why

---

## 📈 Expected Benefits

1. **Simplified Structure**: Only 2 main folders (frontend/, backend/)
2. **Unified Architecture**: All AI functionality in one backend
3. **Better Maintainability**: Centralized codebase
4. **Enhanced Capabilities**: Full OSINT investigation workflows
5. **Improved Performance**: Optimized agent orchestration
6. **Easier Deployment**: Single backend deployment unit

This migration plan ensures a systematic, safe transition to a cleaner, more maintainable architecture while preserving all existing functionality and adding powerful new capabilities.