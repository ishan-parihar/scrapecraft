"""
State management for OSINT investigations.
Replaces the missing ai_agent.src.workflow.state module.
"""

from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import uuid


class InvestigationPhase(Enum):
    """Investigation phases."""
    INITIALIZATION = "initialization"
    PLANNING = "planning"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    REPORTING = "reporting"
    COMPLETED = "completed"


class InvestigationStatus(Enum):
    """Investigation status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Priority(Enum):
    """Investigation priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class InvestigationState:
    """Complete investigation state."""
    # Core identification
    investigation_id: str
    user_request: str
    initiator: str = "system"
    priority: str = "medium"
    
    # Phase and status tracking
    phase: InvestigationPhase = InvestigationPhase.INITIALIZATION
    status: InvestigationStatus = InvestigationStatus.PENDING
    overall_status: str = "pending"  # Backward compatibility
    
    # Timestamps
    initiated_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Investigation components
    objectives: Dict[str, Any] = field(default_factory=dict)
    strategy: Dict[str, Any] = field(default_factory=dict)
    collected_data: Dict[str, Any] = field(default_factory=dict)
    analysis_results: Dict[str, Any] = field(default_factory=dict)
    intelligence: Dict[str, Any] = field(default_factory=dict)
    fused_data: Dict[str, Any] = field(default_factory=dict)  # Backward compatibility
    patterns: list = field(default_factory=list)
    context_analysis: Dict[str, Any] = field(default_factory=dict)  # Backward compatibility
    quality_assessment: Dict[str, Any] = field(default_factory=dict)  # Backward compatibility
    
    # Metadata and tracking
    sources_used: list = field(default_factory=list)
    agents_executed: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    confidence_level: float = 0.0
    progress_percentage: float = 0.0
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "investigation_id": self.investigation_id,
            "user_request": self.user_request,
            "initiator": self.initiator,
            "priority": self.priority,
            "phase": self.phase.value,
            "status": self.status.value,
            "overall_status": self.status.value,  # Backward compatibility
            "initiated_at": self.initiated_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "objectives": self.objectives,
            "strategy": self.strategy,
            "collected_data": self.collected_data,
            "analysis_results": self.analysis_results,
            "intelligence": self.intelligence,
            "fused_data": self.fused_data,  # Backward compatibility
            "patterns": self.patterns,
            "context_analysis": self.context_analysis,  # Backward compatibility
            "quality_assessment": self.quality_assessment,  # Backward compatibility
            "sources_used": self.sources_used,
            "agents_executed": self.agents_executed,
            "errors": self.errors,
            "confidence_level": self.confidence_level,
            "progress_percentage": self.progress_percentage,
            "metadata": self.metadata
        }


def create_initial_state(
    user_request: str,
    investigation_id: Optional[str] = None,
    initiator: str = "system",
    priority: str = "medium"
) -> Dict[str, Any]:
    """Create initial investigation state."""
    
    if not investigation_id:
        investigation_id = f"inv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    state = InvestigationState(
        investigation_id=investigation_id,
        user_request=user_request,
        initiator=initiator,
        priority=priority,
        phase=InvestigationPhase.INITIALIZATION,
        status=InvestigationStatus.PENDING
    )
    
    return state.to_dict()