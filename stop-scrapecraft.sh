#!/bin/bash

# ScrapeCraft Stop Script
# Stops all ScrapeCraft services

echo "🛑 Stopping ScrapeCraft services..."

# Kill any running processes
pkill -f "node.*3000" 2>/dev/null || true
pkill -f "python.*8000" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true

# Stop Docker containers if running
if command -v docker-compose > /dev/null 2>&1; then
    if [ -f "docker-compose.yml" ]; then
        echo "🐳 Stopping Docker containers..."
        docker-compose down 2>/dev/null || true
    fi
fi

echo "✅ All ScrapeCraft services stopped!"