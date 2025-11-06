#!/bin/bash

# OSINT-OS Run Script
# Starts the OSINT-OS intelligence platform
#
# Usage:
#   ./run-osint-os.sh              # Start development servers
#   ./run-osint-os.sh build        # Build and run production mode
#   ./run-osint-os.sh test         # Run tests instead of servers
#   ./run-osint-os.sh backend-only # Start only backend
#   ./run-osint-os.sh frontend-only # Start only frontend

set -e

MODE="dev"
BACKEND_ONLY=false
FRONTEND_ONLY=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        build)
            MODE="build"
            echo "🏗️  Running in BUILD mode"
            ;;
        test)
            MODE="test"
            echo "🧪 Running in TEST mode"
            ;;
        backend-only)
            BACKEND_ONLY=true
            echo "🔧 Running BACKEND ONLY mode"
            ;;
        frontend-only)
            FRONTEND_ONLY=true
            echo "🎨 Running FRONTEND ONLY mode"
            ;;
        --help|-h)
            echo "OSINT-OS Run Script"
            echo ""
            echo "Usage:"
            echo "  ./run-osint-os.sh              # Start development servers (default)"
            echo "  ./run-osint-os.sh build        # Build and run production mode"
            echo "  ./run-osint-os.sh test         # Run tests instead of servers"
            echo "  ./run-osint-os.sh backend-only # Start only backend"
            echo "  ./run-osint-os.sh frontend-only # Start only frontend"
            echo ""
            echo "Ports:"
            echo "  Frontend: http://localhost:4000"
            echo "  Backend:  http://localhost:8000"
            echo "  API Docs: http://localhost:8000/docs"
            exit 0
            ;;
        *)
            echo "❌ Unknown argument: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check for conflicting modes
if [ "$BACKEND_ONLY" = true ] && [ "$FRONTEND_ONLY" = true ]; then
    echo "❌ Cannot specify both backend-only and frontend-only"
    exit 1
fi

echo "🚀 Starting OSINT-OS Intelligence Platform..."
echo "=========================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run from OSINT-OS project root directory"
    echo "💡 Run './setup-osint-os.sh' first if you haven't set up the environment"
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down OSINT-OS..."
    
    # Kill backend process
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "✅ Backend stopped"
    fi
    
    # Kill frontend process
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "✅ Frontend stopped"
    fi
    
    # Wait for processes to actually stop
    sleep 2
    
    # Force kill if still running
    if [ ! -z "$BACKEND_PID" ]; then
        kill -9 $BACKEND_PID 2>/dev/null || true
    fi
    
    if [ ! -z "$FRONTEND_PID" ]; then
        kill -9 $FRONTEND_PID 2>/dev/null || true
    fi
    
    echo "✅ All services stopped!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Test mode
if [ "$MODE" = "test" ]; then
    echo "🧪 Running OSINT-OS Test Suite..."
    
    echo "🔧 Running backend tests..."
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
        
        # Run premium search tests
        echo "🔍 Running premium search tests..."
        python ../test_premium_search_basic.py
        
        # Run unit tests
        if command -v pytest &> /dev/null; then
            echo "🧪 Running pytest tests..."
            pytest -v || echo "⚠️  Some tests failed"
        fi
    else
        echo "❌ Backend virtual environment not found. Run setup-osint-os.sh first"
        exit 1
    fi
    cd ..
    
    echo "🎨 Running frontend tests..."
    cd frontend
    if npm test -- --watchAll=false; then
        echo "✅ Frontend tests passed"
    else
        echo "⚠️  Some frontend tests failed"
    fi
    cd ..
    
    echo "✅ Test suite completed!"
    exit 0
fi

# Clean up any existing processes on our target ports
echo "🧹 Checking for existing processes on ports 8000 and 4000..."

# Kill processes on port 8000 (backend)
echo "🔧 Checking port 8000 (backend)..."
if lsof -i :8000 >/dev/null 2>&1; then
    echo "  Port 8000 is in use, cleaning up..."
    lsof -ti:8000 | xargs kill -TERM 2>/dev/null || true
    sleep 2
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true
fi
fuser -k 8000/tcp 2>/dev/null || true

# Kill processes on port 4000 (frontend) - updated from 3000
echo "🎨 Checking port 4000 (frontend)..."
if lsof -i :4000 >/dev/null 2>&1; then
    echo "  Port 4000 is in use, cleaning up..."
    lsof -ti:4000 | xargs kill -TERM 2>/dev/null || true
    sleep 2
    lsof -ti:4000 | xargs kill -9 2>/dev/null || true
fi
fuser -k 4000/tcp 2>/dev/null || true

# Additional cleanup for common processes
pkill -f "react-scripts.*start" 2>/dev/null || true
pkill -f "node.*4000" 2>/dev/null || true

echo "✅ Port cleanup completed"
sleep 3

