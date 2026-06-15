/**
 * TopNavbar Component.
 *
 * Displays the page title, backend connection status, and help tooltip.
 * All data is derived from real system state — no mock data.
 *
 * @module TopNavbar
 */

import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { HelpCircle, Cpu } from 'lucide-react';
import { getApiBaseUrl } from '../utils/api-client';

export const TopNavbar: React.FC = () => {
  const { pathname } = useLocation();

  // Connection status — checked via health endpoint
  const [connectionStatus, setConnectionStatus] = useState<'Connected' | 'Disconnected' | 'Checking'>('Checking');

  // Help tooltip state
  const [helpOpen, setHelpOpen] = useState(false);
  const helpRef = useRef<HTMLDivElement>(null);

  // Check backend health on page navigation
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const baseUrl = getApiBaseUrl();
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        const res = await fetch(`${baseUrl}/health`, { signal: controller.signal });
        clearTimeout(timeoutId);
        setConnectionStatus(res.ok ? 'Connected' : 'Disconnected');
      } catch {
        setConnectionStatus('Disconnected');
      }
    };
    checkHealth();
  }, [pathname]);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (helpRef.current && !helpRef.current.contains(e.target as Node)) {
        setHelpOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Map path to human-readable page name
  const getPageTitle = () => {
    if (pathname === '/' || pathname === '/dashboard') return 'Executive Dashboard';
    if (pathname.startsWith('/ai-workspace')) return 'AI Workspace';
    if (pathname.startsWith('/experiments')) return 'Experiments (Run & Simulate)';
    if (pathname.startsWith('/predictions')) return 'Predictions & Forecasts';
    if (pathname.startsWith('/recommendations')) return 'AI Recommendations';
    if (pathname.startsWith('/settings')) return 'System Settings';
    return 'Product Intelligence OS';
  };

  const getPageSubtitle = () => {
    if (pathname === '/' || pathname === '/dashboard') return 'Track key metrics, insights and opportunities';
    if (pathname.startsWith('/ai-workspace')) return 'Ask questions, explore insights and get AI-powered analysis';
    if (pathname.startsWith('/experiments')) return 'Create, manage and simulate experiments';
    if (pathname.startsWith('/predictions')) return 'AI-powered forecasts and predictive analytics';
    if (pathname.startsWith('/recommendations')) return 'AI-powered actionable growth recommendations';
    if (pathname.startsWith('/settings')) return 'Configure data sources and system integrations';
    return 'Decision Intelligence Platform';
  };

  return (
    <header className="h-16 bg-white border-b border-slate-100 flex items-center justify-between px-8 sticky top-0 z-40">
      {/* Title */}
      <div>
        <h2 className="text-base font-bold text-slate-800 tracking-tight leading-none">
          {getPageTitle()}
        </h2>
        <p className="text-[10px] text-slate-400 font-medium mt-1">
          {getPageSubtitle()}
        </p>
      </div>

      {/* Right Tools */}
      <div className="flex items-center gap-4">
        {/* Backend Status Badge */}
        <Link
          to="/settings"
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold border transition-colors cursor-pointer ${
            connectionStatus === 'Connected'
              ? 'bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-emerald-100/50'
              : connectionStatus === 'Checking'
              ? 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100/50'
              : 'bg-rose-50 text-rose-600 border-rose-100 hover:bg-rose-100/50'
          }`}
          title={`Backend API at ${getApiBaseUrl()}`}
        >
          <Cpu className="w-3 h-3" />
          <span>
            {connectionStatus === 'Connected'
              ? 'API: Connected'
              : connectionStatus === 'Checking'
              ? 'Checking...'
              : 'API: Disconnected'}
          </span>
          <span
            className={`w-1.5 h-1.5 rounded-full ${
              connectionStatus === 'Connected'
                ? 'bg-emerald-500 animate-pulse'
                : connectionStatus === 'Checking'
                ? 'bg-slate-400 animate-pulse'
                : 'bg-rose-500 animate-pulse'
            }`}
          />
        </Link>

        {/* Help Button */}
        <div className="relative" ref={helpRef}>
          <button
            onClick={() => setHelpOpen((v) => !v)}
            className="text-slate-400 hover:text-slate-600 cursor-pointer p-1.5 rounded-lg hover:bg-slate-50 transition-colors"
            aria-label="Help"
            title="Help & Documentation"
          >
            <HelpCircle className="w-4 h-4" />
          </button>

          {helpOpen && (
            <div className="absolute right-0 top-full mt-2 w-64 bg-white rounded-xl border border-[#E5E7EB] shadow-lg z-50 p-4">
              <h4 className="text-xs font-bold text-[#111827] mb-3">Quick Help</h4>
              <ul className="space-y-2 text-xs text-[#6B7280]">
                <li className="flex items-start gap-2">
                  <span className="w-4 h-4 rounded bg-[#F3E8FF] text-[#7C3AED] text-[9px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">?</span>
                  <span>Use <strong>AI Workspace</strong> to ask natural language questions about your data.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-4 h-4 rounded bg-[#F3E8FF] text-[#7C3AED] text-[9px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">?</span>
                  <span>Run <strong>Simulations</strong> in Experiments to predict revenue impact before launching.</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-4 h-4 rounded bg-[#F3E8FF] text-[#7C3AED] text-[9px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">?</span>
                  <span>View <strong>Predictions</strong> for ML-powered forecasting across all key metrics.</span>
                </li>
              </ul>
              <div className="mt-3 pt-3 border-t border-slate-50">
                <Link
                  to="/settings"
                  onClick={() => setHelpOpen(false)}
                  className="text-[11px] font-bold text-[#7C3AED] hover:underline"
                >
                  Go to Settings →
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
export default TopNavbar;
