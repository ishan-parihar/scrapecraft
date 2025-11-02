import React from 'react';
import { useInvestigationStore } from '../../store/investigationStore';
import InvestigationPlanner from '../OSINT/Chat/InvestigationPlanner';

const ChatContainer: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();

  return (
    <div className="flex flex-col h-full">
      <div className="border-b border-border p-4 bg-secondary">
        <h2 className="text-lg font-semibold">Investigation Planner</h2>
        <p className="text-sm text-muted">
          {currentInvestigation ? currentInvestigation.title : 'Select an investigation'}
        </p>
      </div>
      
      {currentInvestigation ? (
        <InvestigationPlanner investigationId={currentInvestigation.id} />
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center text-muted">
            <div className="text-4xl mb-2">🔍</div>
            <p>No investigation selected</p>
            <p className="text-sm mt-1">Start a new investigation to begin planning</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatContainer;