import React, { useState } from 'react';
import { InvestigationTarget } from '../../types/osint';

interface TargetManagerProps {
  targets: InvestigationTarget[];
}

const TargetManager: React.FC<TargetManagerProps> = ({ targets }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTarget, setSelectedTarget] = useState<InvestigationTarget | null>(null);

  const filteredTargets = targets.filter(target => 
    target.identifier.toLowerCase().includes(searchTerm.toLowerCase()) ||
    target.aliases.some(alias => alias.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const getTargetTypeColor = (type: string) => {
    switch (type) {
      case 'PERSON':
        return 'bg-purple-500/20 text-purple-700 dark:text-purple-300';
      case 'ORGANIZATION':
        return 'bg-blue-500/20 text-blue-700 dark:text-blue-300';
      case 'LOCATION':
        return 'bg-green-500/20 text-green-700 dark:text-green-300';
      case 'DOMAIN':
        return 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-300';
      case 'SOCIAL_MEDIA':
        return 'bg-red-500/20 text-red-700 dark:text-red-300';
      default:
        return 'bg-gray-500/20 text-gray-700 dark:text-gray-300';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'HIGH':
        return 'bg-red-500/20 text-red-700 dark:text-red-300';
      case 'MEDIUM':
        return 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-300';
      case 'LOW':
        return 'bg-green-500/20 text-green-700 dark:text-green-300';
      default:
        return 'bg-gray-500/20 text-gray-700 dark:text-gray-300';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ACTIVE':
        return 'bg-success/20 text-success';
      case 'COMPLETED':
        return 'bg-success/20 text-success';
      case 'FAILED':
        return 'bg-error/20 text-error';
      case 'PENDING':
        return 'bg-warning/20 text-warning';
      default:
        return 'bg-muted/20 text-muted';
    }
  };

  return (
    <div className="flex h-full">
      <div className="w-1/3 pr-4 border-r border-border flex flex-col">
        <div className="mb-4">
          <input
            type="text"
            placeholder="Search targets..."
            className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
        
        <div className="flex-1 overflow-y-auto">
          <h3 className="font-medium mb-2">Targets ({filteredTargets.length})</h3>
          <div className="space-y-2">
            {filteredTargets.map(target => (
              <div 
                key={target.id}
                className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                  selectedTarget?.id === target.id 
                    ? 'border-primary bg-primary/10' 
                    : 'border-border hover:bg-secondary'
                }`}
                onClick={() => setSelectedTarget(target)}
              >
                <div className="flex justify-between items-start">
                  <div className="font-medium text-sm truncate">{target.identifier}</div>
                  <span className={`text-xs px-2 py-1 rounded-full ${getTargetTypeColor(target.type)}`}>
                    {target.type}
                  </span>
                </div>
                
                <div className="flex justify-between items-center mt-2 text-xs">
                  <span className={`px-2 py-0.5 rounded ${getPriorityColor(target.priority)}`}>
                    {target.priority}
                  </span>
                  <span className={`px-2 py-0.5 rounded ${getStatusColor(target.status)}`}>
                    {target.status}
                  </span>
                </div>
                
                {target.aliases.length > 0 && (
                  <div className="mt-2 text-xs text-muted truncate">
                    <span className="font-medium">Aliases:</span> {target.aliases.join(', ')}
                  </div>
                )}
              </div>
            ))}
            
            {filteredTargets.length === 0 && (
              <div className="text-center py-8 text-muted">
                <p>No targets found</p>
                <p className="text-sm mt-1">Try a different search term</p>
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div className="w-2/3 pl-4 flex flex-col">
        {selectedTarget ? (
          <>
            <div className="mb-4">
              <div className="flex justify-between items-start">
                <h3 className="text-lg font-semibold">{selectedTarget.identifier}</h3>
                <span className={`px-3 py-1 rounded-full text-sm ${getTargetTypeColor(selectedTarget.type)}`}>
                  {selectedTarget.type}
                </span>
              </div>
              
              <div className="flex space-x-4 mt-2">
                <div>
                  <span className="text-muted text-sm">Priority: </span>
                  <span className={`text-sm px-2 py-0.5 rounded ${getPriorityColor(selectedTarget.priority)}`}>
                    {selectedTarget.priority}
                  </span>
                </div>
                <div>
                  <span className="text-muted text-sm">Status: </span>
                  <span className={`text-sm px-2 py-0.5 rounded ${getStatusColor(selectedTarget.status)}`}>
                    {selectedTarget.status}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="mb-4">
              <h4 className="font-medium mb-2">Aliases</h4>
              <div className="flex flex-wrap gap-2">
                {selectedTarget.aliases.map((alias, index) => (
                  <span 
                    key={index} 
                    className="px-3 py-1 bg-secondary rounded-full text-sm"
                  >
                    {alias}
                  </span>
                ))}
                {selectedTarget.aliases.length === 0 && (
                  <span className="text-muted italic">No aliases defined</span>
                )}
              </div>
            </div>
            
            <div className="mb-4">
              <h4 className="font-medium mb-2">Collection Requirements</h4>
              <ul className="list-disc list-inside space-y-1">
                {selectedTarget.collection_requirements.map((req, index) => (
                  <li key={index} className="text-sm">{req}</li>
                ))}
                {selectedTarget.collection_requirements.length === 0 && (
                  <li className="text-muted italic">No collection requirements defined</li>
                )}
              </ul>
            </div>
            
            {selectedTarget.metadata && Object.keys(selectedTarget.metadata).length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium mb-2">Metadata</h4>
                <div className="bg-background p-3 rounded border border-border text-sm">
                  <pre className="whitespace-pre-wrap break-words">
                    {JSON.stringify(selectedTarget.metadata, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center text-muted">
              <div className="text-4xl mb-2">🎯</div>
              <p>Select a target to view details</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TargetManager;