'use client';

import React from 'react';
import {
  Filter,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { usePredictions } from '../../hooks/usePredictions';
import { ForecastChart } from '../../components/Charts';

export default function PredictionsPage() {
  const {
    predictionsData,
    selectedMetric,
    setSelectedMetric,
    selectedTimeframe,
    setSelectedTimeframe,
    isLoading,
    isError,
    error,
    refetch,
  } = usePredictions();

  const metrics = [
    { key: 'Revenue', label: 'Revenue Forecast' },
    { key: 'Orders', label: 'Orders Forecast' },
    { key: 'Conversion Rate', label: 'Conversion Rate Forecast' },
    { key: 'AOV', label: 'Average Order Value Forecast' },
    { key: 'Profit', label: 'Profit Forecast' },
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center h-12 bg-white border border-slate-100 rounded-xl animate-pulse w-full shadow-sm" />
        <div className="h-96 bg-white border border-slate-100 rounded-xl animate-pulse w-full shadow-sm" />
        <div className="h-64 bg-white border border-slate-100 rounded-xl animate-pulse w-full shadow-sm" />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-50 border border-rose-100 rounded-xl p-6 text-center max-w-2xl mx-auto my-12">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-800 mb-2">Error Loading Predictions</h3>
        <p className="text-sm text-slate-600 mb-6">{error?.message || 'An unexpected error occurred.'}</p>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Forecast Calculation
        </button>
      </div>
    );
  }

  if (!predictionsData) return null;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Filter Header Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-3.5 rounded-xl border border-slate-100 shadow-sm">
        <div className="flex flex-wrap items-center gap-2.5">
          {/* Metric Selector Dropdown */}
          <select
            value={selectedMetric}
            onChange={(e) => setSelectedMetric(e.target.value)}
            className="bg-slate-50 text-slate-700 font-semibold text-xs px-3.5 py-2 rounded-lg border border-slate-200 focus:outline-none cursor-pointer"
          >
            {metrics.map((m) => (
              <option key={m.key} value={m.key}>
                {m.label}
              </option>
            ))}
          </select>

          {/* Timeframe Selector */}
          <select
            value={selectedTimeframe}
            onChange={(e) => setSelectedTimeframe(e.target.value)}
            className="bg-slate-50 text-slate-700 font-semibold text-xs px-3.5 py-2 rounded-lg border border-slate-200 focus:outline-none cursor-pointer"
          >
            <option>Monthly</option>
            <option>Weekly</option>
          </select>
        </div>

        <button className="flex items-center gap-1.5 text-xs font-semibold bg-slate-50 text-slate-700 hover:bg-slate-100 px-3.5 py-2 rounded-lg border border-slate-200 transition-colors cursor-pointer">
          <Filter className="w-3.5 h-3.5" />
          Filters
        </button>
      </div>

      {/* Main Area Forecast Chart */}
      <div className="grid grid-cols-1">
        <ForecastChart
          data={predictionsData.forecastPoints}
          metricName={predictionsData.metric}
        />
      </div>

      {/* Other Forecasts Summary Table */}
      <div className="bg-white rounded-xl border border-slate-100 shadow-sm p-6 overflow-hidden">
        <h3 className="font-semibold text-slate-900 mb-4 pb-3 border-b border-slate-50">
          Other Forecasts (Next Period Projection)
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="text-slate-400 font-bold border-b border-slate-50 uppercase tracking-wider">
                <th className="pb-3 font-semibold">Metric</th>
                <th className="pb-3 font-semibold">Next Period Forecast</th>
                <th className="pb-3 font-semibold text-center">Projected Change</th>
                <th className="pb-3 font-semibold text-right">Confidence Level</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-50">
              {predictionsData.summaryTable.map((row) => (
                <tr key={row.metric} className="hover:bg-slate-50/50 transition-colors">
                  <td className="py-4 font-bold text-slate-800">{row.metric}</td>
                  <td className="py-4 font-semibold text-slate-700">{row.nextPeriodForecast}</td>
                  <td className="py-4">
                    <div className="flex items-center justify-center gap-1.5 font-bold">
                      <span
                        className={`flex items-center gap-0.5 px-2 py-0.5 rounded-full ${
                          row.isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
                        }`}
                      >
                        {row.isPositive ? (
                          <ArrowUpRight className="w-3 h-3" />
                        ) : (
                          <ArrowDownRight className="w-3 h-3" />
                        )}
                        {Math.abs(row.projectedChangePercent)}%
                      </span>
                    </div>
                  </td>
                  <td className="py-4 text-right">
                    <div className="flex items-center justify-end gap-2">
                      <span className="font-bold text-slate-600">{row.confidence}%</span>
                      <div className="w-20 bg-slate-100 h-1.5 rounded-full overflow-hidden">
                        <div
                          className="bg-indigo-600 h-full rounded-full"
                          style={{ width: `${row.confidence}%` }}
                        />
                      </div>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
