import React from 'react';
import Button from '../Common/Button';

interface QuickActionsProps {
  onAction: (action: string) => void;
  actions: string[];
  disabled?: boolean;
}

const QuickActions: React.FC<QuickActionsProps> = ({ 
  onAction, 
  actions,
  disabled = false
}) => {
  return (
    <div className="border-t border-border p-4 bg-secondary">
      <div className="flex flex-wrap gap-2">
        {actions.map((action, index) => (
          <Button
            key={index}
            variant="secondary"
            size="sm"
            onClick={() => onAction(action)}
            disabled={disabled}
          >
            {action}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default QuickActions;