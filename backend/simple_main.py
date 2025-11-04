from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ScrapeCraft Backend",
    version="1.0.0",
    description="Backend for ScrapeCraft OSINT and scraping platform"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:80"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "ScrapeCraft Backend",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include OSINT router with error handling
try:
    from app.api.osint import router as osint_router
    app.include_router(osint_router, prefix="/api/osint", tags=["osint"])
    logger.info("OSINT router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load OSINT router: {e}")

# Import other routers gradually
try:
    from app.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    logger.info("Auth router loaded successfully")
except Exception as e:
    logger.error(f"Failed to load auth router: {e}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting simplified ScrapeCraft backend...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)