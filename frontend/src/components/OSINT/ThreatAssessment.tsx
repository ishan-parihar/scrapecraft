import React, { useState, useEffect, useCallback } from 'react';
import { ThreatAssessment as ThreatAssessmentType, Investigation } from '../../types/osint';
import { osintAgentApi } from '../../services/osintAgentApi';

interface ThreatAssessmentProps {
  investigationId?: string;
  threats?: ThreatAssessmentType[];  // Add this to support direct threats prop
}

const ThreatAssessment: React.FC<ThreatAssessmentProps> = ({ investigationId, threats: threatsProp }) => {
  const [threats, setThreats] = useState<ThreatAssessmentType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadThreats = useCallback(async () => {
    if (!investigationId) return;
    
    try {
      setLoading(true);
      // This would be a real API call - for now using the investigation data
      const investigations: Investigation[] = await osintAgentApi.getInvestigations();
      const investigation = investigations.find((inv: Investigation) => inv.id === investigationId);
      
      if (investigation) {
        setThreats(investigation.threat_assessments || []);
      }
      setError(null);
    } catch (err) {
      console.error('Failed to load threats:', err);
      setError('Failed to load threat assessments');
      setThreats([]);
    } finally {
      setLoading(false);
    }
  }, [investigationId]);

  // Load threats for the investigation or use provided threats
  useEffect(() => {
    if (threatsProp && threatsProp.length > 0) {
      setThreats(threatsProp);
      setLoading(false);
    } else if (investigationId) {
      loadThreats();
    }
  }, [investigationId, threatsProp, loadThreats]);

  const getThreatLevelColor = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return 'text-red-500';
      case 'HIGH':
        return 'text-orange-500';
      case 'MEDIUM':
        return 'text-yellow-500';
      case 'LOW':
        return 'text-green-500';
      default:
        return 'text-gray-500';
    }
  };

  const createMockThreat = async () => {
    if (!investigationId) return;
    
    try {
      const newThreat = {
        title: 'Sample Security Threat',
        description: 'Potential security vulnerability identified in target infrastructure',
        threat_level: 'MEDIUM',
        threat_type: 'CYBERSECURITY',
        targets: ['target-001'],
        likelihood: 60,
        impact: 70
      };
      
      // This would create via API when endpoint is available
      // await osintAgentApi.createThreat(investigationId, newThreat);
      
      // For now, add to local state
      const threat: ThreatAssessmentType = {
        id: `threat-${Date.now()}`,
        investigation_id: investigationId,
        title: newThreat.title,
        description: newThreat.description,
        threat_level: newThreat.threat_level as any,
        threat_type: newThreat.threat_type as any,
        targets: newThreat.targets,
        likelihood: newThreat.likelihood,
        impact: newThreat.impact,
        risk_score: newThreat.likelihood * newThreat.impact / 100,
        status: 'ACTIVE',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        indicators: ['unusual_network_activity', 'suspicious_login_attempts'],
        mitigation_recommendations: ['Implement additional monitoring', 'Update security protocols'],
        sources: ['ev_001', 'ev_002']
      };
      
      setThreats(prev => [...prev, threat]);
    } catch (err) {
      console.error('Failed to create threat:', err);
    }
  };

  return (
    <div className="p-4 h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">Threat Assessments</h3>
        <button
          onClick={createMockThreat}
          className="px-3 py-1 bg-primary/10 hover:bg-primary/20 text-primary rounded text-sm"
        >
          Add Threat
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="text-center py-8 text-muted">
            <p>Loading threat assessments...</p>
          </div>
        ) : error ? (
          <div className="text-center py-8 text-error">
            <p>{error}</p>
          </div>
        ) : threats.length === 0 ? (
          <div className="text-center py-8 text-muted">
            <div className="text-4xl mb-2">🛡️</div>
            <p>No threat assessments available</p>
            <p className="text-sm mt-1">Threats will appear here when identified</p>
          </div>
        ) : (
          <div className="space-y-4">
            {threats.map((threat) => (
               <div key={threat.id} className="border border-border rounded-lg p-4 bg-secondary">
                 <div className="flex justify-between items-start">
                   <h4 className="font-medium text-lg">{threat.title}</h4>
                   <span className={`font-semibold ${getThreatLevelColor(threat.threat_level)}`}>
                     {threat.threat_level}
                   </span>
                 </div>
                 
                 <p className="text-muted mt-2">{threat.description}</p>
                 
                 <div className="grid grid-cols-3 gap-4 mt-4">
                   <div>
                     <p className="text-sm text-muted">Likelihood</p>
                     <p className="font-medium">{threat.likelihood}%</p>
                   </div>
                   <div>
                     <p className="text-sm text-muted">Impact</p>
                     <p className="font-medium">{threat.impact}%</p>
                   </div>
                   <div>
                     <p className="text-sm text-muted">Risk Score</p>
                     <p className="font-medium">{Math.round(threat.risk_score)}%</p>
                   </div>
                 </div>
                 
                 {threat.indicators && threat.indicators.length > 0 && (
                   <div className="mt-4">
                     <p className="text-sm text-muted">Indicators</p>
                     <div className="flex flex-wrap gap-2 mt-1">
                       {threat.indicators.map((indicator, index) => (
                         <span key={index} className="px-2 py-1 bg-primary/10 text-primary rounded text-sm">
                           {indicator}
                         </span>
                       ))}
                     </div>
                   </div>
                 )}
                 
                 {threat.mitigation_recommendations && threat.mitigation_recommendations.length > 0 && (
                   <div className="mt-4">
                     <p className="text-sm text-muted">Mitigation Recommendations</p>
                     <ul className="list-disc list-inside mt-1">
                       {threat.mitigation_recommendations.map((rec, index) => (
                         <li key={index} className="text-sm">{rec}</li>
                       ))}
                     </ul>
                   </div>
                 )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ThreatAssessment;