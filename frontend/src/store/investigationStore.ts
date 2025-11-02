import { create } from 'zustand';
import { Investigation, InvestigationTarget, IntelligenceRequirement, CollectedEvidence, ThreatAssessment, InvestigationReport } from '../types/osint';
import { api } from '../services/api';

interface InvestigationState {
  investigations: Investigation[];
  currentInvestigation: Investigation | null;
  isLoading: boolean;
  
  // Actions
  fetchInvestigations: () => Promise<void>;
  createInvestigation: (data: Partial<Investigation>) => Promise<void>;
  updateInvestigation: (id: string, data: Partial<Investigation>) => Promise<void>;
  deleteInvestigation: (id: string) => Promise<void>;
  setCurrentInvestigation: (investigation: Investigation | null) => void;
  
  // Target management
  addTarget: (investigationId: string, target: InvestigationTarget) => Promise<void>;
  updateTarget: (investigationId: string, targetId: string, data: Partial<InvestigationTarget>) => Promise<void>;
  removeTarget: (investigationId: string, targetId: string) => Promise<void>;
  
  // Evidence management
  addEvidence: (investigationId: string, evidence: CollectedEvidence) => Promise<void>;
  updateEvidence: (investigationId: string, evidenceId: string, data: Partial<CollectedEvidence>) => Promise<void>;
  
  // Threat assessment
  addThreatAssessment: (investigationId: string, threat: ThreatAssessment) => Promise<void>;
  updateThreatAssessment: (investigationId: string, threatId: string, data: Partial<ThreatAssessment>) => Promise<void>;
  
  // Report management
  generateReport: (investigationId: string, report: Partial<InvestigationReport>) => Promise<void>;
}

