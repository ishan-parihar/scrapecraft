import React, { useEffect, useState } from 'react';
import { useWebSocketStore } from '../../store/websocketStore';
 import { useInvestigationStore } from '../../store/investigationStore';
import clsx from 'clsx';

interface WorkflowPhase {
  id: string;
  label: string;
  description: string;
  icon: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

interface WorkflowState {
    investigation_id: string;
   phase: string;
    sources: any[];
    intelligence_fields: any[];
   generated_code: string;
   pending_approvals: any[];
   phase_transitions: any[];
   updated_at: string;
 }
 
 // Add state to track phase transition in progress
 const [transitioningPhase, setTransitioningPhase] = useState<string | null>(null);

const WorkflowSidebar: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();
  const { ws, send } = useWebSocketStore();
  const [workflowState, setWorkflowState] = useState<WorkflowState | null>(null);
  // Add state to track phase transition in progress
  const [transitioningPhase, setTransitioningPhase] = useState<string | null>(null);

  const phases: WorkflowPhase[] = [
    {
      id: 'initial',
      label: 'Start',
      description: 'Initialize pipeline',
      icon: '🚀',
      status: 'pending'
    },
    {
      id: 'url_collection',
      label: 'Collect URLs',
       description: 'Find or add intelligence sources',
      icon: '🔍',
      status: 'pending'
    },
    {
       id: 'source_validation',
       label: 'Validate Sources',
       description: 'Check source relevance',
      icon: '✅',
      status: 'pending'
    },
    {
       id: 'intelligence_definition',
       label: 'Define Intelligence',
       description: 'Specify intelligence to collect',
      icon: '📋',
      status: 'pending'
    },
    {
       id: 'intelligence_validation',
       label: 'Validate Intelligence',
       description: 'Verify intelligence completeness',
      icon: '🔍',
      status: 'pending'
    },
    {
      id: 'code_generation',
      label: 'Generate Code',
       description: 'Create intelligence collection script',
      icon: '💻',
      status: 'pending'
    },
    {
      id: 'ready_to_execute',
      label: 'Ready',
      description: 'Review and approve',
      icon: '👀',
      status: 'pending'
    },
    {
      id: 'executing',
      label: 'Execute',
       description: 'Run the investigation',
      icon: '▶️',
      status: 'pending'
    },
    {
      id: 'completed',
      label: 'Complete',
       description: 'Investigation finished',
      icon: '✨',
      status: 'pending'
    }
  ];

  useEffect(() => {
     if (currentInvestigation && ws) {
      // Request current workflow state
      send({
        type: 'state_request'
      });
    }
   }, [currentInvestigation, ws, send]);

  useEffect(() => {
     // Listen for workflow updates
     const handleMessage = (event: MessageEvent) => {
       try {
         const data = JSON.parse(event.data);
         
         if (data.type === 'workflow_state') {
           setWorkflowState(data.workflow);
           // Clear transitioning state when we get a new workflow state
           setTransitioningPhase(null);
         } else if (data.type === 'workflow_update') {
           setWorkflowState(data.workflow);
           // Clear transitioning state when we get a workflow update
           setTransitioningPhase(null);
         } else if (data.type === 'approval_request') {
           // Handle approval request
           handleApprovalRequest(data.approval);
         } else if (data.type === 'workflow_error') {
           // Handle workflow errors (including phase transition errors)
           console.error('Workflow error:', data.message);
           alert(`Workflow Error: ${data.message}`);
           // Clear transitioning state on error
           setTransitioningPhase(null);
         } else if (data.type === 'phase_transition_result') {
           // Handle phase transition results
           if (data.success) {
             console.log(`Successfully transitioned to phase: ${data.to_phase}`);
             // The workflow state will be updated via the workflow_update message
             // Clear transitioning state after a brief delay to allow UI to show transition
             setTimeout(() => setTransitioningPhase(null), 500);
           } else {
             console.error(`Failed to transition to phase: ${data.to_phase}`, data.error);
             alert(`Failed to transition to ${data.to_phase}: ${data.error}`);
             setTransitioningPhase(null);
           }
         }
       } catch (error) {
         console.error('Failed to parse WebSocket message:', error);
         // Clear transitioning state on error
         setTransitioningPhase(null);
       }
     };
     
     // Listen for websocket errors
     const handleError = (event: CustomEvent) => {
       console.log('WebSocket error:', event.detail.message);
       // Clear transitioning state on websocket error
       setTransitioningPhase(null);
     };

     if (ws) {
       ws.addEventListener('message', handleMessage);
       window.addEventListener('websocket-error' as any, handleError);
       
       return () => {
         ws.removeEventListener('message', handleMessage);
         window.removeEventListener('websocket-error' as any, handleError);
       };
     }
   }, [ws]);

