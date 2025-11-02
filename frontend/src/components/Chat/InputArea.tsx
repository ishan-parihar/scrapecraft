import React, { useState, KeyboardEvent } from 'react';
import Button from '../Common/Button';

interface InputAreaProps {
  input: string;
  setInput: (value: string) => void;
  onSend: () => void;
  isLoading: boolean;
  placeholder?: string;
  quickActions?: string[];
  onQuickAction?: (action: string) => void;
}

const InputArea: React.FC<InputAreaProps> = ({ 
  input, 
  setInput, 
  onSend, 
  isLoading, 
  placeholder = "Press Enter to send, Shift+Enter for new line",
  quickActions = [],
  onQuickAction = () => {}
}) => {
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSend();
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="border-t border-border p-4 bg-secondary">
      {quickActions.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-3">
          {quickActions.map((action, index) => (
            <Button
              key={index}
              variant="secondary"
              size="sm"
              onClick={() => onQuickAction(action)}
              disabled={isLoading}
            >
              {action}
            </Button>
          ))}
        </div>
      )}
      
      <form onSubmit={handleSubmit}>
        <div className="flex space-x-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="input flex-1 resize-none bg-background"
            rows={3}
            disabled={isLoading}
          />
          
          <Button
            type="submit"
            variant="primary"
            disabled={!input.trim() || isLoading}
          >
            Send
          </Button>
        </div>
      </form>
    </div>
  );
};

export default InputArea;