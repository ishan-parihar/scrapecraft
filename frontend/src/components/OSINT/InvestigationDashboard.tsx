import React, { useState } from 'react';
import ClassificationBanner from '../Common/ClassificationBanner';
import TargetManager from './TargetManager';
import EvidenceViewer from './EvidenceViewer';
import AgentCoordinator from '../Workflow/AgentCoordinator';
import ThreatAssessment from './ThreatAssessment';
import Reports from './Reports';
import AnalysisView from './AnalysisView';
import { Investigation } from '../../types/osint';

type TabType = 'overview' | 'targets' | 'agents' | 'evidence' | 'analysis' | 'threats' | 'reports';

interface InvestigationDashboardProps {
  investigation: Investigation;
  onPhaseChange: (phase: string) => void;
  onAgentAssignment: (assignment: any) => void;
}

const InvestigationDashboard: React.FC<InvestigationDashboardProps> = ({ 
  investigation,
  onPhaseChange,
  onAgentAssignment
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'overview', label: 'Overview', icon: '📊' },
    { id: 'targets', label: 'Targets', icon: '🎯' },
    { id: 'agents', label: 'Agents', icon: '🤖' },
    { id: 'evidence', label: 'Evidence', icon: '📋' },
    { id: 'analysis', label: 'Analysis', icon: '🔍' },
    { id: 'threats', label: 'Threats', icon: '⚠️' },
    { id: 'reports', label: 'Reports', icon: '📄' }
  ];

   const renderContent = () => {
     switch (activeTab) {
       case 'overview':
         return <div className="p-4">Investigation Overview content goes here</div>;
       case 'targets':
         return <TargetManager targets={investigation.targets} />;
       case 'agents':
         return <AgentCoordinator />;
       case 'evidence':
         return <EvidenceViewer />;
       case 'analysis':
         return <AnalysisView evidence={investigation.collected_evidence} analysisResults={investigation.analysis_results} />;
       case 'threats':
         return <ThreatAssessment threats={investigation.threat_assessments} />;
       case 'reports':
         return <Reports reports={investigation.generated_reports} />;
       default:
         return <div className="p-4">Select a tab to view content</div>;
     }
   };

  return (
    <div className="flex flex-col h-full">
      {/* Classification Banner */}
      <ClassificationBanner classification={investigation.classification} />
      
      {/* Tab Navigation */}
      <div className="border-b border-border bg-secondary">
        <div className="flex space-x-1 p-2 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap flex items-center ${
                activeTab === tab.id
                  ? 'bg-background text-foreground border-b-2 border-primary'
                  : 'text-muted hover:text-foreground hover:bg-secondary'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">
        {renderContent()}
      </div>
    </div>
  );
};

export default InvestigationDashboard;