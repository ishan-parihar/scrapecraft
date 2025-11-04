import React, { useState } from 'react';
import Button from '../Common/Button';
import SettingsModal from '../Settings/SettingsModal';
import logo from '../../assets/logo.png';
import { useInvestigationStore } from '../../store/investigationStore';

const Header: React.FC = () => {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const { createInvestigation } = useInvestigationStore();

  const handleNewInvestigation = async () => {
    await createInvestigation({
      title: 'New OSINT Investigation',
      description: 'Conducting intelligence assessment',
      classification: 'UNCLASSIFIED',
      priority: 'MEDIUM'
    });
  };

  // Mock investigation data for demonstration
  const currentInvestigation = {
    title: 'Corporate Intelligence Assessment',
    classification: 'CONFIDENTIAL'
  };

  return (
    <>
    <header className="bg-secondary border-b border-border px-6 py-3 flex items-center justify-between">
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2">
          <img src={logo} alt="OSINT-OS" className="h-8 w-8" />
          <h1 className="text-xl font-semibold text-primary">OSINT-OS</h1>
        </div>
        {currentInvestigation && (
          <span className="text-sm text-muted">
            {currentInvestigation.title}
          </span>
        )}
      </div>
      
      <div className="flex items-center space-x-3">
        <Button
          variant="secondary"
          size="sm"
          onClick={handleNewInvestigation}
        >
          New Investigation
        </Button>
        <Button 
          variant="secondary" 
          size="sm"
          onClick={() => setIsSettingsOpen(true)}
        >
          Settings
        </Button>
      </div>
    </header>
    
    <SettingsModal 
      isOpen={isSettingsOpen}
      onClose={() => setIsSettingsOpen(false)}
    />
    </>
  );
};

export default Header;