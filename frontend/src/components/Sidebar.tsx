import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Brain,
  FlaskConical,
  LineChart,
  Lightbulb,
  Settings,
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { pathname } = useLocation();

  const menuItems = [
    { name: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
    { name: 'AI Workspace', path: '/ai-workspace', icon: Brain },
    { name: 'Experiments', path: '/experiments', icon: FlaskConical },
    { name: 'Predictions', path: '/predictions', icon: LineChart },
    { name: 'Recommendations', path: '/recommendations', icon: Lightbulb },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  return (
    <aside className="w-[280px] bg-white text-[#111827] flex flex-col justify-between border-r border-[#E5E7EB] h-screen sticky top-0 flex-shrink-0 z-50">
      <div>
        {/* Brand Logo */}
        <div className="p-6 border-b border-[#E5E7EB]">
          <Link to="/dashboard" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-[#7C3AED] flex items-center justify-center shadow-lg group-hover:bg-[#6D28D9] transition-all duration-150">
              <span className="font-extrabold text-white text-base">π</span>
            </div>
            <div>
              <h1 className="font-bold text-sm tracking-wide text-[#111827] leading-tight">Product</h1>
              <p className="text-[10px] text-[#7C3AED] font-bold tracking-widest uppercase">Intelligence System</p>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="px-4 py-6 space-y-1.5">
          {menuItems.map((item) => {
            const isActive =
              item.path === '/dashboard'
                ? pathname === '/' || pathname === '/dashboard'
                : pathname.startsWith(item.path);
            const Icon = item.icon;

            return (
              <Link
                key={item.name}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-[12px] h-[44px] text-sm font-semibold transition-all duration-150 cursor-pointer ${
                  isActive
                    ? 'bg-[#7C3AED] text-white shadow-md shadow-purple-200'
                    : 'text-[#111827] hover:bg-[#F3E8FF] hover:text-[#7C3AED] group'
                }`}
              >
                <Icon className={`w-4 h-4 transition-colors ${isActive ? 'text-white' : 'text-[#6B7280] group-hover:text-[#7C3AED]'}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User profile at bottom */}
      <div className="p-4 border-t border-[#E5E7EB] bg-slate-50/50 flex items-center gap-3">
        <div className="w-9 h-9 rounded-full bg-[#F3E8FF] text-[#7C3AED] font-bold text-xs flex items-center justify-center">
          AR
        </div>
        <div>
          <h4 className="text-xs font-bold text-[#111827]">Aarav R.</h4>
          <p className="text-[10px] text-[#6B7280]">Product Team</p>
        </div>
      </div>
    </aside>
  );
};
