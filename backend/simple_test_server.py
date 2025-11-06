#!/usr/bin/env python3
"""
Simple server runner for testing
"""
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")