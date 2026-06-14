import React, { useState, useEffect } from 'react';
import {
  User,
  Bell,
  Sun,
  Database,
  Cpu,
  Sliders,
  CheckCircle,
  RefreshCw,
  Plus,
  X,
} from 'lucide-react';
import { useSettings } from '../hooks/useSettings';
import { SystemSettings } from '../types/settings';

export default function SettingsPage() {
  const {
    settings,
    isLoading,
    isSaving,
    testStatus,
    saveSettings,
    testConnection,
  } = useSettings();

  const [form, setForm] = useState<SystemSettings | null>(null);
  const [activeTab, setActiveTab] = useState<'profile' | 'notifications' | 'theme' | 'data' | 'api' | 'model'>('profile');
  
  // Custom states for missing fields
  const [profile, setProfile] = useState({
    name: 'Aarav R.',
    email: 'aarav.r@intelligenceos.com',
    role: 'Product Lead',
  });
  const [notifications, setNotifications] = useState({
    anomalies: true,
    recommendations: true,
    digests: false,
  });
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [newSource, setNewSource] = useState('');

  useEffect(() => {
    if (settings) {
      setForm(settings);
    }
  }, [settings]);

  if (isLoading || !form) {
    return (
      <div className="space-y-6">
        <div className="h-10 bg-slate-100 rounded-lg animate-pulse w-full max-w-sm" />
        <div className="h-96 bg-white rounded-xl border border-slate-100 p-5 shadow-sm animate-pulse" />
      </div>
    );
  }

  const handleToggleFastApi = () => {
    setForm({
      ...form,
      enableFastApi: !form.enableFastApi,
    });
  };

  const handleFieldChange = (field: keyof SystemSettings, val: any) => {
    setForm({
      ...form,
      [field]: val,
    });
  };

  const handleAddDataSource = () => {
    if (!newSource.trim()) return;
    if (form.selectedDataSources.includes(newSource.trim())) return;

    setForm({
      ...form,
      selectedDataSources: [...form.selectedDataSources, newSource.trim()],
    });
    setNewSource('');
  };

  const handleRemoveDataSource = (name: string) => {
    setForm({
      ...form,
      selectedDataSources: form.selectedDataSources.filter((s) => s !== name),
    });
  };

  const handleSaveAll = (e: React.FormEvent) => {
    e.preventDefault();
    saveSettings(form);
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl">
      <div>
        <h1 className="text-2xl font-extrabold text-[#111827] tracking-tight">Settings</h1>
        <p className="text-xs text-[#6B7280] mt-1">Configure profile preferences, system modules, and active data streams</p>
      </div>

      {/* Tabs Navigation */}
      <div className="flex border-b border-[#E5E7EB] pb-px overflow-x-auto gap-2 scrollbar-none">
        {[
          { id: 'profile', label: 'Profile', icon: User },
          { id: 'notifications', label: 'Notifications', icon: Bell },
          { id: 'theme', label: 'Theme', icon: Sun },
          { id: 'data', label: 'Data Connections', icon: Database },
          { id: 'api', label: 'API Integrations', icon: Cpu },
          { id: 'model', label: 'Model Settings', icon: Sliders },
        ].map((t) => {
          const Icon = t.icon;
          return (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTab(t.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer whitespace-nowrap ${
                activeTab === t.id
                  ? 'border-[#7C3AED] text-[#7C3AED]'
                  : 'border-transparent text-[#6B7280] hover:text-[#111827]'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {t.label}
            </button>
          );
        })}
      </div>

      {/* Active Tab Content Card */}
      <div className="bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm min-h-[300px] flex flex-col justify-between">
        <form onSubmit={handleSaveAll} className="space-y-6">
          
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <div className="space-y-5">
              <div className="border-b border-slate-50 pb-3">
                <h3 className="text-sm font-bold text-[#111827]">User Profile</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Manage your personal identification details</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#6B7280] uppercase block mb-1">Full Name</label>
                  <input
                    type="text"
                    value={profile.name}
                    onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                    className="w-full h-[44px] px-3 border border-[#E5E7EB] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED] focus:ring-2 focus:ring-[#F3E8FF]"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-[#6B7280] uppercase block mb-1">Email Address</label>
                  <input
                    type="email"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    className="w-full h-[44px] px-3 border border-[#E5E7EB] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED] focus:ring-2 focus:ring-[#F3E8FF]"
                  />
                </div>
                <div>
                  <label className="text-[10px] font-bold text-[#6B7280] uppercase block mb-1">Job Title</label>
                  <input
                    type="text"
                    value={profile.role}
                    onChange={(e) => setProfile({ ...profile, role: e.target.value })}
                    className="w-full h-[44px] px-3 border border-[#E5E7EB] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED] focus:ring-2 focus:ring-[#F3E8FF]"
                  />
                </div>
              </div>
            </div>
          )}

          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <div className="space-y-5">
              <div className="border-b border-slate-50 pb-3">
                <h3 className="text-sm font-bold text-[#111827]">Notifications Preferences</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Toggle alert preferences and digest scopes</p>
              </div>

              <div className="space-y-3">
                {[
                  { id: 'anomalies', label: 'Anomaly & Volatility Alerts', desc: 'Real-time notifications when major metric spikes or drops are processed.' },
                  { id: 'recommendations', label: 'AI Growth Opportunities', desc: 'Weekly digests containing recommended items matching priority criteria.' },
                  { id: 'digests', label: 'Weekly Summary Email', desc: 'Receive aggregated metrics reports directly in your inbox.' },
                ].map((n) => (
                  <div key={n.id} className="flex justify-between items-center p-3 border border-[#E5E7EB] rounded-xl bg-slate-50/50">
                    <div>
                      <span className="text-xs font-bold text-[#111827]">{n.label}</span>
                      <p className="text-[10px] text-[#6B7280] mt-0.5">{n.desc}</p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setNotifications({ ...notifications, [n.id]: !notifications[n.id as keyof typeof notifications] })}
                      className={`w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors duration-200 focus:outline-none ${
                        notifications[n.id as keyof typeof notifications] ? 'bg-[#7C3AED]' : 'bg-slate-200'
                      }`}
                    >
                      <div className={`bg-white w-4 h-4 rounded-full shadow transform transition-transform ${
                        notifications[n.id as keyof typeof notifications] ? 'translate-x-5' : 'translate-x-0'
                      }`} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Theme Tab */}
          {activeTab === 'theme' && (
            <div className="space-y-5">
              <div className="border-b border-slate-50 pb-3">
                <h3 className="text-sm font-bold text-[#111827]">Visual Theme</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Toggle theme preferences for the user interface</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div
                  onClick={() => setTheme('light')}
                  className={`p-4 border rounded-[20px] cursor-pointer hover:border-purple-200 transition-all ${
                    theme === 'light' ? 'border-[#7C3AED] bg-purple-50/20 shadow-sm' : 'border-[#E5E7EB]'
                  }`}
                >
                  <div className="w-8 h-8 rounded-lg bg-amber-50 text-[#F59E0B] flex items-center justify-center mb-3">
                    <Sun className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-[#111827]">Light Mode</span>
                  <p className="text-[10px] text-[#6B7280] mt-0.5">Clean white interface themed workspace</p>
                </div>

                <div
                  onClick={() => setTheme('dark')}
                  className={`p-4 border rounded-[20px] cursor-pointer hover:border-purple-200 transition-all opacity-75 ${
                    theme === 'dark' ? 'border-[#7C3AED] bg-purple-50/20 shadow-sm' : 'border-[#E5E7EB]'
                  }`}
                >
                  <div className="w-8 h-8 rounded-lg bg-slate-900 text-white flex items-center justify-center mb-3">
                    <Sun className="w-4 h-4" />
                  </div>
                  <span className="text-xs font-bold text-[#111827]">Dark Mode (Coming Soon)</span>
                  <p className="text-[10px] text-[#6B7280] mt-0.5">Midnight charcoal dark layout</p>
                </div>
              </div>
            </div>
          )}

          {/* Data Connections Tab */}
          {activeTab === 'data' && (
            <div className="space-y-5">
              <div className="border-b border-slate-50 pb-3">
                <h3 className="text-sm font-bold text-[#111827]">Active Data Connections</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Data repositories sync checklist</p>
              </div>

              <div className="flex flex-wrap gap-2">
                {form.selectedDataSources.map((source) => (
                  <div key={source} className="flex items-center gap-1.5 text-xs bg-purple-50 text-[#7C3AED] border border-purple-100 px-3 py-1.5 rounded-xl font-bold">
                    <span>{source}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveDataSource(source)}
                      className="text-purple-400 hover:text-purple-600 cursor-pointer"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 max-w-md">
                <input
                  type="text"
                  placeholder="e.g. GA4, Snowflake, Mixpanel"
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  className="flex-grow h-[44px] px-3.5 border border-[#E5E7EB] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED]"
                />
                <button
                  type="button"
                  onClick={handleAddDataSource}
                  className="px-4 bg-[#7C3AED] hover:bg-[#6D28D9] text-white rounded-[12px] text-xs font-bold cursor-pointer transition-colors"
                >
                  Add Source
                </button>
              </div>
            </div>
          )}

          {/* API Integrations Tab */}
          {activeTab === 'api' && (
            <div className="space-y-5">
              <div className="border-b border-slate-50 pb-3">
                <h3 className="text-sm font-bold text-[#111827]">API Integrations Settings</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Toggle between static mock data and live FastAPI backend</p>
              </div>

              {/* Toggle switch */}
              <div className="flex justify-between items-center bg-slate-50/50 p-4 rounded-xl border border-slate-50">
                <div>
                  <span className="text-xs font-bold text-[#111827]">Enable FastAPI Integration Mode</span>
                  <p className="text-[10px] text-[#6B7280] mt-0.5">Redirect queries to a local or production FastAPI endpoint</p>
                </div>
                <button
                  type="button"
                  onClick={handleToggleFastApi}
                  className={`w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors duration-200 focus:outline-none ${
                    form.enableFastApi ? 'bg-[#7C3AED]' : 'bg-slate-200'
                  }`}
                >
                  <div
                    className={`bg-white w-4 h-4 rounded-full shadow transform transition-transform duration-200 ${
                      form.enableFastApi ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </button>
              </div>

              {/* Input parameters */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-[10px] font-bold text-[#6B7280] uppercase block mb-1">
                    FastAPI Base URL
                  </label>
                  <input
                    type="url"
                    placeholder="http://localhost:8000"
                    value={form.fastapiUrl}
                    onChange={(e) => handleFieldChange('fastapiUrl', e.target.value)}
                    disabled={!form.enableFastApi}
                    className="w-full h-[44px] px-3.5 border border-[#E5E7EB] disabled:bg-slate-50/50 disabled:text-[#9CA3AF] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED]"
                  />
                </div>

                <div>
                  <label className="text-[10px] font-bold text-[#6B7280] uppercase block mb-1">
                    API Auth Token
                  </label>
                  <input
                    type="password"
                    placeholder="pi_live_..."
                    value={form.apiKey}
                    onChange={(e) => handleFieldChange('apiKey', e.target.value)}
                    disabled={!form.enableFastApi}
                    className="w-full h-[44px] px-3.5 border border-[#E5E7EB] disabled:bg-slate-50/50 disabled:text-[#9CA3AF] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED]"
                  />
                </div>
              </div>

              {/* Testing Connection */}
              {form.enableFastApi && (
                <div className="flex justify-between items-center p-3 border border-slate-100 rounded-xl bg-slate-50/30">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-bold text-[#9CA3AF]">Health Check:</span>
                    {testStatus === 'Connected' ? (
                      <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-100">
                        Connected
                      </span>
                    ) : testStatus === 'Disconnected' ? (
                      <span className="text-[10px] font-bold text-rose-600 bg-rose-50 px-2 py-0.5 rounded-full border border-rose-100">
                        Disconnected
                      </span>
                    ) : testStatus === 'testing' ? (
                      <span className="text-[10px] font-bold text-slate-500 bg-slate-50 px-2 py-0.5 rounded-full">
                        Verifying...
                      </span>
                    ) : (
                      <span className="text-[10px] font-bold text-slate-400">Not Tested</span>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => testConnection(form.fastapiUrl, form.apiKey)}
                    disabled={testStatus === 'testing'}
                    className="h-8 px-3.5 bg-white border border-[#E5E7EB] hover:bg-slate-50 text-[#111827] text-[10px] font-bold rounded-lg cursor-pointer transition-colors"
                  >
                    Test Connection
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Model Settings Tab */}
          {activeTab === 'model' && (
            <div className="space-y-5">
              <div className="border-b border-slate-50 pb-3">
                <h3 className="text-sm font-bold text-[#111827]">Model Configuration</h3>
                <p className="text-xs text-[#6B7280] mt-0.5">Control mock network delay values and ML training confidence ranges</p>
              </div>

              {/* Latency slider */}
              <div>
                <div className="flex justify-between items-center mb-2">
                  <label className="text-[10px] font-bold text-[#6B7280] uppercase tracking-wider">
                    Simulated Network Latency (Delay)
                  </label>
                  <span className="text-xs font-bold text-[#7C3AED]">{form.mockDelay} ms</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="3000"
                  step="100"
                  value={form.mockDelay}
                  onChange={(e) => handleFieldChange('mockDelay', parseInt(e.target.value))}
                  className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-[#7C3AED]"
                />
              </div>

              {/* Confidence Interval range */}
              <div className="max-w-xs">
                <label className="text-[10px] font-bold text-[#6B7280] uppercase block mb-1">Default Confidence Bands</label>
                <select className="w-full h-[44px] px-3 border border-[#E5E7EB] rounded-[12px] text-xs font-semibold focus:outline-none focus:border-[#7C3AED] bg-white">
                  <option>95% Confidence Interval</option>
                  <option>90% Confidence Interval</option>
                  <option>99% Confidence Interval</option>
                </select>
              </div>
            </div>
          )}

          {/* Save panel */}
          <div className="flex justify-end pt-4 border-t border-slate-50 mt-6">
            <button
              type="submit"
              disabled={isSaving}
              className="h-[44px] px-6 bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-400 text-white rounded-[12px] text-xs font-bold transition-all shadow-sm flex items-center gap-1.5 cursor-pointer"
            >
              {isSaving ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <CheckCircle className="w-4 h-4" /> Save Configurations
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