# Backend setup and startup
if [ "$FRONTEND_ONLY" != true ]; then
    echo "🔧 Starting backend server..."
    cd backend
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "❌ Backend virtual environment not found"
        echo "💡 Run './setup-osint-os.sh' first to set up the environment"
        exit 1
    fi
    
    # Activate virtual environment
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Error: Virtual environment not found"
        exit 1
    fi
    
    # Start the backend
    echo "🚀 Starting backend on http://localhost:8000"
    if [ "$MODE" = "build" ]; then
        uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info > ../backend.log 2>&1 &
    else
        uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level warning --reload > ../backend.log 2>&1 &
    fi
    BACKEND_PID=$!
    
    cd ..
    
    # Wait for backend to start
    echo "⏳ Waiting for backend to start..."
    for i in {1..15}; do
        if curl -s http://127.0.0.1:8000/health >/dev/null 2>&1; then
            echo "✅ Backend started successfully!"
            break
        fi
        if [ $i -eq 15 ]; then
            echo "⚠️ Backend health check failed after 15 attempts"
            echo "📋 Backend log:"
            tail -10 backend.log
            cleanup
        fi
        sleep 2
    done
fi

# Frontend setup and startup
if [ "$BACKEND_ONLY" != true ]; then
    echo "🎨 Starting frontend..."
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo "❌ Frontend dependencies not found"
        echo "💡 Run './setup-osint-os.sh' first to set up the environment"
        cleanup
    fi
    
    # Build frontend if in build mode, otherwise start dev server
    if [ "$MODE" = "build" ]; then
        echo "🏗️  Building frontend for production..."
        npm run build > ../frontend-build.log 2>&1
        if [ $? -eq 0 ]; then
            echo "✅ Frontend build completed successfully!"
            
            # Serve the built frontend with a simple HTTP server
            echo "🚀 Serving frontend on http://localhost:4000"
            cd build
            python3 -m http.server 4000 > ../../frontend-serve.log 2>&1 &
            FRONTEND_PID=$!
            cd ..
        else
            echo "❌ Frontend build failed!"
            echo "📋 Build log:"
            tail -20 frontend-build.log
            cleanup
        fi
    else
        # Start frontend development server
        echo "🚀 Starting frontend on http://localhost:4000"
        BROWSER=none PORT=4000 npm start > ../frontend.log 2>&1 &
        FRONTEND_PID=$!
    fi
    
    cd ..
    
    # Wait for frontend to start
    echo "⏳ Waiting for frontend to start..."
    for i in {1..20}; do
        if curl -s http://localhost:4000 >/dev/null 2>&1; then
            echo "✅ Frontend started successfully!"
            break
        fi
        if [ $i -eq 20 ]; then
            echo "⚠️ Frontend health check failed after 20 attempts"
            echo "📋 Frontend log (last 10 lines):"
            tail -10 frontend.log
            cleanup
        fi
        sleep 3
    done
fi

# Display success message
echo ""
if [ "$MODE" = "build" ]; then
    echo "🎉 OSINT-OS is running in PRODUCTION mode!"
else
    echo "🎉 OSINT-OS is now running!"
fi

if [ "$BACKEND_ONLY" = true ]; then
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
elif [ "$FRONTEND_ONLY" = true ]; then
    echo "📱 Frontend: http://localhost:4000"
else
    echo "📱 Frontend: http://localhost:4000"
    echo "🔧 Backend API: http://localhost:8000"
    echo "📚 API Docs: http://localhost:8000/docs"
    echo "🔍 Premium Search: http://localhost:4000 (via frontend)"
fi

echo ""
echo "📋 Logs:"
echo "   Backend: ./backend.log"
if [ "$FRONTEND_ONLY" != true ]; then
    if [ "$MODE" = "build" ]; then
        echo "   Frontend serve: ./frontend-serve.log"
    else
        echo "   Frontend: ./frontend.log"
    fi
fi

if [ "$MODE" = "build" ]; then
    echo "   Frontend build: ./frontend-build.log"
fi

echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

if [ "$BACKEND_ONLY" = false ]; then
    echo "🌐 Premium Search Demo:"
    echo "   1. Open http://localhost:4000"
    echo "   2. Navigate to Investigations"
    echo "   3. Create new investigation"
    echo "   4. Try the Search functionality"
    echo ""
fi

# Keep the script running and monitor services
while true; do
    # Check if backend is still running (if started)
    if [ "$FRONTEND_ONLY" != true ] && [ ! -z "$BACKEND_PID" ]; then
        if ! kill -0 $BACKEND_PID 2>/dev/null; then
            echo "❌ Backend stopped unexpectedly!"
            echo "📋 Backend log (last 10 lines):"
            tail -10 backend.log
            cleanup
        fi
    fi
    
    # Check if frontend is still running (if started)
    if [ "$BACKEND_ONLY" != true ] && [ ! -z "$FRONTEND_PID" ]; then
        if ! kill -0 $FRONTEND_PID 2>/dev/null; then
            echo "❌ Frontend stopped unexpectedly!"
            echo "📋 Frontend log (last 10 lines):"
            tail -10 frontend.log
            cleanup
        fi
    fi
    
    sleep 10
done