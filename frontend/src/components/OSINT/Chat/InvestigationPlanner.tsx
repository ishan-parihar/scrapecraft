import React, { useState, useEffect, useRef } from 'react';
import { useChatStore } from '../../../store/chatStore';
import { useWebSocketStore } from '../../../store/websocketStore';

import { ChatMessage } from '../../../types';
import { api } from '../../../services/api';
import MessageList from '../../Chat/MessageList';
import InputArea from '../../Chat/InputArea';
import QuickActions from '../../Chat/QuickActions';

interface InvestigationPlannerProps {
  investigationId: string;
}

const InvestigationPlanner: React.FC<InvestigationPlannerProps> = ({ investigationId }) => {
  const { messages, addMessage } = useChatStore();
  const { connect, disconnect, connectionStatus } = useWebSocketStore();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  // Filter messages for the current investigation
  const investigationMessages = messages.filter(
    msg => msg.investigation_id === investigationId
  );

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [investigationMessages]);

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    if (investigationId && investigationId !== 'default') {
      connect(investigationId);
    }
    
    return () => {
      disconnect();
    };
  }, [investigationId, connect, disconnect]);

  // Listen for WebSocket errors
  useEffect(() => {
    const handleWebSocketError = (event: CustomEvent) => {
      console.error('WebSocket error in Investigation Planner:', event.detail);
      setError('Connection error. Using fallback polling for updates.');
    };

    window.addEventListener('websocket-error', handleWebSocketError as EventListener);
    
    return () => {
      window.removeEventListener('websocket-error', handleWebSocketError as EventListener);
    };
  }, []);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    // Clear any previous errors
    setError(null);

    // Add user message
    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input,
      timestamp: new Date().toISOString(),
      investigation_id: investigationId,
      message_type: 'planning',
      metadata: {
        classification: 'UNCLASSIFIED',
        toolsUsed: [],
        executionTime: 0
      }
    };

    addMessage(userMessage);
    setInput('');
    setIsLoading(true);

    try {
      // Make real API call to backend
      const response = await api.post('/ai-investigation/start', {
        target: input,
        objective: 'plan investigation',
        priority: 'medium'
      });

      // Add initial response message
      const initialResponse: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response.data.message || `Investigation started for target: ${input}`,
        timestamp: new Date().toISOString(),
        investigation_id: response.data.investigation_id, // Use the actual investigation ID from response
        message_type: 'planning',
        metadata: {
          classification: 'UNCLASSIFIED',
          toolsUsed: ['planning_agent'],
          executionTime: 0
        }
      };

      addMessage(initialResponse);

      // Connect WebSocket to the actual investigation ID
      connect(response.data.investigation_id);

      // If WebSocket is connected, real-time updates will be handled through WebSocket messages
      // Otherwise, we can poll for status updates
      if (connectionStatus !== 'connected') {
        // Fallback to polling if WebSocket is not available
        pollInvestigationStatus(response.data.investigation_id);
      }

    } catch (apiError: any) {
      console.error('Failed to start investigation:', apiError);
      
      let errorMessage = 'Failed to start investigation. Please try again.';
      
      if (apiError.response?.data?.detail) {
        errorMessage = apiError.response.data.detail;
      } else if (apiError.message) {
        errorMessage = `Network error: ${apiError.message}`;
      }

      setError(errorMessage);

      // Add error message to chat
      const errorResponse: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: `❌ ${errorMessage}`,
        timestamp: new Date().toISOString(),
        investigation_id: investigationId,
        message_type: 'planning',
        metadata: {
          classification: 'UNCLASSIFIED',
          toolsUsed: [],
          executionTime: 0,
          urgency: 'high'
        }
      };

      addMessage(errorResponse);
    } finally {
      setIsLoading(false);
    }
  };

  // Poll investigation status as fallback when WebSocket is not available
  const pollInvestigationStatus = async (investigationId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await api.get(`/ai-investigation/${investigationId}/status`);
        const status = response.data;

        // Add status update message if there are significant changes
        if (status.progress_percentage > 0 && status.progress_percentage % 25 === 0) {
          const statusMessage: ChatMessage = {
            id: `msg_${Date.now()}`,
            role: 'assistant',
            content: `📊 Investigation Progress: ${status.progress_percentage}% - Current phase: ${status.current_phase}`,
            timestamp: new Date().toISOString(),
            investigation_id: investigationId,
            message_type: 'status',
            metadata: {
              classification: 'UNCLASSIFIED',
              toolsUsed: ['status_monitor'],
              executionTime: 0
            }
          };
          addMessage(statusMessage);
        }

        // Stop polling when investigation is completed or failed
        if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
          clearInterval(pollInterval);
          
          if (status.status === 'completed' && status.results) {
            const completionMessage: ChatMessage = {
              id: `msg_${Date.now()}`,
              role: 'assistant',
              content: `✅ Investigation completed successfully! Results: ${JSON.stringify(status.results, null, 2)}`,
              timestamp: new Date().toISOString(),
              investigation_id: investigationId,
              message_type: 'analysis',
              metadata: {
                classification: 'UNCLASSIFIED',
                toolsUsed: ['analysis_agent'],
                executionTime: 0
              }
            };
            addMessage(completionMessage);
          } else if (status.status === 'failed') {
            const failureMessage: ChatMessage = {
              id: `msg_${Date.now()}`,
              role: 'assistant',
              content: `❌ Investigation failed: ${status.errors?.join(', ') || 'Unknown error'}`,
              timestamp: new Date().toISOString(),
              investigation_id: investigationId,
              message_type: 'alert',
              metadata: {
                classification: 'UNCLASSIFIED',
                toolsUsed: [],
                executionTime: 0,
                urgency: 'high'
              }
            };
            addMessage(failureMessage);
          }
        }
      } catch (error) {
        console.error('Failed to poll investigation status:', error);
        clearInterval(pollInterval);
      }
    }, 3000); // Poll every 3 seconds

    // Stop polling after 5 minutes to prevent infinite polling
    setTimeout(() => {
      clearInterval(pollInterval);
    }, 300000);
  };

  const handleQuickAction = (action: string) => {
    setInput(action);
    setTimeout(() => {
      handleSendMessage();
    }, 100);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat Header */}
      <div className="border-b border-border p-4 bg-secondary">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full mr-2 ${
              connectionStatus === 'connected' ? 'bg-success animate-pulse' :
              connectionStatus === 'connecting' ? 'bg-warning animate-pulse' :
              'bg-error'
            }`}></div>
            <h3 className="font-semibold">Investigation Planner</h3>
            <span className={`ml-2 text-xs px-2 py-0.5 rounded ${
              connectionStatus === 'connected' ? 'bg-success/10 text-success' :
              connectionStatus === 'connecting' ? 'bg-warning/10 text-warning' :
              'bg-error/10 text-error'
            }`}>
              {connectionStatus === 'connected' ? 'Connected' :
               connectionStatus === 'connecting' ? 'Connecting...' :
               'Offline'}
            </span>
          </div>
          {isLoading && (
            <div className="flex items-center text-xs text-muted">
              <div className="animate-spin rounded-full h-3 w-3 border-b border-primary mr-1"></div>
              Processing...
            </div>
          )}
        </div>
        <p className="text-sm text-muted mt-1">
          Plan your investigation, define targets, and coordinate agents
        </p>
        {error && (
          <div className="mt-2 p-2 bg-error/10 border border-error/20 rounded text-xs text-error">
            ⚠️ {error}
          </div>
        )}
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <MessageList messages={investigationMessages} />
        <div ref={messagesEndRef} />
      </div>
      
       {/* Quick Actions */}
       <QuickActions 
         onAction={handleQuickAction}
         actions={[
           "Define investigation targets",
           "Set collection requirements",
           "Assign collection agents",
           "Start reconnaissance phase"
         ]}
       />
       
       {/* Input Area */}
       <InputArea 
         input={input}
         setInput={setInput}
         onSend={handleSendMessage}
         isLoading={isLoading}
         placeholder="Plan your investigation..."
         quickActions={[
           "Define investigation targets",
           "Set collection requirements",
           "Assign collection agents",
           "Start reconnaissance phase"
         ]}
         onQuickAction={handleQuickAction}
       />
    </div>
  );
};

export default InvestigationPlanner;