  const handleApprovalRequest = (approval: any) => {
    // Show approval dialog or notification
    const approved = window.confirm(`Approval needed: ${approval.action}\n\nApprove this action?`);
    
    send({
      type: 'approval',
      approval_id: approval.id,
      approved: approved
    });
  };

  const getPhaseStatus = (phaseId: string): WorkflowPhase['status'] => {
    if (!workflowState) return 'pending';
    
    const phaseOrder = phases.map(p => p.id);
    const currentIndex = phaseOrder.indexOf(workflowState.phase);
    const targetIndex = phaseOrder.indexOf(phaseId);
    
    if (workflowState.phase === 'error') return 'error';
    if (targetIndex < currentIndex) return 'completed';
    if (targetIndex === currentIndex) return 'active';
    return 'pending';
  };

  const handlePhaseClick = async (phaseId: string) => {
    if (!workflowState) {
      console.error('No workflow state available');
      return;
    }

    // Check if we're already transitioning
    if (transitioningPhase) {
      console.log('Already transitioning to another phase');
      return;
    }

    // Check if the target phase is different from current phase
    if (phaseId === workflowState.phase) {
      console.log('Already in this phase');
      return;
    }

    // Define the allowed transitions for basic validation
    // This is a simplified version - the full logic is handled on the backend
    const allowedTransitions: Record<string, string[]> = {
      'initial': ['url_collection'],
      'url_collection': ['url_validation', 'initial'],
      'url_validation': ['schema_definition', 'url_collection', 'initial'],
      'schema_definition': ['schema_validation', 'url_collection', 'initial'],
      'schema_validation': ['code_generation', 'schema_definition', 'initial'],
      'code_generation': ['ready_to_execute', 'schema_validation', 'initial'],
      'ready_to_execute': ['executing', 'code_generation', 'initial'],
      'executing': ['completed', 'ready_to_execute', 'initial'],
      'completed': ['initial'],
      'error': ['initial']
    };

    // Check if the transition is allowed based on current phase
    const validTransitions = allowedTransitions[workflowState.phase] || [];
    if (!validTransitions.includes(phaseId)) {
      const currentPhaseLabel = phases.find(p => p.id === workflowState.phase)?.label || workflowState.phase;
      const targetPhaseLabel = phases.find(p => p.id === phaseId)?.label || phaseId;
      alert(`Cannot transition from ${currentPhaseLabel} to ${targetPhaseLabel}. Valid transitions are: ${validTransitions.map((t: string) => phases.find(p => p.id === t)?.label || t).join(', ')}`);
      return;
    }

    // Show confirmation for backward transitions or risky transitions
    const backwardPhases = ['initial', 'url_collection', 'schema_definition', 'ready_to_execute'];
    if (backwardPhases.includes(phaseId)) {
      const currentPhaseLabel = phases.find(p => p.id === workflowState.phase)?.label || workflowState.phase;
      const targetPhaseLabel = phases.find(p => p.id === phaseId)?.label || phaseId;
      const confirmed = window.confirm(
        `You are about to transition from ${currentPhaseLabel} back to ${targetPhaseLabel}. This may require reconfiguring previous settings. Are you sure?`
      );
      if (!confirmed) return;
    }

    try {
      // Set the transitioning state
      setTransitioningPhase(phaseId);

      // Send the phase transition request via WebSocket
      send({
        type: 'workflow_phase_transition',
        target_phase: phaseId,
        reason: 'manual_transition'
      });

      console.log(`Requesting transition to phase: ${phaseId}`);

      // Set a timeout to clear the transitioning state if no response is received within 10 seconds
      setTimeout(() => {
        if (transitioningPhase === phaseId) {
          setTransitioningPhase(null);
          console.warn(`Phase transition to ${phaseId} timed out`);
          alert(`Phase transition to ${phaseId} timed out. Please try again.`);
        }
      }, 10000);
      
    } catch (error) {
      console.error('Error requesting phase transition:', error);
      setTransitioningPhase(null); // Reset transitioning state on error
    }
  };

