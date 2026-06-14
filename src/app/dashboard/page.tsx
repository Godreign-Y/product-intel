'use client';

import React from 'react';
import Link from 'next/link';
import {
  Calendar,
  Filter,
  ArrowRight,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  FlaskConical,
  RefreshCw,
} from 'lucide-react';
import { useDashboardData } from '../../hooks/useDashboardData';
import { KPICard } from '../../components/KPICard';
import { PerformanceChart } from '../../components/Charts';

export default function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboardData();

  if (isLoading) {
    return (
      <div className="space-y-6">
        {/* Date Row Skeleton */}
        <div className="flex justify-between items-center h-10 bg-slate-100 rounded-lg animate-pulse w-full max-w-sm" />
        
        {/* KPIs Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-5 gap-5">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-32 bg-white rounded-xl border border-slate-100 p-5 shadow-sm animate-pulse" />
          ))}
        </div>

        {/* Charts Skeleton */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 h-96 bg-white rounded-xl border border-slate-100 p-5 shadow-sm animate-pulse" />
          <div className="h-96 bg-white rounded-xl border border-slate-100 p-5 shadow-sm animate-pulse" />
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
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Retry Request
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6 pb-12">
      {/* Top Filter Panel */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-3.5 rounded-xl border border-slate-100 shadow-sm">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
          <Calendar className="w-4 h-4 text-slate-400" />
          <span className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100">
            May 20 - Jun 18, 2026
          </span>
          <span className="text-slate-400 font-normal">Compare to:</span>
          <span className="bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 cursor-pointer hover:bg-slate-100">
            Apr 20 - May 19, 2026
          </span>
        </div>
        <button className="flex items-center gap-1.5 text-xs font-semibold bg-slate-50 text-slate-700 hover:bg-slate-100 px-3 py-2 rounded-lg border border-slate-200 transition-colors cursor-pointer">
          <Filter className="w-3.5 h-3.5" />
          Filters
        </button>
      </div>

      {/* KPI Section */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-5">
        {data.kpis.map((kpi) => (
          <KPICard key={kpi.id} data={kpi} />
        ))}
      </div>

      {/* Main Charts & Insight Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Performance Line Chart */}
        <div className="lg:col-span-2">
          <PerformanceChart data={data.performanceData} />
        </div>

        {/* AI Insight Summary */}
        <div className="bg-white rounded-xl border border-slate-100 p-5 shadow-sm flex flex-col justify-between h-full">
          <div>
            <h3 className="font-semibold text-slate-900 flex items-center gap-1.5 border-b border-slate-50 pb-3 mb-4">
              <TrendingUp className="w-4 h-4 text-indigo-500" />
              AI Insights Summary
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed font-medium bg-indigo-50/30 p-3.5 rounded-lg border border-indigo-50/50 mb-4">
              {data.insightSummary.text}
            </p>
            <ul className="space-y-3.5">
              {data.insightSummary.bulletPoints.map((bullet, i) => (
                <li key={i} className="flex items-start gap-2.5 text-xs text-slate-500 leading-normal">
                  <span className="w-1.5 h-1.5 bg-indigo-600 rounded-full mt-1.5 flex-shrink-0" />
                  <span>{bullet}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="pt-6 mt-6 border-t border-slate-50">
            <Link
              href="/ai-workspace"
              className="flex items-center justify-center gap-1.5 w-full py-2.5 rounded-xl text-xs font-bold text-indigo-600 bg-indigo-50 hover:bg-indigo-100 transition-colors cursor-pointer"
            >
              Go to AI Workspace
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Bottom Grid: Opportunities, Anomalies & Recent Experiments */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Top Opportunities */}
        <div className="bg-white rounded-xl border border-slate-100 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-3 border-b border-slate-50 mb-4">
              <h3 className="font-semibold text-slate-900 flex items-center gap-1.5">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                Top Opportunities
              </h3>
              <Link href="/recommendations" className="text-[10px] font-bold text-indigo-600 hover:underline">
                View all
              </Link>
            </div>
            <div className="space-y-3">
              {data.opportunities.map((opp) => (
                <div key={opp.id} className="flex justify-between items-center p-2.5 bg-slate-50/50 border border-slate-50 rounded-lg">
                  <div>
                    <h4 className="text-xs font-bold text-slate-800">{opp.title}</h4>
                    <span className="text-[10px] text-slate-400 mt-0.5 block">Potential Impact: {opp.impactValue}</span>
                  </div>
                  <span className={`text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded ${
                    opp.priority === 'high' ? 'bg-rose-50 text-rose-600' : 'bg-amber-50 text-amber-600'
                  }`}>
                    {opp.impactLevel}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Anomaly Detection */}
        <div className="bg-white rounded-xl border border-slate-100 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-3 border-b border-slate-50 mb-4">
              <h3 className="font-semibold text-slate-900 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-rose-500" />
                Anomaly Detection
              </h3>
              <button className="text-[10px] font-bold text-indigo-600 hover:underline cursor-pointer">
                View all
              </button>
            </div>
            <div className="space-y-3">
              {data.anomalies.map((anom) => (
                <div key={anom.id} className="flex items-start gap-2.5 p-2.5 bg-slate-50/50 border border-slate-50 rounded-lg">
                  <span className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${
                    anom.severity === 'high' ? 'bg-rose-500' : anom.severity === 'medium' ? 'bg-amber-500' : 'bg-slate-400'
                  }`} />
                  <div>
                    <h4 className="text-xs font-bold text-slate-800 leading-tight">{anom.title}</h4>
                    <p className="text-[10px] text-slate-400 mt-0.5">{anom.description}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Recent Experiments */}
        <div className="bg-white rounded-xl border border-slate-100 p-5 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex justify-between items-center pb-3 border-b border-slate-50 mb-4">
              <h3 className="font-semibold text-slate-900 flex items-center gap-1.5">
                <FlaskConical className="w-4 h-4 text-emerald-500" />
                Recent Experiments
              </h3>
              <Link href="/experiments" className="text-[10px] font-bold text-indigo-600 hover:underline">
                View all
              </Link>
            </div>
            <div className="space-y-3">
              {data.recentExperiments.map((exp) => (
                <div key={exp.id} className="flex justify-between items-center p-2.5 bg-slate-50/50 border border-slate-50 rounded-lg">
                  <span className="text-xs font-bold text-slate-800 truncate max-w-[150px]">{exp.name}</span>
                  <div className="flex items-center gap-2">
                    <span className={`text-[9px] font-semibold px-2 py-0.5 rounded ${
                      exp.status === 'Completed' ? 'bg-emerald-50 text-emerald-600' : 'bg-indigo-50 text-indigo-600'
                    }`}>
                      {exp.status}
                    </span>
                    {exp.result && (
                      <span className={`text-[10px] font-bold ${exp.isPositive ? 'text-emerald-600' : 'text-rose-600'}`}>
                        {exp.changePercent ? `${exp.changePercent > 0 ? '+' : ''}${exp.changePercent}%` : exp.result}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
