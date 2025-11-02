import React from 'react';
import { ThreatAssessment as ThreatAssessmentType } from '../../types/osint';

interface ThreatAssessmentProps {
  threats: ThreatAssessmentType[];
}

const ThreatAssessment: React.FC<ThreatAssessmentProps> = ({ threats }) => {
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

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Threat Assessments</h3>
      
      {threats.length === 0 ? (
        <div className="text-center py-8 text-muted">
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
                  <p className="text-sm text-muted">Type</p>
                  <p className="font-medium">{threat.threat_type}</p>
                </div>
                <div>
                  <p className="text-sm text-muted">Likelihood</p>
                  <p className="font-medium">{threat.likelihood * 100}%</p>
                </div>
                <div>
                  <p className="text-sm text-muted">Impact</p>
                  <p className="font-medium">{threat.impact * 100}%</p>
                </div>
              </div>
              
              {threat.targets && threat.targets.length > 0 && (
                <div className="mt-4">
                  <p className="text-sm text-muted">Targets</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {threat.targets.map((target, index) => (
                      <span key={index} className="px-2 py-1 bg-primary/10 text-primary rounded text-sm">
                        {target}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ThreatAssessment;