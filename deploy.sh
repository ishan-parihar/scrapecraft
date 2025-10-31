#!/bin/bash

# ScrapeCraft Docker Deployment Script
# This script sets up and deploys ScrapeCraft with local ScrapeGraphAI

set -e

echo "🚀 Starting ScrapeCraft deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📋 Creating .env file from template..."
    cp .env.example.fixed .env
    echo "⚠️  Please edit .env file with your API keys before running again!"
    echo "Required variables:"
    echo "  - OPENROUTER_API_KEY"
    echo "  - OPENAI_API_KEY (for local ScrapeGraphAI)"
    echo "  - JWT_SECRET"
    exit 1
fi

# Load environment variables
source .env

echo "🔧 Building Docker images..."

# Build and start services
docker-compose -f docker-compose.fixed.yml up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
docker-compose -f docker-compose.fixed.yml ps

# Test backend health
echo "🏥 Testing backend health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Backend is healthy!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to become healthy"
        docker-compose -f docker-compose.fixed.yml logs backend
        exit 1
    fi
    echo "⏳ Waiting for backend... ($i/30)"
    sleep 2
done

# Test frontend
echo "🌐 Testing frontend..."
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is accessible!"
else
    echo "⚠️  Frontend not ready yet, this is normal"
fi

echo ""
echo "🎉 ScrapeCraft deployment complete!"
echo ""
echo "📋 Service URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Database: localhost:5432"
echo "  Redis: localhost:6379"
echo ""
echo "🔧 Management commands:"
echo "  View logs: docker-compose -f docker-compose.fixed.yml logs -f [service]"
echo "  Stop services: docker-compose -f docker-compose.fixed.yml down"
echo "  Restart services: docker-compose -f docker-compose.fixed.yml restart"
echo ""
echo "🤖 Local LLM Options:"
echo "  To use Ollama: docker-compose -f docker-compose.fixed.yml --profile ollama up -d"
echo "  Then set USE_OLLAMA=true in .env"