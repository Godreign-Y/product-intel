import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bell, HelpCircle, Cpu, X, CheckCircle2, AlertTriangle, Info } from 'lucide-react';
import { getSystemSettings } from '../utils/api-client';

// ─────────────────────────────────────────────
// Mock notifications data
// ─────────────────────────────────────────────
const NOTIFICATIONS = [
  {
    id: 'n1',
    type: 'alert',
    title: 'Conversion rate dropped',
    body: 'Mobile conversion rate decreased by 7.8% — checkout may need attention.',
    time: '2 hours ago',
    read: false,
  },
  {
    id: 'n2',
    type: 'info',
    title: 'Simulation complete',
    body: 'Checkout Simplification experiment finished simulation with +6.2% lift.',
    time: '4 hours ago',
    read: false,
  },
  {
    id: 'n3',
    type: 'success',
    title: 'New recommendation available',
    body: 'AI identified a high-impact bundle pricing opportunity worth +$180K/year.',
    time: 'Yesterday',
    read: true,
  },
];

export const TopNavbar: React.FC = () => {
  const { pathname } = useLocation();

  // Settings checks to show status indicator
  const [fastApiEnabled, setFastApiEnabled] = React.useState(false);
  const [dbStatus, setDbStatus] = React.useState<'Connected' | 'Disconnected' | 'Connecting'>('Disconnected');

  // Notification panel state
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState(NOTIFICATIONS);
  const notifRef = useRef<HTMLDivElement>(null);

  // Help tooltip state
  const [helpOpen, setHelpOpen] = useState(false);
  const helpRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter(n => !n.read).length;

  React.useEffect(() => {
    const settings = getSystemSettings();
    setFastApiEnabled(settings.enableFastApi);
    setDbStatus(settings.dbStatus);
  }, [pathname]);

  // Close dropdowns on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) {
        setNotifOpen(false);
      }
      if (helpRef.current && !helpRef.current.contains(e.target as Node)) {
        setHelpOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, read: true })));

  const dismissNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

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

  const notifIcon = (type: string) => {
    if (type === 'alert') return <AlertTriangle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />;
    if (type === 'success') return <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />;
    return <Info className="w-4 h-4 text-[#7C3AED] flex-shrink-0 mt-0.5" />;
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
          to="/settings"
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

        {/* Help Button */}
        <div className="relative" ref={helpRef}>
          <button
            onClick={() => setHelpOpen(v => !v)}
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
                  <span>Enable <strong>FastAPI Mode</strong> in Settings to connect a live backend.</span>
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

        {/* Notifications Button */}
        <div className="relative" ref={notifRef}>
          <button
            onClick={() => setNotifOpen(v => !v)}
            className="text-slate-400 hover:text-slate-600 cursor-pointer p-1.5 rounded-lg hover:bg-slate-50 relative transition-colors"
            aria-label={`Notifications${unreadCount > 0 ? ` — ${unreadCount} unread` : ''}`}
          >
            <Bell className="w-4 h-4" />
            {unreadCount > 0 && (
              <span className="absolute top-0.5 right-0.5 w-2 h-2 bg-rose-500 rounded-full border border-white flex items-center justify-center text-[7px] text-white font-bold" />
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 bg-white rounded-xl border border-[#E5E7EB] shadow-lg z-50 overflow-hidden">
              {/* Header */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-50">
                <span className="text-xs font-bold text-[#111827]">
                  Notifications
                  {unreadCount > 0 && (
                    <span className="ml-1.5 text-[10px] bg-rose-100 text-rose-600 font-bold px-1.5 py-0.5 rounded-full">{unreadCount}</span>
                  )}
                </span>
                {unreadCount > 0 && (
                  <button
                    onClick={markAllRead}
                    className="text-[10px] font-bold text-[#7C3AED] hover:underline cursor-pointer"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              {/* Notification list */}
              <div className="max-h-72 overflow-y-auto">
                {notifications.length === 0 ? (
                  <div className="py-8 text-center text-xs text-[#9CA3AF]">No notifications</div>
                ) : (
                  notifications.map(n => (
                    <div
                      key={n.id}
                      className={`flex items-start gap-3 px-4 py-3 border-b border-slate-50 hover:bg-slate-50/50 transition-colors ${!n.read ? 'bg-[#F3E8FF]/20' : ''}`}
                    >
                      {notifIcon(n.type)}
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-bold ${n.read ? 'text-[#6B7280]' : 'text-[#111827]'}`}>{n.title}</p>
                        <p className="text-[11px] text-[#9CA3AF] leading-relaxed mt-0.5 line-clamp-2">{n.body}</p>
                        <span className="text-[10px] text-[#9CA3AF] font-semibold mt-1 block">{n.time}</span>
                      </div>
                      <button
                        onClick={() => dismissNotification(n.id)}
                        className="text-slate-300 hover:text-slate-500 cursor-pointer p-0.5 flex-shrink-0"
                        title="Dismiss"
                      >
                        <X className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
export default TopNavbar;
