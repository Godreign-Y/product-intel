import React from 'react';
import { Settings, RefreshCw } from 'lucide-react';
import { useSettings } from '../hooks/useSettings';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';

export default function SettingsPage() {
  const { data: settings, isLoading, isError, error, refetch } = useSettings();

  return (
    <>
      <div className="header">
        <div>
          <h1>Platform Settings</h1>
          <p>Configure dashboard preferences and integrations</p>
        </div>
        <button onClick={() => refetch()} className="filter-select" style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
          <RefreshCw size={14} /> Reload
        </button>
      </div>
      
      <div className="animate-fade-in" style={{ padding: '20px', textAlign: 'center', marginTop: '60px' }}>
        {isLoading ? (
          <LoadingState message="Loading preferences..." />
        ) : isError ? (
          <ErrorState message={error instanceof Error ? error.message : 'Error fetching settings'} onRetry={() => refetch()} />
        ) : (
          <>
            <Settings size={48} style={{ color: 'var(--text-muted)', marginBottom: '16px' }} />
            <h3 style={{ color: 'var(--text-secondary)' }}>Settings Configuration</h3>
            <p style={{ color: 'var(--text-muted)' }}>
              This section is currently under development.<br/>
              <span style={{ fontSize: '12px', marginTop: '8px', display: 'block' }}>Current Theme: {settings?.theme}</span>
            </p>
          </>
        )}
      </div>
    </>
  );
}
