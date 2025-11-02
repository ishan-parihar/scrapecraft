import React from 'react';
import { InvestigationReport } from '../../types/osint';

interface ReportsProps {
  reports: InvestigationReport[];
}

const Reports: React.FC<ReportsProps> = ({ reports }) => {
  const getReportStatusColor = (status: string) => {
    switch (status) {
      case 'DRAFT':
        return 'text-yellow-500';
      case 'PENDING_REVIEW':
        return 'text-blue-500';
      case 'APPROVED':
        return 'text-green-500';
      case 'DISTRIBUTED':
        return 'text-primary';
      default:
        return 'text-gray-500';
    }
  };

  const getClassificationColor = (classification: string) => {
    switch (classification) {
      case 'UNCLASSIFIED':
        return 'text-green-500';
      case 'CONFIDENTIAL':
        return 'text-blue-500';
      case 'SECRET':
        return 'text-red-500';
      default:
        return 'text-gray-500';
    }
  };

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-4">Investigation Reports</h3>
      
      {reports.length === 0 ? (
        <div className="text-center py-8 text-muted">
          <p>No reports generated yet</p>
          <p className="text-sm mt-1">Reports will appear here when generated</p>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <div key={report.id} className="border border-border rounded-lg p-4 bg-secondary">
              <div className="flex justify-between items-start">
                <h4 className="font-medium text-lg">{report.title}</h4>
                <div className="flex space-x-3">
                  <span className={`font-semibold ${getClassificationColor(report.classification)}`}>
                    {report.classification}
                  </span>
                  <span className={`font-semibold ${getReportStatusColor(report.status)}`}>
                    {report.status}
                  </span>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <p className="text-sm text-muted">ID</p>
                  <p className="font-mono text-sm">{report.id}</p>
                </div>
                <div>
                  <p className="text-sm text-muted">Date</p>
                  <p className="font-medium">{new Date(report.created_at).toLocaleDateString()}</p>
                </div>
              </div>
              
              {report.content && (
                <div className="mt-4">
                  <p className="text-sm text-muted">Content Preview</p>
                  <div className="mt-1 p-3 bg-background border border-border rounded text-sm max-h-24 overflow-y-auto">
                    {typeof report.content === 'string' 
                      ? report.content.substring(0, 150) + '...' 
                      : JSON.stringify(report.content).substring(0, 150) + '...'}
                  </div>
                </div>
              )}
              
              <div className="mt-4 flex space-x-3">
                <button className="px-3 py-1 bg-primary text-primary-foreground rounded text-sm hover:bg-primary/90 transition-colors">
                  View Report
                </button>
                <button className="px-3 py-1 bg-secondary text-foreground border border-border rounded text-sm hover:bg-secondary/80 transition-colors">
                  Download
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Reports;