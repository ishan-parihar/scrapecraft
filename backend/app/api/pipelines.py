from fastapi import APIRouter, Depends, Query
from typing import List, Dict, Optional
from datetime import datetime
import uuid
import logging

from app.api.common.responses import (
    APIResponse, ErrorCode, ValidationError, NotFoundError,
    create_success_response, create_error_response,
    create_paginated_response, validate_required_fields
)
from app.api.common.schemas import (
    Pipeline, PipelineCreate, PipelineUpdate, Status,
    PaginationRequest
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipelines", tags=["Pipelines"])

# In-memory storage for demonstration (replace with database)
pipelines_store = {}

@router.post("", response_model=APIResponse)
async def create_pipeline(pipeline_data: PipelineCreate) -> APIResponse:
    """
    Create a new scraping pipeline.
    
    Args:
        pipeline_data: Pipeline creation data
        
    Returns:
        APIResponse with created pipeline
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        # Validate required fields
        validate_required_fields(
            pipeline_data.dict(),
            ["name", "description"]
        )
        
        # Create pipeline
        pipeline_id = str(uuid.uuid4())
        new_pipeline = Pipeline(
            id=pipeline_id,
            name=pipeline_data.name,
            description=pipeline_data.description,
            urls=pipeline_data.urls or [],
            extraction_schema=pipeline_data.extraction_schema or {},
            code="",
            status=Status.IDLE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        pipelines_store[pipeline_id] = new_pipeline
        
        logger.info(f"Created pipeline: {pipeline_id}")
        
        return create_success_response(
            data=new_pipeline.dict(),
            message="Pipeline created successfully"
        )
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Create pipeline error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to create pipeline",
            details={"error": str(e)}
        )

@router.get("/{pipeline_id}", response_model=APIResponse)
async def get_pipeline(pipeline_id: str) -> APIResponse:
    """
    Get a specific pipeline by ID.
    
    Args:
        pipeline_id: Pipeline ID
        
    Returns:
        APIResponse with pipeline data
        
    Raises:
        NotFoundError: If pipeline not found
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        return create_success_response(
            data=pipeline.dict(),
            message="Pipeline retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Get pipeline error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve pipeline",
            details={"error": str(e)}
        )

@router.get("", response_model=APIResponse)
async def list_pipelines(
    pagination: PaginationRequest = Depends(),
    search: Optional[str] = Query(None, description="Search term"),
    status: Optional[Status] = Query(None, description="Filter by status")
) -> APIResponse:
    """
    List pipelines with filtering and pagination.
    
    Args:
        pagination: Pagination parameters
        search: Search term
        status: Filter by status
        
    Returns:
        APIResponse with paginated pipelines
    """
    try:
        # Get all pipelines
        pipelines = list(pipelines_store.values())
        
        # Apply filters
        if status:
            pipelines = [p for p in pipelines if p.status == status]
        if search:
            search_lower = search.lower()
            pipelines = [
                p for p in pipelines 
                if search_lower in p.name.lower() or search_lower in p.description.lower()
            ]
        
        # Sort by creation date (newest first)
        pipelines.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total = len(pipelines)
        start_idx = (pagination.page - 1) * pagination.page_size
        end_idx = start_idx + pagination.page_size
        paginated_items = pipelines[start_idx:end_idx]
        
        return create_paginated_response(
            items=[pipeline.dict() for pipeline in paginated_items],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size
        )
        
    except Exception as e:
        logger.error(f"List pipelines error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve pipelines",
            details={"error": str(e)}
        )

@router.put("/{pipeline_id}", response_model=APIResponse)
async def update_pipeline(
    pipeline_id: str,
    update_data: PipelineUpdate
) -> APIResponse:
    """
    Update an existing pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        update_data: Update data
        
    Returns:
        APIResponse with updated pipeline
        
    Raises:
        NotFoundError: If pipeline not found
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(pipeline, field, value)
        
        pipeline.updated_at = datetime.utcnow()
        
        logger.info(f"Updated pipeline: {pipeline_id}")
        
        return create_success_response(
            data=pipeline.dict(),
            message="Pipeline updated successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Update pipeline error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to update pipeline",
            details={"error": str(e)}
        )

@router.delete("/{pipeline_id}", response_model=APIResponse)
async def delete_pipeline(pipeline_id: str) -> APIResponse:
    """
    Delete a pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        
    Returns:
        APIResponse with success message
        
    Raises:
        NotFoundError: If pipeline not found
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        # Check if pipeline can be deleted
        if pipeline.status == Status.RUNNING:
            raise ValidationError(
                message="Cannot delete pipeline that is currently running",
                details={"status": pipeline.status}
            )
        
        del pipelines_store[pipeline_id]
        
        logger.info(f"Deleted pipeline: {pipeline_id}")
        
        return create_success_response(
            message="Pipeline deleted successfully"
        )
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Delete pipeline error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to delete pipeline",
            details={"error": str(e)}
        )

