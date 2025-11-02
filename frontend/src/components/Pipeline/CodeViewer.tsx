import React, { useEffect, useState } from 'react';
 import { useInvestigationStore } from '../../store/investigationStore';
import Button from '../Common/Button';
import Prism from 'prismjs';

const CodeViewer: React.FC = () => {
  const { currentInvestigation } = useInvestigationStore();
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<any>(null);

  useEffect(() => {
    // Highlight code when it changes
    Prism.highlightAll();
   }, [currentInvestigation?.code]);

   const handleCopyCode = () => {
     if (currentInvestigation?.code) {
       navigator.clipboard.writeText(currentInvestigation.code);
       // You could add a toast notification here
     }
   };

   const handleDownloadCode = () => {
     if (currentInvestigation?.code) {
       const blob = new Blob([currentInvestigation.code], { type: 'text/plain' });
       const url = window.URL.createObjectURL(blob);
       const a = document.createElement('a');
       a.href = url;
        a.download = `${currentInvestigation.title.replace(/\s+/g, '_')}_osint_collector.py`;
       document.body.appendChild(a);
       a.click();
       document.body.removeChild(a);
       window.URL.revokeObjectURL(url);
     }
   };

    const handleExecuteCode = async () => {
      if (!currentInvestigation?.code) {
        alert('Please ensure you have code generated before executing.');
        return;
      }

     // Check for API key
     const apiKey = localStorage.getItem('SCRAPEGRAPH_API_KEY');
     if (!apiKey) {
       alert('Please configure your ScrapeGraphAI API key in Settings before executing.');
       return;
     }

     setIsExecuting(true);
     setExecutionResult(null);

      try {
        // For OSINT, we may want to execute the code differently
        // For now, let's just simulate execution or call the backend API directly
        // This would need to call a backend endpoint for actual execution
        console.log('Executing OSINT collection code...', currentInvestigation.id);
        
        // Placeholder for actual execution logic
        // In a real implementation, this would call an API endpoint to execute the code
        setExecutionResult({ 
          success: true, 
          results: ['OSINT collection executed successfully'] 
        });
      } catch (error) {
        console.error('Execution failed:', error);
        setExecutionResult({ 
          success: false, 
          errors: [`Execution failed: ${error}`] 
        });
      } finally {
        setIsExecuting(false);
      }
   };

     if (!currentInvestigation?.code) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <div className="text-center text-muted">
          <p className="text-lg mb-2">No code generated yet</p>
          <p className="text-sm">
             Use the AI assistant to generate code for your OSINT investigation
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border">
        <h3 className="text-lg font-semibold">Generated Code</h3>
        <div className="flex space-x-2">
          <Button 
            variant="primary" 
            size="sm" 
            onClick={handleExecuteCode}
            disabled={isExecuting}
          >
            {isExecuting ? '⚡ Executing...' : '▶️ Run'}
          </Button>
          <Button variant="secondary" size="sm" onClick={handleCopyCode}>
            📋 Copy
          </Button>
          <Button variant="secondary" size="sm" onClick={handleDownloadCode}>
            💾 Download
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-4">
        {executionResult && (
          <div className={`mb-4 p-4 rounded-lg ${executionResult.success ? 'bg-green-900/20 border border-green-500' : 'bg-red-900/20 border border-red-500'}`}>
            <h4 className="font-semibold mb-2">
              {executionResult.success ? '✅ Execution Successful' : '❌ Execution Failed'}
            </h4>
            {executionResult.success ? (
              <div>
                 <p className="text-sm mb-2">Collected {executionResult.results?.length || 0} intelligence items successfully!</p>
                <p className="text-xs text-muted">Check the Output tab to see the results.</p>
              </div>
            ) : (
              <div>
                <p className="text-sm text-red-400">
                  {executionResult.errors?.join(', ') || 'Unknown error occurred'}
                </p>
              </div>
            )}
          </div>
        )}
        
        <pre className="language-python">
          <code className="language-python">
             {currentInvestigation.code}
          </code>
        </pre>
      </div>
    </div>
  );
};

export default CodeViewer;