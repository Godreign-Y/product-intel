'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Bell, HelpCircle, Network, ShieldCheck, Cpu } from 'lucide-react';
import { getSystemSettings } from '../utils/api-client';

export const TopNavbar: React.FC = () => {
  const pathname = usePathname();
  
  // Settings checks to show status indicator
  const [fastApiEnabled, setFastApiEnabled] = React.useState(false);
  const [dbStatus, setDbStatus] = React.useState<'Connected' | 'Disconnected' | 'Connecting'>('Disconnected');

  React.useEffect(() => {
    // Only access localStorage on client side
    const settings = getSystemSettings();
    setFastApiEnabled(settings.enableFastApi);
    setDbStatus(settings.dbStatus);
  }, [pathname]); // Refresh on navigation changes

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
        {/* FastAPI Status Badge */}
        <Link
          href="/settings"
          className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold border transition-colors cursor-pointer ${
            fastApiEnabled
              ? dbStatus === 'Connected'
                ? 'bg-emerald-50 text-emerald-600 border-emerald-100 hover:bg-emerald-100/50'
                : 'bg-rose-50 text-rose-600 border-rose-100 hover:bg-rose-100/50'
              : 'bg-slate-50 text-slate-500 border-slate-200 hover:bg-slate-100/50'
          }`}
          title={fastApiEnabled ? `Live FastAPI backend at ${dbStatus}` : 'Click to enable FastAPI integration'}
        >
          <Cpu className="w-3 h-3" />
          <span>{fastApiEnabled ? `FastAPI: ${dbStatus}` : 'Mock Engine Active'}</span>
          <span className={`w-1.5 h-1.5 rounded-full ${
            fastApiEnabled
              ? dbStatus === 'Connected'
                ? 'bg-emerald-500 animate-pulse'
                : 'bg-rose-500 animate-pulse'
              : 'bg-slate-400'
          }`} />
        </Link>

        {/* Support Link */}
        <button className="text-slate-400 hover:text-slate-600 cursor-pointer p-1 rounded-lg hover:bg-slate-50">
          <HelpCircle className="w-4 h-4" />
        </button>

        {/* Notifications */}
        <button className="text-slate-400 hover:text-slate-600 cursor-pointer p-1 rounded-lg hover:bg-slate-50 relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1 right-1 w-1.5 h-1.5 bg-rose-500 rounded-full" />
        </button>
      </div>
    </header>
  );
};
export default TopNavbar;
