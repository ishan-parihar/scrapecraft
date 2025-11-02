import React from 'react';
import clsx from 'clsx';

interface ClassificationBannerProps {
  classification: 'UNCLASSIFIED' | 'CONFIDENTIAL' | 'SECRET' | 'TOP_SECRET';
  compact?: boolean;
}

const ClassificationBanner: React.FC<ClassificationBannerProps> = ({ 
  classification, 
  compact = false 
}) => {
  const getClassificationStyles = () => {
    switch (classification) {
      case 'TOP_SECRET':
        return {
          bg: 'bg-red-900/90',
          text: 'text-red-100',
          border: 'border-red-700',
          label: 'TOP SECRET'
        };
      case 'SECRET':
        return {
          bg: 'bg-red-800/80',
          text: 'text-red-50',
          border: 'border-red-600',
          label: 'SECRET'
        };
      case 'CONFIDENTIAL':
        return {
          bg: 'bg-blue-800/80',
          text: 'text-blue-50',
          border: 'border-blue-600',
          label: 'CONFIDENTIAL'
        };
      case 'UNCLASSIFIED':
      default:
        return {
          bg: 'bg-green-800/80',
          text: 'text-green-50',
          border: 'border-green-600',
          label: 'UNCLASSIFIED'
        };
    }
  };

  const styles = getClassificationStyles();

  if (compact) {
    return (
      <div className={clsx(
        'px-3 py-1 text-xs font-bold uppercase tracking-wider text-center',
        styles.bg,
        styles.text,
        styles.border,
        'border-t border-b'
      )}>
        {classification}
      </div>
    );
  }

  return (
    <div className={clsx(
      'flex justify-between items-center px-4 py-2 text-sm font-bold uppercase tracking-wider',
      styles.bg,
      styles.text,
      styles.border,
      'border-t border-b'
    )}>
      <span>{classification}</span>
      <span className="text-right">{classification}</span>
    </div>
  );
};

export default ClassificationBanner;