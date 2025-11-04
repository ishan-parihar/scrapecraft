// OSINT-Specific Type Definitions for Investigation Management

// Investigation Core Models
export interface Investigation {
  id: string;
  title: string;
  description: string;
  classification: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET' | 'TOP_SECRET';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'PLANNING' | 'ACTIVE' | 'PAUSED' | 'COMPLETED' | 'ARCHIVED';
  
  // Targets and Intelligence Requirements
  targets: InvestigationTarget[];
  intelligence_requirements: IntelligenceRequirement[];
  
  // Agent Coordination
  assigned_agents: AgentAssignment[];
  active_phases: InvestigationPhase[];
  
  // Evidence and Analysis
  collected_evidence: CollectedEvidence[];
  analysis_results: AnalysisResult[];
  threat_assessments: ThreatAssessment[];
  
  // Workflow and Timeline
  current_phase: string;
  phase_history: PhaseTransition[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
  
  // OSINT Collection Code (for automated collection)
  code?: string; // Generated OSINT collection code
  
  // Sources for OSINT collection
  sources?: string[]; // URLs or sources for intelligence collection
  
  // Reporting
  generated_reports: InvestigationReport[];
  final_assessment?: FinalAssessment;
}

export interface InvestigationTarget {
  id: string;
  type: 'PERSON' | 'ORGANIZATION' | 'LOCATION' | 'DOMAIN' | 'SOCIAL_MEDIA' | 'OTHER';
  identifier: string;
  aliases: string[];
  priority: 'LOW' | 'MEDIUM' | 'HIGH';
  collection_requirements: string[];
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED';
  metadata?: Record<string, any>;
}

export interface IntelligenceRequirement {
  id: string;
  requirement: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  category: 'FINANCIAL' | 'LEGAL' | 'TECHNICAL' | 'PERSONNEL' | 'OPERATIONAL' | 'OTHER';
  source_type: 'PUBLIC' | 'HUMINT' | 'SOURCES' | 'TECHNICAL' | 'COMBINED';
  deadline?: string;
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  evidence_collected: string[];
}

// Agent Management Models
export interface AgentAssignment {
  agent_id: string;
  agent_type: 'PLANNING' | 'COLLECTION' | 'ANALYSIS' | 'SYNTHESIS' | 'REPORTING';
  assigned_targets: string[];
  current_task: AgentTask;
  status: 'IDLE' | 'ACTIVE' | 'WAITING' | 'COMPLETED' | 'ERROR';
  performance_metrics: AgentMetrics;
  last_updated: string;
}

export interface AgentTask {
  id: string;
  type: 'COLLECTION' | 'ANALYSIS' | 'VERIFICATION' | 'REPORTING';
  target_id: string;
  description: string;
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  estimated_duration: number; // in minutes
  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED';
  started_at?: string;
  completed_at?: string;
  results?: any;
  metadata?: Record<string, any>;
}

export interface AgentMetrics {
  tasks_completed: number;
  success_rate: number;
  average_response_time: number; // in seconds
  reliability_score: number; // 0-100
  last_active: string;
  resource_usage: {
    cpu: number;
    memory: number;
    network: number;
  };
}

// Evidence Management Models
export interface CollectedEvidence {
  id: string;
  investigation_id: string;
  source: string;
  source_type: 'SOCIAL_MEDIA' | 'PUBLIC_RECORDS' | 'WEB_CONTENT' | 'DARK_WEB' | 'HUMINT' | 'LEAKED_DATA' | 'API' | 'OTHER';
  content: EvidenceContent;
  metadata: EvidenceMetadata;
  reliability_score: number; // 0-100
  relevance_score: number; // 0-100
  collected_at: string;
  verified: boolean;
  verified_by?: string;
  verification_time?: string;
  classification: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET';
  tags: string[];
  related_evidence: string[];
  source_confidence: number; // 0-100
  data_type: 'TEXT' | 'IMAGE' | 'VIDEO' | 'AUDIO' | 'DOCUMENT' | 'STRUCTURED_DATA';
}

export interface EvidenceContent {
  type: string;
  data: string | Record<string, any> | FileReference;
  value?: string | Record<string, any>; // Added for backward compatibility with components
  summary?: string;
  extracted_text?: string;
  language?: string;
  tags?: string[];
}

export interface EvidenceMetadata {
  url?: string;
  timestamp: string;
  source_agent: string;
  collection_method: string;
  file_path?: string;
  size?: number;
  mime_type?: string;
  extraction_method?: string;
  original_format?: string;
}

export interface FileReference {
  name: string;
  size: number;
  type: string;
  download_url: string;
  file_hash: string;
}

// Analysis and Threat Models
export interface AnalysisResult {
  id: string;
  investigation_id: string;
  evidence_id: string;
  analysis_type: 'PATTERN' | 'CORRELATION' | 'CONTENT' | 'SOURCE_VERIFICATION' | 'THREAT_ASSESSMENT';
  result: any;
  confidence: number; // 0-100
  analyst: string;
  timestamp: string;
  tags: string[];
  related_analysis: string[];
  metadata?: Record<string, any>;
}

export interface ThreatAssessment {
  id: string;
  investigation_id: string;
  title: string;
  description: string;
  threat_type: string; // cyber, physical, reputational, etc.
  threat_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  targets: string[]; // target IDs
  likelihood: number; // 0.0 to 1.0
  impact: number; // 0.0 to 1.0
  risk_score: number; // 0.0 to 1.0 (calculated)
  status: string; // ACTIVE, MONITORED, RESOLVED, etc.
  created_at: string;
  updated_at: string;
  analyst_notes?: string;
  // Additional properties that ThreatAssessment.tsx component is trying to access
  indicators?: string[];
  mitigation_recommendations?: string[];
  sources?: string[];
  probability?: number;
  timeline?: string;
  analyst?: string;
  recommendations?: string[];
  target_id?: string;
}

// Investigation Workflow Models
export interface InvestigationPhase {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED';
  start_time?: string;
  end_time?: string;
  agents_involved: string[];
  deliverables: string[];
  dependencies: string[];
  progress: number; // 0-100
  metadata?: Record<string, any>;
}

export interface PhaseTransition {
  from: string;
  to: string;
  timestamp: string;
  reason: string;
  approved_by?: string;
  metadata?: Record<string, any>;
}

// Reporting Models
export interface InvestigationReport {
  id: string;
  investigation_id: string;
  title: string;
  report_type: 'PRELIMINARY' | 'INTERIM' | 'FINAL' | 'EXECUTIVE' | 'TECHNICAL';
  classification: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET' | 'TOP_SECRET';
  author: string;
  created_at: string;
  content: ReportContent;
  recipients: ReportRecipient[];
  status: 'DRAFT' | 'REVIEW' | 'APPROVED' | 'DISTRIBUTED' | 'ARCHIVED';
  approval_chain: ApprovalStep[];
  distribution_list: string[];
  metadata?: Record<string, any>;
}

export interface ReportContent {
  executive_summary: string;
  findings: ReportFinding[];
  methodology: string;
  limitations: string[];
  recommendations: string[];
  evidence_summary: string;
  threat_assessment_summary: string;
  timeline: string;
  appendices: ReportAppendix[];
}

export interface ReportFinding {
  id: string;
  title: string;
  description: string;
  evidence_ids: string[];
  classification: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET';
  confidence: number; // 0-100
  impact_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  status: 'CONFIRMED' | 'PROBABLE' | 'POSSIBLE' | 'UNCONFIRMED';
}

export interface ReportAppendix {
  id: string;
  title: string;
  content: string;
  file_attachments?: FileReference[];
}

export interface ReportRecipient {
  id: string;
  name: string;
  email: string;
  classification_level: string;
  role: string;
  distribution_method: 'EMAIL' | 'SECURE_PORTAL' | 'PAPER' | 'OTHER';
}

export interface ApprovalStep {
  approver: string;
  required: boolean;
  approved: boolean;
  approved_at?: string;
  comments?: string;
}

// Final Assessment Models
export interface FinalAssessment {
  overall_threat_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence_level: 'LOW' | 'MEDIUM' | 'HIGH';
  key_findings: string[];
  critical_gaps: string[];
  recommendations: string[];
  classification: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET';
  executive_summary: string;
  assessment_date: string;
  assessed_by: string;
  next_review_date?: string;
}

// OSINT Chat and Planning Models
export interface OSINTChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'agent';
  content: string;
  timestamp: string;
  investigation_id?: string;
  agent_id?: string;
  message_type: 'planning' | 'status' | 'evidence' | 'analysis' | 'alert' | 'task';
  metadata?: {
    related_targets?: string[];
    related_evidence?: string[];
    urgency?: 'low' | 'medium' | 'high' | 'critical';
    classification?: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET';
    toolsUsed?: string[];
    executionTime?: number;
  };
}

// OSINT-Specific Pipeline Model (Backwards Compatible)
export interface OSINTPipeline {
  id: string;
  name: string;
  description?: string;
  investigation_id: string; // Links to investigation
  pipeline_type: 'RECONNAISSANCE' | 'COLLECTION' | 'ANALYSIS' | 'VERIFICATION' | 'REPORTING';
  target_ids: string[];
  configuration: {
    urls: string[];
    schema: Record<string, any>;
    agents: string[];
    collection_requirements: string[];
    analysis_requirements: string[];
  };
  status: 'PENDING' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'STOPPED';
  created_at: string;
  updated_at: string;
  last_run?: string;
  results_summary?: {
    total_collected: number;
    verified_count: number;
    reliability_average: number;
  };
}