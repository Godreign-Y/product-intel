import React, { useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  AlertTriangle,
  BookOpen,
  MessageSquare,
  Settings,
  Menu,
  X,
  Sun,
  Moon,
} from 'lucide-react';
import { FilterProvider } from '../components/FilterContext';
import { useTheme } from '../context/ThemeContext';
import { ThreeDInteractiveBackground } from '../components/ThreeDInteractiveBackground';

const NAV_ITEMS = [
  { to: '/', end: true, icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/predictions', icon: TrendingUp, label: 'Analytics' },
  { to: '/recommendations', icon: AlertTriangle, label: 'Anomalies' },
  { to: '/experiments', icon: BookOpen, label: 'Repository' },
  { to: '/workspace', icon: MessageSquare, label: 'AI Assistant' },
  { to: '/settings', icon: Settings, label: 'Settings' },
];

export const MainLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  const closeSidebar = () => setSidebarOpen(false);

  return (
    <FilterProvider>
      <ThreeDInteractiveBackground />
      <button
        className="mobile-menu-btn"
        onClick={() => setSidebarOpen(!sidebarOpen)}
        aria-label="Toggle navigation"
      >
        {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      <div
        className={`sidebar-overlay ${sidebarOpen ? 'visible' : ''}`}
        onClick={closeSidebar}
        aria-hidden
      />

      <div className="app-container">
        <aside className={`sidebar ${sidebarOpen ? 'open' : ''}`}>
          <div className="logo-container">
            <img 
              src="/favicon.svg" 
              alt="ProductIntel Logo" 
              style={{ width: 40, height: 40, objectFit: 'contain' }} 
            />
            <div>
              <div className="logo-text">ProductIntel</div>
              <div className="logo-tagline">Product Intelligence</div>
            </div>
          </div>

          <div className="nav-section-label">Navigation</div>
          <nav className="nav-links">
            {NAV_ITEMS.map(({ to, end, icon: Icon, label }) => (
              <NavLink
                key={to}
                to={to}
                end={end}
                className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
                onClick={closeSidebar}
              >
                <Icon size={18} strokeWidth={1.75} />
                {label}
              </NavLink>
            ))}
          </nav>

          <div className="sidebar-footer">
            <button className="theme-toggle-btn" onClick={toggleTheme}>
              <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                {theme === 'dark' ? <Moon size={16} /> : <Sun size={16} />}
                {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
              </span>
              <span style={{ fontSize: 11, opacity: 0.6 }}>Toggle</span>
            </button>
          </div>
        </aside>

        <main className="main-content">
          <div className="page-enter">
            <Outlet />
          </div>
        </main>
      </div>
    </FilterProvider>
  );
};