@router.post("/{pipeline_id}/run", response_model=APIResponse)
async def run_pipeline(pipeline_id: str) -> APIResponse:
    """
    Execute a scraping pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        
    Returns:
        APIResponse with execution status
        
    Raises:
        NotFoundError: If pipeline not found
        ValidationError: If pipeline cannot be run
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        # Validate pipeline can run
        if not pipeline.urls:
            raise ValidationError(
                message="No URLs defined in pipeline",
                details={"field": "urls"}
            )
        
        if not pipeline.extraction_schema:
            raise ValidationError(
                message="No extraction schema defined in pipeline",
                details={"field": "extraction_schema"}
            )
        
        if pipeline.status == Status.RUNNING:
            raise ValidationError(
                message="Pipeline is already running",
                details={"status": pipeline.status}
            )
        
        # Update status to running
        pipeline.status = Status.RUNNING
        pipeline.updated_at = datetime.utcnow()
        
        logger.info(f"Started pipeline execution: {pipeline_id}")
        
        # Execute scraping through the agent service
        try:
            from app.services.local_scraping_service import LocalScrapingService
            from app.agents.specialized.collection.surface_web_collector import SurfaceWebCollector
            
            # Initialize scraping service
            scraping_service = LocalScrapingService()
            
            # Execute pipeline with real scraping
            results = await scraping_service.execute_pipeline(
                urls=pipeline.config.urls,
                schema=pipeline.config.schema_dict,
                prompt=pipeline.config.prompt
            )
            
            # Update pipeline with results
            pipeline.results = results
            pipeline.status = Status.COMPLETED if all(r.get('success', False) for r in results) else Status.FAILED
            pipeline.updated_at = datetime.utcnow()
            
            # Store results
            successful_results = [r for r in results if r.get('success', False)]
            failed_results = [r for r in results if not r.get('success', False)]
            
            logger.info(f"Pipeline {pipeline_id} completed: {len(successful_results)} successful, {len(failed_results)} failed")
            
        except Exception as execution_error:
            logger.error(f"Pipeline execution failed: {execution_error}")
            pipeline.status = Status.FAILED
            pipeline.error = str(execution_error)
            pipeline.updated_at = datetime.utcnow()
        
        return create_success_response(
            data={
                "pipeline_id": pipeline_id,
                "status": pipeline.status.value,
                "message": "Pipeline execution started"
            },
            message="Pipeline execution started successfully"
        )
        
    except (NotFoundError, ValidationError):
        raise
    except Exception as e:
        logger.error(f"Run pipeline error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to run pipeline",
            details={"error": str(e)}
        )

@router.get("/{pipeline_id}/status", response_model=APIResponse)
async def get_pipeline_status(pipeline_id: str) -> APIResponse:
    """
    Get the current status of a pipeline.
    
    Args:
        pipeline_id: Pipeline ID
        
    Returns:
        APIResponse with pipeline status
        
    Raises:
        NotFoundError: If pipeline not found
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        status_data = {
            "pipeline_id": pipeline_id,
            "status": pipeline.status.value,
            "updated_at": pipeline.updated_at.isoformat(),
            "created_at": pipeline.created_at.isoformat()
        }
        
        return create_success_response(
            data=status_data,
            message="Pipeline status retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Get pipeline status error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve pipeline status",
            details={"error": str(e)}
        )

