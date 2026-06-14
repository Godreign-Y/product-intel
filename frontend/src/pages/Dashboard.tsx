import React, { useState, useRef, useEffect } from 'react';
import {
  Calendar,
  Download,
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  RefreshCw,
  Info,
  Check,
  ChevronDown,
  X,
} from 'lucide-react';
import { useDashboardData } from '../hooks/useDashboardData';
import { KPICard } from '../components/KPICard';
import { RevenueTrendChart, ConversionTrendChart } from '../components/Charts';

// ─────────────────────────────────────────────
// Date Range Definitions
// ─────────────────────────────────────────────
const DATE_RANGES = [
  { label: 'Last 30 Days',  value: '30d',  display: 'May 20 – Jun 18, 2026' },
  { label: 'Last 7 Days',   value: '7d',   display: 'Jun 12 – Jun 18, 2026' },
  { label: 'Last 90 Days',  value: '90d',  display: 'Mar 21 – Jun 18, 2026' },
  { label: 'This Quarter',  value: 'qtd',  display: 'Apr 01 – Jun 18, 2026' },
  { label: 'Last Quarter',  value: 'lq',   display: 'Jan 01 – Mar 31, 2026' },
  { label: 'This Year',     value: 'ytd',  display: 'Jan 01 – Jun 18, 2026' },
];

