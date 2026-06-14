import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import QueryProvider from './components/QueryProvider';
import MainLayout from './layouts/MainLayout';

// Pages
import DashboardPage from './pages/Dashboard';
import AIWorkspacePage from './pages/AIWorkspace';
import ExperimentsPage from './pages/Experiments';
import PredictionsPage from './pages/Predictions';
import RecommendationsPage from './pages/Recommendations';
import SettingsPage from './pages/Settings';

export default function App() {
  return (
    <QueryProvider>
      <BrowserRouter>
        <MainLayout>
          <Routes>
            {/* Redirect / to /dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            
            {/* Core Routes */}
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/ai-workspace" element={<AIWorkspacePage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/predictions" element={<PredictionsPage />} />
            <Route path="/recommendations" element={<RecommendationsPage />} />
            <Route path="/settings" element={<SettingsPage />} />

            {/* Fallback to dashboard */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </MainLayout>
      </BrowserRouter>
    </QueryProvider>
  );
}
