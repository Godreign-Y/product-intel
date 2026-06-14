import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { useState, useRef, useEffect } from 'react';
import { Calendar, Download, AlertTriangle, Lightbulb, TrendingUp, RefreshCw, Info, Check, ChevronDown, X, } from 'lucide-react';
import { useDashboardData } from '../hooks/useDashboardData';
import { KPICard } from '../components/KPICard';
import { RevenueTrendChart, ConversionTrendChart } from '../components/Charts';
// ─────────────────────────────────────────────
// Date Range Definitions
// ─────────────────────────────────────────────
const DATE_RANGES = [
    { label: 'Last 30 Days', value: '30d', display: 'May 20 – Jun 18, 2026' },
    { label: 'Last 7 Days', value: '7d', display: 'Jun 12 – Jun 18, 2026' },
    { label: 'Last 90 Days', value: '90d', display: 'Mar 21 – Jun 18, 2026' },
    { label: 'This Quarter', value: 'qtd', display: 'Apr 01 – Jun 18, 2026' },
    { label: 'Last Quarter', value: 'lq', display: 'Jan 01 – Mar 31, 2026' },
    { label: 'This Year', value: 'ytd', display: 'Jan 01 – Jun 18, 2026' },
];
export default function DashboardPage() {
    const { data, isLoading, isError, error, refetch } = useDashboardData();
    // ── Date range state ──────────────────────────
    const [selectedRange, setSelectedRange] = useState(DATE_RANGES[0]);
    const [datePickerOpen, setDatePickerOpen] = useState(false);
    const datePickerRef = useRef(null);
    // ── Export state ──────────────────────────────
    const [exportState, setExportState] = useState('idle');
    const [exportFormat, setExportFormat] = useState('json');
    const [exportMenuOpen, setExportMenuOpen] = useState(false);
    const exportMenuRef = useRef(null);
    // Close dropdowns on outside click
    useEffect(() => {
        const handleClickOutside = (e) => {
            if (datePickerRef.current && !datePickerRef.current.contains(e.target)) {
                setDatePickerOpen(false);
            }
            if (exportMenuRef.current && !exportMenuRef.current.contains(e.target)) {
                setExportMenuOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);
    // ── Export handler ────────────────────────────
    const handleExport = (format) => {
        if (!data || exportState === 'loading')
            return;
        setExportMenuOpen(false);
        setExportState('loading');
        // Simulate async export
        setTimeout(() => {
            try {
                if (format === 'json') {
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `dashboard-export-${selectedRange.value}.json`;
                    a.click();
                    URL.revokeObjectURL(url);
                }
                else {
                    // CSV: flatten KPI data
                    const headers = ['Metric', 'Value', 'Change %', 'Positive'];
                    const rows = data.kpis.map(k => [k.title, k.value, k.changePercent, k.isPositive].join(','));
                    const csv = [headers.join(','), ...rows].join('\n');
                    const blob = new Blob([csv], { type: 'text/csv' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = `dashboard-export-${selectedRange.value}.csv`;
                    a.click();
                    URL.revokeObjectURL(url);
                }
                setExportState('success');
                setTimeout(() => setExportState('idle'), 3000);
            }
            catch {
                setExportState('error');
                setTimeout(() => setExportState('idle'), 3000);
            }
        }, 900);
    };
    // ─────────────────────────────────────────────
    if (isLoading) {
        return (_jsxs("div", { className: "space-y-6", children: [_jsx("div", { className: "flex justify-between items-center h-12 bg-slate-100 rounded-lg animate-pulse w-full" }), _jsx("div", { className: "grid grid-cols-1 md:grid-cols-4 gap-6", children: [...Array(4)].map((_, i) => (_jsx("div", { className: "h-[140px] bg-white rounded-[20px] border border-slate-100 p-5 shadow-sm animate-pulse" }, i))) }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-6", children: [_jsx("div", { className: "h-[350px] bg-white rounded-[20px] border border-slate-100 p-5 shadow-sm animate-pulse" }), _jsx("div", { className: "h-[350px] bg-white rounded-[20px] border border-slate-100 p-5 shadow-sm animate-pulse" })] })] }));
    }
    if (isError) {
        return (_jsxs("div", { className: "bg-rose-50 border border-rose-100 rounded-xl p-6 text-center max-w-2xl mx-auto my-12", children: [_jsx(AlertTriangle, { className: "w-12 h-12 text-rose-500 mx-auto mb-4" }), _jsx("h3", { className: "text-lg font-bold text-slate-800 mb-2", children: "Error Loading Dashboard" }), _jsx("p", { className: "text-sm text-slate-600 mb-6", children: error?.message || 'An unexpected error occurred.' }), _jsxs("button", { onClick: () => refetch(), className: "flex items-center gap-1.5 px-4 py-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer", children: [_jsx(RefreshCw, { className: "w-3.5 h-3.5" }), "Retry Request"] })] }));
    }
    if (!data)
        return null;
    return (_jsxs("div", { className: "space-y-8 pb-12", children: [_jsxs("div", { className: "flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4", children: [_jsxs("div", { children: [_jsx("h1", { className: "text-2xl font-extrabold text-[#111827] tracking-tight", children: "Dashboard" }), _jsx("p", { className: "text-xs text-[#6B7280] mt-1", children: "Executive overview of business performance" })] }), _jsxs("div", { className: "flex items-center gap-3 w-full sm:w-auto", children: [_jsxs("div", { className: "relative", ref: datePickerRef, children: [_jsxs("button", { onClick: () => setDatePickerOpen(v => !v), className: "flex items-center gap-2 bg-white px-3 py-2 rounded-xl border border-[#E5E7EB] hover:bg-slate-50 cursor-pointer shadow-sm transition-colors", "aria-haspopup": "listbox", "aria-expanded": datePickerOpen, children: [_jsx(Calendar, { className: "w-4 h-4 text-[#6B7280]" }), _jsx("span", { className: "text-xs font-semibold text-[#111827]", children: selectedRange.display }), _jsx(ChevronDown, { className: `w-3.5 h-3.5 text-[#6B7280] transition-transform ${datePickerOpen ? 'rotate-180' : ''}` })] }), datePickerOpen && (_jsx("div", { className: "absolute right-0 top-full mt-2 w-52 bg-white rounded-xl border border-[#E5E7EB] shadow-lg z-50 py-1 overflow-hidden", children: DATE_RANGES.map(range => (_jsxs("button", { onClick: () => {
                                                setSelectedRange(range);
                                                setDatePickerOpen(false);
                                            }, className: `w-full text-left px-4 py-2.5 text-xs font-semibold flex items-center justify-between transition-colors ${selectedRange.value === range.value
                                                ? 'bg-[#F3E8FF] text-[#7C3AED]'
                                                : 'text-[#111827] hover:bg-slate-50'}`, children: [_jsx("span", { children: range.label }), selectedRange.value === range.value && _jsx(Check, { className: "w-3.5 h-3.5" })] }, range.value))) }))] }), _jsxs("div", { className: "relative", ref: exportMenuRef, children: [_jsx("button", { onClick: () => {
                                            if (exportState === 'idle')
                                                setExportMenuOpen(v => !v);
                                        }, disabled: exportState === 'loading', className: `flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold shadow-sm cursor-pointer transition-all ${exportState === 'success'
                                            ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                                            : exportState === 'error'
                                                ? 'bg-rose-50 text-rose-600 border-rose-200'
                                                : exportState === 'loading'
                                                    ? 'bg-slate-50 text-[#6B7280] border-[#E5E7EB] cursor-not-allowed'
                                                    : 'bg-white text-[#111827] hover:bg-slate-50 border-[#E5E7EB]'}`, "aria-label": "Export dashboard data", children: exportState === 'loading' ? (_jsxs(_Fragment, { children: [_jsx(RefreshCw, { className: "w-4 h-4 animate-spin" }), _jsx("span", { children: "Exporting..." })] })) : exportState === 'success' ? (_jsxs(_Fragment, { children: [_jsx(Check, { className: "w-4 h-4" }), _jsx("span", { children: "Exported!" })] })) : exportState === 'error' ? (_jsxs(_Fragment, { children: [_jsx(X, { className: "w-4 h-4" }), _jsx("span", { children: "Failed" })] })) : (_jsxs(_Fragment, { children: [_jsx(Download, { className: "w-4 h-4 text-[#6B7280]" }), _jsx("span", { children: "Export" }), _jsx(ChevronDown, { className: "w-3 h-3 text-[#6B7280]" })] })) }), exportMenuOpen && exportState === 'idle' && (_jsxs("div", { className: "absolute right-0 top-full mt-2 w-44 bg-white rounded-xl border border-[#E5E7EB] shadow-lg z-50 py-1 overflow-hidden", children: [_jsxs("button", { onClick: () => handleExport('json'), className: "w-full text-left px-4 py-2.5 text-xs font-semibold text-[#111827] hover:bg-slate-50 flex items-center gap-2", children: [_jsx("span", { className: "text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded", children: "JSON" }), "Export as JSON"] }), _jsxs("button", { onClick: () => handleExport('csv'), className: "w-full text-left px-4 py-2.5 text-xs font-semibold text-[#111827] hover:bg-slate-50 flex items-center gap-2", children: [_jsx("span", { className: "text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded", children: "CSV" }), "Export as CSV"] })] }))] }), _jsx("div", { className: "w-9 h-9 rounded-full bg-[#F3E8FF] text-[#7C3AED] font-bold text-xs flex items-center justify-center border border-purple-100 shadow-sm cursor-pointer hover:ring-2 hover:ring-purple-200 transition-all", title: "Aarav R. \u2014 Product Team", children: "AR" })] })] }), selectedRange.value !== '30d' && (_jsxs("div", { className: "flex items-center gap-2 text-[11px] font-semibold text-[#7C3AED] bg-[#F3E8FF] border border-purple-100 px-3 py-1.5 rounded-lg w-fit", children: [_jsx(Calendar, { className: "w-3.5 h-3.5" }), "Viewing: ", selectedRange.label, " \u2014 ", selectedRange.display] })), _jsx("div", { className: "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6", children: data.kpis
                    .filter(kpi => kpi.id !== 'aov')
                    .map((kpi) => (_jsx(KPICard, { data: kpi }, kpi.id))) }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-2 gap-6", children: [_jsx(RevenueTrendChart, { data: data.performanceData }), _jsx(ConversionTrendChart, { data: data.performanceData })] }), _jsxs("div", { className: "bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 min-h-[220px] flex flex-col justify-between", children: [_jsxs("div", { className: "pb-3 border-b border-slate-50 flex items-center justify-between", children: [_jsxs("h3", { className: "text-sm font-bold text-[#111827] flex items-center gap-2", children: [_jsx(TrendingUp, { className: "w-4 h-4 text-[#7C3AED]" }), "AI Executive Summary"] }), _jsx("span", { className: "text-[10px] text-[#9CA3AF] font-semibold uppercase", children: "Real-Time Generated" })] }), _jsxs("div", { className: "grid grid-cols-1 lg:grid-cols-4 gap-6 pt-4 flex-grow", children: [_jsx("div", { className: "lg:col-span-2 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-slate-100 pb-4 lg:pb-0 lg:pr-6", children: _jsx("p", { className: "text-xs text-[#6B7280] leading-relaxed font-medium bg-slate-50 p-3.5 rounded-xl border border-slate-100", children: data.insightSummary.text }) }), _jsxs("div", { className: "flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-slate-100 pb-4 lg:pb-0 lg:px-6 space-y-3", children: [_jsxs("div", { className: "flex items-start gap-1.5", children: [_jsx(Lightbulb, { className: "w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" }), _jsxs("div", { children: [_jsx("span", { className: "text-[11px] font-bold text-[#111827]", children: "Opportunity: " }), _jsx("span", { className: "text-[11px] text-[#6B7280] font-semibold", children: data.opportunities[0]?.title })] })] }), _jsxs("div", { className: "flex items-start gap-1.5", children: [_jsx(AlertTriangle, { className: "w-3.5 h-3.5 text-rose-500 mt-0.5 flex-shrink-0" }), _jsxs("div", { children: [_jsx("span", { className: "text-[11px] font-bold text-[#111827]", children: "Risk: " }), _jsx("span", { className: "text-[11px] text-[#6B7280] font-semibold", children: data.anomalies[0]?.title })] })] })] }), _jsxs("div", { className: "flex flex-col items-center justify-center lg:pl-6 text-center", children: [_jsx("span", { className: "text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block", children: "AI Confidence" }), _jsx("span", { className: "text-3xl font-extrabold text-[#7C3AED] mt-1 block", children: "94%" }), _jsxs("div", { className: "flex items-center gap-1 mt-1 bg-purple-50 text-[#7C3AED] px-2 py-0.5 rounded-full text-[9px] font-bold border border-purple-100", children: [_jsx(Info, { className: "w-2.5 h-2.5" }), " High Precision"] })] })] })] }), _jsxs("div", { children: [_jsx("h3", { className: "text-sm font-bold text-[#111827] mb-4", children: "Recent Insights" }), _jsx("div", { className: "grid grid-cols-1 md:grid-cols-3 gap-6", children: data.recentInsights.map((insight) => (_jsxs("div", { className: "bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between min-h-[160px]", children: [_jsxs("div", { children: [_jsxs("div", { className: "flex justify-between items-start mb-2.5 gap-2", children: [_jsx("h4", { className: "text-xs font-bold text-[#111827] leading-snug", children: insight.title }), _jsx("span", { className: `text-[9px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded flex-shrink-0 ${insight.priority === 'High' ? 'bg-rose-50 text-[#EF4444]' :
                                                        insight.priority === 'Medium' ? 'bg-amber-50 text-[#F59E0B]' :
                                                            'bg-sky-50 text-[#3B82F6]'}`, children: insight.priority })] }), _jsx("p", { className: "text-xs text-[#6B7280] leading-relaxed line-clamp-3", children: insight.description })] }), _jsxs("div", { className: "pt-4 mt-4 border-t border-slate-50 flex justify-between items-center", children: [_jsx("span", { className: "text-[10px] text-[#9CA3AF] font-bold uppercase", children: "Expected Impact" }), _jsx("span", { className: "text-xs font-extrabold text-[#7C3AED]", children: insight.expectedImpact })] })] }, insight.id))) })] })] }));
}
