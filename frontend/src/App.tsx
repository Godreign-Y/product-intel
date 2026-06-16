import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import './App.css';

// Lazy loaded page components for performance
const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));
const WorkspacePage = React.lazy(() => import('./pages/WorkspacePage'));
const ExperimentsPage = React.lazy(() => import('./pages/ExperimentsPage'));
const PredictionsPage = React.lazy(() => import('./pages/PredictionsPage'));
const RecommendationsPage = React.lazy(() => import('./pages/RecommendationsPage'));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage'));

// Simple loading fallback
const PageLoader = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: 'var(--text-muted)' }}>
    Loading module...
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback={<PageLoader />}>
        <Routes>
          <Route path="/" element={<MainLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="workspace" element={<WorkspacePage />} />
            <Route path="experiments" element={<ExperimentsPage />} />
            <Route path="predictions" element={<PredictionsPage />} />
            <Route path="recommendations" element={<RecommendationsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
