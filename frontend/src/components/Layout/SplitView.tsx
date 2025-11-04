import React, { useState } from 'react';
import ChatContainer from '../Chat/ChatContainer';
import InvestigationDashboard from '../OSINT/InvestigationDashboard';
import AgentCoordinator from '../Workflow/AgentCoordinator';
import { useInvestigationStore } from '../../store/investigationStore';

const SplitView: React.FC = () => {
  const [splitPosition, setSplitPosition] = useState(40); // 40% for chat
  const [isDragging, setIsDragging] = useState(false);
  const { currentInvestigation } = useInvestigationStore();

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    
    const container = e.currentTarget;
    const rect = container.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const percentage = (x / rect.width) * 100;
    
    setSplitPosition(Math.min(Math.max(percentage, 20), 80));
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handlePhaseChange = (phase: string) => {
    if (currentInvestigation) {
      // Update investigation phase via store
      useInvestigationStore.getState().updateInvestigation(currentInvestigation.id, {
        current_phase: phase,
        updated_at: new Date().toISOString()
      });
    }
  };

  const handleAgentAssignment = (assignment: any) => {
    console.log('Agent assigned:', assignment);
    // In a real implementation, this would update agent assignments in the store
  };

  return (
    <div className="flex h-full overflow-hidden">
      {/* Agent Coordinator Sidebar - Replaces Workflow Sidebar */}
      <div className="w-80 flex-shrink-0">
        <AgentCoordinator />
      </div>
      
      {/* Main Content Area */}
      <div 
        className="flex-1 flex h-full relative overflow-hidden"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {/* Chat Panel - Investigation Planning */}
        <div 
          className="h-full border-r border-border"
          style={{ width: `${splitPosition}%` }}
        >
          <ChatContainer />
        </div>
        
        {/* Resizer */}
        <div
          className="absolute top-0 h-full w-1 cursor-col-resize hover:bg-primary/50 transition-colors"
          style={{ left: `${splitPosition}%`, marginLeft: '-2px' }}
          onMouseDown={handleMouseDown}
        />
        
        {/* Investigation Dashboard - Replaces Pipeline Panel */}
        <div 
          className="h-full overflow-auto"
          style={{ width: `${100 - splitPosition}%` }}
        >
          {currentInvestigation ? (
            <InvestigationDashboard 
              investigation={currentInvestigation}
              onPhaseChange={handlePhaseChange}
              onAgentAssignment={handleAgentAssignment}
            />
          ) : (
            <div className="h-full flex items-center justify-center bg-background">
              <div className="text-center">
                <div className="text-4xl mb-4">🔍</div>
                <h3 className="text-lg font-medium mb-2">No Investigation Selected</h3>
                <p className="text-muted">Start a new investigation to begin</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SplitView;