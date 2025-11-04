import { create } from 'zustand';
import { useInvestigationStore } from './investigationStore';
import { useChatStore } from './chatStore';

interface WebSocketState {
  ws: WebSocket | null;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
  reconnectAttempts: number;
  
  // Actions
  connect: (investigationId: string) => void;
  disconnect: () => void;
  send: (data: any) => void;
}

export const useWebSocketStore = create<WebSocketState>((set, get) => ({
  ws: null,
  connectionStatus: 'disconnected',
  reconnectAttempts: 0,

  connect: (investigationId: string) => {
    const { ws, disconnect } = get();
    
    // Don't connect if investigationId is not provided or invalid
    if (!investigationId || investigationId.trim() === '' || investigationId === 'default') {
      console.log('⚠️ No valid investigation ID provided, skipping WebSocket connection');
      set({ connectionStatus: 'disconnected' });
      return;
    }
    
    // Disconnect existing connection
    if (ws) {
      disconnect();
    }

    console.log(`🔌 Connecting WebSocket for investigation: ${investigationId}`);
    set({ connectionStatus: 'connecting' });

    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    const websocket = new WebSocket(`${wsUrl}/ws/${investigationId}`);
    console.log(`🌐 WebSocket URL: ${wsUrl}/ws/${investigationId}`);

    websocket.onopen = () => {
      console.log('✅ OSINT WebSocket connected successfully!');
      set({ 
        ws: websocket, 
        connectionStatus: 'connected',
        reconnectAttempts: 0 
      });
    };

    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    websocket.onerror = (error) => {
      console.error('❌ OSINT WebSocket error:', error);
      console.error('WebSocket state:', websocket.readyState);
    };

    websocket.onclose = (event) => {
      console.log('❌ OSINT WebSocket disconnected:', event.code, event.reason);
      set({ connectionStatus: 'disconnected' });
      
      // Attempt to reconnect
      const { reconnectAttempts } = get();
      if (reconnectAttempts < 5) {
        setTimeout(() => {
          set((state) => ({ reconnectAttempts: state.reconnectAttempts + 1 }));
          get().connect(investigationId);
        }, Math.min(1000 * Math.pow(2, reconnectAttempts), 10000));
      }
    };
  },

  disconnect: () => {
    const { ws } = get();
    if (ws) {
      ws.close();
      set({ ws: null, connectionStatus: 'disconnected' });
    }
  },

  send: (data) => {
    const { ws, connectionStatus } = get();
    if (ws && connectionStatus === 'connected') {
      ws.send(JSON.stringify(data));
    }
  }
}));

// Handle incoming WebSocket messages
function handleWebSocketMessage(data: any) {
  const { type } = data;
  
  switch (type) {
    case 'investigation:updated':
      // Update investigation state
      if (data.investigation) {
        const investigationStore = useInvestigationStore.getState();
        const currentInvestigation = investigationStore.currentInvestigation;
        if (currentInvestigation && currentInvestigation.id === data.investigation.id) {
          investigationStore.updateInvestigation(data.investigation.id, data.investigation);
        }
      }
      break;
      
    case 'investigation:phase_changed':
      // Update investigation phase
      if (data.investigation_id && data.new_phase) {
        const investigationStore = useInvestigationStore.getState();
        const currentInvestigation = investigationStore.currentInvestigation;
        if (currentInvestigation && currentInvestigation.id === data.investigation_id) {
          investigationStore.updateInvestigation(data.investigation_id, {
            current_phase: data.new_phase,
            updated_at: new Date().toISOString()
          });
        }
      }
      break;
      
    case 'agent:status_changed':
      // Handle agent status changes
      console.log('Agent status changed:', data);
      break;
      
    case 'agent:task_assigned':
      // Handle agent task assignments
      console.log('Agent task assigned:', data);
      break;
      
    case 'agent:task_completed':
      // Handle agent task completions
      console.log('Agent task completed:', data);
      break;
      
    case 'evidence:collected':
      // Add collected evidence to investigation
      if (data.evidence) {
        const investigationStore = useInvestigationStore.getState();
        const currentInvestigation = investigationStore.currentInvestigation;
        if (currentInvestigation && currentInvestigation.id === data.evidence.investigation_id) {
          investigationStore.addEvidence(data.evidence.investigation_id, data.evidence);
        }
      }
      break;
      
    case 'evidence:verified':
      // Update evidence verification status
      if (data.evidence_id && data.verification_result) {
        // Implementation for updating evidence verification status
        console.log('Evidence verified:', data);
      }
      break;
      
    case 'threat:identified':
      // Add threat assessment
      if (data.threat) {
        const investigationStore = useInvestigationStore.getState();
        const currentInvestigation = investigationStore.currentInvestigation;
        if (currentInvestigation && currentInvestigation.id === data.threat.investigation_id) {
          investigationStore.addThreatAssessment(data.threat.investigation_id, data.threat);
        }
      }
      break;
      
    case 'report:generated':
      // Handle report generation
      if (data.report) {
        const investigationStore = useInvestigationStore.getState();
        const currentInvestigation = investigationStore.currentInvestigation;
        if (currentInvestigation && currentInvestigation.id === data.report.investigation_id) {
          investigationStore.generateReport(data.report.investigation_id, data.report);
        }
      }
      break;
      
    case 'error':
      // Handle error messages
      console.error('WebSocket error:', data.message);
      // Notify components about the error
      window.dispatchEvent(new CustomEvent('websocket-error', { detail: data }));
      break;
      
    case 'response':
       // Handle AI responses for investigation planning
       if (data.response) {
         const chatStore = useChatStore.getState();
         chatStore.addMessage({
           id: Date.now().toString(),
           role: data.role || 'assistant',
           content: data.response,
           timestamp: new Date().toISOString(),
           investigation_id: data.investigation_id,
           agent_id: data.agent_id,
           message_type: data.message_type || 'planning',
           metadata: {
             toolsUsed: data.toolsUsed || [],
             executionTime: data.executionTime || 0,
             classification: data.classification || 'UNCLASSIFIED',
             related_targets: data.related_targets,
             related_evidence: data.related_evidence,
             urgency: data.urgency
           }
         });
       }
      break;
      
    default:
      console.log('Unknown WebSocket message type:', type);
  }
}