@router.get("/{pipeline_id}/results", response_model=APIResponse)
async def get_pipeline_results(pipeline_id: str) -> APIResponse:
    """
    Get the results of a pipeline execution.
    
    Args:
        pipeline_id: Pipeline ID
        
    Returns:
        APIResponse with pipeline results
        
    Raises:
        NotFoundError: If pipeline not found
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        # Retrieve actual results from storage
        results = pipeline.results or []
        
        # Calculate statistics
        total_results = len(results)
        successful_results = len([r for r in results if r.get('success', False)])
        failed_results = total_results - successful_results
        
        results_data = {
            "pipeline_id": pipeline_id,
            "results": results,
            "total": total_results,
            "success": successful_results,
            "failed": failed_results,
            "status": pipeline.status.value,
            "config": {
                "urls": pipeline.config.urls,
                "prompt": pipeline.config.prompt,
                "schema_provided": pipeline.config.schema_dict is not None
            },
            "execution_time": (pipeline.updated_at - pipeline.created_at).total_seconds() if pipeline.updated_at and pipeline.created_at else None
        }
        
        if pipeline.error:
            results_data["error"] = pipeline.error
        
        return create_success_response(
            data=results_data,
            message="Pipeline results retrieved successfully"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Get pipeline results error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to retrieve pipeline results",
            details={"error": str(e)}
        )

@router.post("/{pipeline_id}/export", response_model=APIResponse)
async def export_pipeline_results(
    pipeline_id: str,
    format: str = Query("json", regex="^(json|csv|excel)$")
) -> APIResponse:
    """
    Export pipeline results in various formats.
    
    Args:
        pipeline_id: Pipeline ID
        format: Export format
        
    Returns:
        APIResponse with export information
        
    Raises:
        NotFoundError: If pipeline not found
        ValidationError: If format is invalid
    """
    try:
        if pipeline_id not in pipelines_store:
            raise NotFoundError("Pipeline")
        
        pipeline = pipelines_store[pipeline_id]
        
        # Implement export functionality
        import json
        import csv
        from io import StringIO
        import tempfile
        import os
        
        results = pipeline.results or []
        
        if not results:
            raise create_error_response(
                error_code=ErrorCode.NOT_FOUND,
                message="No results to export",
                details={"pipeline_id": pipeline_id}
            )
        
        # Create export file
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"pipeline_{pipeline_id}_{timestamp}.{format}"
        
        if format == "json":
            export_content = json.dumps({
                "pipeline_id": pipeline_id,
                "export_timestamp": datetime.utcnow().isoformat(),
                "pipeline_config": {
                    "urls": pipeline.config.urls,
                    "prompt": pipeline.config.prompt,
                    "schema_provided": pipeline.config.schema_dict is not None
                },
                "results": results,
                "summary": {
                    "total": len(results),
                    "successful": len([r for r in results if r.get('success', False)]),
                    "failed": len([r for r in results if not r.get('success', False)])
                }
            }, indent=2)
            
        elif format == "csv":
            # Flatten results for CSV
            output = StringIO()
            if results:
                fieldnames = ["url", "success", "error", "title", "content", "scraped_at"]
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    row = {
                        "url": result.get("url", ""),
                        "success": result.get("success", False),
                        "error": result.get("error", ""),
                        "title": result.get("data", {}).get("title", ""),
                        "content": result.get("data", {}).get("content", "")[:500],  # Limit content
                        "scraped_at": result.get("data", {}).get("scraped_at", "")
                    }
                    writer.writerow(row)
            
            export_content = output.getvalue()
            output.close()
            
        else:  # excel
            # For now, return JSON as excel placeholder
            export_content = json.dumps({"error": "Excel export not yet implemented"}, indent=2)
            format = "json"  # Fallback to JSON
        
        # Save to temporary file
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(export_content)
        
        export_data = {
            "pipeline_id": pipeline_id,
            "format": format,
            "filename": filename,
            "download_url": f"/api/v1/pipelines/{pipeline_id}/download/{format}",
            "file_size": len(export_content),
            "expires_at": (datetime.utcnow().timestamp() + 3600),  # 1 hour expiry
            "summary": {
                "total_results": len(results),
                "successful": len([r for r in results if r.get('success', False)]),
                "failed": len([r for r in results if not r.get('success', False)])
            }
        }
        
        logger.info(f"Exported pipeline {pipeline_id} results as {format}")
        
        return create_success_response(
            data=export_data,
            message=f"Results exported as {format}"
        )
        
    except NotFoundError:
        raise
    except Exception as e:
        logger.error(f"Export pipeline results error: {e}")
        raise create_error_response(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="Failed to export pipeline results",
            details={"error": str(e)}
        )