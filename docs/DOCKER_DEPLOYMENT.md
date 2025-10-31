# ScrapeCraft Docker Deployment Guide

This guide covers deploying ScrapeCraft with local ScrapeGraphAI integration using Docker.

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available
- API keys for LLM services

### 1. Environment Setup
Copy the environment template and configure your API keys:

```bash
cp .env.example.fixed .env
```

Edit `.env` with your configuration:

```bash
# Required API Keys
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENAI_API_KEY=your-openai-api-key-here  # For local ScrapeGraphAI
JWT_SECRET=your-super-secret-jwt-secret-key-here

# Local scraping (recommended)
USE_LOCAL_SCRAPING=true
LOCAL_LLM_MODEL=gpt-3.5-turbo

# Alternative: Use Ollama for local LLM
# USE_OLLAMA=true
# OLLAMA_MODEL=llama3.2
```

### 2. Deploy with Script
Run the automated deployment script:

```bash
./deploy.sh
```

### 3. Manual Deployment
Or deploy manually:

```bash
# Build and start all services
docker-compose -f docker-compose.fixed.yml up --build -d

# View logs
docker-compose -f docker-compose.fixed.yml logs -f

# Stop services
docker-compose -f docker-compose.fixed.yml down
```

## 🏗️ Architecture

### Services
- **Backend**: FastAPI server with local ScrapeGraphAI
- **Frontend**: React SPA served by Nginx
- **Database**: PostgreSQL for data persistence
- **Redis**: For caching and job queues
- **Ollama**: Optional local LLM service

### Local ScrapeGraphAI Integration
The setup includes a complete local installation of ScrapeGraphAI, providing:
- No API rate limits
- Local data processing
- Support for custom LLMs
- Full control over scraping pipeline

## 🔧 Configuration

### LLM Options

#### Option 1: OpenAI (Default)
```env
USE_LOCAL_SCRAPING=true
OPENAI_API_KEY=your-openai-api-key
LOCAL_LLM_MODEL=gpt-3.5-turbo
```

#### Option 2: Ollama (Free Local)
```env
USE_LOCAL_SCRAPING=true
USE_OLLAMA=true
OLLAMA_MODEL=llama3.2
OLLAMA_BASE_URL=http://localhost:11434
```

Start Ollama service:
```bash
docker-compose -f docker-compose.fixed.yml --profile ollama up -d
```

Pull model:
```bash
docker-compose exec ollama ollama pull llama3.2
```

#### Option 3: Other OpenAI-Compatible APIs
```env
USE_LOCAL_SCRAPING=true
LOCAL_LLM_API_KEY=your-api-key
LOCAL_LLM_MODEL=your-model-name
LOCAL_LLM_BASE_URL=https://api.your-provider.com/v1
```

### ScrapeGraphAI Settings
```env
SCRAPEGRAPHAI_HEADLESS=true    # Run browser in headless mode
SCRAPEGRAPHAI_VERBOSE=false    # Reduce log noise
```

## 🌐 Access Points

After deployment:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432
- **Redis**: localhost:6379

## 🔍 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check logs
docker-compose -f docker-compose.fixed.yml logs backend

# Common causes:
# - Missing API keys in .env
# - Port conflicts
# - Insufficient memory
```

#### Scraping Fails
```bash
# Test local scraping configuration
curl -X POST http://localhost:8000/api/test-scraping \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "prompt": "Extract the title"}'

# Check LLM configuration
docker-compose -f docker-compose.fixed.yml logs backend | grep -i llm
```

#### Memory Issues
Increase Docker memory allocation to at least 4GB.

#### Permission Issues
```bash
# Fix Docker permissions
sudo chown -R 1000:1000 ./backend
```

### Development vs Production

#### Development Mode
- Source code mounted as volume
- Auto-reload enabled
- Verbose logging

#### Production Mode
Use the production Dockerfile:
```yaml
backend:
  build:
    context: .
    dockerfile: backend/Dockerfile.production
  # Remove volume mounts
  # Remove --reload flag
```

## 📊 Monitoring

### Health Checks
```bash
# Backend health
curl http://localhost:8000/health

# Database connection
docker-compose exec backend python -c "from app.config import settings; print(settings.DATABASE_URL)"

# Redis connection
docker-compose exec redis redis-cli ping
```

### Logs
```bash
# All services
docker-compose -f docker-compose.fixed.yml logs -f

# Specific service
docker-compose -f docker-compose.fixed.yml logs -f backend

# Last 100 lines
docker-compose -f docker-compose.fixed.yml logs --tail=100 backend
```

## 🔐 Security

### Production Considerations
1. Change default passwords
2. Use HTTPS in production
3. Restrict database access
4. Enable API rate limiting
5. Use environment-specific secrets

### Network Security
```bash
# Secure database (uncomment in production)
# ports:
#   - "127.0.0.1:5432:5432"  # Only localhost

# Secure Redis
# ports:
#   - "127.0.0.1:6379:6379"  # Only localhost
```

## 🚀 Scaling

### Horizontal Scaling
```yaml
backend:
  deploy:
    replicas: 3
  # Remove volume mounts for scaling
```

### Resource Limits
```yaml
backend:
  deploy:
    resources:
      limits:
        memory: 2G
        cpus: '1.0'
      reservations:
        memory: 1G
        cpus: '0.5'
```

## 📝 Backup and Recovery

### Database Backup
```bash
# Backup
docker-compose exec db pg_dump -U user scrapecraft > backup.sql

# Restore
docker-compose exec -T db psql -U user scrapecraft < backup.sql
```

### Volume Backup
```bash
# Backup all volumes
docker run --rm -v scrapecraft_pgdata:/data -v $(pwd):/backup ubuntu tar czf /backup/pgdata.tar.gz -C /data .
```

## 🔄 Updates

### Update ScrapeGraphAI
```bash
# Pull latest ScrapeGraphAI
git pull origin main  # in Scrapegraph-ai directory

# Rebuild
docker-compose -f docker-compose.fixed.yml up --build -d backend
```

### Update Dependencies
```bash
# Rebuild with latest dependencies
docker-compose -f docker-compose.fixed.yml build --no-cache
docker-compose -f docker-compose.fixed.yml up -d
```