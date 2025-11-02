import React from 'react';
 import { useInvestigationStore } from '../../store/investigationStore';
import LoadingSpinner from '../Common/LoadingSpinner';

const OutputView: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();

   if (!currentInvestigation) {
    return (
      <div className="h-full flex items-center justify-center text-muted">
         <p>No investigation selected</p>
      </div>
    );
  }

   if (currentInvestigation.status === 'ACTIVE' || currentInvestigation.status === 'PLANNING') {
    return (
      <div className="h-full flex flex-col items-center justify-center">
        <LoadingSpinner />
         <p className="mt-4 text-muted">Investigation in progress...</p>
      </div>
    );
  }

  const evidence = currentInvestigation.collected_evidence || [];
  if (!evidence || evidence.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-muted">
        <p className="text-lg mb-2">No collected evidence yet</p>
         <p className="text-sm">Execute your investigation to collect OSINT intelligence</p>
      </div>
    );
  }

   return (
    <div className="h-full flex flex-col p-4">
      <div className="mb-4">
         <h3 className="text-lg font-semibold mb-2">Collected Evidence</h3>
         <div className="text-sm text-muted">
           Status: <span className={`font-medium ${
             currentInvestigation.status === 'COMPLETED' ? 'text-success' : 
             currentInvestigation.status === 'ARCHIVED' ? 'text-muted' : 
             'text-warning'
           }`}>
             {currentInvestigation.status}
           </span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-4">
        {evidence.map((item, index) => (
          <div key={item.id} className="card">
            <div className="flex items-start justify-between mb-2">
              <h4 className="font-medium">
                Evidence {index + 1}: {item.source_type}
                <span className="text-sm text-muted ml-2">({item.source})</span>
              </h4>
              <span className={`text-sm ${
                item.reliability_score >= 70 ? 'text-success' : 
                item.reliability_score >= 30 ? 'text-warning' : 
                'text-error'
              }`}>
                Reliability: {item.reliability_score}%
              </span>
            </div>
            
            <div className="bg-code-bg rounded-md p-3 overflow-x-auto">
              <pre className="text-sm text-code-text">
                {JSON.stringify(item, null, 2)}
              </pre>
            </div>
          </div>
        ))}
      </div>

      {evidence.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border">
          <div className="flex justify-between items-center">
            <span className="text-sm text-muted">
              Total evidence: {evidence.length}
            </span>
            <button
              onClick={() => {
                const dataStr = JSON.stringify(evidence, null, 2);
                const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                
                 const exportFileDefaultName = `osint_evidence_${Date.now()}.json`;
                
                const linkElement = document.createElement('a');
                linkElement.setAttribute('href', dataUri);
                linkElement.setAttribute('download', exportFileDefaultName);
                linkElement.click();
              }}
              className="text-sm text-accent hover:underline"
            >
              Export as JSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default OutputView;