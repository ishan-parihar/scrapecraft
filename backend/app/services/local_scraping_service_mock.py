from typing import List, Dict, Optional, Any
import asyncio
import logging
from pydantic import BaseModel, Field
from typing import List as ListType
import os

logger = logging.getLogger(__name__)

class LocalScrapingService:
    """Mock service for testing local ScrapeGraphAI functionality."""
    
    def __init__(self, llm_config: Optional[Dict] = None):
        # Use environment variables to configure LLM
        self.llm_config = llm_config or {
            "model": os.getenv("LOCAL_LLM_MODEL", "gpt-3.5-turbo"),
            "api_key": os.getenv("LOCAL_LLM_API_KEY", os.getenv("OPENAI_API_KEY", "fake-key-for-local")),
            "temperature": 0,
        }
        
        # Override model if using Ollama
        if os.getenv("USE_OLLAMA", "false").lower() == "true":
            self.llm_config = {
                "model": os.getenv("OLLAMA_MODEL", "llama3.2"),
                "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            }
    
    async def execute_pipeline(
        self,
        urls: List[str],
        schema: Optional[Dict[str, Any]],
        prompt: str
    ) -> List[Dict]:
        """Mock execute scraping for multiple URLs."""
        results = []
        
        try:
            for url in urls:
                # Mock scraping result in the expected format
                mock_data = {
                    "url": url,
                    "title": f"Mock Title for {url}",
                    "content": f"This is mock scraped content from {url}",
                    "status": "success",
                    "scraped_at": "2025-10-30T00:00:00Z",
                    "metadata": {
                        "model_used": self.llm_config.get("model", "unknown"),
                        "prompt": prompt,
                        "schema_provided": schema is not None
                    }
                }
                
                # If schema is provided, try to match it
                if schema:
                    for key in schema.keys():
                        if key not in mock_data:
                            mock_data[key] = f"Mock {key} value"
                
                # Return in the expected ScrapingResult format
                mock_result = {
                    "url": url,
                    "success": True,
                    "data": mock_data,
                    "error": None
                }
                
                results.append(mock_result)
                
            logger.info(f"Mock scraped {len(urls)} URLs successfully")
            return results
            
        except Exception as e:
            logger.error(f"Mock scraping failed: {e}")
            # Return error result for each URL in expected format
            return [{
                "url": url,
                "success": False,
                "data": None,
                "error": str(e)
            } for url in urls]