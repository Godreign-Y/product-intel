import React from 'react';
import { Sidebar } from '../components/Sidebar';
import { TopNavbar } from '../components/TopNavbar';

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="flex bg-slate-50/50 min-h-screen text-slate-600 antialiased font-sans">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Container */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Navbar */}
        <TopNavbar />

        {/* Page Content Workspace */}
        <main className="flex-grow p-8 overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
};
export default MainLayout;
