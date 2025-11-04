import React, { useState, useEffect, useCallback } from 'react';
import { useWebSocketStore } from '../../store/websocketStore';
import { useInvestigationStore } from '../../store/investigationStore';
import { osintAgentApi, AgentAssignment } from '../../services/osintAgentApi';

interface AgentStatusCardProps {
  agent: AgentAssignment;
  onTaskAssign: (task: any) => void;
  onStatusChange: (status: string) => void;
}

const AgentStatusCard: React.FC<AgentStatusCardProps> = ({ agent, onTaskAssign, onStatusChange }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-success/20 border-success';
      case 'IDLE':
        return 'bg-secondary border-border';
      case 'ERROR':
        return 'bg-error/20 border-error';
      case 'COMPLETED':
        return 'bg-success/20 border-success';
      case 'BUSY':
        return 'bg-warning/20 border-warning';
      default:
        return 'bg-secondary border-border';
    }
  };

  const performance = agent.performance_metrics || {};
  
  return (
    <div className={`p-3 rounded-lg border ${getStatusColor(agent.status)}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-sm truncate">{agent.agent_id}</div>
        <div className={`w-3 h-3 rounded-full flex-shrink-0 ${
          agent.status === 'ACTIVE' ? 'bg-success animate-pulse' : 
          agent.status === 'ERROR' ? 'bg-error' : 
          agent.status === 'BUSY' ? 'bg-warning' : 'bg-muted'
        }`}></div>
      </div>
      <div className="text-xs text-muted mb-2 capitalize">{agent.agent_type}</div>
      <div className="text-xs mb-3">
        <div>Tasks: {performance.tasks_completed || 0}</div>
        <div>Success: {Math.round(performance.success_rate || 0)}%</div>
      </div>
      <div className="space-y-2">
        <button 
          className="w-full text-xs bg-primary/10 hover:bg-primary/20 text-primary px-2 py-1 rounded"
          onClick={() => onTaskAssign(agent)}
        >
          Assign Task
        </button>
        <select 
          className="w-full text-xs bg-secondary border border-border rounded px-2 py-1"
          value={agent.status}
          onChange={(e) => onStatusChange(e.target.value)}
        >
          <option value="IDLE">Idle</option>
          <option value="ACTIVE">Active</option>
          <option value="BUSY">Busy</option>
          <option value="ERROR">Error</option>
        </select>
      </div>
    </div>
  );
};

const CoordinationEventLog: React.FC<{ events: any[] }> = ({ events }) => {
  return (
    <div className="bg-background/50 rounded p-3 flex-shrink-0">
      <h4 className="font-medium mb-2 text-sm">Recent Events</h4>
      <div className="space-y-1 max-h-32 overflow-y-auto text-xs">
        {events.length > 0 ? (
          events.slice(0, 5).map((event, index) => (
            <div key={index} className="p-1 bg-secondary/50 rounded">
              <span className="text-muted">{event.timestamp}</span> - {event.message}
            </div>
          ))
        ) : (
          <div className="text-muted italic">No recent events</div>
        )}
      </div>
    </div>
  );
};



const AgentCoordinator: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();
  const { connectionStatus, connect, disconnect } = useWebSocketStore();
  
  // State for real data
  const [agents, setAgents] = useState<AgentAssignment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<any[]>([]);

  const addEvent = (message: string) => {
    setEvents(prev => [{ timestamp: new Date().toLocaleTimeString(), message }, ...prev].slice(0, 50));
  };

  const loadAgents = useCallback(async () => {
    if (!currentInvestigation?.id) return;
    
    try {
      setLoading(true);
      const data = await osintAgentApi.getInvestigationAgents(currentInvestigation.id);
      setAgents(data.agents || []);
      setError(null);
    } catch (err) {
      console.error('Failed to load agents:', err);
      setError('Failed to load agents');
      setAgents([]);
    } finally {
      setLoading(false);
    }
  }, [currentInvestigation?.id]);

  const loadDefaultInvestigation = async () => {
    try {
      const investigations = await osintAgentApi.getInvestigations();
      if (investigations.length > 0) {
        const data = await osintAgentApi.getInvestigationAgents(investigations[0].id);
        setAgents(data.agents || []);
      }
    } catch (err) {
      console.error('Failed to load default investigation:', err);
      setError('Failed to load investigation data');
      setAgents([]);
    } finally {
      setLoading(false);
    }
  };

  // Load agents for current investigation
  useEffect(() => {
    if (currentInvestigation?.id) {
      loadAgents();
      // Connect to WebSocket for real-time updates
      connect(currentInvestigation.id);
    } else {
      // Load default investigation if none selected
      loadDefaultInvestigation();
    }
    
    // Cleanup WebSocket on unmount
    return () => {
      disconnect();
    };
  }, [currentInvestigation?.id, connect, disconnect, loadAgents]);

  // Listen for WebSocket events
  useEffect(() => {
    const handleAgentEvent = (event: CustomEvent) => {
      const { detail } = event;
      addEvent(`${detail.type}: ${detail.agent_id || detail.investigation_id}`);
      
      // Reload agents if this was an agent-related event
      if (detail.type?.includes('agent') && currentInvestigation?.id) {
        loadAgents();
      }
    };

    window.addEventListener('websocket-error', handleAgentEvent as EventListener);
    
    return () => {
      window.removeEventListener('websocket-error', handleAgentEvent as EventListener);
    };
  }, [currentInvestigation?.id, loadAgents]);
  
  

  const handleTaskAssign = async (agent: AgentAssignment) => {
    try {
      const task = {
        type: 'collection',
        description: 'Collect evidence from assigned targets',
        priority: 'MEDIUM' as 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
      };
      
      await osintAgentApi.assignTask(agent.agent_id, task);
      addEvent(`Task assigned to ${agent.agent_id}`);
      // Reload agents to get updated status
      if (currentInvestigation?.id) {
        await loadAgents();
      }
    } catch (err) {
      console.error('Failed to assign task:', err);
      addEvent(`Failed to assign task to ${agent.agent_id}`);
    }
  };

  const handleStatusChange = async (agent: AgentAssignment, newStatus: string) => {
    try {
      await osintAgentApi.updateAgentStatus(agent.agent_id, { 
        status: newStatus as any,
        task_details: agent.current_task 
      });
      addEvent(`${agent.agent_id} status changed to ${newStatus}`);
      // Reload agents to get updated status
      if (currentInvestigation?.id) {
        await loadAgents();
      }
    } catch (err) {
      console.error('Failed to update agent status:', err);
      addEvent(`Failed to update ${agent.agent_id} status`);
    }
  };

  const handleAssignNewAgent = async () => {
    if (!currentInvestigation?.id) return;
    
    try {
      const newAgent = {
        agent_id: `agent-${Date.now()}`,
        agent_type: 'COLLECTION',
        status: 'IDLE'
      };
      
      await osintAgentApi.assignAgent(currentInvestigation.id, newAgent);
      addEvent(`New agent ${newAgent.agent_id} assigned to investigation`);
      // Reload agents to get updated list
      await loadAgents();
    } catch (err) {
      console.error('Failed to assign new agent:', err);
      addEvent('Failed to assign new agent');
    }
  };

  return (
    <div className="w-full h-full bg-secondary border-r border-border flex flex-col">
      <div className="p-4 flex-shrink-0 border-b border-border">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-semibold">Agent Coordination</h3>
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              connectionStatus === 'connected' ? 'bg-success animate-pulse' : 
              connectionStatus === 'connecting' ? 'bg-warning animate-pulse' : 'bg-error'
            }`}></div>
            <button
              onClick={handleAssignNewAgent}
              className="text-xs bg-primary/10 hover:bg-primary/20 text-primary px-3 py-1 rounded"
            >
              Assign Agent
            </button>
          </div>
        </div>
        {currentInvestigation && (
          <div className="text-xs text-muted mt-1">
            Investigation: {currentInvestigation.title || currentInvestigation.id} | 
            Connection: {connectionStatus}
          </div>
        )}
      </div>
      
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto p-4 space-y-6">
          {loading ? (
            <div className="text-sm text-muted p-4 text-center">Loading agents...</div>
          ) : error ? (
            <div className="text-sm text-error p-4 text-center">{error}</div>
          ) : (
            <>
              {/* Agent Status Grid */}
              <div>
                <h4 className="font-medium mb-3">
                  Active Agents ({agents.length})
                </h4>
                <div className="grid grid-cols-2 gap-3">
                  {agents.map(agent => (
                    <AgentStatusCard 
                      key={agent.agent_id}
                      agent={agent}
                      onTaskAssign={() => handleTaskAssign(agent)}
                      onStatusChange={(status) => handleStatusChange(agent, status)}
                    />
                  ))}
                  {agents.length === 0 && (
                    <div className="col-span-2 text-sm text-muted italic p-4 text-center">
                      No agents assigned to this investigation
                    </div>
                  )}
                </div>
              </div>
              
              {/* Current Tasks from agents */}
              <div>
                <h4 className="font-medium mb-3">Current Tasks</h4>
                <div className="space-y-2">
                  {agents
                    .filter(agent => agent.current_task)
                    .map(agent => (
                      <div key={agent.agent_id} className="p-3 bg-background rounded border border-border">
                        <div className="flex justify-between items-start mb-1">
                          <div className="font-medium text-sm">{agent.agent_id}</div>
                          <span className={`text-xs px-2 py-1 rounded ${
                            agent.status === 'ACTIVE' ? 'bg-primary/20 text-primary' :
                            agent.status === 'ERROR' ? 'bg-error/20 text-error' :
                            'bg-muted/20 text-muted'
                          }`}>
                            {agent.status}
                          </span>
                        </div>
                        {agent.current_task && (
                          <div className="text-xs text-muted">
                            <div className="mb-1">
                              <strong>Task:</strong> {agent.current_task.description || 'No description'}
                            </div>
                            <div className="mb-1">
                              <strong>Type:</strong> {agent.current_task.type || 'Unknown'}
                            </div>
                            <div>
                              <strong>Priority:</strong> {agent.current_task.priority || 'MEDIUM'}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  {agents.filter(agent => agent.current_task).length === 0 && (
                    <div className="text-sm text-muted italic p-4 text-center">No active tasks</div>
                  )}
                </div>
              </div>
            </>
          )}
          
          {/* Coordination Events */}
          <CoordinationEventLog events={events} />
        </div>
      </div>
    </div>
  );
};

export default AgentCoordinator;