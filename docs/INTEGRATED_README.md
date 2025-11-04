# ScrapeCraft Integrated System

## 🚀 Quick Start

The ScrapeCraft system consists of a React frontend and FastAPI backend that work together. Here are three ways to run it:

### Option 1: Integrated Development (Recommended)

```bash
# Start the complete system (frontend + backend)
./start-dev.sh

# Stop the system
./stop.sh
```

### Option 2: Docker Integration

```bash
# Start with Docker Compose
./start-docker.sh

# View logs
./start-docker.sh --logs

# Stop
docker-compose down
```

### Option 3: NPM Commands

```bash
# Start integrated development
npm run dev

# Start with Docker
npm run dev:docker

# Stop all services
npm run stop
```

## 📋 What's Running

- **Frontend**: React app on http://localhost:3000
- **Backend**: FastAPI server on http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔧 System Integration

The system is designed as an integrated unit:

1. **Backend starts first** on port 8000 with mock OSINT endpoints
2. **Frontend starts second** on port 3000 and proxies API calls to backend
3. **No more proxy errors** - both services communicate seamlessly
4. **Unified startup/shutdown** - single command controls everything

## 📁 Key Files

- `start-dev.sh` - Integrated development startup
- `start-docker.sh` - Docker-based startup
- `stop.sh` - Stop all services
- `backend/dev_server.py` - Minimal backend with OSINT endpoints
- `frontend/` - React frontend
- `package.json` - Root package with unified scripts

## 🛠️ Development

The system provides mock data for:
- OSINT investigations
- Agents and tasks
- Evidence collection
- Threat assessments

All frontend components are fully functional and type-error free.

## 📊 System Status

✅ Compilation: No errors  
✅ TypeScript: All type errors resolved  
✅ Integration: Frontend ↔ Backend connected  
✅ Build: Production-ready  

The system is now running as a **unified integrated platform** rather than isolated components.