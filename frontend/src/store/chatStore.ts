import { create } from 'zustand';
import { ChatMessage } from '../types';
import { api } from '../services/api';
import { useInvestigationStore } from './investigationStore';

// Helper to generate UUID (you might want to install uuid package)
function uuidv4() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  addMessage: (message: ChatMessage) => void;
  sendMessage: (content: string, pipelineId: string) => Promise<void>;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
  messages: [],
  isLoading: false,
  error: null,

  addMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message]
    }));
  },

  sendMessage: async (content, pipelineId) => {
    const { addMessage, setLoading, setError } = get();
    
    // Add user message
    const userMessage: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content,
      timestamp: new Date().toISOString()
    };
    
    addMessage(userMessage);
    setLoading(true);
    setError(null);

    try {
       // Get current investigation context (using a placeholder for now)
       const investigationStore = useInvestigationStore.getState();
       const currentInvestigation = investigationStore.currentInvestigation;
      
       const response = await api.post('/chat/message', {
         message: content,
         investigation_id: pipelineId, // Using pipelineId as investigationId for now
         context: {
           targets: currentInvestigation?.targets || [],
           intelligence_requirements: currentInvestigation?.intelligence_requirements || [],
           collected_evidence: currentInvestigation?.collected_evidence || []
         }
       });

       const assistantMessage: ChatMessage = {
         id: uuidv4(),
         role: 'assistant',
         content: response.data.response,
         timestamp: new Date().toISOString(),
         metadata: {
           toolsUsed: response.data.tools_used,
           classification: 'UNCLASSIFIED'
         }
       };

      addMessage(assistantMessage);

       // Update investigation state if needed
       if (response.data.targets || response.data.intelligence_requirements || response.data.evidence) {
         investigationStore.updateInvestigation(pipelineId, {
           targets: response.data.targets || currentInvestigation?.targets || [],
           intelligence_requirements: response.data.intelligence_requirements || currentInvestigation?.intelligence_requirements || [],
           collected_evidence: response.data.evidence || currentInvestigation?.collected_evidence || []
         });
       }

    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to send message');
      
       const errorMessage: ChatMessage = {
         id: uuidv4(),
         role: 'assistant',
         content: 'Sorry, I encountered an error processing your request. Please try again.',
         timestamp: new Date().toISOString(),
         metadata: {
           classification: 'UNCLASSIFIED'
         }
       };
      
      addMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  },

  clearMessages: () => {
    set({ messages: [], error: null });
  },

  setLoading: (loading) => {
    set({ isLoading: loading });
  },

  setError: (error) => {
    set({ error });
  }
}));