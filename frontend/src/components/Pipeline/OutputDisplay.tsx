import React, { useState } from 'react';
 import { useInvestigationStore } from '../../store/investigationStore';
import Button from '../Common/Button';

type ViewMode = 'table' | 'json';

const OutputDisplay: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('table');
  const { currentInvestigation } = useInvestigationStore();

  const renderTableView = () => {
    const evidence = currentInvestigation?.collected_evidence || [];
    
    if (!evidence || evidence.length === 0) return null;

    // Get all unique keys from evidence content
    const allKeys = new Set<string>();
    evidence.forEach(item => {
      if (item.content.type === 'structured' && typeof item.content.value === 'object') {
        Object.keys(item.content.value).forEach(key => allKeys.add(key));
      }
    });

    const keys = Array.from(allKeys);

    return (
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b border-border">
              <th className="p-2 text-left text-sm font-medium text-muted">ID</th>
              <th className="p-2 text-left text-sm font-medium text-muted">Type</th>
              <th className="p-2 text-left text-sm font-medium text-muted">Source</th>
              <th className="p-2 text-left text-sm font-medium text-muted">Reliability</th>
              {keys.map(key => (
                <th key={key} className="p-2 text-left text-sm font-medium text-muted">
                  {key}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {evidence.map((item, index) => (
              <tr key={item.id} className="border-b border-border hover:bg-secondary/50">
                <td className="p-2 text-sm">
                  {item.id.substring(0, 8)}...
                </td>
                <td className="p-2 text-sm">
                  {item.source_type}
                </td>
                <td className="p-2 text-sm">
                  {item.source}
                </td>
                <td className="p-2 text-sm">
                  {item.reliability_score}%
                </td>
                {item.content.type === 'structured' && typeof item.content.value === 'object' && !Array.isArray(item.content.value) && item.content.value !== null ? (
                  keys.map(key => (
                    <td key={key} className="p-2 text-sm">
                      {item.content.value && typeof item.content.value === 'object' && key in item.content.value 
                        ? (item.content.value as Record<string, any>)[key] 
                        : '-'}
                    </td>
                  ))
                ) : (
                  <td colSpan={keys.length} className="p-2 text-sm">
                    {item.content.summary || (typeof item.content.value === 'string' ? item.content.value : JSON.stringify(item.content.value)) || '-'}
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const handleExport = (format: 'json' | 'csv') => {
    const evidence = currentInvestigation?.collected_evidence || [];
    if (!evidence || evidence.length === 0) return;

    let content: string;
    let mimeType: string;
    let extension: string;

    if (format === 'json') {
      content = JSON.stringify(evidence, null, 2);
      mimeType = 'application/json';
      extension = 'json';
    } else {
      // CSV export
      if (evidence.length === 0) return;

      // Create CSV from evidence data
      const keys = ['id', 'source_type', 'source', 'reliability_score', 'created_at'];
      const csv = [
        ['ID', 'Type', 'Source', 'Reliability', 'Date', ...keys].join(','),
        ...evidence.map(item => {
          const basicData = [
            item.id.substring(0, 16),
            item.source_type,
            item.source,
            item.reliability_score,
            new Date(item.collected_at).toLocaleDateString()
          ];
          
          if (item.content.type === 'structured' && typeof item.content.value === 'object' && !Array.isArray(item.content.value) && item.content.value !== null) {
            return [...basicData, ...keys.map(k => JSON.stringify((item.content.value as Record<string, any>)[k] || ''))].join(',');
          } else {
            return [...basicData, ...keys.map(() => JSON.stringify(typeof item.content.value === 'string' ? item.content.value : JSON.stringify(item.content.value) || ''))].join(',');
          }
        })
      ].join('\n');

      content = csv;
      mimeType = 'text/csv';
      extension = 'csv';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
     a.download = `${currentInvestigation?.title.replace(/\s+/g, '_')}_evidence.${extension}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const evidence = currentInvestigation?.collected_evidence || [];
  if (!evidence || evidence.length === 0) {
    return (
      <div className="h-full flex items-center justify-center p-4">
        <div className="text-center text-muted">
          <p className="text-lg mb-2">No evidence collected yet</p>
          <p className="text-sm">
            Execute your investigation to see the collected intelligence here
          </p>
        </div>
      </div>
    );
  }

  const reliableCount = evidence.filter(e => e.reliability_score >= 70).length;
  const questionableCount = evidence.filter(e => e.reliability_score < 70 && e.reliability_score >= 30).length;
  const unreliableCount = evidence.filter(e => e.reliability_score < 30).length;

  const renderJsonView = () => {
    const evidence = currentInvestigation?.collected_evidence || [];
    return (
      <pre className="language-json overflow-auto">
        <code>
          {JSON.stringify(evidence, null, 2)}
        </code>
      </pre>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-4 border-b border-border">
         <div className="flex items-center space-x-4">
           <h3 className="text-lg font-semibold">Collected Evidence</h3>
           <div className="text-sm text-muted">
             <span className="text-success">{reliableCount} reliable</span>
             {questionableCount > 0 && (
               <span className="text-warning ml-2">{questionableCount} questionable</span>
             )}
             {unreliableCount > 0 && (
               <span className="text-error ml-2">{unreliableCount} unreliable</span>
             )}
           </div>
         </div>
        
        <div className="flex items-center space-x-2">
          <div className="flex rounded-md overflow-hidden">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1 text-sm ${
                viewMode === 'table'
                  ? 'bg-primary text-white'
                  : 'bg-secondary text-foreground'
              }`}
            >
              Table
            </button>
            <button
              onClick={() => setViewMode('json')}
              className={`px-3 py-1 text-sm ${
                viewMode === 'json'
                  ? 'bg-primary text-white'
                  : 'bg-secondary text-foreground'
              }`}
            >
              JSON
            </button>
          </div>
          
          <Button variant="secondary" size="sm" onClick={() => handleExport('json')}>
            Export JSON
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('csv')}>
            Export CSV
          </Button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-4">
        {viewMode === 'table' ? renderTableView() : renderJsonView()}
      </div>
    </div>
  );
};

export default OutputDisplay;