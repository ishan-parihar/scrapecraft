import React, { useState, useEffect, useRef } from 'react';
import { useChatStore } from '../../../store/chatStore';
import { useWebSocketStore } from '../../../store/websocketStore';
import { ChatMessage } from '../../../types';
import MessageList from '../../Chat/MessageList';
import InputArea from '../../Chat/InputArea';
import QuickActions from '../../Chat/QuickActions';

interface InvestigationPlannerProps {
  investigationId: string;
}

const InvestigationPlanner: React.FC<InvestigationPlannerProps> = ({ investigationId }) => {
  const { messages, addMessage, clearMessages } = useChatStore();
  const { ws, send } = useWebSocketStore();
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
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

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

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
      // In a real implementation, this would send to the backend
      // For now, we'll simulate a response
       setTimeout(() => {
         const assistantMessage: ChatMessage = {
           id: `msg_${Date.now() + 1}`,
           role: 'assistant',
           content: `I understand you want to plan an investigation. I can help with defining targets, collection requirements, and agent assignments. For your query: "${input}", I recommend starting with target identification and intelligence requirements gathering.`,
           timestamp: new Date().toISOString(),
           investigation_id: investigationId,
           message_type: 'planning',
           metadata: {
             classification: 'UNCLASSIFIED',
             toolsUsed: ['planning_agent'],
             executionTime: 1200
           }
         };
         
         addMessage(assistantMessage);
         setIsLoading(false);
       }, 1000);
    } catch (error) {
      console.error('Failed to send message:', error);
      setIsLoading(false);
    }
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
        <div className="flex items-center">
          <div className="w-3 h-3 rounded-full bg-success mr-2 animate-pulse"></div>
          <h3 className="font-semibold">Investigation Planner</h3>
          <span className="ml-2 text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">
            Active
          </span>
        </div>
        <p className="text-sm text-muted mt-1">
          Plan your investigation, define targets, and coordinate agents
        </p>
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