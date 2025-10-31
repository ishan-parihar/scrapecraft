#!/usr/bin/env python3
"""
ScrapeGraph Enhanced - Setup Script
Automated setup and verification for the enhanced scraping service.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description="", check=True):
    """Run a shell command and handle errors."""
    print(f"🔄 {description}")
    try:
        result = subprocess.run(command, shell=True, check=check, 
                              capture_output=True, text=True, cwd="backend")
        if result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr.strip() if e.stderr.strip() else str(e)}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} - Need Python 3.8+")
        return False

def create_virtual_environment():
    """Create or activate virtual environment."""
    print("📦 Setting up virtual environment...")
    
    venv_path = Path("backend/venv")
    if not venv_path.exists():
        print("   Creating new virtual environment...")
        success = run_command("python -m venv venv", "Creating venv")
        if not success:
            return False
    else:
        print("   ✅ Virtual environment already exists")
    
    return True

def get_activate_command():
    """Get the appropriate activation command for the platform."""
    if platform.system() == "Windows":
        return "venv\\Scripts\\activate"
    else:
        return "source venv/bin/activate"

def install_dependencies():
    """Install required dependencies."""
    print("📚 Installing dependencies...")
    
    # Core dependencies
    deps = [
        "fastapi>=0.111.0",
        "uvicorn[standard]>=0.30.0",
        "httpx>=0.27.0",
        "beautifulsoup4>=4.12.0",
        "html2text>=2020.1.16",
        "openai>=1.0.0",
        "pydantic>=2.10.0",
        "redis>=5.0.0"
    ]
    
    for dep in deps:
        success = run_command(f"pip install {dep}", f"Installing {dep}")
        if not success:
            return False
    
    print("   ✅ All dependencies installed")
    return True

def create_env_file():
    """Create .env file if it doesn't exist."""
    print("⚙️ Setting up environment configuration...")
    
    env_path = Path("backend/.env")
    if not env_path.exists():
        env_content = """# ScrapeGraph Enhanced Configuration
# OpenAI Configuration (Optional - removes "LIMITED FUNCTIONALITY" warning)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1

# Redis Configuration (for task storage)
REDIS_URL=redis://localhost:6379

# Application Settings
USE_LOCAL_SCRAPING=true
SCRAPEGRAPH_API_KEY=not-used-with-local-scraping

# Server Settings
HOST=0.0.0.0
PORT=8000
"""
        
        with open(env_path, 'w') as f:
            f.write(env_content)
        
        print("   ✅ Created .env file with default configuration")
        print("   📝 Edit backend/.env to add your OpenAI API key (optional)")
    else:
        print("   ✅ .env file already exists")
    
    return True

def test_imports():
    """Test if all modules can be imported."""
    print("🧪 Testing module imports...")
    
    test_script = '''
import sys
sys.path.append(".")

try:
    from app.services.enhanced_scraping_service import EnhancedScrapingService
    print("   ✅ Enhanced scraping service")
except ImportError as e:
    print(f"   ❌ Enhanced scraping service: {e}")
    sys.exit(1)

try:
    import fastapi
    print("   ✅ FastAPI")
except ImportError as e:
    print(f"   ❌ FastAPI: {e}")
    sys.exit(1)

try:
    import httpx
    print("   ✅ HTTPX")
except ImportError as e:
    print(f"   ❌ HTTPX: {e}")
    sys.exit(1)

try:
    import bs4
    print("   ✅ BeautifulSoup")
except ImportError as e:
    print(f"   ❌ BeautifulSoup: {e}")
    sys.exit(1)

try:
    import html2text
    print("   ✅ HTML2Text")
except ImportError as e:
    print(f"   ❌ HTML2Text: {e}")
    sys.exit(1)

print("   ✅ All modules imported successfully")
'''
    
    success = run_command(f"python3 -c '{test_script}'", "Testing imports", check=False)
    return success

