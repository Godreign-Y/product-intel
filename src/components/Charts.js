'use client';
import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, } from 'recharts';
// Client-only wrapper helper to prevent hydration mismatch in Recharts
const ClientOnly = ({ children }) => {
    const [mounted, setMounted] = useState(false);
    useEffect(() => {
        setMounted(true);
    }, []);
    if (!mounted) {
        return (_jsx("div", { className: "w-full h-full flex items-center justify-center bg-slate-50/50 rounded-lg animate-pulse", children: _jsx("span", { className: "text-sm text-slate-400 font-medium", children: "Loading visualization..." }) }));
    }
    return _jsx(_Fragment, { children: children });
};
export const PerformanceChart = ({ data }) => {
    const [activeMetrics, setActiveMetrics] = useState({
        revenue: true,
        orders: false,
        conversionRate: false,
        profit: false,
    });
    const formatYAxis = (value, metric) => {
        if (metric === 'revenue' || metric === 'profit') {
            if (value >= 1000000)
                return `$${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000)
                return `$${(value / 1000).toFixed(0)}K`;
            return `$${value}`;
        }
        if (metric === 'conversionRate') {
            return `${value}%`;
        }
        if (value >= 1000)
            return `${(value / 1000).toFixed(1)}k`;
        return value.toString();
    };
    const getPrimaryMetric = () => {
        if (activeMetrics.revenue)
            return 'revenue';
        if (activeMetrics.profit)
            return 'profit';
        if (activeMetrics.orders)
            return 'orders';
        return 'conversionRate';
    };
    const activeKey = getPrimaryMetric();
    return (_jsxs("div", { className: "bg-white rounded-xl border border-slate-100 p-5 shadow-sm h-full flex flex-col justify-between", children: [_jsxs("div", { className: "flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 pb-4 border-b border-slate-50", children: [_jsxs("div", { children: [_jsx("h3", { className: "font-semibold text-slate-900", children: "Performance Over Time" }), _jsx("p", { className: "text-xs text-slate-400 mt-0.5", children: "Track key performance metrics side by side" })] }), _jsx("div", { className: "flex flex-wrap gap-2", children: [
                            { key: 'revenue', label: 'Revenue', color: 'bg-indigo-600 text-white border-indigo-600', inactive: 'text-slate-600 hover:bg-slate-50 border-slate-200' },
                            { key: 'orders', label: 'Orders', color: 'bg-sky-600 text-white border-sky-600', inactive: 'text-slate-600 hover:bg-slate-50 border-slate-200' },
                            { key: 'conversionRate', label: 'Conversion Rate (%)', color: 'bg-rose-600 text-white border-rose-600', inactive: 'text-slate-600 hover:bg-slate-50 border-slate-200' },
                            { key: 'profit', label: 'Profit', color: 'bg-emerald-600 text-white border-emerald-600', inactive: 'text-slate-600 hover:bg-slate-50 border-slate-200' },
                        ].map((item) => {
                            const isSelected = activeMetrics[item.key];
                            return (_jsx("button", { onClick: () => setActiveMetrics((prev) => ({
                                    ...prev,
                                    [item.key]: !isSelected,
                                    // Ensure at least one metric is active
                                    ...(isSelected && Object.values(prev).filter(Boolean).length === 1 ? { [item.key]: true } : {}),
                                })), className: `text-xs font-semibold px-3 py-1.5 rounded-lg border transition-all duration-150 cursor-pointer ${isSelected ? item.color : item.inactive}`, children: item.label }, item.key));
                        }) })] }), _jsx("div", { className: "h-72 mt-6", children: _jsx(ClientOnly, { children: _jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(LineChart, { data: data, margin: { top: 10, right: 10, left: -10, bottom: 0 }, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#f1f5f9", vertical: false }), _jsx(XAxis, { dataKey: "date", stroke: "#94a3b8", fontSize: 11, tickLine: false, axisLine: false, dy: 10 }), _jsx(YAxis, { stroke: "#94a3b8", fontSize: 11, tickLine: false, axisLine: false, tickFormatter: (v) => formatYAxis(v, activeKey), dx: -5 }), _jsx(Tooltip, { contentStyle: {
                                        backgroundColor: '#ffffff',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '12px',
                                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03)',
                                    }, labelStyle: { fontWeight: 'bold', color: '#1e293b', marginBottom: '4px' }, itemStyle: { fontSize: '12px', padding: '2px 0' } }), _jsx(Legend, { verticalAlign: "top", height: 36, iconType: "circle", iconSize: 8, wrapperStyle: { fontSize: '11px', color: '#64748b' } }), activeMetrics.revenue && (_jsx(Line, { name: "Revenue", type: "monotone", dataKey: "revenue", stroke: "#4f46e5", strokeWidth: 2.5, dot: { r: 4, strokeWidth: 1, fill: '#ffffff' }, activeDot: { r: 6, strokeWidth: 0 } })), activeMetrics.orders && (_jsx(Line, { name: "Orders", type: "monotone", dataKey: "orders", stroke: "#0284c7", strokeWidth: 2.5, dot: { r: 4, strokeWidth: 1, fill: '#ffffff' }, activeDot: { r: 6, strokeWidth: 0 } })), activeMetrics.conversionRate && (_jsx(Line, { name: "Conversion Rate", type: "monotone", dataKey: "conversionRate", stroke: "#e11d48", strokeWidth: 2.5, dot: { r: 4, strokeWidth: 1, fill: '#ffffff' }, activeDot: { r: 6, strokeWidth: 0 } })), activeMetrics.profit && (_jsx(Line, { name: "Profit", type: "monotone", dataKey: "profit", stroke: "#059669", strokeWidth: 2.5, dot: { r: 4, strokeWidth: 1, fill: '#ffffff' }, activeDot: { r: 6, strokeWidth: 0 } }))] }) }) }) })] }));
};
export const ForecastChart = ({ data, metricName }) => {
    const formatYAxis = (value) => {
        if (metricName.toLowerCase().includes('rate') || metricName.includes('%')) {
            return `${value.toFixed(2)}%`;
        }
        if (value >= 1000000)
            return `$${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000)
            return `$${(value / 1000).toFixed(0)}K`;
        return `$${value}`;
    };
    return (_jsxs("div", { className: "bg-white rounded-xl border border-slate-100 p-5 shadow-sm h-full flex flex-col justify-between", children: [_jsx("div", { className: "pb-4 border-b border-slate-50 flex items-center justify-between", children: _jsxs("div", { children: [_jsxs("h3", { className: "font-semibold text-slate-900", children: [metricName, " Forecast"] }), _jsx("p", { className: "text-xs text-slate-400 mt-0.5", children: "3-Month forecast with 95% confidence intervals" })] }) }), _jsx("div", { className: "h-72 mt-6", children: _jsx(ClientOnly, { children: _jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(AreaChart, { data: data, margin: { top: 10, right: 10, left: -10, bottom: 0 }, children: [_jsxs("defs", { children: [_jsxs("linearGradient", { id: "actualGradient", x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "5%", stopColor: "#4f46e5", stopOpacity: 0.1 }), _jsx("stop", { offset: "95%", stopColor: "#4f46e5", stopOpacity: 0 })] }), _jsxs("linearGradient", { id: "forecastGradient", x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "5%", stopColor: "#818cf8", stopOpacity: 0.2 }), _jsx("stop", { offset: "95%", stopColor: "#818cf8", stopOpacity: 0 })] })] }), _jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#f1f5f9", vertical: false }), _jsx(XAxis, { dataKey: "date", stroke: "#94a3b8", fontSize: 11, tickLine: false, axisLine: false, dy: 10 }), _jsx(YAxis, { stroke: "#94a3b8", fontSize: 11, tickLine: false, axisLine: false, tickFormatter: formatYAxis, dx: -5 }), _jsx(Tooltip, { contentStyle: {
                                        backgroundColor: '#ffffff',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '12px',
                                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -1px rgba(0,0,0,0.03)',
                                    }, labelStyle: { fontWeight: 'bold', color: '#1e293b' }, itemStyle: { fontSize: '12px', padding: '2px 0' } }), _jsx(Legend, { verticalAlign: "top", height: 36, iconType: "circle", iconSize: 8, wrapperStyle: { fontSize: '11px' } }), _jsx(Area, { name: "Confidence Interval", type: "monotone", dataKey: (v) => [v.confidenceLower, v.confidenceUpper], stroke: "none", fill: "#818cf8", fillOpacity: 0.15 }), _jsx(Area, { name: "Actual", type: "monotone", dataKey: "actual", stroke: "#4f46e5", strokeWidth: 2.5, fill: "url(#actualGradient)", dot: { r: 4, strokeWidth: 1, fill: '#ffffff' } }), _jsx(Line, { name: "Forecast", type: "monotone", dataKey: "forecast", stroke: "#818cf8", strokeWidth: 2.5, strokeDasharray: "5 5", dot: { r: 4, strokeWidth: 1, fill: '#ffffff', stroke: '#818cf8' } })] }) }) }) })] }));
};
export const SimulationChart = ({ data }) => {
    const formatYAxis = (value) => {
        if (value >= 1000000)
            return `$${(value / 1000000).toFixed(2)}M`;
        return `$${value}`;
    };
    return (_jsx("div", { className: "h-48", children: _jsx(ClientOnly, { children: _jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(LineChart, { data: data, margin: { top: 10, right: 10, left: -10, bottom: 0 }, children: [_jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#f8fafc", vertical: false }), _jsx(XAxis, { dataKey: "week", stroke: "#cbd5e1", fontSize: 10, tickLine: false, axisLine: false, dy: 5 }), _jsx(YAxis, { stroke: "#cbd5e1", fontSize: 10, tickLine: false, axisLine: false, tickFormatter: formatYAxis, dx: -5 }), _jsx(Tooltip, { contentStyle: {
                                backgroundColor: '#ffffff',
                                border: '1px solid #f1f5f9',
                                borderRadius: '8px',
                                fontSize: '11px',
                            } }), _jsx(Legend, { verticalAlign: "top", height: 24, iconSize: 6, wrapperStyle: { fontSize: '10px' } }), _jsx(Line, { name: "Current", type: "monotone", dataKey: "current", stroke: "#94a3b8", strokeWidth: 1.5, strokeDasharray: "4 4", dot: false }), _jsx(Line, { name: "Simulated", type: "monotone", dataKey: "simulated", stroke: "#22c55e", strokeWidth: 2, dot: { r: 3, fill: '#22c55e' } })] }) }) }) }));
};
// 4. Dedicated Revenue Trend Chart for Dashboard
export const RevenueTrendChart = ({ data }) => {
    const formatYAxis = (value) => {
        if (value >= 1000000)
            return `$${(value / 1000000).toFixed(1)}M`;
        if (value >= 1000)
            return `$${(value / 1000).toFixed(0)}K`;
        return `$${value}`;
    };
    return (_jsxs("div", { className: "bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 h-[350px] flex flex-col justify-between", children: [_jsxs("div", { className: "pb-3 border-b border-slate-50", children: [_jsx("h3", { className: "text-sm font-bold text-[#111827]", children: "Revenue Trend" }), _jsx("p", { className: "text-xs text-[#6B7280]", children: "Monthly revenue tracking stream" })] }), _jsx("div", { className: "h-56 mt-4", children: _jsx(ClientOnly, { children: _jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(AreaChart, { data: data, margin: { top: 10, right: 10, left: -10, bottom: 0 }, children: [_jsx("defs", { children: _jsxs("linearGradient", { id: "revenueColor", x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "5%", stopColor: "#7C3AED", stopOpacity: 0.2 }), _jsx("stop", { offset: "95%", stopColor: "#7C3AED", stopOpacity: 0 })] }) }), _jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#f1f5f9", vertical: false }), _jsx(XAxis, { dataKey: "date", stroke: "#9CA3AF", fontSize: 11, tickLine: false, axisLine: false, dy: 10 }), _jsx(YAxis, { stroke: "#9CA3AF", fontSize: 11, tickLine: false, axisLine: false, tickFormatter: formatYAxis, dx: -5 }), _jsx(Tooltip, { contentStyle: {
                                        backgroundColor: '#ffffff',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '12px',
                                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
                                    }, labelStyle: { fontWeight: 'bold', color: '#111827' }, itemStyle: { fontSize: '12px' } }), _jsx(Area, { type: "monotone", name: "Revenue", dataKey: "revenue", stroke: "#7C3AED", strokeWidth: 2.5, fillOpacity: 1, fill: "url(#revenueColor)", dot: { r: 4, strokeWidth: 1, fill: '#ffffff', stroke: '#7C3AED' } })] }) }) }) })] }));
};
// 5. Dedicated Conversion Trend Chart for Dashboard
export const ConversionTrendChart = ({ data }) => {
    return (_jsxs("div", { className: "bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 h-[350px] flex flex-col justify-between", children: [_jsxs("div", { className: "pb-3 border-b border-slate-50", children: [_jsx("h3", { className: "text-sm font-bold text-[#111827]", children: "Conversion Trend" }), _jsx("p", { className: "text-xs text-[#6B7280]", children: "Conversion rate tracking stream" })] }), _jsx("div", { className: "h-56 mt-4", children: _jsx(ClientOnly, { children: _jsx(ResponsiveContainer, { width: "100%", height: "100%", children: _jsxs(AreaChart, { data: data, margin: { top: 10, right: 10, left: -10, bottom: 0 }, children: [_jsx("defs", { children: _jsxs("linearGradient", { id: "conversionColor", x1: "0", y1: "0", x2: "0", y2: "1", children: [_jsx("stop", { offset: "5%", stopColor: "#3B82F6", stopOpacity: 0.2 }), _jsx("stop", { offset: "95%", stopColor: "#3B82F6", stopOpacity: 0 })] }) }), _jsx(CartesianGrid, { strokeDasharray: "3 3", stroke: "#f1f5f9", vertical: false }), _jsx(XAxis, { dataKey: "date", stroke: "#9CA3AF", fontSize: 11, tickLine: false, axisLine: false, dy: 10 }), _jsx(YAxis, { stroke: "#9CA3AF", fontSize: 11, tickLine: false, axisLine: false, tickFormatter: (v) => `${v}%`, dx: -5 }), _jsx(Tooltip, { contentStyle: {
                                        backgroundColor: '#ffffff',
                                        border: '1px solid #e2e8f0',
                                        borderRadius: '12px',
                                        boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
                                    }, labelStyle: { fontWeight: 'bold', color: '#111827' }, itemStyle: { fontSize: '12px' } }), _jsx(Area, { type: "monotone", name: "Conversion Rate", dataKey: "conversionRate", stroke: "#3B82F6", strokeWidth: 2.5, fillOpacity: 1, fill: "url(#conversionColor)", dot: { r: 4, strokeWidth: 1, fill: '#ffffff', stroke: '#3B82F6' } })] }) }) }) })] }));
};
