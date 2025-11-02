import React from 'react';
import { AnalysisResult, CollectedEvidence } from '../../types/osint';

interface AnalysisViewProps {
  evidence: CollectedEvidence[];
  analysisResults: AnalysisResult[];
}

const AnalysisView: React.FC<AnalysisViewProps> = ({ evidence, analysisResults }) => {
  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Analysis & Findings</h3>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Evidence Summary */}
        <div className="border border-border rounded-lg p-4 bg-secondary">
          <h4 className="font-medium text-md mb-3">Evidence Summary</h4>
          
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-muted">Total Evidence</span>
              <span className="font-medium">{evidence.length}</span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-muted">Avg. Reliability</span>
              <span className="font-medium">
                {evidence.length > 0 
                  ? Math.round(evidence.reduce((sum, ev) => sum + ev.reliability_score, 0) / evidence.length) + '%' 
                  : '0%'}
              </span>
            </div>
            
            <div className="flex justify-between">
              <span className="text-muted">Avg. Relevance</span>
              <span className="font-medium">
                {evidence.length > 0 
                  ? Math.round(evidence.reduce((sum, ev) => sum + ev.relevance_score, 0) / evidence.length) + '%' 
                  : '0%'}
              </span>
            </div>
          </div>
          
          {evidence.length > 0 && (
            <div className="mt-4">
              <h5 className="font-medium text-sm mb-2">Top Evidence</h5>
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {evidence
                  .sort((a, b) => b.reliability_score - a.reliability_score)
                  .slice(0, 5)
                  .map((ev) => (
                    <div key={ev.id} className="p-2 bg-background border border-border rounded text-sm">
                      <div className="flex justify-between">
                        <span className="truncate">{ev.source}</span>
                        <span className="ml-2 text-muted">{Math.round(ev.reliability_score)}%</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
        
        {/* Analysis Results */}
        <div className="border border-border rounded-lg p-4 bg-secondary">
          <h4 className="font-medium text-md mb-3">Analysis Results</h4>
          
          {analysisResults.length === 0 ? (
            <div className="text-center py-4 text-muted">
              <p>No analysis results available</p>
              <p className="text-sm mt-1">Analysis will appear here after processing</p>
            </div>
          ) : (
            <div className="space-y-3">
              {analysisResults.map((result) => (
                <div key={result.id} className="p-3 bg-background border border-border rounded">
                  <div className="flex justify-between">
                    <h5 className="font-medium">{result.analysis_type}</h5>
                    <span className="text-xs px-2 py-1 bg-secondary rounded">
                      {Math.round(result.confidence * 100)}% confidence
                    </span>
                  </div>
                  
                  <div className="mt-2 text-sm">
                    <pre className="whitespace-pre-wrap break-words text-xs">
                      {JSON.stringify(result.results, null, 2).substring(0, 200) + '...'}
                    </pre>
                  </div>
                  
                  <div className="mt-2 flex flex-wrap gap-1">
                    {result.tags.map((tag, index) => (
                      <span key={index} className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
      
      {/* Correlation Map */}
      <div className="mt-6 border border-border rounded-lg p-4 bg-secondary">
        <h4 className="font-medium text-md mb-3">Evidence Correlations</h4>
        <div className="text-center py-8 text-muted">
          <p>Correlation visualization will appear here</p>
          <p className="text-sm mt-1">This view shows relationships between different pieces of evidence</p>
        </div>
      </div>
    </div>
  );
};

export default AnalysisView;