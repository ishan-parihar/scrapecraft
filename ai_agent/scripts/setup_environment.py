#!/usr/bin/env python3
"""
AI Agent Environment Setup Script

This script sets up the development environment for the OSINT AI Agent system,
including dependency installation, database setup, and configuration.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvironmentSetup:
    """Handles environment setup for AI Agent system"""
    
    def __init__(self, project_root: str = None):
        if project_root is None:
            # Assume script is in scripts/ directory
            self.project_root = Path(__file__).parent.parent
        else:
            self.project_root = Path(project_root)
        
        self.ai_agent_dir = self.project_root / "ai_agent"
        self.src_dir = self.ai_agent_dir / "src"
        self.config_dir = self.ai_agent_dir / "config"
        
        logger.info(f"Project root: {self.project_root}")
        logger.info(f"AI Agent directory: {self.ai_agent_dir}")
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        required_version = (3, 8)
        current_version = sys.version_info[:2]
        
        if current_version < required_version:
            logger.error(f"Python {required_version[0]}.{required_version[1]}+ required, found {current_version[0]}.{current_version[1]}")
            return False
        
        logger.info(f"Python version check passed: {current_version[0]}.{current_version[1]}")
        return True
    
    def create_virtual_environment(self) -> bool:
        """Create Python virtual environment"""
        venv_path = self.project_root / "venv"
        
        if venv_path.exists():
            logger.info("Virtual environment already exists")
            return True
        
        try:
            logger.info("Creating virtual environment...")
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True)
            
            logger.info("Virtual environment created successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create virtual environment: {e}")
            return False
    
    def get_venv_python(self) -> Path:
        """Get path to virtual environment Python executable"""
        if sys.platform == "win32":
            return self.project_root / "venv" / "Scripts" / "python.exe"
        else:
            return self.project_root / "venv" / "bin" / "python"
    
    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        requirements_file = self.ai_agent_dir / "requirements.txt"
        
        if not requirements_file.exists():
            logger.error(f"Requirements file not found: {requirements_file}")
            return False
        
        venv_python = self.get_venv_python()
        
        try:
            logger.info("Installing Python dependencies...")
            subprocess.run([
                str(venv_python), "-m", "pip", "install", "--upgrade", "pip"
            ], check=True)
            
            subprocess.run([
                str(venv_python), "-m", "pip", "install", "-r", str(requirements_file)
            ], check=True)
            
            logger.info("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install dependencies: {e}")
            return False
    
    def create_directories(self) -> bool:
        """Create necessary directories"""
        directories = [
            self.ai_agent_dir / "logs",
            self.ai_agent_dir / "data",
            self.ai_agent_dir / "data" / "raw",
            self.ai_agent_dir / "data" / "processed",
            self.ai_agent_dir / "data" / "reports",
            self.config_dir,
            self.ai_agent_dir / "tests" / "unit",
            self.ai_agent_dir / "tests" / "integration",
            self.ai_agent_dir / "tests" / "performance",
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Failed to create directory {directory}: {e}")
                return False
        
        logger.info("All directories created successfully")
        return True
    
    def create_config_files(self) -> bool:
        """Create configuration files"""
        config_files = {
            "agent_config.yaml": self.get_agent_config_template(),
            "database_config.yaml": self.get_database_config_template(),
            "logging_config.yaml": self.get_logging_config_template(),
            ".env.example": self.get_env_template()
        }
        
        for filename, content in config_files.items():
            config_path = self.config_dir / filename
            
            if config_path.exists():
                logger.debug(f"Config file already exists: {config_path}")
                continue
            
            try:
                with open(config_path, 'w') as f:
                    f.write(content)
                logger.info(f"Created config file: {config_path}")
            except Exception as e:
                logger.error(f"Failed to create config file {config_path}: {e}")
                return False
        
        return True
    
    def get_agent_config_template(self) -> str:
        """Get agent configuration template"""
        return """# AI Agent Configuration

# General Settings
debug: false
log_level: INFO

# Agent Settings
default_timeout: 300
max_iterations: 10
retry_attempts: 3

# LLM Settings
llm_provider: openai  # openai, anthropic, local
model_name: gpt-4
temperature: 0.1
max_tokens: 4000

# LangChain Settings
verbose: true
memory_enabled: true
memory_limit: 100

# Communication Settings
message_queue: redis
redis_url: redis://localhost:6379/0
communication_timeout: 30

# Storage Settings
database_url: postgresql://user:password@localhost:5432/osint_agents
vector_db_url: chroma://localhost:8000
cache_enabled: true

# Security Settings
encryption_enabled: true
api_key_required: true
rate_limiting: true

# Performance Settings
max_concurrent_agents: 10
agent_pool_size: 5
task_queue_size: 1000
"""
    
    def get_database_config_template(self) -> str:
        """Get database configuration template"""
        return """# Database Configuration

# PostgreSQL Configuration
postgresql:
  host: localhost
  port: 5432
  database: osint_agents
  username: postgres
  password: password
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
  pool_recycle: 3600

# Redis Configuration
redis:
  host: localhost
  port: 6379
  database: 0
  password: null
  max_connections: 100
  socket_timeout: 30
  socket_connect_timeout: 30

