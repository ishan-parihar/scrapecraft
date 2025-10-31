from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
import asyncio
import uuid

from app.services.scrapegraph import ScrapingService
from app.services.task_storage import task_storage
from app.config import settings

router = APIRouter()

class ScrapingRequest(BaseModel):
    urls: List[HttpUrl]
    prompt: str
    schema: Optional[Dict] = None

class ScrapingResponse(BaseModel):
    task_id: str
    status: str
    message: str

class ScrapingResult(BaseModel):
    url: str
    success: bool
    data: Optional[Dict]
    error: Optional[str]

@router.post("/execute", response_model=ScrapingResponse)
async def execute_scraping(
    request: ScrapingRequest,
    background_tasks: BackgroundTasks
):
    """Execute a scraping job asynchronously."""
    task_id = str(uuid.uuid4())
    
    # Create task in Redis
    await task_storage.create_task(
        task_id=task_id,
        urls=[str(url) for url in request.urls],
        prompt=request.prompt,
        schema=request.schema
    )
    
    # Add to background tasks
    background_tasks.add_task(
        run_scraping_task,
        task_id,
        request.urls,
        request.prompt,
        request.schema
    )
    
    return ScrapingResponse(
        task_id=task_id,
        status="pending",
        message="Scraping task started"
    )

async def run_scraping_task(
    task_id: str,
    urls: List[str],
    prompt: str,
    schema: Optional[Dict]
):
    """Run the actual scraping task."""
    scraping_service = ScrapingService(settings.SCRAPEGRAPH_API_KEY)
    
    try:
        await task_storage.update_task_status(task_id, "running")
        
        results = await scraping_service.execute_pipeline(
            urls=[str(url) for url in urls],
            schema=schema,
            prompt=prompt
        )
        
        await task_storage.update_task_status(
            task_id, 
            "completed", 
            results=results
        )
        
    except Exception as e:
        await task_storage.update_task_status(
            task_id, 
            "failed", 
            error=str(e)
        )

@router.get("/status/{task_id}")
async def get_scraping_status(task_id: str):
    """Get the status of a scraping task."""
    task = await task_storage.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task_id,
        "status": task["status"],
        "error": task.get("error")
    }

@router.get("/results/{task_id}", response_model=List[ScrapingResult])
async def get_scraping_results(task_id: str):
    """Get the results of a completed scraping task."""
    task = await task_storage.get_task(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task is {task['status']}, not completed"
        )
    
    return task["results"]

@router.post("/validate-url")
async def validate_url(url: HttpUrl):
    """Validate if a URL is accessible."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.head(str(url), follow_redirects=True)
            
            return {
                "url": str(url),
                "valid": response.status_code < 400,
                "status_code": response.status_code,
                "content_type": response.headers.get("content-type", "")
            }
    except Exception as e:
        return {
            "url": str(url),
            "valid": False,
            "error": str(e)
        }

@router.post("/preview")
async def preview_scraping(url: HttpUrl, selector: Optional[str] = None):
    """Preview what would be scraped from a URL."""
    # TODO: Implement preview functionality
    return {
        "url": str(url),
        "preview": "Preview functionality not yet implemented",
        "selector": selector
    }

@router.post("/search")
async def search_urls(query: str, max_results: int = 5):
    """Search for URLs based on a query."""
    try:
        scraping_service = ScrapingService(settings.SCRAPEGRAPH_API_KEY)
        results = await scraping_service.search_urls(query, max_results)
        
        return {
            "query": query,
            "max_results": max_results,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")