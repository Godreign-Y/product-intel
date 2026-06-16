import React from 'react';
import { RefreshCw, AlertTriangle } from 'lucide-react';

interface LoadingProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingProps> = ({ message = 'Loading...' }) => (
  <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>
    <RefreshCw size={24} className="spin" style={{ marginBottom: '12px', display: 'inline-block' }} />
    <p>{message}</p>
  </div>
);

interface ErrorProps {
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorProps> = ({ message = 'An error occurred while fetching data.', onRetry }) => (
  <div style={{ textAlign: 'center', padding: '40px', backgroundColor: 'rgba(239, 68, 68, 0.05)', border: '1px solid var(--danger)', borderRadius: '12px', margin: '20px 0' }}>
    <AlertTriangle size={32} color="var(--danger)" style={{ marginBottom: '12px', display: 'inline-block' }} />
    <h3 style={{ color: 'var(--danger)', marginBottom: '8px' }}>Data Fetch Failed</h3>
    <p style={{ color: 'var(--text-secondary)', marginBottom: '20px' }}>{message}</p>
    {onRetry && (
      <button 
        onClick={onRetry}
        className="nav-button"
        style={{ margin: '0 auto', border: '1px solid var(--border-color)' }}
      >
        <RefreshCw size={14} style={{ marginRight: '6px' }} /> Retry Request
      </button>
    )}
  </div>
);