def test_scraping_service():
    """Test the scraping service with a simple example."""
    print("🌐 Testing scraping service...")
    
    test_script = '''
import asyncio
import sys
sys.path.append(".")

from app.services.enhanced_scraping_service import EnhancedScrapingService

async def test():
    service = EnhancedScrapingService()
    try:
        # Test validation
        is_valid = await service.validate_config()
        if is_valid:
            print("   ✅ Service configuration valid")
            
            # Test basic scraping
            results = await service.execute_pipeline(
                urls=["https://example.com"],
                schema=None,
                prompt="Extract main title"
            )
            
            if results and results[0]["success"]:
                data = results[0]["data"]
                print(f"   ✅ Successfully scraped: {data.get('title', 'N/A')}")
                return True
            else:
                print(f"   ❌ Scraping failed: {results[0].get('error', 'Unknown')}")
                return False
        else:
            print("   ❌ Service configuration invalid")
            return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False
    finally:
        await service.http_client.aclose()

result = asyncio.run(test())
sys.exit(0 if result else 1)
'''
    
    success = run_command(f"python3 -c '{test_script}'", "Testing scraping service", check=False)
    return success

def create_start_script():
    """Create a convenient start script."""
    print("🚀 Creating start script...")
    
    if platform.system() == "Windows":
        script_content = '''@echo off
echo Starting ScrapeGraph Enhanced...
cd backend
call venv\\Scripts\\activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
'''
        script_name = "start_scrapegraph.bat"
    else:
        script_content = '''#!/bin/bash
echo "🚀 Starting ScrapeGraph Enhanced..."
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
'''
        script_name = "start_scrapegraph.sh"
    
    with open(script_name, 'w') as f:
        f.write(script_content)
    
    if platform.system() != "Windows":
        os.chmod(script_name, 0o755)
    
    print(f"   ✅ Created {script_name}")
    return True

def print_success_message():
    """Print success message and next steps."""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📋 What's been set up:")
    print("   ✅ Virtual environment with dependencies")
    print("   ✅ Enhanced scraping service")
    print("   ✅ Environment configuration")
    print("   ✅ Start scripts")
    print("   ✅ Comprehensive documentation")
    
    print("\n🚀 Quick Start Options:")
    print("   1. Use the start script:")
    if platform.system() == "Windows":
        print("      .\\start_scrapegraph.bat")
    else:
        print("      ./start_scrapegraph.sh")
    
    print("   2. Start manually:")
    print("      cd backend")
    print(f"      {get_activate_command()}")
    print("      uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload")
    
    print("\n📖 Documentation:")
    print("   • SCRAPEGRAPH_USER_GUIDE.md - Detailed user guide")
    print("   • README_SCRAPING.md - Complete documentation")
    print("   • example_usage.py - Code examples")
    print("   • http://localhost:8000/docs - API documentation")
    
    print("\n🧪 Test the service:")
    print("   curl -X POST 'http://localhost:8000/api/scraping/execute' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"urls\": [\"https://example.com\"], \"prompt\": \"Extract title\"}'")
    
    print("\n💡 Pro Tips:")
    print("   • Add OPENAI_API_KEY to backend/.env for AI enhancement")
    print("   • Use structured schemas for better data extraction")
    print("   • Process multiple URLs in batches for efficiency")
    print("   • Check the API docs at /docs for all endpoints")
    
    print("\n" + "="*60)

def main():
    """Main setup function."""
    print("🔧 ScrapeGraph Enhanced - Setup Script")
    print("="*60)
    
    # Change to backend directory
    if not Path("backend").exists():
        print("❌ Backend directory not found. Please run from project root.")
        sys.exit(1)
    
    os.chdir("backend")
    
    # Run setup steps
    steps = [
        ("Python Version", check_python_version),
        ("Virtual Environment", create_virtual_environment),
        ("Dependencies", install_dependencies),
        ("Environment File", create_env_file),
        ("Module Imports", test_imports),
        ("Scraping Service", test_scraping_service),
        ("Start Script", create_start_script),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n{step_name}:")
        if not step_func():
            failed_steps.append(step_name)
            print(f"   ❌ {step_name} failed")
        else:
            print(f"   ✅ {step_name} completed")
    
    # Return to project root for final message
    os.chdir("..")
    
    if failed_steps:
        print(f"\n❌ Setup failed at: {', '.join(failed_steps)}")
        print("Please check the errors above and try again.")
        sys.exit(1)
    else:
        print_success_message()

if __name__ == "__main__":
    main()