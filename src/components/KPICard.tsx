import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { KPICardData } from '../types/dashboard';

interface KPICardProps {
  data: KPICardData;
}

export const KPICard: React.FC<KPICardProps> = ({ data }) => {
  const { title, value, changePercent, isPositive, timeframe, sparkline } = data;

  // Generate SVG path for sparkline
  const points = sparkline.map(p => p.value);
  const min = Math.min(...points);
  const max = Math.max(...points);
  const range = max - min === 0 ? 1 : max - min;
  
  const width = 140;
  const height = 40;
  const svgPoints = sparkline
    .map((p, index) => {
      const x = (index / (sparkline.length - 1)) * width;
      const y = height - ((p.value - min) / range) * (height - 8) - 4; // leave 4px padding top/bottom
      return `${x},${y}`;
    })
    .join(' ');

  const strokeColor = isPositive ? '#22c55e' : '#ef4444'; // green or red
  const fillColor = isPositive ? 'rgba(34, 197, 94, 0.05)' : 'rgba(239, 68, 68, 0.05)';

  return (
    <div className="bg-white rounded-xl border border-slate-100 p-5 shadow-sm hover:shadow-md transition-all duration-200 flex flex-col justify-between h-full group">
      <div>
        <div className="flex justify-between items-start">
          <span className="text-sm font-medium text-slate-500">{title}</span>
          <div
            className={`flex items-center text-xs font-semibold px-2 py-0.5 rounded-full ${
              isPositive ? 'bg-emerald-50 text-emerald-600' : 'bg-rose-50 text-rose-600'
            }`}
          >
            {isPositive ? (
              <ArrowUpRight className="w-3.5 h-3.5 mr-0.5" />
            ) : (
              <ArrowDownRight className="w-3.5 h-3.5 mr-0.5" />
            )}
            {Math.abs(changePercent)}%
          </div>
        </div>

        <div className="mt-2 flex items-baseline">
          <span className="text-2xl font-bold text-slate-900 tracking-tight">{value}</span>
        </div>
        
        <p className="text-xs text-slate-400 mt-1">{timeframe}</p>
      </div>

      <div className="mt-4 pt-2 flex items-center justify-between">
        <div className="w-full">
          <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-10 overflow-visible">
            <defs>
              <linearGradient id={`gradient-${data.id}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={strokeColor} stopOpacity="0.2" />
                <stop offset="100%" stopColor={strokeColor} stopOpacity="0.0" />
              </linearGradient>
            </defs>
            {/* Area under the line */}
            <polygon
              points={`0,${height} ${svgPoints} ${width},${height}`}
              fill={`url(#gradient-${data.id})`}
            />
            {/* The sparkline */}
            <polyline
              fill="none"
              stroke={strokeColor}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={svgPoints}
            />
          </svg>
        </div>
      </div>
    </div>
  );
};
