#!/bin/bash

# ScrapeCraft Unified Startup Script
# The ONLY script you need to run the complete integrated system

set -e

echo "🚀 Starting ScrapeCraft Integrated System..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run from project root directory"
    exit 1
fi

# Kill any existing processes
echo "🧹 Cleaning up existing processes..."
pkill -f "node.*3000" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "python.*8000" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true

# Force kill processes on ports 3000 and 8000
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
sleep 3

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down ScrapeCraft..."
    pkill -f "node.*3000" 2>/dev/null || true
    pkill -f "python.*8000" 2>/dev/null || true
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    echo "✅ All services stopped!"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start backend
echo "🔧 Starting backend server..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install minimal dependencies if needed
if [ requirements-minimal.txt -nt venv/pyvenv.cfg ] 2>/dev/null || [ ! -f "venv/pyvenv.cfg" ]; then
    echo "📦 Installing backend dependencies..."
    pip install -r requirements-minimal.txt
fi

# Start the minimal backend
echo "🚀 Starting backend on http://localhost:8000"
python dev_server.py &
BACKEND_PID=$!

cd ..

# Wait for backend to start
echo "⏳ Waiting for backend to start..."
sleep 3

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend started successfully!"
else
    echo "❌ Backend failed to start"
    kill $BACKEND_PID 2>/dev/null || true
    exit 1
fi

# Start frontend
echo "🎨 Starting frontend..."
cd frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start frontend development server
echo "🚀 Starting frontend on http://localhost:3000"
BROWSER=none npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!

cd ..

# Wait for frontend to start
echo "⏳ Waiting for frontend to start..."
sleep 8

# Check if frontend is running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Frontend started successfully!"
else
    echo "⚠️  Frontend may still be starting..."
fi

echo ""
echo "🎉 ScrapeCraft is now running!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🛑 Press Ctrl+C to stop all services"
echo ""

# Keep the script running and monitor services
while true; do
    # Check if backend is still running
    if ! kill -0 $BACKEND_PID 2>/dev/null; then
        echo "❌ Backend stopped unexpectedly!"
        cleanup
    fi
    
    # Check if frontend is still running  
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "❌ Frontend stopped unexpectedly!"
        cleanup
    fi
    
    sleep 5
done