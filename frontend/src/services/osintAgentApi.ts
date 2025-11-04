import { api } from './api';

export interface AgentAssignment {
  agent_id: string;
  agent_type: 'PLANNING' | 'COLLECTION' | 'ANALYSIS' | 'SYNTHESIS' | 'REPORTING';
  assigned_targets: string[];
  current_task: any;
  status: 'IDLE' | 'ACTIVE' | 'BUSY' | 'ERROR' | 'COMPLETED';
  performance_metrics: {
    tasks_completed: number;
    success_rate: number;
    average_task_time: number;
    error_count: number;
  };
  assigned_at: string;
  updated_at: string;
}

export interface AgentPerformance {
  agent_id: string;
  investigation_id: string;
  agent_type: string;
  current_status: string;
  assigned_at: string;
  last_updated: string;
  current_task: any;
  performance_metrics: {
    tasks_completed: number;
    success_rate: number;
    average_task_time: number;
    error_count: number;
  };
}

export interface TaskAssignment {
  type: string;
  description: string;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  details?: any;
}

export interface StatusUpdate {
  status: 'IDLE' | 'ACTIVE' | 'BUSY' | 'ERROR' | 'COMPLETED';
  task_details?: any;
}

// OSINT Agent Coordination API
export const osintAgentApi = {
  // Get all agents for an investigation
  getInvestigationAgents: async (investigationId: string) => {
    const response = await api.get(`/osint/investigations/${investigationId}/agents`);
    return response.data;
  },

  // Assign agent to investigation
  assignAgent: async (investigationId: string, assignment: {
    agent_id: string;
    agent_type?: string;
    status?: string;
    assigned_targets?: string[];
    current_task?: any;
    performance_metrics?: any;
  }) => {
    const response = await api.post(`/osint/investigations/${investigationId}/agents/assign`, assignment);
    return response.data;
  },

  // Update agent status
  updateAgentStatus: async (agentId: string, statusUpdate: StatusUpdate) => {
    const response = await api.put(`/osint/agents/${agentId}/status`, statusUpdate);
    return response.data;
  },

  // Assign task to agent
  assignTask: async (agentId: string, task: TaskAssignment) => {
    const response = await api.post(`/osint/agents/${agentId}/tasks`, task);
    return response.data;
  },

  // Get agent performance metrics
  getAgentPerformance: async (agentId: string): Promise<AgentPerformance> => {
    const response = await api.get(`/osint/agents/${agentId}/performance`);
    return response.data;
  },

  // Get investigations
  getInvestigations: async () => {
    const response = await api.get('/osint/investigations');
    return response.data;
  },

  // Create investigation
  createInvestigation: async (investigation: {
    title: string;
    description: string;
    classification: string;
    priority: string;
  }) => {
    const response = await api.post('/osint/investigations', investigation);
    return response.data;
  }
};