'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Brain,
  FlaskConical,
  LineChart,
  Lightbulb,
  Settings,
  ShieldAlert,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const pathname = usePathname();

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Workspace', path: '/ai-workspace', icon: Brain },
    { name: 'Experiments', path: '/experiments', icon: FlaskConical },
    { name: 'Predictions', path: '/predictions', icon: LineChart },
    { name: 'Recommendations', path: '/recommendations', icon: Lightbulb },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-slate-100 flex flex-col justify-between border-r border-slate-800 h-screen sticky top-0">
      {/* Brand Logo */}
      <div className="p-6 border-b border-slate-800">
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center shadow-lg group-hover:scale-105 transition-transform duration-150">
            <span className="font-extrabold text-white text-base">π</span>
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-wide text-white leading-tight">Product</h1>
            <p className="text-[10px] text-indigo-400 font-bold tracking-widest uppercase">Intelligence OS</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {menuItems.map((item) => {
          // Check if active: matches start of path (except settings which matches exact)
          const isActive =
            item.path === '/dashboard'
              ? pathname === '/' || pathname === '/dashboard'
              : pathname.startsWith(item.path);
          const Icon = item.icon;

          return (
            <Link
              key={item.name}
              href={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all duration-150 cursor-pointer ${
                isActive
                  ? 'bg-indigo-600 text-white shadow-md shadow-indigo-900/30'
                  : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-slate-200'}`} />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* User Profile */}
      <div className="p-4 border-t border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center gap-3 bg-slate-800/40 p-3 rounded-xl border border-slate-800/60">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 text-indigo-400 flex items-center justify-center font-bold text-xs">
            AR
          </div>
          <div className="overflow-hidden">
            <h4 className="text-xs font-bold text-slate-200 truncate">Aarav R.</h4>
            <p className="text-[9px] text-slate-500 font-semibold tracking-wider uppercase truncate">Product Team</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
export default Sidebar;
