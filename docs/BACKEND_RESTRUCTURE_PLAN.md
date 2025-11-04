# Backend Restructuring Plan: AI Agent & ScrapeGraphAI Integration

## 🎯 Target Structure

```
backend/
├── app/
│   ├── agents/                    # Enhanced AI agent system
│   │   ├── __init__.py
│   │   ├── base/                  # Base agent framework
│   │   │   ├── __init__.py
│   │   │   ├── osint_agent.py
│   │   │   └── communication.py
│   │   ├── specialized/           # Domain-specific agents
│   │   │   ├── __init__.py
│   │   │   ├── collection/
│   │   │   │   ├── surface_web_collector.py
│   │   │   │   ├── social_media_collector.py
│   │   │   │   ├── public_records_collector.py
│   │   │   │   └── dark_web_collector.py
│   │   │   ├── analysis/
│   │   │   │   ├── data_fusion_agent.py
│   │   │   │   ├── pattern_recognition_agent.py
│   │   │   │   └── contextual_analysis_agent.py
│   │   │   ├── synthesis/
│   │   │   │   ├── intelligence_synthesis_agent.py
│   │   │   │   ├── quality_assurance_agent.py
│   │   │   │   └── report_generation_agent.py
│   │   │   └── planning/
│   │   │       ├── objective_definition.py
│   │   │       └── strategy_formulation.py
│   │   ├── tools/                 # AI agent tools
│   │   │   ├── __init__.py
│   │   │   ├── langchain_tools.py
│   │   │   ├── scrapegraph_tools.py
│   │   │   └── bridge_tools.py
│   │   ├── nodes/                 # ScrapeGraphAI nodes
│   │   │   ├── __init__.py
│   │   │   ├── scrape_nodes.py
│   │   │   ├── custom_nodes.py
│   │   │   └── node_factory.py
│   │   └── legacy/                # Current basic agents
│   │       ├── __init__.py
│   │       ├── kimi_agent.py
│   │       ├── langgraph_agent.py
│   │       ├── openrouter_agent.py
│   │       └── scraping_agent.py
│   ├── api/                       # API endpoints
│   │   ├── __init__.py
│   │   ├── ai_investigation.py    # New: AI investigation endpoints
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── execution.py
│   │   ├── osint.py
│   │   ├── pipelines.py
│   │   ├── scraping.py
│   │   ├── workflow.py
│   │   └── workflow_v2.py
│   ├── models/                    # Pydantic models
│   │   ├── __init__.py
│   │   ├── ai_investigation.py    # New: AI investigation models
│   │   ├── chat.py
│   │   ├── osint.py
│   │   ├── pipeline.py
│   │   └── workflow.py
│   ├── services/                  # Business logic services
│   │   ├── __init__.py
│   │   ├── ai_investigation.py    # New: Investigation service
│   │   ├── ai_bridge.py           # Enhanced: AI-backend bridge
│   │   ├── investigation_state.py # New: State management
│   │   ├── osint_workflow.py      # New: OSINT workflow engine
│   │   ├── scrapegraph_enhanced.py # Enhanced: ScrapeGraphAI service
│   │   ├── workflow_orchestrator.py # New: Workflow orchestration
│   │   ├── database.py
│   │   ├── enhanced_scraping_service.py
│   │   ├── enhanced_websocket.py
│   │   ├── langchain_compatibility.py
│   │   ├── local_scraping_service.py
│   │   ├── local_scraping_service_mock.py
│   │   ├── local_scraping_service_real.py
│   │   ├── openrouter.py
│   │   ├── pattern_learner.py
│   │   ├── scrapegraph.py
│   │   ├── scraping_service_enhanced.py
│   │   ├── task_storage.py
│   │   ├── websocket.py
│   │   ├── workflow_manager.py
│   │   └── workflow_manager_v2.py
│   ├── config.py                  # Enhanced configuration
│   ├── main.py                    # FastAPI application
│   └── utils/                     # Shared utilities
│       ├── __init__.py
│       ├── logging.py
│       ├── async_utils.py
│       └── validation.py
├── migrations/                    # Database migrations
│   └── versions/
│       ├── 001_osint_models.py
│       └── 002_ai_investigation_models.py  # New: AI investigation tables
├── requirements.txt               # Enhanced dependencies
├── Dockerfile
├── Dockerfile.production
├── dev_server.py
├── simple_main.py
└── tests/                        # Test suite
    ├── __init__.py
    ├── test_agents/
    ├── test_services/
    ├── test_api/
    └── test_integration/
```

## 🔄 Migration Mapping

### **Current → Target Structure**

| Current Location | Target Location | Action |
|------------------|----------------|--------|
| `ai_agent/src/agents/base/` | `backend/app/agents/base/` | Move |
| `ai_agent/src/agents/collection/` | `backend/app/agents/specialized/collection/` | Move |
| `ai_agent/src/agents/analysis/` | `backend/app/agents/specialized/analysis/` | Move |
| `ai_agent/src/agents/synthesis/` | `backend/app/agents/specialized/synthesis/` | Move |
| `ai_agent/src/agents/planning/` | `backend/app/agents/specialized/planning/` | Move |
| `ai_agent/src/utils/tools/` | `backend/app/agents/tools/` | Move |
| `ai_agent/src/utils/bridge/` | `backend/app/services/` | Move & Enhance |
| `ai_agent/src/utils/clients/` | `backend/app/services/` | Move |
| `ai_agent/src/workflow/` | `backend/app/services/` | Move |
| `backend/app/agents/` | `backend/app/agents/legacy/` | Move existing |
| `Scrapegraph-ai/nodes/` | `backend/app/agents/nodes/` | Selective move |
| `Scrapegraph-ai/graphs/` | `backend/app/services/scrapegraph_enhanced.py` | Integrate |

## 📋 Integration Benefits

### **1. Unified Architecture**
- All AI functionality in one cohesive backend
- Consistent patterns and shared utilities
- Simplified deployment and scaling

### **2. Enhanced Capabilities**
- Sophisticated OSINT investigation workflows
- Advanced agent orchestration
- Rich ScrapeGraphAI integration

### **3. Better API Design**
- Single API surface for all AI features
- Consistent authentication and authorization
- Unified error handling and logging

### **4. Improved Maintainability**
- Centralized codebase
- Shared configuration and dependencies
- Easier testing and debugging

## 🚀 Implementation Phases

### **Phase 1: Foundation (Week 1)**
1. Create new folder structure
2. Move base agent framework
3. Enhance configuration system
4. Update dependencies

### **Phase 2: Core Integration (Week 2)**
1. Move specialized agents
2. Integrate workflow system
3. Enhance ScrapeGraph service
4. Create basic API endpoints

### **Phase 3: API Enhancement (Week 3)**
1. Create AI investigation endpoints
2. Integrate state synchronization
3. Add WebSocket support for investigations
4. Create comprehensive models

### **Phase 4: Testing & Polish (Week 4)**
1. Write comprehensive tests
2. Performance optimization
3. Documentation updates
4. Integration testing

This structure provides a solid foundation for a powerful, unified AI backend system while maintaining existing functionality and enabling future enhancements.