# Vector Database Configuration (ChromaDB)
chromadb:
  host: localhost
  port: 8000
  collection_name: osint_embeddings
  persist_directory: ./data/vector_db
  distance_metric: cosine

# Data Retention
retention:
  raw_data_days: 90
  processed_data_days: 365
  reports_days: 1095
  logs_days: 30
"""
    
    def get_logging_config_template(self) -> str:
        """Get logging configuration template"""
        return """# Logging Configuration

version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  detailed:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: DEBUG
    formatter: detailed
    filename: ./logs/ai_agent.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: ./logs/ai_agent_error.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

loggers:
  ai_agent:
    level: DEBUG
    handlers: [console, file, error_file]
    propagate: false

  langchain:
    level: WARNING
    handlers: [file]
    propagate: false

  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
"""
    
    def get_env_template(self) -> str:
        """Get environment variables template"""
        return """# AI Agent Environment Variables

# API Keys (Required)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/osint_agents
REDIS_URL=redis://localhost:6379/0

# Vector Database
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Security
SECRET_KEY=your_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# External Services
SHODAN_API_KEY=your_shodan_api_key_here
TWITTER_API_KEY=your_twitter_api_key_here
LINKEDIN_API_KEY=your_linkedin_api_key_here

# Monitoring
SENTRY_DSN=your_sentry_dsn_here
PROMETHEUS_PORT=9090

# Development
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=development

# ScrapeCraft Integration
SCRAPECRAFT_API_URL=http://localhost:8000
SCRAPECRAFT_API_KEY=your_scrapecraft_api_key_here
"""
    
    def create_gitignore(self) -> bool:
        """Create .gitignore file"""
        gitignore_path = self.ai_agent_dir / ".gitignore"
        
        if gitignore_path.exists():
            logger.info(".gitignore already exists")
            return True
        
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Data
data/
!data/.gitkeep

# Configuration
.env
config/secrets.yaml
config/production.yaml

# Database
*.db
*.sqlite3

# Vector Database
chroma_db/
vector_db/

# Jupyter Notebooks
.ipynb_checkpoints/

# Testing
.pytest_cache/
.coverage
htmlcov/

# Documentation
docs/_build/

# Temporary files
tmp/
temp/
*.tmp
"""
        
        try:
            with open(gitignore_path, 'w') as f:
                f.write(gitignore_content)
            logger.info("Created .gitignore file")
            return True
        except Exception as e:
            logger.error(f"Failed to create .gitignore: {e}")
            return False
    
    def create_init_files(self) -> bool:
        """Create __init__.py files for Python packages"""
        init_files = [
            self.src_dir / "__init__.py",
            self.src_dir / "agents" / "__init__.py",
            self.src_dir / "workflow" / "__init__.py",
            self.src_dir / "crews" / "__init__.py",
            self.src_dir / "tools" / "__init__.py",
            self.src_dir / "storage" / "__init__.py",
            self.src_dir / "monitoring" / "__init__.py",
            self.src_dir / "api" / "__init__.py",
        ]
        
        for init_file in init_files:
            if init_file.exists():
                continue
            
            try:
                init_file.parent.mkdir(parents=True, exist_ok=True)
                init_file.write_text('"""Package initialization"""\n')
                logger.debug(f"Created init file: {init_file}")
            except Exception as e:
                logger.error(f"Failed to create init file {init_file}: {e}")
                return False
        
        return True
    
    def run_setup(self) -> bool:
        """Run complete environment setup"""
        logger.info("Starting AI Agent environment setup...")
        
        steps = [
            ("Checking Python version", self.check_python_version),
            ("Creating virtual environment", self.create_virtual_environment),
            ("Installing dependencies", self.install_dependencies),
            ("Creating directories", self.create_directories),
            ("Creating configuration files", self.create_config_files),
            ("Creating .gitignore", self.create_gitignore),
            ("Creating init files", self.create_init_files),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            if not step_func():
                logger.error(f"Setup failed at step: {step_name}")
                return False
        
        logger.info("Environment setup completed successfully!")
        self.print_next_steps()
        return True
    
    def print_next_steps(self):
        """Print next steps for the user"""
        next_steps = """
🎉 Setup completed successfully! Next steps:

1. Activate the virtual environment:
   - On Linux/macOS: source venv/bin/activate
   - On Windows: venv\\Scripts\\activate

2. Configure environment variables:
   cp ai_agent/config/.env.example ai_agent/.env
   # Edit ai_agent/.env with your API keys and configuration

3. Start the development services:
   - PostgreSQL: Ensure PostgreSQL is running and create the 'osint_agents' database
   - Redis: Ensure Redis is running on localhost:6379
   - ChromaDB: Optional, for vector storage

4. Run tests to verify setup:
   cd ai_agent
   python -m pytest tests/

5. Start the AI Agent system:
   python src/api/main.py

For more information, see:
- ai_agent/docs/README.md
- ai_agent/DEVELOPMENT_ROADMAP.md
"""
        print(next_steps)


def main():
    """Main setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AI Agent development environment")
    parser.add_argument(
        "--project-root",
        help="Project root directory (default: auto-detect)",
        default=None
    )
    
    args = parser.parse_args()
    
    setup = EnvironmentSetup(args.project_root)
    success = setup.run_setup()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()