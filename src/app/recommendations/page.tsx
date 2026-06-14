'use client';

import React from 'react';
import { Lightbulb, AlertTriangle, RefreshCw } from 'lucide-react';
import { useRecommendations } from '../../hooks/useRecommendations';
import { RecommendationCard } from '../../components/RecommendationCard';

export default function RecommendationsPage() {
  const {
    recommendations,
    filter,
    setFilter,
    isLoading,
    isError,
    error,
    isApplying,
    applyRecommendation,
  } = useRecommendations();

  const filters: ('All' | 'High Impact' | 'Quick Win' | 'Ongoing')[] = [
    'All',
    'High Impact',
    'Quick Win',
    'Ongoing',
  ];

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex border-b border-slate-100 pb-px">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-8 w-20 bg-slate-100 rounded mr-4 animate-pulse" />
          ))}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-72 bg-white rounded-xl border border-slate-100 animate-pulse shadow-sm" />
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
          className="flex items-center gap-1.5 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold mx-auto transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Reload Recommendations
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Category filters */}
      <div className="flex border-b border-slate-100 pb-px">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-4 py-2.5 text-xs font-bold border-b-2 transition-all cursor-pointer ${
              filter === f
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-400 hover:text-slate-600'
            }`}
          >
            {f === 'All' ? 'All Recommendations' : f}
          </button>
        ))}
      </div>

      {recommendations.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-100 rounded-xl max-w-md mx-auto shadow-sm">
          <Lightbulb className="w-12 h-12 stroke-1 text-slate-300 mx-auto mb-3" />
          <h4 className="text-sm font-bold text-slate-700">No Recommendations Found</h4>
          <p className="text-xs text-slate-400 mt-1 px-4 leading-relaxed">
            There are currently no active actionable recommendations in this category. Check back later or run another experiment simulation.
          </p>
        </div>
      ) : (
        /* Recommendations Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((rec) => (
            <RecommendationCard
              key={rec.id}
              recommendation={rec}
              onApply={applyRecommendation}
              isApplying={isApplying}
            />
          ))}
        </div>
      )}
    </div>
  );
}
