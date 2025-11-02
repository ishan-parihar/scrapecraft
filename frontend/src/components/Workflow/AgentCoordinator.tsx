import React, { useState } from 'react';
import { useWebSocketStore } from '../../store/websocketStore';
import { useInvestigationStore } from '../../store/investigationStore';
import clsx from 'clsx';

interface AgentStatusCardProps {
  agent: any;
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
      default:
        return 'bg-secondary border-border';
    }
  };

  return (
    <div className={`p-3 rounded-lg border ${getStatusColor(agent.status)}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-sm">{agent.name || agent.id}</div>
        <div className={`w-3 h-3 rounded-full ${
          agent.status === 'ACTIVE' ? 'bg-success animate-pulse' : 
          agent.status === 'ERROR' ? 'bg-error' : 'bg-muted'
        }`}></div>
      </div>
      <div className="text-xs text-muted mb-2 capitalize">{agent.type || agent.agent_type}</div>
      <div className="text-xs mb-2">
        <div>Tasks: {agent.tasks_completed || 0}</div>
        <div>Success: {agent.success_rate || 0}%</div>
      </div>
      <button 
        className="w-full text-xs bg-primary/10 hover:bg-primary/20 text-primary px-2 py-1 rounded"
        onClick={() => onTaskAssign({ agent_id: agent.id, type: 'COLLECTION' })}
      >
        Assign Task
      </button>
    </div>
  );
};

interface TaskProgressCardProps {
  task: any;
  onCancel: () => void;
  onPriorityChange: (priority: string) => void;
}

const TaskProgressCard: React.FC<TaskProgressCardProps> = ({ task, onCancel, onPriorityChange }) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return 'border-red-500';
      case 'HIGH':
        return 'border-orange-500';
      case 'MEDIUM':
        return 'border-yellow-500';
      default:
        return 'border-border';
    }
  };

  return (
    <div className={`p-3 rounded border ${getPriorityColor(task.priority)}`}>
      <div className="flex justify-between items-start mb-1">
        <div className="font-medium text-sm truncate">{task.description}</div>
        <span className={`text-xs px-2 py-1 rounded ${
          task.status === 'COMPLETED' ? 'bg-success/20 text-success' :
          task.status === 'FAILED' ? 'bg-error/20 text-error' :
          'bg-warning/20 text-warning'
        }`}>
          {task.status}
        </span>
      </div>
      <div className="flex justify-between text-xs text-muted mb-2">
        <span>{task.agent_id}</span>
        <span>{task.progress || 0}%</span>
      </div>
      <div className="w-full bg-secondary rounded-full h-1.5 mb-2">
        <div 
          className="bg-primary h-1.5 rounded-full" 
          style={{ width: `${task.progress || 0}%` }}
        ></div>
      </div>
      <div className="flex space-x-2">
        <button 
          className="text-xs bg-error/20 hover:bg-error/30 text-error px-2 py-1 rounded"
          onClick={onCancel}
        >
          Cancel
        </button>
        <select 
          className="text-xs bg-secondary border border-border rounded px-2 py-1"
          value={task.priority}
          onChange={(e) => onPriorityChange(e.target.value)}
        >
          <option value="LOW">Low</option>
          <option value="MEDIUM">Medium</option>
          <option value="HIGH">High</option>
          <option value="CRITICAL">Critical</option>
        </select>
      </div>
    </div>
  );
};

const CoordinationEventLog: React.FC<{ events: any[] }> = ({ events }) => {
  return (
    <div className="bg-background/50 rounded p-3">
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

interface WorkflowPhase {
  id: string;
  label: string;
  description: string;
  icon: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED';
}

interface InvestigationPhase {
  id: string;
  name: string;
  description: string;
  icon: string;
  status: 'PENDING' | 'ACTIVE' | 'COMPLETED' | 'FAILED';
  progress: number;
  agents_involved: string[];
}

const AgentCoordinator: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();
  const { ws, send } = useWebSocketStore();
  
  // Mock data for demonstration
  const mockAgents = [
    {
      id: 'planning_agent_1',
      name: 'Planning Agent',
      type: 'PLANNING',
      status: 'ACTIVE',
      tasks_completed: 5,
      success_rate: 95
    },
    {
      id: 'collection_agent_1',
      name: 'Collection Agent',
      type: 'COLLECTION',
      status: 'IDLE',
      tasks_completed: 12,
      success_rate: 87
    },
    {
      id: 'analysis_agent_1',
      name: 'Analysis Agent',
      type: 'ANALYSIS',
      status: 'ACTIVE',
      tasks_completed: 8,
      success_rate: 92
    },
    {
      id: 'synthesis_agent_1',
      name: 'Synthesis Agent',
      type: 'SYNTHESIS',
      status: 'IDLE',
      tasks_completed: 3,
      success_rate: 100
    }
  ];
  
  const mockTasks = [
    {
      id: 'task_1',
      agent_id: 'collection_agent_1',
      description: 'Collect social media profiles',
      status: 'IN_PROGRESS',
      priority: 'HIGH',
      progress: 75
    },
    {
      id: 'task_2',
      agent_id: 'analysis_agent_1',
      description: 'Analyze collected evidence',
      status: 'PENDING',
      priority: 'MEDIUM',
      progress: 0
    }
  ];
  
  const mockEvents = [
    { timestamp: '10:30:15', message: 'Collection Agent started gathering data from Twitter' },
    { timestamp: '10:25:42', message: 'Analysis Agent completed threat assessment' },
    { timestamp: '10:20:18', message: 'Planning Agent defined new intelligence requirement' },
    { timestamp: '10:15:33', message: 'Synthesis Agent linked evidence items 12 and 15' },
    { timestamp: '10:10:50', message: 'Collection Agent verified source reliability' }
  ];
  
  const phases: InvestigationPhase[] = [
    { id: 'planning', name: 'Planning', description: 'Define investigation scope', icon: '📋', status: 'COMPLETED', progress: 100, agents_involved: ['planning_agent_1'] },
    { id: 'reconnaissance', name: 'Reconnaissance', description: 'Initial information gathering', icon: '🔍', status: 'ACTIVE', progress: 65, agents_involved: ['collection_agent_1'] },
    { id: 'collection', name: 'Collection', description: 'Systematic evidence collection', icon: '📥', status: 'PENDING', progress: 0, agents_involved: [] },
    { id: 'analysis', name: 'Analysis', description: 'Analyze collected evidence', icon: '🔬', status: 'PENDING', progress: 0, agents_involved: [] },
    { id: 'synthesis', name: 'Synthesis', description: 'Synthesize findings', icon: '🧩', status: 'PENDING', progress: 0, agents_involved: [] },
    { id: 'reporting', name: 'Reporting', description: 'Generate reports', icon: '📄', status: 'PENDING', progress: 0, agents_involved: [] }
  ];

  const handleTaskAssign = (task: any) => {
    console.log('Assigning task:', task);
    // In a real implementation, this would send the task assignment to the backend
  };

  const handleStatusChange = (status: string) => {
    console.log('Changing agent status to:', status);
  };

  const handleTaskCancel = (taskId: string) => {
    console.log('Cancelling task:', taskId);
  };

  const handlePriorityChange = (taskId: string, priority: string) => {
    console.log('Changing task priority:', taskId, priority);
  };

  return (
    <div className="w-80 bg-secondary p-4 border-r border-border flex flex-col h-full">
      <h3 className="text-lg font-semibold mb-4">Agent Coordination</h3>
      
      {/* Investigation Phases */}
      <div className="mb-6">
        <h4 className="font-medium mb-3">Investigation Phases</h4>
        <div className="space-y-2">
          {phases.map((phase, index) => (
            <div key={phase.id} className="p-2 bg-background rounded border border-border">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center">
                  <span className="mr-2">{phase.icon}</span>
                  <span className="text-sm font-medium">{phase.name}</span>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded ${
                  phase.status === 'COMPLETED' ? 'bg-success/20 text-success' :
                  phase.status === 'ACTIVE' ? 'bg-primary/20 text-primary' :
                  phase.status === 'FAILED' ? 'bg-error/20 text-error' : 'bg-muted/20 text-muted'
                }`}>
                  {phase.status}
                </span>
              </div>
              {phase.status !== 'PENDING' && (
                <div className="w-full bg-secondary rounded-full h-1.5 mb-1">
                  <div 
                    className="bg-primary h-1.5 rounded-full" 
                    style={{ width: `${phase.progress}%` }}
                  ></div>
                </div>
              )}
              <div className="text-xs text-muted">
                {phase.agents_involved.length} agents assigned
              </div>
            </div>
          ))}
        </div>
      </div>
      
      {/* Agent Status Grid */}
      <div className="mb-6">
        <h4 className="font-medium mb-3">Active Agents</h4>
        <div className="grid grid-cols-2 gap-3">
          {mockAgents.map(agent => (
            <AgentStatusCard 
              key={agent.id}
              agent={agent}
              onTaskAssign={handleTaskAssign}
              onStatusChange={handleStatusChange}
            />
          ))}
        </div>
      </div>
      
      {/* Active Tasks */}
      <div className="mb-6 flex-1 min-h-0">
        <h4 className="font-medium mb-3">Active Tasks</h4>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {mockTasks.map(task => (
            <TaskProgressCard 
              key={task.id}
              task={task}
              onCancel={() => handleTaskCancel(task.id)}
              onPriorityChange={(priority) => handlePriorityChange(task.id, priority)}
            />
          ))}
          {mockTasks.length === 0 && (
            <div className="text-sm text-muted italic p-4 text-center">No active tasks</div>
          )}
        </div>
      </div>
      
      {/* Coordination Events */}
      <CoordinationEventLog events={mockEvents} />
    </div>
  );
};

export default AgentCoordinator;