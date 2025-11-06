from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.agents.openrouter_agent import openrouter_agent
from app.models.chat import ChatMessage, ChatResponse
from app.services.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()

class MessageRequest(BaseModel):
    message: str
    pipeline_id: str
    context: Optional[Dict] = None

class MessageResponse(BaseModel):
    response: str
    urls: List[str]
    schema: Dict
    code: Optional[str]
    results: List[Dict]
    status: str
    timestamp: datetime

@router.post("/message", response_model=MessageResponse)
async def send_message(request: MessageRequest):
    """Send a message to the scraping agent and get a response."""
    try:
        result = await openrouter_agent.process_message(
            message=request.message,
            pipeline_id=request.pipeline_id,
            context=request.context
        )
        
        return MessageResponse(
            response=result["response"],
            urls=result["urls"],
            schema=result["schema"],
            code=result.get("code"),
            results=result.get("results", []),
            status=result["status"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{pipeline_id}")
async def get_chat_history(pipeline_id: str, limit: int = 50):
    """Get chat history for a specific pipeline."""
    try:
        # Implement database query using file-based storage
        import json
        from pathlib import Path
        
        chat_dir = Path("chat_history")
        chat_dir.mkdir(exist_ok=True)
        
        chat_file = chat_dir / f"{pipeline_id}.json"
        
        if chat_file.exists():
            with open(chat_file, 'r') as f:
                chat_data = json.load(f)
            
            messages = chat_data.get("messages", [])
            
            # Apply limit
            if limit > 0:
                messages = messages[-limit:]
            
            return {
                "pipeline_id": pipeline_id,
                "messages": messages,
                "total": len(chat_data.get("messages", []))
            }
        else:
            return {
                "pipeline_id": pipeline_id,
                "messages": [],
                "total": 0
            }
    except Exception as e:
        logger.error(f"Failed to get chat history for {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")

@router.delete("/history/{pipeline_id}")
async def clear_chat_history(pipeline_id: str):
    """Clear chat history for a specific pipeline."""
    try:
        # Implement database deletion using file-based storage
        from pathlib import Path
        
        chat_dir = Path("chat_history")
        chat_file = chat_dir / f"{pipeline_id}.json"
        
        if chat_file.exists():
            chat_file.unlink()
            logger.info(f"Cleared chat history for pipeline {pipeline_id}")
        
        return {"message": "Chat history cleared successfully"}
    except Exception as e:
        logger.error(f"Failed to clear chat history for {pipeline_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")

@router.post("/feedback")
async def submit_feedback(
    pipeline_id: str,
    message_id: str,
    feedback: str,
    rating: Optional[int] = None
):
    """Submit feedback for a specific message."""
    try:
        # Store feedback in database using file-based storage
        import json
        from pathlib import Path
        from datetime import datetime
        
        feedback_dir = Path("feedback_storage")
        feedback_dir.mkdir(exist_ok=True)
        
        feedback_file = feedback_dir / f"{pipeline_id}_feedback.json"
        
        # Load existing feedback
        feedback_data = []
        if feedback_file.exists():
            with open(feedback_file, 'r') as f:
                feedback_data = json.load(f)
        
        # Add new feedback
        new_feedback = {
            "message_id": message_id,
            "feedback": feedback,
            "rating": rating,
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline_id": pipeline_id
        }
        
        feedback_data.append(new_feedback)
        
        # Save feedback
        with open(feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2)
        
        logger.info(f"Stored feedback for pipeline {pipeline_id}, message {message_id}")
        
        return {"message": "Feedback submitted successfully"}
    except Exception as e:
        logger.error(f"Failed to store feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")