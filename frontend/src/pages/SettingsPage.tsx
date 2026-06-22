import React, { useState } from 'react';
import { RefreshCw, Palette, Bell, Shield, Database, Home } from 'lucide-react';
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
    { id: 'data', label: 'Data & sync', icon: <Database size={16} /> },
    { id: 'security', label: 'Security', icon: <Shield size={16} /> },
  ];

  return (
    <>
      <header className="pin-hero animate-fade-in">
        <div>
          <div className="pin-hero-eyebrow">
            <Home size={14} />
            Your nook
          </div>
          <h1>Make it feel like home</h1>
          <p className="pin-hero-desc">
            Tune the look, alerts, and connections — so the workspace matches how you like to work.
          </p>
        </div>
        <Button variant="ghost" size="sm" icon={<RefreshCw size={14} />} onClick={() => refetch()}>
          Reload
        </Button>
      </header>

      <div className="animate-fade-in">
        {isLoading ? (
          <LoadingState message="Loading your preferences…" />
        ) : isError ? (
          <ErrorState
            message={error instanceof Error ? error.message : 'Error fetching settings'}
            onRetry={() => refetch()}
          />
        ) : (
          <div className="settings-nook">
            <nav className="settings-nook-nav">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  className={`settings-nook-tab ${activeTab === tab.id ? 'active' : ''}`}
                  onClick={() => setActiveTab(tab.id)}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </nav>

            <div className="settings-nook-panel">
              {activeTab === 'appearance' && (
                <>
                  <div className="settings-nook-intro">
                    <h2>Appearance</h2>
                    <p>Warm daylight or soft evening — pick what feels right.</p>
                  </div>

                  <Card padding="lg" className="pin-card">
                    <h3 className="card-title" style={{ marginBottom: 'var(--space-2)' }}>
                      Color mode
                    </h3>
                    <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-muted)', marginBottom: 'var(--space-4)' }}>
                      Switch between light and dark themes
                    </p>

                    <div className="theme-preview theme-preview--cozy">
                      <button
                        type="button"
                        className={`theme-preview-card theme-preview-dark ${theme === 'dark' ? 'selected' : ''}`}
                        onClick={() => setTheme('dark')}
                      >
                        <div className="theme-preview-label">Evening</div>
                        <div className="theme-preview-swatches">
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-bush-deep)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--cozy-rose)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--cozy-sage)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--calm-cashmere)' }} />
                        </div>
                      </button>
                      <button
                        type="button"
                        className={`theme-preview-card theme-preview-light ${theme === 'light' ? 'selected' : ''}`}
                        onClick={() => setTheme('light')}
                      >
                        <div className="theme-preview-label">Daylight</div>
                        <div className="theme-preview-swatches">
                          <div className="theme-preview-swatch" style={{ background: 'var(--cozy-linen)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--cozy-blush)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--cozy-rose)' }} />
                          <div className="theme-preview-swatch" style={{ background: 'var(--cozy-sage)' }} />
                        </div>
                      </button>
                    </div>

                    <div style={{ marginTop: 'var(--space-6)' }}>
                      <Toggle
                        checked={theme === 'dark'}
                        onChange={(checked) => setTheme(checked ? 'dark' : 'light')}
                        label="Evening mode"
                        description="Softer contrast for late-night sessions"
                      />
                    </div>
                  </Card>

                  <Card padding="lg" className="pin-card">
                    <h3 className="card-title" style={{ marginBottom: 'var(--space-4)' }}>
                      Typography
                    </h3>
                    <div className="settings-row">
                      <span className="settings-row-label">Display</span>
                      <span className="settings-row-value">Newsreader</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Body</span>
                      <span className="settings-row-value">Inter</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Style</span>
                      <span className="settings-row-value">Stone minimal</span>
                    </div>
                  </Card>
                </>
              )}

              {activeTab === 'notifications' && (
                <>
                  <div className="settings-nook-intro">
                    <h2>Notifications</h2>
                    <p>Choose how we reach you when something needs attention.</p>
                  </div>
                  <Card padding="lg" className="pin-card">
                    <Toggle
                      checked={notifications}
                      onChange={setNotifications}
                      label="Push notifications"
                      description="Real-time alerts for critical anomalies"
                    />
                    <Toggle
                      checked={anomalyAlerts}
                      onChange={setAnomalyAlerts}
                      label="Anomaly alerts"
                      description="Notify when high-severity issues appear"
                    />
                    <Toggle
                      checked={emailDigest}
                      onChange={setEmailDigest}
                      label="Weekly digest"
                      description="A Monday summary of the week&apos;s metrics"
                    />
                  </Card>
                </>
              )}

              {activeTab === 'data' && (
                <>
                  <div className="settings-nook-intro">
                    <h2>Data & sync</h2>
                    <p>Where your numbers come from and when they last updated.</p>
                  </div>
                  <Card padding="lg" className="pin-card">
                    <div className="settings-row">
                      <span className="settings-row-label">Data source</span>
                      <span className="settings-row-value">PostgreSQL / Neon</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Last sync</span>
                      <span className="settings-row-value">On demand</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Theme (API)</span>
                      <span className="settings-row-value">{settings?.theme ?? theme}</span>
                    </div>
                  </Card>
                </>
              )}

              {activeTab === 'security' && (
                <>
                  <div className="settings-nook-intro">
                    <h2>Security</h2>
                    <p>Access and session settings for your account.</p>
                  </div>
                  <Card padding="lg" className="pin-card">
                    <div className="settings-row">
                      <span className="settings-row-label">API authentication</span>
                      <span className="settings-row-value">Bearer token</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Session timeout</span>
                      <span className="settings-row-value">24 hours</span>
                    </div>
                    <div className="settings-row">
                      <span className="settings-row-label">Two-factor auth</span>
                      <span className="settings-row-value">Not set up</span>
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
