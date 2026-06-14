'use client';

import React, { useState, useEffect } from 'react';
import {
  Database,
  Cpu,
  Save,
  Activity,
  AlertTriangle,
  CheckCircle,
  Network,
  RefreshCw,
} from 'lucide-react';
import { useSettings } from '../../hooks/useSettings';
import { SystemSettings } from '../../types/settings';

export default function SettingsPage() {
  const {
    settings,
    isLoading,
    isSaving,
    testStatus,
    saveSettings,
    testConnection,
  } = useSettings();

  // Local form states
  const [enableFastApi, setEnableFastApi] = useState(false);
  const [fastapiUrl, setFastapiUrl] = useState('');
  const [apiKey, setApiKey] = useState('');
  const [mockDelay, setMockDelay] = useState(800);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);

  // Sync settings when loaded
  useEffect(() => {
    if (settings) {
      setEnableFastApi(settings.enableFastApi);
      setFastapiUrl(settings.fastapiUrl);
      setApiKey(settings.apiKey);
      setMockDelay(settings.mockDelay);
      setSelectedSources(settings.selectedDataSources);
    }
  }, [settings]);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;

    const updated: SystemSettings = {
      ...settings,
      enableFastApi,
      fastapiUrl,
      apiKey,
      mockDelay,
      selectedDataSources: selectedSources,
    };
    saveSettings(updated);
  };

  const handleTestConnection = () => {
    testConnection(fastapiUrl, apiKey);
  };

  const toggleSource = (sourceName: string) => {
    if (selectedSources.includes(sourceName)) {
      setSelectedSources(selectedSources.filter((s) => s !== sourceName));
    } else {
      setSelectedSources([...selectedSources, sourceName]);
    }
  };

  if (isLoading || !settings) {
    return (
      <div className="space-y-6">
        <div className="h-48 bg-white border border-slate-100 rounded-xl animate-pulse shadow-sm" />
        <div className="h-48 bg-white border border-slate-100 rounded-xl animate-pulse shadow-sm" />
      </div>
    );
  }

  const sourcesList = [
    'Shopify Analytics',
    'Google Analytics 4',
    'Mixpanel',
    'Amplitude',
    'Segment',
    'Snowflake Data Warehouse',
  ];

  return (
    <div className="max-w-3xl mx-auto space-y-6 pb-12">
      <form onSubmit={handleSave} className="space-y-6">
        {/* FastAPI Integration Configuration Card */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-50">
            <Cpu className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">FastAPI Integration Settings</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Toggle between static mock data and live FastAPI backend</p>
            </div>
          </div>

          <div className="flex items-center justify-between p-3.5 bg-indigo-50/20 rounded-xl border border-indigo-50/50">
            <div className="space-y-0.5">
              <span className="text-xs font-bold text-slate-800">Enable FastAPI Integration Mode</span>
              <p className="text-[10px] text-slate-500">Redirect data queries to a local or production FastAPI endpoint</p>
            </div>
            <label className="relative inline-flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={enableFastApi}
                onChange={(e) => setEnableFastApi(e.target.checked)}
                className="sr-only peer"
              />
              <div className="w-11 h-6 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-indigo-600"></div>
            </label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                FastAPI Base URL
              </label>
              <input
                type="url"
                disabled={!enableFastApi}
                placeholder="http://localhost:8000"
                value={fastapiUrl}
                onChange={(e) => setFastapiUrl(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-200 disabled:bg-slate-50 disabled:text-slate-400 rounded-lg text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-100"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-1">
                API Auth Token
              </label>
              <input
                type="password"
                disabled={!enableFastApi}
                placeholder="pi_live_..."
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                className="w-full px-3.5 py-2 border border-slate-200 disabled:bg-slate-50 disabled:text-slate-400 rounded-lg text-sm focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-100"
              />
            </div>
          </div>

          {enableFastApi && (
            <div className="pt-2.5 flex items-center justify-between border-t border-slate-50">
              <div className="flex items-center gap-2 text-xs font-semibold">
                <span className="text-slate-500">Database Status:</span>
                <span className={`inline-flex items-center gap-1 font-bold ${
                  settings.dbStatus === 'Connected' ? 'text-emerald-600' : 'text-rose-600'
                }`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${
                    settings.dbStatus === 'Connected' ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'
                  }`} />
                  {settings.dbStatus}
                </span>
              </div>

              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testStatus === 'testing' || !fastapiUrl}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-600 font-bold rounded-lg text-[10px] uppercase tracking-wider transition-colors cursor-pointer"
              >
                {testStatus === 'testing' ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    Testing...
                  </>
                ) : (
                  <>
                    <Network className="w-3.5 h-3.5" />
                    Test Connection
                  </>
                )}
              </button>
            </div>
          )}

          {testStatus !== 'idle' && testStatus !== 'testing' && (
            <div className={`p-3 rounded-lg flex items-start gap-2 text-xs ${
              testStatus === 'Connected' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' : 'bg-rose-50 text-rose-700 border border-rose-100'
            }`}>
              {testStatus === 'Connected' ? (
                <>
                  <CheckCircle className="w-4 h-4 flex-shrink-0" />
                  <p className="font-medium">Connection verified successfully! The platform will query API routes.</p>
                </>
              ) : (
                <>
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" />
                  <p className="font-medium">Failed to reach FastAPI endpoint at {fastapiUrl}. Check server logs or verify CORS config.</p>
                </>
              )}
            </div>
          )}
        </div>

        {/* Engine Parameters Card */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-50">
            <Activity className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Simulation Engine parameters</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Control mock network delay values to preview loading states</p>
            </div>
          </div>

          <div className="space-y-2.5">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-600">Simulated Latency (Delay)</span>
              <span className="font-bold text-indigo-600">{mockDelay} ms</span>
            </div>
            <input
              type="range"
              min="0"
              max="3000"
              step="100"
              value={mockDelay}
              onChange={(e) => setMockDelay(Number(e.target.value))}
              className="w-full accent-indigo-600 bg-slate-100 h-1.5 rounded-lg appearance-none cursor-pointer"
            />
            <p className="text-[10px] text-slate-400">
              Useful for demonstrating full loading states, loaders, and transitions inside UI pages.
            </p>
          </div>
        </div>

        {/* Connected Data Sources Card */}
        <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 space-y-5">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-50">
            <Database className="w-5 h-5 text-indigo-600" />
            <div>
              <h3 className="font-semibold text-slate-900 text-sm">Data Sources</h3>
              <p className="text-[10px] text-slate-400 mt-0.5">Manage historical analytics repositories feeding your AI assistant</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
            {sourcesList.map((source) => {
              const isChecked = selectedSources.includes(source);
              return (
                <div
                  key={source}
                  onClick={() => toggleSource(source)}
                  className={`flex items-center justify-between p-3 border rounded-xl cursor-pointer transition-all duration-150 ${
                    isChecked
                      ? 'border-indigo-100 bg-indigo-50/20 text-indigo-900 font-semibold'
                      : 'border-slate-100 bg-slate-50/30 text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <span className="text-xs">{source}</span>
                  <input
                    type="checkbox"
                    checked={isChecked}
                    readOnly
                    className="accent-indigo-600 rounded"
                  />
                </div>
              );
            })}
          </div>
        </div>

        {/* Save Bar */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isSaving}
            className="flex items-center gap-1.5 px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-100 hover:shadow cursor-pointer"
          >
            {isSaving ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                Saving Changes...
              </>
            ) : (
              <>
                <Save className="w-3.5 h-3.5" />
                Save Configurations
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
