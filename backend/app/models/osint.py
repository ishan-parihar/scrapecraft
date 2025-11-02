from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class InvestigationClassification(str, Enum):
    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"


class InvestigationPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvestigationStatus(str, Enum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class InvestigationTargetType(str, Enum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DOMAIN = "DOMAIN"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    OTHER = "OTHER"


class TargetStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EvidenceSourceType(str, Enum):
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    PUBLIC_RECORDS = "PUBLIC_RECORDS"
    WEB_CONTENT = "WEB_CONTENT"
    DARK_WEB = "DARK_WEB"
    HUMINT = "HUMINT"


class AgentType(str, Enum):
    PLANNING = "PLANNING"
    COLLECTION = "COLLECTION"
    ANALYSIS = "ANALYSIS"
    SYNTHESIS = "SYNTHESIS"


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class InvestigationPhase(str, Enum):
    PLANNING = "planning"
    RECONNAISSANCE = "reconnaissance"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    REPORTING = "reporting"


class ThreatLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvestigationTarget(BaseModel):
    id: str
    type: InvestigationTargetType
    identifier: str
    aliases: List[str] = []
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    collection_requirements: List[str] = []
    status: TargetStatus = TargetStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IntelligenceRequirement(BaseModel):
    id: str
    title: str
    description: str
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    status: str = "ACTIVE"  # ACTIVE, COMPLETED, CANCELLED
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AgentAssignment(BaseModel):
    agent_id: str
    agent_type: AgentType
    assigned_targets: List[str] = []
    current_task: Optional[Dict[str, Any]] = None
    status: AgentStatus = AgentStatus.IDLE
    performance_metrics: Optional[Dict[str, Any]] = None
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceContent(BaseModel):
    type: str  # text, image, document, video, etc.
    data: str  # URL, file path, or raw text
    summary: Optional[str] = None
    tags: List[str] = []


class EvidenceMetadata(BaseModel):
    source_url: Optional[str] = None
    retrieved_date: Optional[datetime] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    hash: Optional[str] = None
    provenance: Optional[str] = None  # chain of custody info


class CollectedEvidence(BaseModel):
    id: str
    investigation_id: str
    source: str
    source_type: EvidenceSourceType
    content: EvidenceContent
    metadata: EvidenceMetadata
    reliability_score: float = 0.0  # 0.0 to 1.0
    relevance_score: float = 0.0  # 0.0 to 1.0
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False
    verification_notes: Optional[str] = None
    analyst_notes: Optional[str] = None


class AnalysisResult(BaseModel):
    id: str
    evidence_id: Optional[str] = None
    investigation_id: str
    analysis_type: str  # pattern, correlation, attribution, etc.
    results: Dict[str, Any]
    confidence: float = 0.0  # 0.0 to 1.0
    analyst_id: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: List[str] = []


class ThreatAssessment(BaseModel):
    id: str
    investigation_id: str
    title: str
    description: str
    threat_level: ThreatLevel
    threat_type: str  # cyber, physical, reputational, etc.
    targets: List[str] = []  # target IDs
    likelihood: float = 0.0  # 0.0 to 1.0
    impact: float = 0.0  # 0.0 to 1.0
    risk_score: float = 0.0  # 0.0 to 1.0 (calculated)
    status: str = "ACTIVE"  # ACTIVE, MONITORED, RESOLVED, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    analyst_notes: Optional[str] = None


class PhaseTransition(BaseModel):
    from_phase: InvestigationPhase
    to_phase: InvestigationPhase
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: Optional[str] = None
    triggered_by: str = "system"  # system, user, or agent


class InvestigationReport(BaseModel):
    id: str
    investigation_id: str
    title: str
    content: str
    format: str = "json"  # json, html, pdf
    classification: InvestigationClassification = InvestigationClassification.UNCLASSIFIED
    authors: List[str] = []
    recipients: List[str] = []
    status: str = "DRAFT"  # DRAFT, PENDING_REVIEW, APPROVED, DISTRIBUTED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    distributed_at: Optional[datetime] = None


class FinalAssessment(BaseModel):
    executive_summary: str
    key_findings: List[str] = []
    recommendations: List[Dict[str, Any]] = []  # {item: str, priority: str, action: str}
    confidence_level: float = 0.0  # 0.0 to 1.0
    overall_threat_level: ThreatLevel = ThreatLevel.LOW
    classification: InvestigationClassification = InvestigationClassification.UNCLASSIFIED


class Investigation(BaseModel):
    id: str
    title: str
    description: str
    classification: InvestigationClassification = InvestigationClassification.UNCLASSIFIED
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    status: InvestigationStatus = InvestigationStatus.PLANNING
    
    # Targets and Intelligence Requirements
    targets: List[InvestigationTarget] = []
    intelligence_requirements: List[IntelligenceRequirement] = []
    
    # Agent Coordination
    assigned_agents: List[AgentAssignment] = []
    active_phases: List[InvestigationPhase] = []
    
    # Evidence and Analysis
    collected_evidence: List[CollectedEvidence] = []
    analysis_results: List[AnalysisResult] = []
    threat_assessments: List[ThreatAssessment] = []
    
    # Workflow and Timeline
    current_phase: InvestigationPhase = InvestigationPhase.PLANNING
    phase_history: List[PhaseTransition] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Reporting
    generated_reports: List[InvestigationReport] = []
    final_assessment: Optional[FinalAssessment] = None

    # Helper methods
    def add_phase_transition(self, to_phase: InvestigationPhase, reason: str = "", triggered_by: str = "system"):
        """Add a phase transition to history."""
        transition = PhaseTransition(
            from_phase=self.current_phase,
            to_phase=to_phase,
            reason=reason,
            triggered_by=triggered_by
        )
        self.phase_history.append(transition)
        self.current_phase = to_phase
        self.updated_at = datetime.utcnow()

    def add_target(self, target: InvestigationTarget):
        """Add a target to the investigation."""
        self.targets.append(target)
        self.updated_at = datetime.utcnow()

    def add_evidence(self, evidence: CollectedEvidence):
        """Add collected evidence to the investigation."""
        self.collected_evidence.append(evidence)
        self.updated_at = datetime.utcnow()

    def add_threat_assessment(self, threat: ThreatAssessment):
        """Add a threat assessment to the investigation."""
        self.threat_assessments.append(threat)
        self.updated_at = datetime.utcnow()


class InvestigationCreate(BaseModel):
    title: str
    description: str
    classification: InvestigationClassification = InvestigationClassification.UNCLASSIFIED
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    intelligence_requirements: Optional[List[Dict[str, Any]]] = None


class InvestigationUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    classification: Optional[InvestigationClassification] = None
    priority: Optional[InvestigationPriority] = None
    status: Optional[InvestigationStatus] = None
    current_phase: Optional[InvestigationPhase] = None


class TargetCreate(BaseModel):
    type: InvestigationTargetType
    identifier: str
    aliases: List[str] = []
    priority: InvestigationPriority = InvestigationPriority.MEDIUM
    collection_requirements: List[str] = []


class EvidenceCreate(BaseModel):
    source: str
    source_type: EvidenceSourceType
    content: EvidenceContent
    metadata: EvidenceMetadata
    reliability_score: float = 0.0
    relevance_score: float = 0.0


class ThreatAssessmentCreate(BaseModel):
    title: str
    description: str
    threat_level: ThreatLevel
    threat_type: str
    targets: List[str] = []
    likelihood: float = 0.0
    impact: float = 0.0


class ReportCreate(BaseModel):
    title: str
    content: str
    format: str = "json"
    classification: InvestigationClassification = InvestigationClassification.UNCLASSIFIED
    recipients: List[str] = []