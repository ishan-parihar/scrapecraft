#!/bin/bash

# OSINT-OS Setup Script
# Sets up the complete OSINT-OS environment including all dependencies
#
# Usage:
#   ./setup-osint-os.sh              # Full setup for development
#   ./setup-osint-os.sh --production # Setup for production
#   ./setup-osint-os.sh --clean      # Clean setup (removes existing venv/node_modules)

set -e

PRODUCTION_MODE=false
CLEAN_MODE=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --production)
            PRODUCTION_MODE=true
            echo "🏭 Setting up for production environment"
            ;;
        --clean)
            CLEAN_MODE=true
            echo "🧹 Performing clean setup"
            ;;
        --help|-h)
            echo "OSINT-OS Setup Script"
            echo ""
            echo "Usage:"
            echo "  ./setup-osint-os.sh              # Standard development setup"
            echo "  ./setup-osint-os.sh --production # Production setup"
            echo "  ./setup-osint-os.sh --clean      # Clean setup (removes existing)"
            echo ""
            exit 0
            ;;
        *)
            echo "❌ Unknown argument: $arg"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "🚀 Setting up OSINT-OS Intelligence Platform..."
echo "================================================"

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ] || [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo "❌ Error: Please run from OSINT-OS project root directory"
    exit 1
fi

# System requirements check
echo "🔍 Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.9"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION detected"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is required but not installed"
    exit 1
fi

NODE_VERSION=$(node -v | sed 's/v//')
echo "✅ Node.js $NODE_VERSION detected"

# Check npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm is required but not installed"
    exit 1
fi

NPM_VERSION=$(npm -v)
echo "✅ npm $NPM_VERSION detected"

# Check Docker (optional)
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | sed 's/Docker version //')
    echo "✅ Docker $DOCKER_VERSION detected"
else
    echo "⚠️  Docker not found (optional for containerized deployment)"
fi

echo ""
echo "📦 Setting up backend environment..."
cd backend

# Clean setup if requested
if [ "$CLEAN_MODE" = true ]; then
    echo "🧹 Cleaning existing backend environment..."
    rm -rf venv
    rm -rf __pycache__
    rm -rf .mypy_cache
    rm -rf .pytest_cache
    find . -name "*.pyc" -delete
    find . -name "*.pyo" -delete
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Error: Failed to create virtual environment"
    exit 1
fi

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ "$PRODUCTION_MODE" = true ]; then
    # Install production dependencies
    pip install -r requirements.txt
    echo "✅ Production dependencies installed"
else
    # Install development dependencies
    pip install -r requirements.txt
    pip install pytest pytest-asyncio black ruff isort mypy bandit
    echo "✅ Development dependencies installed"
fi

# Install Playwright browsers for premium search
echo "🌐 Installing Playwright browsers for premium search..."
source venv/bin/activate
playwright install chromium --with-deps
echo "✅ Playwright browsers installed"

# Database setup
echo "🗄️  Setting up database..."
if [ -f "alembic.ini" ]; then
    # Run database migrations
    alembic upgrade head
    echo "✅ Database migrations completed"
else
    echo "⚠️  No Alembic configuration found, skipping migrations"
fi

# Verify installation
echo "🔍 Verifying backend installation..."
python -c "
import sys
sys.path.insert(0, '.')
try:
    from app.main import app
    from app.services.premium_scraping_service import PremiumScrapingService
    from app.agents.specialized.collection.premium_search_agent import PremiumSearchAgent
    print('✅ Backend modules imported successfully')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"

cd ..

echo ""
echo "🎨 Setting up frontend environment..."
cd frontend

# Clean setup if requested
if [ "$CLEAN_MODE" = true ]; then
    echo "🧹 Cleaning existing frontend environment..."
    rm -rf node_modules
    rm -rf build
    rm -rf .next
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

if [ "$PRODUCTION_MODE" = true ]; then
    echo "🏗️  Building frontend for production..."
    npm run build
    echo "✅ Frontend build completed"
else
    echo "🔧 Installing development dependencies..."
    npm install --save-dev
    echo "✅ Frontend development setup completed"
fi

# Verify frontend installation
echo "🔍 Verifying frontend installation..."
npm run type-check 2>/dev/null || echo "⚠️  TypeScript type check issues detected"
echo "✅ Frontend verification completed"

cd ..

echo ""
echo "🔧 Configuring environment..."

# Create environment files if they don't exist
if [ ! -f "backend/.env" ]; then
    echo "📝 Creating backend environment file..."
    cp backend/.env.example backend/.env
    echo "✅ Backend .env file created (please review and update)"
fi

if [ ! -f "frontend/.env" ]; then
    echo "📝 Creating frontend environment file..."
    cat > frontend/.env << EOF
# Frontend Environment Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_VERSION=1.0.0
EOF
    echo "✅ Frontend .env file created"
fi

# Update frontend package.json to use port 4000
echo "🔧 Updating frontend configuration for port 4000..."
if [ -f "frontend/package.json" ]; then
    # Check if the start script already uses port 4000
    if grep -q "PORT=3000" frontend/package.json; then
        # Replace port 3000 with 4000
        sed -i 's/PORT=3000/PORT=4000/g' frontend/package.json
        echo "✅ Updated frontend to use port 4000"
    elif grep -q '"start"' frontend/package.json && ! grep -q "PORT" frontend/package.json; then
        # Add PORT=4000 to start script
        sed -i 's/"start": "react-scripts start"/"start": "PORT=4000 react-scripts start"/' frontend/package.json
        echo "✅ Added port 4000 to frontend start script"
    else
        echo "⚠️  Could not automatically update frontend port configuration"
    fi
fi

echo ""
echo "🧪 Running setup verification..."

# Test backend can start
echo "🔍 Testing backend startup..."
cd backend
source venv/bin/activate
python -c "
import asyncio
import sys
sys.path.insert(0, '.')
try:
    from app.services.premium_scraping_service import PremiumScrapingService
    service = PremiumScrapingService()
    print('✅ Premium scraping service initialized')
except Exception as e:
    print(f'⚠️  Backend test warning: {e}')
"
cd ..

# Test frontend can build
echo "🔍 Testing frontend build..."
cd frontend
if npm run build --silent; then
    echo "✅ Frontend builds successfully"
else
    echo "⚠️  Frontend build issues detected"
fi
cd ..

echo ""
echo "🎉 OSINT-OS Setup Complete!"
echo "============================"
echo ""
echo "📱 Frontend will run on: http://localhost:4000"
echo "🔧 Backend API will run on: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "🚀 Next Steps:"
echo "   1. Review and update environment files:"
echo "      - backend/.env"
echo "      - frontend/.env"
echo "   2. Start the system:"
echo "      ./run-osint-os.sh"
echo "   3. Access the application:"
echo "      Frontend: http://localhost:4000"
echo "      Backend: http://localhost:8000"
echo ""
echo "🔧 Optional Services:"
echo "   - Docker services: docker-compose up -d"
echo "   - Database: alembic upgrade head"
echo "   - Tests: ./run-osint-os.sh --test"
echo ""
echo "📚 Documentation:"
echo "   - README.md"
echo "   - CRUSH.md"
echo "   - PHASE_3_COMPLETION_REPORT.md"
echo ""
if [ "$PRODUCTION_MODE" = true ]; then
    echo "🏭 Production Setup Complete!"
    echo "   Frontend build: ./frontend/build/"
    echo "   Backend ready for deployment"
else
    echo "🛠️  Development Setup Complete!"
    echo "   Ready for development and testing"
fi
echo ""