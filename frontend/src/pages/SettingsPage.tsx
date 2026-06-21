import React, { useState } from 'react';
import { RefreshCw, Palette, Bell, Shield, Database } from 'lucide-react';
import { useSettings } from '../hooks/useSettings';
import { LoadingState, ErrorState } from '../components/LoadingErrorState';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Toggle } from '../components/ui/Badge';
import { useTheme } from '../context/ThemeContext';

type SettingsTab = 'appearance' | 'notifications' | 'data' | 'security';

export default function SettingsPage() {
  const { data: settings, isLoading, isError, error, refetch } = useSettings();
  const { theme, setTheme } = useTheme();
  const [activeTab, setActiveTab] = useState<SettingsTab>('appearance');
  const [notifications, setNotifications] = useState(true);
  const [emailDigest, setEmailDigest] = useState(false);
  const [anomalyAlerts, setAnomalyAlerts] = useState(true);

  const tabs: { id: SettingsTab; label: string; icon: React.ReactNode }[] = [
    { id: 'appearance', label: 'Appearance', icon: <Palette size={16} /> },
    { id: 'notifications', label: 'Notifications', icon: <Bell size={16} /> },
    { id: 'data', label: 'Data & Sync', icon: <Database size={16} /> },
    { id: 'security', label: 'Security', icon: <Shield size={16} /> },
  ];

  return (
    <>
      <header className="page-header">
        <div className="page-header-text">
          <h1>Settings</h1>
          <p>Configure appearance, notifications, and platform preferences</p>
        </div>
        <div className="page-header-actions">
          <Button
            variant="ghost"
            size="sm"
            icon={<RefreshCw size={14} />}
            onClick={() => refetch()}
          >
            Reload
          </Button>
        </div>
      </header>

      <div className="animate-fade-in">
        {isLoading ? (
          <LoadingState message="Loading preferences..." />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'Error fetching settings'}
            onRetry={() => refetch()}
          />
        ) : (
          <div className="settings-layout">
            <nav className="settings-nav">
              {tabs.map(tab => (
                <button
                  key={tab.id}
                  className={`settings-nav-item ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                  style={{ display: 'flex', alignItems: 'center', gap: 10 }}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </nav>

            <div className="settings-section">
              {activeTab === 'appearance' && (
                <>
                  <div>
                    <h2 className="settings-group-title">Appearance</h2>
                    <p className="settings-group-desc">
                      Customize the visual experience. The Calm palette adapts seamlessly across modes.
                    </p>
                  </div>

                  <Card padding="lg">
                    <h3 className="card-title" style={{ marginBottom: 'var(--space-2)' }}>
                      Color Mode
                    </h3>
                    <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
                      Choose between light and dark themes
                    </p>

                    <div className="theme-preview">
                      <button
                        className={`theme-preview-card theme-preview-dark ${theme === 'dark' ? 'selected' : ''}`}
                        onClick={() => setTheme('dark')}
                        type="button"
                      >
                        <div className="theme-preview-label">Dark</div>
                        <div className="theme-preview-swatches">
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-bush-deep)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-bush)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-sienna)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-cashmere)' }} />
                        </div>
                      </button>
                      <button
                        className={`theme-preview-card theme-preview-light ${theme === 'light' ? 'selected' : ''}`}
                        onClick={() => setTheme('light')}
                        type="button"
                      >
                        <div className="theme-preview-label">Light</div>
                        <div className="theme-preview-swatches">
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-cashmere-light-mode)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-oak-light-mode)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-sienna)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-bush)' }} />
                        </div>
                      </button>
                    </div>

                    <div style={{ marginTop: 'var(--space-6)' }}>
                      <Toggle
                        checked={theme === 'dark'}
                        onChange={checked => setTheme(checked ? 'dark' : 'light')}
                        label="Dark mode"
                        description="Use charcoal and bush tones for reduced eye strain"
                      />
                    </div>
                  </Card>

                  <Card padding="lg">
                    <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
                      Typography
                    </h3>
                    <div className="settings-row">
                      <span className="settings-row-label">Typeface</span>
                      <span className="settings-row-value">IBM Plex Sans</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Style</span>
                      <span className="settings-row-value">Single-family, weight-based hierarchy</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Design System</span>
                      <span className="settings-row-value">Calm v1.0</span>
                    </div>
                  </Card>
                </>
              )}

              {activeTab === 'notifications' && (
                <>
                  <div>
                    <h2 className="settings-group-title">Notifications</h2>
                    <p className="settings-group-desc">Manage how you receive alerts and updates</p>
                  </div>
                  <Card padding="lg">
                    <Toggle
                      checked={notifications}
                      onChange={setNotifications}
                      label="Push notifications"
                      description="Receive real-time alerts for critical anomalies"
                    />
                    <Toggle
                      checked={anomalyAlerts}
                      onChange={setAnomalyAlerts}
                      label="Anomaly alerts"
                      description="Get notified when high-severity anomalies are detected"
                    />
                    <Toggle
                      checked={emailDigest}
                      onChange={setEmailDigest}
                      label="Weekly email digest"
                      description="Summary of performance metrics every Monday"
                    />
                  </Card>
                </>
              )}

              {activeTab === 'data' && (
                <>
                  <div>
                    <h2 className="settings-group-title">Data & Sync</h2>
                    <p className="settings-group-desc">Database connections and data refresh settings</p>
                  </div>
                  <Card padding="lg">
                    <div className="settings-row">
                      <span className="settings-row-label">Data Source</span>
                      <span className="settings-row-value">PostgreSQL / Neon</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Last Sync</span>
                      <span className="settings-row-value">Auto (on demand)</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Current Theme (API)</span>
                      <span className="settings-row-value">{settings?.theme ?? theme}</span>
                    </div>
                  </Card>
                </>
              )}

              {activeTab === 'security' && (
                <>
                  <div>
                    <h2 className="settings-group-title">Security</h2>
                    <p className="settings-group-desc">Access control and session management</p>
                  </div>
                  <Card padding="lg">
                    <div className="settings-row">
                      <span className="settings-row-label">API Authentication</span>
                      <span className="settings-row-value">Bearer Token</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Session Timeout</span>
                      <span className="settings-row-value">24 hours</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Two-Factor Auth</span>
                      <span className="settings-row-value">Not configured</span>
                    </div>
                  </Card>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
