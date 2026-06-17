import React from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';
import { Button } from './ui/Button';

interface LoadingProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingProps> = ({ message = 'Loading...' }) => (
  <div className="loading-state animate-fade-in">
    <RefreshCw size={28} className="spin loading-state-icon" />
    <p className="loading-state-text">{message}</p>
  </div>
);

interface ErrorProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorProps> = ({
  message = 'An error occurred while fetching data.',
  onRetry,
}) => (
  <div className="error-state animate-fade-in-scale">
    <AlertTriangle size={36} color="var(--danger)" style={{ marginBottom: 'var(--space-3)' }} />
    <h3>Unable to Load Data</h3>
    <p>{message}</p>
    {onRetry && (
      <Button variant="secondary" size="sm" icon={<RefreshCw size={14} />} onClick={onRetry}>
        Retry Request
      </Button>
    )}
  </div>
);
