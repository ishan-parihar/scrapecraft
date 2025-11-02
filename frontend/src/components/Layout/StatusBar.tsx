import React from 'react';
import { useInvestigationStore } from '../../store/investigationStore';
import { useWebSocketStore } from '../../store/websocketStore';

const StatusBar: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();
  const { connectionStatus } = useWebSocketStore();

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'text-success';
      case 'connecting':
        return 'text-warning';
      case 'disconnected':
        return 'text-error';
      default:
        return 'text-muted';
    }
  };

  return (
    <div className="bg-secondary border-t border-border px-6 py-2 flex items-center justify-between text-sm">
      <div className="flex items-center space-x-6">
        <div className="flex items-center space-x-2">
          <span className="text-muted">Investigation:</span>
          <span className={getStatusColor(currentInvestigation?.status || 'PLANNING')}>
            {currentInvestigation?.status || 'PLANNING'}
          </span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-muted">Targets:</span>
          <span>{currentInvestigation?.targets.length || 0}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-muted">Evidence:</span>
          <span>{currentInvestigation?.collected_evidence.length || 0}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <span className="text-muted">Threats:</span>
          <span>{currentInvestigation?.threat_assessments.length || 0}</span>
        </div>
      </div>
      
      <div className="flex items-center space-x-4 text-xs text-muted">
        <span>OSINT-OS Intelligence Platform</span>
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${connectionStatus === 'connected' ? 'bg-success' : 'bg-error'}`} />
          <span className={getStatusColor(connectionStatus)}>
            {connectionStatus}
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;