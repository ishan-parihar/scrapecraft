import React, { useState, useEffect, useCallback } from 'react';
import { CollectedEvidence } from '../../types/osint';

interface EvidenceViewerProps {
  investigationId?: string;
}

const EvidenceViewer: React.FC<EvidenceViewerProps> = ({ investigationId }) => {
  const [selectedEvidence, setSelectedEvidence] = useState<CollectedEvidence | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [filterReliability, setFilterReliability] = useState<number>(0);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [evidence, setEvidence] = useState<CollectedEvidence[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadEvidence = useCallback(async () => {
    if (!investigationId) return;
    
    try {
      setLoading(true);
      // This would be a real API call - for now using mock data
      // const evidenceData = await osintAgentApi.getInvestigationEvidence(investigationId);
      
      // Mock evidence data for demonstration
      const mockEvidence: CollectedEvidence[] = [
    {
      id: 'ev_001',
      investigation_id: 'inv_001',
      source: 'twitter.com/user123',
      source_type: 'SOCIAL_MEDIA',
      content: {
        type: 'text',
        data: 'Important information about the target organization',
        summary: 'Twitter post mentioning key personnel change'
      },
      metadata: {
        url: 'https://twitter.com/user123/status/123456789',
        timestamp: '2023-10-15T10:30:00Z',
        source_agent: 'social_media_collector_1',
        collection_method: 'API'
      },
      reliability_score: 85,
      relevance_score: 90,
      collected_at: '2023-10-15T10:30:00Z',
      verified: true,
      classification: 'CONFIDENTIAL',
      tags: ['personnel', 'change', 'twitter'],
      related_evidence: ['ev_002', 'ev_005'],
      source_confidence: 90,
      data_type: 'TEXT'
    },
    {
      id: 'ev_002',
      investigation_id: 'inv_001',
      source: 'linkedin.com/company/abc-corp',
      source_type: 'SOCIAL_MEDIA',
      content: {
        type: 'structured',
        data: {
          company: 'ABC Corp',
          employees: 500,
          recent_posts: 12,
          hiring_activity: 'high'
        },
        summary: 'LinkedIn company profile showing recent activity'
      },
      metadata: {
        url: 'https://linkedin.com/company/abc-corp',
        timestamp: '2023-10-15T09:15:00Z',
        source_agent: 'social_media_collector_1',
         collection_method: 'web_extraction'
      },
      reliability_score: 95,
      relevance_score: 85,
      collected_at: '2023-10-15T09:15:00Z',
      verified: true,
      classification: 'CONFIDENTIAL',
      tags: ['company', 'profile', 'linkedin'],
      related_evidence: ['ev_001'],
      source_confidence: 95,
      data_type: 'STRUCTURED_DATA'
    },
    {
      id: 'ev_003',
      investigation_id: 'inv_001',
      source: 'public-records.gov',
      source_type: 'PUBLIC_RECORDS',
content: {
          type: 'structured',
          data: {
            name: 'John Smith',
            filing_date: '2023-09-20',
            document_type: 'Financial Disclosure'
          },
          summary: 'Public financial disclosure filing'
        },
      metadata: {
        url: 'https://public-records.gov/filing/12345',
        timestamp: '2023-10-14T14:20:00Z',
        source_agent: 'public_records_collector_1',
        collection_method: 'document_retrieval'
      },
      reliability_score: 100,
      relevance_score: 75,
      collected_at: '2023-10-14T14:20:00Z',
      verified: true,
      classification: 'CONFIDENTIAL',
      tags: ['financial', 'disclosure', 'public_record'],
      related_evidence: [],
      source_confidence: 100,
      data_type: 'DOCUMENT'
    }
  ];
      
      setEvidence(mockEvidence);
      setError(null);
    } catch (err) {
      console.error('Failed to load evidence:', err);
      setError('Failed to load evidence');
      setEvidence([]);
    } finally {
      setLoading(false);
    }
  }, [investigationId]);

  // Load evidence for the investigation
  useEffect(() => {
    if (investigationId) {
      loadEvidence();
    }
  }, [investigationId, loadEvidence]);

  const filteredEvidence = evidence.filter(evidenceItem => {
    const matchesType = filterType === 'ALL' || evidenceItem.source_type === filterType;
    const matchesReliability = evidenceItem.reliability_score >= filterReliability;
    const matchesSearch = searchTerm === '' || 
      evidenceItem.source.toLowerCase().includes(searchTerm.toLowerCase()) ||
      evidenceItem.content.summary?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      evidenceItem.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    
    return matchesType && matchesReliability && matchesSearch;
  });

  const getSourceTypeColor = (type: string) => {
    switch (type) {
      case 'SOCIAL_MEDIA':
        return 'bg-red-500/20 text-red-700 dark:text-red-300';
      case 'PUBLIC_RECORDS':
        return 'bg-blue-500/20 text-blue-700 dark:text-blue-300';
      case 'WEB_CONTENT':
        return 'bg-green-500/20 text-green-700 dark:text-green-300';
      case 'DARK_WEB':
        return 'bg-purple-500/20 text-purple-700 dark:text-purple-300';
      case 'HUMINT':
        return 'bg-yellow-500/20 text-yellow-700 dark:text-yellow-300';
      default:
        return 'bg-gray-500/20 text-gray-700 dark:text-gray-300';
    }
  };

  const getReliabilityColor = (score: number) => {
    if (score >= 90) return 'text-success';
    if (score >= 70) return 'text-warning';
    return 'text-error';
  };

  const getReliabilityBgColor = (score: number) => {
    if (score >= 90) return 'bg-success/20';
    if (score >= 70) return 'bg-warning/20';
    return 'bg-error/20';
  };

  const createMockEvidence = async () => {
    if (!investigationId) return;
    
    try {
      // This would create via API when endpoint is available
      // await osintAgentApi.createEvidence(investigationId, evidenceData);
      
      // For now, add to local state
      const newEvidence: CollectedEvidence = {
        id: `ev-${Date.now()}`,
        investigation_id: investigationId,
        source: 'mock-source.com',
        source_type: 'WEB_CONTENT',
        content: {
          type: 'text',
          data: 'Mock evidence content for demonstration',
          summary: 'Mock evidence created for testing purposes'
        },
        metadata: {
          url: 'https://mock-source.com/evidence',
          timestamp: new Date().toISOString(),
          source_agent: 'test-agent',
          collection_method: 'manual'
        },
        reliability_score: 75,
        relevance_score: 80,
        collected_at: new Date().toISOString(),
        verified: false,
        classification: 'CONFIDENTIAL',
        tags: ['mock', 'test'],
        related_evidence: [],
        source_confidence: 75,
        data_type: 'TEXT'
      };
      
      setEvidence(prev => [newEvidence, ...prev]);
    } catch (err) {
      console.error('Failed to create evidence:', err);
    }
  };

  return (
    <div className="flex h-full flex-col">
      {/* Filters */}
      <div className="p-4 border-b border-border bg-secondary">
        <div className="flex justify-between items-center mb-4">
          <h3 className="font-medium">Evidence Collection</h3>
          <button
            onClick={createMockEvidence}
            className="px-3 py-1 bg-primary/10 hover:bg-primary/20 text-primary rounded text-sm"
          >
            Add Evidence
          </button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Search</label>
            <input
              type="text"
              placeholder="Search evidence..."
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">Source Type</label>
            <select
              className="w-full px-3 py-2 bg-background border border-border rounded-md text-foreground text-sm"
              value={filterType}
              onChange={(e) => setFilterType(e.target.value)}
            >
              <option value="ALL">All Types</option>
              <option value="SOCIAL_MEDIA">Social Media</option>
              <option value="PUBLIC_RECORDS">Public Records</option>
              <option value="WEB_CONTENT">Web Content</option>
              <option value="DARK_WEB">Dark Web</option>
              <option value="HUMINT">HUMINT</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium mb-1">
              Reliability: {filterReliability}%
            </label>
            <input
              type="range"
              min="0"
              max="100"
              value={filterReliability}
              onChange={(e) => setFilterReliability(parseInt(e.target.value))}
              className="w-full"
            />
          </div>
          
          <div className="flex items-end">
            <button className="w-full px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm">
              Apply Filters
            </button>
          </div>
        </div>
</div>
       
       <div className="flex flex-1 overflow-hidden">
         {/* Evidence List */}
         <div className="w-1/3 pr-4 border-r border-border overflow-y-auto">
           <h3 className="font-medium mb-3">
             Collected Evidence ({filteredEvidence.length})
           </h3>
           
           {loading ? (
             <div className="text-center py-8 text-muted">
               <p>Loading evidence...</p>
             </div>
           ) : error ? (
             <div className="text-center py-8 text-error">
               <p>{error}</p>
             </div>
           ) : (
             <div className="space-y-3">
            {filteredEvidence.map(evidenceItem => (
<div 
                 key={evidenceItem.id}
                 className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                   selectedEvidence?.id === evidenceItem.id 
                     ? 'border-primary bg-primary/10' 
                     : 'border-border hover:bg-secondary'
                 }`}
                 onClick={() => setSelectedEvidence(evidenceItem)}
               >
                 <div className="flex justify-between items-start">
                   <div className="font-medium text-sm truncate">{evidenceItem.source}</div>
                   <span className={`text-xs px-2 py-1 rounded-full ${getSourceTypeColor(evidenceItem.source_type)}`}>
                     {evidenceItem.source_type.replace('_', ' ')}
                   </span>
                 </div>
                 
                 <div className="mt-2 text-xs text-muted line-clamp-2">
                   {evidenceItem.content.summary || 'No summary available'}
                 </div>
                 
                 <div className="flex justify-between items-center mt-3">
                   <div className={`text-xs px-2 py-1 rounded ${getReliabilityBgColor(evidenceItem.reliability_score)}`}>
                     <span className={getReliabilityColor(evidenceItem.reliability_score)}>
                       {evidenceItem.reliability_score}% reliability
                     </span>
                   </div>
                   
                   <div className="text-xs text-muted">
                     {new Date(evidenceItem.collected_at).toLocaleDateString()}
                   </div>
                 </div>
                 
                 <div className="mt-2 flex flex-wrap gap-1">
                   {evidenceItem.tags.slice(0, 3).map((tag, index) => (
                     <span key={index} className="text-xs bg-secondary px-2 py-0.5 rounded">
                       {tag}
                     </span>
                   ))}
                   {evidenceItem.tags.length > 3 && (
                     <span className="text-xs text-muted">+{evidenceItem.tags.length - 3} more</span>
                   )}
                 </div>
               </div>
            ))}
            
{filteredEvidence.length === 0 && (
               <div className="text-center py-8 text-muted">
                 <p>No evidence found</p>
                 <p className="text-sm mt-1">Try different filters</p>
               </div>
             )}
             </div>
           )}
        </div>
        
        {/* Evidence Detail */}
        <div className="w-2/3 pl-4 overflow-y-auto">
          {selectedEvidence ? (
            <div className="h-full">
              <div className="mb-4">
                <div className="flex justify-between items-start">
                  <h3 className="text-lg font-semibold">{selectedEvidence.source}</h3>
                  <span className={`px-3 py-1 rounded-full text-sm ${getSourceTypeColor(selectedEvidence.source_type)}`}>
                    {selectedEvidence.source_type.replace('_', ' ')}
                  </span>
                </div>
                
                <div className="flex space-x-4 mt-2 text-sm">
                  <div>
                    <span className="text-muted">Reliability: </span>
                    <span className={getReliabilityColor(selectedEvidence.reliability_score)}>
                      {selectedEvidence.reliability_score}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted">Relevance: </span>
                    <span>{selectedEvidence.relevance_score}%</span>
                  </div>
                  <div>
                    <span className="text-muted">Collected: </span>
                    <span>{new Date(selectedEvidence.collected_at).toLocaleString()}</span>
                  </div>
                </div>
              </div>
              
              <div className="mb-6">
                <h4 className="font-medium mb-2">Summary</h4>
                <p className="text-sm">{selectedEvidence.content.summary || 'No summary available'}</p>
              </div>
              
              <div className="mb-6">
                <h4 className="font-medium mb-2">Content</h4>
                <div className="bg-background p-4 rounded border border-border">
<pre className="whitespace-pre-wrap break-words text-sm">
                     {typeof selectedEvidence.content.data === 'string' 
                       ? selectedEvidence.content.data 
                       : JSON.stringify(selectedEvidence.content.data, null, 2)}
                   </pre>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-6 mb-6">
                <div>
                  <h4 className="font-medium mb-2">Metadata</h4>
                  <div className="bg-background p-4 rounded border border-border text-sm">
                    <div className="mb-2">
                      <span className="font-medium">URL: </span>
                      <a 
                        href={selectedEvidence.metadata.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-primary hover:underline"
                      >
                        {selectedEvidence.metadata.url}
                      </a>
                    </div>
                    <div className="mb-2">
                      <span className="font-medium">Source Agent: </span>
                      {selectedEvidence.metadata.source_agent}
                    </div>
                    <div className="mb-2">
                      <span className="font-medium">Collection Method: </span>
                      {selectedEvidence.metadata.collection_method}
                    </div>
                    <div>
                      <span className="font-medium">Collected At: </span>
                      {new Date(selectedEvidence.metadata.timestamp).toLocaleString()}
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-2">Classification & Tags</h4>
                  <div className="bg-background p-4 rounded border border-border text-sm">
                    <div className="mb-2">
                      <span className="font-medium">Classification: </span>
                      <span className="ml-2 px-2 py-0.5 bg-secondary rounded">
                        {selectedEvidence.classification}
                      </span>
                    </div>
                    <div className="mb-2">
                      <span className="font-medium">Data Type: </span>
                      {selectedEvidence.data_type}
                    </div>
                    <div>
                      <span className="font-medium">Tags: </span>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {selectedEvidence.tags.map((tag, index) => (
                          <span key={index} className="px-2 py-0.5 bg-secondary rounded text-xs">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              {selectedEvidence.related_evidence.length > 0 && (
                <div className="mb-6">
                  <h4 className="font-medium mb-2">Related Evidence</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedEvidence.related_evidence.map((id, index) => (
                      <span key={index} className="px-3 py-1 bg-secondary rounded-full text-sm">
                        {id}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center text-muted">
                <div className="text-4xl mb-2">📋</div>
                <p>Select evidence to view details</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EvidenceViewer;