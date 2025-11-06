from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
import asyncio
import uuid
import logging

from app.services.scrapegraph import ScrapingService
from app.services.llm_integration import get_llm_service
from app.services.task_storage import task_storage
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

class ScrapingRequest(BaseModel):
    urls: List[HttpUrl]
    prompt: str
    scraping_schema: Optional[Dict] = None

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
        schema=request.scraping_schema
    )
    
    # Add to background tasks
    background_tasks.add_task(
        run_scraping_task,
        task_id,
        request.urls,
        request.prompt,
        request.scraping_schema
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
    # Use appropriate API key or None for local scraping
    api_key = settings.SCRAPEGRAPH_API_KEY if settings.SCRAPEGRAPH_API_KEY else None
    scraping_service = ScrapingService(api_key)
    
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
    try:
        # Implement preview functionality
        import aiohttp
        from bs4 import BeautifulSoup
        
        async with aiohttp.ClientSession(headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }) as session:
            async with session.get(str(url), timeout=30) as response:
                if response.status != 200:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Failed to fetch URL: HTTP {response.status}"
                    )
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract basic preview information
                title = soup.find('title')
                title_text = title.get_text().strip() if title else "No title found"
                
                # Extract meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                description = meta_desc.get('content', '') if meta_desc else "No description found"
                
                # Extract headings
                headings = []
                for h in soup.find_all(['h1', 'h2', 'h3']):
                    headings.append({
                        'tag': h.name,
                        'text': h.get_text().strip()[:100]  # Limit length
                    })
                
                # Extract links if selector provided
                links = []
                if selector:
                    try:
                        elements = soup.select(selector)
                        for element in elements[:10]:  # Limit to 10 elements
                            if element.name == 'a' and element.get('href'):
                                links.append({
                                    'text': element.get_text().strip()[:50],
                                    'href': element.get('href')
                                })
                            else:
                                links.append({
                                    'tag': element.name,
                                    'text': element.get_text().strip()[:100]
                                })
                    except Exception as selector_error:
                        logger.warning(f"Selector error: {selector_error}")
                        links = [{"error": f"Invalid selector: {selector}"}]
                
                # Extract content preview
                content_tags = soup.find_all(['p', 'div', 'article'])[:5]
                content_preview = ' '.join([tag.get_text().strip() for tag in content_tags])
                
                preview_data = {
                    "url": str(url),
                    "title": title_text,
                    "description": description,
                    "headings": headings[:5],  # Limit to 5 headings
                    "links": links,
                    "content_preview": content_preview[:500],  # Limit preview length
                    "content_length": len(content_preview),
                    "selector": selector,
                    "status": "success"
                }
                
                return preview_data
                
    except aiohttp.ClientTimeout:
        raise HTTPException(status_code=408, detail="Request timeout - URL took too long to respond")
    except aiohttp.ClientError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        logger.error(f"Preview error for {url}: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

class SearchRequest(BaseModel):
    query: str
    max_results: int = 5

@router.post("/search")
async def search_urls(request: SearchRequest):
    """Search for URLs based on a query with LLM enhancement."""
    try:
        # Get LLM service for query enhancement
        llm_service = await get_llm_service()
        
        # First, enhance the search query using LLM
        enhanced_search = await llm_service.enhance_search_query(
            original_query=request.query,
            search_context="OSINT investigation"
        )
        
        # Use enhanced queries or fallback to original
        enhanced_queries = enhanced_search.get("enhanced_queries", {})
        search_query = enhanced_queries.get("primary", request.query)
        
        # Use scraping service with appropriate configuration
        api_key = settings.SCRAPEGRAPH_API_KEY if settings.SCRAPEGRAPH_API_KEY else None
        scraping_service = ScrapingService(api_key)
        
        # Perform search with enhanced query
        results = await scraping_service.search_urls(search_query, request.max_results)
        
        # If no results, try with original query
        if not results and search_query != request.query:
            results = await scraping_service.search_urls(request.query, request.max_results)
        
        # Enhance results with LLM analysis if we have data
        enhanced_results = results
        if results and len(results) > 0:
            # Create context for LLM analysis
            context = {
                "surface_web": {"articles": results},
                "metadata": {"sources_used": ["search_results"]}
            }
            
            # Generate intelligence insights
            intelligence = await llm_service.generate_intelligence_insights(
                context=context,
                investigation_query=request.query
            )
            
            enhanced_results = {
                "search_results": results,
                "intelligence_insights": intelligence,
                "query_enhancement": enhanced_search,
                "llm_provider": llm_service.provider.name
            }
        
        return {
            "query": request.query,
            "enhanced_query": search_query,
            "max_results": request.max_results,
            "results": enhanced_results,
            "count": len(results) if isinstance(results, list) else len(results.get("search_results", [])),
            "llm_enhanced": True
        }
        
    except Exception as e:
        # Fallback to basic search without LLM
        try:
            api_key = settings.SCRAPEGRAPH_API_KEY if settings.SCRAPEGRAPH_API_KEY else None
            scraping_service = ScrapingService(api_key)
            results = await scraping_service.search_urls(request.query, request.max_results)
            
            return {
                "query": request.query,
                "max_results": request.max_results,
                "results": results,
                "count": len(results),
                "llm_enhanced": False,
                "fallback_mode": True
            }
        except Exception as fallback_error:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}, Fallback also failed: {str(fallback_error)}")