type ExportState = 'idle' | 'loading' | 'success' | 'error';

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboardData();

  // ── Date range state ──────────────────────────
  const [selectedRange, setSelectedRange] = useState(DATE_RANGES[0]);
  const [datePickerOpen, setDatePickerOpen] = useState(false);
  const datePickerRef = useRef<HTMLDivElement>(null);

  // ── Export state ──────────────────────────────
  const [exportState, setExportState] = useState<ExportState>('idle');
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');
  const [exportMenuOpen, setExportMenuOpen] = useState(false);
  const exportMenuRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (datePickerRef.current && !datePickerRef.current.contains(e.target as Node)) {
        setDatePickerOpen(false);
      }
      if (exportMenuRef.current && !exportMenuRef.current.contains(e.target as Node)) {
        setExportMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // ── Export handler ────────────────────────────
  const handleExport = (format: 'json' | 'csv') => {
    if (!data || exportState === 'loading') return;
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
        } else {
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
      } catch {
        setExportState('error');
        setTimeout(() => setExportState('idle'), 3000);
      }
    }, 900);
  };

  // ─────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center h-12 bg-slate-100 rounded-lg animate-pulse w-full" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-[140px] bg-white rounded-[20px] border border-slate-100 p-5 shadow-sm animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-[350px] bg-white rounded-[20px] border border-slate-100 p-5 shadow-sm animate-pulse" />
          <div className="h-[350px] bg-white rounded-[20px] border border-slate-100 p-5 shadow-sm animate-pulse" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-50 border border-rose-100 rounded-xl p-6 text-center max-w-2xl mx-auto my-12">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-800 mb-2">Error Loading Dashboard</h3>
        <p className="text-sm text-slate-600 mb-6">{error?.message || 'An unexpected error occurred.'}</p>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-8 pb-12">
      {/* ── Top Header ── */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-[#111827] tracking-tight">Dashboard</h1>
          <p className="text-xs text-[#6B7280] mt-1">Executive overview of business performance</p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* ── Date Range Picker ── */}
          <div className="relative" ref={datePickerRef}>
            <button
              onClick={() => setDatePickerOpen(v => !v)}
              className="flex items-center gap-2 bg-white px-3 py-2 rounded-xl border border-[#E5E7EB] hover:bg-slate-50 cursor-pointer shadow-sm transition-colors"
              aria-haspopup="listbox"
              aria-expanded={datePickerOpen}
            >
              <Calendar className="w-4 h-4 text-[#6B7280]" />
              <span className="text-xs font-semibold text-[#111827]">{selectedRange.display}</span>
              <ChevronDown className={`w-3.5 h-3.5 text-[#6B7280] transition-transform ${datePickerOpen ? 'rotate-180' : ''}`} />
            </button>

            {datePickerOpen && (
              <div className="absolute right-0 top-full mt-2 w-52 bg-white rounded-xl border border-[#E5E7EB] shadow-lg z-50 py-1 overflow-hidden">
                {DATE_RANGES.map(range => (
                  <button
                    key={range.value}
                    onClick={() => {
                      setSelectedRange(range);
                      setDatePickerOpen(false);
                    }}
                    className={`w-full text-left px-4 py-2.5 text-xs font-semibold flex items-center justify-between transition-colors ${
                      selectedRange.value === range.value
                        ? 'bg-[#F3E8FF] text-[#7C3AED]'
                        : 'text-[#111827] hover:bg-slate-50'
                    }`}
                  >
                    <span>{range.label}</span>
                    {selectedRange.value === range.value && <Check className="w-3.5 h-3.5" />}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* ── Export Button ── */}
          <div className="relative" ref={exportMenuRef}>
            <button
              onClick={() => {
                if (exportState === 'idle') setExportMenuOpen(v => !v);
              }}
              disabled={exportState === 'loading'}
              className={`flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl border text-xs font-semibold shadow-sm cursor-pointer transition-all ${
                exportState === 'success'
                  ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                  : exportState === 'error'
                  ? 'bg-rose-50 text-rose-600 border-rose-200'
                  : exportState === 'loading'
                  ? 'bg-slate-50 text-[#6B7280] border-[#E5E7EB] cursor-not-allowed'
                  : 'bg-white text-[#111827] hover:bg-slate-50 border-[#E5E7EB]'
              }`}
              aria-label="Export dashboard data"
            >
              {exportState === 'loading' ? (
                <><RefreshCw className="w-4 h-4 animate-spin" /><span>Exporting...</span></>
              ) : exportState === 'success' ? (
                <><Check className="w-4 h-4" /><span>Exported!</span></>
              ) : exportState === 'error' ? (
                <><X className="w-4 h-4" /><span>Failed</span></>
              ) : (
                <><Download className="w-4 h-4 text-[#6B7280]" /><span>Export</span><ChevronDown className="w-3 h-3 text-[#6B7280]" /></>
              )}
            </button>

            {exportMenuOpen && exportState === 'idle' && (
              <div className="absolute right-0 top-full mt-2 w-44 bg-white rounded-xl border border-[#E5E7EB] shadow-lg z-50 py-1 overflow-hidden">
                <button
                  onClick={() => handleExport('json')}
                  className="w-full text-left px-4 py-2.5 text-xs font-semibold text-[#111827] hover:bg-slate-50 flex items-center gap-2"
                >
                  <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">JSON</span>
                  Export as JSON
                </button>
                <button
                  onClick={() => handleExport('csv')}
                  className="w-full text-left px-4 py-2.5 text-xs font-semibold text-[#111827] hover:bg-slate-50 flex items-center gap-2"
                >
                  <span className="text-[10px] font-bold bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">CSV</span>
                  Export as CSV
                </button>
              </div>
            )}
          </div>

          {/* ── User Avatar ── */}
          <div
            className="w-9 h-9 rounded-full bg-[#F3E8FF] text-[#7C3AED] font-bold text-xs flex items-center justify-center border border-purple-100 shadow-sm cursor-pointer hover:ring-2 hover:ring-purple-200 transition-all"
            title="Aarav R. — Product Team"
          >
            AR
          </div>
        </div>
      </div>

      {/* ── Date range context label ── */}
      {selectedRange.value !== '30d' && (
        <div className="flex items-center gap-2 text-[11px] font-semibold text-[#7C3AED] bg-[#F3E8FF] border border-purple-100 px-3 py-1.5 rounded-lg w-fit">
          <Calendar className="w-3.5 h-3.5" />
          Viewing: {selectedRange.label} — {selectedRange.display}
        </div>
      )}

      {/* ── Section 1: KPI Cards ── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {data.kpis
          .filter(kpi => kpi.id !== 'aov')
          .map((kpi) => (
            <KPICard key={kpi.id} data={kpi} />
          ))}
      </div>

      {/* ── Section 2: Analytics Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <RevenueTrendChart data={data.performanceData} />
        <ConversionTrendChart data={data.performanceData} />
      </div>

      {/* ── Section 3: AI Executive Summary ── */}
      <div className="bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 min-h-[220px] flex flex-col justify-between">
        <div className="pb-3 border-b border-slate-50 flex items-center justify-between">
          <h3 className="text-sm font-bold text-[#111827] flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-[#7C3AED]" />
            AI Executive Summary
          </h3>
          <span className="text-[10px] text-[#9CA3AF] font-semibold uppercase">Real-Time Generated</span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 pt-4 flex-grow">
          {/* Summary Text */}
          <div className="lg:col-span-2 flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-slate-100 pb-4 lg:pb-0 lg:pr-6">
            <p className="text-xs text-[#6B7280] leading-relaxed font-medium bg-slate-50 p-3.5 rounded-xl border border-slate-100">
              {data.insightSummary.text}
            </p>
          </div>

          {/* Opportunities and Risks */}
          <div className="flex flex-col justify-center border-b lg:border-b-0 lg:border-r border-slate-100 pb-4 lg:pb-0 lg:px-6 space-y-3">
            <div className="flex items-start gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-amber-500 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-[11px] font-bold text-[#111827]">Opportunity: </span>
                <span className="text-[11px] text-[#6B7280] font-semibold">{data.opportunities[0]?.title}</span>
              </div>
            </div>
            <div className="flex items-start gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-500 mt-0.5 flex-shrink-0" />
              <div>
                <span className="text-[11px] font-bold text-[#111827]">Risk: </span>
                <span className="text-[11px] text-[#6B7280] font-semibold">{data.anomalies[0]?.title}</span>
              </div>
            </div>
          </div>

          {/* Confidence Score */}
          <div className="flex flex-col items-center justify-center lg:pl-6 text-center">
            <span className="text-[10px] font-bold text-[#9CA3AF] uppercase tracking-wider block">AI Confidence</span>
            <span className="text-3xl font-extrabold text-[#7C3AED] mt-1 block">94%</span>
            <div className="flex items-center gap-1 mt-1 bg-purple-50 text-[#7C3AED] px-2 py-0.5 rounded-full text-[9px] font-bold border border-purple-100">
              <Info className="w-2.5 h-2.5" /> High Precision
            </div>
          </div>
        </div>
      </div>

      {/* ── Section 4: Recent Insights ── */}
      <div>
        <h3 className="text-sm font-bold text-[#111827] mb-4">Recent Insights</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {data.recentInsights.map((insight) => (
            <div
              key={insight.id}
              className="bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between min-h-[160px]"
            >
              <div>
                <div className="flex justify-between items-start mb-2.5 gap-2">
                  <h4 className="text-xs font-bold text-[#111827] leading-snug">{insight.title}</h4>
                  <span className={`text-[9px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded flex-shrink-0 ${
                    insight.priority === 'High' ? 'bg-rose-50 text-[#EF4444]' :
                    insight.priority === 'Medium' ? 'bg-amber-50 text-[#F59E0B]' :
                    'bg-sky-50 text-[#3B82F6]'
                  }`}>
                    {insight.priority}
                  </span>
                </div>
                <p className="text-xs text-[#6B7280] leading-relaxed line-clamp-3">{insight.description}</p>
              </div>

              <div className="pt-4 mt-4 border-t border-slate-50 flex justify-between items-center">
                <span className="text-[10px] text-[#9CA3AF] font-bold uppercase">Expected Impact</span>
                <span className="text-xs font-extrabold text-[#7C3AED]">{insight.expectedImpact}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
