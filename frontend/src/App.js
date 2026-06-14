import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
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
    return (_jsx(QueryProvider, { children: _jsx(BrowserRouter, { children: _jsx(MainLayout, { children: _jsxs(Routes, { children: [_jsx(Route, { path: "/", element: _jsx(Navigate, { to: "/dashboard", replace: true }) }), _jsx(Route, { path: "/dashboard", element: _jsx(DashboardPage, {}) }), _jsx(Route, { path: "/ai-workspace", element: _jsx(AIWorkspacePage, {}) }), _jsx(Route, { path: "/experiments", element: _jsx(ExperimentsPage, {}) }), _jsx(Route, { path: "/predictions", element: _jsx(PredictionsPage, {}) }), _jsx(Route, { path: "/recommendations", element: _jsx(RecommendationsPage, {}) }), _jsx(Route, { path: "/settings", element: _jsx(SettingsPage, {}) }), _jsx(Route, { path: "*", element: _jsx(Navigate, { to: "/dashboard", replace: true }) })] }) }) }) }));
}