export const useInvestigationStore = create<InvestigationState>((set, get) => ({
  investigations: [],
  currentInvestigation: null,
  isLoading: false,

  fetchInvestigations: async () => {
    try {
      set({ isLoading: true });
      const response = await api.get('/osint/investigations');
      set({ investigations: response.data, isLoading: false });
      
      // Set current investigation if none selected
      const { currentInvestigation, investigations } = get();
      if (!currentInvestigation && investigations.length > 0) {
        set({ currentInvestigation: investigations[0] });
      }
    } catch (error) {
      console.error('Failed to fetch investigations:', error);
      set({ isLoading: false });
    }
  },

   createInvestigation: async (data) => {
     set({ isLoading: true });
     try {
         const response = await api.post('/osint/investigations', {
          title: data.title || 'New Investigation',
          description: data.description || 'Investigation description',
          classification: data.classification || 'UNCLASSIFIED',
          priority: data.priority || 'MEDIUM',
          status: 'PLANNING',
          targets: data.targets || [],
          intelligence_requirements: data.intelligence_requirements || [],
          assigned_agents: [],
          active_phases: [],
          collected_evidence: [],
          analysis_results: [],
          threat_assessments: [],
          current_phase: 'PLANNING',
          phase_history: [],
          code: data.code || '', // Include code property
          sources: data.sources || [], // Include sources property
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          generated_reports: []
        });
       
       const newInvestigation: Investigation = response.data;
      
      set((state) => ({
        investigations: [...state.investigations, newInvestigation],
        currentInvestigation: newInvestigation,
        isLoading: false
      }));
    } catch (error) {
      console.error('Failed to create investigation:', error);
      set({ isLoading: false });
    }
  },

  updateInvestigation: async (id, data) => {
    try {
       const response = await api.put(`/osint/investigations/${id}`, data);
      const updatedInvestigation = response.data;
      
      set((state) => ({
        investigations: state.investigations.map(inv => 
          inv.id === id ? updatedInvestigation : inv
        ),
        currentInvestigation: state.currentInvestigation?.id === id 
          ? updatedInvestigation 
          : state.currentInvestigation
      }));
    } catch (error) {
      console.error('Failed to update investigation:', error);
    }
  },

  deleteInvestigation: async (id) => {
    try {
       await api.delete(`/osint/investigations/${id}`);
      
      set((state) => {
        const investigations = state.investigations.filter(inv => inv.id !== id);
        const currentInvestigation = state.currentInvestigation?.id === id 
          ? investigations[0] || null 
          : state.currentInvestigation;
        
        return { investigations, currentInvestigation };
      });
    } catch (error) {
      console.error('Failed to delete investigation:', error);
    }
  },

  setCurrentInvestigation: (investigation) => {
    set({ currentInvestigation: investigation });
  },

   addTarget: async (investigationId, target) => {
      try {
        // Add target via dedicated endpoint
        const response = await api.post(`/osint/investigations/${investigationId}/targets`, {
          type: target.type,
          identifier: target.identifier,
          aliases: target.aliases,
          priority: target.priority,
          collection_requirements: target.collection_requirements
          // Note: status and metadata are not part of the TargetCreate model in backend
        });
        
        const newTarget = response.data;
        
        // Update the store
        set((state) => {
          const updatedInvestigations = state.investigations.map(inv => 
            inv.id === investigationId 
              ? { 
                  ...inv, 
                  targets: [...inv.targets, newTarget],
                  updated_at: new Date().toISOString()
                } 
              : inv
          );
          
          const updatedCurrentInvestigation = state.currentInvestigation?.id === investigationId 
            ? { 
                ...state.currentInvestigation,
                targets: [...state.currentInvestigation.targets, newTarget],
                updated_at: new Date().toISOString()
              }
            : state.currentInvestigation;
          
          return {
            investigations: updatedInvestigations,
            currentInvestigation: updatedCurrentInvestigation
          };
        });
     } catch (error) {
       console.error('Failed to add target:', error);
     }
   },

   updateTarget: async (investigationId, targetId, data) => {
      try {
        // Note: The backend might not have a specific endpoint for updating targets
        // For now, we'll update the entire investigation as before
        const { investigations, currentInvestigation } = get();
        const investigation = investigations.find(inv => inv.id === investigationId);
        
        if (!investigation) return;
        
        const updatedTargets = investigation.targets.map(target => 
          target.id === targetId ? { ...target, ...data } : target
        );
        
        const updatedInvestigation = {
          ...investigation,
          targets: updatedTargets,
          updated_at: new Date().toISOString()
        };
        
        // Update the investigation in the backend
        await api.put(`/osint/investigations/${investigationId}`, updatedInvestigation);
        
        // Update the store
       set((state) => ({
         investigations: state.investigations.map(inv => 
           inv.id === investigationId ? updatedInvestigation : inv
         ),
         currentInvestigation: state.currentInvestigation?.id === investigationId 
           ? updatedInvestigation 
           : state.currentInvestigation
       }));
     } catch (error) {
       console.error('Failed to update target:', error);
     }
   },

   removeTarget: async (investigationId, targetId) => {
      try {
        // Note: The backend might not have a specific endpoint for removing targets
        // For now, we'll update the entire investigation as before
        const { investigations, currentInvestigation } = get();
        const investigation = investigations.find(inv => inv.id === investigationId);
        
        if (!investigation) return;
        
        const updatedTargets = investigation.targets.filter(target => target.id !== targetId);
        
        const updatedInvestigation = {
          ...investigation,
          targets: updatedTargets,
          updated_at: new Date().toISOString()
        };
        
        // Update the investigation in the backend
        await api.put(`/osint/investigations/${investigationId}`, updatedInvestigation);
        
        // Update the store
       set((state) => ({
         investigations: state.investigations.map(inv => 
           inv.id === investigationId ? updatedInvestigation : inv
         ),
         currentInvestigation: state.currentInvestigation?.id === investigationId 
           ? updatedInvestigation 
           : state.currentInvestigation
       }));
     } catch (error) {
       console.error('Failed to remove target:', error);
     }
   },

   addEvidence: async (investigationId, evidence) => {
      try {
        // Add evidence via dedicated endpoint
        const response = await api.post(`/osint/investigations/${investigationId}/evidence`, {
          source: evidence.source,
          source_type: evidence.source_type,
          content: evidence.content,
          metadata: evidence.metadata,
          reliability_score: evidence.reliability_score,
          relevance_score: evidence.relevance_score
          // Note: classification, tags, source_confidence, data_type are not part of EvidenceCreate model in backend
        });
        
        const newEvidence = response.data;
        
        // Update the store
        set((state) => {
          const updatedInvestigations = state.investigations.map(inv => 
            inv.id === investigationId 
              ? { 
                  ...inv, 
                  collected_evidence: [...inv.collected_evidence, newEvidence],
                  updated_at: new Date().toISOString()
                } 
              : inv
          );
          
          const updatedCurrentInvestigation = state.currentInvestigation?.id === investigationId 
            ? { 
                ...state.currentInvestigation,
                collected_evidence: [...state.currentInvestigation.collected_evidence, newEvidence],
                updated_at: new Date().toISOString()
              }
            : state.currentInvestigation;
          
          return {
            investigations: updatedInvestigations,
            currentInvestigation: updatedCurrentInvestigation
          };
        });
     } catch (error) {
       console.error('Failed to add evidence:', error);
     }
   },

   updateEvidence: async (investigationId, evidenceId, data) => {
      try {
        // Note: The backend might not have a specific endpoint for updating evidence
        // For now, we'll update the entire investigation as before
        const { investigations, currentInvestigation } = get();
        const investigation = investigations.find(inv => inv.id === investigationId);
        
        if (!investigation) return;
        
        const updatedEvidence = investigation.collected_evidence.map(evidence => 
          evidence.id === evidenceId ? { ...evidence, ...data } : evidence
        );
        
        const updatedInvestigation = {
          ...investigation,
          collected_evidence: updatedEvidence,
          updated_at: new Date().toISOString()
        };
        
        // Update the investigation in the backend
        await api.put(`/osint/investigations/${investigationId}`, updatedInvestigation);
        
        // Update the store
       set((state) => ({
         investigations: state.investigations.map(inv => 
           inv.id === investigationId ? updatedInvestigation : inv
         ),
         currentInvestigation: state.currentInvestigation?.id === investigationId 
           ? updatedInvestigation 
           : state.currentInvestigation
       }));
     } catch (error) {
       console.error('Failed to update evidence:', error);
     }
   },

   addThreatAssessment: async (investigationId, threat) => {
      try {
        // Add threat via dedicated endpoint
        const response = await api.post(`/osint/investigations/${investigationId}/threats`, {
          title: threat.title,
          description: threat.description,
          threat_level: threat.threat_level,
          threat_type: threat.threat_type,
          targets: threat.targets,
          likelihood: threat.likelihood,
          impact: threat.impact
          // Note: mitigation_strategies, status, classification, severity are not part of ThreatAssessmentCreate model in backend
        });
        
        const newThreat = response.data;
        
        // Update the store
        set((state) => {
          const updatedInvestigations = state.investigations.map(inv => 
            inv.id === investigationId 
              ? { 
                  ...inv, 
                  threat_assessments: [...inv.threat_assessments, newThreat],
                  updated_at: new Date().toISOString()
                } 
              : inv
          );
          
          const updatedCurrentInvestigation = state.currentInvestigation?.id === investigationId 
            ? { 
                ...state.currentInvestigation,
                threat_assessments: [...state.currentInvestigation.threat_assessments, newThreat],
                updated_at: new Date().toISOString()
              }
            : state.currentInvestigation;
          
          return {
            investigations: updatedInvestigations,
            currentInvestigation: updatedCurrentInvestigation
          };
        });
     } catch (error) {
       console.error('Failed to add threat assessment:', error);
     }
   },

   updateThreatAssessment: async (investigationId, threatId, data) => {
      try {
        // Note: The backend might not have a specific endpoint for updating threats
        // For now, we'll update the entire investigation as before
        const { investigations, currentInvestigation } = get();
        const investigation = investigations.find(inv => inv.id === investigationId);
        
        if (!investigation) return;
        
        const updatedThreats = investigation.threat_assessments.map(threat => 
          threat.id === threatId ? { ...threat, ...data } : threat
        );
        
        const updatedInvestigation = {
          ...investigation,
          threat_assessments: updatedThreats,
          updated_at: new Date().toISOString()
        };
        
        // Update the investigation in the backend
        await api.put(`/osint/investigations/${investigationId}`, updatedInvestigation);
        
        // Update the store
       set((state) => ({
         investigations: state.investigations.map(inv => 
           inv.id === investigationId ? updatedInvestigation : inv
         ),
         currentInvestigation: state.currentInvestigation?.id === investigationId 
           ? updatedInvestigation 
           : state.currentInvestigation
       }));
     } catch (error) {
       console.error('Failed to update threat assessment:', error);
     }
   },

   generateReport: async (investigationId, report) => {
     try {
       const { investigations, currentInvestigation } = get();
       const investigation = investigations.find(inv => inv.id === investigationId);
       
       if (!investigation) return;
       
       const fullReport: InvestigationReport = {
         id: `report_${Date.now()}`,
         investigation_id: investigationId,
         title: report.title || 'Investigation Report',
         report_type: report.report_type || 'PRELIMINARY',
         classification: report.classification || investigation.classification,
         author: report.author || 'System',
         created_at: new Date().toISOString(),
         content: {
           executive_summary: report.content?.executive_summary || 'Auto-generated report',
           findings: report.content?.findings || [],
           methodology: report.content?.methodology || 'Automated OSINT collection and analysis',
           limitations: report.content?.limitations || [],
           recommendations: report.content?.recommendations || [],
           evidence_summary: report.content?.evidence_summary || '',
           threat_assessment_summary: report.content?.threat_assessment_summary || '',
           timeline: report.content?.timeline || '',
           appendices: report.content?.appendices || [],
         },
         recipients: report.recipients || [],
         status: report.status || 'DRAFT',
         approval_chain: report.approval_chain || [],
         distribution_list: report.distribution_list || [],
         metadata: report.metadata || {},
         ...report
       };
       
       const updatedInvestigation = {
         ...investigation,
         generated_reports: [...investigation.generated_reports, fullReport],
         updated_at: new Date().toISOString()
       };
       
       // Update the investigation in the backend
       await api.put(`/osint/investigations/${investigationId}`, updatedInvestigation);
       
       // Update the store
       set((state) => ({
         investigations: state.investigations.map(inv => 
           inv.id === investigationId ? updatedInvestigation : inv
         ),
         currentInvestigation: state.currentInvestigation?.id === investigationId 
           ? updatedInvestigation 
           : state.currentInvestigation
       }));
     } catch (error) {
       console.error('Failed to generate report:', error);
     }
   }
}));