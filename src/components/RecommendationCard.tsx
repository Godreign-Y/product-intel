import React from 'react';
import { Sparkles, Check, ArrowRight, TrendingUp } from 'lucide-react';
import { Recommendation } from '../types/recommendations';

interface RecommendationCardProps {
  recommendation: Recommendation;
  onApply?: (id: string) => void;
  isApplying?: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({
  recommendation,
  onApply,
  isApplying = false,
}) => {
  const { id, title, description, category, expectedImpact, businessValue, confidenceLevel, priority, status, tags } =
    recommendation;

  const categoryColors = {
    'High Impact': 'bg-rose-50 text-rose-700 border-rose-100',
    'Quick Win': 'bg-amber-50 text-amber-700 border-amber-100',
    'Ongoing': 'bg-sky-50 text-sky-700 border-sky-100',
  };

  const priorityColors = {
    High: 'bg-rose-100 text-rose-800',
    Medium: 'bg-amber-100 text-amber-800',
    Low: 'bg-slate-100 text-slate-800',
  };

  const isImplemented = status === 'Implemented';

  return (
    <div className="bg-white rounded-xl border border-slate-100 p-6 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between group">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <span
              className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${
                categoryColors[category] || 'bg-slate-50 text-slate-700 border-slate-100'
              }`}
            >
              {category}
            </span>
            <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded ${priorityColors[priority]}`}>
              {priority} Priority
            </span>
          </div>
          <div className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-2 py-1 rounded">
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{confidenceLevel}% Conf</span>
          </div>
        </div>

        <h3 className="text-base font-bold text-slate-900 mt-4 group-hover:text-indigo-600 transition-colors duration-150">
          {title}
        </h3>
        
        <p className="text-sm text-slate-500 mt-2 line-clamp-3 leading-relaxed">
          {description}
        </p>

        {/* Expected Impact & Value */}
        <div className="mt-4 grid grid-cols-2 gap-3 bg-slate-50/50 p-3 rounded-lg border border-slate-50">
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Expected Impact</span>
            <p className="text-sm font-bold text-emerald-600 mt-0.5">{expectedImpact}</p>
          </div>
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Business Value</span>
            <p className="text-sm font-bold text-slate-800 mt-0.5">{businessValue}</p>
          </div>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mt-4">
          {tags.map((tag) => (
            <span key={tag} className="text-xs text-slate-400 bg-slate-100/50 px-2 py-0.5 rounded">
              #{tag}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-slate-50 flex items-center justify-between">
        <span className="text-xs text-slate-400">
          Status: <strong className={isImplemented ? 'text-emerald-600' : 'text-slate-600'}>{status}</strong>
        </span>
        {onApply && (
          <button
            onClick={() => onApply(id)}
            disabled={isImplemented || isApplying}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold border transition-all duration-200 cursor-pointer ${
              isImplemented
                ? 'bg-emerald-50 text-emerald-600 border-emerald-100 cursor-not-allowed'
                : 'bg-indigo-600 text-white border-indigo-600 hover:bg-indigo-700 shadow-sm shadow-indigo-100 hover:shadow'
            }`}
          >
            {isImplemented ? (
              <>
                <Check className="w-3.5 h-3.5" />
                Applied
              </>
            ) : isApplying ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Applying...
              </>
            ) : (
              <>
                <Sparkles className="w-3.5 h-3.5" />
                Apply Now
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};
