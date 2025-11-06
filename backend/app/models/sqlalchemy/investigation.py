"""
Investigation-related SQLAlchemy models.
"""

from sqlalchemy import Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ARRAY
from .base import Base
from enum import Enum as PyEnum
from datetime import datetime
import uuid


# Enums
class InvestigationClassification(PyEnum):
    UNCLASSIFIED = "UNCLASSIFIED"
    CONFIDENTIAL = "CONFIDENTIAL"
    SECRET = "SECRET"
    TOP_SECRET = "TOP_SECRET"


class InvestigationPriority(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class InvestigationStatus(PyEnum):
    PLANNING = "PLANNING"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class InvestigationPhase(PyEnum):
    PLANNING = "planning"
    RECONNAISSANCE = "reconnaissance"
    COLLECTION = "collection"
    ANALYSIS = "analysis"
    SYNTHESIS = "synthesis"
    REPORTING = "reporting"


class InvestigationTargetType(PyEnum):
    PERSON = "PERSON"
    ORGANIZATION = "ORGANIZATION"
    LOCATION = "LOCATION"
    DOMAIN = "DOMAIN"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    OTHER = "OTHER"


class TargetStatus(PyEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EvidenceSourceType(PyEnum):
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    PUBLIC_RECORDS = "PUBLIC_RECORDS"
    WEB_CONTENT = "WEB_CONTENT"
    DARK_WEB = "DARK_WEB"
    HUMINT = "HUMINT"


class AgentType(PyEnum):
    PLANNING = "PLANNING"
    COLLECTION = "COLLECTION"
    ANALYSIS = "ANALYSIS"
    SYNTHESIS = "SYNTHESIS"


class AgentStatus(PyEnum):
    IDLE = "IDLE"
    ACTIVE = "ACTIVE"
    WAITING = "WAITING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class ThreatLevel(PyEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Main Investigation Model
class Investigation(Base):
    """Main investigation model."""
    
    __tablename__ = "investigations"
    
    # Basic fields
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Classification and priority
    classification: Mapped[InvestigationClassification] = mapped_column(Enum(InvestigationClassification), nullable=False)
    priority: Mapped[InvestigationPriority] = mapped_column(Enum(InvestigationPriority), nullable=False)
    status: Mapped[InvestigationStatus] = mapped_column(Enum(InvestigationStatus), nullable=False)
    
    # Workflow
    current_phase: Mapped[InvestigationPhase] = mapped_column(Enum(InvestigationPhase), nullable=False)
    
    # Timestamps (inherited from Base: created_at, updated_at, deleted_at)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    targets = relationship("InvestigationTarget", back_populates="investigation", cascade="all, delete-orphan")
    intelligence_requirements = relationship("IntelligenceRequirement", back_populates="investigation", cascade="all, delete-orphan")
    agent_assignments = relationship("AgentAssignment", back_populates="investigation", cascade="all, delete-orphan")
    collected_evidence = relationship("CollectedEvidence", back_populates="investigation", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResult", back_populates="investigation", cascade="all, delete-orphan")
    threat_assessments = relationship("ThreatAssessment", back_populates="investigation", cascade="all, delete-orphan")
    phase_transitions = relationship("PhaseTransition", back_populates="investigation", cascade="all, delete-orphan")
    reports = relationship("InvestigationReport", back_populates="investigation", cascade="all, delete-orphan")
    final_assessment = relationship("FinalAssessment", back_populates="investigation", cascade="all, delete-orphan", uselist=False)


class InvestigationTarget(Base):
    """Investigation targets."""
    
    __tablename__ = "investigation_targets"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    type: Mapped[InvestigationTargetType] = mapped_column(Enum(InvestigationTargetType), nullable=False)
    identifier: Mapped[str] = mapped_column(String, nullable=False)
    aliases: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    
    priority: Mapped[InvestigationPriority] = mapped_column(Enum(InvestigationPriority), nullable=False)
    collection_requirements: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    status: Mapped[TargetStatus] = mapped_column(Enum(TargetStatus), nullable=False)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="targets")


class IntelligenceRequirement(Base):
    """Intelligence requirements for investigations."""
    
    __tablename__ = "intelligence_requirements"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    priority: Mapped[InvestigationPriority] = mapped_column(Enum(InvestigationPriority), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    
    # Relationships
    investigation = relationship("Investigation", back_populates="intelligence_requirements")


class AgentAssignment(Base):
    """Agent assignments for investigations."""
    
    __tablename__ = "agent_assignments"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    agent_id: Mapped[str] = mapped_column(String, nullable=False)
    agent_type: Mapped[AgentType] = mapped_column(Enum(AgentType), nullable=False)
    
    assigned_targets: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    current_task: Mapped[dict] = mapped_column(JSON, nullable=True)
    status: Mapped[AgentStatus] = mapped_column(Enum(AgentStatus), nullable=False)
    performance_metrics: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="agent_assignments")


class CollectedEvidence(Base):
    """Collected evidence for investigations."""
    
    __tablename__ = "collected_evidence"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    source: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[EvidenceSourceType] = mapped_column(Enum(EvidenceSourceType), nullable=False)
    
    # Content fields
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    content_data: Mapped[str] = mapped_column(Text, nullable=False)
    content_summary: Mapped[str] = mapped_column(Text, nullable=True)
    content_tags: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    
    # Metadata
    evidence_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)
    reliability_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    # Verification
    verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    verification_notes: Mapped[str] = mapped_column(Text, nullable=True)
    analyst_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="collected_evidence")


