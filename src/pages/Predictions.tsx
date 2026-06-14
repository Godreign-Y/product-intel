import React from 'react';
import {
  LineChart as LineChartIcon,
  AlertTriangle,
  RefreshCw,
  Cpu,
  BrainCircuit,
  Info,
} from 'lucide-react';
import { usePredictions } from '../hooks/usePredictions';
import { ForecastChart } from '../components/Charts';

export default function PredictionsPage() {
  const {
    predictionsData: data,
    selectedMetric: metric,
    setSelectedMetric: setMetric,
    selectedTimeframe: timeframe,
    setSelectedTimeframe: setTimeframe,
    isLoading,
    isError,
    error,
    refetch,
  } = usePredictions();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center h-10 bg-slate-100 rounded-lg animate-pulse w-full max-w-sm" />
        <div className="grid grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-28 bg-white rounded-xl border border-slate-100 animate-pulse shadow-sm" />
          ))}
        </div>
        <div className="h-[450px] bg-white rounded-xl border border-slate-100 p-5 shadow-sm animate-pulse" />
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
          className="flex items-center gap-1.5 px-4 py-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      </div>
    );
  }

  if (!data) return null;

  // 4 Forecast Cards mock stats
  const forecastCards = [
    { title: 'Revenue Forecast', value: '$7.80M', change: '+10.4%', isPositive: true, conf: '95%' },
    { title: 'Profit Forecast', value: '$912K', change: '+14.2%', isPositive: true, conf: '95%' },
    { title: 'Retention Forecast', value: '94.2%', change: '+1.5%', isPositive: true, conf: '92%' },
    { title: 'Conversion Forecast', value: '3.72%', change: '+2.8%', isPositive: true, conf: '90%' },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Header with Title and Model Status Badge */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl font-extrabold text-[#111827] tracking-tight">Predictions</h1>
            <span className="flex items-center gap-1 bg-emerald-50 text-[#10B981] border border-emerald-100 text-[10px] font-bold px-2 py-0.5 rounded-full">
              <Cpu className="w-3 h-3" /> ML Model Active
            </span>
          </div>
          <p className="text-xs text-[#6B7280] mt-1">Machine learning predictive modeling and future horizons</p>
        </div>

        {/* Selection filters */}
        <div className="flex items-center gap-3 w-full sm:w-auto bg-white p-1.5 rounded-xl border border-[#E5E7EB] shadow-sm">
          <div className="flex items-center gap-1.5 px-2">
            <span className="text-[10px] font-bold text-[#9CA3AF] uppercase">Metric:</span>
            <select
              value={metric}
              onChange={(e) => setMetric(e.target.value)}
              className="text-xs font-bold text-[#111827] bg-transparent focus:outline-none cursor-pointer"
            >
              <option value="revenue">Revenue</option>
              <option value="orders">Orders</option>
              <option value="conversionRate">Conversion Rate</option>
              <option value="aov">Average Order Value</option>
              <option value="profit">Profit</option>
            </select>
          </div>
          <div className="w-px h-4 bg-[#E5E7EB]" />
          <div className="flex items-center gap-1.5 px-2">
            <span className="text-[10px] font-bold text-[#9CA3AF] uppercase">Interval:</span>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="text-xs font-bold text-[#111827] bg-transparent focus:outline-none cursor-pointer"
            >
              <option value="Weekly">Weekly</option>
              <option value="Monthly">Monthly</option>
            </select>
          </div>
        </div>
      </div>

      {/* Forecast Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {forecastCards.map((card, i) => (
          <div key={i} className="bg-white border border-[#E5E7EB] rounded-[20px] p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between h-[120px]">
            <div>
              <span className="text-xs font-semibold text-[#6B7280]">{card.title}</span>
              <p className="text-xl font-extrabold text-[#111827] mt-1">{card.value}</p>
            </div>
            <div className="flex justify-between items-center text-[10px] font-bold">
              <span className="text-[#10B981]">{card.change} Next Period</span>
              <span className="text-[#9CA3AF]">{card.conf} Conf</span>
            </div>
          </div>
        ))}
      </div>

      {/* Forecast Graph: Large Full Width Chart */}
      <div className="bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200">
        <h3 className="font-bold text-[#111827] text-sm flex items-center gap-1.5 border-b border-slate-50 pb-3 mb-6">
          <LineChartIcon className="w-4 h-4 text-[#7C3AED]" />
          AI Forecast Modeling Projection
        </h3>
        <div className="h-[380px]">
          <ForecastChart data={data.forecastPoints} metricName={data.metric} />
        </div>
      </div>

      {/* AI Explanation Card */}
      <div className="bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200">
        <h3 className="font-bold text-[#111827] text-sm pb-3 border-b border-slate-50 mb-4 flex items-center gap-2">
          <BrainCircuit className="w-4 h-4 text-[#7C3AED]" />
          AI Explanation Model Details
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 pt-2">
          {/* Why prediction was made */}
          <div className="lg:col-span-2 space-y-3">
            <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider">Prediction Drivers & Causality</h4>
            <p className="text-xs text-[#6B7280] leading-relaxed">
              The model projections are driven primarily by a sustained increase in organic referral velocities and the simulated positive outcome of checkout page updates. Seasonal Q3 adjustment indices have been factored at 1.04x baseline.
            </p>
            <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
              <span className="text-[10px] font-bold text-[#111827] block mb-1">Causal Factors Weighting:</span>
              <ul className="text-[11px] text-[#6B7280] list-disc list-inside space-y-1">
                <li>Organic traffic coefficient: <strong className="text-[#111827]">+0.42</strong></li>
                <li>Checkout step reductions: <strong className="text-[#111827]">+0.28</strong></li>
                <li>Inflation/AOV adjustments: <strong className="text-[#111827]">-0.11</strong></li>
              </ul>
            </div>
          </div>

          {/* Top factors / confidence score list */}
          <div className="border-t lg:border-t-0 lg:border-l border-slate-100 pt-4 lg:pt-0 lg:pl-6 flex flex-col justify-between">
            <div>
              <h4 className="text-xs font-bold text-[#111827] uppercase tracking-wider mb-3">Model Accuracy Indicators</h4>
              <div className="space-y-2.5">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#6B7280] font-semibold">Model Confidence</span>
                  <span className="font-extrabold text-[#7C3AED]">95.4%</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#6B7280] font-semibold">Mean Absolute Error (MAE)</span>
                  <span className="font-extrabold text-[#111827]">2.41%</span>
                </div>
                <div className="flex justify-between items-center text-xs">
                  <span className="text-[#6B7280] font-semibold">Training Horizon</span>
                  <span className="font-extrabold text-[#111827]">18 Months</span>
                </div>
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-50 flex items-center gap-1.5 text-[10px] text-[#9CA3AF] font-semibold">
              <Info className="w-3.5 h-3.5 text-[#7C3AED]" />
              <span>Calculated using ARIMA + LSTM Hybrid Models.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
