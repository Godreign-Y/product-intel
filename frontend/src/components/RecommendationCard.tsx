/**
 * RecommendationCard Component.
 *
 * Renders a single growth recommendation with priority badge, business
 * value, and an "Implement" action button. All data comes from the backend.
 *
 * @module RecommendationCard
 */

import React from 'react';
import { Sparkles, Check, Info } from 'lucide-react';
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
  const { id, title, description, category, businessValue, priority, status, timeToImplement, effort } =
    recommendation;

  const priorityColors: Record<string, string> = {
    'High Impact': 'bg-rose-50 text-rose-700 border-rose-100',
    'Quick Win': 'bg-amber-50 text-amber-700 border-amber-100',
    'Ongoing': 'bg-sky-50 text-sky-700 border-sky-100',
  };

  const categoryColors: Record<string, string> = {
    Conversion: 'bg-purple-50 text-purple-700 border-purple-100',
    Logistics: 'bg-blue-50 text-blue-700 border-blue-100',
    Marketing: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    Pricing: 'bg-amber-50 text-amber-700 border-amber-100',
    Retention: 'bg-rose-50 text-rose-700 border-rose-100',
  };

  const isImplemented = status === 'Implemented';

  return (
    <div className="bg-white rounded-[20px] border border-[#E5E7EB] p-6 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between group h-full">
      <div>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border ${
                categoryColors[category] || 'bg-slate-50 text-slate-700 border-slate-100'
              }`}
            >
              {category}
            </span>
            <span className={`text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded border ${priorityColors[priority] || 'bg-slate-50 text-slate-700 border-slate-100'}`}>
              {priority}
            </span>
          </div>
          {effort && (
            <div className="flex items-center gap-1.5 text-xs font-bold text-[#6B7280] bg-slate-50 px-2.5 py-0.5 rounded-full border border-slate-100">
              <span>{effort} Effort</span>
            </div>
          )}
        </div>

        <h3 className="text-base font-bold text-[#111827] mt-4 group-hover:text-[#7C3AED] transition-colors duration-150">
          {title}
        </h3>

        <p className="text-xs text-[#6B7280] mt-2 line-clamp-3 leading-relaxed">
          {description}
        </p>

        {/* Business Value & Timeline */}
        <div className="mt-4 grid grid-cols-2 gap-3 bg-slate-50/50 p-3.5 rounded-[12px] border border-slate-100">
          <div>
            <span className="text-[9px] font-bold text-[#9CA3AF] uppercase tracking-wider">Business Value</span>
            <p className="text-xs font-extrabold text-[#10B981] mt-0.5">{businessValue}</p>
          </div>
          <div>
            <span className="text-[9px] font-bold text-[#9CA3AF] uppercase tracking-wider">Time to Implement</span>
            <p className="text-xs font-extrabold text-[#111827] mt-0.5">{timeToImplement || '—'}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 pt-4 border-t border-slate-50 flex items-center justify-between">
        <span className="text-xs text-[#6B7280]">
          Status: <strong className={isImplemented ? 'text-[#10B981]' : 'text-[#6B7280]'}>{status}</strong>
        </span>

        <div className="flex items-center gap-2">
          {/* Learn More Button */}
          <button
            type="button"
            className="h-[36px] px-3 bg-white border border-[#E5E7EB] hover:bg-slate-50 text-[#111827] rounded-[8px] text-xs font-semibold cursor-pointer transition-colors flex items-center gap-1"
          >
            <Info className="w-3.5 h-3.5 text-[#6B7280]" />
            Learn More
          </button>

          {/* Implement Button */}
          {onApply && (
            <button
              onClick={() => onApply(id)}
              disabled={isImplemented || isApplying}
              className={`h-[36px] px-4 rounded-[8px] text-xs font-bold border transition-all duration-200 cursor-pointer flex items-center gap-1.5 ${
                isImplemented
                  ? 'bg-emerald-50 text-[#10B981] border-emerald-100 cursor-not-allowed'
                  : 'bg-[#7C3AED] text-white border-[#7C3AED] hover:bg-[#6D28D9] shadow-sm shadow-purple-100 hover:shadow'
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
                  Implement
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
