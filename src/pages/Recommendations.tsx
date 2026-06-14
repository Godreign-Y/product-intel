import React from 'react';
import {
  Lightbulb,
  AlertTriangle,
  RefreshCw,
} from 'lucide-react';
import { useRecommendations } from '../hooks/useRecommendations';
import { RecommendationCard } from '../components/RecommendationCard';

export default function RecommendationsPage() {
  const {
    recommendations,
    filter,
    setFilter,
    isLoading,
    isError,
    error,
    applyRecommendation,
  } = useRecommendations();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex justify-between items-center h-10 bg-slate-100 rounded-lg animate-pulse w-full max-w-sm" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-48 bg-white rounded-xl border border-slate-100 animate-pulse shadow-sm" />
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-50 border border-rose-100 rounded-xl p-6 text-center max-w-2xl mx-auto my-12">
        <AlertTriangle className="w-12 h-12 text-rose-500 mx-auto mb-4" />
        <h3 className="text-lg font-bold text-slate-800 mb-2">Error Loading Recommendations</h3>
        <p className="text-sm text-slate-600 mb-6">{error?.message || 'An unexpected error occurred.'}</p>
        <button
          onClick={() => window.location.reload()}
          className="flex items-center gap-1.5 px-4 py-2 bg-[#7C3AED] hover:bg-[#6D28D9] text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reload Page
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      <div>
        <h1 className="text-2xl font-extrabold text-[#111827] tracking-tight">Recommendations</h1>
        <p className="text-xs text-[#6B7280] mt-1">Growth strategies and conversion optimization playbooks suggested by AI models</p>
      </div>

      {/* Filtering row */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-3.5 rounded-[20px] border border-[#E5E7EB] shadow-sm">
        <div className="flex flex-wrap gap-2">
          {(['All', 'High Impact', 'Quick Win', 'Ongoing'] as const).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`h-[36px] px-4 rounded-[8px] text-xs font-bold transition-all border cursor-pointer ${
                filter === f
                  ? 'bg-[#7C3AED] border-[#7C3AED] text-white shadow-sm shadow-purple-100'
                  : 'bg-slate-50 border-[#E5E7EB] text-[#6B7280] hover:bg-[#F3E8FF] hover:text-[#7C3AED]'
              }`}
            >
              {f === 'All' ? 'All Opportunities' : f}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-xs font-bold text-[#6B7280] bg-[#F3E8FF] text-[#7C3AED] px-3 py-1.5 rounded-full border border-purple-100">
          <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
          <span>Active Opportunities: {recommendations.length}</span>
        </div>
      </div>

      {/* Cards list */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {recommendations.map((rec) => (
          <RecommendationCard
            key={rec.id}
            recommendation={rec}
            onApply={applyRecommendation}
          />
        ))}
      </div>
    </div>
  );
}