  return (
    <div className="w-64 bg-secondary p-4 border-r border-border overflow-y-auto">
      <h3 className="text-lg font-semibold mb-4">Workflow Progress</h3>
      
      <div className="space-y-2">
        {phases.map((phase, index) => {
          const status = getPhaseStatus(phase.id);
          const isActive = status === 'active';
          const isCompleted = status === 'completed';
          const isError = status === 'error';
          
           return (
             <div key={phase.id}>
               <div
                 className={clsx(
                   'p-3 rounded-lg cursor-pointer transition-all relative',
                   'hover:bg-background/50',
                   {
                     'bg-primary/20 border border-primary': isActive,
                     'bg-success/10': isCompleted,
                     'bg-error/10': isError,
                     'opacity-50': status === 'pending' && transitioningPhase !== phase.id,
                     'bg-primary/30': transitioningPhase === phase.id
                   }
                 )}
                 onClick={() => handlePhaseClick(phase.id)}
                 style={{ pointerEvents: transitioningPhase ? 'none' : 'auto' }}
               >
                 <div className="flex items-center space-x-3">
                   <div className={clsx(
                     'text-2xl relative',
                     (isActive || transitioningPhase === phase.id) && 'animate-pulse'
                   )}>
                     {phase.icon}
                     {transitioningPhase === phase.id && (
                       <span className="absolute -top-1 -right-1 bg-primary text-white rounded-full w-4 h-4 flex items-center justify-center text-xs">
                         ⏳
                       </span>
                     )}
                   </div>
                   <div className="flex-1">
                     <div className="font-medium flex items-center">
                       {phase.label}
                       {transitioningPhase === phase.id && (
                         <span className="ml-2 text-xs text-primary animate-pulse">transitioning</span>
                       )}
                     </div>
                     <div className="text-xs text-muted">{phase.description}</div>
                   </div>
                   {isCompleted && !transitioningPhase && (
                     <div className="text-success">✓</div>
                   )}
                   {isError && !transitioningPhase && (
                     <div className="text-error">✗</div>
                   )}
                 </div>
               </div>
               
               {index < phases.length - 1 && (
                 <div className={clsx(
                   'w-0.5 h-4 mx-6 transition-colors',
                   isCompleted ? 'bg-success' : 'bg-border'
                 )} />
               )}
             </div>
           );
        })}
      </div>
      
      {workflowState ? (
        <div className="mt-6 space-y-4">
          <div className="border-t border-border pt-4">
            <h4 className="font-medium mb-2">Current State</h4>
            <div className="space-y-2 text-sm">
              <div>
                 <span className="text-muted">Sources:</span>{' '}
                 <span className="font-medium">{workflowState.sources.length}</span>
              </div>
              <div>
                 <span className="text-muted">Intelligence Fields:</span>{' '}
                 <span className="font-medium">{workflowState.intelligence_fields.length}</span>
              </div>
              <div>
                <span className="text-muted">Code:</span>{' '}
                <span className="font-medium">
                  {workflowState.generated_code ? 'Generated' : 'Not ready'}
                </span>
              </div>
            </div>
          </div>
          
          {workflowState.pending_approvals.length > 0 && (
            <div className="border-t border-border pt-4">
              <h4 className="font-medium mb-2 text-warning">
                Pending Approvals ({workflowState.pending_approvals.length})
              </h4>
              <div className="space-y-2">
                {workflowState.pending_approvals.map((approval: any) => (
                  <div
                    key={approval.id}
                    className="p-2 bg-warning/10 rounded text-sm cursor-pointer hover:bg-warning/20"
                    onClick={() => handleApprovalRequest(approval)}
                  >
                    {approval.action}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          <div className="border-t border-border pt-4 text-xs text-muted">
            Last updated: {new Date(workflowState.updated_at).toLocaleTimeString()}
          </div>
        </div>
      ) : (
        <div className="mt-6 text-sm text-muted text-center">
          <p>Start a conversation to begin the workflow</p>
        </div>
      )}
    </div>
  );
};

export default WorkflowSidebar;