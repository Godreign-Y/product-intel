import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import {
  LayoutDashboard,
  TrendingUp,
  AlertTriangle,
  BookOpen,
  MessageSquare,
  Sparkles,
  Settings
} from 'lucide-react';
import { FilterProvider } from '../components/FilterContext';

export const MainLayout: React.FC = () => {
  return (
    <FilterProvider>
      <div className="app-container">
        {/* Sidebar */}
        <div className="sidebar">
          <div className="logo-container">
            <Sparkles size={24} className="kpi-icon ltv" />
            <span className="logo-text">ProductIntel</span>
          </div>

          <div className="nav-links">
            <NavLink 
              to="/" 
              end
              className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
            >
              <LayoutDashboard size={18} />
              Dashboard
            </NavLink>
            <NavLink 
              to="/predictions" 
              className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
            >
              <TrendingUp size={18} />
              Trend Analysis
            </NavLink>
            <NavLink 
              to="/recommendations" 
              className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
            >
              <AlertTriangle size={18} />
              Anomalies
            </NavLink>
            <NavLink 
              to="/experiments" 
              className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
            >
              <BookOpen size={18} />
              Repository
            </NavLink>
            <NavLink 
              to="/workspace" 
              className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
            >
              <MessageSquare size={18} />
              AI Assistant
            </NavLink>
            <NavLink 
              to="/settings" 
              className={({ isActive }) => `nav-button ${isActive ? 'active' : ''}`}
            >
              <Settings size={18} />
              Settings
            </NavLink>
          </div>
        </div>

        {/* Main Panel Content */}
        <div className="main-content">
          <Outlet />
        </div>
      </div>
    </FilterProvider>
  );
};