class AnalysisResult(Base):
    """Analysis results for evidence."""
    
    __tablename__ = "analysis_results"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    evidence_uuid: Mapped[str] = mapped_column(String, ForeignKey("collected_evidence.uuid"), nullable=True)
    
    analysis_type: Mapped[str] = mapped_column(String, nullable=False)
    results: Mapped[dict] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    analyst_id: Mapped[str] = mapped_column(String, nullable=True)
    tags: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="analysis_results")
    evidence = relationship("CollectedEvidence")


class ThreatAssessment(Base):
    """Threat assessments for investigations."""
    
    __tablename__ = "threat_assessments"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    threat_level: Mapped[ThreatLevel] = mapped_column(Enum(ThreatLevel), nullable=False)
    threat_type: Mapped[str] = mapped_column(String, nullable=False)
    targets: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    
    likelihood: Mapped[float] = mapped_column(Float, nullable=False)
    impact: Mapped[float] = mapped_column(Float, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="ACTIVE")
    
    analyst_notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="threat_assessments")


class PhaseTransition(Base):
    """Phase transitions for investigations."""
    
    __tablename__ = "phase_transitions"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    from_phase: Mapped[InvestigationPhase] = mapped_column(Enum(InvestigationPhase), nullable=False)
    to_phase: Mapped[InvestigationPhase] = mapped_column(Enum(InvestigationPhase), nullable=False)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    triggered_by: Mapped[str] = mapped_column(String, nullable=False)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="phase_transitions")


class InvestigationReport(Base):
    """Investigation reports."""
    
    __tablename__ = "investigation_reports"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    title: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    format: Mapped[str] = mapped_column(String, nullable=False, default="json")
    
    classification: Mapped[InvestigationClassification] = mapped_column(Enum(InvestigationClassification), nullable=False)
    authors: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    recipients: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    
    status: Mapped[str] = mapped_column(String, nullable=False, default="DRAFT")
    approved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    distributed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="reports")


class FinalAssessment(Base):
    """Final assessment for investigations."""
    
    __tablename__ = "final_assessments"
    
    uuid: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_uuid: Mapped[str] = mapped_column(String, ForeignKey("investigations.uuid"), nullable=False)
    
    executive_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_findings: Mapped[list] = mapped_column(ARRAY(String), nullable=True)
    confidence_level: Mapped[float] = mapped_column(Float, nullable=False)
    overall_threat_level: Mapped[ThreatLevel] = mapped_column(Enum(ThreatLevel), nullable=False)
    classification: Mapped[InvestigationClassification] = mapped_column(Enum(InvestigationClassification), nullable=False)
    
    # Relationships
    investigation = relationship("Investigation", back_populates="final_assessment")