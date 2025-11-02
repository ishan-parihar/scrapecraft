import React, { useEffect, useState } from 'react';
import SplitView from './components/Layout/SplitView';
import Header from './components/Layout/Header';
import StatusBar from './components/Layout/StatusBar';
import LoadingScreen from './components/Common/LoadingScreen';
import { useWebSocket } from './hooks/useWebSocket';
import { useInvestigationStore } from './store/investigationStore';
import Prism from 'prismjs';
import 'prismjs/components/prism-python';
import 'prismjs/themes/prism-tomorrow.css';

function App() {
  const { 
    currentInvestigation, 
    createInvestigation, 
    fetchInvestigations, 
    isLoading 
  } = useInvestigationStore();
  const [isInitializing, setIsInitializing] = useState(true);
  
  useEffect(() => {
    // Initialize PrismJS
    Prism.highlightAll();
    
    // Auto-create an investigation on first load
    const initializeInvestigation = async () => {
      await fetchInvestigations();
      
      // If no current investigation, create one automatically
      if (!currentInvestigation) {
        await createInvestigation({
          title: 'New OSINT Investigation',
          description: 'Conducting intelligence assessment',
          classification: 'CONFIDENTIAL',
          priority: 'MEDIUM'
        });
      }
      
      // Small delay to ensure smooth loading experience
      setTimeout(() => {
        setIsInitializing(false);
      }, 500);
    };
    
    initializeInvestigation();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Initialize WebSocket connection
  useWebSocket(currentInvestigation?.id || 'default');

  // Show loading screen during initialization
  if (isInitializing || (isLoading && !currentInvestigation)) {
    return <LoadingScreen />;
  }

  return (
    <div className="h-screen flex flex-col bg-background text-foreground">
      <Header />
      <div className="flex-1 overflow-hidden">
        <SplitView />
      </div>
      <StatusBar />
      {/* ApprovalManager is now integrated in AgentCoordinator */}
    </div>
  );
}

export default App;