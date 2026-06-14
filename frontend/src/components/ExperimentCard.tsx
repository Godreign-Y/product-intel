import React from 'react';
import { Calendar, Layers, CheckCircle2, Play, FileText, ChevronRight } from 'lucide-react';
import { Experiment } from '../types/experiments';

interface ExperimentCardProps {
  experiment: Experiment;
  onSelect?: (exp: Experiment) => void;
}

export const ExperimentCard: React.FC<ExperimentCardProps> = ({ experiment, onSelect }) => {
  const { id, name, objective, hypothesis, primaryMetric, type, status, createdAt, variables, result, changePercent, isPositive } =
    experiment;

  const statusColors = {
    Completed: 'bg-emerald-50 text-emerald-700 border-emerald-100',
    Running: 'bg-purple-50 text-[#7C3AED] border-purple-100',
    Draft: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  const statusIcons = {
    Completed: <CheckCircle2 className="w-3.5 h-3.5" />,
    Running: <Play className="w-3.5 h-3.5 animate-pulse" />,
    Draft: <FileText className="w-3.5 h-3.5" />,
  };

  const formattedDate = new Date(createdAt).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="bg-white rounded-xl border border-slate-100 p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between h-full group">
      <div>
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
            {type}
          </span>
          <div
            className={`flex items-center gap-1 text-xs font-medium px-2.5 py-0.5 rounded-full border ${
              statusColors[status]
            }`}
          >
            {statusIcons[status]}
            <span>{status}</span>
          </div>
        </div>

        <h3 className="text-base font-bold text-slate-900 mt-4 group-hover:text-[#7C3AED] transition-colors duration-150">
          {name}
        </h3>

        <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
          <Calendar className="w-3 h-3" />
          <span>Launched {formattedDate}</span>
        </p>

        <div className="mt-4 space-y-2.5">
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Objective</span>
            <p className="text-xs text-slate-600 font-medium line-clamp-2 mt-0.5">{objective}</p>
          </div>
          <div>
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">Primary Metric</span>
            <p className="text-xs text-slate-800 font-bold mt-0.5">{primaryMetric}</p>
          </div>
        </div>

        {/* Variables List */}
        <div className="mt-4 pt-3 border-t border-slate-50">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5">Variables Tested</span>
          <div className="space-y-1.5">
            {variables.map((v) => (
              <div key={v.id} className="flex items-center justify-between text-xs bg-slate-50 px-2.5 py-1 rounded">
                <span className="text-slate-500 font-medium">{v.name}</span>
                <span className="flex items-center text-[10px] font-bold text-slate-700">
                  <span className="text-slate-400 line-through mr-1">{v.currentValue}</span>
                  <ChevronRight className="w-2.5 h-2.5 text-slate-400 mx-0.5" />
                  <span className="text-indigo-600 bg-purple-50 px-1 rounded">{v.newValue}</span>
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-6 pt-3 border-t border-slate-50 flex items-center justify-between">
        {status === 'Completed' && result ? (
          <div className="w-full">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Outcome</span>
            <p
              className={`text-sm font-bold mt-0.5 ${
                isPositive ? 'text-emerald-600' : 'text-rose-600'
              }`}
            >
              {result}
            </p>
          </div>
        ) : (
          <div className="w-full">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">Outcome</span>
            <p className="text-xs text-slate-400 italic mt-0.5">Simulation running...</p>
          </div>
        )}
        
        {onSelect && (
          <button
            onClick={() => onSelect(experiment)}
            className="text-xs text-[#7C3AED] hover:text-[#6D28D9] font-bold flex items-center gap-0.5 cursor-pointer whitespace-nowrap"
          >
            Details
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>
    </div>
  );
};
