"""
Minimal FastAPI App for Testing Basic Structure
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(
    title="ScrapeCraft Backend - Minimal",
    version="0.1.0-minimal",
    description="Minimal version for testing basic structure"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "ScrapeCraft Backend",
        "version": "0.1.0-minimal",
        "status": "minimal_working",
        "message": "Basic structure is working - dependencies need to be installed"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "mode": "minimal"}

@app.get("/api/status")
async def api_status():
    return {
        "backend_integration": "in_progress",
        "phase": "8",
        "dependencies_missing": True,
        "available_apis": ["basic_endpoints_only"],
        "missing_apis": [
            "auth",
            "pipelines", 
            "scraping",
            "execution",
            "workflow",
            "osint",
            "ai_investigation"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)