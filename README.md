# 🕵️‍♂️ ScrapeCraft OSINT Platform

Advanced OSINT Investigation Platform with AI-Powered Agents and Real-Time Workflows

## 🌟 **FEATURES**

- **AI-Powered OSINT Agents**: Advanced collection, analysis, and synthesis agents
- **Real-Time Workflows**: WebSocket-enabled investigation workflows
- **ScrapeGraphAI Integration**: Intelligent web scraping with AI
- **Multi-Modal Investigation**: Surface, deep, and dark web intelligence collection
- **Collaborative Interface**: Real-time frontend-backend communication
- **Modular Architecture**: Clean separation of concerns with scalable design

## 🏗️ **ARCHITECTURE**

```
scrapecraft/
├── frontend/                    # React/TypeScript frontend
│   ├── src/
│   │   ├── components/         # UI components
│   │   ├── services/           # API clients
│   │   ├── store/              # State management
│   │   └── hooks/              # React hooks
│   ├── package.json            # Frontend dependencies
│   └── ...
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── agents/             # AI agent framework
│   │   │   ├── base/           # Base agent classes
│   │   │   ├── specialized/    # Collection, analysis, synthesis agents
│   │   │   ├── tools/          # LangChain integration
│   │   │   └── nodes/          # ScrapeGraphAI nodes
│   │   ├── api/                # REST API endpoints
│   │   ├── services/           # Business logic services
│   │   ├── models/             # Data models & Pydantic schemas
│   │   └── config.py           # Configuration settings
│   ├── requirements.txt        # Backend dependencies
│   └── dev_server.py           # Development server
├── docs/                       # Documentation & integration guides
└── scripts/                    # Deployment and utility scripts
```

### **AI Agent Framework**
- **Collection Agents**: Public records, social media, surface web, dark web collectors
- **Analysis Agents**: Contextual analysis, pattern recognition, data fusion
- **Synthesis Agents**: Report generation, intelligence synthesis, quality assurance
- **Tools Integration**: LangChain compatibility with ScrapeGraphAI

### **Real-Time Workflows**
- **WebSocket Communication**: Live updates between frontend and backend
- **Investigation States**: Progress tracking and workflow orchestration
- **Approval System**: Secure multi-step workflow validation
- **Real-Time Monitoring**: Live progress updates and status tracking

## 🚀 **QUICK START**

### **Backend Setup**
```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start development server
python dev_server.py
# Server starts on http://localhost:8000
```

### **Frontend Setup**
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
# Frontend serves on http://localhost:3000
```

### **API Endpoints**
- `GET /api/docs` - Interactive API documentation
- `POST /api/pipelines` - Create scraping pipelines
- `POST /api/scraping` - Execute scraping tasks
- `POST /api/workflow` - Manage investigation workflows
- `POST /api/osint` - OSINT investigation operations
- `POST /api/ai-investigation` - AI-powered investigations

## 🤖 **AI AGENT CAPABILITIES**

### **Collection Agents**
- **Public Records Collector**: Government databases, public records
- **Social Media Collector**: Twitter, Facebook, Instagram data collection
- **Surface Web Collector**: Traditional web intelligence
- **Dark Web Collector**: Tor network intelligence gathering

### **Analysis Agents**
- **Contextual Analysis**: Content analysis and context extraction
- **Pattern Recognition**: Trend identification and pattern detection
- **Data Fusion**: Multiple source data integration

### **Synthesis Agents**
- **Report Generation**: Structured intelligence reports
- **Intelligence Synthesis**: Multi-source intelligence consolidation
- **Quality Assurance**: Data verification and validation

## 🌐 **INTEGRATION HIGHLIGHTS**

### **ScrapeGraphAI Integration**
- Direct API integration with advanced scraping capabilities
- AI-powered content extraction and structure detection
- Schema-based data extraction
- Multi-URL concurrent processing

### **LangChain Compatibility**
- Tool integration framework for agent extensibility
- LLM orchestration and workflow management
- Memory management and context handling

### **Real-Time Communication**
- WebSocket-based live updates
- Real-time progress tracking
- Live data streaming and visualization

## 🛠️ **DEVELOPMENT**

### **Project Structure**
- **Frontend**: React/TypeScript with modern component architecture
- **Backend**: FastAPI with async/await patterns
- **Database**: SQLAlchemy with Pydantic validation
- **Real-time**: WebSocket communication layer
- **Agents**: Modular AI agent framework

### **Testing**
```bash
# Backend tests
cd backend
pytest -v

# Frontend tests
cd frontend
npm test
```

## 🤝 **CONTRIBUTING**

This is an open-source OSINT platform. Contributions are welcome in the form of:
- Bug reports and fixes
- Feature requests and implementations
- Documentation improvements
- Agent capability enhancements
- UI/UX improvements

## 📄 **LICENSE**

See the LICENSE file for licensing information.

## 📞 **SUPPORT**

For support and questions, please open an issue in the GitHub repository.
